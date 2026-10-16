import copy
from contextlib import closing
from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

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

    def test_owned_player_comparison_preserves_bonus_and_never_grants_signing(self):
        player=self.bindings['players'][0]['player_id']
        members=resolve_bindings(self.bindings,self.payload)
        store=FranchiseStore(Path(self.temporary.name)/'classified.sqlite')
        store.create_franchise({'49ers':Ledger.from_opening(OpeningBooks(
            legacy_contracts=legacy_contracts(self.bindings,self.payload)['49ers']),
            cap=80500000,roster_reserve=0,max_bonus_years=5,
            veteran_minimums={player:(1000000,)*7},
            observed_player_ids=frozenset(p['player_id'] for p in members.values()),
            observed_player_source='authored snapshot')},seed=self.bindings['personality_seed'])
        observation=copy.deepcopy(self.observation)
        observation['biography'].update(source_slot=0,first_name='Synthetic',last_name='Starter')
        before=store.load_team('49ers').financial_snapshot()
        result=reconcile_signing_context(self.bindings,self.payload,observation,store,
            expected_revision=0,guest_offer={'amount_word':829,'flags_word':(1<<29)|(2<<16)|4})
        comparison=result['offer_context']
        self.assertEqual(comparison['outcome'],'amendment_comparison')
        self.assertIsNone(comparison['preview']);self.assertIsNone(comparison['reason'])
        self.assertEqual(comparison['amendment']['carried_bonus_charges'],[1658000,1658000])
        self.assertEqual(comparison['amendment']['combined_player_charges'],[6424000,5181000])
        self.assertFalse(comparison['amendment']['settlement_authorized'])
        self.assertFalse(result['ai_authorized']);self.assertFalse(result['write_authorized'])
        self.assertEqual(before,store.load_team('49ers').financial_snapshot())
        from franchise.bridge import Bridge
        from unittest.mock import Mock
        provider=Mock(side_effect=AssertionError('Comparison must not grant inference'))
        bridge=Bridge(store,provider=provider,access_check=lambda:None,
                      guest_snapshot=(self.bindings,self.payload))
        denied=bridge.handle(dict(protocol=1,request_id='owned-comparison',operation='negotiate_proposal',
            observation=observation,guest_offer={'amount_word':829,'flags_word':(1<<29)|(2<<16)|4},
            expected_revision=0,timeout_ms=5000))
        self.assertEqual(denied['error'],'state_rejected')
        self.assertIn('does not authorize',denied['detail'])
        provider.assert_not_called()
        self.assertEqual(before,store.load_team('49ers').financial_snapshot())

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

    def test_one_validated_replay_supplies_inventory_finances_and_player_context(self):
        expected=self.store.player_context('49ers',self.bindings['players'][1]['player_id'])
        before=Path(self.store.path).read_bytes()
        with patch.object(self.store,'_load',wraps=self.store._load) as load:
            result=self.inspect()
        self.assertEqual(load.call_count,1)
        self.assertEqual(result['player_context'],expected)
        self.assertEqual(Path(self.store.path).read_bytes(),before)

    def test_concurrent_budget_commit_is_not_hidden_by_the_read_snapshot(self):
        with closing(sqlite3.connect(self.store.path)) as db:
            self.assertEqual(db.execute('PRAGMA journal_mode=WAL').fetchone()[0],'wal')
        writer=FranchiseStore(self.store.path)
        original=self.store._player_context_from_ledger
        def commit_after_read(*args,**kwargs):
            context=original(*args,**kwargs)
            writer.update_budget('49ers',cap=80501000,roster_reserve=0,expected_revision=0)
            return context
        with patch.object(self.store,'_player_context_from_ledger',side_effect=commit_after_read):
            with self.assertRaisesRegex(ValueError,'changed during inspection'):self.inspect()
        self.assertEqual(writer.load_team('49ers').revision,1)

    def test_concurrent_existing_actor_edit_is_detected_without_new_events(self):
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute('PRAGMA journal_mode=WAL')
            count=db.execute('SELECT count(*) FROM events').fetchone()[0]
        original=self.store._player_context_from_ledger
        def edit_after_read(*args,**kwargs):
            context=original(*args,**kwargs)
            with closing(sqlite3.connect(self.store.path)) as db:
                event_id,raw=db.execute("SELECT id,payload FROM events WHERE kind='actor' LIMIT 1").fetchone()
                event=json.loads(raw);event['actor']['relationships']['trust']=0.6
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(event),event_id));db.commit()
                self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0],count)
            return context
        with patch.object(self.store,'_player_context_from_ledger',side_effect=edit_after_read):
            with self.assertRaisesRegex(ValueError,'changed during inspection'):self.inspect()
        with self.assertRaisesRegex(ValueError,'franchise origin'):self.inspect()

    def test_database_file_replacement_during_read_is_rejected(self):
        replacement=Path(self.temporary.name)/'replacement.sqlite'
        shutil.copyfile(self.store.path,replacement)
        writer=FranchiseStore(replacement)
        writer.update_budget('49ers',cap=80501000,roster_reserve=0,expected_revision=0)
        original=self.store._player_context_from_ledger
        def replace_after_read(*args,**kwargs):
            context=original(*args,**kwargs)
            try:os.replace(replacement,self.store.path)
            except PermissionError:self.skipTest('Platform prevents replacing an open SQLite file')
            return context
        with patch.object(self.store,'_player_context_from_ledger',side_effect=replace_after_read):
            with self.assertRaisesRegex(ValueError,'changed during inspection'):self.inspect()
        self.assertEqual(self.store.load_team('49ers').revision,1)


if __name__ == '__main__':
    unittest.main()
