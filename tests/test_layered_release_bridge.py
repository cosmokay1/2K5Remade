from dataclasses import asdict
import unittest
from franchise.bridge import Bridge
from tests import test_layered_release_store


class LayeredReleaseBridgeTests(unittest.TestCase):
    def setUp(self):
        fixture=test_layered_release_store.LayeredReleaseStoreTests();fixture.setUp()
        self.addCleanup(fixture.doCleanups);self.fixture=fixture
        def forbidden(*_):raise AssertionError('Manual release invoked AI')
        self.bridge=Bridge(fixture.store,provider=forbidden,access_check=forbidden)
        scope=asdict(fixture.inputs['scope'])
        scope.update(removed_on=scope['removed_on'].isoformat(),first_regular_season_game=scope['first_regular_season_game'].isoformat(),
            exclusions=sorted(scope['exclusions']))
        self.request=dict(protocol=1,request_id='layered-release',operation='manual_release',team_id='a',player_id='v',
            expected_revision=fixture.inputs['expected_revision'],timeout_ms=5000,decision_mode='manual',
            calendar_format='calendar_v2',generation_id=fixture.gid,scope=scope,
            discount=dict(league_year=2028,annual_rate=0,rate_source=fixture.inputs['discount'].rate_source),payment_year_offsets=[0])

    def test_full_compact_unpaid_liability_and_historical_retry_after_rollover(self):
        before=self.fixture.path.read_bytes()
        self.assertIsNotNone(self.bridge.handle({**self.request,'calendar_format':'calendar_v1'})['error'])
        self.assertEqual(self.fixture.path.read_bytes(),before)
        full=self.bridge.handle(self.request);self.assertIsNone(full['error'])
        compact=self.bridge.handle({**self.request,'receipt_format':'target_v1'});self.assertIsNone(compact['error'])
        self.assertEqual(full['result']['release']['format'],3)
        self.assertEqual(full['result']['release']['cash']['unpaid_total'],2000000)
        self.assertEqual(compact['result']['release']['amendment_history'],full['result']['release']['amendment_history'])
        self.fixture.next_year();before=self.fixture.path.read_bytes()
        self.assertEqual(self.bridge.handle(self.request),full)
        self.assertEqual(self.bridge.handle({**self.request,'receipt_format':'target_v1'}),compact)
        self.assertEqual(self.fixture.path.read_bytes(),before)

    def test_final_disconnect_bad_identity_and_frame_rejection_roll_back(self):
        from unittest.mock import patch
        from franchise.bridge import ResponseTooLarge
        before=self.fixture.path.read_bytes();calls=[]
        def disconnected():
            calls.append(1)
            if len(calls)>1:raise TimeoutError('synthetic final disconnect')
        self.bridge.connection_check=disconnected
        self.assertEqual(self.bridge.handle(self.request)['error'],'timeout')
        self.assertEqual(self.fixture.path.read_bytes(),before)
        self.bridge.connection_check=lambda:None
        for change in ({'calendar_format':'calendar_v3'},{'generation_id':True},{'expected_revision':True}):
            self.assertIsNotNone(self.bridge.handle({**self.request,**change})['error'])
            self.assertEqual(self.fixture.path.read_bytes(),before)
        with patch.object(self.bridge,'_require_frame',side_effect=ResponseTooLarge('synthetic oversized receipt')):
            self.assertIsNotNone(self.bridge.handle(self.request)['error'])
        self.assertEqual(self.fixture.path.read_bytes(),before)
