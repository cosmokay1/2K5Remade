"""Cross-check production native league capture against authored saved semantics."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

from tools.franchise_finance_state import saved_finance_state


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    executable = Path(args[0]).resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tests'))
    from test_franchise_finance_state import fixture, live_fixture
    payload = fixture(); expected = saved_finance_state(payload)
    cases = 0
    with tempfile.TemporaryDirectory(prefix='native finance state ') as directory:
        root = Path(directory); memory, output = root/'memory.dat', root/'state.dat'
        def check(image, outcome):
            nonlocal cases
            output.unlink(missing_ok=True); memory.write_bytes(image)
            result = subprocess.run([str(executable), str(memory), str(output)], timeout=15, capture_output=True)
            if outcome == 'invalid':
                assert result.returncode == 1 and not output.exists(), (outcome, result.returncode, result.stderr)
            else:
                assert result.returncode == 0, (outcome, result.returncode, result.stderr)
                assert (output.read_bytes() == expected) == (outcome == 'equal'), outcome
            cases += 1
        for relocation in (0, 0x20000):
            check(live_fixture(payload, relocation), 'equal')
        reordered = live_fixture(payload)
        reordered[0xA0000:0xA0008] = reordered[0xA0004:0xA0008]+reordered[0xA0000:0xA0004]
        check(reordered, 'equal')
        # Selected and unrelated/unrostered contract changes, all32 cap branches,
        # another club's membership, league cap and calendar must all differ.
        for address, fmt, value in ((0x200000+10, '<H', 830), (0x200000+2618*0x54+36, '<I', 2),
                (0x200000+8, '<B', 8), (0x80000+31*0x1F4+0x124, '<I', 1),
                (0x80000+31*0x1F4+0x19C, '<H', 1), (0xE5775C+31*4, '<I', 1),
                (0xE3C278, '<I', 80501), (0xE576B8, '<I', 23), (0xE576BC, '<I', 1)):
            changed = live_fixture(payload); struct.pack_into(fmt, changed, address, value)
            check(changed, 'different')
        moved = live_fixture(payload)
        struct.pack_into('<I', moved, 0x10038, 1)
        struct.pack_into('<I', moved, 0x80000+31*0x1F4, 0x200000+2*0x54)
        moved[0x80000+31*0x1F4+0x11C] = 1
        check(moved, 'different')
        for address, fmt, value in ((0xB72918, '<I', 0xffffffff), (0x10000, '<I', 5199),
                (0x10004, '<I', 0xfffffff0), (0xE576A0, '<I', 0), (0xE576AC, '<I', 31),
                (0xE576B8, '<I', 256), (0xE3C278, '<I', 0), (0x10038, '<I', 2620),
                (0x1003C, '<I', 0xffffffff), (0xA0000, '<I', 0x200001),
                (0xA0000, '<I', 0x200000), (0xA0004, '<I', 0x200000+0x54),
                (0xE5786C+4, '<I', 0x80000), (0x80000+0x11C, '<B', 72)):
            malformed = live_fixture(payload); struct.pack_into(fmt, malformed, address, value)
            check(malformed, 'invalid')
        check(live_fixture(payload)[:0xE57870], 'invalid')
    print(f'{cases} native financial comparison cases passed; no write authorization or game execution.')


if __name__ == '__main__':
    main()
