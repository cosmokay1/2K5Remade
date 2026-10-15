"""Validate the authored inputs used by the real Windows C-client check."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from franchise.bridge import Bridge
from franchise.store import FranchiseStore
from tools.check_native_saved_signing import fixture


class NativeSavedSigningFixtureTests(unittest.TestCase):
    def test_captured_acceptance_replays_and_saved_journal_settles_without_another_provider_call(self):
        with tempfile.TemporaryDirectory() as directory:
            data=fixture(Path(directory));paths=data['paths'];sample=data['sample']
            forbidden=Mock(side_effect=AssertionError('Native replay/settlement must not invoke a model'))
            bridge=Bridge(FranchiseStore(data['database']),provider=forbidden,access_check=lambda:None,
                guest_snapshot=(sample.bindings,sample.before),guest_signing_reader=lambda:paths['save'].read_bytes())
            proposal=json.loads(paths['proposal'].read_text())
            replay=bridge.handle(proposal)
            self.assertEqual(replay,data['reply'])
            prepare=dict(protocol=1,request_id='native-captured-guest',operation='guest_signing_prepare',timeout_ms=10000,
                team_id='49ers',proposal_request_id=proposal['request_id'],guest_offer=proposal['guest_offer'],expected_revision=1,
                expected_before_sha256=hashlib.sha256(sample.before).hexdigest(),
                live_finance_sha256=hashlib.sha256(paths['finance'].read_bytes()).hexdigest())
            self.assertIsNone(bridge.handle(prepare)['error'])
            paths['save'].write_bytes(sample.after)
            confirm=dict(protocol=1,request_id='native-confirm',operation='guest_signing_confirm',timeout_ms=10000,
                journal_request_id=prepare['request_id'],expected_after_sha256=hashlib.sha256(sample.after).hexdigest())
            receipt=bridge.handle(confirm)
            self.assertIsNone(receipt['error'],receipt)
            self.assertEqual(bridge.handle(confirm),receipt)
            self.assertEqual(receipt['result']['financial_revision'],2)
            self.assertIsNone(bridge.store.load_team('49ers').cash_snapshot()['nominal_total'])
            forbidden.assert_not_called();data['provider'].assert_called_once()
