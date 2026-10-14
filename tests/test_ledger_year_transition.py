from dataclasses import replace
from fractions import Fraction
from datetime import date
import unittest
from franchise.books import ActiveContract,OpeningBooks,ChargeRecord
from franchise.cap import Ledger,Offer,Rejected
from franchise.cash import CashBook,CashObligation
from franchise.salary_rules import VeteranMinimumProfile
from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
from franchise.guarantees import DiscountProfile


class LedgerYearTransitionTests(unittest.TestCase):
    def release_inputs(self,ledger,**changes):
        inputs=dict(generation_id=ledger.contract_identity('v').generation_id,
            scope=PreseasonReleaseScope(2027,date(2027,7,1),date(2027,9,10),EXCLUDED_LIABILITIES,
                True,True,0,'synthetic verified healthy release'),
            discount=DiscountProfile(2027,Fraction(0),'synthetic discount'),payment_year_offsets=(0,1),
            record_id='calendar-release',expected_revision=1)
        inputs.update(changes);return inputs

    def test_calendar_release_uses_current_cursor_and_retained_charges_age_once(self):
        ledger=self.ledger();gid=ledger.contract_identity('v').generation_id
        economic=ledger.generation_accounting(gid)
        self.transition(ledger)
        ledger._last_transaction_date=date(2026,6,1)
        plan=ledger.apply_calendar_preseason_release('v',**self.release_inputs(ledger))
        self.assertEqual(plan.original_contract.elapsed_years,1)
        archive=ledger.generation_accounting(gid)
        self.assertIs(archive.contract,economic.contract)
        self.assertEqual(archive.release_calendar_year,2027)
        self.assertEqual(archive.payment_ceilings()['base:0'],2000000)
        self.assertEqual(ledger.charges,(Fraction(1000011),Fraction(1000013)))
        self.assertEqual(ledger.cash_snapshot()['paid_total'],5000000)
        self.assertEqual(ledger.cash_snapshot()['unpaid_total'],0)
        self.assertNotIn('v',ledger._players)
        self.transition(ledger,from_year=2027,to_year=2028,expected_revision=2,
            next_minimum_profile=VeteranMinimumProfile(2028,(('v',(7,7),('active_inactive',)*2),)))
        self.assertEqual(ledger.charges,(Fraction(1000013),))
        self.assertEqual(ledger.generation_calendar_view(gid).annual_charges(),plan.charges()[1:])

    def test_invalid_calendar_release_cannot_change_financial_or_cash_state(self):
        for changes in ({'generation_id':'foreign'},{'generation_id':True},{'expected_revision':True},
                        {'payment_year_offsets':(0,)}, {'record_id':''}):
            ledger=self.ledger();self.transition(ledger)
            before=ledger.generation_snapshot();calendar=ledger.generation_calendar_snapshot()
            with self.subTest(changes=changes),self.assertRaises((Rejected,ValueError)):
                ledger.apply_calendar_preseason_release('v',**self.release_inputs(ledger,**changes))
            self.assertEqual(ledger.generation_snapshot(),before)
            self.assertEqual(ledger.generation_calendar_snapshot(),calendar)
        ledger=self.ledger();self.transition(ledger)
        with self.assertRaises(Rejected):
            ledger.apply_preseason_release('v',**{key:value for key,value in self.release_inputs(ledger).items()
                                                if key!='generation_id'})

    def ledger(self,term=3):
        contract=ActiveContract(Offer('v',(2000000,)*term,3000000),'synthetic economic terms')
        ledger=Ledger.from_opening(OpeningBooks(contracts=(contract,),retained=(ChargeRecord('debt',(7,11,13),'synthetic retained'),)),
            cap=10000000,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1000000,)*term})
        ledger._cash=CashBook((CashObligation('contract:v','v',contract.nominal_cash,5000000,
            'synthetic allocated settlement',(('signing_bonus',3000000),('base:0',2000000))),),'synthetic cash')
        ledger.bind_team_identity('a');ledger._league_year=2026
        return ledger

    def transition(self,ledger,**changes):
        inputs=dict(from_year=2026,to_year=2027,expected_revision=0,next_cap=9000000,roster_reserve=500,
            next_minimum_profile=VeteranMinimumProfile(2027,(('v',(7,7,7),('active_inactive',)*3),)),
            source='synthetic verified closing exclusions and next budget',expired_generation_ids=())
        inputs.update(changes);return ledger.apply_year_transition(**inputs)

    def test_survivor_ages_preserving_all_cash_and_economic_archives(self):
        ledger=self.ledger();gid=ledger.contract_identity('v').generation_id
        agreement=ledger.generation_accounting(gid);cash=ledger.cash_snapshot();charges=ledger.charges
        result=self.transition(ledger)
        self.assertEqual(ledger.active_contract('v').elapsed_years,1)
        self.assertIs(ledger.generation_accounting(gid),agreement)
        self.assertEqual(ledger.cash_snapshot(),cash)
        self.assertEqual(ledger.charges,charges[1:]);self.assertEqual(ledger.cap,9000000)
        self.assertEqual(result['league_year'],2027);self.assertEqual(ledger.revision,1)
        self.assertEqual(ledger.generation_calendar_view(gid).payment_ceilings(),agreement.payment_ceilings())
        with self.assertRaises(Rejected):ledger.preview_offer(Offer('v',(2000000,),0),1)
        # Payment remains explicit and enables another independent year close.
        original=ledger._cash.records['contract:v']
        ledger._cash.records['contract:v']=replace(original,paid=7000000,
            paid_components=original.paid_components+(('base:1',2000000),))
        self.transition(ledger,from_year=2027,to_year=2028,expected_revision=1,
            next_minimum_profile=VeteranMinimumProfile(2028,(('v',(7,7),('active_inactive',)*2),)))
        self.assertEqual(ledger.active_contract('v').elapsed_years,2)
        self.assertEqual(ledger.charges,charges[2:])

    def test_expiry_requires_exact_eligibility_and_full_settlement(self):
        ledger=self.ledger(1);gid=ledger.contract_identity('v').generation_id
        before=ledger.financial_snapshot();cash=ledger.cash_snapshot()
        with self.assertRaises(Rejected):self.transition(ledger)
        self.assertEqual(ledger.financial_snapshot(),before);self.assertEqual(ledger.cash_snapshot(),cash)
        self.transition(ledger,expired_generation_ids=(gid,))
        self.assertEqual(ledger._players,set());self.assertEqual(ledger.charges,(Fraction(11),Fraction(13)))
        self.assertEqual(ledger.generation_accounting(gid).status,'active')
        self.assertEqual(ledger.generation_calendar_view(gid).status,'expired')
        self.assertEqual(ledger.cash_snapshot(),cash)
        with self.assertRaises(Rejected):ledger.active_contract('v')

    def test_invalid_closing_inputs_do_not_mutate(self):
        for changes in ({'from_year':True},{'to_year':2028},{'expected_revision':True},
                        {'source':''},{'expired_generation_ids':('unknown',)},
                        {'next_minimum_profile':None},{'next_cap':-1}):
            ledger=self.ledger();before=ledger.financial_snapshot();cash=ledger.cash_snapshot()
            with self.subTest(changes=changes),self.assertRaises((Rejected,ValueError)):
                self.transition(ledger,**changes)
            self.assertEqual(ledger.financial_snapshot(),before);self.assertEqual(ledger.cash_snapshot(),cash)
        ledger=self.ledger();ledger._cash.records['contract:v']=replace(ledger._cash.records['contract:v'],paid_components=None)
        with self.assertRaises(Rejected):self.transition(ledger)

    def test_closed_release_and_assignment_keep_original_payment_rights(self):
        from tests import test_releases,test_trades
        for kind,fixture in (('release',test_releases.PreseasonReleaseTests()),('trade',test_trades.PreseasonTradeTests())):
            ledger=Ledger.from_opening(OpeningBooks(contracts=(fixture.contract(),)),cap=100,roster_reserve=0,
                max_bonus_years=5,veteran_minimums={'v':(1,1,1)})
            ledger._cash=CashBook((fixture.cash(),),'synthetic cash');ledger.bind_team_identity('a');ledger._league_year=2026
            if kind=='release':
                plan=fixture.plan()
                ledger.apply_preseason_release('v',scope=plan.scope,discount=plan.discount,
                    payment_year_offsets=plan.payment_year_offsets,record_id='release',expected_revision=0)
            else:ledger.apply_preseason_trade_out('v',scope=fixture.scope(),record_id='trade',expected_revision=0)
            gid=ledger.contract_identity('v').generation_id;agreement=ledger.generation_accounting(gid)
            cash=ledger.cash_snapshot();charges=ledger.charges;ceilings=agreement.payment_ceilings()
            self.transition(ledger,expected_revision=1)
            self.assertIs(ledger.generation_accounting(gid),agreement)
            self.assertEqual(ledger.generation_calendar_view(gid).payment_ceilings(),ceilings)
            self.assertEqual(ledger.charges,charges[1:]);self.assertEqual(ledger.cash_snapshot(),cash)

    def test_layered_survivor_keeps_layer_and_original_amendment_plan(self):
        from tests.test_restructures import PreseasonRestructureTests
        ledger=self.ledger();old=ledger._active_contracts['v']
        guaranteed=replace(old,offer=replace(old.offer,guaranteed_salaries=(2000000,0,0)))
        ledger._active_contracts['v']=guaranteed;ledger._contracts['v']=guaranteed.offer
        # This fixture replaces its original source before any operation.
        ledger._generation_agreements.clear();ledger._refresh_generation_agreement('v')
        cash=ledger._cash.records['contract:v']
        ledger._cash.records['contract:v']=replace(cash,paid=3000000,paid_components=(('signing_bonus',3000000),))
        plan=ledger.apply_preseason_restructure('v',scope=PreseasonRestructureTests().scope(),converted_base=1000000,
            record_id='conversion',expected_revision=0)
        cash=ledger._cash.records['contract:v']
        ledger._cash.records['contract:v']=replace(cash,paid=5000000,
            paid_components=(('signing_bonus',3000000),('bonus:conversion',1000000),('base:0',1000000)))
        gid=ledger.contract_identity('v').generation_id;before=ledger.cash_snapshot()
        self.transition(ledger,expected_revision=1)
        self.assertEqual(ledger.active_contract('v').bonus_layers,plan.contract.bonus_layers)
        self.assertIs(ledger.generation_accounting(gid).restructure,plan)
        self.assertEqual(ledger.cash_snapshot(),before)
