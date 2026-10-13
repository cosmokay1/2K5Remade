import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from tools.package_steamdeck import package


class DeckPackageTests(unittest.TestCase):
    def test_archive_receipt_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = b'fixture, not a runnable executable' * 50000
            (root / 'Game.exe').write_bytes(data)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'entrypoint': 'Game.exe', 'files': ['Game.exe']}))
            output = root / 'candidate.zip'
            receipt = package(root, manifest, output)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.read('LLM-2K5/Game.exe'), data)
                self.assertEqual(json.loads(archive.read('LLM-2K5/package-receipt.json')), receipt)
            self.assertEqual(receipt['sha256']['Game.exe'], hashlib.sha256(data).hexdigest())
            original = output.read_bytes()
            with self.assertRaises(FileExistsError):
                package(root, manifest, output)
            self.assertEqual(output.read_bytes(), original)

    def test_invalid_paths_leave_no_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'Game.exe').write_bytes(b'fixture')
            manifest, output = root / 'manifest.json', root / 'candidate.zip'
            for bad in ('../outside', '/absolute', 'a//b', 'a/./b', 'C:drive', 'a\\b',
                        '.env', 'secret.key', 'franchise.sqlite', 'CON.dll', 'a.',
                        'package-receipt.json', 'game.EXE'):
                with self.subTest(path=bad):
                    manifest.write_text(json.dumps({'entrypoint': 'Game.exe', 'files': ['Game.exe', bad]}))
                    with self.assertRaises(ValueError):
                        package(root, manifest, output)
                    self.assertFalse(output.exists())
