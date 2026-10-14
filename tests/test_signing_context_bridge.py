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


if __name__ == '__main__':
    unittest.main()
