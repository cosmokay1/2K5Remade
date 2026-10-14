"""Read-only original payroll reconciliation; never authorize modern cap writes.

Compares supported roster contract charges with saved team+0x124 totals. Extra
mode-specific obligations are not guessed: any difference prevents a match.
"""
import argparse
import json
from pathlib import Path
import struct

from tools.inspect_franchise_save import inspect_save, PLAYER_START, PLAYER_STRIDE, TEAMS
from tools.inspect_player_contract import original_annual_rows


def reconcile_payroll(payload: bytes) -> dict:
    roster = inspect_save(payload)
    teams = {}
    for index, name in enumerate(TEAMS):
        charges = []
        inactive = 0
        for player in roster['teams'][name]:
            offset = PLAYER_START + player['source_slot'] * PLAYER_STRIDE
            amount = struct.unpack_from('<H', payload, offset + 0x0A)[0]
            packed = struct.unpack_from('<I', payload, offset + 0x24)[0]
            remaining, original = packed & 15, (packed >> 24) & 15
            if remaining == 0:
                # C3F00 skips this record; this says nothing about retained debt.
                inactive += 1
                continue
            if remaining > original:
                raise ValueError('Remaining contract term exceeds original term')
            rows = original_annual_rows(amount, (packed >> 20) & 15, (packed >> 16) & 15, original)
            row = rows[original - remaining]
            charges.append({'source_slot': player['source_slot'],
                            'contract_year_index_from_term_fields': original - remaining,
                            'original_game_charge_dollars': row['original_game_charge_dollars']})
        reconstructed = sum(row['original_game_charge_dollars'] for row in charges)
        stored = struct.unpack_from('<I', payload, 0x44A8 + index * 0x1F4 + 0x124)[0] * 1000
        teams[name] = {'stored_payroll_dollars': stored,
                       'reconstructed_roster_payroll_dollars': reconstructed,
                       'difference_dollars': stored - reconstructed,
                       'matched': stored == reconstructed,
                       'inactive_roster_records': inactive, 'charges': charges}
    return {'scope': 'original-game roster payroll reconciliation; not modern cap or cash authorization',
            'payload_sha256': roster['payload_sha256'],
            'source_slot_semantics': roster['source_slot_semantics'],
            'matched': all(team['matched'] for team in teams.values()), 'teams': teams}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    args = parser.parse_args(argv)
    try:
        report = reconcile_payroll(args.save.read_bytes())
    except (ValueError, OSError) as exc:
        parser.exit(2, f'reconcile_franchise_payroll: {exc}\n')
    print(json.dumps(report, indent=2))
    if not report['matched']:
        parser.exit(3, 'Original roster payroll does not reconcile; import must remain blocked\n')


if __name__ == '__main__':
    main()
