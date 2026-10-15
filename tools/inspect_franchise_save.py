"""Read-only inspection of the observed retail Xbox FXG layout.

Format references: BAD-AL/nfl2k5tool_dart, gamesave_tool.dart at
https://github.com/BAD-AL/nfl2k5tool_dart/tree/e3afeece61896380a95e506ab43ae1abda0ae8a5
This independent reader exposes no ratings or financial interpretations.
Source slots locate records in this snapshot; they are not persistent player IDs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SIZE = 720044
PLAYER_START = 0xB288
PLAYER_STRIDE = 0x54
STRING_START, STRING_END = 0x75C40, 0x94D10
TEAMS = ('49ers','Bears','Bengals','Bills','Broncos','Browns','Buccaneers','Cardinals',
         'Chargers','Chiefs','Colts','Cowboys','Dolphins','Eagles','Falcons','Giants',
         'Jaguars','Jets','Lions','Packers','Panthers','Patriots','Raiders','Rams',
         'Ravens','Redskins','Saints','Seahawks','Steelers','Texans','Titans','Vikings')


def inspect_save(payload: bytes) -> dict:
    if type(payload) is not bytes or len(payload) != SIZE:
        raise ValueError('Unsupported raw Xbox FXG layout; expected observed 720044-byte payload')

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
    if (payload[0x2E0:0x2E4] != b'ROST' or
            payload[0x30C:0x310] != b'ROST' or
            struct.unpack_from('<I', payload, 0x2E4)[0] != 0x91020):
        raise ValueError('Unsupported serialized roster section')
    player_count = struct.unpack_from('<I', payload, 0x320)[0]
    if (not 0 < player_count <= (STRING_START - PLAYER_START) // PLAYER_STRIDE or
            pointer(0x324) != PLAYER_START or
            pointer(0x32C) != PLAYER_START + player_count * PLAYER_STRIDE):
        raise ValueError('Invalid declared player bank boundaries')

    def player_name(location):
        start = pointer(location)
        if start % 2 or not STRING_START <= start < STRING_END:
            raise ValueError('Player name pointer is outside the UTF-16 string region')
        end = start
        while end + 2 <= STRING_END and end - start < 100:
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
            delta = record - PLAYER_START
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
        count = payload[0x45C4 + index * 0x1F4]
        # Pointer table ends at its count byte; 71 four-byte entries fit.
        if count > 71:
            raise ValueError('Team count exceeds the supported pointer table')
        teams[team] = members(0x44A8 + index * 0x1F4, count)
    free_count = struct.unpack_from('<H', payload, 0x358)[0]
    if free_count > player_count:
        raise ValueError('Free-agent count exceeds the player record capacity')
    free_agents = members(pointer(0x35C), free_count)
    return {'format':1,'scope':'observed retail Xbox FXG roster inspection',
            'source_slot_semantics':'snapshot record locator; not a persistent player identity',
            'payload_sha256':hashlib.sha256(payload).hexdigest(),'size_bytes':len(payload),
            'player_record_count':player_count,
            'year_scope':'scheduled-game year byte; not authoritative franchise season',
            'year':2000 + payload[0x917EF],'teams':teams,'free_agents':free_agents,
            'membership_count':len(seen)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path, help='Raw Xbox franchise SAVEGAME.DAT; no writes')
    args = parser.parse_args(argv)
    print(json.dumps(inspect_save(args.save.read_bytes()), indent=2))


if __name__ == '__main__':
    main()
