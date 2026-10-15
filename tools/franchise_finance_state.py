"""Canonical saved financial state for comparison with the native addon snapshot.

Raw guest units only. This is not identity proof, complete modern books, an
atomic live read or an application permit. No ratings/names/addresses exported.
"""
import argparse
from pathlib import Path
import struct

from tools.inspect_franchise_save import inspect_save, PLAYER_START, PLAYER_STRIDE, TEAMS
from tools.inspect_franchise_calendar import inspect_calendar
from tools.inspect_franchise_cap import inspect_cap

HEADER_SIZE = 432
RECORD_SIZE = 11


def saved_finance_state(payload: bytes) -> bytes:
    roster = inspect_save(payload)
    calendar = inspect_calendar(payload)
    cap = inspect_cap(payload)  # Require reconciled saved roster payroll.
    count = roster['player_record_count']
    result = bytearray(HEADER_SIZE + RECORD_SIZE * count)
    struct.pack_into('<11I', result, 0, 1, count, calendar['table_mode'],
        cap['league_cap_dollars'] // 1000, calendar['phase_01_raw'], calendar['phase_02_raw'], 32,
        calendar['step_04_raw'], calendar['step_05_raw'], calendar['season_index'], calendar['counter_08_raw'])
    owners = [0xffffffff] * count
    for index, team in enumerate(TEAMS):
        observed = cap['teams'][team]
        struct.pack_into('<3I', result, 48 + 12 * index,
            observed['roster_payroll_dollars'] // 1000, observed['original_team_flag_raw'],
            observed['original_first_year_accumulator_dollars'] // 1000)
        for player in roster['teams'][team]:
            owners[player['source_slot']] = index
    for player in roster['free_agents']:
        owners[player['source_slot']] = 32
    for slot, owner in enumerate(owners):
        source = PLAYER_START + PLAYER_STRIDE * slot
        destination = HEADER_SIZE + RECORD_SIZE * slot
        result[destination:destination+7] = payload[source+8:source+9] + payload[source+10:source+12] + payload[source+36:source+40]
        struct.pack_into('<I', result, destination+7, owner)
    return bytes(result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('native_snapshot', type=Path, help='Used bytes of franchise.finance-state.v1 snapshot')
    args = parser.parse_args(argv)
    expected = saved_finance_state(args.save.read_bytes())
    if args.native_snapshot.read_bytes() != expected:
        parser.exit(1, 'Live financial state differs from the reconciled saved projection; signing must remain held.\n')
    print('Financial projection matches; identity, quiescence, authority and application remain unverified.')


if __name__ == '__main__':
    main()
