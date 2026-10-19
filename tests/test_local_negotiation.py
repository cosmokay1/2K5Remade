import copy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest

from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer
from franchise.local_negotiation import LocalNegotiationProvider
from franchise.negotiation import Decision, Negotiation
from franchise.promises import PromiseGoal
from franchise.store import FranchiseStore, StoredLedger


class LocalNegotiationTests(unittest.TestCase):
    def context(self, offer=None, **updates):
        return {'player_id': 'p', 'offer': (offer or Offer('p', (1000,), 0)).to_dict(),
                'personality': {'money': 0.5, 'security': 0.5, 'patience': 0.5, 'loyalty': 0.5},
                'relationships': {'trust': 0.5, 'respect': 0.5},
                'performance': {}, 'history': [], 'promise_goals': [], **updates}

    def decide(self, provider, context):
        return Decision.parse(provider(context), 'p')

    def test_accept_preserves_terms_context_and_stable_voice(self):
        provider = LocalNegotiationProvider(Offer('p', (1000,), 0))
        context = self.context(); before = copy.deepcopy(context)
        first = provider(context)
        self.assertEqual(first, provider(context))
        self.assertEqual(Decision.parse(first, 'p').action, 'accept')
        self.assertIsNone(Decision.parse(first, 'p').counter)
        self.assertNotIn('signed', json.loads(first)['reason'])
        self.assertEqual(context, before)

    def test_money_and_existing_relationship_change_small_concessions(self):
        provider = LocalNegotiationProvider(Offer('p', (1000,), 0))
        context = self.context(Offer('p', (970,), 0),
                               relationships={'trust': 1, 'respect': 1})
        context['personality'].update(money=0, loyalty=1)
        self.assertEqual(self.decide(provider, context).action, 'accept')
        context['personality']['money'] = 1
        self.assertEqual(self.decide(provider, context).action, 'counter')

    def test_headline_money_does_not_replace_security(self):
        provider = LocalNegotiationProvider(Offer('p', (1000,), 200))
        no_security = self.decide(provider, self.context(Offer('p', (1200,), 0)))
        self.assertEqual(no_security.action, 'counter')
        self.assertEqual(no_security.counter.signing_bonus, 200)
        protected = Offer('p', (1200,), 0, (200,))
        self.assertEqual(self.decide(provider, self.context(protected)).action, 'accept')

    def test_different_term_does_not_compare_total_to_longer_deal_as_lowball(self):
        provider = LocalNegotiationProvider(Offer('p', (1000, 1000, 1000), 0))
        decision = self.decide(provider, self.context())
        self.assertEqual(decision.action, 'counter')
        self.assertEqual(decision.reaction, 'none')
        self.assertEqual(decision.counter.salaries, (1000, 1000, 1000))

    def test_counter_preserves_explicit_promise_proposals(self):
        provider = LocalNegotiationProvider(Offer('p', (1000,), 0))
        goal = asdict(PromiseGoal('starts', 'starts', 10, 80, 'season-1', 'test proposal'))
        context = self.context(Offer('p', (800,), 0), promise_goals=[goal])
        decision = self.decide(provider, context)
        self.assertEqual(decision.action, 'counter')
        self.assertEqual([asdict(x) for x in decision.counter_promises], [goal])

    def test_patience_limits_the_explicit_window_without_new_offense(self):
        context = self.context()
        context['personality']['patience'] = 0
        context['history'] = [dict(request_id=str(i), offer=Offer('p', (800,), 0).to_dict(),
                                   action='counter', reaction='none') for i in range(2)]
        provider = LocalNegotiationProvider(Offer('p', (1000,), 0))
        result = self.decide(provider, context)
        self.assertEqual((result.action, result.reaction), ('reject', 'none'))
        context['personality']['patience'] = 1
        self.assertEqual(self.decide(provider, context).action, 'accept')

    def test_incompatible_identity_hidden_ratings_and_invalid_traits_reject(self):
        provider = LocalNegotiationProvider(Offer('p', (1000,), 0))
        cases = []
        c = self.context(); c['player_id'] = 'other'; cases.append(c)
        c = self.context(); c['performance'] = {'catching_rating': 99}; cases.append(c)
        c = self.context(); c['personality']['money'] = float('nan'); cases.append(c)
        c = self.context(); c['relationships'].pop('respect'); cases.append(c)
        for context in cases:
            with self.subTest(context=context), self.assertRaises(ValueError):
                provider(context)

    def test_corrupt_or_foreign_history_and_unavailable_cursor_reject(self):
        provider = LocalNegotiationProvider(Offer('p', (1000,), 0))
        event = dict(request_id='old', offer=Offer('p', (800,), 0).to_dict())
        for history in [[event, event], [dict(event, offer=Offer('other', (800,), 0).to_dict())]]:
            with self.assertRaises(ValueError): provider(self.context(history=history))
        with self.assertRaises(ValueError):
            LocalNegotiationProvider(Offer('p', (1000,), 0), history_start=1)(self.context())
        for demand, cursor in [(Offer('p', (0,), 0), 0), (Offer('p', (1,), 0), True)]:
            with self.assertRaises(ValueError): LocalNegotiationProvider(demand, cursor)


