"""Authored transient membership only; no assets, inference or writes."""
import struct
import unittest

from tools.compare_live_franchise import compare
from tools.franchise_finance_state import saved_finance_state
from tools.franchise_identity_state import saved_identity_state
from tools.franchise_offer_state import saved_offer_screen_state
from test_franchise_finance_state import fixture


def capture(finance, identity):
    return b'2K5CAP1\0' + struct.pack('<2I', len(finance), len(identity)) + finance + identity


class OfferScreenStateTests(unittest.TestCase):
    def setUp(self):
        self.payload = fixture()

    def test_only_selected_free_agent_membership_and_identity_presence_change(self):
        finance, identity = saved_offer_screen_state(self.payload, 1)
        full = bytearray(saved_finance_state(self.payload))
        struct.pack_into('<I', full, 432 + 11 + 7, 0xffffffff)
        self.assertEqual(finance, bytes(full))
        original = saved_identity_state(self.payload)
        # Authored members are slots0,1,2; drop precisely the selected slot1.
        expected = struct.pack('<3I', 1, 2619, 2) + original[12:223] + original[434:]
        self.assertEqual(identity, expected)
        self.assertEqual(self.payload, fixture())
        result = compare(self.payload, capture(finance, identity))
        self.assertFalse(result['financial_match']); self.assertFalse(result['identity_match'])
        result = compare(self.payload, capture(finance, identity), pending_free_agent_slot=1)
        self.assertTrue(result['financial_match']); self.assertTrue(result['identity_match'])
        self.assertEqual(result['comparison_scope'], 'offer_screen_pending_free_agent')

    def test_wrong_candidate_other_changes_and_mixed_projection_pairs_reject(self):
        finance, identity = saved_offer_screen_state(self.payload, 1)
        wrong = compare(self.payload, capture(finance, identity), pending_free_agent_slot=2)
        self.assertFalse(wrong['financial_match']); self.assertFalse(wrong['identity_match'])
        for offset in (48, 432 + 2 * 11 + 1, 432 + 2618 * 11 + 3):
            changed = bytearray(finance); changed[offset] ^= 1
            result = compare(self.payload, capture(changed, identity), pending_free_agent_slot=1)
            self.assertFalse(result['financial_match'])
        changed = bytearray(identity); changed[16] ^= 1
        self.assertFalse(compare(self.payload, capture(finance, changed),
                                 pending_free_agent_slot=1)['identity_match'])
        for slot in (0, 2618, -1, 2619, True, '1'):
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                saved_offer_screen_state(self.payload, slot)
