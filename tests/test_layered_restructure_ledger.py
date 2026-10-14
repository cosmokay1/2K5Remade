"""Explicit later-year conversions preserve prior plans and original cash indices."""
from dataclasses import replace
from datetime import date
import unittest
from franchise.cap import Rejected
from franchise.salary_rules import VeteranMinimumProfile
from tests import test_ledger_year_transition


class LayeredRestructureLedgerTests(unittest.TestCase):
    def ledger(self,*,second_year=True):
        fixture=test_ledger_year_transition.LedgerYearTransitionTests()
        ledger=fixture.ledger();old=ledger._active_contracts['v']
        contract=replace(old,offer=replace(old.offer,guaranteed_salaries=(0,2000000,2000000)))
        ledger._active_contracts['v']=contract;ledger._contracts['v']=contract.offer
        ledger._generation_agreements.clear();ledger._refresh_generation_agreement('v')
        fixture.transition(ledger)
        first=ledger.apply_calendar_preseason_restructure('v',**fixture.amendment_inputs(ledger))
        if second_year:
            ledger._cash.pay('contract:v',100000,ledger._cash.revision,component='bonus:calendar-conversion')
            ledger._cash.pay('contract:v',1900000,ledger._cash.revision,component='base:1')
            fixture.transition(ledger,from_year=2027,to_year=2028,expected_revision=2,
                next_minimum_profile=VeteranMinimumProfile(2028,(('v',(7,7),('active_inactive',)*2),)))
        return ledger,first

    def inputs(self,ledger,first,**changes):
        scope=replace(first.scope,league_year=2028,amended_on=date(2028,6,1),first_regular_season_game=date(2028,9,10),
            minimum_source=ledger._veteran_minimum_profile.source,source='synthetic later-year conversion')
        args=dict(generation_id=ledger.contract_identity('v').generation_id,scope=scope,converted_base=200000,
            record_id='second-conversion',expected_revision=ledger.revision)
        args.update(changes);return args

    def state(self,ledger):
        return (ledger.financial_snapshot(),ledger.cash_snapshot(),ledger.generation_agreements(),
            ledger.generation_calendar_snapshot(),dict(ledger._contracts),dict(ledger._active_contracts))

    def test_second_conversion_keeps_complete_history_and_original_cash_indices(self):
        ledger,first=self.ledger();gid=ledger.contract_identity('v').generation_id
        original=ledger.generation_accounting(gid).original_contract
        cash=ledger.cash_snapshot();first_layer=first.bonus_layer
        plan=ledger.apply_calendar_layered_preseason_restructure('v',**self.inputs(ledger,first))
        agreement=ledger.generation_accounting(gid)
        self.assertIs(agreement.original_contract,original)
        self.assertEqual(agreement.prior_restructures,(first,))
        self.assertIs(agreement.restructure,plan)
        self.assertEqual(agreement.contract.elapsed_years,2)
        self.assertEqual(agreement.contract.bonus_layers,(first_layer,plan.bonus_layer))
        self.assertEqual((plan.bonus_layer.original_start_index,plan.bonus_layer.allocation_years),(2,1))
        self.assertEqual(agreement.contract.offer.salaries,(2000000,1900000,1800000))
        self.assertEqual(agreement.contract.offer.guaranteed_salaries,(0,1900000,1800000))
        self.assertEqual(ledger.charges,(3050013,))
        self.assertEqual(ledger.generation_calendar_view(gid).anchor_year,2028)
        self.assertEqual(ledger.cash_snapshot()['nominal_total'],cash['nominal_total'])
        self.assertEqual(ledger.cash_snapshot()['paid_total'],cash['paid_total'])
        self.assertEqual(ledger.cash_snapshot()['obligations'][0]['paid_components'],cash['obligations'][0]['paid_components'])
        self.assertEqual(agreement.payment_ceilings()['base:1'],1900000)
        self.assertEqual(agreement.payment_ceilings()['bonus:calendar-conversion'],100000)
        self.assertEqual(agreement.payment_ceilings()['bonus:second-conversion'],200000)
        with self.assertRaisesRegex(Rejected,'versioned generation posting'):ledger.generation_snapshot()

    def test_invalid_generation_year_source_and_duplicate_layer_are_atomic(self):
        for scenario in ('generation','revision','year','source','duplicate'):
            ledger,first=self.ledger();args=self.inputs(ledger,first)
            if scenario=='generation':args['generation_id']='foreign'
            if scenario=='revision':args['expected_revision']=True
            if scenario=='year':args['scope']=replace(first.scope,minimum_source=ledger._veteran_minimum_profile.source)
            if scenario=='source':args['scope']=replace(args['scope'],minimum_source='wrong minimum provenance')
            if scenario=='duplicate':args['record_id']=first.bonus_layer.record_id
            before=self.state(ledger)
            with self.subTest(scenario=scenario),self.assertRaises((ValueError,Rejected)):
                ledger.apply_calendar_layered_preseason_restructure('v',**args)
            self.assertEqual(self.state(ledger),before)

    def test_unpaid_old_layer_rejects_without_mutation(self):
        ledger,first=self.ledger();cash=ledger._cash.records['contract:v']
        ledger._cash.records['contract:v']=replace(cash,paid=cash.paid-100000,
            paid_components=tuple(item for item in cash.paid_components if item[0]!='bonus:calendar-conversion'))
        before=self.state(ledger)
        with self.assertRaisesRegex(ValueError,'existing bonus layer'):
            ledger.apply_calendar_layered_preseason_restructure('v',**self.inputs(ledger,first))
        self.assertEqual(self.state(ledger),before)

    def test_first_api_and_same_year_explicit_api_remain_guarded(self):
        ledger,first=self.ledger();before=self.state(ledger)
        with self.assertRaisesRegex(ValueError,'Repeated layered'):
            ledger.apply_calendar_preseason_restructure('v',**self.inputs(ledger,first))
        self.assertEqual(self.state(ledger),before)
        ledger,first=self.ledger(second_year=False);before=self.state(ledger)
        args=self.inputs(ledger,first,scope=first.scope)
        with self.assertRaises(Rejected):ledger.apply_calendar_layered_preseason_restructure('v',**args)
        self.assertEqual(self.state(ledger),before)
