"""Authored full-league FA signing including enforced opening liabilities."""
from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch
from hashlib import sha256
import json
from pathlib import Path
import struct
import unittest

from franchise import guest_signing,guest_application,opening_native
from franchise.books import OpeningBooks,ChargeRecord
from franchise.bridge import Bridge
from franchise.cap import Ledger,Rejected
from franchise.store import FranchiseStore
from franchise.saved_checkpoint import projection,verify
from tools.franchise_offer_state import saved_offer_screen_state
from tools.inspect_franchise_save import TEAMS
from tools.reconcile_signing_context import reconcile_signing_context
from tests import test_retained_guest_cap as fixtures
from tests import test_confirm_saved_signing as saved_fixtures


class NativeFreeAgentTests(unittest.TestCase):
    def sample(self,pending=False,scale=1):
        helper=fixtures.RetainedGuestCapTests();self.addCleanup(helper.doCleanups)
        s=helper.sample();s.player=s.bindings['players'][1]['player_id']
        s.bindings=deepcopy(s.bindings);s.bindings['game_context']['money_scale']=scale
        ledgers={}
        for team in TEAMS:
            old=s.store.load_team(team)
            books=replace(old._opening_books,legacy_contracts=tuple(replace(c,game_dollar_scale=scale) for c in old._opening_books.legacy_contracts))
            ledgers[team]=Ledger.from_opening(books,cap=old.cap*scale,roster_reserve=0,
                max_bonus_years=5,veteran_minimums={p['player_id']:(1000000,)*5 for p in s.bindings['players']})
        s.store=FranchiseStore(Path(s.store.path).with_name('fa.sqlite'))
        s.store.create_franchise(ledgers,seed=s.bindings['personality_seed'])
        for team in TEAMS:s.store.initialize_cash(team,(),source='authored legacy unknown',unknown_legacy_players=tuple(ledgers[team]._legacy_contracts))
        s.before,proof=opening_native.build(s.store,s.bindings,s.before,source={'fixture':'authored all-team obligations'})
        opening_native.register(s.store,proof,s.before)
        sf=saved_fixtures.SavedSigningConfirmationTests();sf.setUp()
        from franchise.guest_contracts import GuestContractTerms
        s.format='softdrink_fxg_v1' if scale==4 else 'original_fxg_v1'
        s.offer=GuestContractTerms.from_context(**sf.raw).to_offer(s.player,contract_format=s.format)
        s.raw=sf.raw;s.sf=sf
        s.observation=deepcopy(s.observation)
        s.observation['biography'].update(source_slot=1,first_name='Authored',last_name='Freeagent')
        s.observation['team']['payroll_raw']=struct.unpack_from('<I',s.before,0x44a8+0x124)[0]
        s.live=self.live(s.before,pending)
        context=s.store.player_context('49ers',s.player)
        reply=Bridge(s.store,provider=lambda _:json.dumps(dict(action='accept',reason='Agreed.',salaries=None,signing_bonus=None)),access_check=lambda:True).handle(dict(
            protocol=1,request_id='fa-proposal',operation='negotiate_proposal',team_id='49ers',offer=s.offer.to_dict(),
            contract_format=s.format,expected_revision=s.store.load_team('49ers').revision,timeout_ms=5000,
            personality=context['personality'],relationships=context['relationships'],performance={}))
        self.assertIsNone(reply['error'],reply)
        return s

    def live(self,payload,pending=False):
        native,finance,identity=projection(payload)
        if pending:
            raw,identity=saved_offer_screen_state(native,1);raw=bytearray(raw)
            for i in range(32):raw[48+12*i:52+12*i]=finance[48+12*i:52+12*i]
            finance=bytes(raw)
        return dict(finance=sha256(finance).hexdigest(),identity=sha256(identity).hexdigest())

    def prepare(self,s):
        return guest_signing.prepare(s.store,'49ers','fa-proposal','fa-journal',bindings=s.bindings,
            before_payload=s.before,guest_offer=s.raw,expected_before_sha256=sha256(s.before).hexdigest(),
            expected_revision=s.store.load_team('49ers').revision,access_check=lambda:True,
            live_projection=s.live,observation=s.observation,salary_clock=s.clock)

    def test_consent_native_issuance_cap_settlement_restart_and_checkpoint(self):
        for pending in (False,True):
            with self.subTest(pending=pending):
                s=self.sample(pending);self.prepare(s);self.prepare(s)
                plan=guest_application.authorize(s.store,'issue','fa-journal',s.before,
                    access_check=lambda:True,live_projection=s.live)['application_plan']
                self.assertEqual(plan['enforced_payroll_raw'],14532)
                self.assertEqual(plan['native_payroll_raw'],9532)
                with self.assertRaises(Rejected):guest_application.authorize(s.store,'again','fa-journal',s.before,access_check=lambda:True,live_projection=s.live)
                after=bytearray(s.sf.signed(s.before));struct.pack_into('<I',after,0x44a8+0x124,plan['enforced_payroll_raw']);after=bytes(after)
                self.assertTrue(guest_signing.inspect(s.store,'fa-journal',after,live_projection=self.live(after))['live_application_matches'])
                finance=projection(after)[1]
                recovery=guest_application.restore_cap(s.store,'pending-reload',after,source_epoch=4,
                    loaded_payload_sha256=sha256(after).hexdigest(),live_projection=self.live(after),
                    finance_payrolls=[struct.unpack_from('<I',finance,48+12*i)[0] for i in range(32)],connection_check=lambda:True)
                self.assertEqual(recovery['cap_plan']['enforced_payroll_raw'],14532)
                self.assertEqual(s.store.load_team('49ers').charges[0],9766000)
                self.assertFalse(guest_signing.inspect(s.store,'fa-journal',after)['write_authorized'])
                receipt=guest_signing.settle(s.store,'fa-journal',after,access_check=lambda:True)
                reopened=FranchiseStore(s.store.path)
                self.assertEqual(reopened.load_team('49ers').charges[0],14532000)
                self.assertEqual(guest_signing.settle(reopened,'fa-journal',after,access_check=lambda:True),receipt)
                with reopened._connection() as db:
                    self.assertTrue(verify(reopened,db,after))
                    with self.assertRaises(Rejected):verify(reopened,db,s.before)
                finance,identity=projection(after)[1:]
                restored=guest_application.restore_cap(reopened,'reload',after,source_epoch=4,
                    loaded_payload_sha256=sha256(after).hexdigest(),live_projection=self.live(after),
                    finance_payrolls=[struct.unpack_from('<I',finance,48+12*i)[0] for i in range(32)],connection_check=lambda:True)
                self.assertEqual(restored['cap_plan']['enforced_payroll_raw'],14532)
                self.assertEqual(len(restored['additional_cap_plans']),31)
                # Read-only next negotiation can see the new modern contract inventory.
                obs=deepcopy(s.observation);obs['biography'].update(source_slot=0,first_name='Synthetic',last_name='Starter')
                obs['team']['payroll_raw']=14532
                reconcile_signing_context(s.bindings,after,obs,reopened,expected_revision=reopened.load_team('49ers').revision)

    def test_owned_negotiation_after_free_agent_signing_keeps_both_contracts_accounted(self):
        s=self.sample();self.prepare(s)
        plan=guest_application.authorize(s.store,'first-issue','fa-journal',s.before,access_check=lambda:True,live_projection=s.live)['application_plan']
        after=bytearray(s.sf.signed(s.before));struct.pack_into('<I',after,0x44a8+0x124,plan['enforced_payroll_raw']);after=bytes(after)
        guest_signing.settle(s.store,'fa-journal',after,access_check=lambda:True)
        from franchise.salary_clock import bind_salary_clock
        from franchise.guest_contracts import GuestContractTerms
        from tests.test_follow_on_guest_amendment import FollowOnAmendmentTests
        obs=deepcopy(s.observation);obs['biography'].update(source_slot=0,first_name='Synthetic',last_name='Starter');obs['team']['payroll_raw']=14532
        scope=bind_salary_clock(s.bindings,after,obs,s.clock);player=s.bindings['players'][0]['player_id']
        offer=GuestContractTerms.from_context(**s.offer_raw).to_offer(player);actor=s.store.player_context('49ers',player)
        reply=Bridge(s.store,provider=lambda _:json.dumps(dict(action='accept',reason='Agreed.',salaries=None,signing_bonus=None)),access_check=lambda:True).handle(dict(
            protocol=1,request_id='owned-proposal',operation='negotiate_proposal',team_id='49ers',offer=offer.to_dict(),
            contract_format='original_fxg_v1',expected_revision=s.store.load_team('49ers').revision,timeout_ms=5000,
            personality=actor['personality'],relationships=actor['relationships'],performance={},
            amendment_rule='legacy_bonus_carry_v1',amendment_scope=scope.to_dict()))
        self.assertIsNone(reply['error'],reply)
        guest_signing.prepare(s.store,'49ers','owned-proposal','owned-journal',bindings=s.bindings,before_payload=after,
            guest_offer=s.offer_raw,expected_before_sha256=sha256(after).hexdigest(),expected_revision=s.store.load_team('49ers').revision,
            access_check=lambda:True,live_projection=self.live(after),observation=obs,salary_clock=s.clock)
        plan=guest_application.authorize(s.store,'owned-issue','owned-journal',after,access_check=lambda:True,live_projection=self.live(after))['application_plan']
        self.assertEqual(plan['enforced_payroll_raw'],13424)
        saved=FollowOnAmendmentTests().apply(after,s.offer_raw,plan)
        finance=projection(saved)[1]
        recovery=guest_application.restore_cap(s.store,'pending-owned',saved,source_epoch=4,
            loaded_payload_sha256=sha256(saved).hexdigest(),live_projection=self.live(saved),
            finance_payrolls=[struct.unpack_from('<I',finance,48+12*i)[0] for i in range(32)],connection_check=lambda:True)
        self.assertEqual(recovery['cap_plan']['enforced_payroll_raw'],13424)
        guest_signing.settle(s.store,'owned-journal',saved,access_check=lambda:True)
        with s.store._connection() as db:self.assertTrue(verify(s.store,db,saved))

    def test_dropping_liabilities_shutdown_or_changed_owner_does_not_settle(self):
        s=self.sample();self.prepare(s)
        initial=s.store.load_team('49ers').financial_snapshot()
        wrong=bytearray(s.sf.signed(s.before));struct.pack_into('<I',wrong,0x44a8+0x124,9532);wrong=bytes(wrong)
        with self.assertRaises(ValueError):guest_signing.settle(s.store,'fa-journal',wrong,access_check=lambda:True)
        with self.assertRaises(Rejected):guest_application.authorize(s.store,'denied','fa-journal',s.before,access_check=lambda:False,live_projection=s.live)
        self.assertEqual(initial,s.store.load_team('49ers').financial_snapshot())

    def test_bridge_dispatches_captured_free_agent_clock_without_another_inference(self):
        s=self.sample(pending=True)
        def no_inference(_):self.fail('Journal operations cannot call the model')
        bridge=Bridge(s.store,provider=no_inference,access_check=lambda:True,
            guest_snapshot=(s.bindings,s.before),guest_signing_reader=lambda:s.before)
        request=dict(protocol=1,request_id='fa-journal',operation='guest_signing_prepare',timeout_ms=5000,
            team_id='49ers',proposal_request_id='fa-proposal',guest_offer=s.raw,
            expected_before_sha256=sha256(s.before).hexdigest(),expected_revision=s.store.load_team('49ers').revision,
            live_finance_sha256=s.live['finance'],live_identity_sha256=s.live['identity'],
            salary_clock=s.clock,observation=s.observation)
        reply=bridge.handle(request);self.assertIsNone(reply['error'],reply)
        reply=bridge.handle(dict(protocol=1,request_id='issue',operation='guest_signing_authorize',timeout_ms=5000,
            journal_request_id='fa-journal',live_finance_sha256=s.live['finance'],live_identity_sha256=s.live['identity']))
        self.assertIsNone(reply['error'],reply)
        self.assertEqual(reply['result']['application_plan']['enforced_payroll_raw'],14532)

    def test_scaled_native_units_preserve_exact_modern_dollars_and_retained_charge(self):
        s=self.sample(pending=True,scale=4);self.prepare(s)
        plan=guest_application.authorize(s.store,'issue','fa-journal',s.before,access_check=lambda:True,live_projection=s.live)['application_plan']
        self.assertEqual(plan['enforced_payroll_raw'],10782)
        after=bytearray(s.sf.signed(s.before));struct.pack_into('<I',after,0x44a8+0x124,10782)
        receipt=guest_signing.settle(s.store,'fa-journal',bytes(after),access_check=lambda:True)
        self.assertEqual(receipt.charges[0],19064000)
        self.assertEqual(s.store.load_team('49ers').charges[0],43128000)

    def test_in_season_offer_is_held_before_inference_until_proration_is_supported(self):
        s=self.sample();raw=bytearray(s.before)
        from tools.inspect_franchise_calendar import inspect_calendar
        offset=inspect_calendar(s.before)['scheduler_offset']
        raw[offset+1]=8;raw[offset+4]=18;raw[offset+5]=3;payload=bytes(raw)
        observation=deepcopy(s.observation);calendar=inspect_calendar(payload)
        observation['calendar']={k:calendar[k] for k in observation['calendar']}
        def no_inference(_):self.fail('Unsupported salary period cannot spend an inference request')
        bridge=Bridge(s.store,provider=no_inference,access_check=lambda:True,
            guest_snapshot=(s.bindings,s.before),guest_signing_reader=lambda:payload)
        with patch.dict('franchise.salary_clock.DESCRIPTORS',{8:(sha256(bytes(16)).hexdigest(),18)}):
            reply=bridge.handle(dict(protocol=1,request_id='in-season',operation='negotiate_proposal',
                observation=observation,salary_clock=s.clock,guest_offer=s.raw,
                expected_revision=s.store.load_team('49ers').revision,timeout_ms=5000))
        self.assertEqual(reply['error'],'state_rejected',reply)
        self.assertIn('proration',reply['detail'])
