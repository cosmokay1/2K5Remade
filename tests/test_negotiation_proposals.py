"""Game-facing decisions persist without creating a phantom signing."""
import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

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


    def game_request(self, **changes):
        from franchise.guest_contracts import GuestContractTerms
        self.store.create_team('game', Ledger.from_opening(OpeningBooks(), cap=100_000_000,
            roster_reserve=0, max_bonus_years=5, veteran_minimums={'v': (1000,)*15}))
        return self.request(team_id='game', contract_format='original_fxg_v1',
            offer=GuestContractTerms(829, 4, 1, 2).to_offer('v').to_dict(), **changes)

    def test_game_proposal_encoding_restart_and_format_replay_guard(self):
        request = self.game_request()
        before = self.store.load_team('game').financial_snapshot()
        event = self.bridge.handle(request)['result']
        self.assertEqual(event['outcome'], 'accepted_proposal')
        from franchise.guest_contracts import GuestContractTerms
        raw = event['guest_offer']
        self.assertEqual(GuestContractTerms.from_context(**raw).to_offer('v').to_dict(), request['offer'])
        self.assertIsNone(event['guest_counter'])
        reopened = Bridge(FranchiseStore(self.path), provider=lambda _: self.fail('Repeated inference'), access_check=self.access)
        self.assertEqual(reopened.handle(request)['result'], event)
        changed = dict(request); changed.pop('contract_format')
        self.assertEqual(reopened.handle(changed)['error'], 'state_rejected')
        self.assertEqual(self.store.load_team('game').financial_snapshot(), before)

    # Test format rejection independently of Windows runner scheduling; deadline
    # expiration has separate bridge tests with an advancing clock.
    @patch('franchise.bridge.time.monotonic', return_value=0)
    def test_game_proposal_refuses_unrepresentable_input_before_inference(self, _clock):
        request = self.game_request()
        request['offer']['salaries'][0] += 1
        self.assertEqual(self.bridge.handle(request)['error'], 'invalid_request')
        self.assertEqual(self.calls, 0)
        self.assertEqual(self.store.negotiation_history('game', 'v'), [])
        request['operation'] = 'negotiate'
        self.assertEqual(self.bridge.handle(request)['error'], 'invalid_request')

    def test_game_counter_preserves_demand_without_rounding_or_eligibility(self):
        request = self.game_request()
        before = self.store.load_team('game').financial_snapshot()
        def provider(context):
            self.assertEqual(context['contract_format'], 'original_fxg_v1')
            self.assertFalse(context['contract_format_constraints']['base_guarantees_supported'])
            return json.dumps(dict(action='counter', reason='My demand', salaries=[3_100_001, 1_860_000], signing_bonus=3_316_000))
        bridge = Bridge(self.store, provider=provider, access_check=self.access)
        event = bridge.handle(request)['result']
        self.assertEqual(event['counter']['salaries'][0], 3_100_001)
        self.assertEqual(event['counter_validation']['status'], 'ineligible')
        self.assertIsNone(event['guest_counter'])
        self.assertEqual(self.store.load_team('game').financial_snapshot(), before)
        self.assertEqual(Bridge(FranchiseStore(self.path), provider=lambda _: self.fail('Repeated inference'),
            access_check=self.access).handle(request)['result'], event)

    def test_game_compatible_counter_keeps_cap_validation(self):
        from franchise.guest_contracts import GuestContractTerms
        request = self.game_request()
        counter = GuestContractTerms(1000, 4, 2, 2).to_offer('v')
        bridge = Bridge(self.store, provider=lambda _: json.dumps(dict(action='counter', reason='Counter',
            salaries=list(counter.salaries), signing_bonus=counter.signing_bonus)), access_check=self.access)
        event = bridge.handle(request)['result']
        self.assertEqual(event['counter_validation']['status'], 'eligible')
        raw = event['guest_counter']
        self.assertEqual(GuestContractTerms.from_context(**raw).to_offer('v').to_dict(), counter.to_dict())
        self.assertEqual(self.store.load_team('game').revision, 0)
        huge = GuestContractTerms(20000, 0, 2, 1).to_offer('v')
        bridge.provider = lambda _: json.dumps(dict(action='counter', reason='Too much',
            salaries=list(huge.salaries), signing_bonus=0))
        request['request_id'] = 'overcap-counter'
        event = bridge.handle(request)['result']
        self.assertIsNotNone(event['guest_counter'])
        self.assertEqual(event['counter_validation']['status'], 'ineligible')
        self.assertIn('cap room', event['counter_validation']['reason'])
        self.assertEqual(self.store.load_team('game').revision, 0)

    def test_softdrink_counter_encoding_and_restart_preserve_scale(self):
        from franchise.guest_contracts import GuestContractTerms, SOFTDRINK_CONTRACT_FORMAT
        fmt=SOFTDRINK_CONTRACT_FORMAT
        request=self.game_request()
        request.update(contract_format=fmt,
            offer=GuestContractTerms(829,4,1,2).to_offer('v',contract_format=fmt).to_dict())
        counter=GuestContractTerms(1000,4,2,2).to_offer('v',contract_format=fmt)
        bridge=Bridge(self.store,provider=lambda _:json.dumps(dict(action='counter',reason='Counter',
            salaries=list(counter.salaries),signing_bonus=counter.signing_bonus)),access_check=self.access)
        before=self.store.load_team('game').financial_snapshot()
        reply=bridge.handle(request);self.assertIsNone(reply['error'])
        event=reply['result']
        self.assertEqual(event['contract_format'],fmt)
        self.assertEqual(event['guest_offer']['amount_word'],829)
        self.assertEqual(event['guest_counter']['amount_word'],1000)
        self.assertEqual(GuestContractTerms.from_context(**event['guest_counter']).to_offer(
            'v',contract_format=fmt),counter)
        reopened=Bridge(FranchiseStore(self.path),provider=lambda _:self.fail('Repeated inference'),
            access_check=self.access)
        self.assertEqual(reopened.handle(request),reply)
        self.assertEqual(self.store.load_team('game').financial_snapshot(),before)
        # Replaying with a false retail label cannot reinterpret persisted dollars.
        with closing(sqlite3.connect(self.path)) as db,db:
            payload=json.loads(db.execute("SELECT payload FROM events WHERE request_key='dialogue:proposal'").fetchone()[0])
            payload['event']['contract_format']='original_fxg_v1'
            db.execute("UPDATE events SET payload=? WHERE request_key='dialogue:proposal'",(json.dumps(payload),))
        with self.assertRaisesRegex(ValueError,'encoding|schedule'):self.store.load_team('game')

    def test_tampered_game_encoding_fails_durable_replay(self):
        request = self.game_request()
        self.bridge.handle(request)
        with closing(sqlite3.connect(self.path)) as db, db:
            payload = json.loads(db.execute("SELECT payload FROM events WHERE request_key='dialogue:proposal'").fetchone()[0])
            payload['event']['guest_offer']['amount_word'] += 1
            db.execute("UPDATE events SET payload=? WHERE request_key='dialogue:proposal'", (json.dumps(payload),))
        with self.assertRaisesRegex(ValueError, 'encoding'):
            self.store.load_team('game')
