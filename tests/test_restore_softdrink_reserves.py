"""Authored sparse overlays exercise the real range replacement without assets."""
import struct
import unittest
import copy
import json
from pathlib import Path
import sys
import zipfile

from tools.restore_softdrink_reserves import EXTENT, RECIPE_ENTRY, patch_index, replace_extents, restore


class ReserveOverlayTests(unittest.TestCase):
    def render(self, extents, literal):
        out = bytearray(b'.' * 40)
        sources = {0: b'abcdefghijklmnopqrstuvwxyz0123456789ABCD'}
        for dst, size, kind, source, offset in EXTENT.iter_unpack(extents):
            value = literal if kind == 0 else sources[source]
            out[dst:dst+size] = value[offset:offset+size]
        return bytes(out)

    def test_clipped_copy_and_literal_preserve_both_boundaries(self):
        original = EXTENT.pack(2, 12, 1, 0, 3) + EXTENT.pack(16, 18, 0, 65535, 0)
        literal = b'ABCDEFGHIJKLMNOPQR' + b'xxxxxxxxxxxx'
        changed = replace_extents(original, 10, 12, 18)
        before, after = self.render(original, literal), self.render(changed, literal)
        self.assertEqual(after, before[:10] + b'x' * 12 + before[22:])

    def test_sparse_gap_before_between_and_after_existing_extents(self):
        original = EXTENT.pack(8, 4, 1, 0, 0) + EXTENT.pack(24, 4, 1, 0, 4)
        for start in (0, 14, 34):
            with self.subTest(start=start):
                result = replace_extents(original, start, 3, 0)
                before = self.render(original, b'xyz')
                self.assertEqual(self.render(result, b'xyz'), before[:start]+b'xyz'+before[start+3:])

    def test_bad_tables_refused(self):
        for data in (b'bad', EXTENT.pack(2, 0, 1, 0, 0),
                     EXTENT.pack(5, 8, 1, 0, 0)+EXTENT.pack(6, 3, 1, 0, 0)):
            with self.subTest(data=data), self.assertRaises(ValueError):
                replace_extents(data, 1, 2, 0)

    def test_only_selected_volume_table_changes(self):
        names = [b'default.xbe', b'vc_53450030/0']
        header = b'2K5OVL1\0' + struct.pack('<II', 2, 2)
        for name in names:
            header += struct.pack('<H', len(name))+name+struct.pack('<QQ', 40, 40)
        untouched = struct.pack('<II', 0, 1)+EXTENT.pack(0, 40, 1, 0, 0)
        selected = struct.pack('<II', 1, 1)+EXTENT.pack(0, 40, 1, 1, 0)
        result, index = patch_index(header+untouched+selected, 9, b'new', 50)
        self.assertEqual(index, 1)
        self.assertEqual(result[:len(header+untouched)], header+untouched)
        fields = list(EXTENT.iter_unpack(result[len(header+untouched)+8:]))
        self.assertEqual(fields, [(0,9,1,1,0),(9,3,0,65535,50),(12,28,1,1,12)])


class PrivateStockReserveTests(unittest.TestCase):
    """Optional real-format checks; private user assets are never test fixtures."""
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1] / '.local-runtime/softdrink-v0.6.1'
        patch = root / 'SOFTDRINK-2K28-v0.6.1.2k5patch'
        if not patch.exists() or not (root / 'codec').exists():
            raise unittest.SkipTest('Private stock pack/official codec not installed')
        sys.path.insert(0, str(root / 'codec'))
        from mod_editor.core import nfl2k5_roster_records, nfl2k5_practice_squad
        cls.records, cls.squads = nfl2k5_roster_records, nfl2k5_practice_squad
        cls.payload = (root / 'default-roster-resource.bin').read_bytes()
        with zipfile.ZipFile(patch) as archive:
            cls.recipe = json.loads(archive.read(RECIPE_ENTRY))

    def test_all_clubs_and_exact_existing_record_preservation(self):
        result, receipt = restore(self.payload, self.recipe, self.records, self.squads)
        self.assertEqual(len(receipt['restored']), 81)
        self.assertEqual(len({p['team'] for p in receipt['restored']}), 32)
        self.assertTrue(receipt['restored_to_active_rosters'])
        old = self.records.RosterDocument(self.payload, base=32, reference_year=2026)
        new = self.records.RosterDocument(result, base=32, reference_year=2026)
        for p in old.players:
            self.assertEqual(self.payload[p.offset:p.offset+84], result[p.offset:p.offset+84])
        for a, b in zip(old.teams, new.teams):
            self.assertEqual(a.slots, b.slots[:len(a.slots)])
            self.assertEqual(old.reserves[a.index], new.reserves[a.index])
            self.assertLessEqual(len(b.slots) + len(new.reserves[b.index]), 65)
            if a.index >= 32:
                self.assertEqual(a.slots, b.slots)
        self.assertEqual(old.free_agents, new.free_agents)
        for index in (987, 958):  # Dart/Burns must be selectable, not hidden reserves.
            self.assertNotIn(('primary', index), new.reserve_owner)
            self.assertIn(new.primary_table + index * 84, new.teams[15].slots)
        self.assertEqual(len(new.teams[15].slots), 56)
        self.assertEqual(sum(len(t.slots) for t in new.teams[:32]) -
                         sum(len(t.slots) for t in old.teams[:32]), 81)

    def test_mismatched_identity_and_duplicate_source_refused(self):
        for mode in ('name', 'duplicate'):
            recipe = copy.deepcopy(self.recipe)
            row = next(p for p in recipe['roster_refresh']['players'] if p['status'] == 'RES')
            if mode == 'name':
                row['last'] = 'Different identity'
            else:
                recipe['roster_refresh']['players'].append(copy.deepcopy(row))
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                restore(self.payload, recipe, self.records, self.squads)

    def test_nonstock_roster_refused(self):
        data = bytearray(self.payload)
        data[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'unmodified'):
            restore(bytes(data), self.recipe, self.records, self.squads)


if __name__ == '__main__':
    unittest.main()
