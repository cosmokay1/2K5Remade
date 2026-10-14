from dataclasses import replace
import unittest
from franchise.trades import calculate_preseason_trade
from tests import test_releases, test_restructures, test_trades


class GenerationCalculatorTests(unittest.TestCase):
    def cases(self):
        release=test_releases.PreseasonReleaseTests()
        restructure=test_restructures.PreseasonRestructureTests()
        trade=test_trades.PreseasonTradeTests()
        return ((release,release.plan), (restructure,restructure.plan),
            (trade,lambda **kwargs:calculate_preseason_trade(trade.contract(),kwargs.pop('cash',trade.cash()),
                scope=trade.scope(),record_id='trade:v',**kwargs)))

    def test_explicit_generation_identity_preserves_cash_and_cap_math(self):
        for fixture,calculate in self.cases():
            with self.subTest(calculator=type(fixture).__name__):
                original=calculate()
                cash=replace(fixture.cash(),obligation_id='contract-gen:second')
                changed=calculate(cash=cash,expected_cash_id='contract-gen:second')
                self.assertEqual(changed.original_cash,cash)
                if hasattr(changed,'seller_cash'):
                    self.assertEqual(changed.seller_cash.obligation_id,'contract-gen:second')
                    self.assertEqual(changed.buyer_cash.obligation_id,'contract-gen:second')
                    self.assertEqual(changed.retained_bonus,original.retained_bonus)
                    self.assertEqual(changed.buyer_contract,original.buyer_contract)
                else:
                    self.assertEqual(changed.cash_obligation.obligation_id,'contract-gen:second')
                    self.assertEqual(changed.cash_obligation.amount,original.cash_obligation.amount)
                    self.assertEqual(changed.cash_obligation.paid_components,original.cash_obligation.paid_components)
                    if hasattr(changed,'contract'):
                        self.assertEqual(changed.contract,original.contract)
                    else:
                        self.assertEqual(changed.charges(),original.charges())

    def test_no_inference_of_identity_or_relaxation_of_player_matching(self):
        for fixture,calculate in self.cases():
            for cash,expected in ((replace(fixture.cash(),obligation_id='foreign'),None),
                                  (fixture.cash(),'foreign'),
                                  (replace(fixture.cash(),player_id='other'),'contract:v')):
                with self.subTest(calculator=type(fixture).__name__,expected=expected),self.assertRaises(ValueError):
                    calculate(cash=cash,expected_cash_id=expected)
            for expected in ('',' ',True,1,[],{}):
                with self.subTest(expected=expected),self.assertRaises(ValueError):
                    calculate(expected_cash_id=expected)

    def test_trade_destination_identity_is_separate_and_preserves_conservation(self):
        fixture=test_trades.PreseasonTradeTests()
        cash=replace(fixture.cash(),obligation_id='contract-gen:seller')
        plan=calculate_preseason_trade(fixture.contract(),cash,scope=fixture.scope(),record_id='trade:v',
            expected_cash_id='contract-gen:seller',buyer_cash_id='contract-gen:buyer')
        self.assertEqual(plan.seller_cash.obligation_id,cash.obligation_id)
        self.assertEqual(plan.buyer_cash.obligation_id,'contract-gen:buyer')
        self.assertEqual(plan.seller_cash.amount+plan.buyer_cash.amount,cash.amount)
        for identity in ('',' ',False,5,[]):
            with self.subTest(identity=identity),self.assertRaises(ValueError):
                calculate_preseason_trade(fixture.contract(),fixture.cash(),scope=fixture.scope(),
                    record_id='trade:v',buyer_cash_id=identity)

    def test_cash_creation_separates_agreements_without_overwriting_old_obligations(self):
        from franchise.cash import CashBook
        from franchise.cap import Offer, Rejected
        book=CashBook((),'synthetic coverage')
        offer=Offer('v',(10,),2)
        book.add_contract(offer,'original')
        book.add_contract(offer,'later',obligation_id='contract-gen:second')
        self.assertEqual(set(book.records),{'contract:v','contract-gen:second'})
        self.assertEqual(book.records['contract:v'].source,'original')
        before=book.snapshot()
        with self.assertRaises(Rejected):
            book.add_contract(offer,'duplicate',obligation_id='contract-gen:second')
        for identity in ('',' ',True,7,[]):
            with self.subTest(identity=identity),self.assertRaises(ValueError):
                book.add_contract(offer,'bad',obligation_id=identity)
        self.assertEqual(book.snapshot(),before)
