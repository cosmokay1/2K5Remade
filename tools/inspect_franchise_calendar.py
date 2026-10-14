"""Read-only scheduler header for the observed Xbox FXG layout.

Independently derived from original save/load and display routines. Raw phase
codes are not modern league phases; this does not import or advance a ledger.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from tools.inspect_franchise_save import SIZE


def inspect_calendar(payload: bytes) -> dict:
    if type(payload) is not bytes or len(payload) != SIZE or payload[:4] != b'\x04\0\0\0':
        raise ValueError('Unsupported observed Xbox FXG layout')
    # E2E00 supplies the prefix size. C1F90 stores bank allocation+0x20
    # at prefix+4, while BFE50/16A0F0 advance allocation+0x40 (even).
    prefix = 0x2E0
    if payload[prefix:prefix+4] != b'ROST' or payload[prefix+0x2C:prefix+0x30] != b'ROST':
        raise ValueError('Observed serialized roster headers required')
    stored_size = struct.unpack_from('<I', payload, prefix + 4)[0]
    if stored_size < 0x20:
        raise ValueError('Invalid roster section size')
    bank_size = stored_size + 0x20
    start = prefix + bank_size + (bank_size & 1)
    # C5300 scheduler size; 2D0780 franchise tail size. Reject another layout,
    # rather than find a plausible header by scanning or from the file's end.
    if start + 0x83DC + 0x165B0 != len(payload):
        raise ValueError('Serialized section boundaries do not match observed FXG')
    header = payload[start:start+11]
    if header[0] != 2 or header[3] != 32:
        raise ValueError('Observed 32-team franchise scheduler required')
    # C5310 stores E576B8 at +6; C5800 zero-extends it on load.
    # C4EB0 retrieves it; 247AC0 displays it with a 2004 offset.
    return {'scope': 'saved original scheduler; live calendar and modern phases unverified',
            'payload_sha256': hashlib.sha256(payload).hexdigest(),
            'scheduler_offset': start, 'table_mode': header[0],
            'season_index': header[6], 'display_year': 2004 + header[6],
            'phase_01_raw': header[1], 'phase_02_raw': header[2],
            'step_04_raw': header[4], 'step_05_raw': header[5],
            'counter_08_raw': struct.unpack_from('<H', header, 8)[0]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect_calendar(args.save.read_bytes())
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
