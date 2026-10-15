"""Canonical sampled roster biography comparison; no ratings, inference or grant."""
import struct

from tools.inspect_franchise_save import inspect_save, PLAYER_START, PLAYER_STRIDE

HEADER_SIZE = 12
RECORD_SIZE = 211


def saved_identity_state(payload: bytes) -> bytes:
    roster = inspect_save(payload)
    players = sorted([player for team in roster['teams'].values() for player in team]
                     + roster['free_agents'], key=lambda player: player['source_slot'])
    result = bytearray(HEADER_SIZE + RECORD_SIZE*len(players))
    struct.pack_into('<3I', result, 0, 1, roster['player_record_count'], len(players))
    for index, player in enumerate(players):
        destination = HEADER_SIZE + RECORD_SIZE*index
        source = PLAYER_START + PLAYER_STRIDE*player['source_slot']
        struct.pack_into('<I', result, destination, player['source_slot'])
        result[destination+4:destination+11] = payload[source+4:source+8] + payload[source+0x19:source+0x1C]
        for offset, field in ((11, 'first_name'), (111, 'last_name')):
            encoded = player[field].encode('utf-16le')
            if not 0 < len(encoded) <= 98:
                raise ValueError('Bounded UTF-16 player identity required')
            result[destination+offset:destination+offset+len(encoded)] = encoded
    return bytes(result)
