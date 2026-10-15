"""Identity samples bind roster actors, without ratings or guest write authority."""
import struct
import unittest

from tools.franchise_identity_state import saved_identity_state, HEADER_SIZE, RECORD_SIZE
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE, STRING_END
import test_franchise_finance_state as authored


def rename(payload, slot, first, last):
    result = bytearray(payload); cursor = STRING_END-0x200
    for offset, name in ((0x10, first), (0x14, last)):
        location = PLAYER_START+slot*PLAYER_STRIDE+offset
        struct.pack_into('<i', result, location, cursor-location+1)
        encoded = (name+'\0').encode('utf-16le')
        result[cursor:cursor+len(encoded)] = encoded; cursor += len(encoded)
    return bytes(result)


class FranchiseIdentityStateTests(unittest.TestCase):
    def test_all_rostered_and_free_agent_guards_are_ordered_by_bank_slot(self):
        payload = authored.fixture(); state = saved_identity_state(payload)
        self.assertEqual(struct.unpack_from('<3I', state), (1, 2619, 3))
        self.assertEqual(len(state), HEADER_SIZE+3*RECORD_SIZE)
        self.assertEqual([struct.unpack_from('<I', state, HEADER_SIZE+i*RECORD_SIZE)[0] for i in range(3)], [0, 1, 2])
        self.assertEqual(state[23:123], 'Synthetic'.encode('utf-16le').ljust(100, b'\0'))
        self.assertEqual(payload, authored.fixture())

    def test_all_bound_photo_and_dob_guards_affect_the_sample(self):
        payload = authored.fixture(); original = saved_identity_state(payload)
        for slot in (0, 1, 2):
            for field in (4, 5, 6, 7, 0x19, 0x1A, 0x1B):
                changed = bytearray(payload); changed[PLAYER_START+slot*PLAYER_STRIDE+field] ^= 1
                with self.subTest(slot=slot, field=field):
                    self.assertNotEqual(saved_identity_state(bytes(changed)), original)
        self.assertNotEqual(saved_identity_state(rename(payload, 0, 'Another', 'Player')), original)

    def test_pointer_relocation_order_and_unrostered_biographies_are_excluded(self):
        payload = authored.fixture(); original = saved_identity_state(payload)
        self.assertEqual(saved_identity_state(rename(payload, 0, 'Synthetic', 'Starter')), original)
        changed = bytearray(payload)
        table = 0x35C+struct.unpack_from('<i', changed, 0x35C)[0]-1
        for index, slot in enumerate((2, 1)):
            struct.pack_into('<i', changed, table+index*4, PLAYER_START+slot*PLAYER_STRIDE-(table+index*4)+1)
        changed[PLAYER_START+2618*PLAYER_STRIDE+4] = 0xff
        struct.pack_into('<I', changed, PLAYER_START+2618*PLAYER_STRIDE+0x10, 0xffffffff)
        self.assertEqual(saved_identity_state(bytes(changed)), original)

    def test_unicode_surrogate_pairs_and_maximum_bounded_names_are_preserved(self):
        for first, last in (('É😀"\\', "O'Neal"), ('a'*49, 'b'*49)):
            with self.subTest(first=first):
                state = saved_identity_state(rename(authored.fixture(), 0, first, last))
                self.assertEqual(state[23:123], first.encode('utf-16le').ljust(100, b'\0'))
                self.assertEqual(state[123:223], last.encode('utf-16le').ljust(100, b'\0'))
        with self.assertRaises(ValueError):
            saved_identity_state(rename(authored.fixture(), 0, 'a'*50, 'Last'))
