from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from franchise.books import ActiveContract, OpeningBooks
from franchise.cap import Ledger, Offer
from franchise.store import FranchiseStore
from tests import test_restructures, test_releases, test_trade_store


class PlayerContractContextTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture=test_restructures.PreseasonRestructureTests()
        self.store=FranchiseStore(Path(self.temp.name)/'state.sqlite')
        ledger=Ledger.from_opening(OpeningBooks(contracts=(self.fixture.contract(),)),cap=200,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(2,)*5,'unsigned':(1,)})
        self.store.create_team('a',ledger)
        self.store.initialize_cash('a',(self.fixture.cash(),),source='synthetic allocated cash')

    def context(self):
        return self.store.player_context('a','v')

    def amend(self):
        self.store.restructure_preseason_veteran('a','conversion','v',scope=self.fixture.scope(),
            converted_base=8,expected_revision=1,access_check=lambda:None)

    def test_read_returns_only_identified_contract_and_does_not_initialize_actor_or_mutate(self):
        before=self.store.load_team('a').financial_snapshot()
        with closing(sqlite3.connect(self.store.path)) as db, db:
            events_before=db.execute('SELECT count(*) FROM events').fetchone()[0]
        context=self.context()
        accounting=context['contract_accounting']
        self.assertEqual(set(accounting),{'generation_id','status','charge_scope','annual_charges','contract','cash_obligation','guarantees'})
        self.assertEqual(accounting['generation_id'],self.store.contract_generations('a')['generations'][0]['generation_id'])
        self.assertEqual(accounting['charge_scope'],'active_contract')
        self.assertFalse(context['initialized'])
        self.assertEqual(accounting['status'],'active')
        self.assertEqual(accounting['contract'],self.fixture.contract().to_dict())
        self.assertEqual(accounting['annual_charges'],[12,22,32,40,50])
        self.assertEqual(accounting['cash_obligation']['player_id'],'v')
        self.assertEqual(accounting['cash_obligation']['amount'],180)
        self.assertEqual(self.store.player_context('a','unsigned')['contract_accounting'],None)
        self.assertEqual(self.store.load_team('a').financial_snapshot(),before)
        with closing(sqlite3.connect(self.store.path)) as db, db:
            self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0],events_before)

    def test_amendment_and_payment_context_are_exact_and_persist_on_restart(self):
        self.amend()
        context=self.context()
        accounting=context['contract_accounting']
        self.assertEqual(accounting['annual_charges'],['28/5','118/5','168/5','208/5','258/5'])
        self.assertEqual(accounting['contract']['bonus_layers'][0]['amount'],8)
        self.assertEqual(accounting['guarantees']['unpaid_signing_bonus'],8)
        self.store.record_payment('a','paid','contract:v',4,expected_cash_revision=1,
            source='synthetic payment',payment_reference='receipt-1',component='bonus:restructure:conversion')
        changed=self.context()
        self.assertEqual(changed['contract_accounting']['generation_id'],accounting['generation_id'])
        self.assertEqual(changed['financial_revision'],3)
        self.assertEqual(changed['contract_accounting']['annual_charges'],accounting['annual_charges'])
        self.assertEqual(changed['contract_accounting']['cash_obligation']['paid'],34)
        self.assertEqual(changed['contract_accounting']['guarantees']['unpaid_signing_bonus'],4)
        self.assertEqual(FranchiseStore(self.store.path).player_context('a','v'),changed)

    def test_released_status_preserves_layers_retained_debt_and_known_cash(self):
        original_id=self.context()['contract_accounting']['generation_id']
        self.amend()
        release=test_releases.PreseasonReleaseTests().plan()
        self.store.release_preseason_veteran('a','release','v',scope=release.scope,
            discount=release.discount,payment_year_offsets=(0,)*5,expected_revision=2,access_check=lambda:None)
        accounting=self.context()['contract_accounting']
        self.assertEqual(accounting['generation_id'],original_id)
        self.assertEqual(accounting['status'],'released')
        self.assertEqual(accounting['annual_charges'],[36])
        self.assertEqual(accounting['contract']['bonus_layers'][0]['amount'],8)
        self.assertEqual(accounting['cash_obligation']['amount'],60)
        self.assertEqual(accounting['guarantees']['unpaid_signing_bonus'],8)
        self.assertIn('retained',accounting['charge_scope'])
        self.assertEqual(FranchiseStore(self.store.path).player_context('a','v'),self.context())

    def test_assignment_separates_seller_retained_and_buyer_active_obligations(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=test_trade_store.TradeStoreTests()
            store=fixture.setup_store(directory)
            fixture.trade(store)
            seller=store.player_context('a','v')['contract_accounting']
            buyer=store.player_context('b','v')['contract_accounting']
            self.assertNotEqual(seller['generation_id'],buyer['generation_id'])
            self.assertEqual(seller['status'],'assigned')
            self.assertEqual(seller['charge_scope'],'retained_obligations')
            self.assertEqual(seller['annual_charges'],[9])
            self.assertEqual(seller['cash_obligation']['amount'],seller['cash_obligation']['paid'])
            self.assertEqual(sum(seller['guarantees']['unpaid_guaranteed_base_by_original_year']),0)
            self.assertEqual(buyer['status'],'active')
            self.assertEqual(buyer['annual_charges'],[10,20,30])
            self.assertEqual(buyer['contract']['offer']['signing_bonus'],0)
            self.assertEqual(buyer['cash_obligation']['amount'],60)
            self.assertEqual(FranchiseStore(store.path).player_context('a','v')['contract_accounting'],seller)

    def test_missing_cash_coverage_stays_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            store.create_team('a',Ledger.from_opening(OpeningBooks(contracts=(ActiveContract(Offer('v',(10,),0),'fixture'),)),
                cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)}))
            accounting=store.player_context('a','v')['contract_accounting']
            self.assertIsNone(accounting['cash_obligation'])
            self.assertIsNone(accounting['guarantees'])
