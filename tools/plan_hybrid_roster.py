"""Read-only preseason membership plan over SOFTDRINK's native player records.

Never copy PS2 records, portrait IDs, ratings or contract words into the native
bank. Exact names plus decoded birth dates are provisional matching evidence,
not persistent identities. Missing/ambiguous players require explicit resolution.
Layout credit: BAD-AL/nfl2k5tool_dart, as pinned in inspect_franchise_save.
"""
import argparse
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import struct

from tools.inspect_franchise_save import PLAYER_STRIDE, TEAMS
from tools.inspect_roster_save import inspect_roster


def _players(payload, roster):
    result = []
    for team, members in [*roster['teams'].items(), ('free_agents', roster['free_agents']),
                          ('unassigned', roster.get('unassigned_players', []))]:
        for member in members:
            record = 0xAFA8 + member['source_slot'] * PLAYER_STRIDE
            month = payload[record+0x19] >> 4
            day = payload[record+0x1A] & 31
            year = (payload[record+0x1A] >> 5) | ((payload[record+0x1B] & 15) << 3)
            try:
                birthday = date(year + (1900 if year > 54 else 2000), month, day).isoformat()
            except ValueError:
                birthday = None
            result.append({**member, 'team': team, 'birth_date': birthday,
                           'native_photo_id': struct.unpack_from('<H', payload, record+6)[0]})
    return result


def plan_hybrid(native_payload, preseason_payload):
    native = inspect_roster(native_payload, include_unassigned=True)
    preseason = inspect_roster(preseason_payload)
    base = _players(native_payload, native)
    desired = _players(preseason_payload, preseason)
    def key(player):
        return player['first_name'].casefold(), player['last_name'].casefold()
    native_names, desired_names = defaultdict(list), defaultdict(list)
    for player in base:
        native_names[key(player)].append(player)
    for player in desired:
        desired_names[key(player)].append(player)
    matched, unresolved = [], []
    for player in desired:
        candidates = native_names[key(player)]
        if len(desired_names[key(player)]) != 1 or len(candidates) > 1:
            reason = 'ambiguous_name'
        elif not candidates:
            reason = 'missing_from_readable_native_bank'
        elif player['birth_date'] is None or candidates[0]['birth_date'] is None:
            reason = 'unknown_birth_date'
        elif candidates[0]['birth_date'] != player['birth_date']:
            reason = 'birth_date_conflict'
        else:
            original = candidates[0]
            matched.append({'first_name': player['first_name'], 'last_name': player['last_name'],
                            'birth_date': player['birth_date'],
                            'preseason_slot': player['source_slot'], 'native_slot': original['source_slot'],
                            'current_team': original['team'], 'desired_team': player['team'],
                            'preserve_native_photo_id': original['native_photo_id']})
            continue
        unresolved.append({'player': player, 'reason': reason, 'native_candidates': candidates})
    used = {player['native_slot'] for player in matched}
    return {'scope': 'read-only hybrid membership plan; no save or financial authority',
            'native_sha256': native['payload_sha256'], 'preseason_sha256': preseason['payload_sha256'],
            'matched': matched, 'unresolved': unresolved,
            'native_players_without_preseason_match': [p for p in base if p['source_slot'] not in used],
            'clubs': {team: {'desired': len(preseason['teams'][team]),
                             'matched': sum(p['desired_team'] == team for p in matched),
                             'unresolved': sum(p['player']['team'] == team for p in unresolved)} for team in TEAMS},
            'all_desired_members_matched': not unresolved,
            'matching_scope': 'native memberships plus readable unassigned bank; desired preseason memberships',
            'unreadable_native_unassigned_slots': native['unreadable_unassigned_slots'],
            'game_compatibility_verified': False, 'contracts_reconciled': False,
            'writes_performed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native_roster', type=Path)
    parser.add_argument('preseason_roster', type=Path)
    args = parser.parse_args()
    print(json.dumps(plan_hybrid(args.native_roster.read_bytes(), args.preseason_roster.read_bytes()), indent=2))


if __name__ == '__main__':
    main()
