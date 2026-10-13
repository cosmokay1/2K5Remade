from datetime import date
from fractions import Fraction
import unittest
from franchise.books import ActiveContract, BonusLayer
from franchise.cap import Ledger, Offer
from franchise.cash import CashObligation
from franchise.store import FranchiseStore
from franchise.trades import EXCLUDED_TRADE_LIABILITIES, PreseasonTradeScope, calculate_preseason_trade


class BonusLayerArchiveTests(unittest.TestCase):
    def contract(self):
        return ActiveContract(Offer('v',(10,10,2,20,30,40,50),10,(10,10,2,20,0,0,0)),
            'synthetic amended original',2,5,(BonusLayer('conversion',8,2,5,'synthetic conversion'),))

    def test_nominal_components_preserve_layer_identity_and_total(self):
        contract=self.contract()
        self.assertEqual(contract.nominal_cash,180)
        self.assertEqual(contract.compensation_components()['bonus:conversion'],8)
        self.assertEqual(contract.compensation_components()['signing_bonus'],10)
        self.assertEqual(contract.compensation_components()['base:2'],2)

    def test_assignment_snapshot_and_reconstruction_preserve_all_layers(self):
        contract=self.contract()
        cash=CashObligation('contract:v','v',180,38,'synthetic paid bonuses and prior base',
            (('signing_bonus',10),('bonus:conversion',8),('base:0',10),('base:1',10)))
        scope=PreseasonTradeScope(2026,date(2026,6,2),date(2026,9,10),date(2026,9,11),
            EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'synthetic assignment')
        plan=calculate_preseason_trade(contract,cash,scope=scope,record_id='trade')
        snapshot=Ledger._trade_snapshot(plan)
        self.assertEqual(snapshot['original_contract'],contract.to_dict())
        reconstructed=FranchiseStore._trade_plan({**snapshot,'record_id':'trade'})
        self.assertEqual(reconstructed,plan)
        self.assertEqual(plan.retained_bonus.annual_charges,(Fraction(18,5),Fraction(52,5)))
        self.assertEqual(plan.buyer_contract.charges(),(2,20,30,40,50))
        self.assertEqual((plan.seller_cash.amount,plan.buyer_cash.amount),(38,142))
