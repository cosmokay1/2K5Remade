"""Sequential saved negotiations preserve old bonuses and enforced payroll."""
import hashlib
import json
import struct
import unittest
from franchise import guest_application,guest_signing
from franchise.bridge import Bridge
from franchise.cap import Rejected
from franchise.saved_checkpoint import projection,verify
from franchise.store import FranchiseStore
from franchise.guest_contracts import GuestContractTerms
from tools.inspect_franchise_save import PLAYER_START,PLAYER_STRIDE
from tools.reconcile_signing_context import reconcile_signing_context
from tests import test_retained_guest_cap as fixtures


class FollowOnAmendmentTests(unittest.TestCase):
    def setUp(self):
        helper=fixtures.RetainedGuestCapTests();self.addCleanup(helper.doCleanups)
        self.s=helper.sample(team_flag=getattr(self,"team_flag",0))
        self.native_cases=[]

    def apply(self,before,raw,plan):
        start=PLAYER_START+plan['source_slot']*PLAYER_STRIDE
        payload=bytearray(before);t=GuestContractTerms.from_context(**raw)
        payload[start+8]&=0xf7
        struct.pack_into('<H',payload,start+10,t.amount_word)
        flags=struct.unpack_from('<I',payload,start+36)[0]
        struct.pack_into('<I',payload,start+36,(flags&~0x0ff7000f)|(t.years<<24)|(t.shape_code<<16)|(t.bonus_code<<20)|t.years)
        # Apply every bounded native finance byte, including accumulation.
        # Payroll is saved separately at its mapped cached word.
        prior=projection(before)[1];target=bytearray(prior)
        for i,value in plan['finance_changes']:target[i]=value
        struct.pack_into('<H',payload,0x44a8+0x19c,struct.unpack_from('<I',target,56)[0])
        struct.pack_into('<I',payload,0x44a8+0x124,plan['enforced_payroll_raw'])
        return bytes(payload)

    def first(self):
        s=self.s;s.prepare()
        plan=guest_application.authorize(s.store,'issue','journal',s.before,
            access_check=lambda:True,live_projection=s.projection())['application_plan']
        after=self.apply(s.before,s.offer_raw,plan)
        guest_signing.settle(s.store,'journal',after,access_check=lambda:True)
        return after

    def test_two_saved_agreements_reopen_negotiate_sign_and_restore_latest(self):
        s=self.s;after=self.first();store=FranchiseStore(s.store.path)
        observation=json.loads(json.dumps(s.observation));observation['team']['payroll_raw']=struct.unpack_from('<I',projection(after)[1],48)[0]
        observation['team']['first_year_accumulator_raw']=struct.unpack_from('<I',projection(after)[1],56)[0]
        rev=store.load_team('49ers').revision
        raw={'amount_word':900,'flags_word':(2<<29)|(3<<16)|3}
        current=[after]
        bridge=Bridge(store,provider=lambda _:json.dumps(dict(action='accept',reason='Agreed.',salaries=None,signing_bonus=None)),
            access_check=lambda:True,guest_snapshot=(s.bindings,s.before),guest_signing_reader=lambda:current[0])
        request=dict(protocol=1,operation='signing_context',request_id='context2',timeout_ms=5000,
            observation=observation,expected_revision=rev,guest_offer=raw,salary_clock=s.clock)
        context=bridge.handle(request)
        self.native_cases.append(dict(request=request,response=context,valid=True))
        self.assertIsNone(context['error'],context)
        self.assertEqual(context['result']['saved_payload_sha256'],hashlib.sha256(after).hexdigest())
        request=dict(protocol=1,operation='negotiate_proposal',request_id='proposal2',timeout_ms=5000,
            observation=observation,expected_revision=rev,guest_offer=raw,salary_clock=s.clock,amendment_rule='legacy_bonus_carry_v1')
        proposal=bridge.handle(request)
        self.native_cases.append(dict(request=request,response=proposal,valid=True,journal_preparation=True))
        self.assertIsNone(proposal['error'],proposal)
        live=dict(finance=hashlib.sha256(projection(after)[1]).hexdigest(),identity=hashlib.sha256(projection(after)[2]).hexdigest())
        guest_application.prepare_amendment(store,'49ers','proposal2','journal2',bindings=s.bindings,
            before_payload=after,guest_offer=raw,expected_before_sha256=hashlib.sha256(after).hexdigest(),
            expected_revision=rev,access_check=lambda:True,live_projection=live,observation=observation,salary_clock=s.clock)
        # Loading with a later prepared offer must still restore the previous
        # settled cap correction; pending work cannot make old debt disappear.
        native_finance=projection(projection(after)[0])[1]
        payrolls=[struct.unpack_from('<I',native_finance,48+12*i)[0] for i in range(32)]
        restored=guest_application.restore_cap(store,'pending-restore',after,source_epoch=4,
            loaded_payload_sha256=hashlib.sha256(after).hexdigest(),finance_payrolls=payrolls,
            live_projection=dict(finance=hashlib.sha256(native_finance).hexdigest(),identity=live['identity']),connection_check=lambda:True)
        self.assertEqual(restored['cap_plan']['enforced_payroll_raw'],observation['team']['payroll_raw'])
        plan=guest_application.authorize(store,'issue2','journal2',after,access_check=lambda:True,live_projection=live)['application_plan']
        final=self.apply(after,raw,plan)
        receipt=guest_signing.settle(store,'journal2',final,access_check=lambda:True)
        reopened=FranchiseStore(store.path)
        self.assertEqual(receipt.charges,(4658000,4658000,3000000))
        self.assertEqual(reopened.load_team('49ers').charges,(9658000,6658000,3000000))
        self.assertEqual(reopened.load_team('49ers').revision,rev+1)
        self.assertEqual(guest_signing.inspect(reopened,'journal2',final)['save_position'],'confirmed_after')
        with reopened._connection() as db:
            self.assertTrue(verify(reopened,db,final))
            with self.assertRaises(Rejected):verify(reopened,db,after)
        finance=projection(final)[1];native=projection(final)[0]
        payrolls=[struct.unpack_from('<I',projection(native)[1],48+12*i)[0] for i in range(32)]
        live_finance=bytearray(finance)
        for i,value in enumerate(payrolls):struct.pack_into('<I',live_finance,48+12*i,value)
        restore=guest_application.restore_cap(reopened,'restore2',final,source_epoch=4,
            loaded_payload_sha256=hashlib.sha256(final).hexdigest(),finance_payrolls=payrolls,
            live_projection=dict(finance=hashlib.sha256(live_finance).hexdigest(),identity=hashlib.sha256(projection(final)[2]).hexdigest()),connection_check=lambda:True)
        self.assertEqual(restore['cap_plan']['enforced_payroll_raw'],struct.unpack_from('<I',projection(final)[1],48)[0])
        self.final_payload=final
        self.final_store=reopened

    def test_third_agreement_after_playing_weeks_keeps_both_old_bonus_layers_and_earned_pay(self):
        self.test_two_saved_agreements_reopen_negotiate_sign_and_restore_latest()
        s=self.s;store=self.final_store
        from tools.inspect_franchise_calendar import inspect_calendar
        from unittest.mock import patch
        advanced=bytearray(self.final_payload);offset=inspect_calendar(bytes(advanced))['scheduler_offset']
        advanced[offset+1]=8;advanced[offset+4]=18;advanced[offset+5]=9
        advanced=bytes(advanced);observation=json.loads(json.dumps(s.observation))
        observation['team']['payroll_raw']=struct.unpack_from('<I',projection(advanced)[1],48)[0]
        observation['team']['first_year_accumulator_raw']=struct.unpack_from('<I',projection(advanced)[1],56)[0]
        cal=inspect_calendar(advanced)
        observation['calendar']={k:cal[k] for k in observation['calendar']}
        raw={'amount_word':1200,'flags_word':(2<<29)|(3<<16)|3}
        rev=store.load_team('49ers').revision
        with patch.dict('franchise.salary_clock.DESCRIPTORS',{8:(hashlib.sha256(bytes(16)).hexdigest(),18)}):
            bridge=Bridge(store,provider=lambda _:json.dumps(dict(action='accept',reason='Agreed.',salaries=None,signing_bonus=None)),
                access_check=lambda:True,guest_snapshot=(s.bindings,s.before),guest_signing_reader=lambda:advanced)
            request=dict(protocol=1,operation='signing_context',request_id='context3',timeout_ms=5000,
                observation=observation,expected_revision=rev,guest_offer=raw,salary_clock=s.clock)
            context=bridge.handle(request);self.assertIsNone(context['error'],context)
            self.native_cases.append(dict(request=request,response=context,valid=True))
            proposal=bridge.handle(dict(request,operation='negotiate_proposal',request_id='proposal3',amendment_rule='legacy_bonus_carry_v1'))
            self.assertIsNone(proposal['error'],proposal)
            live=dict(finance=hashlib.sha256(projection(advanced)[1]).hexdigest(),identity=hashlib.sha256(projection(advanced)[2]).hexdigest())
            guest_application.prepare_amendment(store,'49ers','proposal3','journal3',bindings=s.bindings,
                before_payload=advanced,guest_offer=raw,expected_before_sha256=hashlib.sha256(advanced).hexdigest(),
                expected_revision=rev,access_check=lambda:True,live_projection=live,observation=observation,salary_clock=s.clock)
            plan=guest_application.authorize(store,'issue3','journal3',advanced,access_check=lambda:True,live_projection=live)['application_plan']
            self.assertEqual(plan['enforced_payroll_raw']+struct.unpack_from('<I',projection(advanced)[1],56)[0]+(2700 if self.s.observation['team']['team_flag_raw'] else 0),11208)
            final=self.apply(advanced,raw,plan)
            receipt=guest_signing.settle(store,'journal3',final,access_check=lambda:True)
            self.assertEqual(receipt.charges,(6208000,6558000,4900000))
            self.assertEqual(FranchiseStore(store.path).load_team('49ers').charges,(11208000,8558000,4900000))

    def test_giants_adjusted_branch_does_not_charge_old_bonus_twice(self):
        self.doCleanups();self.team_flag=1;self.setUp()
        self.test_third_agreement_after_playing_weeks_keeps_both_old_bonus_layers_and_earned_pay()

    def test_save_changing_during_context_read_is_rejected_without_a_decision(self):
        s=self.s;after=self.first();observation=json.loads(json.dumps(s.observation))
        observation['team']['payroll_raw']=8658
        snapshots=iter((after,s.before))
        from unittest.mock import Mock
        provider=Mock(side_effect=AssertionError('No decision during context read'))
        bridge=Bridge(s.store,provider=provider,access_check=lambda:True,guest_snapshot=(s.bindings,s.before),guest_signing_reader=lambda:next(snapshots))
        before=s.store.load_team('49ers').financial_snapshot()
        reply=bridge.handle(dict(protocol=1,operation='signing_context',request_id='changing',timeout_ms=5000,
            observation=observation,expected_revision=s.store.load_team('49ers').revision,guest_offer=s.offer_raw,salary_clock=s.clock))
        self.assertEqual(reply['error'],'state_rejected',reply)
        provider.assert_not_called()
        self.assertEqual(s.store.load_team('49ers').financial_snapshot(),before)

    def test_second_player_can_negotiate_without_losing_first_players_cap_debt(self):
        self.doCleanups()
        helper=fixtures.RetainedGuestCapTests();self.addCleanup(helper.doCleanups)
        s=self.s=helper.sample(team_flag=1,two_players=True)
        after=self.first();store=FranchiseStore(s.store.path)
        player=s.bindings['players'][1]['player_id'];observation=json.loads(json.dumps(s.observation))
        observation['biography'].update(source_slot=1,first_name='Authored',last_name='Freeagent')
        observation['team']['payroll_raw']=struct.unpack_from('<I',projection(after)[1],48)[0]
        observation['team']['first_year_accumulator_raw']=struct.unpack_from('<I',projection(after)[1],56)[0]
        raw={'amount_word':900,'flags_word':(2<<29)|(3<<16)|3};rev=store.load_team('49ers').revision
        bridge=Bridge(store,provider=lambda _:json.dumps(dict(action='accept',reason='Agreed.',salaries=None,signing_bonus=None)),
            access_check=lambda:True,guest_snapshot=(s.bindings,s.before),guest_signing_reader=lambda:after)
        request=dict(protocol=1,operation='negotiate_proposal',request_id='other-proposal',timeout_ms=5000,
            observation=observation,expected_revision=rev,guest_offer=raw,salary_clock=s.clock,amendment_rule='legacy_bonus_carry_v1')
        reply=bridge.handle(request);self.assertIsNone(reply['error'],reply)
        self.native_cases=[dict(request=request,response=reply,valid=True,journal_preparation=True)]
        live=dict(finance=hashlib.sha256(projection(after)[1]).hexdigest(),identity=hashlib.sha256(projection(after)[2]).hexdigest())
        guest_application.prepare_amendment(store,'49ers','other-proposal','other-journal',bindings=s.bindings,
            before_payload=after,guest_offer=raw,expected_before_sha256=hashlib.sha256(after).hexdigest(),expected_revision=rev,
            access_check=lambda:True,live_projection=live,observation=observation,salary_clock=s.clock)
        plan=guest_application.authorize(store,'other-issue','other-journal',after,access_check=lambda:True,live_projection=live)['application_plan']
        self.assertEqual(plan['source_slot'],1);self.assertEqual(plan['enforced_payroll_raw'],6684)
        final=self.apply(after,raw,plan)
        guest_signing.settle(store,'other-journal',final,access_check=lambda:True)
        ledger=FranchiseStore(store.path).load_team('49ers')
        self.assertEqual(ledger.charges,(13316000,10316000,5000000))
        self.assertEqual(len(ledger._legacy_amendments),2)

    def test_unrecorded_enforced_payroll_cannot_be_normalized_into_authority(self):
        s=self.s;bad=bytearray(s.before);struct.pack_into('<I',bad,0x44a8+0x124,8658)
        with s.store._connection() as db,self.assertRaises(Rejected):verify(s.store,db,bytes(bad))
