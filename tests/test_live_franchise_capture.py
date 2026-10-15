import struct
import unittest

from tools.compare_live_franchise import compare, read_capture
from tools.franchise_finance_state import saved_finance_state
from tools.franchise_identity_state import saved_identity_state
from test_franchise_finance_state import fixture


class LiveCaptureTests(unittest.TestCase):
    def setUp(self):
        self.payload = fixture()
        self.finance = saved_finance_state(self.payload)
        self.identity = saved_identity_state(self.payload)
        self.capture = b'2K5CAP1\0' + struct.pack('<2I', len(self.finance), len(self.identity)) + self.finance + self.identity

    def test_exact_saved_projections_and_independent_mismatches(self):
        result = compare(self.payload, self.capture)
        self.assertTrue(result['financial_match'])
        self.assertTrue(result['identity_match'])
        changed = bytearray(self.capture); changed[16+48] ^= 1
        result = compare(self.payload, bytes(changed))
        self.assertFalse(result['financial_match']); self.assertTrue(result['identity_match'])
        changed = bytearray(self.capture); changed[16+len(self.finance)+16] ^= 1
        result = compare(self.payload, bytes(changed))
        self.assertTrue(result['financial_match']); self.assertFalse(result['identity_match'])

    def test_partial_trailing_oversized_and_inconsistent_captures_are_refused(self):
        for data in (b'', self.capture[:15], self.capture[:-1], self.capture+b'\0',
                     b'wrongtag'+self.capture[8:]):
            with self.subTest(size=len(data)), self.assertRaises(ValueError): read_capture(data)
        for offset, value in ((8, 0xffffffff), (12, 0), (16, 2), (20, 0),
                              (16+len(self.finance), 2), (20+len(self.finance), 2618),
                              (24+len(self.finance), 2620)):
            data = bytearray(self.capture); struct.pack_into('<I', data, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError): read_capture(bytes(data))
