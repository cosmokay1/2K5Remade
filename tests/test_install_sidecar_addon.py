import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tools.install_sidecar_addon import install


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dll(marker):
    data = bytearray(128)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 0x3c, 64)
    data[64:68] = b'PE\0\0'
    struct.pack_into('<H', data, 68, 0x8664)
    struct.pack_into('<H', data, 86, 0x2000)
    return bytes(data) + marker


class InstallSidecarAddonTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.game = self.root / 'game'
        self.package = self.root / 'package'
        self.game.mkdir(); self.package.mkdir()
        self.host = b'synthetic supported native host'
        (self.game / 'NFL2K5.exe').write_bytes(self.host)
        self.target = self.game / 'addons/franchise/franchise-addon.dll'
        self.spec = {'format': 1, 'supported_host_sha256': [sha(self.host)], 'dll_sha256': sha(dll(b'v1'))}
        (self.package / 'franchise-addon.dll').write_bytes(dll(b'v1'))
        self.write_spec()

    def write_spec(self):
        (self.package / 'addon-package.json').write_text(json.dumps(self.spec))

    def snapshot(self):
        return {str(p.relative_to(self.game)): p.read_bytes() for p in self.game.rglob('*') if p.is_file()}

    def test_install_upgrade_and_repeat_preserve_game_state_and_backup(self):
        for name, data in [('saves/FRANCHISE', b'save'), ('mods/active-pack.ini', b'SOFTDRINK\n'),
                           ('addons/franchise/enabled.ini', b'enabled=1\n')]:
            p = self.game / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
        untouched = self.snapshot()
        first = install(self.package, self.game)
        self.assertTrue(first['changed'])
        self.assertIsNone(first['previous_sha256'])
        (self.package / 'franchise-addon.dll').write_bytes(dll(b'v2'))
        self.spec['dll_sha256'] = sha(dll(b'v2')); self.write_spec()
        upgrade = install(self.package, self.game)
        self.assertEqual(upgrade['previous_sha256'], sha(dll(b'v1')))
        self.assertEqual(self.target.read_bytes(), dll(b'v2'))
        self.assertEqual(self.target.with_name('franchise-addon.previous-' + sha(dll(b'v1')) + '.dll').read_bytes(), dll(b'v1'))
        before = self.snapshot()
        self.assertFalse(install(self.package, self.game)['changed'])
        self.assertEqual(self.snapshot(), before)
        for name, data in untouched.items():
            self.assertEqual((self.game / name).read_bytes(), data)

    def test_unsupported_host_and_corrupt_payload_make_no_changes(self):
        for change in ('host', 'payload', 'architecture', 'not-dll'):
            with self.subTest(change=change):
                (self.game / 'NFL2K5.exe').write_bytes(self.host if change != 'host' else b'older repack')
                data = dll(b'v1')
                if change == 'payload': data += b'corruption'
                if change == 'architecture': data = data[:68] + b'\x4c\x01' + data[70:]
                if change == 'not-dll': data = data[:86] + b'\0\0' + data[88:]
                (self.package / 'franchise-addon.dll').write_bytes(data)
                self.spec['dll_sha256'] = sha(dll(b'v1')) if change == 'payload' else sha(data)
                self.write_spec(); before = self.snapshot()
                with self.assertRaises(ValueError): install(self.package, self.game)
                self.assertEqual(self.snapshot(), before)
                self.assertFalse((self.game / 'addons').exists())

    def test_failed_replace_preserves_installed_dll_and_selection(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(dll(b'old'))
        selection = self.target.parent / 'enabled.ini'; selection.write_bytes(b'enabled=0\n')
        with patch('tools.install_sidecar_addon.os.replace', side_effect=PermissionError('loaded DLL')):
            with self.assertRaises(PermissionError): install(self.package, self.game)
        self.assertEqual(self.target.read_bytes(), dll(b'old'))
        self.assertEqual(selection.read_bytes(), b'enabled=0\n')
        self.assertFalse(list(self.target.parent.glob('.addon-*')))

    def test_symlinked_addon_directory_is_rejected(self):
        outside = self.root / 'outside'; outside.mkdir()
        try: (self.game / 'addons').symlink_to(outside, target_is_directory=True)
        except OSError: self.skipTest('Symlink creation unavailable')
        with self.assertRaisesRegex(ValueError, 'symlinks'): install(self.package, self.game)
        self.assertEqual(list(outside.iterdir()), [])

    def test_install_does_not_activate_addon(self):
        install(self.package, self.game)
        self.assertFalse((self.target.parent / 'enabled.ini').exists())
