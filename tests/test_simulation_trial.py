import hmac
from pathlib import Path
import struct
import tempfile
import unittest
from tests.test_inspect_franchise_calendar import CalendarTests
from tools.prepare_simulation_trial import patch_simulated_minutes, prepare_trial


class SimulationTrialTests(unittest.TestCase):
    def payload(self):
        b=CalendarTests().fixture()
        struct.pack_into('<2I', b, 0x8c, 8, 5)
        return bytes(b)

    def test_only_simulation_word_changes(self):
        before=self.payload();after=patch_simulated_minutes(before, 6)
        self.assertEqual(before[:0x90], after[:0x90])
        self.assertEqual(before[0x94:], after[0x94:])
        self.assertEqual(struct.unpack_from('<2I', after, 0x8c), (8,6))
        for invalid in (True, 2, 16, 5.5):
            with self.assertRaises(ValueError):patch_simulated_minutes(before, invalid)

    def test_signed_copy_and_source_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source';src.mkdir();dst=Path(d)/'trial'
            data=self.payload();sig=hmac.digest(bytes(16),data,'sha1')
            (src/'SAVEGAME.DAT').write_bytes(data);(src/'EXTRA').write_bytes(sig)
            result=prepare_trial(src,dst,7)
            self.assertTrue(result['signature_verified'])
            self.assertEqual((src/'SAVEGAME.DAT').read_bytes(),data)
            self.assertEqual((src/'EXTRA').read_bytes(),sig)
            with self.assertRaises(ValueError):prepare_trial(src,src,6)
            with self.assertRaises(ValueError):prepare_trial(src,dst,6)

    def test_bad_signature_leaves_no_trial(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source';src.mkdir();dst=Path(d)/'trial'
            (src/'SAVEGAME.DAT').write_bytes(self.payload());(src/'EXTRA').write_bytes(bytes(20))
            with self.assertRaises(ValueError):prepare_trial(src,dst,6)
            self.assertFalse(dst.exists())
