import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock

from franchise.bridge import Bridge
from franchise.control import AccessDisabled
import test_reconcile_signing_context as checkpoints


class SigningContextBridgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = checkpoints.SigningContextTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.provider = Mock(side_effect=AssertionError('No model call for checkpoint'))
        self.access = Mock(side_effect=AccessDisabled('Disabled'))
        self.bridge = Bridge(self.fixture.store, provider=self.provider, access_check=self.access,
                             guest_snapshot=(self.fixture.bindings, self.fixture.payload))
        self.request = dict(protocol=1, request_id='checkpoint', operation='signing_context',
                            observation=self.fixture.observation, expected_revision=0, timeout_ms=5000)

    def test_read_context_works_while_ai_disabled_and_mutates_no_finances(self):
        before = self.fixture.store.load_team('49ers').financial_snapshot()
        hello = self.bridge.handle(dict(protocol=1, request_id='hello', operation='hello'))
        self.assertEqual(hello['error'], 'ai_disabled')
        result = self.bridge.handle(self.request)
        self.assertIsNone(result['error'])
        self.assertTrue(result['result']['player_context']['classification_pending'])
        self.assertFalse(result['result']['ai_authorized'])
        self.assertFalse(result['result']['write_authorized'])
        self.assertEqual(before, self.fixture.store.load_team('49ers').financial_snapshot())
        self.provider.assert_not_called()
        self.assertEqual(self.access.call_count, 1)

    def test_missing_configuration_stale_revision_and_extra_paths_reject(self):
        bridge = Bridge(self.fixture.store, provider=self.provider, access_check=self.access)
        self.assertEqual(bridge.handle(self.request)['error'], 'state_rejected')
        self.assertEqual(self.bridge.handle({**self.request, 'expected_revision': 1})['error'], 'state_rejected')
        self.assertEqual(self.bridge.handle({**self.request, 'save': '/other/save'})['error'], 'invalid_request')
        self.provider.assert_not_called()
        self.access.assert_not_called()

    def test_disconnect_denies_read_result(self):
        self.bridge.connection_check = Mock(side_effect=AccessDisabled('Disconnected'))
        self.assertEqual(self.bridge.handle(self.request)['error'], 'ai_disabled')
        self.provider.assert_not_called()

    def test_saved_performance_keeps_identity_and_missing_metrics_unknown(self):
        request={**self.request,'performance_format':'saved_history_v1'}
        reply=self.bridge.handle(request)
        self.assertIsNone(reply['error'])
        evidence=reply['result']['performance_context']
        self.assertEqual(evidence['player_id'],reply['result']['player_id'])
        self.assertFalse(evidence['history_present'])
        self.assertEqual(evidence['saved_history'],[])
        self.assertEqual(len(evidence['missing_named_metrics']),10)
        self.assertEqual(evidence['unmapped_requested_metrics'],['tackles','targets','pressures','qb_hits'])
        self.assertNotIn('performance_context',self.bridge.handle(self.request)['result'])
        self.assertEqual(self.bridge.handle({**request,'performance_format':'live'})['error'],'invalid_request')
        self.provider.assert_not_called(); self.access.assert_not_called()

    def test_live_guest_terms_reject_modern_horizon_and_missing_minimum_without_model(self):
        before=self.fixture.store.load_team('49ers').financial_snapshot()
        request={**self.request,'guest_offer':{'amount_word':1949,'flags_word':(2<<29)|(6<<16)|4}}
        reply=self.bridge.handle(request)
        self.assertIsNone(reply['error'])
        self.assertEqual(reply['result']['offer_context']['outcome'],'format_rejected')
        self.assertIn('five-year',reply['result']['offer_context']['reason'])
        request['guest_offer']={'amount_word':600,'flags_word':(2<<29)|(3<<16)}
        reply=self.bridge.handle(request)
        self.assertIsNone(reply['error'])
        self.assertEqual(reply['result']['offer_context']['outcome'],'accounting_rejected')
        self.assertIsNone(reply['result']['offer_context']['preview'])
        self.assertFalse(reply['result']['write_authorized'])
        self.assertEqual(before,self.fixture.store.load_team('49ers').financial_snapshot())
        self.provider.assert_not_called(); self.access.assert_not_called()

    def test_actual_process_uses_server_pinned_snapshot_despite_missing_adc(self):
        root = Path(self.fixture.temporary.name)
        save, bindings = root / 'authored.dat', root / 'bindings.json'
        save.write_bytes(self.fixture.payload); bindings.write_text(json.dumps(self.fixture.bindings))
        environment = dict(os.environ, GOOGLE_APPLICATION_CREDENTIALS=str(root / 'missing-adc.json'))
        command = [sys.executable, '-m', 'franchise.sidecar', '--database', str(self.fixture.store.path),
                   '--provider', 'vertex', '--impersonate-runtime', '--guest-save', str(save),
                   '--guest-bindings', str(bindings)]
        completed = subprocess.run(command, input=json.dumps(self.request)+'\n', text=True,
                                   capture_output=True, env=environment, check=True, timeout=10)
        result = json.loads(completed.stdout)
        self.assertIsNone(result['error'])
        self.assertEqual(result['result']['player_id'], self.fixture.bindings['players'][1]['player_id'])
        self.assertFalse(result['result']['ai_authorized'])
        self.assertEqual(self.fixture.store.load_team('49ers').revision, 0)

    def captured_proposal(self):
        return {**self.request, 'operation': 'negotiate_proposal',
                'guest_offer': {'amount_word': 829, 'flags_word': (1<<29)|(2<<16)|4}}

    def classified_bridge(self, provider, access=lambda: None):
        # Authored fixture floors only; do not assign a policy to real players.
        from franchise.books import OpeningBooks
        from franchise.cap import Ledger
        from franchise.store import FranchiseStore
        from tools.export_legacy_contracts import legacy_contracts
        player = self.fixture.bindings['players'][1]['player_id']
        store = FranchiseStore(Path(self.fixture.temporary.name)/'classified.sqlite')
        store.create_franchise({'49ers': Ledger.from_opening(OpeningBooks(
            legacy_contracts=legacy_contracts(self.fixture.bindings,self.fixture.payload)['49ers']),
            cap=80500000, roster_reserve=0, max_bonus_years=5,
            veteran_minimums={player: (1000,)*15})}, seed=self.fixture.bindings['personality_seed'])
        return Bridge(store, provider=provider, access_check=access,
            guest_snapshot=(self.fixture.bindings,self.fixture.payload))

    def test_captured_proposal_requires_control_and_known_minimum_before_inference(self):
        request = self.captured_proposal()
        self.assertEqual(self.bridge.handle(request)['error'], 'ai_disabled')
        self.bridge.access_check = lambda: None
        reply = self.bridge.handle(request)
        self.assertEqual(reply['error'], 'state_rejected')
        self.assertIn('classification', reply['detail'].lower())
        self.provider.assert_not_called()
        self.assertEqual(self.fixture.store.negotiation_history('49ers',self.fixture.bindings['players'][1]['player_id']), [])

    def test_captured_proposal_derives_actor_performance_offer_and_replays_without_signing(self):
        calls=[]
        def provider(context):
            calls.append(context)
            return json.dumps(dict(action='accept', reason='Agreement proposed', salaries=None, signing_bonus=None))
        bridge = self.classified_bridge(provider)
        request = self.captured_proposal()
        before = bridge.store.load_team('49ers').financial_snapshot()
        reply = bridge.handle(request)
        self.assertIsNone(reply['error'])
        result = reply['result']; checkpoint = result['signing_checkpoint']
        self.assertEqual(result['outcome'], 'accepted_proposal')
        self.assertEqual(calls[0]['personality'], checkpoint['player_context']['personality'])
        self.assertEqual(calls[0]['relationships'], checkpoint['player_context']['relationships'])
        self.assertEqual(calls[0]['performance'], checkpoint['performance_context'])
        self.assertFalse(calls[0]['performance']['history_present'])
        self.assertEqual(result['offer'], checkpoint['offer_context']['offer'])
        self.assertFalse(checkpoint['ai_authorized']); self.assertFalse(checkpoint['write_authorized'])
        from franchise.store import FranchiseStore
        reopened = Bridge(FranchiseStore(bridge.store.path), provider=lambda _: self.fail('Repeated inference'),
            access_check=lambda: None, guest_snapshot=bridge.guest_snapshot)
        replay = reopened.handle(request)
        self.assertIsNone(replay['error'])
        self.assertEqual(replay['result']['evidence'], result['evidence'])
        self.assertEqual(bridge.store.load_team('49ers').financial_snapshot(), before)
        self.assertEqual(len(calls), 1)

    def test_captured_reaction_retry_keeps_old_evidence_and_fresh_changed_opinion(self):
        calls=[]
        def provider(context):
            calls.append(context)
            return json.dumps(dict(action='reject', reason='Please take our concerns seriously.',
                salaries=None, signing_bonus=None, reaction='offended' if len(calls)==1 else 'none'))
        bridge=self.classified_bridge(provider)
        request=self.captured_proposal()
        before=bridge.store.load_team('49ers').financial_snapshot()
        first=bridge.handle(request)
        self.assertIsNone(first['error'])
        from franchise.store import FranchiseStore
        reopened=Bridge(FranchiseStore(bridge.store.path),provider=provider,
            access_check=lambda:None,guest_snapshot=bridge.guest_snapshot)
        retry=reopened.handle(request)
        self.assertIsNone(retry['error'])
        self.assertEqual(retry['result']['evidence'],first['result']['evidence'])
        self.assertEqual(retry['result']['reaction_effect'],first['result']['reaction_effect'])
        self.assertEqual(retry['result']['signing_checkpoint']['player_context']['relationships']['respect'],0.45)
        self.assertEqual(len(calls),1)
        request={**request,'request_id':'improved','guest_offer':{**request['guest_offer'],'amount_word':830}}
        self.assertIsNone(reopened.handle(request)['error'])
        self.assertEqual(calls[-1]['relationships']['respect'],0.45)
        self.assertEqual(bridge.store.load_team('49ers').financial_snapshot(),before)

    def test_recalled_acceptance_cannot_ignore_changed_opinion(self):
        calls=[]
        def provider(context):
            calls.append(context)
            return json.dumps(dict(action='accept' if len(calls)==1 else 'reject',
                reason='Response to the actual terms.',salaries=None,signing_bonus=None,
                reaction='none' if len(calls)==1 else 'offended'))
        bridge=self.classified_bridge(provider)
        request=self.captured_proposal()
        self.assertEqual(bridge.handle(request)['result']['outcome'],'accepted_proposal')
        self.assertIsNone(bridge.handle({**request,'request_id':'later-rejected-offer'})['error'])
        self.assertEqual(bridge.handle(request)['error'],'state_rejected')
        self.assertEqual(len(calls),2)

    def test_captured_proposal_rejects_overridden_actor_source_terms_and_revision(self):
        import copy
        bridge = self.classified_bridge(self.provider)
        request = self.captured_proposal()
        for field in ('personality','performance','relationships','team_id','offer','save'):
            with self.subTest(field=field):
                self.assertEqual(bridge.handle({**request,field:{}})['error'], 'invalid_request')
        changed = copy.deepcopy(request); changed['observation']['biography']['dob_region_raw']='000001'
        self.assertEqual(bridge.handle(changed)['error'], 'state_rejected')
        self.assertEqual(bridge.handle({**request,'expected_revision':1})['error'], 'state_rejected')
        changed = copy.deepcopy(request); changed['guest_offer']['flags_word']=(6<<16)|4
        self.assertEqual(bridge.handle(changed)['error'], 'state_rejected')
        self.provider.assert_not_called()

    def test_captured_proposal_rechecks_shutdown_before_model_dispatch(self):
        access = Mock(side_effect=[None, AccessDisabled('Disabled after checkpoint')])
        bridge = self.classified_bridge(self.provider, access)
        self.assertEqual(bridge.handle(self.captured_proposal())['error'], 'ai_disabled')
        self.provider.assert_not_called()

    def test_captured_request_cannot_relabel_a_client_supplied_evidence_proposal(self):
        provider = Mock(return_value=json.dumps(dict(action='accept',reason='Authored',salaries=None,signing_bonus=None)))
        bridge = self.classified_bridge(provider)
        request = self.captured_proposal()
        context_request = {**request,'operation':'signing_context','performance_format':'saved_history_v1'}
        checkpoint = bridge.handle(context_request)['result']
        direct = dict(protocol=1,request_id=request['request_id'],operation='negotiate_proposal',
            team_id=checkpoint['team_id'],offer=checkpoint['offer_context']['offer'],
            expected_revision=0,timeout_ms=5000,contract_format='original_fxg_v1',
            personality=checkpoint['player_context']['personality'],
            relationships=checkpoint['player_context']['relationships'],performance={'games':16})
        self.assertIsNone(bridge.handle(direct)['error'])
        reply = bridge.handle(request)
        self.assertEqual(reply['error'],'state_rejected')
        self.assertIn('evidence',reply['detail'])
        self.assertEqual(provider.call_count,1)
        self.assertEqual(bridge.store.load_team('49ers').revision,0)


if __name__ == '__main__':
    unittest.main()
