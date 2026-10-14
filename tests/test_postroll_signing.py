from dataclasses import replace
import unittest
from franchise.cap import Offer,Rejected
from franchise.salary_rules import VeteranMinimumProfile
from tests import test_ledger_year_transition as year_fixture


class PostrollSigningTests(unittest.TestCase):
    def ledger(self):
        fixture=year_fixture.LedgerYearTransitionTests();ledger=fixture.ledger()
        ledger._veteran_minimums['new']=(1000000,)*3
        profile=VeteranMinimumProfile(2027,tuple((p,(7,7,7),('active_inactive',)*3) for p in ('v','new')))
        fixture.transition(ledger,next_minimum_profile=profile)
        return ledger

    def test_newborn_uses_current_epoch_then_ages_one_year_without_changing_old_cash(self):
        ledger=self.ledger();old_gid=ledger.contract_identity('v').generation_id
        old_cash=ledger.generation_cash(old_gid);old_agreement=ledger.generation_accounting(old_gid)
        receipt=ledger.sign('new-2027',Offer('new',(2000000,2000000),1000000),1)
        gid=ledger.contract_identity('new').generation_id
        self.assertEqual(ledger.generation_calendar_view(gid).anchor_year,2027)
        self.assertEqual(ledger.active_contract('new').elapsed_years,0)
        self.assertEqual(ledger.sign('new-2027',receipt.offer,1),receipt)
        ledger._cash.add_contract(receipt.offer,'synthetic new contract')
        for player,component,amount in (('v','base:1',2000000),('new','signing_bonus',1000000),('new','base:0',2000000)):
            key='contract:'+player;cash=ledger._cash.records[key]
            ledger._cash.records[key]=replace(cash,paid=cash.paid+amount,
                paid_components=cash.paid_components+((component,amount),))
        cash=ledger.cash_snapshot()
        profile=VeteranMinimumProfile(2028,tuple((p,(7,7),('active_inactive',)*2) for p in ('v','new')))
        ledger.apply_year_transition(from_year=2027,to_year=2028,expected_revision=2,next_cap=9000000,
            roster_reserve=0,next_minimum_profile=profile,source='synthetic verified next close')
        self.assertEqual(ledger.active_contract('new').elapsed_years,1)
        self.assertEqual(ledger.active_contract('v').elapsed_years,2)
        self.assertEqual(ledger.cash_snapshot(),cash)
        self.assertIs(ledger.generation_accounting(old_gid),old_agreement)
        self.assertEqual(old_cash.paid,5000000)
        self.assertEqual(ledger.generation_calendar_view(gid).annual_charges(),(2500000,))

    def test_current_minimum_cap_and_historical_identity_guards_preserve_state(self):
        ledger=self.ledger();before=ledger.financial_snapshot();cash=ledger.cash_snapshot()
        for player,salaries in (('new',(1,)),('new',(9000000,)),('v',(2000000,)),('unknown',(2000000,))):
            with self.subTest(player=player,salaries=salaries),self.assertRaises(Rejected):
                ledger.sign('reject',Offer(player,salaries,0),1)
            self.assertEqual(ledger.financial_snapshot(),before);self.assertEqual(ledger.cash_snapshot(),cash)
        fixture=year_fixture.LedgerYearTransitionTests();expired=fixture.ledger(1)
        gid=expired.contract_identity('v').generation_id
        fixture.transition(expired,expired_generation_ids=(gid,))
        with self.assertRaises(Rejected):expired.sign('expired-new',Offer('v',(2000000,),0),1)

    def test_newborn_year_close_cannot_skip_its_own_outgoing_salary(self):
        ledger=self.ledger();offer=Offer('new',(2000000,2000000),0)
        ledger.sign('new',offer,1);ledger._cash.add_contract(offer,'synthetic original cash')
        current=ledger._cash.records['contract:v']
        ledger._cash.records['contract:v']=replace(current,paid=7000000,
            paid_components=current.paid_components+(('base:1',2000000),))
        before=ledger.financial_snapshot();cash=ledger.cash_snapshot()
        with self.assertRaises(Rejected):
            ledger.apply_year_transition(from_year=2027,to_year=2028,expected_revision=2,next_cap=9000000,
                roster_reserve=0,next_minimum_profile=VeteranMinimumProfile(2028,tuple(
                    (p,(7,7),('active_inactive',)*2) for p in ('v','new'))),source='synthetic close')
        self.assertEqual(ledger.financial_snapshot(),before);self.assertEqual(ledger.cash_snapshot(),cash)
