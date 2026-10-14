"""Authored save fixtures only; original payroll match is not modern legality."""
import contextlib
import io
from pathlib import Path
import struct
import tempfile
import unittest

import test_inspect_franchise_save as save_fixtures
from tools.inspect_franchise_save import PLAYER_START
from tools.reconcile_franchise_payroll import reconcile_payroll, main


class ReconcilePayrollTests(unittest.TestCase):
    def fixture(self):
        payload = save_fixtures.InspectFranchiseSaveTests().fixture()
        struct.pack_into('<H', payload, PLAYER_START + 10, 829)
        struct.pack_into('<I', payload, PLAYER_START + 36, 0x02410BA2)
        struct.pack_into('<I', payload, 0x44A8 + 0x124, 4766)
        return payload

    def test_matching_total_and_snapshot_charge_without_mutation(self):
        payload = bytes(self.fixture())
        report = reconcile_payroll(payload)
        self.assertTrue(report['matched'])
        self.assertEqual(len(report['teams']), 32)
        self.assertEqual(report['teams']['49ers']['charges'], [
            {'source_slot': 0, 'contract_year_index_from_term_fields': 0,
             'original_game_charge_dollars': 4766000}])
        self.assertEqual(payload, bytes(self.fixture()))
        self.assertNotIn('cap_room', report)

    def test_term_index_selects_later_charge(self):
        payload = self.fixture()
        struct.pack_into('<I', payload, PLAYER_START + 36, 0x02410BA1)
        struct.pack_into('<I', payload, 0x44A8 + 0x124, 3523)
        report = reconcile_payroll(bytes(payload))
        self.assertTrue(report['matched'])
        self.assertEqual(report['teams']['49ers']['charges'][0]['contract_year_index_from_term_fields'], 1)

    def test_mismatch_exposes_unknown_obligations_and_cli_fails(self):
        payload = self.fixture()
        struct.pack_into('<I', payload, 0x44A8 + 0x124, 5000)
        report = reconcile_payroll(bytes(payload))
        self.assertFalse(report['matched'])
        self.assertEqual(report['teams']['49ers']['difference_dollars'], 234000)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'SAVEGAME.DAT'; path.write_bytes(payload)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main([str(path)])
            self.assertEqual(error.exception.code, 3)
            self.assertEqual(path.read_bytes(), payload)

    def test_inactive_contract_is_not_imported_as_debt(self):
        payload = self.fixture()
        struct.pack_into('<I', payload, PLAYER_START + 36, 0x02410BA0)
        struct.pack_into('<I', payload, 0x44A8 + 0x124, 0)
        report = reconcile_payroll(bytes(payload))
        self.assertTrue(report['matched'])
        self.assertEqual(report['teams']['49ers']['inactive_roster_records'], 1)
        self.assertEqual(report['teams']['49ers']['charges'], [])

    def test_unsupported_active_fields_reject_before_match(self):
        for packed in (0x02410BA3, 0x00410BA2, 0x02480BA2, 0x02F10BA2):
            payload = self.fixture()
            struct.pack_into('<I', payload, PLAYER_START + 36, packed)
            with self.subTest(packed=packed), self.assertRaises(ValueError):
                reconcile_payroll(bytes(payload))
