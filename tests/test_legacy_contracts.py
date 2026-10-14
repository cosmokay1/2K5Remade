"""Legacy data preservation, independent of modern acquisition accounting."""
import json
import struct
import unittest
import tempfile
from pathlib import Path
from dataclasses import FrozenInstanceError

import test_reconcile_franchise_payroll as payroll_fixtures
from franchise.legacy_contracts import LegacyContract
from tools.export_legacy_contracts import legacy_contracts
from tools.franchise_snapshot_bindings import create_bindings
from franchise.books import OpeningBooks, ActiveContract
from franchise.cap import Ledger, Offer, Rejected
from franchise.store import FranchiseStore


class LegacyContractsTests(unittest.TestCase):
    def ledger(self):
        return Ledger.from_opening(OpeningBooks(legacy_contracts=(
            LegacyContract('old', 900, 4, 2, 8, 7, 'authored preserved schedule'),)),
            cap=1400000, roster_reserve=0, max_bonus_years=5,
            veteran_minimums={'free': (200000,)})

    def test_durable_legacy_ownership_charges_and_new_signing_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'state.sqlite'; store = FranchiseStore(path)
            other = Ledger.from_opening(OpeningBooks(), cap=1400000, roster_reserve=0,
                max_bonus_years=5, veteran_minimums={'old': (1,), 'free': (200000,)})
            store.create_franchise({'a': self.ledger(), 'b': other}, seed='authored-world')
            before = store.load_team('a').financial_snapshot()
            self.assertEqual(before['charges'], [1125000]*7)
            self.assertEqual(before['signed_players'], ['old'])
            self.assertTrue(store.player_context('a', 'old')['initialized'])
            self.assertIsNone(store.player_context('a', 'old')['contract_accounting'])
            self.assertEqual(store.contract_generations('a')['preserved_legacy_contracts'][0]['original_years'], 8)
            with self.assertRaises(Rejected): store.sign('b', 'steal', Offer('old', (1,), 0), 0)
            with self.assertRaises(Rejected): store.sign('a', 'over-cap', Offer('free', (276000,), 0), 0)
            self.assertEqual(store.load_team('a').financial_snapshot(), before)
            store.sign('a', 'legal', Offer('free', (250000,), 0), 0)
            reopened = FranchiseStore(path).load_team('a')
            self.assertEqual(reopened.charges, (1375000, *([1125000]*6)))
            self.assertEqual(reopened.financial_snapshot()['signed_players'], ['free', 'old'])
            self.assertEqual(reopened.financial_snapshot()['legacy_schedule_sha256'], before['legacy_schedule_sha256'])
            self.assertEqual(reopened._opening_books.legacy_contracts, self.ledger()._opening_books.legacy_contracts)

    def test_unknown_legacy_cash_and_calendar_cannot_be_zeroed_or_advanced(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FranchiseStore(Path(directory)/'state.sqlite')
            store.create_team('a', self.ledger()); before = store.load_team('a').financial_snapshot()
            with self.assertRaises(Rejected): store.initialize_cash('a', (), source='authored incomplete cash')
            with self.assertRaises(Rejected): store.anchor_calendar(request_id='advance', league_year=2026,
                source='authored calendar', expected_revisions={'a':0})
            with self.assertRaises(Rejected): store.load_team('a').active_contract('old')
            self.assertEqual(store.load_team('a').financial_snapshot(), before)

    def test_modern_and_legacy_books_cannot_duplicate_ownership(self):
        legacy = LegacyContract('old', 900, 4, 2, 8, 7, 'authored')
        with self.assertRaises(ValueError):
            OpeningBooks(contracts=(ActiveContract(Offer('old', (1,), 0), 'authored'),), legacy_contracts=(legacy,))

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
