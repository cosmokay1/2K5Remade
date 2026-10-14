from copy import deepcopy
from dataclasses import asdict
import unittest
from unittest.mock import patch
from franchise.bridge import Bridge,ResponseTooLarge
from franchise.receipts import compact_lifecycle_result
from tests import test_layered_trade_store


class LayeredTradeBridgeTests(unittest.TestCase):
    def setUp(self):
        fixture=test_layered_trade_store.LayeredTradeStoreTests();fixture.setUp()
        self.addCleanup(fixture.doCleanups);self.fixture=fixture
        def forbidden(*_):raise AssertionError('Manual assignment invoked AI')
        self.bridge=Bridge(fixture.store,provider=forbidden,access_check=forbidden)
        scope=asdict(fixture.inputs['scope']);scope.update(exclusions=sorted(scope['exclusions']))
        for field in ('traded_on','seller_first_regular_season_game','buyer_first_regular_season_game'):
            scope[field]=scope[field].isoformat()
        self.request=dict(protocol=1,request_id='assignment',operation='manual_trade',seller='a',buyer='b',player_id='v',
            seller_revision=fixture.inputs['seller_revision'],buyer_revision=fixture.inputs['buyer_revision'],
            timeout_ms=5000,decision_mode='manual',calendar_format='calendar_v2',seller_generation_id=fixture.gid,
            buyer_previous_generation_id=None,scope=scope)

    def test_full_compact_history_and_separate_buyer_cash_survive_next_roll(self):
        before=self.fixture.path.read_bytes()
        self.assertIsNotNone(self.bridge.handle({**self.request,'calendar_format':'calendar_v1'})['error'])
        self.assertEqual(self.fixture.path.read_bytes(),before)
        full=self.bridge.handle(self.request);self.assertIsNone(full['error'])
        compact=self.bridge.handle({**self.request,'receipt_format':'target_v1'});self.assertIsNone(compact['error'])
        self.assertEqual(full['result']['format'],3)
        self.assertEqual(full['result']['amendment_history'],self.fixture.original.amendment_history_snapshot())
        self.assertEqual(compact['result'],compact_lifecycle_result(full['result'],'manual_trade'))
        self.assertEqual(compact['result']['trade']['a']['cash']['paid_total'],7200000)
        self.assertEqual(compact['result']['trade']['b']['cash']['nominal_total'],3800000)
        self.fixture.fixture.pay('b','base:0',1800000);self.fixture.fixture.roll(('a','b'),2028)
        before=self.fixture.path.read_bytes()
        self.assertEqual(self.bridge.handle(self.request),full)
        self.assertEqual(self.bridge.handle({**self.request,'receipt_format':'target_v1'}),compact)
        self.assertEqual(self.fixture.path.read_bytes(),before)
        for scenario in ('missing','empty','source','cursor','format'):
            result=deepcopy(full['result'])
            if scenario=='missing':del result['amendment_history']
            elif scenario=='empty':result['amendment_history']['prior_restructures']=[]
            elif scenario=='source':result['amendment_history']['latest_restructure']['contract']['source']='changed'
            elif scenario=='cursor':result['league_year']=2029
            else:result['format']=2
            with self.subTest(scenario=scenario),self.assertRaises(ValueError):
                compact_lifecycle_result(result,'manual_trade')

    def test_disconnect_frame_rejection_and_invalid_identity_leave_both_books(self):
        before=self.fixture.path.read_bytes();calls=[]
        def disconnected():
            calls.append(1)
            if len(calls)>1:raise TimeoutError('synthetic final disconnect')
        self.bridge.connection_check=disconnected
        self.assertEqual(self.bridge.handle(self.request)['error'],'timeout')
        self.assertEqual(self.fixture.path.read_bytes(),before)
        self.bridge.connection_check=lambda:None
        with patch.object(self.bridge,'_require_frame',side_effect=ResponseTooLarge('synthetic frame cap')):
            self.assertIsNotNone(self.bridge.handle(self.request)['error'])
        self.assertEqual(self.fixture.path.read_bytes(),before)
        for change in ({'calendar_format':'calendar_v3'},{'seller_generation_id':True},{'buyer_revision':True}):
            self.assertIsNotNone(self.bridge.handle({**self.request,**change})['error'])
            self.assertEqual(self.fixture.path.read_bytes(),before)
