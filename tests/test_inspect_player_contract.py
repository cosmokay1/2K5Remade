"""Authored fixtures validate observed contract readback, not modern rules."""
import contextlib
import io
from pathlib import Path
import struct
import tempfile
import unittest

import test_inspect_franchise_save as save_fixtures
from tools.inspect_franchise_save import PLAYER_START
from tools.inspect_player_contract import inspect_player_contract, main


class InspectPlayerContractTests(unittest.TestCase):
    def fixture(self):
        payload = save_fixtures.InspectFranchiseSaveTests().fixture()
        struct.pack_into('<H', payload, PLAYER_START + 0x0A, 829)
        struct.pack_into('<I', payload, PLAYER_START + 0x24, 0x02410BA2)
        return payload

    def test_observed_gildon_terms_and_unrelated_bits(self):
        payload = self.fixture(); before = bytes(payload)
        result = inspect_player_contract(before, 0)
        self.assertEqual(result['game_contract_total_dollars'], 8290000)
        self.assertEqual(result['game_bonus_percent'], 40)
        self.assertEqual(result['game_payment_style'], 'Descending')
        self.assertEqual((result['term_low_nibble_raw'], result['term_high_nibble_raw']), (2, 2))
        self.assertEqual(result['team'], '49ers')
        self.assertEqual(bytes(payload), before)
        self.assertNotIn('cap_charge', result)
        self.assertNotIn('guarantee', result)

    def test_unsupported_contracts_and_slots_do_not_invent_obligations(self):
        for word in (0, 0x00410BA2, 0x02410BA3, 0x02F10BA2, 0x02400BA2, 0x02470BA2):
            payload = self.fixture(); struct.pack_into('<I', payload, PLAYER_START + 0x24, word)
            with self.subTest(word=word), self.assertRaises(ValueError):
                inspect_player_contract(bytes(payload), 0)
        payload = bytes(self.fixture())
        for slot in (-1, True, 1.0, 2000):
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                inspect_player_contract(payload, slot)

    def test_balanced_and_read_only_cli(self):
        payload = self.fixture(); struct.pack_into('<I', payload, PLAYER_START + 0x24, 0x02420BA2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'SAVEGAME.DAT'; path.write_bytes(payload)
            with contextlib.redirect_stdout(io.StringIO()) as output:
                main([str(path), '0'])
            self.assertIn('Balanced', output.getvalue())
            self.assertEqual(path.read_bytes(), payload)
