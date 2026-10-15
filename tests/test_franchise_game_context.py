"""One explicit intake path, with lossless old-registry recovery conversion."""
import contextlib
import copy
import hashlib
import io
import json
import struct
import tempfile
import unittest
from pathlib import Path

from tools.franchise_game_context import raw_context
from tools.franchise_snapshot_bindings import (create_bindings, resolve_bindings, initial_profiles,
    migrate_context, main, LEGACY_VERSION, SOFTDRINK_PROFILE, SOFTDRINK_XBE_SHA256)
from tools.export_legacy_contracts import legacy_contracts
import test_legacy_contracts as fixtures


class GameContextTests(unittest.TestCase):
    def setUp(self):
        self.payload = bytes(fixtures.LegacyContractsTests().fixture())

    def legacy(self, bindings):
        old = copy.deepcopy(bindings)
        old.pop('game_context'); old['version'] = LEGACY_VERSION
        return old

    def test_executable_identity_never_selects_calendar_or_units(self):
        for image in (b'authored original-like image', b'authored SOFTDRINK-like image'):
            for scale in (1, 4):
                context = {**raw_context(self.payload), 'money_scale': scale}
                binding = create_bindings(self.payload, game_xbe=image, game_context=context)
                self.assertNotIn('game_profile', binding)
                self.assertEqual(binding['game_context']['money_scale'], scale)
                self.assertEqual(binding['game_context']['source_image_sha256'], hashlib.sha256(image).hexdigest())
                self.assertEqual(legacy_contracts(binding, self.payload)['49ers'][0].charges(),
                                 (4766000 * scale, 3523000 * scale))
                resolve_bindings(json.loads(json.dumps(binding)), self.payload)
        # Provenance alone leaves the measured/raw context's default units intact.
        self.assertEqual(create_bindings(self.payload, game_xbe=b'any image')['game_context']['money_scale'], 1)

    def test_calendar_mapping_uses_explicit_data_for_any_image(self):
        payload = bytearray(self.payload); payload[0x91326] = 0
        context = {**raw_context(bytes(payload)), 'season_year': 2026}
        for image in (b'first authored image', b'second authored image'):
            binding = create_bindings(bytes(payload), game_xbe=image, game_context=context)
            self.assertEqual(binding['baseline_year'], 2026)
            self.assertEqual(binding['game_context']['season_index'], 0)
            resolve_bindings(binding, bytes(payload))
        with self.assertRaises(ValueError): create_bindings(bytes(payload))

    def test_invalid_context_and_changed_saved_context_reject(self):
        context = raw_context(self.payload)
        for key, value in (('money_scale', True), ('money_scale', 2), ('season_index', False),
                           ('season_index', 256), ('season_year', '2026'), ('season_year', 1999),
                           ('league_cap_raw', True), ('league_cap_raw', None),
                           ('league_cap_raw', 0), ('source_image_sha256', 'G' * 64)):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                create_bindings(self.payload, game_context={**context, key: value})
        with self.assertRaises(ValueError):
            create_bindings(self.payload, game_xbe=b'one',
                game_context={**context, 'source_image_sha256': hashlib.sha256(b'other').hexdigest()})
        binding = create_bindings(self.payload)
        for offset in (0x91326, 0x917EF, 0x91320 + 0x83DC + 0x15D0):
            changed = bytearray(self.payload); changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError): resolve_bindings(binding, bytes(changed))

    def check_migration(self, old, payload):
        original = json.dumps(old, sort_keys=True); before = bytes(payload)
        migrated = migrate_context(old, payload)
        for key in ('franchise_id', 'players', 'personality_seed', 'baseline_year', 'baseline_payload_sha256'):
            self.assertEqual(migrated[key], old[key])
        self.assertEqual(initial_profiles(migrated, payload), initial_profiles(old, payload))
        self.assertEqual(legacy_contracts(migrated, payload), legacy_contracts(old, payload))
        self.assertEqual(resolve_bindings(migrated, payload), resolve_bindings(old, payload))
        self.assertEqual(json.dumps(old, sort_keys=True), original)
        self.assertEqual(bytes(payload), before)
        self.assertEqual(migrate_context(migrated, payload), migrated)
        return migrated

    def test_old_plain_registry_migrates_without_identity_or_contract_changes(self):
        old = self.legacy(create_bindings(self.payload, seed='preserved actors'))
        migrated = self.check_migration(old, self.payload)
        self.assertEqual(migrated['game_context']['money_scale'], 1)

    def test_historical_named_registry_remains_readable_and_migrates_once(self):
        payload = bytearray(self.payload); payload[0x91326] = 0
        struct.pack_into('<i', payload, 0x91320 + 0x83DC + 0x15D0, 75300)
        context = {**raw_context(bytes(payload)), 'season_year': 2026, 'money_scale': 4}
        old = self.legacy(create_bindings(bytes(payload), seed='preserved actors', game_context=context))
        old['game_profile'] = {'id': SOFTDRINK_PROFILE, 'xbe_sha256': SOFTDRINK_XBE_SHA256}
        migrated = self.check_migration(old, bytes(payload))
        self.assertNotIn('game_profile', migrated)
        self.assertEqual(migrated['game_context'], {**context, 'source_image_sha256': SOFTDRINK_XBE_SHA256})
        old['game_profile']['xbe_sha256'] = '0' * 64
        with self.assertRaises(ValueError): migrate_context(old, bytes(payload))

    def test_mixed_schema_never_overrides_context(self):
        binding = create_bindings(self.payload)
        binding['game_profile'] = {'id': SOFTDRINK_PROFILE, 'xbe_sha256': SOFTDRINK_XBE_SHA256}
        with self.assertRaises(ValueError): resolve_bindings(binding, self.payload)
        binding.pop('game_profile'); binding['version'] = LEGACY_VERSION
        with self.assertRaises(ValueError): resolve_bindings(binding, self.payload)

    def test_cli_creation_and_copy_migration_never_overwrite_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); save = root/'SAVEGAME.DAT'; save.write_bytes(self.payload)
            context = root/'context.json'; context.write_text(json.dumps(raw_context(self.payload)))
            image = root/'authored-image'; image.write_bytes(b'not a game asset')
            registry = root/'new.json'
            with contextlib.redirect_stdout(io.StringIO()):
                main([str(save), str(registry), '--create', '--game-context', str(context), '--game-xbe', str(image)])
            created = json.loads(registry.read_text()); old = self.legacy(created)
            legacy = root/'old.json'; legacy.write_text(json.dumps(old))
            original = legacy.read_bytes(); converted = root/'converted.json'
            with contextlib.redirect_stdout(io.StringIO()):
                main([str(save), str(legacy), '--migrate-context', str(converted)])
            self.assertEqual(json.loads(converted.read_text()), migrate_context(old, self.payload))
            self.assertEqual(legacy.read_bytes(), original); self.assertEqual(save.read_bytes(), self.payload)
            published = converted.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main([str(save), str(legacy), '--migrate-context', str(converted)])
            self.assertEqual(converted.read_bytes(), published); self.assertEqual(legacy.read_bytes(), original)
