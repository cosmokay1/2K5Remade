"""Authored records only; do not mistake cross-mod portrait IDs for identity."""
import struct
import unittest

from tests.test_roster_trial import fixture
from tools.plan_hybrid_roster import plan_hybrid


class HybridPlanTests(unittest.TestCase):
    def roster(self):
        data = fixture()
        for slot in (0, 1):
            at = 0xAFA8 + slot*0x54
            # January 2, 2000. Low nibble shares other appearance fields.
            data[at+0x19:at+0x1C] = bytes((0x10, 2, 0))
        return data

    def test_preserves_native_slot_and_photo_without_mutating_inputs(self):
        native, preseason = self.roster(), self.roster()
        struct.pack_into('<H', native, 0xAFA8+6, 1234)
        struct.pack_into('<H', preseason, 0xAFA8+6, 9876)
        preseason[0xAFA8+0x19] |= 7  # Not part of DOB.
        before = bytes(native), bytes(preseason)
        report = plan_hybrid(*before)
        self.assertTrue(report['all_desired_members_matched'])
        self.assertEqual(report['matched'][0]['preserve_native_photo_id'], 1234)
        self.assertEqual(report['matched'][0]['birth_date'], '2000-01-02')
        self.assertEqual((bytes(native), bytes(preseason)), before)
        self.assertFalse(report['writes_performed'])
        self.assertFalse(report['contracts_reconciled'])

    def test_conflicting_or_unknown_birth_date_blocks_match(self):
        for day, reason in ((3, 'birth_date_conflict'), (0, 'unknown_birth_date')):
            native, preseason = self.roster(), self.roster()
            preseason[0xAFA8+0x1A] = day
            report = plan_hybrid(bytes(native), bytes(preseason))
            self.assertFalse(report['all_desired_members_matched'])
            self.assertEqual(report['unresolved'][0]['reason'], reason)

    def test_missing_player_does_not_match_by_slot_or_portrait(self):
        native, preseason = self.roster(), self.roster()
        field = 0xAFA8+0x10
        target = field + struct.unpack_from('<i', preseason, field)[0] - 1
        preseason[target:target+2] = 'X'.encode('utf-16le')
        report = plan_hybrid(bytes(native), bytes(preseason))
        self.assertEqual(report['unresolved'][0]['reason'], 'missing_from_readable_native_bank')
        self.assertEqual(len(report['matched']), 1)

    def test_unassigned_native_player_can_match_without_copying_source_record(self):
        native, preseason = self.roster(), self.roster()
        # Remove slot 1 from native free agency, retaining its record/name data.
        struct.pack_into('<H', native, 0x78, 0)
        report = plan_hybrid(bytes(native), bytes(preseason))
        self.assertTrue(report['all_desired_members_matched'])
        player = next(p for p in report['matched'] if p['native_slot'] == 1)
        self.assertEqual(player['current_team'], 'unassigned')
        self.assertEqual(player['desired_team'], 'free_agents')

    def test_duplicate_native_name_is_not_resolved_by_matching_slot(self):
        native, preseason = self.roster(), self.roster()
        for field in (0x10, 0x14):
            old, new = 0xAFA8+field, 0xAFA8+0x54+field
            target = old + struct.unpack_from('<i', native, old)[0] - 1
            struct.pack_into('<i', native, new, target-new+1)
        report = plan_hybrid(bytes(native), bytes(preseason))
        self.assertEqual(report['unresolved'][0]['reason'], 'ambiguous_name')
        self.assertFalse(report['all_desired_members_matched'])


if __name__ == '__main__':
    unittest.main()
