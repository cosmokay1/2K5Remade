"""Authored FXG transitions only; saved effects are not write authorization."""
import copy
import hashlib
import json
import struct
import unittest

from franchise.guest_contracts import GuestContractTerms
from tools.confirm_saved_signing import confirm_saved_signing
from tools.franchise_offer_state import expected_signed_state
from tools.franchise_finance_state import saved_finance_state
from tools.franchise_identity_state import saved_identity_state
from tools.franchise_snapshot_bindings import create_bindings, SOFTDRINK_PROFILE, SOFTDRINK_XBE_SHA256
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE
import test_legacy_contracts as fixtures


class SavedSigningConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.before=bytes(fixtures.LegacyContractsTests().fixture())
        self.bindings=create_bindings(self.before,seed='Authored saved transition')
        self.player=self.bindings['players'][1]['player_id']
        self.offer=GuestContractTerms(829,4,1,2).to_offer(self.player)
        self.raw={'amount_word':829,'flags_word':(1<<29)|(2<<16)|4}
        self.after=self.signed(self.before)

    def signed(self,before,team=0):
        after=bytearray(before)
        # Move bound free-agent slot1 into the chosen team's pointer list.
        count=after[0x45C4+team*0x1F4]
        location=0x44A8+team*0x1F4+count*4
        struct.pack_into('<i',after,location,PLAYER_START+PLAYER_STRIDE-location+1)
        after[0x45C4+team*0x1F4]=count+1
        struct.pack_into('<H',after,0x358,0)
        struct.pack_into('<H',after,PLAYER_START+PLAYER_STRIDE+10,829)
        struct.pack_into('<I',after,PLAYER_START+PLAYER_STRIDE+36,(2<<24)|(4<<20)|(1<<16)|2)
        location=0x44A8+team*0x1F4+0x124
        struct.pack_into('<I',after,location,struct.unpack_from('<I',before,location)[0]+4766)
        return bytes(after)

    def confirm(self,after=None,**changes):
        args=dict(expected_before_sha256=hashlib.sha256(self.before).hexdigest(),offer=self.offer,
                  guest_offer=self.raw,team_id='49ers')
        args.update(changes)
        return confirm_saved_signing(self.bindings,self.before,self.after if after is None else after,**args)

    def test_exact_saved_effects_are_json_serializable_and_read_only(self):
        before,after=self.before,self.after
        report=self.confirm()
        self.assertEqual(report['source_slot'],1)
        self.assertEqual(report['player_id'],self.player)
        self.assertEqual(report['contract_charges'],[4766000,3523000])
        self.assertEqual((report['before_roster_payroll'],report['after_roster_payroll']),(4766000,9532000))
        self.assertFalse(report['write_authorized'])
        self.assertEqual(json.loads(json.dumps(report)),report)
        self.assertEqual((self.before,self.after),(before,after))
        self.assertEqual(report['after_payload_sha256'],hashlib.sha256(after).hexdigest())

    def test_correct_destination_and_captured_economic_terms_are_required(self):
        with self.assertRaises(ValueError): self.confirm(team_id='Bears')
        self.assertEqual(self.confirm(self.signed(self.before,team=1),team_id='Bears')['team_id'],'Bears')
        with self.assertRaises(ValueError): self.confirm(offer=GuestContractTerms(828,4,1,2).to_offer(self.player))
        with self.assertRaises(ValueError): self.confirm(guest_offer={**self.raw,'amount_word':828})
        with self.assertRaises(ValueError): self.confirm(offer=GuestContractTerms(829,4,1,2).to_offer('unknown'))

    def test_wrong_pinned_save_or_absent_transition_rejects(self):
        with self.assertRaises(ValueError): self.confirm(expected_before_sha256='0'*64)
        with self.assertRaises(ValueError): self.confirm(expected_before_sha256=True)
        with self.assertRaises(ValueError): self.confirm(self.before)
        with self.assertRaises(ValueError): self.confirm(b'wrong layout')

    def test_changed_contract_or_elapsed_term_rejects_even_with_plausible_payroll(self):
        for packed in ((2<<24)|(4<<20)|(1<<16)|1,(2<<24)|(3<<20)|(1<<16)|2):
            after=bytearray(self.after)
            struct.pack_into('<I',after,PLAYER_START+PLAYER_STRIDE+36,packed)
            with self.subTest(packed=packed),self.assertRaisesRegex(ValueError,'Saved contract'):
                self.confirm(bytes(after))

    def test_other_player_contract_changes_include_unbound_bank_slots(self):
        for slot in (0,2):
            after=bytearray(self.after)
            struct.pack_into('<H',after,PLAYER_START+slot*PLAYER_STRIDE+10,830)
            with self.subTest(slot=slot),self.assertRaisesRegex(ValueError,'Another player contract'):
                self.confirm(bytes(after))

    def test_another_player_moving_teams_is_not_an_isolated_signing(self):
        after=bytearray(self.after)
        # Move original slot0 to Bears while slot1 remains on 49ers.
        struct.pack_into('<i',after,0x44A8,PLAYER_START+PLAYER_STRIDE-0x44A8+1)
        after[0x45C4]=1
        location=0x44A8+0x1F4
        struct.pack_into('<i',after,location,PLAYER_START-location+1)
        after[0x45C4+0x1F4]=1
        with self.assertRaisesRegex(ValueError,'Another player changed roster'):
            self.confirm(bytes(after))

    def test_calendar_cap_adjustments_and_payroll_must_be_unchanged_except_target_charge(self):
        cases=[('calendar',0x91321,'<B',1),('cap',0x91320+0x83DC+0x15D0,'<i',81500),
               ('flag',0x91320+0xAC,'<I',1),('accumulator',0x44A8+0x19C,'<H',1),
               ('target-payroll',0x44A8+0x124,'<I',9531),('foreign-payroll',0x44A8+0x1F4+0x124,'<I',1)]
        for name,offset,fmt,value in cases:
            after=bytearray(self.after);struct.pack_into(fmt,after,offset,value)
            with self.subTest(name=name),self.assertRaises(ValueError): self.confirm(bytes(after))

    def test_identity_and_bank_size_changes_reject(self):
        after=bytearray(self.after)
        after[PLAYER_START+PLAYER_STRIDE+4]=1
        with self.assertRaises(ValueError): self.confirm(bytes(after))
        after=bytearray(self.after)
        struct.pack_into('<I',after,0x320,2480)
        location=0x32C
        struct.pack_into('<i',after,location,PLAYER_START+2480*PLAYER_STRIDE-location+1)
        with self.assertRaisesRegex(ValueError,'bank size'): self.confirm(bytes(after))

    def test_nonfinancial_settings_changes_do_not_invent_a_full_byte_equality_requirement(self):
        after=bytearray(self.after);after[:4]=b'\x01\0\0\0'
        report=self.confirm(bytes(after))
        self.assertEqual(report['contract_charges'],[4766000,3523000])
        self.assertIn('effects only',report['scope'])

    def test_four_to_one_scale_comes_from_the_validated_profile(self):
        before=bytearray(self.before)
        before[0x91326]=0
        struct.pack_into('<i',before,0x91320+0x83DC+0x15D0,75300)
        self.before=bytes(before);self.after=self.signed(self.before)
        self.bindings=copy.deepcopy(self.bindings)
        self.bindings.update(game_profile={'id':SOFTDRINK_PROFILE,'xbe_sha256':SOFTDRINK_XBE_SHA256},
            baseline_payload_sha256=hashlib.sha256(self.before).hexdigest())
        self.offer=GuestContractTerms(829,4,1,2).to_offer(self.player,contract_format='softdrink_fxg_v1')
        report=self.confirm()
        self.assertEqual(report['contract_format'],'softdrink_fxg_v1')
        self.assertEqual(report['contract_charges'],[19064000,14092000])
        self.assertEqual(report['after_roster_payroll']-report['before_roster_payroll'],19064000)
        self.assertEqual(expected_signed_state(self.bindings,self.before,offer=self.offer,
            guest_offer=self.raw,team_id='49ers'),
            (saved_finance_state(self.after),saved_identity_state(self.after)))
        self.bindings['game_profile']['xbe_sha256']='0'*64
        with self.assertRaises(ValueError): self.confirm()

    def test_expected_native_target_matches_independently_authored_saved_signing(self):
        before=self.before
        for team,index in (('49ers',0),('Bears',1)):
            expected=expected_signed_state(self.bindings,before,offer=self.offer,
                guest_offer=self.raw,team_id=team)
            after=self.signed(before,team=index)
            self.assertEqual(expected,(saved_finance_state(after),saved_identity_state(after)))
        self.assertEqual(self.before,before)

    def test_raw_flag_changes_outside_native_signing_effects_are_rejected(self):
        for slot,offset,bit in ((0,8,1),(1,8,1),(2,8,1),
                                (0,36,1<<31),(1,36,1<<31),(2,36,1<<31)):
            after=bytearray(self.after)
            where=PLAYER_START+slot*PLAYER_STRIDE+offset
            if offset==8:after[where]^=bit
            else:struct.pack_into('<I',after,where,struct.unpack_from('<I',after,where)[0]^bit)
            with self.subTest(slot=slot,offset=offset),self.assertRaisesRegex(ValueError,'raw financial'):
                self.confirm(bytes(after))

    def test_target_preserves_other_packed_bits_and_only_clears_signing_flag(self):
        before=bytearray(self.before)
        where=PLAYER_START+PLAYER_STRIDE
        before[where+8]=0xA9
        preserved=0xF000FFF0
        original=struct.unpack_from('<I',before,where+36)[0]
        struct.pack_into('<I',before,where+36,original|preserved)
        self.before=bytes(before)
        after=bytearray(self.signed(self.before))
        after[where+8]=0xA1
        packed=struct.unpack_from('<I',after,where+36)[0]
        struct.pack_into('<I',after,where+36,packed|preserved)
        self.assertEqual(expected_signed_state(self.bindings,self.before,offer=self.offer,
            guest_offer=self.raw,team_id='49ers'),
            (saved_finance_state(bytes(after)),saved_identity_state(bytes(after))))
        self.confirm(bytes(after))
        after[where+8]|=8
        with self.assertRaisesRegex(ValueError,'raw financial'):self.confirm(bytes(after))

    def test_target_refuses_wrong_candidate_or_terms(self):
        owned=GuestContractTerms.from_context(**self.raw).to_offer(self.bindings['players'][0]['player_id'])
        unknown=GuestContractTerms.from_context(**self.raw).to_offer('unknown')
        for offer,raw,team in ((unknown,self.raw,'49ers'),(owned,self.raw,'49ers'),
                               (self.offer,{**self.raw,'amount_word':828},'49ers'),
                               (self.offer,self.raw,'unsupported')):
            with self.subTest(team=team),self.assertRaises(ValueError):
                expected_signed_state(self.bindings,self.before,offer=offer,guest_offer=raw,team_id=team)
