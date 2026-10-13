from dataclasses import replace
from fractions import Fraction
import json
import unittest
from franchise.books import ActiveContract, ChargeRecord, OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.cash import CashBook
from tests import test_releases as release_fixtures


class ReleaseLedgerTests(unittest.TestCase):
    def setUp(self):
        self.fixture = release_fixtures.PreseasonReleaseTests()

    def ledger(self, *, cap=100, retained_id='existing-debt'):
        books = OpeningBooks(contracts=(self.fixture.contract(),
            ActiveContract(Offer('other', (5, 6, 7, 8), 0), 'other synthetic contract')),
            retained=(ChargeRecord(retained_id, (2, 3, 4, 5, 6), 'synthetic retained debt'),))
        ledger = Ledger.from_opening(books, cap=cap, roster_reserve=0, max_bonus_years=5,
            veteran_minimums={'v': (1, 1, 1), 'other': (1, 1, 1, 1), 'free': (1,)})
        ledger._cash = CashBook((self.fixture.cash(),), 'synthetic allocated cash')
        return ledger

    def release(self, ledger, **changes):
        plan = self.fixture.plan()
        args = dict(scope=plan.scope, discount=plan.discount, payment_year_offsets=plan.payment_year_offsets,
                    record_id='release:v', expected_revision=0)
        args.update(changes)
        return ledger.apply_preseason_release('v', **args)

    def test_replaces_only_active_row_and_archives_original_terms_and_cash(self):
        ledger = self.ledger()
        self.assertNotIn('released_contracts', ledger.financial_snapshot())
        plan = self.release(ledger)
        self.assertEqual(ledger.charges, (46, 9, 11, 13, 6))
        self.assertEqual(ledger.revision, 1)
        self.assertEqual(ledger._cash.revision, 1)
        self.assertEqual(ledger._contracts['v'], self.fixture.contract().offer)
        self.assertEqual(ledger._released['v'], plan)
        self.assertNotIn('v', ledger._players)
        self.assertNotIn('v', ledger._active_contracts)
        self.assertEqual(ledger._cash.records['contract:v'].amount, 39)
        saved = ledger.financial_snapshot()['released_contracts']['v']
        self.assertEqual(saved['cancelled_unearned_base'], 30)
        self.assertEqual(saved['original_cash']['amount'], 69)
        self.assertEqual(saved['scope']['removed_on'], '2026-06-01')
        self.assertEqual(saved['original_contract']['offer']['guaranteed_salaries'], [0, 20, 10])
        json.dumps(saved, allow_nan=False)
        with self.assertRaises(Rejected):
            ledger.active_contract('v')
        with self.assertRaisesRegex(Rejected, 'generation IDs'):
            ledger.preview_offer(Offer('v', (1,), 0), 1)

    def test_overcap_acceleration_preserves_debt_and_blocks_new_signings(self):
        ledger = self.ledger(cap=25)
        self.release(ledger)
        self.assertEqual(ledger.charges[0], 46)
        with self.assertRaises(Rejected):
            ledger.sign('new', Offer('free', (1,), 0), 1)

    def test_release_cannot_reuse_original_retained_record_identity(self):
        ledger=self.ledger(retained_id='release:v:bonus')
        before,cash=ledger.financial_snapshot(),ledger.cash_snapshot()
        with self.assertRaisesRegex(Rejected,'identity already exists'):self.release(ledger)
        self.assertEqual(ledger.financial_snapshot(),before)
        self.assertEqual(ledger.cash_snapshot(),cash)

    def test_failures_leave_finances_cash_ownership_and_original_contract_unchanged(self):
        ledger = self.ledger()
        before, cash_before = ledger.financial_snapshot(), ledger.cash_snapshot()
        for changes in ({'expected_revision': True}, {'expected_revision': 1},
                        {'payment_year_offsets': (0,)}, {'scope': None}):
            with self.subTest(changes=changes), self.assertRaises((Rejected, ValueError)):
                self.release(ledger, **changes)
            self.assertEqual(ledger.financial_snapshot(), before)
            self.assertEqual(ledger.cash_snapshot(), cash_before)
            self.assertEqual(ledger.active_contract('v'), self.fixture.contract())
        ledger._cash.records['contract:v'] = replace(self.fixture.cash(), paid_components=None)
        with self.assertRaises(ValueError):
            self.release(ledger)
        self.assertEqual(ledger.financial_snapshot(), before)
        ledger._cash = None
        with self.assertRaises(Rejected):
            self.release(ledger)

    def test_repeat_release_and_unknown_or_rookie_classification_reject(self):
        ledger = self.ledger()
        self.release(ledger)
        before = ledger.financial_snapshot()
        with self.assertRaises(Rejected):
            self.release(ledger, expected_revision=1)
        self.assertEqual(ledger.financial_snapshot(), before)
        other = self.ledger()
        other._rookies['v'] = object()
        with self.assertRaisesRegex(Rejected, 'veteran classification'):
            self.release(other)
