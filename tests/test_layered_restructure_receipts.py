from copy import deepcopy
import unittest
from franchise.receipts import compact_lifecycle_result
from tests import test_layered_restructure_ledger


class LayeredRestructureReceiptTests(unittest.TestCase):
    def result(self):
        fixture=test_layered_restructure_ledger.LayeredRestructureLedgerTests()
        ledger,first=fixture.ledger()
        ledger.apply_calendar_layered_preseason_restructure('v',**fixture.inputs(ledger,first))
        gid=ledger.contract_identity('v').generation_id
        return dict(decision_mode='manual',team_id='a',player_id='v',generation_id=gid,
            restructure=dict(format=3,generation_id=gid,league_year=2028,
                financial=ledger.financial_snapshot(),cash=ledger.cash_snapshot(),
                amendment_history=ledger.generation_accounting(gid).amendment_history_snapshot()))

    def test_compact_receipt_preserves_full_prior_and_latest_history(self):
        result=self.result();before=deepcopy(result)
        compact=compact_lifecycle_result(result,'manual_restructure')
        self.assertEqual(compact['restructure']['format'],3)
        self.assertEqual(compact['restructure']['amendment_history'],result['restructure']['amendment_history'])
        self.assertEqual(compact['restructure']['generation_id'],result['generation_id'])
        self.assertEqual(result,before)
        self.assertEqual(compact['restructure']['cash']['nominal_total'],9000000)
        self.assertEqual(compact['restructure']['cash']['paid_total'],7000000)

    def test_missing_downgraded_or_unbound_history_rejects(self):
        for scenario in ('missing','format','empty','prior','latest','identity','extra'):
            result=self.result();receipt=result['restructure'];history=receipt['amendment_history']
            if scenario=='missing':del receipt['amendment_history']
            elif scenario=='format':history['format']=True
            elif scenario=='empty':history['prior_restructures']=[]
            elif scenario=='prior':history['prior_restructures'][0]={}
            elif scenario=='latest':history['latest_restructure']['converted_base']=1
            elif scenario=='identity':receipt['generation_id']='foreign'
            else:history['extra']=True
            with self.subTest(scenario=scenario),self.assertRaises(ValueError):
                compact_lifecycle_result(result,'manual_restructure')
