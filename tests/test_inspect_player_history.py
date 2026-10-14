"""Authored packed-history fixtures; no retail histories or inferred metrics."""
import struct
import unittest

import test_inspect_franchise_save as save_fixtures
from tools.inspect_franchise_save import PLAYER_START
from tools.inspect_player_history import inspect_player_history


class InspectPlayerHistoryTests(unittest.TestCase):
    def fixture(self):
        payload = save_fixtures.InspectFranchiseSaveTests().fixture()
        bank = 0x41D54
        struct.pack_into('<I', payload, 0x360, 2)
        struct.pack_into('<i', payload, 0x364, bank - 0x364 + 1)
        struct.pack_into('<i', payload, PLAYER_START + 44, bank - (PLAYER_START + 44) + 1)
        struct.pack_into('<II', payload, bank, (1 << 23) | (18 << 16) | 122,
                         0xF0000000 | (2 << 23) | (19 << 16) | 0xFFFE)
        return payload

    def test_raw_values_flags_and_terminal_record_are_preserved(self):
        payload = self.fixture(); before = bytes(payload)
        report = inspect_player_history(before, 0)
        self.assertTrue(report['history_present'])
        self.assertEqual(report['entries'], [
            {'statistic_code_raw': 18, 'period_code_raw': 1, 'signed_value_raw': 122,
             'deleted': False, 'mode_code_raw': 0, 'bit30_raw': 0, 'last_entry': False},
            {'statistic_code_raw': 19, 'period_code_raw': 2, 'signed_value_raw': -2,
             'deleted': True, 'mode_code_raw': 1, 'bit30_raw': 1, 'last_entry': True}])
        self.assertEqual(payload, before)
        self.assertNotIn('tackles', report)
        self.assertNotIn('ratings', report)

    def test_null_is_unknown_not_zero(self):
        report = inspect_player_history(bytes(self.fixture()), 1)
        self.assertFalse(report['history_present'])
        self.assertEqual(report['entries'], [])
        self.assertIn('do not infer zero', report['missing_evidence'])

    def test_outside_unaligned_or_unterminated_history_rejects(self):
        for case in range(6):
            payload = self.fixture()
            if case == 0: struct.pack_into('<i', payload, PLAYER_START + 44, 1)
            if case == 1: struct.pack_into('<i', payload, PLAYER_START + 44, 0x41D55 - PLAYER_START - 44 + 1)
            if case == 2: struct.pack_into('<I', payload, 0x360, 0)
            if case == 3: struct.pack_into('<I', payload, 0x360, 0xFFFFFFFF)
            if case == 4: struct.pack_into('<I', payload, 0x41D58, 0)
            if case == 5: struct.pack_into('<i', payload, 0x364, 0)
            with self.subTest(case=case), self.assertRaises(ValueError):
                inspect_player_history(bytes(payload), 0)

    def test_slots_validate_without_coercion(self):
        for slot in (-1, True, 1.0, 2000):
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                inspect_player_history(bytes(self.fixture()), slot)
