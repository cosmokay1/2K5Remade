"""Actual addon identity snapshots against independent authored saved semantics."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

from tools.franchise_identity_state import saved_identity_state
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    executable = Path(args[0]).resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tests'))
    from test_franchise_finance_state import fixture, live_fixture
    from test_franchise_identity_state import rename
    payload = fixture(); expected = saved_identity_state(payload); cases = 0
    with tempfile.TemporaryDirectory(prefix='native identity state ') as directory:
        root = Path(directory); memory, output = root/'memory.dat', root/'state.dat'
        def check(image, outcome, reference=expected):
            nonlocal cases
            output.unlink(missing_ok=True); memory.write_bytes(image)
            result = subprocess.run([str(executable), str(memory), str(output), 'identity'], timeout=15, capture_output=True)
            if outcome == 'invalid':
                assert result.returncode == 1 and not output.exists(), (outcome, result.returncode, result.stderr)
            else:
                assert result.returncode == 0, (outcome, result.returncode, result.stderr)
                assert (output.read_bytes() == reference) == (outcome == 'equal'), outcome
            cases += 1
        for relocation in (0, 0x20000):
            check(live_fixture(payload, relocation), 'equal')
        reordered = live_fixture(payload)
        reordered[0xA0000:0xA0008] = reordered[0xA0004:0xA0008]+reordered[0xA0000:0xA0004]
        check(reordered, 'equal')
        for first, last in (('É😀"\\', "O'Neal"), ('a'*49, 'b'*49)):
            unicode_payload = rename(payload, 0, first, last)
            check(live_fixture(unicode_payload), 'equal', saved_identity_state(unicode_payload))
        expanded = bytearray(payload)
        struct.pack_into('<I', expanded, 0x320, 5198)
        struct.pack_into('<i', expanded, 0x32C, PLAYER_START+5198*PLAYER_STRIDE-0x32C+1)
        check(live_fixture(bytes(expanded)), 'equal', saved_identity_state(bytes(expanded)))
        for slot, field in ((0, 4), (1, 7), (2, 0x19), (2, 0x1B)):
            changed = live_fixture(payload); changed[0x200000+slot*0x54+field] ^= 1
            check(changed, 'different')
        changed = live_fixture(payload)
        name = struct.unpack_from('<I', changed, 0x200000+2*0x54+0x10)[0]
        struct.pack_into('<H', changed, name, ord('Z'))
        check(changed, 'different')
        ignored = live_fixture(payload)
        ignored[0x200000+2618*0x54+4] = 255
        struct.pack_into('<I', ignored, 0x200000+2618*0x54+0x10, 0xffffffff)
        check(ignored, 'equal')
        contract = live_fixture(payload); struct.pack_into('<H', contract, 0x200000+10, 830)
        check(contract, 'equal') # Financial comparison independently rejects this.
        for pointer in (0, 1, 0xffffffff, 0xE57FFE):
            malformed = live_fixture(payload); struct.pack_into('<I', malformed, 0x200000+0x10, pointer)
            check(malformed, 'invalid')
        for invalid_name in (b'\0\0', b'\x1f\0\0\0', b'\0\xd8\0\0', b'\0\xdc\0\0',
                             b'\0\xd8\0\xd8\0\0', ('X'*50).encode('utf-16le')):
            malformed = live_fixture(payload)
            malformed[0x400000:0x400000+len(invalid_name)] = invalid_name
            check(malformed, 'invalid')
        duplicate = live_fixture(payload); struct.pack_into('<I', duplicate, 0xA0000, 0x200000)
        check(duplicate, 'invalid')
        check(live_fixture(payload)[:0xE57870], 'invalid')
    print(f'{cases} native identity comparisons passed; no atomicity, runtime identity or write grant.')


if __name__ == '__main__':
    main()
