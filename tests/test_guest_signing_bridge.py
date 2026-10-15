"""Authored save/league/process fixtures. No retail assets or provider requests."""
import hashlib
import json
import os
from pathlib import Path
from queue import Queue
import subprocess
import struct
import sys
from threading import Event, Thread
import unittest
from unittest.mock import Mock, patch

from franchise import guest_signing
from franchise.bridge import Bridge, ResponseTooLarge
from franchise.control import AccessDisabled
from franchise.sidecar import read_guest_save, serve
from franchise.store import FranchiseStore
from tools.franchise_finance_state import saved_finance_state
from tools.franchise_identity_state import saved_identity_state
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE
import test_guest_signing_journal as journal_fixtures


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


class GuestSigningBridgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture=journal_fixtures.GuestSigningJournalTests();self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.current=self.fixture.before
        self.provider=Mock(side_effect=AssertionError('Journal coordination must not invoke a model'))
        self.access=Mock(return_value=None)
        self.bridge=self.make_bridge()

    def make_bridge(self,**changes):
        args=dict(provider=self.provider,access_check=self.access,
                  guest_snapshot=(self.fixture.bindings,self.current),guest_signing_reader=lambda:self.current)
        args.update(changes)
        return Bridge(FranchiseStore(self.fixture.path),**args)

    def prepare(self,**changes):
        return {**dict(protocol=1,request_id='journal',operation='guest_signing_prepare',timeout_ms=5000,
                    team_id='49ers',proposal_request_id='proposal',guest_offer=self.fixture.raw,
                    expected_revision=self.fixture.revision,expected_before_sha256=digest(self.fixture.before),
                    live_finance_sha256=digest(saved_finance_state(self.fixture.before)),
                    live_identity_sha256=digest(saved_identity_state(self.fixture.before))),**changes}

    def confirm(self):
        return dict(protocol=1,request_id='confirm',operation='guest_signing_confirm',timeout_ms=5000,
                    journal_request_id='journal',expected_after_sha256=digest(self.fixture.after))

    def status(self):
        return dict(protocol=1,request_id='status',operation='guest_signing_status',timeout_ms=5000,
                    journal_request_id='journal')

    def assert_unchanged(self,pending=True):
        reopened=FranchiseStore(self.fixture.path)
        self.assertEqual(reopened.load_team('49ers').financial_snapshot(),self.fixture.initial)
        self.assertEqual(len(reopened.negotiation_history('49ers',self.fixture.player)),1)
        if pending:
            self.assertEqual(guest_signing.inspect(reopened,'journal',self.current)['state'],'prepared')
        else:
            with self.assertRaises(ValueError): guest_signing.inspect(reopened,'journal',self.current)

    def test_explicit_configuration_and_handshake_capabilities(self):
        disabled=self.make_bridge(guest_signing_reader=None)
        self.assertEqual(disabled.handle(self.prepare())['error'],'state_rejected')
        hello=dict(protocol=1,request_id='hello',operation='hello')
        self.assertNotIn('guest_signing_prepare',disabled.handle(hello)['result']['operations'])
        self.assertIn('guest_signing_confirm',self.bridge.handle(hello)['result']['operations'])
        with self.assertRaises(ValueError): self.make_bridge(guest_snapshot=None)
        self.provider.assert_not_called();self.assert_unchanged(False)

    def test_bound_pending_free_agent_prepares_and_retries_without_financial_mutation(self):
        from tools.franchise_offer_state import saved_offer_screen_state
        finance, identity = saved_offer_screen_state(self.fixture.before, 1)
        request = self.prepare(live_finance_sha256=digest(finance), live_identity_sha256=digest(identity))
        result = self.bridge.handle(request)
        self.assertIsNone(result['error'], result)
        self.assertFalse(result['result']['write_authorized'])
        self.assertEqual(self.make_bridge().handle(request), result)
        self.assert_unchanged(); self.provider.assert_not_called()
        self.assertEqual(self.fixture.before, self.current)

    def test_pending_offer_requires_joint_hashes_and_preserves_every_other_field(self):
        from tools.franchise_offer_state import saved_offer_screen_state
        finance, identity = saved_offer_screen_state(self.fixture.before, 1)
        for financial, identities in ((finance, saved_identity_state(self.fixture.before)),
                                      (saved_finance_state(self.fixture.before), identity)):
            result = self.bridge.handle(self.prepare(live_finance_sha256=digest(financial),
                                                    live_identity_sha256=digest(identities)))
            self.assertEqual(result['error'], 'state_rejected'); self.assert_unchanged(False)
        for offset in (12, 48, 432 + 1 * 11 + 1, 432 + 2 * 11 + 3):
            changed = bytearray(finance); changed[offset] ^= 1
            result = self.bridge.handle(self.prepare(live_finance_sha256=digest(changed),
                                                    live_identity_sha256=digest(identity)))
            self.assertEqual(result['error'], 'state_rejected'); self.assert_unchanged(False)
        changed = bytearray(identity); changed[16] ^= 1
        result = self.bridge.handle(self.prepare(live_finance_sha256=digest(finance),
                                                live_identity_sha256=digest(changed)))
        self.assertEqual(result['error'], 'state_rejected'); self.assert_unchanged(False)
        self.provider.assert_not_called()

    def test_financial_mismatch_rejects_before_creating_a_journal(self):
        changed=bytearray(self.fixture.before)
        struct.pack_into('<H',changed,PLAYER_START+2*PLAYER_STRIDE+10,1)
        altered=digest(saved_finance_state(bytes(changed)))
        for fingerprint in ('0'*64, altered):
            request={**self.prepare(),'live_finance_sha256':fingerprint}
            with self.subTest(fingerprint=fingerprint):
                self.assertEqual(self.bridge.handle(request)['error'],'state_rejected')
                self.assert_unchanged(False)
        self.provider.assert_not_called()

    def test_financial_capture_is_required_and_canonical(self):
        missing=self.prepare();missing.pop('live_finance_sha256')
        self.assertEqual(self.bridge.handle(missing)['error'],'invalid_request')
        for value in (None, True, 0, '', 'a'*63, 'A'*64, 'g'*64):
            with self.subTest(value=value):
                self.assertEqual(self.bridge.handle({**self.prepare(),'live_finance_sha256':value})['error'],'invalid_request')
        self.assert_unchanged(False);self.provider.assert_not_called()

    def test_unselected_biography_changes_reject_with_identical_finances(self):
        changed=bytearray(self.fixture.before);changed[PLAYER_START+4]^=1
        self.assertEqual(saved_finance_state(bytes(changed)),saved_finance_state(self.fixture.before))
        request={**self.prepare(),'live_identity_sha256':digest(saved_identity_state(bytes(changed)))}
        self.assertEqual(self.bridge.handle(request)['error'],'state_rejected')
        self.assert_unchanged(False);self.provider.assert_not_called()

    def test_identity_capture_is_required_and_canonical_on_every_preparation(self):
        missing=self.prepare();missing.pop('live_identity_sha256')
        self.assertEqual(self.bridge.handle(missing)['error'],'invalid_request')
        for value in (None, True, 0, '', 'a'*63, 'A'*64, 'g'*64):
            with self.subTest(value=value):
                self.assertEqual(self.bridge.handle({**self.prepare(),'live_identity_sha256':value})['error'],'invalid_request')
        self.assert_unchanged(False)
        prepared=self.bridge.handle(self.prepare());self.assertIsNone(prepared['error'],prepared)
        self.assertEqual(self.bridge.handle({**self.prepare(),'live_identity_sha256':'f'*64})['error'],'state_rejected')
        self.assertEqual(self.bridge.handle(self.prepare()),prepared)
        self.assert_unchanged();self.provider.assert_not_called()

    def test_preparation_retry_checks_new_capture_without_changing_existing_journal(self):
        prepared=self.bridge.handle(self.prepare());self.assertIsNone(prepared['error'],prepared)
        self.assertEqual(self.bridge.handle({**self.prepare(),'live_finance_sha256':'f'*64})['error'],'state_rejected')
        self.assertEqual(self.bridge.handle(self.prepare()),prepared)
        self.assert_unchanged();self.provider.assert_not_called()

    def test_prepare_read_current_after_save_restart_and_settle_exactly_once(self):
        prepared=self.bridge.handle(self.prepare());self.assertIsNone(prepared['error'],prepared)
        self.assertFalse(prepared['result']['write_authorized']);self.assert_unchanged()
        self.current=self.fixture.after # The startup snapshot still contains the before-save.
        self.assertEqual(self.bridge.handle(self.status())['result']['save_position'],'candidate_after')
        receipt=self.bridge.handle(self.confirm());self.assertIsNone(receipt['error'],receipt)
        self.assertEqual(receipt['result']['charges'],[4766000,3523000])
        self.assertEqual(receipt['result']['financial_revision'],self.fixture.revision+1)
        self.assertFalse(receipt['result']['write_authorized'])
        self.assertEqual(self.make_bridge().handle(self.confirm()),receipt)
        status=self.make_bridge().handle(self.status())['result']
        self.assertEqual((status['state'],status['save_position']),('settled','confirmed_after'))
        self.assertEqual(status['after_payload_sha256'],digest(self.current))
        self.assertNotIn('before_payload',status);self.assertNotIn('after_payload',status)
        self.assertEqual(len(self.fixture.store.negotiation_history('49ers',self.fixture.player)),2)
        self.provider.assert_not_called();self.assertEqual(self.fixture.calls,1)

    def test_paths_payloads_raw_authority_and_extra_fields_cannot_be_supplied(self):
        for name in ('save','path','before_payload','bindings','write_authorized','offer','game_stopped','pending_free_agent_slot','live_projection'):
            with self.subTest(name=name):
                self.assertEqual(self.bridge.handle({**self.prepare(),name:True})['error'],'invalid_request')
        self.assertEqual(self.bridge.handle({**self.prepare(),'expected_before_sha256':'0'*64})['error'],'state_rejected')
        for value in (True,'x',None):
            self.assertEqual(self.bridge.handle({**self.prepare(),'expected_before_sha256':value})['error'],'invalid_request')
        self.assert_unchanged(False);self.provider.assert_not_called()

    def test_save_changes_after_preparation_insert_roll_back_reservation(self):
        reads=0
        def reader():
            nonlocal reads
            reads+=1
            return self.fixture.before if reads<3 else self.fixture.after
        self.bridge.guest_signing_reader=reader
        self.assertEqual(self.bridge.handle(self.prepare())['error'],'state_rejected')
        self.assertEqual(reads,3);self.assert_unchanged(False)

    def test_save_changes_after_financial_inserts_roll_back_confirmation(self):
        self.assertIsNone(self.bridge.handle(self.prepare())['error']);self.current=self.fixture.after
        reads=0
        def reader():
            nonlocal reads
            reads+=1
            return self.fixture.after if reads<4 else self.fixture.before
        self.bridge.guest_signing_reader=reader
        self.assertEqual(self.bridge.handle(self.confirm())['error'],'state_rejected')
        self.assertEqual(reads,4);self.assert_unchanged()

    def test_shutdown_after_prepare_or_financial_insert_is_atomic(self):
        self.access.side_effect=[None,AccessDisabled('After preparation insert')]
        self.assertEqual(self.bridge.handle(self.prepare())['error'],'ai_disabled');self.assert_unchanged(False)
        self.access.side_effect=None
        self.assertIsNone(self.bridge.handle(self.prepare())['error']);self.current=self.fixture.after
        self.access.side_effect=[None,None,AccessDisabled('After financial inserts')]
        self.assertEqual(self.bridge.handle(self.confirm())['error'],'ai_disabled');self.assert_unchanged()
        self.access.reset_mock(side_effect=True);self.access.side_effect=AccessDisabled('Disabled')
        self.assertEqual(self.bridge.handle(self.status())['result']['save_position'],'candidate_after')
        self.access.assert_not_called();self.provider.assert_not_called()

    def test_shutdown_after_receipt_validation_still_rolls_back(self):
        self.assertIsNone(self.bridge.handle(self.prepare())['error']);self.current=self.fixture.after
        self.access.reset_mock()
        self.access.side_effect=[None,None,None,AccessDisabled('Disabled after receipt validation')]
        self.assertEqual(self.bridge.handle(self.confirm())['error'],'ai_disabled')
        self.assertEqual(self.access.call_count,4);self.assert_unchanged()

    def test_deadline_after_financial_inserts_rolls_back_without_inference(self):
        self.assertIsNone(self.bridge.handle(self.prepare())['error']);self.current=self.fixture.after
        clock=[0];calls=0
        def access():
            nonlocal calls
            calls+=1
            if calls==3: clock[0]=100
        self.bridge.access_check=access
        with patch('franchise.bridge.time.monotonic',side_effect=lambda:clock[0]):
            self.assertEqual(self.bridge.handle(self.confirm())['error'],'timeout')
        self.assertEqual(calls,3);self.assert_unchanged();self.provider.assert_not_called()

    def test_unsendable_confirmation_rolls_back_journal_and_finances(self):
        self.assertIsNone(self.bridge.handle(self.prepare())['error']);self.current=self.fixture.after
        with patch.object(self.bridge,'_require_frame',side_effect=ResponseTooLarge('Authored frame refusal')):
            self.assertEqual(self.bridge.handle(self.confirm())['error'],'response_too_large')
        self.assert_unchanged()
        self.assertIsNone(self.bridge.handle(self.confirm())['error'])
        self.provider.assert_not_called()

    def test_unsendable_preparation_never_reserves_the_journal(self):
        self.assertEqual(self.bridge.handle({**self.prepare(),'request_id':'x'*65536})['error'],'response_too_large')
        self.assert_unchanged(False)

    def test_disconnect_or_explicit_false_control_denies_confirmation(self):
        self.assertIsNone(self.bridge.handle(self.prepare())['error']);self.current=self.fixture.after
        self.bridge.access_check=lambda:False
        self.assertEqual(self.bridge.handle(self.confirm())['error'],'ai_disabled');self.assert_unchanged()
        self.bridge=self.make_bridge(connection_check=Mock(side_effect=AccessDisabled('Disconnected')))
        self.assertEqual(self.bridge.handle(self.confirm())['error'],'ai_disabled');self.assert_unchanged()
        self.bridge=self.make_bridge(connection_check=lambda:False)
        self.assertEqual(self.bridge.handle(self.confirm())['error'],'ai_disabled');self.assert_unchanged()

    def test_missing_or_changed_after_save_cannot_confirm(self):
        self.assertIsNone(self.bridge.handle(self.prepare())['error'])
        self.assertEqual(self.bridge.handle(self.confirm())['error'],'state_rejected');self.assert_unchanged()
        self.current=bytes(len(self.fixture.after))
        reply=self.bridge.handle({**self.confirm(),'expected_after_sha256':digest(self.current)})
        self.assertEqual(reply['error'],'invalid_request');self.assert_unchanged()
        self.assertEqual(self.bridge.handle(self.status())['result']['save_position'],'unrecognized')

    def test_transport_detects_eof_after_preparation_insert_and_refuses_busy_requests(self):
        self.check_transport_disconnect(confirm=False)

    def test_transport_detects_eof_after_financial_inserts_and_rolls_back(self):
        self.check_transport_disconnect(confirm=True)

    def check_transport_disconnect(self,*,confirm):
        if confirm:
            self.assertIsNone(self.bridge.handle(self.prepare())['error']);self.current=self.fixture.after
        entered,release,closed=Event(),Event(),Event()
        incoming,outgoing=Queue(),Queue()
        class Reader:
            def readline(self,limit):
                line=incoming.get(timeout=5)
                if not line: closed.set()
                return line
        class Writer:
            def write(self,line): outgoing.put(json.loads(line))
            def flush(self): pass
        calls=0
        def access():
            nonlocal calls
            calls+=1
            if calls==(3 if confirm else 2):
                entered.set();release.wait(timeout=5)
        self.bridge.access_check=access
        worker=Thread(target=serve,args=(self.bridge,Reader(),Writer()))
        worker.start()
        try:
            incoming.put(json.dumps(self.confirm() if confirm else self.prepare())+'\n')
            self.assertTrue(entered.wait(timeout=5))
            incoming.put(json.dumps({**self.prepare(),'request_id':'competing'})+'\n')
            self.assertEqual(outgoing.get(timeout=5)['error'],'busy')
            incoming.put('');self.assertTrue(closed.wait(timeout=5))
        finally:
            release.set();worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assert_unchanged(pending=confirm);self.provider.assert_not_called()

    def process_request(self,command,request,env=None):
        if env is None: env=dict(os.environ,NFL2K5_FRANCHISE_GUEST_SIGNING='0')
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
        try:
            process.stdin.write(json.dumps(request)+'\n');process.stdin.flush()
            replies=Queue()
            Thread(target=lambda:replies.put(process.stdout.readline()),daemon=True).start()
            line=replies.get(timeout=10)
            if not line:
                process.wait(timeout=5)
                self.fail('Child exited without a reply (exit '+str(process.returncode)+'): '+process.stderr.read())
            return json.loads(line)
        finally:
            process.stdin.close()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill();process.wait(timeout=5)
            process.stdout.close();process.stderr.close()

    def test_actual_sidecar_process_pinned_file_prepare_restart_confirm_and_disabled_status(self):
        save=self.fixture.path.with_suffix('.dat');save.write_bytes(self.fixture.before)
        bindings=self.fixture.path.with_suffix('.json');bindings.write_text(json.dumps(self.fixture.bindings))
        command=[sys.executable,'-m','franchise.sidecar','--database',str(self.fixture.path),
                 '--provider','offline-fixture','--guest-save',str(save),'--guest-bindings',str(bindings)]
        self.assertEqual(self.process_request(command,self.prepare())['error'],'state_rejected')
        enabled=dict(os.environ,NFL2K5_FRANCHISE_GUEST_SIGNING='1')
        reply=self.process_request(command,self.prepare(),enabled);self.assertIsNone(reply['error'],reply)
        for value in ('yes','','2'):
            result=subprocess.run(command,input='',text=True,capture_output=True,
                env=dict(enabled,NFL2K5_FRANCHISE_GUEST_SIGNING=value),timeout=10)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('must be 0 or 1',result.stderr)
        command+=['--guest-signing']
        reply=self.process_request(command,self.prepare());self.assertIsNone(reply['error'],reply)
        save.write_bytes(self.fixture.after)
        reply=self.process_request(command,self.confirm());self.assertIsNone(reply['error'],reply)
        command[command.index('offline-fixture')]='vertex'
        environment=dict(os.environ,GOOGLE_APPLICATION_CREDENTIALS=str(save.parent/'missing-adc.json'))
        reply=self.process_request(command,self.status(),environment)
        self.assertIsNone(reply['error'],reply)
        self.assertEqual(reply['result']['save_position'],'confirmed_after')
        self.assertEqual(self.fixture.store.load_team('49ers').revision,self.fixture.revision+1)
        self.assertEqual(read_guest_save(save),self.fixture.after)
        save.write_bytes(self.fixture.after+b'x')
        with self.assertRaises(ValueError): read_guest_save(save)
        with self.assertRaises(ValueError): read_guest_save(save.parent)
        self.provider.assert_not_called();self.assertEqual(self.fixture.calls,1)
