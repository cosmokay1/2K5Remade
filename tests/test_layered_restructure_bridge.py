from dataclasses import asdict
import unittest
from franchise.bridge import Bridge
from tests import test_layered_restructure_store


class LayeredRestructureBridgeTests(unittest.TestCase):
    def setUp(self):
        fixture=test_layered_restructure_store.LayeredRestructureStoreTests();fixture.setUp()
        self.addCleanup(fixture.doCleanups);self.fixture=fixture
        def forbidden(*_):raise AssertionError('Manual amendment invoked AI')
        self.bridge=Bridge(fixture.store,provider=forbidden,access_check=forbidden)
        scope=asdict(fixture.inputs['scope'])
        scope.update(amended_on=scope['amended_on'].isoformat(),
            first_regular_season_game=scope['first_regular_season_game'].isoformat(),exclusions=sorted(scope['exclusions']))
        self.request=dict(protocol=1,request_id='second-2028',operation='manual_restructure',team_id='a',player_id='v',
            expected_revision=fixture.inputs['expected_revision'],timeout_ms=5000,decision_mode='manual',
            calendar_format='calendar_v2',generation_id=fixture.gid,scope=scope,converted_base=200000)

    def test_full_compact_and_historical_retries_preserve_history_after_expiry(self):
        before=self.fixture.path.read_bytes()
        self.assertIsNotNone(self.bridge.handle({**self.request,'calendar_format':'calendar_v1'})['error'])
        self.assertEqual(self.fixture.path.read_bytes(),before)
        full=self.bridge.handle(self.request);self.assertIsNone(full['error'])
        compact=self.bridge.handle({**self.request,'receipt_format':'target_v1'});self.assertIsNone(compact['error'])
        self.assertEqual(full['result']['restructure']['format'],3)
        self.assertEqual(compact['result']['restructure']['amendment_history'],full['result']['restructure']['amendment_history'])
        self.fixture.expire();before=self.fixture.path.read_bytes()
        self.assertEqual(self.bridge.handle(self.request),full)
        self.assertEqual(self.bridge.handle({**self.request,'receipt_format':'target_v1'}),compact)
        self.assertEqual(self.fixture.path.read_bytes(),before)

    def test_final_disconnect_and_bad_format_leave_database_unchanged(self):
        before=self.fixture.path.read_bytes();calls=[]
        def disconnected():
            calls.append(1)
            if len(calls)>1:raise TimeoutError('synthetic final disconnect')
        self.bridge.connection_check=disconnected
        self.assertEqual(self.bridge.handle(self.request)['error'],'timeout')
        self.assertEqual(self.fixture.path.read_bytes(),before)
        self.bridge.connection_check=lambda:None
        for change in ({'calendar_format':'calendar_v3'},{'generation_id':True},{'converted_base':True}):
            self.assertIsNotNone(self.bridge.handle({**self.request,**change})['error'])
            self.assertEqual(self.fixture.path.read_bytes(),before)
