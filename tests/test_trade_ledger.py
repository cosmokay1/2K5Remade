from dataclasses import replace
import json
import unittest
from franchise.books import ActiveContract, ChargeRecord, OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.cash import CashBook
from tests import test_trades as trade_fixtures


class TradeLedgerTests(unittest.TestCase):
    def setUp(self):
        self.fixture = trade_fixtures.PreseasonTradeTests()

    def seller(self, retained=()):
        ledger = Ledger.from_opening(OpeningBooks(contracts=(self.fixture.contract(),), retained=retained),
            cap=100, roster_reserve=0, max_bonus_years=5, veteran_minimums={'v': (1, 1, 1)})
        ledger._cash = CashBook((self.fixture.cash(),), 'synthetic seller cash')
        return ledger

    def buyer(self, cap=100, floors=(1, 1, 1)):
        ledger = Ledger.from_opening(OpeningBooks(), cap=cap, roster_reserve=0,
            max_bonus_years=5, veteran_minimums={'v': floors})
        ledger._cash = CashBook((), 'synthetic buyer cash')
        return ledger

    def outgoing(self, seller, **changes):
        args = dict(scope=self.fixture.scope(), record_id='trade:v', expected_revision=0)
        args.update(changes)
        return seller.apply_preseason_trade_out('v', **args)

    def test_both_books_preserve_cash_guarantees_original_history_and_ownership(self):
        seller, buyer = self.seller(), self.buyer()
        plan = self.outgoing(seller)
        buyer.apply_preseason_trade_in(plan, expected_revision=0)
        self.assertEqual(seller.charges, (9, 0, 0))
        self.assertEqual(buyer.charges, (10, 20, 30))
        self.assertEqual(seller._players, set())
        self.assertEqual(buyer._players, {'v'})
        self.assertEqual(seller._contracts['v'], self.fixture.contract().offer)
        self.assertEqual(buyer.active_contract('v').offer.guaranteed_salaries, (0, 20, 10))
        self.assertEqual(seller.guarantee_cash('v')['unpaid_signing_bonus'], 0)
        self.assertEqual(sum(seller.guarantee_cash('v')['unpaid_guaranteed_base_by_original_year']), 0)
        self.assertEqual(sum(buyer.guarantee_cash('v')['unpaid_guaranteed_base_by_original_year']), 30)
        self.assertEqual(seller._cash.snapshot()['nominal_total'] + buyer._cash.snapshot()['nominal_total'], 69)
        self.assertEqual((seller.revision, buyer.revision, seller._cash.revision, buyer._cash.revision), (1, 1, 1, 1))
        outgoing = seller.financial_snapshot()['outgoing_trades']['v']
        incoming = buyer.financial_snapshot()['incoming_trades']['v']
        self.assertEqual(outgoing, incoming)
        self.assertEqual(outgoing['original_cash']['amount'], 69)
        self.assertEqual(outgoing['assigned_base'], 60)
        json.dumps(outgoing, allow_nan=False)
        with self.assertRaisesRegex(Rejected, 'generation IDs'):
            seller.preview_offer(Offer('v', (1,), 0), 1)

    def test_buyer_floor_and_current_cap_failures_have_no_mutation(self):
        plan = self.outgoing(self.seller())
        for buyer in (self.buyer(cap=9), self.buyer(floors=(11, 20, 30))):
            before, cash = buyer.financial_snapshot(), buyer.cash_snapshot()
            with self.assertRaises(Rejected):
                buyer.apply_preseason_trade_in(plan, expected_revision=0)
            self.assertEqual(buyer.financial_snapshot(), before)
            self.assertEqual(buyer.cash_snapshot(), cash)
        buyer = self.buyer()
        buyer._cash = None
        with self.assertRaises(Rejected):
            buyer.apply_preseason_trade_in(plan, expected_revision=0)

    def test_incoming_plan_tampering_prior_contract_and_repeat_reject(self):
        plan = self.outgoing(self.seller())
        buyer = self.buyer()
        before = buyer.financial_snapshot()
        with self.assertRaisesRegex(ValueError, 'original obligations'):
            buyer.apply_preseason_trade_in(replace(plan, assigned_base=59), expected_revision=0)
        self.assertEqual(buyer.financial_snapshot(), before)
        buyer._contracts['v'] = Offer('v', (1,), 0)
        with self.assertRaisesRegex(Rejected, 'generation IDs'):
            buyer.apply_preseason_trade_in(plan, expected_revision=0)
        buyer = self.buyer()
        buyer.apply_preseason_trade_in(plan, expected_revision=0)
        with self.assertRaises(Rejected):
            buyer.apply_preseason_trade_in(plan, expected_revision=1)

    def test_outgoing_stale_unknown_cash_record_collision_and_rookie_failures(self):
        seller = self.seller()
        before, cash = seller.financial_snapshot(), seller.cash_snapshot()
        for changes in ({'expected_revision': True}, {'expected_revision': 1}, {'scope': None}):
            with self.subTest(changes=changes), self.assertRaises((ValueError, Rejected)):
                self.outgoing(seller, **changes)
            self.assertEqual(seller.financial_snapshot(), before)
            self.assertEqual(seller.cash_snapshot(), cash)
        collision = self.seller((ChargeRecord('trade:v:seller-bonus', (2,), 'synthetic collision'),))
        with self.assertRaisesRegex(Rejected, 'record identity'):
            self.outgoing(collision)
        seller._cash = None
        with self.assertRaises(Rejected):
            self.outgoing(seller)
        seller = self.seller()
        seller._rookies['v'] = object()
        with self.assertRaisesRegex(Rejected, 'veteran classification'):
            self.outgoing(seller)