class LocalNegotiationLedgerTests(unittest.TestCase):
    def session(self, ledger, **options):
        return Negotiation(ledger, player_id='p', personality={'patience': 0.5},
                           performance={}, relationships={'trust': 0.5, 'respect': 0.5},
                           access_check=lambda: None, **options)

    def ledger(self, cap=1000, minimum=1):
        return Ledger.from_opening(OpeningBooks(), cap=cap, roster_reserve=0,
                                   max_bonus_years=5, veteran_minimums={'p': (minimum,)})

    def test_local_acceptance_still_cannot_override_cap_or_minimum(self):
        for cap, minimum, salary in [(50, 1, 100), (1000, 100, 50)]:
            session = self.session(self.ledger(cap, minimum)); before = session.ledger.financial_snapshot()
            offer = Offer('p', (salary,), 0)
            result = session.respond('local', offer, LocalNegotiationProvider(offer))
            self.assertEqual(result['action'], 'accept')
            self.assertEqual(result['outcome'], 'accounting_rejected')
            self.assertEqual(session.ledger.financial_snapshot(), before)

    def test_counter_does_not_lower_the_asking_price_to_fit_team_cap(self):
        session = self.session(self.ledger(cap=50))
        result = session.respond('local', Offer('p', (80,), 0),
                                 LocalNegotiationProvider(Offer('p', (100,), 0)))
        self.assertEqual(result['outcome'], 'counteroffer')
        self.assertEqual(result['counter']['salaries'], [100])
        self.assertEqual(result['counter_validation']['status'], 'ineligible')

    def test_signed_receipt_is_replayed_without_another_charge_or_provider_call(self):
        session = self.session(self.ledger()); offer = Offer('p', (100,), 0)
        first = session.respond('local', offer, LocalNegotiationProvider(offer))
        self.assertEqual(first['outcome'], 'signed')
        def unexpected(_): self.fail('Local provider called again for a completed request')
        self.assertEqual(session.respond('local', offer, unexpected), first)
        self.assertEqual(session.ledger.charges, (100,))

    def test_lowball_and_refusal_survive_store_restart_without_double_penalty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'franchise.sqlite'
            store = FranchiseStore(path); store.create_team('club', self.ledger())
            session = self.session(StoredLedger(store, 'club'), proposal_only=True)
            provider = LocalNegotiationProvider(Offer('p', (100,), 0))
            first = session.respond('lowball', Offer('p', (50,), 0), provider, expected_revision=0)
            self.assertEqual(first['reaction'], 'offended')
            reopened = FranchiseStore(path)
            session = self.session(StoredLedger(reopened, 'club'), proposal_only=True)
            self.assertEqual(session.respond('lowball', Offer('p', (50,), 0), provider,
                                            expected_revision=0), first)
            better = session.respond('better', Offer('p', (100,), 0), provider, expected_revision=0)
            self.assertEqual(better['outcome'], 'player_rejected')
            self.assertEqual(better['reaction'], 'none')
            self.assertEqual(reopened.player_context('club', 'p')['relationships']['respect'], 0.45)
            self.assertEqual(reopened.load_team('club').charges, (0,))
            # Explicitly opening a new window is a separate caller decision;
            # constructing another provider with cursor zero does not do it.
            next_window = LocalNegotiationProvider(Offer('p', (100,), 0), history_start=2)
            result = session.respond('new-window', Offer('p', (100,), 0), next_window,
                                     expected_revision=0)
            self.assertEqual(result['outcome'], 'accepted_proposal')
            self.assertEqual(reopened.load_team('club').charges, (0,))
