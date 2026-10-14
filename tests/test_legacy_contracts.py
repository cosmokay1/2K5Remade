"""Legacy data preservation, independent of modern acquisition accounting."""
import json
import struct
import unittest
from dataclasses import FrozenInstanceError

import test_reconcile_franchise_payroll as payroll_fixtures
from franchise.legacy_contracts import LegacyContract
from tools.export_legacy_contracts import legacy_contracts
from tools.franchise_snapshot_bindings import create_bindings


class LegacyContractsTests(unittest.TestCase):
    def fixture(self):
        data = payroll_fixtures.ReconcilePayrollTests().fixture()
        data[0x2E0:0x2E4] = b'ROST'; data[0x30C:0x310] = b'ROST'
        struct.pack_into('<I', data, 0x2E4, 0x91020)
        data[0x91320] = 2; data[0x91323] = 32; data[0x91326] = 22
        struct.pack_into('<i', data, 0x91320 + 0x83DC + 0x15D0, 80500)
        return data

    def test_long_original_schedule_and_rounding_survive_serialization(self):
        contract = LegacyContract('p', 900, 4, 2, 8, 7, 'authored raw terms')
        self.assertEqual(contract.charges(), (1125000,)*7)
        self.assertEqual(LegacyContract.from_dict(json.loads(json.dumps(contract.to_dict()))), contract)
        with self.assertRaises(FrozenInstanceError): contract.remaining_years = 6
        gildon = LegacyContract('g', 829, 4, 1, 2, 2, 'authored rounding case')
        self.assertEqual(gildon.charges(), (4766000, 3523000))
        self.assertEqual(sum(gildon.charges()), 8289000)
        self.assertNotIn('guaranteed_salaries', contract.to_dict())
        self.assertNotIn('paid_cash', contract.to_dict())

    def test_export_preserves_pinned_identity_and_rejects_mismatch(self):
        data = self.fixture(); before = bytes(data)
        bindings = create_bindings(before, seed='authored')
        result = legacy_contracts(bindings, before)
        contract = result['49ers'][0]
        self.assertEqual(contract.player_id, bindings['players'][0]['player_id'])
        self.assertEqual(contract.charges(), (4766000, 3523000))
        self.assertEqual(sum(map(len, result.values())), 1)
        self.assertEqual(data, before)
        struct.pack_into('<I', data, 0x44A8 + 0x124, 5000)
        with self.assertRaises(ValueError): legacy_contracts(bindings, bytes(data))

    def test_unknown_term_or_record_fields_reject_without_defaults(self):
        for remaining in (0, 9, True):
            with self.assertRaises(ValueError): LegacyContract('p', 900, 4, 2, 8, remaining, 'fixture')
        data = LegacyContract('p', 900, 4, 2, 8, 7, 'fixture').to_dict()
        data['paid_cash'] = 0
        with self.assertRaises(ValueError): LegacyContract.from_dict(data)
