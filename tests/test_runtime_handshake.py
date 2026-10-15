"""Loaded-image matching gates configured sessions, never guest write authority."""
import contextlib
import copy
import hashlib
import json
import tempfile
import unittest
from unittest.mock import Mock
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
        self.payload = bytes(fixtures.LegacyContractsTests().fixture())
        self.bindings = create_bindings(self.payload,game_xbe=b'authored source bytes',
            game_context={**raw_context(self.payload),'loaded_image_sha256':'a'*64})
        from tools.export_legacy_contracts import legacy_contracts
        from tools.franchise_snapshot_bindings import resolve_bindings
        from tools.inspect_franchise_save import TEAMS
        from franchise.snapshot_origin import bind
        members=resolve_bindings(self.bindings,self.payload)
        self.player=members[1]['player_id']
        contracts=legacy_contracts(self.bindings,self.payload)
        teams={team:Ledger.from_opening(OpeningBooks(legacy_contracts=contracts[team]),cap=80500000,
            roster_reserve=0,max_bonus_years=5,veteran_minimums=({self.player:(1000,)} if team=='49ers' else {})) for team in TEAMS}
        self.store.create_franchise(teams,seed=self.bindings['personality_seed'])
        bind(self.store,self.bindings,self.payload)
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
        return dict(protocol=1,request_id='proposal',operation='negotiate_proposal',team_id='49ers',
            offer=dict(player_id=self.player,salaries=[1000],signing_bonus=0),expected_revision=0,
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
        self.assertEqual(self.store.load_team('49ers').revision,0)

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
        self.assertEqual(self.store.negotiation_history('49ers',self.player),[])

    @staticmethod
    def disabled():
        raise AccessDisabled('Authored shutdown')

    def test_unbound_status_and_preview_stay_available_but_journal_writes_hold(self):
        for operation in ('guest_signing_prepare','guest_signing_confirm','negotiate'):
            self.assertEqual(self.bridge.handle(dict(protocol=1,request_id='x',operation=operation))['error'],'ai_disabled')
        request=self.proposal();request['operation']='preview'
        for key in ('personality','performance','relationships'):request.pop(key)
        self.assertEqual(self.bridge.handle(request)['result']['room_after'],75733000)
        status=self.bridge.handle(dict(protocol=1,request_id='status',operation='guest_signing_status'))
        self.assertEqual(status['error'],'state_rejected')  # Unconfigured journal, not an AI gate.
        self.assertEqual(self.calls,0)

    def test_image_match_cannot_claim_missing_or_other_database_namespace(self):
        from franchise.snapshot_origin import KEY
        import sqlite3
        changed=copy.deepcopy(self.bindings);changed['franchise_id']='d'*32
        bridge=Bridge(self.store,provider=self.provider,access_check=lambda:self.allowed,
            guest_snapshot=(changed,self.payload))
        self.assertEqual(bridge.handle(self.hello())['error'],'state_rejected')
        self.assertEqual(bridge.handle(self.proposal())['error'],'ai_disabled')
        with contextlib.closing(sqlite3.connect(self.store.path)) as db:
            db.execute('DELETE FROM franchise_metadata WHERE key=?',(KEY,));db.commit()
        self.assertEqual(self.bridge.handle(self.hello())['error'],'state_rejected')
        self.assertEqual(self.calls,0)

    def test_image_claim_without_explicit_expected_context_rejects(self):
        self.bindings['game_context'].pop('loaded_image_sha256')
        bridge=self.restart()
        self.assertEqual(bridge.handle(self.hello())['error'],'invalid_request')
        request=self.hello();request.pop('loaded_image_sha256')
        self.assertIsNone(bridge.handle(request)['error'])  # Existing engine-only fixture compatibility.

    def test_read_only_binding_does_not_touch_control_provider_or_grant_ai(self):
        self.bridge.access_check=Mock(side_effect=AssertionError('Read binding must not consult or renew AI control'))
        guard=Mock();self.bridge.connection_check=guard
        reply=self.bridge.handle({**self.hello(),'operation':'bind_runtime'})
        self.assertIsNone(reply['error'])
        self.assertIs(reply['result']['ai_enabled'],False)
        self.assertEqual(reply['result']['operations'],['signing_context'])
        self.assertEqual(reply['result']['runtime_binding']['franchise_id'],self.bindings['franchise_id'])
        self.assertEqual(guard.call_count,2)
        self.bridge.access_check.assert_not_called()
        self.assertFalse(self.bridge.runtime_verified)
        self.assertEqual(self.bridge.handle(self.proposal())['error'],'ai_disabled')
        self.assertEqual(self.calls,0)
        self.assertEqual(self.store.load_team('49ers').revision,0)

    def test_binding_attempt_revokes_old_ai_handshake_and_rejects_wrong_context(self):
        self.assertIsNone(self.bridge.handle(self.hello())['error'])
        request={**self.hello(),'operation':'bind_runtime','loaded_image_sha256':'b'*64}
        self.assertEqual(self.bridge.handle(request)['error'],'state_rejected')
        self.assertEqual(self.bridge.handle(self.proposal())['error'],'ai_disabled')
        request['loaded_image_sha256']='a'*64
        self.assertIsNone(self.bridge.handle(request)['error'])
        self.assertEqual(self.bridge.handle(self.proposal())['error'],'ai_disabled')
        self.assertEqual(self.calls,0)
        self.bindings['game_context'].pop('loaded_image_sha256')
        unbound=self.restart();request.pop('loaded_image_sha256')
        self.assertEqual(unbound.handle(request)['error'],'state_rejected')
