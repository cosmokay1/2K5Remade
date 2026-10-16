"""Actual opinion effects survive restart; retries and failed writes add none."""
import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.control import AccessDisabled
from franchise.negotiation import Decision, Negotiation
from franchise.store import FranchiseStore, StoredLedger


class NegotiationReactionTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name)/'franchise.sqlite'
        self.store = FranchiseStore(self.path)
        self.store.create_team('a', Ledger.from_opening(OpeningBooks(), cap=100,
            roster_reserve=0, max_bonus_years=5, veteran_minimums={'v': (1,), 'w': (1,)}))
        self.calls = 0
        self.contexts = []

    def session(self, store=None, player='v', respect=0.5):
        return Negotiation(StoredLedger(store or self.store, 'a'), player_id=player,
            personality={'patience': 0.5}, performance={'games': 16},
            relationships={'trust': 0.5, 'respect': respect}, access_check=lambda: None,
            proposal_only=True)

    def provider(self, context):
        self.calls += 1
        self.contexts.append(context)
        return json.dumps(dict(action='reject', reason='That offer does not take our concerns seriously.',
            salaries=None, signing_bonus=None, reaction='offended'))

    def offer(self, session, request='first', provider=None):
        return session.respond(request, Offer('v', (10,), 0), provider or self.provider, expected_revision=0)

    def test_reaction_is_atomic_persistent_once_only_and_next_offer_sees_it(self):
        session = self.session()
        before = self.store.load_team('a').financial_snapshot()
        event = self.offer(session)
        self.assertEqual(event['reaction_effect'], dict(policy='offer-reaction-v1',
            relationship='respect', before=0.5, after=0.45))
        self.assertEqual(self.offer(session), event)
        reopened = FranchiseStore(self.path)
        self.assertEqual(self.offer(self.session(reopened)), event)
        self.assertEqual(self.calls, 1)
        self.offer(self.session(reopened), 'next')
        self.assertEqual(self.contexts[-1]['relationships']['respect'], 0.45)
        self.assertEqual(self.contexts[-1]['history'][0]['reaction_effect']['after'], 0.45)
        actor = reopened.player_context('a', 'v')
        self.assertEqual(actor['relationships']['respect'], 0.4)
        self.assertEqual(reopened.load_team('a').financial_snapshot(), before)
        self.assertEqual(reopened.negotiation_history('a', 'w'), [])

    def test_neutral_bargaining_and_better_offer_do_not_erase_prior_offense(self):
        session = self.session()
        self.offer(session)
        neutral = lambda _: json.dumps(dict(action='counter', reason='We can continue at these terms.',
            salaries=[15], signing_bonus=0, reaction='none'))
        event = self.offer(session, 'improved', neutral)
        self.assertNotIn('reaction_effect', event)
        self.assertEqual(self.store.player_context('a', 'v')['relationships']['respect'], 0.45)
        self.assertEqual(event['outcome'], 'counteroffer')

    def test_disable_before_persist_leaves_neither_dialogue_nor_opinion(self):
        session = self.session()
        checks = 0
        def access():
            nonlocal checks
            checks += 1
            if checks == 3: raise AccessDisabled('Disabled after reaction before commit')
        def provider(context):
            response = self.provider(context)
            session._access_check = access
            return response
        with self.assertRaises(AccessDisabled): self.offer(session, provider=provider)
        self.assertEqual(self.store.negotiation_history('a', 'v'), [])
        self.assertEqual(self.store.player_context('a', 'v')['relationships']['respect'], 0.5)

    def test_inflight_other_dialogue_rejects_stale_reaction_without_double_effect(self):
        first, second = self.session(), self.session()
        def provider(context):
            self.offer(second, 'concurrent')
            return self.provider(context)
        with self.assertRaisesRegex(Rejected, 'stale negotiation history'):
            self.offer(first, provider=provider)
        self.assertEqual(len(self.store.negotiation_history('a', 'v')), 1)
        self.assertEqual(self.store.player_context('a', 'v')['relationships']['respect'], 0.45)

    def test_automatic_consequence_cannot_be_manually_applied_again(self):
        self.offer(self.session())
        with self.assertRaisesRegex(Rejected, 'already applied'):
            self.store.update_relationship('a', 'duplicate', 'v', 'respect', -0.05,
                source_request_id='first', expected_revision=0)
        self.assertEqual(self.store.player_context('a', 'v')['relationships']['respect'], 0.45)

    def test_tampered_effect_refuses_replay(self):
        self.offer(self.session())
        with closing(sqlite3.connect(self.path)) as db:
            payload = json.loads(db.execute("SELECT payload FROM events WHERE kind='dialogue'").fetchone()[0])
            payload['event']['reaction_effect']['after'] = 0.1
            db.execute("UPDATE events SET payload=? WHERE kind='dialogue'", (json.dumps(payload),))
            db.commit()
        with self.assertRaisesRegex(ValueError, 'reaction effect'):
            self.store.load_team('a')

    def test_missing_atomic_effect_marker_refuses_replay(self):
        self.offer(self.session())
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DELETE FROM events WHERE kind='offer_reaction'")
            db.commit()
        with self.assertRaisesRegex(ValueError, 'atomic opinion effect'):
            self.store.load_team('a')

    def test_failed_second_insert_rolls_back_dialogue_and_opinion(self):
        session = self.session()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TRIGGER refuse_reaction BEFORE INSERT ON events WHEN NEW.kind='offer_reaction' BEGIN SELECT RAISE(ABORT,'injected failure'); END")
            db.commit()
        with self.assertRaises(sqlite3.IntegrityError): self.offer(session)
        self.assertEqual(self.store.negotiation_history('a','v'), [])
        self.assertEqual(self.store.player_context('a','v')['relationships']['respect'],0.5)

    def test_neutral_legacy_and_invalid_reaction_parsing(self):
        base = dict(action='reject', reason='No agreement.', salaries=None, signing_bonus=None)
        self.assertEqual(Decision.parse(json.dumps(base), 'v').reaction, 'none')
        for change in ({'reaction':'unknown'}, {'reaction':True}, {'reaction':None},
                       {'action':'accept','reaction':'offended'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                Decision.parse(json.dumps({**base, **change}), 'v')

    def test_in_memory_matches_durable_policy_and_actor_is_not_rerolled(self):
        ledger = Ledger(cap=100, existing_charges=(0,), roster_reserve=0,
            max_bonus_years=5, veteran_minimums={'v': (1,)})
        session = Negotiation(ledger, player_id='v', personality={'patience':0.5},
            performance={}, relationships={'respect':0.02}, access_check=lambda: None,
            proposal_only=True)
        self.offer(session)
        self.offer(session, 'again')
        self.assertEqual(self.contexts[-1]['relationships']['respect'], 0)
        self.assertEqual(ledger.revision, 0)
        self.assertEqual(ledger.charges, (0,))
        with self.assertRaises(ValueError):
            ledger.bind_actor('v', {'rating':99}, {'respect':0.5}, access_check=lambda:None)
