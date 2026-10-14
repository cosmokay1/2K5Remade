"""Authored snapshots test issued identity continuity, not retail bank rebuilds."""
import contextlib
import copy
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

import test_inspect_franchise_save as save_fixtures
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE
from tools.franchise_snapshot_bindings import create_bindings, resolve_bindings, initial_profiles, main, resolve_signing_candidate


class SnapshotBindingsTests(unittest.TestCase):
    def fixture(self):
        data = save_fixtures.InspectFranchiseSaveTests().fixture()
        data[0x2E0:0x2E4] = b'ROST'; data[0x30C:0x310] = b'ROST'
        struct.pack_into('<I', data, 0x2E4, 0x91020)
        data[0x91320] = 2; data[0x91323] = 32
        data[0x91326] = 22  # Display season 2026, matching the fixture's game year.
        return data

    def test_signing_transfer_and_restart_preserve_ids_and_initial_profiles(self):
        payload = self.fixture(); original = bytes(payload)
        bindings = create_bindings(original, seed='authored-franchise')
        profiles = initial_profiles(bindings, original)
        before = resolve_bindings(bindings, original)
        # Move the existing free agent to the club and change financial words.
        payload[0x45C4] = 2
        struct.pack_into('<i', payload, 0x44AC, PLAYER_START + PLAYER_STRIDE - 0x44AC + 1)
        struct.pack_into('<H', payload, 0x358, 0)
        struct.pack_into('<H', payload, PLAYER_START + PLAYER_STRIDE + 10, 829)
        persisted = json.loads(json.dumps(bindings))
        after = resolve_bindings(persisted, bytes(payload))
        self.assertEqual(before[1]['player_id'], after[1]['player_id'])
        self.assertEqual(after[1]['team'], '49ers')
        self.assertEqual(initial_profiles(persisted, bytes(payload)), profiles)
        self.assertEqual(original, bytes(self.fixture()))

    def test_guard_rejects_reused_slot_or_changed_biography(self):
        bindings = create_bindings(bytes(self.fixture()))
        for offset in (4, 0x19, 0x1B):
            payload = self.fixture(); payload[PLAYER_START + offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                resolve_bindings(bindings, bytes(payload))
        payload = self.fixture()
        # Swap player name pointers: never carry a profile by slot alone.
        for field in (0x10, 0x14):
            other = PLAYER_START + PLAYER_STRIDE + field
            target = other + struct.unpack_from('<i', payload, other)[0] - 1
            struct.pack_into('<i', payload, PLAYER_START + field, target - PLAYER_START - field + 1)
        with self.assertRaises(ValueError): resolve_bindings(bindings, bytes(payload))

    def test_new_members_or_year_advance_require_explicit_migration(self):
        bindings = create_bindings(bytes(self.fixture()))
        payload = self.fixture(); payload[0x917EF] += 1
        with self.assertRaises(ValueError): resolve_bindings(bindings, bytes(payload))
        # An old game-year byte must not conceal a real season advance.
        payload = self.fixture(); payload[0x91326] += 1
        with self.assertRaises(ValueError): resolve_bindings(bindings, bytes(payload))
        with self.assertRaises(ValueError): create_bindings(bytes(payload))
        payload = self.fixture(); struct.pack_into('<H', payload, 0x358, 0)
        with self.assertRaises(ValueError): resolve_bindings(bindings, bytes(payload))

    def test_duplicate_or_malformed_bindings_fail_closed(self):
        bindings = create_bindings(bytes(self.fixture()))
        for case in range(5):
            bad = copy.deepcopy(bindings)
            if case == 0: bad['players'][1]['player_id'] = bad['players'][0]['player_id']
            if case == 1: bad['players'][1]['source_slot'] = 0
            if case == 2: bad['players'][0]['source_slot'] = False
            if case == 3: bad['personality_seed'] = ''
            if case == 4: bad['baseline_year'] = '2026'
            with self.subTest(case=case), self.assertRaises(ValueError):
                resolve_bindings(bad, bytes(self.fixture()))

    def test_explicit_creation_never_overwrites_or_rerolls(self):
        with tempfile.TemporaryDirectory() as directory:
            save = Path(directory) / 'SAVEGAME.DAT'; save.write_bytes(self.fixture())
            registry = Path(directory) / 'bindings.json'
            with contextlib.redirect_stdout(io.StringIO()): main([str(save), str(registry), '--create'])
            before = registry.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()): main([str(save), str(registry)])
            self.assertEqual(registry.read_bytes(), before)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main([str(save), str(registry), '--create'])
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(registry.read_bytes(), before)
            self.assertEqual(save.read_bytes(), self.fixture())

    def test_signing_candidate_requires_all_guard_fields_and_never_authorizes(self):
        payload = bytes(self.fixture()); bindings = create_bindings(payload)
        observation = {'source_slot': 0, 'first_name': 'Synthetic', 'last_name': 'Starter',
                       'pbp_photo_raw': '00000000', 'dob_region_raw': '000000'}
        candidate = resolve_signing_candidate(bindings, payload, observation)
        self.assertEqual(candidate['candidate_player_id'], resolve_bindings(bindings, payload)[0]['player_id'])
        self.assertIn('unconfirmed', candidate['scope'])
        for field, value in (('source_slot', 1), ('source_slot', False), ('first_name', 'Other'),
                             ('pbp_photo_raw', '01000000'), ('dob_region_raw', '000001'), ('dob_region_raw', '')):
            bad = {**observation, field: value}
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                resolve_signing_candidate(bindings, payload, bad)
        incomplete = dict(observation); del incomplete['dob_region_raw']
        with self.assertRaises(ValueError): resolve_signing_candidate(bindings, payload, incomplete)
