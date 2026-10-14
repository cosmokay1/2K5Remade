"""Authored calendar records, including divergent scheduled-game years."""
import struct
import unittest

from tools.inspect_franchise_calendar import inspect_calendar
from tools.inspect_franchise_save import SIZE


class CalendarTests(unittest.TestCase):
    def fixture(self):
        data = bytearray(SIZE)
        data[:4] = b'\x04\0\0\0'
        data[0x2E0:0x2E4] = b'ROST'
        data[0x30C:0x310] = b'ROST'
        struct.pack_into('<I', data, 0x2E4, 0x91020)
        data[0x91320:0x9132B] = bytes([2, 7, 0, 32, 5, 0, 3, 0, 99, 0, 1])
        data[0x917EF] = 4  # A scheduled game's year is not the season index.
        return data

    def test_season_comes_from_scheduler_and_preserves_raw_unknowns(self):
        data = self.fixture(); before = bytes(data)
        result = inspect_calendar(before)
        self.assertEqual(result['scheduler_offset'], 0x91320)
        self.assertEqual(result['season_index'], 3)
        self.assertEqual(result['display_year'], 2007)
        self.assertEqual(result['counter_08_raw'], 99)
        self.assertEqual(result['phase_01_raw'], 7)
        data[0x917EF] = 26
        self.assertEqual(inspect_calendar(bytes(data))['display_year'], 2007)
        self.assertEqual(before, bytes(self.fixture()))

    def test_wrong_section_boundaries_or_mode_reject(self):
        for case in range(7):
            data = self.fixture()
            if case == 0: data[0] = 3
            if case == 1: data[0x2E0] = 0
            if case == 2: data[0x30C] = 0
            if case == 3: struct.pack_into('<I', data, 0x2E4, 0x91021)
            if case == 4: struct.pack_into('<I', data, 0x2E4, 0)
            if case == 5: data[0x91320] = 1
            if case == 6: data[0x91323] = 52
            with self.subTest(case=case), self.assertRaises(ValueError):
                inspect_calendar(bytes(data))
        with self.assertRaises(ValueError): inspect_calendar(bytes(self.fixture())[:-1])
