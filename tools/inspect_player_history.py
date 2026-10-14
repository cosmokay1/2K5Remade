"""Inspect packed original player history; metric names/units remain unverified.

Static E5E70 relocates player+0x2C; E8A0/E800 and EE40 in the 0x14xxxx
region establish traversal, filter fields and signed values. No ratings read.
"""
import argparse
import json
from pathlib import Path
import struct

from tools.inspect_franchise_save import inspect_save, PLAYER_START, PLAYER_STRIDE


def inspect_player_history(payload: bytes, source_slot: int) -> dict:
    roster = inspect_save(payload)
    if type(source_slot) is not int or source_slot < 0:
        raise ValueError('Source slot must be a nonnegative integer')
    members = [player for players in roster['teams'].values() for player in players] + roster['free_agents']
    found = [player for player in members if player['source_slot'] == source_slot]
    if len(found) != 1:
        raise ValueError('Source slot must identify one supported roster member')
    player = found[0]
    pointer_field = PLAYER_START + source_slot * PLAYER_STRIDE + 0x2C
    relative = struct.unpack_from('<i', payload, pointer_field)[0]
    report = {'scope': 'packed original history; statistic names, calendar periods and units unverified',
              'payload_sha256': roster['payload_sha256'],
              'source_slot_semantics': roster['source_slot_semantics'],
              **player, 'history_present': relative != 0, 'entries': []}
    if relative == 0:
        report['missing_evidence'] = 'No history pointer; do not infer zero performance'
        return report
    count = struct.unpack_from('<I', payload, 0x360)[0]
    bank_relative = struct.unpack_from('<i', payload, 0x364)[0]
    bank = 0x364 + bank_relative - 1
    end = bank + count * 4
    start = pointer_field + relative - 1
    if not count or not bank_relative or bank < 0 or bank % 4 or end > len(payload):
        raise ValueError('History bank is outside the supported aligned payload')
    if start < bank or start + 4 > end or (start - bank) % 4:
        raise ValueError('Player history pointer is outside the declared history bank')
    for offset in range(start, end, 4):
        word = struct.unpack_from('<I', payload, offset)[0]
        value = struct.unpack_from('<h', payload, offset)[0]
        report['entries'].append({'statistic_code_raw': (word >> 16) & 127,
                                  'period_code_raw': (word >> 23) & 31,
                                  'signed_value_raw': value,
                                  'deleted': bool(word & 0x10000000),
                                  'mode_code_raw': (word >> 29) & 1,
                                  'bit30_raw': (word >> 30) & 1,
                                  'last_entry': bool(word & 0x80000000)})
        if word & 0x80000000:
            return report
    raise ValueError('Player history lacks a terminator inside the declared bank')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('source_slot', type=int)
    args = parser.parse_args(argv)
    try:
        report = inspect_player_history(args.save.read_bytes(), args.source_slot)
    except (ValueError, OSError) as exc:
        parser.exit(2, f'inspect_player_history: {exc}\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
