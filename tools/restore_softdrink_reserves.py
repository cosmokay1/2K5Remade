"""Restore omitted SOFTDRINK v0.6.1 players to playable rosters; no addon code.

Requires the user's pack and its original Mod Studio RC112 codec. No retail
assets or player database are distributed here. The recipe's existing records
alone are eligible; missing players are reported, never synthesized.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

ROSTER_SHA = '7c5f9a0091abdb64ae8c8c608adcd0a7854f1f84c2d8c7da0040d095ee991271'
RECIPE_SHA = '132a3ed1d3d1c993272a8669acb0d08caee48b2b5de0564a7b3e53b03fce32d3'
OVERLAY_SHA = '9f754040fa50e29d900fdaec15923a2eb3b3bb93d673a85842877747d0c747e9'
XBE_SHA = '9465382bfd617b6d1aeadc5653fefef256678c12a65a5f828705495291e40610'
RECIPE_ENTRY = ('assets/files/1e91b8a6a2e2fc438da2_'
                '29c4ba3bf96967ecb8f6_roster-edits-hback-2026-10-14.json')
EXTENT = struct.Struct('<QIBHQ')
ROSTER_START = 3815424


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def restore(payload, recipe, records, squads):
    """Append authored RES players to active lists; preserve existing members."""
    require(digest(payload) == ROSTER_SHA, 'Expected the unmodified v0.6.1 disc roster')
    roster = records.RosterDocument(payload, base=32, base_year=2026, reference_year=2026)
    squads.validate_roster(payload, strict_owners=True)
    players = {(p.pool, p.index): p for p in roster.players}
    clubs = {t.abbreviation: t for t in roster.teams[:32]}
    require(len(clubs) == 32, 'Expected all 32 distinct clubs')
    pending = {name: [] for name in clubs}
    seen = set()
    for row in recipe['roster_refresh']['players']:
        if row['status'] != 'RES':
            continue
        key = ('primary', row['index'])
        require(key not in seen, 'Duplicate reserve identity')
        seen.add(key)
        player = players[key]
        require((player.first, player.last, str(player.record.birth_date)) ==
                (row['first'], row['last'], row['birth_date']), 'Reserve identity mismatch')
        require(row['team'] in clubs, 'Unknown reserve club')
        require(roster.club_of(player) is None and not roster.is_free_agent(player),
                'Reserve is already owned or offered as a free agent')
        require(not player.record.on_injured_reserve, 'Existing IR state needs separate handling')
        require(player.record.encode()[8] & 0x1c == 4,
                'Restored record is not an eligible NFL player')
        pending[row['team']].append(row)
    require(len(seen) == 81, 'Pinned release reserve coverage changed')
    out = bytearray(payload)
    allowed = set()
    restored = []
    for name, team in clubs.items():
        additions = pending[name]
        active = [(offset - roster.primary_table) // records.PLAYER_SIZE
                  for offset in team.slots] + [p['index'] for p in additions]
        reserves = list(roster.reserves[team.index])
        require(len(active) <= records.TEAM_SLOTS and len(active) + len(reserves) <= 65,
                'Active/physical roster capacity exceeded')
        raw = squads.repack_team(
            payload[team.offset:team.offset + records.TEAM_SIZE], active, reserves,
            team_offset=team.offset, player_pool_offset=roster.primary_table,
            player_count=len(roster.by_pool('primary')),
            mark=bool(payload[team.offset + squads.VERSION_OFFSET]))
        out[team.offset:team.offset + records.TEAM_SIZE] = raw
        # Existing active pointers, salary/stat caches and every player record
        # are outside this allowance. Existing reserve pointers shift to make
        # room for the new active entries; their identities/order stay intact.
        allowed.update(range(team.offset + len(team.slots) * 4, team.offset + 260))
        allowed.update(team.offset + n for n in (squads.VERSION_OFFSET, squads.COUNT,
                                               squads.MARKER_OFFSET, squads.ACTIVE_COUNT))
        restored.extend(dict(team=name, index=p['index'], name=p['first'] + ' ' + p['last'],
                             gsis_id=p['gsis_id']) for p in additions)
    changed = [i for i, (a, b) in enumerate(zip(payload, out)) if a != b]
    require(set(changed) <= allowed, 'Write escaped membership pointer/count fields')
    squads.validate_roster(bytes(out), strict_owners=True)
    fresh = records.RosterDocument(bytes(out), base=32, base_year=2026, reference_year=2026)
    for p in restored:
        player = fresh.by_offset[roster.primary_table + p['index'] * records.PLAYER_SIZE]
        require(clubs[p['team']].index in player.teams
                and ('primary', p['index']) not in fresh.reserve_owner,
                'Restored player is not on the active roster')
    for old, new in zip(roster.teams, fresh.teams):
        require(new.slots[:len(old.slots)] == old.slots, 'Existing active players changed')
        require(fresh.reserves[old.index] == roster.reserves[old.index], 'Existing reserves changed')
    mapped = {p['gsis_id'] for p in restored}
    unavailable = [p for p in recipe['roster_refresh']['unrepresented']
                   if p['status'] == 'RES' and p['gsis_id'] not in mapped]
    return bytes(out), dict(
        source_roster_sha256=digest(payload), corrected_roster_sha256=digest(out),
        restored=restored, clubs_checked=32, changed_bytes=len(changed),
        unrepresented_without_authored_reserve_record=unavailable,
        player_records_unchanged=True, existing_active_players_preserved=True,
        existing_reserves_preserved=True, restored_to_active_rosters=True,
        free_agents_unchanged=True, alumni_lists_unchanged=True,
        destination='playable active rosters; normal stock roster/cap rules apply',
        game_execution_verified=False, franchise_save_reload_verified=False)


def replace_extents(data, start, length, literal_offset):
    """Replace one byte interval, preserving sparse gaps and clipped sources."""
    require(length > 0 and start >= 0 and literal_offset >= 0, 'Invalid replacement range')
    require(len(data) % EXTENT.size == 0, 'Truncated extent table')
    end = start + length
    out = bytearray()
    inserted = False
    previous_end = 0
    for dst, size, kind, source, offset in EXTENT.iter_unpack(data):
        require(size > 0 and dst >= previous_end and kind in (0, 1), 'Invalid extent order/type')
        previous_end = dst + size
        if dst >= end and not inserted:
            out += EXTENT.pack(start, length, 0, 65535, literal_offset)
            inserted = True
        if dst + size <= start or dst >= end:
            out += EXTENT.pack(dst, size, kind, source, offset)
            continue
        if dst < start:
            out += EXTENT.pack(dst, start - dst, kind, source, offset)
        if not inserted:
            out += EXTENT.pack(start, length, 0, 65535, literal_offset)
            inserted = True
        if dst + size > end:
            out += EXTENT.pack(end, dst + size - end, kind, source, offset + end - dst)
    if not inserted:
        out += EXTENT.pack(start, length, 0, 65535, literal_offset)
    return bytes(out)


def patch_index(index, start, replacement, literal_offset):
    require(index[:8] == b'2K5OVL1\0', 'Unknown overlay format')
    files, tables = struct.unpack_from('<II', index, 8)
    cursor = 16
    target = None
    sizes = []
    for i in range(files):
        n = struct.unpack_from('<H', index, cursor)[0]
        cursor += 2
        name = index[cursor:cursor+n].decode('utf-8').replace('\\', '/')
        cursor += n
        _, size = struct.unpack_from('<QQ', index, cursor)
        sizes.append(size)
        cursor += 16
        if name == 'vc_53450030/0':
            require(target is None, 'Duplicate volume')
            target = i
    require(target is not None and start + len(replacement) <= sizes[target], 'Missing/outside volume')
    out = bytearray(index[:cursor])
    patched = False
    for _ in range(tables):
        i, n = struct.unpack_from('<II', index, cursor)
        cursor += 8
        end = cursor + n * EXTENT.size
        require(end <= len(index), 'Truncated overlay')
        data = index[cursor:end]
        if i == target:
            require(not patched, 'Duplicate volume table')
            data = replace_extents(data, start, len(replacement), literal_offset)
            patched = True
        out += struct.pack('<II', i, len(data) // EXTENT.size) + data
        cursor = end
    require(patched and cursor == len(index), 'Missing table or trailing overlay bytes')
    return bytes(out), target


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('codec', 'patch', 'roster', 'pack', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    args = p.parse_args()
    require(not args.output.exists(), 'Use a new output directory')
    sys.path.insert(0, str(args.codec.resolve()))
    from mod_editor.core import nfl2k5_roster_records as records
    from mod_editor.core import nfl2k5_practice_squad as squads
    with zipfile.ZipFile(args.patch) as z:
        raw = z.read(RECIPE_ENTRY)
    require(digest(raw) == RECIPE_SHA, 'Expected official v0.6.1 recipe')
    replacement, report = restore(args.roster.read_bytes(), json.loads(raw), records, squads)
    original_index = (args.pack / 'overlay.bin').read_bytes()
    require(digest(original_index) == OVERLAY_SHA, 'Expected unmodified v0.6.1 overlay index')
    require(digest((args.pack / 'default.xbe').read_bytes()) == XBE_SHA,
            'Expected unmodified v0.6.1 executable')
    literal = args.pack / 'lit/7.bin'
    index, target = patch_index(original_index, ROSTER_START,
                                replacement, literal.stat().st_size)
    require(target == 7, 'Unexpected pinned volume index')
    args.output.mkdir(parents=True)
    (args.output / 'lit').mkdir()
    (args.output / 'roster.bin').write_bytes(replacement)
    (args.output / 'overlay.bin').write_bytes(index)
    (args.output / 'lit/7.bin').write_bytes(literal.read_bytes() + replacement)
    report['overlay_sha256'] = digest(index)
    report['literal_sha256'] = digest((args.output / 'lit/7.bin').read_bytes())
    (args.output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(restored=len(report['restored']), clubs=32,
                         changed_roster_bytes=report['changed_bytes'],
                         unavailable=len(report['unrepresented_without_authored_reserve_record']))))


if __name__ == '__main__':
    main()
