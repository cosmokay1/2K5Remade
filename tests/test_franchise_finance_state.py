"""Authored saves and relocated memory only; no game assets or write grants."""
import struct
import unittest

from tools.franchise_finance_state import saved_finance_state, HEADER_SIZE, RECORD_SIZE
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE, inspect_save
from tools.inspect_franchise_calendar import inspect_calendar
import test_legacy_contracts as fixtures


def fixture():
    payload = fixtures.LegacyContractsTests().fixture()
    # Expanded bank, second free agent and a non-rostered last bank slot.
    count = 2619
    struct.pack_into('<I', payload, 0x320, count)
    struct.pack_into('<i', payload, 0x32C, PLAYER_START + count*PLAYER_STRIDE - 0x32C + 1)
    old, new = PLAYER_START + PLAYER_STRIDE, PLAYER_START + 2*PLAYER_STRIDE
    payload[new:new+PLAYER_STRIDE] = payload[old:old+PLAYER_STRIDE]
    for field in (0x10, 0x14):
        target = old + field + struct.unpack_from('<i', payload, old+field)[0] - 1
        struct.pack_into('<i', payload, new+field, target-new-field+1)
    struct.pack_into('<H', payload, 0x358, 2)
    table = 0x35C + struct.unpack_from('<i', payload, 0x35C)[0] - 1
    struct.pack_into('<i', payload, table+4, new-(table+4)+1)
    return bytes(payload)


def live_fixture(payload, relocation=0):
    """Load authored saved semantics into a different, absolute-pointer layout."""
    roster = inspect_save(payload)
    calendar = inspect_calendar(payload)
    count = roster['player_record_count']
    bank, base, teams, free = (0x10000+relocation, 0x200000+relocation,
                                0x80000+relocation, 0xA0000+relocation)
    result = bytearray(0xE58000)
    def word(offset, value):
        struct.pack_into('<I', result, offset, value)
    word(0xB72918, bank)
    word(bank, count); word(bank+4, base)
    result[base:base+count*PLAYER_STRIDE] = payload[PLAYER_START:PLAYER_START+count*PLAYER_STRIDE]
    word(bank+0x38, len(roster['free_agents'])); word(bank+0x3C, free)
    for i, player in enumerate(roster['free_agents']):
        word(free+4*i, base+player['source_slot']*PLAYER_STRIDE)
    for i, players in enumerate(roster['teams'].values()):
        team = teams+i*0x1F4
        word(0xE5786C+4*i, team)
        result[team:team+0x1F4] = payload[0x44A8+i*0x1F4:0x44A8+(i+1)*0x1F4]
        for j, player in enumerate(players):
            word(team+4*j, base+player['source_slot']*PLAYER_STRIDE)
        word(0xE5775C+4*i, struct.unpack_from('<I', payload, calendar['scheduler_offset']+0xAC+4*i)[0])
    word(0xE576A0, 2)
    for i, value in enumerate((calendar['phase_01_raw'], calendar['phase_02_raw'], 32,
            calendar['step_04_raw'], calendar['step_05_raw'], calendar['season_index'], calendar['counter_08_raw'])):
        word(0xE576A4+4*i, value)
    word(0xE3C278, struct.unpack_from('<I', payload, calendar['scheduler_offset']+0x83DC+0x15D0)[0])
    return result


class FranchiseFinanceStateTests(unittest.TestCase):
    def test_projection_covers_entire_bank_membership_and_raw_finances(self):
        payload = fixture(); state = saved_finance_state(payload)
        self.assertEqual(len(state), HEADER_SIZE+2619*RECORD_SIZE)
        self.assertEqual(struct.unpack_from('<4I', state), (1, 2619, 2, 80500))
        owners = [struct.unpack_from('<I', state, HEADER_SIZE+i*RECORD_SIZE+7)[0] for i in (0, 1, 2, 2618)]
        self.assertEqual(owners, [0, 32, 32, 0xffffffff])
        self.assertEqual(struct.unpack_from('<3I', state, 48), (4766, 0, 0))
        self.assertEqual(payload, fixture())

    def test_pointer_values_and_free_agent_order_are_not_semantic_changes(self):
        payload = bytearray(fixture()); expected = saved_finance_state(bytes(payload))
        table = 0x35C+struct.unpack_from('<i', payload, 0x35C)[0]-1
        for index, slot in enumerate((2, 1)):
            struct.pack_into('<i', payload, table+index*4, PLAYER_START+slot*PLAYER_STRIDE-(table+index*4)+1)
        self.assertEqual(saved_finance_state(bytes(payload)), expected)

    def test_unbound_contract_and_real_financial_changes_are_not_ignored(self):
        payload = fixture(); expected = saved_finance_state(payload)
        for location, fmt, value in ((PLAYER_START+2618*PLAYER_STRIDE+10, '<H', 829),
                (PLAYER_START+2618*PLAYER_STRIDE+36, '<I', 2),
                (PLAYER_START+8, '<B', 8), (0x91320+0xAC+31*4, '<I', 1),
                (0x44A8+31*0x1F4+0x19C, '<H', 1), (0x91326, '<B', 23)):
            changed = bytearray(payload); struct.pack_into(fmt, changed, location, value)
            with self.subTest(location=location):
                self.assertNotEqual(saved_finance_state(bytes(changed)), expected)

    def test_unreconciled_saved_payroll_is_not_an_expected_projection(self):
        payload = bytearray(fixture()); struct.pack_into('<I', payload, 0x44A8+0x124, 9999)
        with self.assertRaisesRegex(ValueError, 'payroll mismatch'):
            saved_finance_state(bytes(payload))
