from contextlib import closing
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from franchise.books import ActiveContract,OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger,Offer
from franchise.cash import CashObligation
from franchise.receipts import compact_lifecycle_result
from franchise.store import FranchiseStore
from tests import test_release_bridge,test_trade_bridge,test_restructures,test_releases


class CompactReceiptTests(unittest.TestCase):
    def setup_store(self,directory,contracts=None):
        store=FranchiseStore(Path(directory)/'state.sqlite')
        contracts=contracts or (ActiveContract(Offer('v',(10,20,30),9,(10,20,10)),'synthetic original'),)
        for team in ('a','b'):
            store.create_team(team,Ledger.from_opening(OpeningBooks(contracts=contracts) if team=='a' else OpeningBooks(),
                cap=300000000,roster_reserve=0,max_bonus_years=5,
                veteran_minimums={c.offer.player_id:(1,)*3 for c in contracts}))
            cash=tuple(CashObligation('contract:'+c.offer.player_id,c.offer.player_id,sum(c.offer.salaries)+c.offer.signing_bonus,
                c.offer.signing_bonus,'synthetic bonus paid',(('signing_bonus',c.offer.signing_bonus),)) for c in contracts) if team=='a' else ()
            store.initialize_cash(team,cash,source='synthetic complete cash')
        return store

    def bridge(self,store):
        def forbidden(*_):self.fail('compact manual invoked AI')
        return Bridge(store,provider=forbidden,access_check=forbidden)

    def requests(self):
        amendment=asdict(test_restructures.PreseasonRestructureTests().scope())
        amendment.update(amended_on=amendment['amended_on'].isoformat(),
            first_regular_season_game=amendment['first_regular_season_game'].isoformat(),exclusions=sorted(amendment['exclusions']))
        return (test_release_bridge.ReleaseBridgeTests().request(),test_trade_bridge.TradeBridgeTests().request(),
            dict(protocol=1,request_id='amend',operation='manual_restructure',team_id='a',player_id='v',
                expected_revision=1,timeout_ms=5000,decision_mode='manual',scope=amendment,converted_base=4))

    def test_all_three_project_exact_stored_receipts_and_retry_without_relabeling_events(self):
        for request in self.requests():
            with self.subTest(operation=request['operation']),tempfile.TemporaryDirectory() as directory:
                store=self.setup_store(directory);bridge=self.bridge(store)
                request={**request,'receipt_format':'target_v1'}
                result=bridge.handle(request)
                self.assertIsNone(result['error'],result)
                self.assertEqual(result['result']['receipt_format'],'target_v1')
                self.assertEqual(bridge.handle(request),result)
                full_request=dict(request);full_request.pop('receipt_format')
                full=bridge.handle(full_request)
                self.assertNotIn('receipt_format',full['result'])
                self.assertEqual(result['result'],compact_lifecycle_result(full['result'],request['operation']))
                receipt=result['result'][{'manual_release':'release','manual_restructure':'restructure','manual_trade':'trade'}[request['operation']]]
                participants=receipt.values() if request['operation']=='manual_trade' else (receipt,)
                for posting in participants:
                    self.assertEqual(len(posting['financial']),4)
                    self.assertTrue({'revision','charges','signed_players'} <= set(posting['financial']))
                    self.assertEqual(set(posting['cash']['other_obligations']),{'count','nominal_total','paid_total','unpaid_total'})
                    self.assertEqual(set(posting['cash']),{'revision','nominal_total','paid_total','unpaid_total','obligations','other_obligations'})
                    self.assertEqual(len(posting['cash']['obligations']),1)
                with closing(sqlite3.connect(store.path)) as db:
                    for (payload,) in db.execute("SELECT payload FROM events WHERE kind IN ('release','trade_out','trade_in','restructure')"):
                        self.assertNotIn('receipt_format',payload)
                        self.assertIn('"source"',payload)
                changed={**request,'receipt_format':'unknown'}
                before=Path(store.path).read_bytes()
                self.assertEqual(bridge.handle(changed)['error'],'invalid_request')
                self.assertEqual(Path(store.path).read_bytes(),before)

    def test_target_cash_and_totals_must_agree_and_projection_does_not_mutate_full_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory);request=self.requests()[0]
            full=self.bridge(store).handle(request)['result'];original=deepcopy(full)
            compact_lifecycle_result(full,'manual_release');self.assertEqual(full,original)
            for scenario in ('target','totals','duplicate','player'):
                changed=deepcopy(full);cash=changed['release']['cash']
                if scenario=='target':cash['obligations'][0]['source']='changed source'
                if scenario=='totals':cash['nominal_total']+=1
                if scenario=='duplicate':cash['obligations'].append(deepcopy(cash['obligations'][0]))
                if scenario=='player':changed['release']['financial']['released_contracts']['v']['cash_obligation']['player_id']='other'
                with self.subTest(scenario=scenario),self.assertRaises(ValueError):compact_lifecycle_result(changed,'manual_release')

    def test_53_player_long_release_history_commits_compact_and_preserves_full_history(self):
        with tempfile.TemporaryDirectory() as directory:
            contracts=tuple(ActiveContract(Offer('player-'+str(i),(1000000,)*3,9000000,(0,1000000,1000000)),
                'synthetic original contract') for i in range(53))
            store=self.setup_store(directory,contracts);plan=test_releases.PreseasonReleaseTests().plan()
            for i,c in enumerate(contracts[:29]):
                store.release_preseason_veteran('a','release-'+str(i),c.offer.player_id,scope=plan.scope,
                    discount=plan.discount,payment_year_offsets=(0,1,2),expected_revision=i+1,access_check=lambda:None)
            request=self.requests()[0]
            request.update(request_id='release-29',player_id='player-29',expected_revision=30,timeout_ms=60000)
            bridge=self.bridge(store);before=store.load_team('a').generation_snapshot()
            self.assertEqual(bridge.handle(request)['error'],'response_too_large')
            self.assertEqual(store.load_team('a').generation_snapshot(),before)
            request['receipt_format']='target_v1';reply=bridge.handle(request)
            self.assertIsNone(reply['error'],reply)
            self.assertLess(len(json.dumps(reply,allow_nan=False).encode('utf-8'))+1,65536)
            self.assertEqual(len(reply['result']['release']['financial']['released_contracts']),1)
            self.assertEqual(reply['result']['release']['cash']['other_obligations']['count'],52)
            self.assertEqual(bridge.handle(request),reply)
            self.assertEqual(len(store.load_team('a').financial_snapshot()['released_contracts']),30)
            with closing(sqlite3.connect(store.path)) as db:
                payload=json.loads(db.execute("SELECT payload FROM events WHERE request_key='release:release-29'").fetchone()[0])
                self.assertEqual(len(payload['posting']['released_contracts']),30)
                self.assertEqual(len(payload['cash_posting']['obligations']),53)

    def test_format_allowed_only_on_exact_supported_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge=self.bridge(self.setup_store(directory))
            for request in ({'protocol':1,'request_id':'hello','operation':'hello','receipt_format':'target_v1'},
                            {**self.requests()[0],'receipt_format':None},
                            {**self.requests()[0],'receipt_format':'target_v1','unknown':True}):
                self.assertEqual(bridge.handle(request)['error'],'invalid_request')

    def test_versioned_trade_and_historical_compact_retry_keep_agreement_binding(self):
        from tests import test_generation_trade_store
        fixture=test_generation_trade_store.GenerationTradeStoreTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        scope=asdict(fixture.scope)
        for key in ('traded_on','seller_first_regular_season_game','buyer_first_regular_season_game'):scope[key]=scope[key].isoformat()
        scope['exclusions']=sorted(scope['exclusions'])
        request=dict(protocol=1,request_id='assignment',operation='manual_trade',seller='a',buyer='b',player_id='v',
            seller_revision=6,buyer_revision=1,timeout_ms=5000,decision_mode='manual',scope=scope,
            seller_generation_id=fixture.return_id,buyer_previous_generation_id=None,receipt_format='target_v1')
        bridge=self.bridge(fixture.store);response=bridge.handle(request)
        self.assertIsNone(response['error'],response)
        result=response['result'];self.assertEqual(result['seller_generation_id'],fixture.return_id)
        buyer_id=result['buyer_generation_id']
        self.assertEqual(result['trade']['a']['cash']['obligations'][0]['obligation_id'],fixture.return_id)
        self.assertEqual(result['trade']['b']['cash']['obligations'][0]['obligation_id'],buyer_id)
        fixture.store.trade_preseason_veteran('back','b','a','v',scope=fixture.scope,
            seller_revision=2,buyer_revision=7,access_check=lambda:None)
        before=fixture.snapshots()
        self.assertEqual(bridge.handle(request),response)
        self.assertEqual(fixture.snapshots(),before)
        self.assertIn('v',fixture.store.load_team('a')._players)
        self.assertNotIn('v',fixture.store.load_team('b')._players)

    def test_returned_restructure_compact_record_binds_explicit_generation(self):
        from tests import test_return_restructure
        fixture=test_return_restructure.ReturnedRestructureTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        scope=asdict(fixture.scope);scope.update(amended_on=fixture.scope.amended_on.isoformat(),
            first_regular_season_game=fixture.scope.first_regular_season_game.isoformat(),exclusions=sorted(fixture.scope.exclusions))
        request=dict(protocol=1,request_id='conversion',operation='manual_restructure',team_id='a',player_id='v',
            expected_revision=6,timeout_ms=5000,decision_mode='manual',scope=scope,converted_base=4,
            generation_id=fixture.gid,receipt_format='target_v1')
        bridge=self.bridge(fixture.store);response=bridge.handle(request)
        self.assertIsNone(response['error'],response)
        self.assertEqual(response['result']['generation_id'],fixture.gid)
        cash=response['result']['restructure']['cash']
        self.assertEqual(cash['obligations'][0]['obligation_id'],fixture.gid)
        self.assertEqual(cash['other_obligations']['count'],1)
        self.assertEqual(bridge.handle(request),response)
