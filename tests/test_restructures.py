from dataclasses import asdict, replace
from datetime import date
from fractions import Fraction
import unittest
from franchise.books import ActiveContract, BonusLayer, OpeningBooks
from franchise.cap import Ledger, Offer
from franchise.cash import CashObligation
from franchise.restructures import EXCLUDED_RESTRUCTURE_TERMS, PreseasonRestructureScope, calculate_preseason_restructure


class PreseasonRestructureTests(unittest.TestCase):
    def scope(self):
        return PreseasonRestructureScope(2026,date(2026,6,1),date(2026,9,10),0,True,True,True,
            EXCLUDED_RESTRUCTURE_TERMS,'synthetic annual floors','synthetic guaranteed-base amendment')

    def contract(self):
        return ActiveContract(Offer('v',(10,10,10,20,30,40,50),10,(10,10,10,20,0,0,0)),
                              'synthetic seven-year original',elapsed_years=2)

    def cash(self):
        return CashObligation('contract:v','v',180,30,'synthetic allocated cash',
                              (('signing_bonus',10),('base:0',10),('base:1',10)))

    def plan(self,**changes):
        args=dict(scope=self.scope(),converted_base=8,annual_minimums=(2,2,2,2,2),record_id='restructure:v')
        args.update(changes)
        return calculate_preseason_restructure(args.pop('contract',self.contract()),args.pop('cash',self.cash()),**args)

    def test_elapsed_original_bonus_schedule_is_not_combined_or_reset(self):
        plan=self.plan()
        self.assertEqual(plan.contract.charges(),tuple(Fraction(n,5) for n in (28,118,168,208,258)))
        wrong=tuple(Fraction(base)+Fraction(14,5) for base in (2,20,30,40,50))
        self.assertNotEqual(plan.contract.charges(),wrong)
        self.assertEqual(sum(plan.contract.charges()),sum(self.contract().charges()))
        self.assertEqual(plan.contract.offer.signing_bonus,10)
        self.assertEqual(plan.bonus_layer.original_start_index,2)
        self.assertEqual(plan.bonus_layer.allocation_years,5)
        self.assertEqual(plan.contract.offer.guaranteed_salaries,(10,10,2,20,0,0,0))
        self.assertEqual(plan.contract.offer.salaries,(10,10,2,20,30,40,50))

    def test_nominal_cash_and_paid_history_stay_unchanged_new_bonus_is_unpaid(self):
        plan=self.plan()
        self.assertEqual((plan.cash_obligation.amount,plan.cash_obligation.paid),(180,30))
        self.assertEqual(plan.cash_obligation.paid_components,self.cash().paid_components)
        self.assertEqual(plan.bonus_layer.cash_component,'bonus:restructure:v')
        self.assertNotIn(plan.bonus_layer.cash_component,dict(plan.cash_obligation.paid_components))
        self.assertEqual(plan.original_contract,self.contract())
        self.assertEqual(plan.original_cash,self.cash())

    def test_bonus_layer_roundtrip_and_legacy_shape(self):
        old=self.contract()
        self.assertNotIn('bonus_layers',old.to_dict())
        self.assertEqual(ActiveContract.from_dict(old.to_dict()),old)
        books=OpeningBooks(contracts=(self.plan().contract,))
        self.assertEqual(OpeningBooks.from_dict(books.to_dict()),books)
        with self.assertRaises(ValueError):
            Ledger.from_opening(books,cap=200,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*5})
        from franchise.rookie_opening import RookiePoolOpening
        with self.assertRaisesRegex(ValueError,'Layered rookie'):
            RookiePoolOpening(2026,frozenset({'v'}),100,200,0,'synthetic cohort',(self.plan().contract,))

    def test_layers_reject_duplicate_ids_out_of_term_and_mutable_rows(self):
        layer=self.plan().bonus_layer
        for layers in ([layer],(layer,layer),(replace(layer,allocation_years=5,original_start_index=3),)):
            with self.subTest(layers=layers),self.assertRaises(ValueError):
                replace(self.contract(),bonus_layers=layers)
        with self.assertRaises(ValueError):
            BonusLayer('layer',True,0,1,'source')
        for fields in ({'record_id':'incomplete'},{**asdict(layer),'extra':1}):
            with self.assertRaises(ValueError):
                BonusLayer.from_dict(fields)

    def test_unknown_cash_paid_base_nonprotected_base_and_minimum_failures(self):
        for changes in ({'cash':replace(self.cash(),paid_components=None)},
                        {'cash':replace(self.cash(),paid=29,paid_components=(('signing_bonus',9),('base:0',10),('base:1',10)))},
                        {'cash':replace(self.cash(),paid=31,paid_components=self.cash().paid_components+(('base:2',1),))},
                        {'contract':replace(self.contract(),offer=replace(self.contract().offer,guaranteed_salaries=(10,10,9,20,0,0,0)))},
                        {'converted_base':9},{'converted_base':False},{'annual_minimums':(2,)},
                        {'contract':self.plan().contract}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                self.plan(**changes)

    def test_scope_facts_cannot_be_omitted_or_cross_final_year(self):
        for changes in ({'healthy':False},{'consent':1},{'renegotiation_eligible':False},
                        {'current_year_earned_base':False},{'current_year_earned_base':1},
                        {'minimum_source':''},{'exclusions':EXCLUDED_RESTRUCTURE_TERMS-{'guarantee_voids'}}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                replace(self.scope(),**changes)
        fields=asdict(self.scope())
        del fields['healthy']
        with self.assertRaises(TypeError):
            PreseasonRestructureScope(**fields)
        scope=replace(self.scope(),league_year=2030,amended_on=date(2030,6,1),first_regular_season_game=date(2030,9,10))
        with self.assertRaisesRegex(ValueError,'final-CBA'):
            self.plan(scope=scope)

    def test_release_and_trade_reject_layers_before_cash_or_debt_can_be_lost(self):
        from franchise.releases import calculate_preseason_release
        from franchise.trades import calculate_preseason_trade
        from tests import test_releases,test_trades
        release=test_releases.PreseasonReleaseTests().plan()
        trade=test_trades.PreseasonTradeTests().scope()
        plan=self.plan()
        with self.assertRaisesRegex(ValueError,'Layered contract release'):
            calculate_preseason_release(plan.contract,plan.cash_obligation,scope=release.scope,
                discount=release.discount,payment_year_offsets=(0,)*5,record_id='release')
        with self.assertRaisesRegex(ValueError,'Layered contract trade'):
            calculate_preseason_trade(plan.contract,plan.cash_obligation,scope=trade,record_id='trade')
