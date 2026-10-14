from copy import deepcopy
from datetime import date
from fractions import Fraction
import unittest
from franchise.guarantees import DiscountProfile
from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
from franchise.receipts import compact_lifecycle_result
from tests import test_layered_restructure_ledger


class LayeredReleaseReceiptTests(unittest.TestCase):
    def result(self):
        fixture=test_layered_restructure_ledger.LayeredRestructureLedgerTests()
        ledger,first=fixture.ledger()
        ledger.apply_calendar_layered_preseason_restructure('v',**fixture.inputs(ledger,first))
        gid=ledger.contract_identity('v').generation_id
        ledger.apply_calendar_preseason_release('v',generation_id=gid,
            scope=PreseasonReleaseScope(2028,date(2028,6,2),date(2028,9,10),EXCLUDED_LIABILITIES,
                True,True,0,'synthetic healthy layered release'),discount=DiscountProfile(2028,Fraction(0),'synthetic zero'),
            payment_year_offsets=(0,),record_id='calendar-layered-release:release-2028',expected_revision=ledger.revision)
        return dict(decision_mode='manual',player_id='v',release=dict(format=3,generation_id=gid,league_year=2028,
            financial=ledger.financial_snapshot(),cash=ledger.cash_snapshot(),
            amendment_history=ledger.generation_accounting(gid).amendment_history_snapshot()))

    def test_compact_release_retains_history_and_unpaid_converted_bonus(self):
        result=self.result();before=deepcopy(result)
        compact=compact_lifecycle_result(result,'manual_release')
        self.assertEqual(compact['release']['format'],3)
        self.assertEqual(compact['release']['amendment_history'],result['release']['amendment_history'])
        self.assertEqual(compact['release']['cash']['nominal_total'],9000000)
        self.assertEqual(compact['release']['cash']['paid_total'],7000000)
        self.assertEqual(compact['release']['cash']['unpaid_total'],2000000)
        self.assertEqual(result,before)

    def test_history_downgrade_and_wrong_original_year_or_terms_reject(self):
        for scenario in ('missing','empty','year','contract','prior'):
            result=self.result();receipt=result['release'];history=receipt['amendment_history']
            if scenario=='missing':del receipt['amendment_history']
            elif scenario=='empty':history['prior_restructures']=[]
            elif scenario=='year':receipt['league_year']=2029
            elif scenario=='contract':history['latest_restructure']['contract']['source']='changed'
            else:history['prior_restructures'][0]={}
            with self.subTest(scenario=scenario),self.assertRaises(ValueError):
                compact_lifecycle_result(result,'manual_release')
