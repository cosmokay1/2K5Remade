from copy import deepcopy
import unittest
from franchise.bridge import Bridge
from tests import test_layered_restructure_store


class CalendarHistoryBridgeTests(unittest.TestCase):
    def setUp(self):
        fixture=test_layered_restructure_store.LayeredRestructureStoreTests();fixture.setUp()
        self.addCleanup(fixture.doCleanups);self.fixture=fixture;fixture.amend()
        fixture.store.bind_actor('a','v',{'money':0.8},{'trust':0.6},access_check=lambda:None)
        def forbidden(*_):raise AssertionError('Accounting read invoked AI')
        self.bridge=Bridge(fixture.store,provider=forbidden,access_check=forbidden)
        self.contract=dict(protocol=1,request_id='history',operation='contract_context',team_id='a',
            generation_id=fixture.gid,context_format='calendar_v4',timeout_ms=5000)
        self.player=dict(protocol=1,request_id='player-history',operation='player_context',team_id='a',
            player_id='v',context_format='calendar_v4',timeout_ms=5000)

    def test_exact_history_original_terms_and_scoped_player_reads_are_read_only(self):
        before=self.fixture.path.read_bytes()
        reply=self.bridge.handle(self.contract);self.assertIsNone(reply['error'])
        context=reply['result'];self.assertEqual(context['format'],5)
        self.assertEqual(context['original_contract']['elapsed_years'],0)
        self.assertEqual(context['original_contract']['offer']['salaries'],[2000000]*3)
        self.assertEqual(context['economic_archive']['contract']['offer']['salaries'],[2000000,1900000,1800000])
        self.assertEqual(len(context['amendment_history']['prior_restructures']),1)
        player=self.bridge.handle(self.player);self.assertIsNone(player['error'])
        self.assertEqual(player['result']['calendar_contract_context'],context)
        self.assertEqual(player['result']['personality'],{'money':0.8})
        self.assertEqual(player['result']['relationships'],{'trust':0.6})
        foreign=self.bridge.handle({**self.contract,'team_id':'b'})
        self.assertIsNotNone(foreign['error'])
        scoped=self.bridge.handle({**self.player,'team_id':'b'});self.assertIsNone(scoped['error'])
        self.assertIsNone(scoped['result']['calendar_contract_context'])
        self.assertIsNone(scoped['result']['personality'])
        old=self.bridge.handle({**self.contract,'context_format':'calendar_v3'})
        normalized=deepcopy(context);normalized.pop('original_contract');normalized.pop('amendment_history');normalized['format']=4
        self.assertEqual(old['result'],normalized)
        self.assertEqual(self.fixture.path.read_bytes(),before)

    def test_expiry_preserves_history_and_disconnect_or_bad_format_changes_nothing(self):
        history=self.bridge.handle(self.contract)['result']['amendment_history']
        self.fixture.expire();before=self.fixture.path.read_bytes()
        context=self.bridge.handle(self.contract)['result']
        self.assertEqual(context['calendar_accounting']['status'],'expired')
        self.assertEqual(context['amendment_history'],history)
        self.assertEqual(context['economic_archive']['cash_obligation']['paid'],9000000)
        calls=[]
        def disconnected():
            calls.append(1)
            if len(calls)>1:raise TimeoutError('synthetic context disconnect')
        self.bridge.connection_check=disconnected
        self.assertEqual(self.bridge.handle(self.contract)['error'],'timeout')
        self.bridge.connection_check=lambda:None
        for request in (self.contract,self.player):
            for value in ('calendar_v5',True,4):
                self.assertIsNotNone(self.bridge.handle({**request,'context_format':value})['error'])
        self.assertEqual(self.fixture.path.read_bytes(),before)
