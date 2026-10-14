"""Authored packed-history fixtures; no retail histories or inferred metrics."""
import struct
import unittest

import test_inspect_franchise_save as save_fixtures
from tools.inspect_franchise_save import PLAYER_START
from tools.inspect_player_history import inspect_player_history, calendar_candidates


class InspectPlayerHistoryTests(unittest.TestCase):
    def test_candidate_year_uses_player_period_and_preserves_unknowns(self):
        payload = self.fixture()
        payload[0x2E0:0x2E4]=b'ROST'; payload[0x30C:0x310]=b'ROST'
        struct.pack_into('<I',payload,0x2E4,0x91020)
        payload[0x91320]=2;payload[0x91323]=32
        struct.pack_into('<I',payload,PLAYER_START+0x24,7<<8)
        before=bytes(payload); report=calendar_candidates(before,0)
        self.assertEqual(report['current_period_code_raw'],7)
        self.assertEqual(report['entries'][0]['candidate_calendar_year'],1998)
        self.assertIsNone(report['entries'][1]['candidate_calendar_year'])
        self.assertTrue(report['entries'][1]['deleted'])
        self.assertEqual(payload,before)
        struct.pack_into('<I',payload,PLAYER_START+0x24,0)
        self.assertTrue(all(e['candidate_calendar_year'] is None for e in calendar_candidates(bytes(payload),0)['entries']))

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
             'deleted': True, 'mode_code_raw': 1, 'bit30_raw': 1, 'last_entry': True,
             'mapped_metric_name': 'sacks', 'mapped_unit': 'half_sack_units', 'mapped_value': -1.0,
             'mapping_scope': 'historical sack mapping inferred from descriptor and Gildon NFL corroboration; live updates/coverage unverified'}])
        self.assertEqual(payload, before)
        self.assertNotIn('tackles', report)
        self.assertNotIn('ratings', report)

    def test_null_is_unknown_not_zero(self):
        report = inspect_player_history(bytes(self.fixture()), 1)
        self.assertFalse(report['history_present'])
        self.assertEqual(report['entries'], [])
        self.assertIn('do not infer zero', report['missing_evidence'])

    def test_saved_sacks_preserve_raw_half_units_and_exact_values(self):
        payload = self.fixture()
        struct.pack_into('<II', payload, 0x41D54, (1<<23) | (19<<16) | 5,
                         0x80000000 | (2<<23) | (19<<16) | 12)
        report = inspect_player_history(bytes(payload), 0)
        self.assertEqual([e['signed_value_raw'] for e in report['entries']], [5, 12])
        self.assertEqual([e['mapped_value'] for e in report['entries']], [2.5, 6.0])
        self.assertTrue(all(e['mapped_unit']=='half_sack_units' for e in report['entries']))

    def test_passing_mapping_retains_raw_mode_period_and_missing_fields(self):
        payload = self.fixture()
        struct.pack_into('<II', payload, 0x41D54, (1 << 23) | (6 << 16) | 478,
                         0x80000000 | (1 << 23) | (8 << 16) | 3216)
        report = inspect_player_history(bytes(payload), 0)
        self.assertEqual([(e['mapped_metric_name'], e['mapped_unit'], e['signed_value_raw'])
                          for e in report['entries']], [('pass_attempts', 'count', 478), ('passing_yards', 'yards', 3216)])
        self.assertEqual([e['statistic_code_raw'] for e in report['entries']], [6, 8])
        self.assertEqual([e['period_code_raw'] for e in report['entries']], [1, 1])
        self.assertEqual([e['mode_code_raw'] for e in report['entries']], [0, 0])
        self.assertFalse(any(e.get('mapped_metric_name') == 'completions' for e in report['entries']))

    def test_games_and_rushing_are_separate_from_passing_touchdowns(self):
        payload = self.fixture()
        bank = 0x41D54
        struct.pack_into('<I', payload, 0x360, 5)
        for index, (code, value) in enumerate(((0, 10), (1, 30), (2, -2), (3, 2), (9, 5))):
            word = (1 << 23) | (code << 16) | (value & 0xFFFF)
            if index == 4: word |= 0x80000000
            struct.pack_into('<I', payload, bank + 4 * index, word)
        report = inspect_player_history(bytes(payload), 0)
        self.assertEqual([e['mapped_metric_name'] for e in report['entries']],
                         ['games', 'rush_attempts', 'rushing_yards', 'rushing_touchdowns', 'passing_touchdowns'])
        self.assertEqual(report['entries'][2]['mapped_unit'], 'yards')
        self.assertEqual(report['entries'][2]['signed_value_raw'], -2)
        self.assertFalse(any(e.get('mapped_metric_name') in ('targets', 'pressures', 'qb_hits') for e in report['entries']))

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
