from contextlib import closing
from dataclasses import replace
from datetime import date
import json
import sqlite3
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger,Rejected
from franchise.store import FranchiseStore
from franchise.trades import PreseasonTradeScope,EXCLUDED_TRADE_LIABILITIES
from tests import test_return_store,test_restructures


class GenerationTradeStoreTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_return_store.ReturnStoreTests();self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.migrate();self.fixture.sign()
        self.store=self.fixture.store
        self.return_id=self.store.load_team('a').contract_identity('v').generation_id
        self.store.record_payment('a','new-bonus',self.return_id,3,expected_cash_revision=4,
            source='synthetic bank',payment_reference='return bonus receipt',component='signing_bonus')
        self.store.create_team('b',Ledger.from_opening(OpeningBooks(),cap=200,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
        self.store.initialize_cash('b',(),source='synthetic complete buyer cash')
        self.scope=PreseasonTradeScope(2026,date(2026,6,1),date(2026,9,10),date(2026,9,10),
            EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'synthetic versioned assignment')

    def trade(self):
        return self.store.trade_preseason_veteran('assignment','a','b','v',scope=self.scope,
            seller_revision=6,buyer_revision=1,access_check=lambda:None)

    def snapshots(self):return {t:self.store.load_team(t).generation_snapshot() for t in ('a','b')}

    def test_assignment_back_to_former_club_preserves_cash_debt_and_history(self):
        receipt=self.trade()
        buyer_id=self.store.load_team('b').contract_identity('v').generation_id
        self.assertNotEqual(buyer_id,self.return_id)
        self.assertEqual(self.store.load_team('a').charges,(42,0,0))
        self.assertEqual(self.store.load_team('b').charges,(5,5,5))
        self.store.trade_preseason_veteran('back','b','a','v',scope=self.scope,
            seller_revision=2,buyer_revision=7,access_check=lambda:None)
        reopened=FranchiseStore(self.store.path)
        source,target=reopened.load_team('b'),reopened.load_team('a')
        self.assertEqual(target.charges,(47,5,5))
        self.assertEqual(len(target.generation_agreements()),3)
        self.assertEqual(target.generation_cash(self.fixture.old_id).amount,39)
        self.assertEqual(target.generation_cash(self.return_id).amount,3)
        self.assertEqual(source.generation_cash(buyer_id).amount,0)
        self.assertEqual(target.cash_snapshot()['nominal_total']+source.cash_snapshot()['nominal_total'],57)
        before=self.snapshots()
        self.assertEqual(self.trade(),receipt)
        self.assertEqual(self.snapshots(),before)

    def test_receiving_assignment_restructure_and_release_preserve_both_older_debts(self):
        self.trade()
        self.store.trade_preseason_veteran('back','b','a','v',scope=self.scope,
            seller_revision=2,buyer_revision=7,access_check=lambda:None)
        gid=self.store.load_team('a').contract_identity('v').generation_id
        amend=test_restructures.PreseasonRestructureTests().scope()
        self.store.restructure_preseason_veteran('a','assigned-convert','v',scope=amend,converted_base=4,
            expected_revision=8,access_check=lambda:None,generation_id=gid)
        self.store.release_preseason_veteran('a','assigned-release','v',scope=self.fixture.release.scope,
            discount=self.fixture.release.discount,payment_year_offsets=(0,1,2),expected_revision=9,access_check=lambda:None)
        ledger=FranchiseStore(self.store.path).load_team('a')
        self.assertEqual(ledger.charges,(47,0,0))
        self.assertEqual(ledger.generation_cash(gid).amount,5)
        self.assertEqual(ledger.generation_cash(self.fixture.old_id).amount,39)
        self.assertEqual(ledger.generation_cash(self.return_id).amount,3)

    def test_buyer_rejection_and_final_access_failure_preserve_both_books(self):
        before=self.snapshots()
        def disconnected():raise TimeoutError('disconnected')
        with self.assertRaises(TimeoutError):
            self.store.trade_preseason_veteran('fail','a','b','v',scope=self.scope,
                seller_revision=6,buyer_revision=1,access_check=disconnected)
        self.assertEqual(self.snapshots(),before)
        self.store.update_budget('b',cap=1,roster_reserve=0,expected_revision=1)
        before=self.snapshots()
        with self.assertRaises(Rejected):
            self.store.trade_preseason_veteran('fail','a','b','v',scope=self.scope,
                seller_revision=6,buyer_revision=2,access_check=lambda:None)
        self.assertEqual(self.snapshots(),before)

    def test_second_journal_failure_rolls_back_the_entire_pair(self):
        before=self.snapshots()
        with closing(sqlite3.connect(self.store.path)) as db,db:
            db.execute("CREATE TRIGGER reject_generation_in BEFORE INSERT ON events WHEN NEW.kind='generation_trade_in' BEGIN SELECT RAISE(ABORT,'injected'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.trade()
        self.assertEqual(self.snapshots(),before)
        with closing(sqlite3.connect(self.store.path)) as db:
            self.assertEqual(db.execute("SELECT team_id FROM ownership WHERE player_id='v'").fetchone()[0],'a')
            self.assertEqual(db.execute("SELECT count(*) FROM events WHERE kind LIKE 'generation_trade_%'").fetchone()[0],0)

    def test_source_generation_and_pair_corruption_reject(self):
        self.trade()
        with closing(sqlite3.connect(self.store.path)) as db:
            rows=db.execute("SELECT id,payload FROM events WHERE kind LIKE 'generation_trade_%'").fetchall()
        common=json.loads(rows[0][1])['trade']
        common['seller_generation_id']=self.fixture.old_id
        for event,payload in rows:
            data=json.loads(payload);data['trade']=common
            with closing(sqlite3.connect(self.store.path)) as db,db:
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(data),event))
        with self.assertRaises(ValueError):self.store.load_team('b')

    def test_native_trade_ai_off_exact_identities_and_historical_retry(self):
        from dataclasses import asdict
        from franchise.bridge import Bridge
        from franchise.control import AccessDisabled
        scope=asdict(self.scope)
        for field in ('traded_on','seller_first_regular_season_game','buyer_first_regular_season_game'):
            scope[field]=getattr(self.scope,field).isoformat()
        scope['exclusions']=sorted(self.scope.exclusions)
        request=dict(protocol=1,request_id='native-assignment',operation='manual_trade',seller='a',buyer='b',
            player_id='v',seller_revision=6,buyer_revision=1,timeout_ms=5000,decision_mode='manual',scope=scope,
            seller_generation_id=self.return_id,buyer_previous_generation_id=None)
        def provider(_):raise AssertionError('Manual trade used provider')
        def disabled():raise AccessDisabled('disabled')
        bridge=Bridge(self.store,provider=provider,access_check=disabled)
        before=self.snapshots()
        for changes in ({'seller_generation_id':None},{'buyer_previous_generation_id':True},
                        {'seller_generation_id':self.fixture.old_id}):
            with self.subTest(changes=changes):
                self.assertIsNotNone(bridge.handle({**request,**changes})['error'])
                self.assertEqual(self.snapshots(),before)
        missing={key:value for key,value in request.items() if key not in ('seller_generation_id','buyer_previous_generation_id')}
        self.assertEqual(bridge.handle(missing)['error'],'invalid_request')
        receipt=bridge.handle(request)
        self.assertIsNone(receipt['error'],receipt)
        self.assertEqual(receipt['result']['seller_generation_id'],self.return_id)
        self.assertEqual(receipt['result']['buyer_generation_id'],self.store.load_team('b').contract_identity('v').generation_id)
        self.assertEqual(bridge.handle(request),receipt)

    def test_explicit_legacy_source_to_virgin_receiver_creates_versioned_receipt(self):
        import tempfile
        from franchise.bridge import Bridge
        from tests import test_trade_store,test_trade_bridge
        with tempfile.TemporaryDirectory() as directory:
            store=test_trade_store.TradeStoreTests().setup_store(directory)
            FranchiseStore.migrate_generations(store.path)
            identity=store.load_team('a').contract_identity('v').generation_id
            request={**test_trade_bridge.TradeBridgeTests().request(),
                'seller_generation_id':identity,'buyer_previous_generation_id':None}
            bridge=Bridge(store,provider=lambda _:self.fail('model called'),access_check=lambda:self.fail('AI grant used'))
            receipt=bridge.handle(request)
            self.assertIsNone(receipt['error'],receipt)
            self.assertEqual(receipt['result']['seller_generation_id'],identity)
            self.assertTrue(receipt['result']['buyer_generation_id'].startswith('contract-gen:'))
            self.assertEqual(bridge.handle(request),receipt)
