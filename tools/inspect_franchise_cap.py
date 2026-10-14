"""Saved original first-year cap context; not modern accounting authority.

Report both accessor branches. The runtime caller still determines whether
the original team adjustment applies; no cash or guarantees are inferred.
"""
import argparse
import json
from pathlib import Path
import struct

from tools.inspect_franchise_calendar import inspect_calendar
from tools.inspect_franchise_save import TEAMS
from tools.reconcile_franchise_payroll import reconcile_payroll


def inspect_cap(payload: bytes) -> dict:
    calendar = inspect_calendar(payload)
    payroll = reconcile_payroll(payload)
    if not payroll['matched']:
        raise ValueError('Original roster payroll mismatch; cap context is unreconciled')
    scheduler = calendar['scheduler_offset']
    tail = scheduler + 0x83DC
    # 2D0790 writes global E3C278 at tail+15D0; 2D0CE0 restores it.
    cap = struct.unpack_from('<i', payload, tail + 0x15D0)[0] * 1000
    if cap <= 0:
        raise ValueError('Positive original league cap required')
    teams = {}
    for i, name in enumerate(TEAMS):
        # C5310/C5800 copy E5775C[i] via scheduler+AC+4*i.
        flag = struct.unpack_from('<I', payload, scheduler + 0xAC + 4*i)[0]
        accumulator = struct.unpack_from('<H', payload, 0x44A8 + i*0x1F4 + 0x19C)[0] * 1000
        # 13EC30 -> C4D50; 13ECA0 subtracts this only when the flag AND
        # the caller's adjustment argument are nonzero. First year only.
        adjusted = cap - (accumulator if flag else 0)
        total = payroll['teams'][name]['stored_payroll_dollars']
        teams[name] = {'original_team_flag_raw': flag,
                       'original_first_year_accumulator_dollars': accumulator,
                       'roster_payroll_dollars': total,
                       'room_without_team_adjustment_dollars': cap - total,
                       'room_if_team_adjustment_requested_dollars': adjusted - total}
    return {'scope': 'saved original first-year cap branches; no modern cap/cash/guarantee authority',
            'payload_sha256': calendar['payload_sha256'],
            'saved_display_year': calendar['display_year'],
            'league_cap_dollars': cap, 'teams': teams}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect_cap(args.save.read_bytes())
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
