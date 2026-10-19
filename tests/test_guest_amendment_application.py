"""Authored native-clock, durable amendment and one-use authorization fixtures."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger, Rejected
from franchise import guest_signing,guest_application
from franchise.salary_clock import bind_salary_clock
from franchise.store import FranchiseStore
from tools.export_legacy_contracts import legacy_contracts
from tools.franchise_snapshot_bindings import create_bindings,resolve_bindings
from tools.inspect_franchise_calendar import inspect_calendar
from tools.inspect_franchise_save import TEAMS
from tools.franchise_finance_state import saved_finance_state
from tools.franchise_identity_state import saved_identity_state
from tools.franchise_offer_state import expected_amended_state
from tests import test_confirm_saved_amendment as saved_fixture

class GuestAmendmentApplicationTests(unittest.TestCase):
    def setUp(self):
        sample=saved_fixture.SavedAmendmentConfirmationTests();sample.setUp()
        raw=bytearray(sample.before);calendar=inspect_calendar(bytes(raw));start=calendar['scheduler_offset']
        raw[start+1]=7;raw[start+4]=4;raw[start+5]=0
        struct.pack_into('<I',raw,start+0xac,getattr(self,'opening_team_flag',0))
        if getattr(self,'two_players',False):
            from tools.inspect_franchise_save import PLAYER_START,PLAYER_STRIDE
            raw[0x45c4]=2
            struct.pack_into('<i',raw,0x44ac,PLAYER_START+PLAYER_STRIDE-0x44ac+1)
            struct.pack_into('<H',raw,0x358,0)
            struct.pack_into('<H',raw,PLAYER_START+PLAYER_STRIDE+10,829)
            struct.pack_into('<I',raw,PLAYER_START+PLAYER_STRIDE+36,0x02410ba2)
            struct.pack_into('<I',raw,0x44a8+0x124,9532)
        self.before=bytes(raw);self.bindings=create_bindings(self.before,seed='authored application')
        self.player=self.bindings['players'][0]['player_id'];self.offer_raw=sample.raw
        self.clock=dict(source_epoch=3,descriptor_hex='00'*16)
        self.descriptors=patch.dict('franchise.salary_clock.DESCRIPTORS',{7:(hashlib.sha256(bytes(16)).hexdigest(),4)})
        self.descriptors.start();self.addCleanup(self.descriptors.stop)
        cal=inspect_calendar(self.before)
        self.observation=dict(biography=dict(source_slot=0,first_name='Synthetic',last_name='Starter',
            pbp_photo_raw='00000000',dob_region_raw='000000'),team=dict(table_index=0,table_mode=2,payroll_raw=struct.unpack_from('<I',self.before,0x44a8+0x124)[0],
            league_cap_raw=80500,team_flag_raw=getattr(self,'opening_team_flag',0),first_year_accumulator_raw=0),calendar={k:cal[k] for k in
            ('season_index','display_year','phase_01_raw','phase_02_raw','step_04_raw','step_05_raw','counter_08_raw')})
        self.scope=bind_salary_clock(self.bindings,self.before,self.observation,self.clock)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=FranchiseStore(Path(self.temp.name)/'db.sqlite')
        all_players=frozenset(p['player_id'] for p in resolve_bindings(self.bindings,self.before).values())
        records=legacy_contracts(self.bindings,self.before)
        self.store.create_franchise({team:Ledger.from_opening(OpeningBooks(legacy_contracts=records[team],
            retained=getattr(self,"opening_retained",()) if team=="49ers" else (),
            adjustments=getattr(self,"opening_adjustments",()) if team=="49ers" else ()),
            cap=80500000,roster_reserve=0,max_bonus_years=5,veteran_minimums={p:(1000000,)*7 for p in (all_players if getattr(self,'two_players',False) else (self.player,))},
            observed_player_ids=all_players,observed_player_source='authored') for team in TEAMS},seed=self.bindings['personality_seed'])
        for team in TEAMS:self.store.initialize_cash(team,(),source='authored legacy payment unknown',unknown_legacy_players=tuple(c.player_id for c in records[team]))
        self.revision=self.store.load_team('49ers').revision
        self.current=self.before
        self.bridge=Bridge(self.store,provider=lambda _:json.dumps(dict(action='accept',reason='Agreed.',salaries=None,signing_bonus=None)),
            access_check=lambda:True,guest_snapshot=(self.bindings,self.before),guest_signing_reader=lambda:self.current)
        # Use actual persisted actor evidence, rather than arbitrary test traits.
        context=self.store.player_context('49ers',self.player)
        from franchise.guest_contracts import GuestContractTerms
        self.offer=GuestContractTerms.from_context(**self.offer_raw).to_offer(self.player)
        reply=self.bridge.handle(dict(protocol=1,request_id='proposal',operation='negotiate_proposal',team_id='49ers',
            offer=self.offer.to_dict(),expected_revision=self.revision,timeout_ms=5000,
            personality=context['personality'],relationships=context['relationships'],performance={},
            contract_format='original_fxg_v1',amendment_rule='legacy_bonus_carry_v1',amendment_scope=self.scope.to_dict()))
        self.assertIsNone(reply['error'],reply)
        self.assertEqual(reply['result']['outcome'],'accepted_amendment_proposal')
        self.reply=reply

    def projection(self):
        finance=saved_finance_state(self.current) if self.current==self.before else guest_application.saved_amendment_projection(
            self.intent(),self.before,self.current)[0]
        return dict(finance=hashlib.sha256(finance).hexdigest(),
                    identity=hashlib.sha256(saved_identity_state(self.current)).hexdigest())

    def intent(self):
        with self.store._connection() as db:return guest_application.read_amendment(self.store,db,'journal')[0]

    def prepare(self,**changes):
        args=dict(bindings=self.bindings,before_payload=self.before,guest_offer=self.offer_raw,
            expected_before_sha256=hashlib.sha256(self.before).hexdigest(),expected_revision=self.revision,
            access_check=lambda:True,live_projection=self.projection(),observation=self.observation,salary_clock=self.clock)
        args.update(changes)
        return guest_application.prepare_amendment(self.store,'49ers','proposal','journal',**args)

    def test_clock_preserves_scope_and_rejects_changed_descriptor_epoch_and_calendar(self):
        self.assertEqual(self.scope.elapsed_periods,0);self.assertEqual(self.scope.total_periods,18)
        for clock in ({**self.clock,'source_epoch':0},{**self.clock,'source_epoch':True},
                      {**self.clock,'descriptor_hex':'ff'*16},{**self.clock,'extra':1}):
            with self.subTest(clock=clock),self.assertRaises(ValueError):bind_salary_clock(self.bindings,self.before,self.observation,clock)
        observation=json.loads(json.dumps(self.observation));observation['calendar']['step_05_raw']=1
        with self.assertRaises(ValueError):bind_salary_clock(self.bindings,self.before,observation,self.clock)

    def test_live_hash_and_scope_mismatch_never_prepare(self):
        with self.assertRaises(Rejected):self.prepare(live_projection={'finance':'0'*64,'identity':'1'*64})
        with self.assertRaises(Rejected):self.prepare(salary_clock={**self.clock,'source_epoch':4})
        with self.store._connection() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM guest_signings').fetchone()[0],0)

    def test_one_issuance_keeps_books_frozen_until_exact_saved_settlement(self):
        self.assertFalse(self.prepare()['write_authorized']);self.prepare()
        initial=self.store.load_team('49ers').financial_snapshot()
        with self.assertRaises(Rejected):self.store.initialize_cash('Bears',(),source='competing write')
        reply=guest_application.authorize(self.store,'issue','journal',self.before,access_check=lambda:True,live_projection=self.projection())
        plan=reply['application_plan'];self.assertEqual(plan['source_epoch'],3)
        self.assertEqual(plan['enforced_payroll_raw'],3658)
        self.assertEqual(plan['native_payroll_raw'],2000)
        with self.assertRaises(Rejected):guest_application.authorize(self.store,'retry','journal',self.before,access_check=lambda:True,live_projection=self.projection())
        self.assertEqual(initial,self.store.load_team('49ers').financial_snapshot())
        after=bytearray(self.before)
        from tools.inspect_franchise_save import PLAYER_START
        after[PLAYER_START+8]&=0xf7;struct.pack_into('<H',after,PLAYER_START+10,600)
        packed=struct.unpack_from('<I',after,PLAYER_START+36)[0]
        struct.pack_into('<I',after,PLAYER_START+36,(packed&~0x0ff7000f)|(3<<24)|(2<<16)|3)
        struct.pack_into('<I',after,0x44a8+0x124,3658)
        self.current=bytes(after)
        status=guest_signing.inspect(self.store,'journal',self.current,live_projection=self.projection())
        self.assertEqual(status['save_position'],'candidate_after');self.assertTrue(status['live_application_matches'])
        receipt=guest_signing.settle(self.store,'journal',self.current,access_check=lambda:True)
        self.assertEqual(receipt.charges,(3658000,3658000,2000000))
        reopened=FranchiseStore(self.store.path)
        self.assertEqual(guest_signing.inspect(reopened,'journal',self.current)['save_position'],'confirmed_after')
        self.assertEqual(guest_signing.settle(reopened,'journal',self.current,access_check=lambda:True).charges,receipt.charges)
        self.assertEqual(reopened.load_team('49ers').revision,self.revision+1)
        target=guest_application.amendment_target(self.intent(),self.before)[0]
        payrolls=[struct.unpack_from('<I',target,48+12*i)[0] for i in range(32)]
        live=bytearray(target);struct.pack_into('<I',live,48,0x7fffffff);payrolls[0]=0x7fffffff
        restored=guest_application.restore_cap(reopened,'reload',self.current,source_epoch=8,
            loaded_payload_sha256=hashlib.sha256(self.current).hexdigest(),finance_payrolls=payrolls,
            live_projection=dict(finance=hashlib.sha256(live).hexdigest(),identity=self.projection()['identity']),
            connection_check=lambda:True)
        self.assertEqual(restored['cap_plan']['source_epoch'],8)
        self.assertEqual(restored['cap_plan']['enforced_payroll_raw'],3658)
        self.assertNotIn('application_plan',restored)
        with self.assertRaises(Rejected):guest_application.restore_cap(reopened,'rollback',self.before,source_epoch=9,
            loaded_payload_sha256=hashlib.sha256(self.before).hexdigest(),finance_payrolls=payrolls,
            live_projection=self.projection(),connection_check=lambda:True)


    def test_actual_bridge_preparation_and_authorization_do_not_call_provider(self):
        from unittest.mock import Mock
        from franchise.control import AccessDisabled
        self.bridge.provider=Mock(side_effect=AssertionError('No inference during commit coordination'))
        projection=self.projection()
        request=dict(protocol=1,request_id='journal',operation='guest_signing_prepare',timeout_ms=5000,
            team_id='49ers',proposal_request_id='proposal',guest_offer=self.offer_raw,
            expected_revision=self.revision,expected_before_sha256=hashlib.sha256(self.before).hexdigest(),
            live_finance_sha256=projection['finance'],live_identity_sha256=projection['identity'],
            observation=self.observation,salary_clock=self.clock)
        reply=self.bridge.handle(request);self.assertIsNone(reply['error'],reply)
        issue=dict(protocol=1,request_id='issue',operation='guest_signing_authorize',timeout_ms=5000,
            journal_request_id='journal',live_finance_sha256=projection['finance'],live_identity_sha256=projection['identity'])
        self.bridge.access_check=lambda:False
        self.assertEqual(self.bridge.handle(issue)['error'],'ai_disabled')
        self.bridge.access_check=lambda:True
        reply=self.bridge.handle(issue);self.assertIsNone(reply['error'],reply)
        self.assertEqual(reply['result']['application_plan']['enforced_payroll_raw'],3658)
        self.assertEqual(self.bridge.handle(issue)['error'],'state_rejected')
        self.bridge.provider.assert_not_called()

    def test_disabled_control_and_wrong_live_state_do_not_burn_or_issue_permit(self):
        self.prepare()
        for check,projection in ((lambda:False,self.projection()),(lambda:True,{'finance':'0'*64,'identity':'0'*64})):
            with self.assertRaises(Rejected):guest_application.authorize(self.store,'issue','journal',self.before,access_check=check,live_projection=projection)
        self.assertIn('application_plan',guest_application.authorize(self.store,'issue','journal',self.before,access_check=lambda:True,live_projection=self.projection()))
