"""Independent authored save changes expose native cap debt, never grant writes."""
import copy
import hashlib
import struct
import unittest

from franchise.books import OpeningBooks
from franchise.cap import Ledger
from franchise.guest_contracts import GuestContractTerms
from tools.confirm_saved_amendment import confirm_saved_amendment
from tools.export_legacy_contracts import legacy_contracts
from tools.franchise_offer_state import expected_amended_state
from tools.franchise_snapshot_bindings import create_bindings
from tools.inspect_franchise_save import PLAYER_START,PLAYER_STRIDE
import test_legacy_contracts as fixtures


class SavedAmendmentConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.before=bytes(fixtures.LegacyContractsTests().fixture())
        self.bindings=create_bindings(self.before,seed='authored saved amendment')
        self.player=self.bindings['players'][0]['player_id']
        self.raw={'amount_word':600,'flags_word':(2<<29)|(3<<16)}
        self.offer=GuestContractTerms.from_context(**self.raw).to_offer(self.player)
        ledger=Ledger.from_opening(OpeningBooks(legacy_contracts=legacy_contracts(self.bindings,self.before)['49ers']),
            cap=80500000,roster_reserve=0,max_bonus_years=5,veteran_minimums={self.player:(1000000,)*7})
        self.comparison=ledger.preview_legacy_amendment(self.offer,0)
        after=bytearray(self.before)
        after[PLAYER_START+8]&=0xF7
        struct.pack_into('<H',after,PLAYER_START+10,600)
        previous=struct.unpack_from('<I',after,PLAYER_START+36)[0]
        struct.pack_into('<I',after,PLAYER_START+36,(previous&~0x0FF7000F)|(3<<24)|(2<<16)|3)
        struct.pack_into('<I',after,0x44A8+0x124,2000)
        self.after=bytes(after)

    def confirm(self,after=None,**changes):
        args=dict(expected_before_sha256=hashlib.sha256(self.before).hexdigest(),offer=self.offer,
            guest_offer=self.raw,team_id='49ers',comparison=self.comparison)
        args.update(changes)
        return confirm_saved_amendment(self.bindings,self.before,self.after if after is None else after,**args)

    def test_saved_native_effects_prove_the_need_for_cap_adapter_not_enforcement(self):
        before,after=self.before,self.after
        report=self.confirm()
        self.assertEqual(report['native_annual_team_charges_after'],[2000000]*3)
        self.assertEqual(report['required_retained_team_charges'],[1658000,1658000,0])
        self.assertEqual(report['combined_player_charges'],[3658000,3658000,2000000])
        self.assertFalse(report['write_authorized']);self.assertFalse(report['cap_enforcement_verified'])
        self.assertEqual((self.before,self.after),(before,after))
        self.assertEqual(report['source_slot'],0)

    def test_wrong_terms_team_source_and_incomplete_comparison_reject(self):
        for change in ({'expected_before_sha256':'0'*64},{'team_id':'Bears'},
                       {'guest_offer':{**self.raw,'amount_word':601}},
                       {'comparison':{**self.comparison,'requires_player_agreement':False}},
                       {'comparison':{**self.comparison,'carried_bonus_charges':[0,0]}}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.confirm(**change)

    def test_no_native_transition_cannot_prove_new_identical_bonus_agreement(self):
        raw={'amount_word':829,'flags_word':(1<<29)|(2<<16)|4}
        offer=GuestContractTerms.from_context(**raw).to_offer(self.player)
        after=bytearray(self.before);after[0]=1
        with self.assertRaisesRegex(ValueError,'Unchanged native terms'):
            self.confirm(bytes(after),offer=offer,guest_offer=raw)

    def test_other_bank_contract_flags_and_identity_changes_reject(self):
        for offset in (PLAYER_START+2*PLAYER_STRIDE+10,PLAYER_START+4,PLAYER_START+8):
            after=bytearray(self.after);after[offset]^=0x80
            with self.subTest(offset=offset),self.assertRaises(ValueError):self.confirm(bytes(after))

    def test_native_payroll_cannot_be_faked_to_include_supplemental_debt(self):
        after=bytearray(self.after);struct.pack_into('<I',after,0x44A8+0x124,3658)
        with self.assertRaises(ValueError):self.confirm(bytes(after))

    def test_tampered_combined_room_and_posting_reject(self):
        for field in ('combined_player_charges','annual_team_charges_after','room_after'):
            comparison=copy.deepcopy(self.comparison)
            if field=='room_after':comparison[field]+=1
            else:comparison[field][0]+=1
            with self.subTest(field=field),self.assertRaises(ValueError):self.confirm(comparison=comparison)
