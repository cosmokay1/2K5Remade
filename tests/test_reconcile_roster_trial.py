"""Authored fixture evidence; distinguish roster import from modern accounting."""
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).parent))
import test_inspect_franchise_cap as fixtures
from tools.reconcile_roster_trial import reconcile_trial


class ReconcileRosterTrialTests(unittest.TestCase):
    def fixture(self):
        data=bytes(fixtures.OriginalCapTests().fixture())
        return data[0x2E0:0x2E0+0x91040],data

    def test_native_totals_and_adjustment_match_without_modern_authority(self):
        roster,save=self.fixture();r=reconcile_trial(roster,save,money_scale=4)
        t=r['teams']['49ers']
        self.assertTrue(r['all_native_payrolls_match'])
        self.assertTrue(r['roster_membership_and_biography_preserved'])
        self.assertEqual(r['league_cap'],322000000)
        self.assertEqual(t['stored_roster_payroll'],19064000)
        self.assertEqual(t['room_without_adjustment']-t['room_with_adjustment'],2000000)
        self.assertFalse(r['complete_opening_book']);self.assertFalse(r['signing_authorized'])
        self.assertEqual(self.fixture(),(roster,save))

    def test_term_and_membership_changes_reported_separately(self):
        roster,save=self.fixture();changed=bytearray(save)
        struct.pack_into('<H',changed,0xB288+10,900)
        changed[0xB288+4]^=1
        r=reconcile_trial(roster,bytes(changed),money_scale=1)
        self.assertFalse(r['all_native_payrolls_match'])
        self.assertFalse(r['roster_membership_and_biography_preserved'])
        self.assertEqual(len(r['contract_word_changes']),1)
        self.assertEqual(r['roster_differences'][0]['source_slot'],0)

    def test_unknown_schedule_does_not_become_zero_or_a_matching_total(self):
        roster,save=self.fixture();changed=bytearray(save)
        struct.pack_into('<I',changed,0xB288+0x24,3)
        r=reconcile_trial(roster,bytes(changed),money_scale=1)
        self.assertIsNone(r['teams']['49ers']['reconstructed_roster_payroll'])
        self.assertIsNone(r['teams']['49ers']['native_payroll_matches'])
        self.assertFalse(r['all_native_payrolls_match'])
        self.assertEqual(r['unresolved_native_contracts'][0]['status'],'unsupported')

    def test_auxiliary_names_can_be_audited_without_broadening_identity_authority(self):
        roster,save=self.fixture();raw=bytearray(roster);field=0xAFA8+0x10;aux=0x749CC
        struct.pack_into('<i',raw,field,aux-field+1)
        raw[aux:aux+12]='Other\0'.encode('utf-16le')
        changed=bytearray(save);changed[0x2E0:0x2E0+len(raw)]=raw
        r=reconcile_trial(bytes(raw),bytes(changed),money_scale=4)
        self.assertTrue(r['roster_membership_and_biography_preserved'])
        self.assertTrue(r['all_native_payrolls_match'])
        self.assertFalse(r['strict_franchise_identity_supported'])
        self.assertEqual(len(r['saved_nonstandard_name_pointers']),1)
        self.assertFalse(r['signing_authorized'])

    def test_explicit_scale_and_valid_franchise_required(self):
        roster,save=self.fixture()
        for scale in (True,0,2):
            with self.assertRaises(ValueError):reconcile_trial(roster,save,money_scale=scale)
        with self.assertRaises(ValueError):reconcile_trial(roster,roster,money_scale=4)


if __name__=='__main__':unittest.main()
