import copy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from franchise.books import OpeningBooks
from franchise.cap import Ledger
from franchise.store import FranchiseStore
from tools.export_legacy_contracts import legacy_contracts
from tools.franchise_snapshot_bindings import create_bindings, resolve_bindings
from tools.inspect_franchise_calendar import inspect_calendar
from tools.reconcile_signing_context import reconcile_signing_context
import test_legacy_contracts as legacy_fixtures


class SigningContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.payload = bytes(legacy_fixtures.LegacyContractsTests().fixture())
        self.bindings = create_bindings(self.payload, seed='authored-live-checkpoint')
        self.store = FranchiseStore(Path(self.temporary.name) / 'franchise.sqlite')
        members = resolve_bindings(self.bindings, self.payload)
        self.store.create_franchise({'49ers': Ledger.from_opening(OpeningBooks(
            legacy_contracts=legacy_contracts(self.bindings, self.payload)['49ers']),
            cap=80500000, roster_reserve=0, max_bonus_years=5, veteran_minimums={},
            observed_player_ids=frozenset(p['player_id'] for p in members.values()),
            observed_player_source='authored snapshot')}, seed=self.bindings['personality_seed'])
        calendar = inspect_calendar(self.payload)
        self.observation = {'biography': {'source_slot': 1, 'first_name': 'Authored',
            'last_name': 'Freeagent', 'pbp_photo_raw': '00000000', 'dob_region_raw': '000000'},
            'team': {'table_index': 0, 'table_mode': 2, 'payroll_raw': 4766,
                     'league_cap_raw': 80500, 'team_flag_raw': 0, 'first_year_accumulator_raw': 0},
            'calendar': {k: calendar[k] for k in ('season_index', 'display_year', 'phase_01_raw',
                'phase_02_raw', 'step_04_raw', 'step_05_raw', 'counter_08_raw')}}

    def inspect(self, observation=None, revision=0):
        return reconcile_signing_context(self.bindings, self.payload,
            self.observation if observation is None else observation, self.store, expected_revision=revision)

    def test_persisted_free_agent_identity_without_authorizing_or_assigning_floor(self):
        before = self.store.load_team('49ers').financial_snapshot()
        result = self.inspect()
        self.assertEqual(result['player_id'], self.bindings['players'][1]['player_id'])
        self.assertTrue(result['player_context']['initialized'])
        self.assertTrue(result['player_context']['classification_pending'])
        self.assertFalse(result['write_authorized'])
        self.assertFalse(result['ai_authorized'])
        self.assertEqual(before, self.store.load_team('49ers').financial_snapshot())
        self.assertEqual(self.inspect(), result)

    def test_changed_live_identity_calendar_or_cap_rejects(self):
        changes = [('biography', 'source_slot', 0), ('biography', 'dob_region_raw', '000001'),
                   ('calendar', 'season_index', 23), ('calendar', 'phase_01_raw', 1),
                   ('team', 'table_mode', 1), ('team', 'table_index', 32),
                   ('team', 'payroll_raw', 4765), ('team', 'league_cap_raw', 0),
                   ('team', 'team_flag_raw', 1), ('team', 'first_year_accumulator_raw', 1),
                   ('team', 'table_index', False)]
        for group, key, value in changes:
            observation = copy.deepcopy(self.observation); observation[group][key] = value
            with self.subTest(group=group, key=key), self.assertRaises(ValueError):
                self.inspect(observation)
        with self.assertRaises(ValueError): self.inspect(revision=1)
        with self.assertRaises(ValueError): self.inspect(revision=False)

    def test_wrong_snapshot_book_with_same_player_ids_rejects(self):
        # Same cap and identities cannot substitute a different schedule/source.
        data = bytearray(self.payload)
        import struct
        from tools.inspect_franchise_save import PLAYER_START
        struct.pack_into('<H', data, PLAYER_START + 10, 828)
        struct.pack_into('<I', data, 0x44A8 + 0x124, 4760)
        with self.assertRaises(ValueError):
            reconcile_signing_context(self.bindings, bytes(data), self.observation,
                                     self.store, expected_revision=0)

    def test_same_cap_totals_and_ids_do_not_hide_changed_contract_source(self):
        record = legacy_contracts(self.bindings, self.payload)['49ers'][0]
        other = FranchiseStore(Path(self.temporary.name) / 'other.sqlite')
        members = resolve_bindings(self.bindings, self.payload)
        other.create_franchise({'49ers': Ledger.from_opening(OpeningBooks(
            legacy_contracts=(replace(record, source='different saved checkpoint'),)),
            cap=80500000, roster_reserve=0, max_bonus_years=5, veteran_minimums={},
            observed_player_ids=frozenset(p['player_id'] for p in members.values()),
            observed_player_source='authored snapshot')}, seed=self.bindings['personality_seed'])
        self.assertEqual(other.load_team('49ers').charges, self.store.load_team('49ers').charges)
        with self.assertRaisesRegex(ValueError, 'inventory'):
            reconcile_signing_context(self.bindings, self.payload, self.observation,
                                      other, expected_revision=0)


if __name__ == '__main__':
    unittest.main()
