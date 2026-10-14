"""Authored fixtures distinguish original adjustment from roster payroll."""
import struct
import unittest

import test_reconcile_franchise_payroll as payroll_fixtures
from tools.inspect_franchise_cap import inspect_cap


class OriginalCapTests(unittest.TestCase):
    def fixture(self):
        data = payroll_fixtures.ReconcilePayrollTests().fixture()
        data[0x2E0:0x2E4] = b'ROST'; data[0x30C:0x310] = b'ROST'
        struct.pack_into('<I', data, 0x2E4, 0x91020)
        data[0x91320] = 2; data[0x91323] = 32
        struct.pack_into('<i', data, 0x91320 + 0x83DC + 0x15D0, 80500)
        struct.pack_into('<H', data, 0x44A8 + 0x19C, 500)
        struct.pack_into('<I', data, 0x91320 + 0xAC, 1)
        return data

    def test_adjustment_branch_is_separate_and_read_only(self):
        data = self.fixture(); before = bytes(data)
        report = inspect_cap(before)
        row = report['teams']['49ers']
        self.assertEqual(report['league_cap_dollars'], 80500000)
        self.assertEqual(row['room_without_team_adjustment_dollars'], 75734000)
        self.assertEqual(row['room_if_team_adjustment_requested_dollars'], 75234000)
        self.assertEqual(row['roster_payroll_dollars'], 4766000)
        self.assertEqual(data, before)
        struct.pack_into('<I', data, 0x91320 + 0xAC, 0)
        self.assertEqual(inspect_cap(bytes(data))['teams']['49ers']['room_if_team_adjustment_requested_dollars'], 75734000)

    def test_unreconciled_payroll_or_nonpositive_cap_rejects(self):
        data = self.fixture(); struct.pack_into('<I', data, 0x44A8 + 0x124, 5000)
        with self.assertRaises(ValueError): inspect_cap(bytes(data))
        data = self.fixture()
        struct.pack_into('<i', data, 0x91320 + 0x83DC + 0x15D0, -1)
        with self.assertRaises(ValueError): inspect_cap(bytes(data))
