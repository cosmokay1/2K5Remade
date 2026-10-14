from contextlib import closing
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from franchise.bridge import Bridge
from franchise.books import ActiveContract,OpeningBooks
from franchise.cap import Ledger,Offer
from franchise.cash import CashObligation
from franchise.store import FranchiseStore
from tests import test_release_store,test_restructure_store,test_trades


class ReceiptCapacityStoreTests(unittest.TestCase):
    def rejecting(self,receipt):
        raise ValueError('synthetic transport capacity exceeded')

    def test_release_and_restructure_rejected_before_commit_retry_receives_original(self):
        fixture=test_restructure_store.RestructureStoreTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        store=fixture.store;before=Path(store.path).read_bytes()
        with self.assertRaises(ValueError):fixture.amend(receipt_check=self.rejecting)
        self.assertEqual(Path(store.path).read_bytes(),before)
        observed=[];receipt=fixture.amend(receipt_check=observed.append)
        self.assertEqual(observed,[receipt])
        with self.assertRaises(ValueError):fixture.amend(receipt_check=self.rejecting)
        self.assertEqual(fixture.amend(),receipt)
        observed=[];self.assertEqual(fixture.amend(receipt_check=observed.append),receipt)
        self.assertEqual(observed,[receipt])
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        releasefixture=test_release_store.ReleaseStoreTests();release=releasefixture.setup_store(temp.name)
        before=Path(release.path).read_bytes()
        with self.assertRaises(ValueError):releasefixture.release(release,receipt_check=self.rejecting)
        self.assertEqual(Path(release.path).read_bytes(),before)
        observed=[];receipt=releasefixture.release(release,receipt_check=observed.append)
        self.assertEqual(observed,[receipt])
        with self.assertRaises(ValueError):releasefixture.release(release,receipt_check=self.rejecting)
        self.assertEqual(releasefixture.release(release),receipt)

    def test_trade_hook_receives_full_identity_receipt_and_failed_hook_keeps_both_books(self):
        from tests import test_trade_store
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        fixture=test_trade_store.TradeStoreTests();store=fixture.setup_store(temp.name)
        FranchiseStore.migrate_generations(store.path)
        source=store.load_team('a').contract_identity('v').generation_id
        args=dict(scope=test_trades.PreseasonTradeTests().scope(),seller_revision=1,buyer_revision=1,
            access_check=lambda:None,seller_generation_id=source,buyer_previous_generation_id=None,
            include_generation_identity=True)
        before=Path(store.path).read_bytes()
        with self.assertRaises(ValueError):store.trade_preseason_veteran('trade','a','b','v',receipt_check=self.rejecting,**args)
        self.assertEqual(Path(store.path).read_bytes(),before)
        observed=[];receipt=store.trade_preseason_veteran('trade','a','b','v',receipt_check=observed.append,**args)
        self.assertEqual(observed,[receipt]);self.assertIn('buyer_generation_id',receipt)
        with self.assertRaises(ValueError):store.trade_preseason_veteran('trade','a','b','v',receipt_check=self.rejecting,**args)
        self.assertEqual(store.trade_preseason_veteran('trade','a','b','v',**args),receipt)

    def test_real_53_contract_release_receipt_overflow_cannot_commit(self):
        from tests import test_releases
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        store=FranchiseStore(Path(temp.name)/'large.sqlite')
        contracts=tuple(ActiveContract(Offer('player-'+str(i),(1000000,)*3,9000000,(0,1000000,1000000)),
            'synthetic original contract') for i in range(53))
        store.create_team('a',Ledger.from_opening(OpeningBooks(contracts=contracts),cap=300000000,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={c.offer.player_id:(1,)*3 for c in contracts}))
        store.initialize_cash('a',tuple(CashObligation('contract:'+c.offer.player_id,c.offer.player_id,12000000,9000000,
            'synthetic original payment',(('signing_bonus',9000000),)) for c in contracts),source='synthetic complete cash')
        plan=test_releases.PreseasonReleaseTests().plan();sizes=[];rejected=False
        for i,contract in enumerate(contracts):
            player=contract.offer.player_id;request='release-'+str(i)
            def capacity(receipt):
                response=Bridge._reply(request,result={'decision_mode':'manual','player_id':player,'release':receipt})
                size=len(json.dumps(response,allow_nan=False).encode('utf-8'))+1;sizes.append(size)
                if size>65536:raise ValueError('transport capacity exceeded')
            before=store.load_team('a').financial_snapshot(),store.load_team('a').cash_snapshot()
            try:
                store.release_preseason_veteran('a',request,player,scope=plan.scope,discount=plan.discount,
                    payment_year_offsets=(0,1,2),expected_revision=i+1,access_check=lambda:None,receipt_check=capacity)
            except ValueError:
                self.assertGreater(sizes[-1],65536);rejected=True
                self.assertEqual((store.load_team('a').financial_snapshot(),store.load_team('a').cash_snapshot()),before)
                with closing(sqlite3.connect(store.path)) as db:
                    self.assertEqual(db.execute('SELECT team_id FROM ownership WHERE player_id=?',(player,)).fetchone(),('a',))
                    self.assertIsNone(db.execute('SELECT id FROM events WHERE request_key=?',('release:'+request,)).fetchone())
                break
        self.assertTrue(rejected);self.assertLessEqual(sizes[-2],65536)

    def test_serialization_finishes_before_final_access_on_new_and_historical_receipts(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        fixture=test_release_store.ReleaseStoreTests();store=fixture.setup_store(temp.name)
        trace=[]
        def serialize(receipt):trace.append('receipt')
        def access():trace.append('access')
        receipt=fixture.release(store,receipt_check=serialize,access_check=access)
        self.assertEqual(trace,['receipt','access'])
        trace.clear()
        self.assertEqual(fixture.release(store,receipt_check=serialize,access_check=access),receipt)
        self.assertEqual(trace,['receipt','access'])
        def expired():raise TimeoutError('deadline passed during serialization')
        with self.assertRaises(TimeoutError):fixture.release(store,receipt_check=serialize,access_check=expired)
        self.assertEqual(fixture.release(store),receipt)
