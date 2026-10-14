from dataclasses import FrozenInstanceError,replace
from fractions import Fraction
import unittest
from franchise.books import ActiveContract,BonusLayer
from franchise.cap import Offer
from franchise.cash import CashObligation
from franchise.generations import GenerationAgreement,GenerationCalendarView,legacy_identity,project_agreement
from tests import test_releases,test_trades,test_restructures


class GenerationCalendarViewTests(unittest.TestCase):
    def agreement(self):
        contract=ActiveContract(Offer('p',(10,20,30),9,(0,20,0)),'synthetic original',elapsed_years=1,
            bonus_layers=(BonusLayer('layer',6,1,2,'synthetic conversion'),))
        return GenerationAgreement(legacy_identity('a','p'),contract,contract)

    def cash(self):
        return CashObligation('contract:p','p',75,75,'synthetic full settlement',
            (('signing_bonus',9),('bonus:layer',6),('base:0',10),('base:1',20),('base:2',30)))

    def test_layered_current_view_preserves_economics_original_indices_and_legacy_projection(self):
        agreement=self.agreement();view=GenerationCalendarView(agreement,2026,2027)
        self.assertEqual(view.current_contract.elapsed_years,2)
        self.assertEqual(view.current_contract.bonus_layers,agreement.contract.bonus_layers)
        self.assertEqual(view.current_contract.offer,agreement.contract.offer)
        self.assertEqual(view.annual_charges(),(Fraction(36),))
        self.assertEqual(view.to_projection(),project_agreement(agreement,years_forward=1))
        self.assertEqual(view.payment_ceilings(),agreement.payment_ceilings())
        self.assertIs(view.agreement,agreement)
        self.assertEqual(agreement.contract.elapsed_years,1)
        with self.assertRaises(FrozenInstanceError):view.current_year=2028

    def test_schedule_exhaustion_alone_never_expires_or_settles_unpaid_cash(self):
        agreement=self.agreement();view=GenerationCalendarView(agreement,2026,2028)
        unpaid=replace(self.cash(),paid=45,paid_components=(('signing_bonus',9),('bonus:layer',6),('base:0',10),('base:1',20)))
        self.assertTrue(view.scheduled_term_complete)
        self.assertFalse(view.authoritative_expired);self.assertEqual(view.status,'active')
        self.assertIsNone(view.current_contract);self.assertEqual(view.annual_charges(),())
        self.assertEqual(view.payment_ceilings()['base:2'],30)
        self.assertEqual(unpaid.amount-unpaid.paid,30)
        with self.assertRaises(ValueError):
            GenerationCalendarView(agreement,2026,2028,expiry_eligible=True,expiry_cash=unpaid,expiry_source='synthetic eligible close')

    def test_explicit_eligible_settled_expiry_archives_facts_without_touching_source_agreement(self):
        agreement=self.agreement();cash=self.cash()
        view=GenerationCalendarView(agreement,2026,2028,expiry_eligible=True,expiry_cash=cash,expiry_source='synthetic verified eligibility')
        self.assertTrue(view.authoritative_expired);self.assertEqual(view.status,'expired')
        self.assertEqual(agreement.status,'active');self.assertIs(view.agreement,agreement)
        self.assertEqual(view.expiry_cash,cash);self.assertEqual(view.payment_ceilings()['base:0'],10)
        self.assertIsNone(view.current_contract)

    def test_unknown_partial_foreign_or_ineligible_expiry_facts_reject(self):
        agreement=self.agreement();facts=dict(expiry_eligible=True,expiry_cash=self.cash(),expiry_source='synthetic close')
        for changes in ({'expiry_eligible':None},{'expiry_eligible':False},{'expiry_eligible':1},
                        {'expiry_cash':None},{'expiry_source':None},{'expiry_source':''},
                        {'expiry_cash':replace(self.cash(),paid_components=None)},
                        {'expiry_cash':replace(self.cash(),obligation_id='foreign')},
                        {'expiry_cash':replace(self.cash(),player_id='foreign')}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                GenerationCalendarView(agreement,2026,2028,**{**facts,**changes})
        # Equal total paid cannot disguise an overpayment of one component and
        # an unpaid remainder of another component.
        misallocated=replace(self.cash(),paid_components=(('signing_bonus',10),('bonus:layer',6),
            ('base:0',9),('base:1',20),('base:2',30)))
        with self.assertRaises(ValueError):
            GenerationCalendarView(agreement,2026,2028,**{**facts,'expiry_cash':misallocated})
        with self.assertRaises(ValueError):GenerationCalendarView(agreement,2026,2027,**facts)
        for years in ((True,2027),(2026,2025),(2026,2031)):
            with self.assertRaises(ValueError):GenerationCalendarView(agreement,*years)

    def test_released_and_assigned_projection_keeps_closed_payment_ceilings_and_plans(self):
        release=test_releases.PreseasonReleaseTests().plan()
        agreement=GenerationAgreement(legacy_identity('a',release.original_contract.offer.player_id),
            release.original_contract,release.original_contract,release=release)
        view=GenerationCalendarView(agreement,2026,2027)
        self.assertEqual(view.annual_charges(),release.charges()[1:])
        self.assertEqual(view.payment_ceilings(),agreement.payment_ceilings())
        self.assertIsNone(view.current_contract);self.assertFalse(view.authoritative_expired)
        self.assertIs(view.agreement.release,release)
        self.assertEqual(release.cash_obligation.amount,39)
        trade=test_trades.PreseasonTradeTests().plan()
        agreement=GenerationAgreement(legacy_identity('a',trade.original_contract.offer.player_id),
            trade.original_contract,trade.original_contract,outgoing_trade=trade)
        view=GenerationCalendarView(agreement,2026,2027)
        self.assertEqual(view.annual_charges(),trade.retained_bonus.annual_charges[1:])
        self.assertEqual(view.payment_ceilings(),agreement.payment_ceilings())
        self.assertEqual(view.payment_ceilings()['base:1'],0)
        self.assertEqual(view.status,'assigned');self.assertIsNone(view.current_contract)
        self.assertIs(view.agreement.outgoing_trade,trade)
        self.assertEqual(trade.seller_cash.amount,9)

    def test_restructured_projection_preserves_birth_and_amendment_plan(self):
        plan=test_restructures.PreseasonRestructureTests().plan()
        agreement=GenerationAgreement(legacy_identity('a','v'),plan.original_contract,plan.contract,restructure=plan)
        view=GenerationCalendarView(agreement,2026,2027)
        self.assertEqual(view.current_contract.elapsed_years,3)
        self.assertEqual(view.annual_charges(),plan.contract.charges()[1:])
        self.assertEqual(view.current_contract.charges(),view.annual_charges())
        self.assertIs(view.agreement.restructure,plan)
        self.assertEqual(plan.original_contract.elapsed_years,2)
        self.assertEqual(plan.contract.elapsed_years,2)
        self.assertEqual(plan.cash_obligation.amount,180)
