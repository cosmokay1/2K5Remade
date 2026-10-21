"""Resolve cross-mod player names against a pinned Week 1 NFL identity table.

Aliases come only from that player's full/legal/football names. Suffix and
punctuation normalization never overrides a birthday conflict or ambiguity.
No roster, image, contract or cap writes are performed.
"""
from collections import defaultdict
from datetime import date
import re
import struct
import unicodedata

from tools.inspect_roster_save import inspect_roster
from tools.plan_hybrid_roster import _players


def normalize_name(name):
    words = re.sub(r'[^a-z0-9 ]', '', unicodedata.normalize('NFKD', name)
                   .encode('ascii', 'ignore').decode().casefold()).split()
    while words and words[-1] in ('jr', 'sr', 'ii', 'iii', 'iv', 'v'):
        words.pop()
    return ''.join(words)


def resolve_week1(native_payload, source_payload, weekly_rows, *, season_year,
                  allow_biography_corrections=False, historical_identity_rows=(),
                  allow_profile_corroboration=False, include_source_free_agents=True):
    if type(season_year) is not int:
        raise ValueError('Explicit integer season year required')
    identities, aliases = {}, defaultdict(set)
    selected = [(row, False) for row in historical_identity_rows
                if str(row.get('season', '')).isdigit() and int(row['season']) < season_year]
    selected += [(row, True) for row in weekly_rows if
                 str(row.get('season')) == str(season_year) and str(row.get('week')) == '1'
                 and row.get('game_type') == 'REG']
    current_ids = {row['gsis_id'] for row, current in selected
                   if current and row.get('gsis_id') and row.get('birth_date')}
    historical_birthdays = defaultdict(set)
    for row, current in selected:
        if not current and row.get('gsis_id') and row.get('birth_date'):
            historical_birthdays[row['gsis_id']].add(row['birth_date'])
    excluded_historical_ids = sorted(gsis for gsis, birthdays in historical_birthdays.items()
                                     if len(birthdays) != 1)
    selected = [(row, current) for row, current in selected if current or
                row.get('gsis_id') not in current_ids and row.get('gsis_id') not in excluded_historical_ids]
    for row, current in selected:
        gsis, birthday = row.get('gsis_id'), row.get('birth_date')
        if not gsis or not birthday:
            continue
        date.fromisoformat(birthday)
        if gsis in identities and identities[gsis]['birth_date'] != birthday:
            raise ValueError('Week 1 identity has conflicting birth dates')
        identities.setdefault(gsis, {'birth_date': birthday, 'names': set(), 'statuses': set(),
                                    'physical': set(), 'colleges': set(), 'jerseys': set(), 'last_names': set(), 'evidence_seasons': set()})
        identity = identities[gsis]
        identity['evidence_seasons'].add(int(row['season']))
        if current:
            identity['statuses'].add((row.get('team', ''), row.get('status', '')))
        identity['last_names'].add(normalize_name(row.get('last_name', '')))
        if current and str(row.get('jersey_number','')).isdigit():
            identity['jerseys'].add(int(row['jersey_number']))
        identity['colleges'].update(normalize_name(c) for c in (row.get('college') or '').split(';') if c.strip())
        try:
            identity['physical'].add((int(row['height']), int(row['weight']), row['position']))
        except (KeyError, ValueError, TypeError):
            pass
        last = row.get('last_name', '')
        names = (row.get('full_name', ''), row.get('first_name', '')+' '+last,
                 row.get('football_name', '')+' '+last)
        for name in names:
            if normalize_name(name) and (name == row.get('full_name') or last and name.strip() != last):
                aliases[normalize_name(name)].add(gsis)
                identity['names'].add(name.strip())
    if not current_ids or not identities:
        raise ValueError('No supported Week 1 identities in the supplied table')

    positions = {'QB': {0}, 'K': {1}, 'P': {2}, 'WR': {3}, 'DB': {4,5,6}, 'CB': {4},
                 'S': {5,6}, 'FS': {5}, 'SS': {6}, 'RB': {7}, 'FB': {8}, 'TE': {9},
                 'LB': {10,11}, 'OLB': {10}, 'ILB': {11}, 'OL': {12,13,14},
                 'C': {12}, 'G': {13}, 'T': {14}, 'DL': {15,16}, 'DT': {15},
                 'DE': {16}, 'EDGE': {10,16}, 'LS': {12}}

    def physical_matches(payload, player, identity):
        at = 0xAFA8 + player['source_slot']*0x54
        return any(payload[at+0x2B] == height and abs(payload[at+0x2A]+150-weight) <= 5
                   and payload[at+0x35] in positions.get(position, set())
                   for height, weight, position in identity['physical'])

    def profile_corroborates(payload, player, identity, *, require_college=False):
        # A wrong roster DOB needs independent evidence beyond a unique name.
        # College or a current jersey/year match, plus position and bounded physical
        # variation, provide corroboration. Every alternate method stays labeled.
        at = 0xAFA8 + player['source_slot']*0x54
        plausible = any(abs(payload[at+0x2B]-height) <= 2
                   and abs(payload[at+0x2A]+150-weight) <= 35
                   and payload[at+0x35] in (positions.get(position,set()) | ({16} if position=='LB' else set()))
                   for height,weight,position in identity['physical'])
        if not plausible:
            return False
        jersey = (struct.unpack_from('<I',payload,at+0x20)[0]>>3)&127
        if (not require_college and jersey in identity['jerseys'] and player['birth_date']
                and abs(date.fromisoformat(player['birth_date']).year-date.fromisoformat(identity['birth_date']).year)<=1):
            return True
        entry = at+struct.unpack_from('<i',payload,at)[0]-1
        table = 0x64+struct.unpack_from('<i',payload,0x64)[0]-1
        count = struct.unpack_from('<I',payload,0x60)[0]
        if (not 0 < count <= 400 or not 0 <= table <= len(payload)-count*8
                or not table <= entry < table+count*8 or (entry-table)%8):
            return False
        start = entry+struct.unpack_from('<i',payload,entry)[0]-1
        if not 0x75960 <= start < len(payload)-2 or start%2:
            return False
        end = start
        while end+2 <= len(payload) and end-start < 160 and payload[end:end+2] != b'\0\0':
            end += 2
        if end-start >= 160 or end+2 > len(payload):
            return False
        try:
            college = normalize_name(payload[start:end].decode('utf-16le'))
        except UnicodeDecodeError:
            return False
        if not college or college not in identity['colleges']:
            return False
        return True

    def resolve(payload, *, include_unassigned):
        roster = inspect_roster(payload, include_unassigned=include_unassigned)
        matched, unresolved = {}, []
        for player in _players(payload, roster):
            if not include_unassigned and not include_source_free_agents and player['team']=='free_agents':
                continue
            candidates = aliases[normalize_name(player['first_name']+' '+player['last_name'])]
            exact = sorted(gsis for gsis in candidates
                           if identities[gsis]['birth_date'] == player['birth_date'])
            method = 'sourced_name_and_birth_date'
            if not exact and allow_biography_corrections:
                # A unique authoritative name plus independent position/height/
                # weight evidence can identify a possible roster DOB error.
                # The original record is never rewritten by this resolver.
                if len(candidates) == 1:
                    exact = [gsis for gsis in candidates if physical_matches(payload, player, identities[gsis])]
                    method = 'unique_sourced_name_and_physical_profile'
                    if not exact and allow_profile_corroboration:
                        exact = [gsis for gsis in candidates if profile_corroborates(payload,player,identities[gsis])]
                        method = 'unique_sourced_name_corroborated_profile'
                elif not candidates:
                    exact = [gsis for gsis, identity in identities.items()
                             if normalize_name(player['last_name']) in identity['last_names']
                             and player['birth_date'] == identity['birth_date']
                             and physical_matches(payload, player, identity)]
                    method = 'unique_surname_birth_date_and_physical_profile'
                    if not exact and allow_profile_corroboration:
                        exact = [gsis for gsis, identity in identities.items()
                            if normalize_name(player['last_name']) in identity['last_names']
                            and any(normalize_name(n).startswith(normalize_name(player['first_name'])[:1]) for n in identity['names'])
                            and profile_corroborates(payload,player,identity,
                                require_college=player['birth_date']!=identity['birth_date'])]
                        method = 'unique_surname_initial_corroborated_profile'
            if len(exact) == 1:
                gsis = exact[0]
                matched.setdefault(gsis, []).append({**player, 'identity_method': method,
                    'sourced_birth_date': identities[gsis]['birth_date']})
            else:
                unresolved.append({'player': player, 'reason': 'ambiguous_identity' if len(exact)>1
                                   else 'birth_date_conflict' if candidates else 'unknown_name',
                                   'candidate_gsis_ids': sorted(candidates)})
        return roster, matched, unresolved

    native, native_ids, native_unknown = resolve(native_payload, include_unassigned=True)
    source, source_ids, source_unknown = resolve(source_payload, include_unassigned=False)
    matches, blocked = [], list(source_unknown)
    for gsis, members in source_ids.items():
        candidates = native_ids.get(gsis, [])
        if len(members) != 1 or len(candidates) != 1:
            for player in members:
                blocked.append({'player': player, 'gsis_id': gsis,
                                'reason': 'duplicate_identity' if len(members)>1 or len(candidates)>1
                                else 'no_verified_native_image_record'})
            continue
        player, original = members[0], candidates[0]
        matches.append({'gsis_id': gsis, 'source_slot': player['source_slot'],
                        'native_slot': original['source_slot'], 'desired_team': player['team'],
                        'first_name': player['first_name'], 'last_name': player['last_name'],
                        'birth_date': player['birth_date'],
                        'sourced_birth_date': player['sourced_birth_date'],
                        'source_identity_method': player['identity_method'],
                        'native_identity_method': original['identity_method'],
                        'preserve_native_photo_id': original['native_photo_id']})
    free_agents = []
    for member in source['free_agents']:
        slot = member['source_slot']
        ids = [gsis for gsis, players in source_ids.items()
               if any(p['source_slot'] == slot for p in players)]
        entry = {**member, 'gsis_id': ids[0] if len(ids) == 1 else None,
                 'availability_verified': False}
        if len(ids) != 1:
            entry['blocker'] = 'unresolved_identity'
        elif any(p['team'] != 'free_agents' for p in source_ids[ids[0]]):
            entry['blocker'] = 'also_assigned_to_source_team'
        elif len(source_ids[ids[0]]) != 1:
            entry['blocker'] = 'duplicate_free_agent_identity'
        elif any(status in ('ACT', 'INA', 'DEV', 'RES')
                 for _, status in identities[ids[0]]['statuses']):
            entry['blocker'] = 'week1_club_status_conflict'
        else:
            # A prior-season identity, absence from a weekly roster, an inactive
            # contract or a CUT label does not prove unrestricted availability.
            entry['blocker'] = 'missing_dated_availability_evidence'
        free_agents.append(entry)
    return {'season_year': season_year, 'source_sha256': source['payload_sha256'],
            'source_free_agents_included': include_source_free_agents,
            'native_sha256': native['payload_sha256'], 'matched': matches,
            'native_identities': {gsis:members for gsis,members in native_ids.items()},
            'unresolved_source': blocked, 'unresolved_native': native_unknown,
            'source_identities': {gsis: {'birth_date': identities[gsis]['birth_date'],
                                       'names': sorted(identities[gsis]['names']),
                                       'statuses': sorted(identities[gsis]['statuses']),
                                       'identity_evidence_seasons': sorted(identities[gsis]['evidence_seasons']),
                                       'source_slots': [p['source_slot'] for p in members]}
                                  for gsis, members in source_ids.items()},
            'all_source_images_verified': not blocked,
            'free_agent_audit': free_agents,
            'free_agent_pool_verified': False,
            'excluded_conflicting_historical_ids': excluded_historical_ids,
            'writes_performed': False, 'contracts_reconciled': False}
