"""Loaded-image matching gates configured sessions, never guest write authority."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger
from franchise.control import AccessDisabled
from franchise.store import FranchiseStore
from tools.franchise_game_context import raw_context
from tools.franchise_snapshot_bindings import create_bindings
import test_legacy_contracts as fixtures


class RuntimeHandshakeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = FranchiseStore(Path(directory.name)/'state.sqlite')
        self.store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(1,)}))
        self.payload = bytes(fixtures.LegacyContractsTests().fixture())
        self.bindings = create_bindings(self.payload,game_xbe=b'authored source bytes',
            game_context={**raw_context(self.payload),'loaded_image_sha256':'a'*64})
        self.calls = 0
        self.allowed = True
        def provider(_):
            self.calls += 1
            return json.dumps(dict(action='reject',reason='Authored rejection',salaries=None,signing_bonus=None))
        self.provider = provider
        self.bridge = self.restart()

    def restart(self):
        return Bridge(self.store,provider=self.provider,access_check=lambda:self.allowed,
            guest_snapshot=(copy.deepcopy(self.bindings),self.payload))

    def hello(self, **changes):
        return dict(protocol=1,request_id='hello',operation='hello',loaded_image_sha256='a'*64,**changes)

    def proposal(self):
        return dict(protocol=1,request_id='proposal',operation='negotiate_proposal',team_id='a',
            offer=dict(player_id='v',salaries=[10],signing_bonus=0),expected_revision=0,
            timeout_ms=1000,personality={},performance={},relationships={})

    def test_any_explicit_digest_uses_same_handshake_and_echoes_registry(self):
        for image in ('a'*64,'c'*64):
            self.bindings['game_context']['loaded_image_sha256']=image
            bridge=self.restart();request=self.hello();request['loaded_image_sha256']=image
            reply=bridge.handle(request)
            self.assertIsNone(reply['error'])
            binding=reply['result']['runtime_binding']
            self.assertEqual(binding,dict(loaded_image_sha256=image,franchise_id=self.bindings['franchise_id'],
                snapshot_payload_sha256=hashlib.sha256(self.payload).hexdigest(),
                bindings_sha256=hashlib.sha256(json.dumps(self.bindings,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
            self.assertNotIn('write_authorized',binding)
            self.assertEqual(self.calls,0)

    def test_missing_wrong_and_source_digest_never_grant(self):
        for value in (None,'b'*64,'A'*64,self.bindings['game_context']['source_image_sha256'],False):
            request=self.hello()
            if value is None: request.pop('loaded_image_sha256')
            else: request['loaded_image_sha256']=value
            self.assertIsNotNone(self.bridge.handle(request)['error'])
            self.assertEqual(self.bridge.handle(self.proposal())['error'],'ai_disabled')
        self.assertEqual(self.calls,0)
        self.assertEqual(self.store.load_team('a').revision,0)

    def test_restart_and_failed_rehandshake_require_new_match(self):
        self.assertEqual(self.bridge.handle(self.proposal())['error'],'ai_disabled')
        self.assertIsNone(self.bridge.handle(self.hello())['error'])
        self.assertIsNone(self.bridge.handle(self.proposal())['error'])
        self.assertEqual(self.calls,1)
        bridge=self.restart()
        self.assertEqual(bridge.handle(self.proposal())['error'],'ai_disabled')
        self.assertIsNone(bridge.handle(self.hello())['error'])
        request=self.hello();request['protocol']=2
        self.assertEqual(bridge.handle(request)['error'],'protocol_mismatch')
        self.assertEqual(bridge.handle(self.proposal())['error'],'ai_disabled')
        self.assertEqual(self.calls,1)

    def test_matching_image_cannot_bypass_disabled_remote_control(self):
        for check in (lambda:False, self.disabled):
            self.bridge.access_check=check
            self.assertEqual(self.bridge.handle(self.hello())['error'],'ai_disabled')
            self.assertEqual(self.bridge.handle(self.proposal())['error'],'ai_disabled')
        self.assertEqual(self.calls,0)

    def test_matched_session_rechecks_control_before_inference(self):
        self.assertIsNone(self.bridge.handle(self.hello())['error'])
        self.allowed=False
        self.assertEqual(self.bridge.handle(self.proposal())['error'],'ai_disabled')
        self.assertEqual(self.calls,0)
        self.assertEqual(self.store.negotiation_history('a','v'),[])

    @staticmethod
    def disabled():
        raise AccessDisabled('Authored shutdown')

    def test_unbound_status_and_preview_stay_available_but_journal_writes_hold(self):
        for operation in ('guest_signing_prepare','guest_signing_confirm','negotiate'):
            self.assertEqual(self.bridge.handle(dict(protocol=1,request_id='x',operation=operation))['error'],'ai_disabled')
        request=self.proposal();request['operation']='preview'
        for key in ('personality','performance','relationships'):request.pop(key)
        self.assertEqual(self.bridge.handle(request)['result']['room_after'],90)
        status=self.bridge.handle(dict(protocol=1,request_id='status',operation='guest_signing_status'))
        self.assertEqual(status['error'],'state_rejected')  # Unconfigured journal, not an AI gate.
        self.assertEqual(self.calls,0)

    def test_image_claim_without_explicit_expected_context_rejects(self):
        self.bindings['game_context'].pop('loaded_image_sha256')
        bridge=self.restart()
        self.assertEqual(bridge.handle(self.hello())['error'],'invalid_request')
        request=self.hello();request.pop('loaded_image_sha256')
        self.assertIsNone(bridge.handle(request)['error'])  # Existing engine-only fixture compatibility.
