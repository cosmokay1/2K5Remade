"""Prepare a separate signed PC Settings1 copy; never edits a source or roster.

Slider layout: Mod Studio RC112 save_writer; native getters1490E0/1493E0/
1494E0/149B70 and penalty getters149C50..14A3A0. Speed formatter14C480
indexes4ED944 (Slow/Normal/Fast); boolean formatters index4ED994 (Off/On).
The input template supplies unmodified settings and native container metadata.
"""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import shutil
import struct

ORDER = ('Blocking', 'Passing', 'Running', 'Coverage', 'Pursuit',
         'Tackling', 'Kicking', 'Fatigue', 'Catching')
SPECIAL = {'Injury': 0x284, 'Fumble': 0x288, 'Interception': 0x28c}
# No guessed write to unused E600A8/prefix128.
PENALTIES = (0x110, 0x114, 0x118, 0x11c, 0x120, 0x124,
             0x12c, 0x130, 0x134, 0x138)


def prepare(source, output, played_minutes=10):
    source, output = Path(source), Path(output)
    if output.exists() or source.resolve() == output.resolve():
        raise ValueError('Output must be a new settings directory')
    if type(played_minutes) is not int or not 1 <= played_minutes <= 15:
        raise ValueError('Played minutes must be1..15')
    profile = json.loads((Path(__file__).resolve().parents[1] /
                          'data/settings/rspencer86.json').read_text())
    before = (source / 'SAVEGAME.DAT').read_bytes()
    signature = (source / 'EXTRA').read_bytes()
    if len(before) != 736 or not hmac.compare_digest(signature, hmac.digest(bytes(16), before, 'sha1')):
        raise ValueError('Expected a signed PC-runtime STG settings template')
    after = bytearray(before)
    allowed = set()

    def word(offset, fmt, value):
        struct.pack_into(fmt, after, offset, value)
        allowed.update(range(offset, offset + 4))

    for group, starts in (('human', (0x154, 0x2bc)), ('cpu', (0x178, 0x298))):
        for name in ORDER:
            value = profile[group][name]
            for start in starts:
                word(start + ORDER.index(name)*4, '<f', value/40)
    for name, offset in SPECIAL.items():
        word(offset, '<f', profile['shared'][name]/40)
    for offset in PENALTIES:
        word(offset, '<f', 1.0)
    for offset, value in ((0x28, 1), (0xb4, 0), (0xc0, 0), (0x10c, 1),
                          (0x8c, played_minutes), (0x90, 5)):
        word(offset, '<I', value)
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert set(changed) <= allowed and len(after) == 736
    shutil.copytree(source, output)
    (output / 'SAVEGAME.DAT').write_bytes(after)
    (output / 'EXTRA').write_bytes(hmac.digest(bytes(16), after, 'sha1'))
    assert (source / 'SAVEGAME.DAT').read_bytes() == before
    assert (source / 'EXTRA').read_bytes() == signature
    assert hmac.compare_digest((output / 'EXTRA').read_bytes(),
                               hmac.digest(bytes(16), (output / 'SAVEGAME.DAT').read_bytes(), 'sha1'))
    return dict(profile=profile['name'], played_minutes=played_minutes,
                simulated_minutes=5, changed_bytes=len(changed),
                source_sha256=hashlib.sha256(before).hexdigest(),
                settings_sha256=hashlib.sha256(after).hexdigest(),
                source_preserved=True, signature_verified=True,
                coaching_or_roster_writes=False, clock_calibrated=False,
                game_load_verified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--played-minutes', type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output, args.played_minutes), indent=2))
