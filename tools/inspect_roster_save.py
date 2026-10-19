"""Inspect the standalone NFL 2K5 ROST before an isolated import.

Layout credit: BAD-AL/nfl2k5tool_dart (see inspect_franchise_save).
Some community saves reference names outside the primary name pool. Read-only
inspection permits bounded, terminated UTF-16 after the declared player bank,
reports every such reference and does not authorize importing financial records.
The strict franchise/identity reader is unchanged.
"""
import hashlib
import struct
from tools.inspect_franchise_save import TEAMS, PLAYER_STRIDE


def inspect_roster(payload, *, include_unassigned=False):
    if type(payload) is not bytes or len(payload) != 0x91040:
        raise ValueError('Unsupported standalone ROST; expected 593984-byte payload')
    return _inspect_roster(payload, 0, len(payload), include_unassigned=include_unassigned)


def inspect_trial_franchise_roster(payload):
    """Audit only: tolerate/report the imported auxiliary names in saved FXG.

    This never broadens the production franchise identity reader or issues IDs.
    """
    from tools.inspect_franchise_calendar import inspect_calendar
    inspect_calendar(payload)
    return _inspect_roster(payload, 0x2E0, 0x94D10)


def _inspect_roster(payload, prefix, string_end, *, include_unassigned=False):
    player_start, string_start = prefix+0xAFA8, prefix+0x75960
    def pointer(location):
        if type(location) is not int or location < 0 or location + 4 > len(payload) or location % 4:
            raise ValueError('Pointer storage is outside the aligned payload')
        target = location + struct.unpack_from('<i', payload, location)[0] - 1
        if not 0 <= target < len(payload):
            raise ValueError('Relative pointer target is outside the payload')
        return target

    # The prefix contains saved settings, not a format magic. Validate the
    # serialized roster section and its declared record bank instead. SOFTDRINK
    # expands this bank; a fixed retail membership limit loses valid players.
    if (payload[prefix:prefix+4] != b'ROST' or
            payload[prefix+0x2C:prefix+0x30] != b'ROST' or
            struct.unpack_from('<I', payload, prefix+4)[0] != 0x91020):
        raise ValueError('Unsupported serialized roster section')
    player_count = struct.unpack_from('<I', payload, prefix+0x40)[0]
    if (not 0 < player_count <= (string_start - player_start) // PLAYER_STRIDE or
            pointer(prefix+0x44) != player_start or
            pointer(prefix+0x4C) != player_start + player_count * PLAYER_STRIDE):
        raise ValueError('Invalid declared player bank boundaries')

    nonstandard_names = []
    def player_name(location):
        start = pointer(location)
        if start % 2 or not player_start + player_count * PLAYER_STRIDE <= start < string_end:
            raise ValueError('Player name pointer is outside the UTF-16 string region')
        if not string_start <= start < prefix+0x88D80:
            nonstandard_names.append({"pointer_offset":location,"string_offset":start})
        end = start
        while end + 2 <= string_end and end - start < 100:
            if payload[end:end+2] == b'\0\0':
                try:
                    result = payload[start:end].decode('utf-16le')
                except UnicodeDecodeError as error:
                    raise ValueError('Invalid UTF-16 player name') from error
                if not result or any(ord(c) < 32 for c in result):
                    raise ValueError('Empty or invalid player name')
                return result
            end += 2
        raise ValueError('Player name lacks a bounded UTF-16 terminator')

    seen = set()
    def members(start, count):
        if start % 4 or start < 0 or start + count * 4 > len(payload):
            raise ValueError('Roster pointer table is outside the aligned payload')
        result = []
        for location in range(start, start + count * 4, 4):
            record = pointer(location)
            delta = record - player_start
            if delta < 0 or delta % PLAYER_STRIDE or delta // PLAYER_STRIDE >= player_count:
                raise ValueError('Roster pointer does not reference an aligned player record')
            if record in seen:
                raise ValueError('Duplicate player record across roster memberships')
            seen.add(record)
            result.append({'source_slot':delta // PLAYER_STRIDE,
                           'first_name':player_name(record + 0x10),
                           'last_name':player_name(record + 0x14)})
        return result

    teams = {}
    for index, team in enumerate(TEAMS):
        count = payload[prefix+0x42E4 + index * 0x1F4]
        # Pointer table ends at its count byte; 71 four-byte entries fit.
        if count > 71:
            raise ValueError('Team count exceeds the supported pointer table')
        teams[team] = members(prefix+0x41C8 + index * 0x1F4, count)
    free_count = struct.unpack_from('<H', payload, prefix+0x78)[0]
    if free_count > player_count:
        raise ValueError('Free-agent count exceeds the player record capacity')
    free_agents = members(pointer(prefix+0x7C), free_count)
    bank = {}
    if include_unassigned:
        unassigned, unreadable = [], []
        for slot in range(player_count):
            record = player_start + slot * PLAYER_STRIDE
            if record in seen:
                continue
            try:
                first, last = player_name(record+0x10), player_name(record+0x14)
            except ValueError:
                unreadable.append(slot)
                continue
            unassigned.append({'source_slot': slot, 'first_name': first, 'last_name': last})
        bank = {'unassigned_players': unassigned, 'unreadable_unassigned_slots': unreadable}
    return {'format':1,'scope':'standalone ROST read-only membership; no franchise or cap authority',
            'source_slot_semantics':'snapshot record locator; not a persistent player identity',
            'payload_sha256':hashlib.sha256(payload).hexdigest(),'size_bytes':len(payload),
            'player_record_count':player_count,
            'nonstandard_name_pointers':nonstandard_names,'teams':teams,'free_agents':free_agents,
            'membership_count':len(seen), **bank}
