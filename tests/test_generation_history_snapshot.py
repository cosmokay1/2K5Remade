import copy
import json
import unittest
from franchise.cap import Rejected
from tests import test_layered_restructure_ledger as layered_fixture
from tests import test_ledger_year_transition as year_fixture


class GenerationHistorySnapshotTests(unittest.TestCase):
    def test_no_history_format_two_opt_in_preserves_exact_legacy_projection(self):
        ledger=year_fixture.LedgerYearTransitionTests().ledger()
        legacy=ledger.generation_snapshot()
        encoded=json.dumps(legacy,separators=(',',':'))
        newer=ledger.generation_snapshot(history_format=2)
        self.assertEqual(newer['format'],2)
        self.assertIsNone(newer['agreements'][0]['amendment_history'])
        projected=copy.deepcopy(newer);projected['format']=1
        for agreement in projected['agreements']:agreement.pop('amendment_history')
        self.assertEqual(json.dumps(projected,separators=(',',':')),encoded)
        self.assertEqual(json.dumps(ledger.generation_snapshot(),separators=(',',':')),encoded)
        fixture=layered_fixture.LayeredRestructureLedgerTests();ledger,first=fixture.ledger(second_year=False)
        first_snapshot=ledger.generation_snapshot(history_format=2)
        self.assertIsNone(first_snapshot['agreements'][0]['amendment_history'])
        self.assertEqual(first_snapshot['agreements'][0]['restructure']['converted_base'],first.converted_base)
        self.assertNotIn('amendment_history',ledger.generation_snapshot()['agreements'][0])

    def test_second_conversion_explicit_snapshot_keeps_birth_prior_latest_and_live_cash(self):
        fixture=layered_fixture.LayeredRestructureLedgerTests();ledger,first=fixture.ledger()
        gid=ledger.contract_identity('v').generation_id
        birth=ledger.generation_accounting(gid).original_contract.to_dict()
        second=ledger.apply_calendar_layered_preseason_restructure('v',**fixture.inputs(ledger,first))
        snapshot=ledger.generation_snapshot(history_format=2)
        agreement=snapshot['agreements'][0];history=agreement['amendment_history']
        self.assertEqual(snapshot['format'],2);self.assertEqual(history['format'],1)
        self.assertEqual(agreement['original_contract'],birth)
        self.assertEqual(history['prior_restructures'],[ledger._restructure_snapshot(first)])
        self.assertEqual(history['latest_restructure'],ledger._restructure_snapshot(second))
        self.assertEqual(agreement['restructure'],history['latest_restructure'])
        self.assertEqual(agreement['contract']['elapsed_years'],2)
        self.assertEqual(agreement['restructure_calendar_year'],2028)
        self.assertEqual(agreement['cash_obligation'],ledger.generation_cash(gid).to_dict())
        self.assertEqual(snapshot['cash'],ledger.cash_snapshot())
        self.assertEqual(agreement['contract']['offer']['salaries'],[2000000,1900000,1800000])
        self.assertEqual(len(agreement['contract']['bonus_layers']),2)
        saved=copy.deepcopy(snapshot)
        history['prior_restructures'][0]['original_contract']['offer']['salaries'][0]=1
        history['latest_restructure']['cash_obligation']['paid_components'][0][1]=0
        agreement['original_contract']['offer']['salaries'][0]=2
        agreement['cash_obligation']['paid_components'][0][1]=3
        snapshot['cash']['obligations'][0]['paid_components'][0][1]=4
        snapshot['active_generation_ids'].clear()
        self.assertEqual(ledger.generation_snapshot(history_format=2),saved)
        with self.assertRaises(Rejected):ledger.generation_snapshot()
        with self.assertRaises(Rejected):ledger.generation_snapshot(history_format=1)

    def test_unknown_or_noninteger_formats_reject_without_mutation(self):
        ledger=year_fixture.LedgerYearTransitionTests().ledger();before=ledger.generation_snapshot()
        for value in (True,False,'2',2.0,None,0,3,-1):
            with self.subTest(value=value),self.assertRaises(ValueError):
                ledger.generation_snapshot(history_format=value)
            self.assertEqual(ledger.generation_snapshot(),before)
