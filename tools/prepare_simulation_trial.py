"""Create a fresh signed PC-runtime save copy for a simulated-quarter trial.

Never writes the source. Quarter field evidence: menu row 0x52BD74 labels
"Sim. Quarter Length"; getter 0x2C6F60 reads E60010, increment/decrement
0x2C6F00/30 enforce 3..15. Played getter 0x149170 reads E6000C.
Save prefix is E5FF80..E60260, per cruuz's nfl2k5_save_writer.py at e193841.
PC HMAC signing matches src/nfl2k5_save_library.cpp, runtime_zero_key.
These public format constants are not cloud credentials. In-game loading and
setting-display corroboration remain required before simulation acceptance.
"""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import shutil
import struct

from tools.inspect_franchise_calendar import inspect_calendar

SIM_MINUTES = 0x90
PLAYED_MINUTES = 0x8C


def patch_simulated_minutes(payload, minutes):
    if type(minutes) is not int or not 3 <= minutes <= 15:
        raise ValueError('Simulated quarter length must be 3..15 minutes')
    inspect_calendar(payload)
    played, previous = struct.unpack_from('<2I', payload, PLAYED_MINUTES)
    if not 1 <= played <= 15 or not 3 <= previous <= 15:
        raise ValueError('Unsupported saved quarter-length encoding')
    result = bytearray(payload)
    struct.pack_into('<I', result, SIM_MINUTES, minutes)
    assert result[:SIM_MINUTES] == payload[:SIM_MINUTES]
    assert result[SIM_MINUTES+4:] == payload[SIM_MINUTES+4:]
    return bytes(result)


def prepare_trial(source, destination, minutes):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError('Destination must be a fresh directory')
    names = ('SAVEGAME.DAT', 'EXTRA', 'TYPE', 'SaveMeta.xbx', '.nfl2k5-save.ini')
    files = {name: (source/name).read_bytes() for name in names if (source/name).is_file()}
    payload, signature = files['SAVEGAME.DAT'], files['EXTRA']
    if not hmac.compare_digest(signature, hmac.digest(bytes(16), payload, 'sha1')):
        raise ValueError('Source must have a valid PC-runtime signature; no fallback')
    changed = patch_simulated_minutes(payload, minutes)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        for name, data in files.items():
            if name == 'SAVEGAME.DAT': data = changed
            if name == 'EXTRA': data = hmac.digest(bytes(16), changed, 'sha1')
            (destination/name).write_bytes(data)
        for name, data in files.items():
            if (source/name).read_bytes() != data:
                raise ValueError('Source changed during preparation')
        receipt = {'source_sha256': hashlib.sha256(payload).hexdigest(),
                   'trial_sha256': hashlib.sha256(changed).hexdigest(),
                   'played_minutes': struct.unpack_from('<I', changed, PLAYED_MINUTES)[0],
                   'simulated_minutes': minutes, 'only_data_field_changed': '0x90..0x93',
                   'signature_verified': hmac.compare_digest((destination/'EXTRA').read_bytes(),
                       hmac.digest(bytes(16), (destination/'SAVEGAME.DAT').read_bytes(), 'sha1')),
                   'game_load_verified': False, 'seasons_simulated': 0}
        return receipt
    except Exception:
        shutil.rmtree(destination)
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('destination', type=Path)
    p.add_argument('--simulated-minutes', type=int, required=True)
    a = p.parse_args()
    print(json.dumps(prepare_trial(a.source, a.destination, a.simulated_minutes), indent=2))


if __name__ == '__main__':
    main()
