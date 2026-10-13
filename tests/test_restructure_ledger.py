from dataclasses import replace
from datetime import date
from fractions import Fraction
import json
import unittest
from franchise.books import ChargeRecord, OpeningBooks
from franchise.cap import Ledger, Rejected
from franchise.cash import CashBook
from tests import test_restructures, test_releases, test_trades


class RestructureLedgerTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_restructures.PreseasonRestructureTests()

    def ledger(self, retained=(), floors=(2,2,2,2,2)):
        ledger = Ledger.from_opening(OpeningBooks(contracts=(self.fixture.contract(),), retained=retained),
            cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':floors})
        ledger._cash=CashBook((self.fixture.cash(),),'synthetic allocated cash')
        return ledger

    def restructure(self,ledger,**changes):
        inputs=dict(scope=self.fixture.scope(),converted_base=8,record_id='restructure:v',expected_revision=0)
        inputs.update(changes)
        return ledger.apply_preseason_restructure('v',**inputs)

    def test_preserves_exact_bonus_layers_paid_history_and_unrelated_debt(self):
        ledger=self.ledger((ChargeRecord('existing',(1,1,1,1,1,1),'synthetic debt'),))
        self.assertNotIn('restructures',ledger.financial_snapshot())
        self.assertNotIn('bonus_layers',ledger.contract_terms('v'))
        self.assertNotIn('unpaid_bonus_layers',ledger.guarantee_cash('v'))
        plan=self.restructure(ledger)
        self.assertEqual(ledger.charges,tuple(Fraction(n,5) for n in (33,123,173,213,263))+(Fraction(1),))
        self.assertEqual((ledger.revision,ledger._cash.revision),(1,1))
        self.assertEqual(ledger._players,{'v'})
        self.assertEqual(ledger._contracts['v'],plan.contract.offer)
        self.assertEqual(ledger.active_contract('v'),plan.contract)
        self.assertEqual(ledger._cash.records['contract:v'].amount,180)
        self.assertEqual(ledger._cash.records['contract:v'].paid,30)
        cash=ledger.guarantee_cash('v')
        self.assertEqual(cash['unpaid_signing_bonus'],8)
        self.assertEqual(cash['unpaid_original_signing_bonus'],0)
        self.assertEqual(cash['unpaid_bonus_layers'],{'bonus:restructure:v':8})
        self.assertEqual(sum(cash['unpaid_guaranteed_base_by_original_year']),22)
        self.assertEqual(ledger.contract_terms('v')['bonus_layers'][0]['amount'],8)
        archive=ledger.financial_snapshot()['restructures']['v']
        self.assertEqual(archive['original_contract']['offer']['salaries'][2],10)
        self.assertEqual(archive['contract']['offer']['salaries'][2],2)
        self.assertEqual(archive['cash_obligation']['amount'],180)
        json.dumps(archive,allow_nan=False)

    def test_failure_rollback_stale_floor_unknown_cash_and_layer_id_collision(self):
        ledger=self.ledger()
        before,cash=ledger.financial_snapshot(),ledger.cash_snapshot()
        for changes in ({'expected_revision':True},{'expected_revision':1},{'converted_base':9},{'scope':None}):
            with self.subTest(changes=changes),self.assertRaises((ValueError,Rejected)):
                self.restructure(ledger,**changes)
            self.assertEqual(ledger.financial_snapshot(),before)
            self.assertEqual(ledger.cash_snapshot(),cash)
        collision=self.ledger((ChargeRecord('restructure:v',(1,),'synthetic collision'),))
        with self.assertRaisesRegex(Rejected,'layer identity'):
            self.restructure(collision)
        ledger._cash=None
        with self.assertRaises(Rejected):
            self.restructure(ledger)

    def test_repeated_and_rookie_restructures_reject_without_mutation(self):
        ledger=self.ledger()
        self.restructure(ledger)
        before,cash=ledger.financial_snapshot(),ledger.cash_snapshot()
        with self.assertRaisesRegex(ValueError,'Repeated layered'):
            self.restructure(ledger,expected_revision=1,record_id='second')
        self.assertEqual(ledger.financial_snapshot(),before)
        self.assertEqual(ledger.cash_snapshot(),cash)
        ledger=self.ledger()
        ledger._rookies['v']=object()
        with self.assertRaisesRegex(Rejected,'veteran classification'):
            self.restructure(ledger)

    def test_restructured_release_preserves_layer_cash_and_original_archive(self):
        ledger=self.ledger()
        self.restructure(ledger)
        release=test_releases.PreseasonReleaseTests().plan()
        ledger.apply_preseason_release('v',scope=release.scope,discount=release.discount,
            payment_year_offsets=(0,)*5,record_id='release',expected_revision=1)
        self.assertEqual(ledger.charges,(36,0,0,0,0))
        self.assertEqual(ledger.guarantee_cash('v')['unpaid_signing_bonus'],8)
        self.assertEqual(ledger.contract_terms('v')['bonus_layers'][0]['amount'],8)
        self.assertEqual(ledger.financial_snapshot()['released_contracts']['v']['original_contract']['bonus_layers'][0]['amount'],8)

    def test_restructured_trade_requires_layer_paid_and_preserves_archives(self):
        ledger=self.ledger()
        plan=self.restructure(ledger)
        inputs=dict(scope=test_trades.PreseasonTradeTests().scope(),record_id='trade',expected_revision=1)
        before=ledger.financial_snapshot()
        with self.assertRaisesRegex(ValueError,'fully paid'):
            ledger.apply_preseason_trade_out('v',**inputs)
        self.assertEqual(ledger.financial_snapshot(),before)
        ledger._cash.records['contract:v']=replace(plan.cash_obligation,paid=38,
            paid_components=plan.cash_obligation.paid_components+((plan.bonus_layer.cash_component,8),))
        ledger.apply_preseason_trade_out('v',**inputs)
        self.assertEqual(ledger.charges,(14,0,0,0,0))
        self.assertEqual(ledger.guarantee_cash('v')['unpaid_bonus_layers'],{'bonus:restructure:v':0})
        self.assertEqual(ledger.contract_terms('v')['bonus_layers'][0]['amount'],8)

    def test_calendar_cannot_backdate_existing_durable_operations(self):
        ledger=self.ledger()
        ledger._last_transaction_date=date(2026,6,2)
        with self.assertRaises(Rejected):
            self.restructure(ledger)
