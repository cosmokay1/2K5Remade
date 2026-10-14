"""Game-facing decisions persist without creating a phantom signing."""
import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger, Offer, Rejected
from franchise.control import AccessDisabled
from franchise.store import FranchiseStore


class NegotiationProposalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)/'state.sqlite'
        self.store = FranchiseStore(self.path)
        for team in ('a', 'b'):
            self.store.create_team(team, Ledger.from_opening(OpeningBooks(), cap=100,
                roster_reserve=0, max_bonus_years=5, veteran_minimums={'v': (1,), 'other': (1,)}))
        self.calls = 0
        self.enabled = True
        def access():
            if not self.enabled: raise AccessDisabled('Disabled')
        def provider(context):
            self.calls += 1
            self.assertEqual(context['decision_mode'], 'proposal')
            return json.dumps(dict(action='accept', reason='Agreement proposed', salaries=None, signing_bonus=None))
        self.provider = provider
        self.access = access
        self.bridge = Bridge(self.store, provider=provider, access_check=access)

    def request(self, **changes):
        return {**dict(protocol=1, request_id='proposal', operation='negotiate_proposal', team_id='a',
            offer=dict(player_id='v', salaries=[10], signing_bonus=0), expected_revision=0,
            timeout_ms=1000, personality={}, performance={'games': 16}, relationships={}), **changes}

    def test_acceptance_and_restart_preserve_finances_and_do_not_infer_twice(self):
        before = self.store.load_team('a').financial_snapshot()
        reply = self.bridge.handle(self.request())
        event = reply['result']
        self.assertIsNone(reply['error'])
        self.assertEqual(event['outcome'], 'accepted_proposal')
        self.assertEqual(event['decision_mode'], 'proposal')
        self.assertEqual(event['proposal_preview']['room_after'], 90)
        self.assertNotIn('charges', event)
        self.assertEqual(self.store.load_team('a').financial_snapshot(), before)
        reopened = FranchiseStore(self.path)
        bridge = Bridge(reopened, provider=self.provider, access_check=self.access)
        self.assertEqual(bridge.handle(self.request()), reply)
        self.assertEqual(self.calls, 1)
        self.assertEqual(reopened.negotiation_history('a', 'v'), [event])
        self.assertEqual(reopened.load_team('a').financial_snapshot(), before)
        self.enabled = False
        self.assertEqual(bridge.handle(self.request())['error'], 'ai_disabled')
        self.assertEqual(self.calls, 1)

    def test_retry_cannot_promote_proposal_to_signing_or_change_terms(self):
        self.bridge.handle(self.request())
        self.assertEqual(self.bridge.handle(self.request(operation='negotiate'))['error'], 'state_rejected')
        self.assertEqual(self.bridge.handle(self.request(offer=dict(player_id='v', salaries=[11], signing_bonus=0)))['error'], 'state_rejected')
        with self.assertRaises(Rejected): self.store.sign('a', 'proposal', Offer('v', (10,), 0), 0)
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.store.load_team('a').charges, (0,))
        self.assertEqual(self.store.load_team('a').revision, 0)

    def test_retry_rechecks_local_revision_and_foreign_ownership(self):
        self.bridge.handle(self.request())
        self.store.sign('b', 'foreign', Offer('v', (10,), 0), 0)
        self.assertEqual(self.bridge.handle(self.request())['error'], 'state_rejected')
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.store.load_team('a').revision, 0)
        self.store.sign('a', 'changed', Offer('other', (10,), 0), 0)
        self.assertEqual(self.bridge.handle(self.request())['error'], 'state_rejected')
        self.assertEqual(self.calls, 1)

    def test_over_cap_acceptance_records_rejection_without_ownership(self):
        reply = self.bridge.handle(self.request(offer=dict(player_id='v', salaries=[101], signing_bonus=0)))
        self.assertEqual(reply['result']['outcome'], 'accounting_rejected')
        self.assertNotIn('proposal_preview', reply['result'])
        self.assertEqual(self.store.load_team('a').financial_snapshot()['signed_players'], [])
        self.assertEqual(self.store.load_team('a').charges, (0,))

    def test_reject_and_counter_keep_the_proposal_mode_after_restart(self):
        for action in ('reject', 'counter'):
            with self.subTest(action=action):
                provider = lambda _: json.dumps(dict(action=action, reason='Proposal reply',
                    salaries=[12] if action=='counter' else None, signing_bonus=0 if action=='counter' else None))
                bridge = Bridge(self.store, provider=provider, access_check=self.access)
                request = self.request(request_id=action)
                reply = bridge.handle(request)
                self.assertEqual(reply['result']['decision_mode'], 'proposal')
                self.assertEqual(reply['result']['outcome'], 'counteroffer' if action=='counter' else 'player_rejected')
                reopened = Bridge(FranchiseStore(self.path), provider=lambda _: self.fail('Repeated inference'), access_check=self.access)
                self.assertEqual(reopened.handle(request), reply)
        self.assertEqual(self.store.load_team('a').revision, 0)

    def test_disable_during_model_call_never_records_or_commits(self):
        def provider(_):
            self.enabled = False
            return json.dumps(dict(action='accept', reason='Too late', salaries=None, signing_bonus=None))
        self.bridge.provider = provider
        self.assertEqual(self.bridge.handle(self.request())['error'], 'ai_disabled')
        self.assertEqual(self.store.negotiation_history('a', 'v'), [])
        self.assertEqual(self.store.load_team('a').charges, (0,))

    def test_tampered_durable_preview_is_rejected_by_financial_replay(self):
        self.bridge.handle(self.request())
        with closing(sqlite3.connect(self.path)) as db, db:
            payload = json.loads(db.execute("SELECT payload FROM events WHERE request_key='dialogue:proposal'").fetchone()[0])
            payload['event']['proposal_preview']['contract_charges'] = [9]
            db.execute("UPDATE events SET payload=? WHERE request_key='dialogue:proposal'", (json.dumps(payload),))
        with self.assertRaisesRegex(ValueError, 'financial replay'): self.store.load_team('a')

    def test_stale_initial_revision_cannot_invoke_model(self):
        self.assertEqual(self.bridge.handle(self.request(expected_revision=1))['error'], 'state_rejected')
        self.assertEqual(self.calls, 0)
