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
                        'package-receipt.json', 'game.EXE', 'COM¹.dll', 'LPT²/data', 'com³.txt'):
                with self.subTest(path=bad):
                    manifest.write_text(json.dumps({'entrypoint': 'Game.exe', 'files': ['Game.exe', bad]}))
                    with self.assertRaises(ValueError):
                        package(root, manifest, output)
                    self.assertFalse(output.exists())

    def test_file_directory_collisions_and_receipt_descendants_reject_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'Game.exe').write_bytes(b'synthetic executable placeholder')
            manifest,output=root/'manifest.json',root/'candidate.zip'
            for files,reason in ((['Game.exe','game.EXE/data.txt'],'path collision'),
                    (['game.EXE/data.txt','Game.exe'],'path collision'),
                    (['Game.exe','lib/Bridge.dll','LIB/bridge.DLL/child'],'path collision'),
                    (['Game.exe','PACKAGE-RECEIPT.JSON/child'],'Reserved receipt'),
                    (['Game.exe','Assets/a','assets/b'],'consistent directory casing'),
                    *[(['Game.exe',prefix+digit+'.dll'],'Invalid Windows runtime path')
                      for prefix in ('COM','LPT') for digit in '¹²³']):
                with self.subTest(files=files):
                    manifest.write_text(json.dumps({'entrypoint':'Game.exe','files':files}))
                    with self.assertRaisesRegex(ValueError,reason):package(root,manifest,output)
                    self.assertFalse(output.exists())
            output.write_bytes(b'existing archive must survive invalid manifest')
            original=output.read_bytes()
            manifest.write_text(json.dumps({'entrypoint':'Game.exe','files':['Game.exe','game.exe/child']}))
            with self.assertRaisesRegex(ValueError,'path collision'):package(root,manifest,output)
            self.assertEqual(output.read_bytes(),original)

    def test_consistent_nested_runtime_files_preserve_archive_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'Game.exe').write_bytes(b'synthetic executable placeholder')
            (root/'runtime').mkdir()
            (root/'runtime'/'a.dll').write_bytes(b'synthetic dependency a')
            (root/'runtime'/'b.dll').write_bytes(b'synthetic dependency b')
            files=['Game.exe','runtime/a.dll','runtime/b.dll']
            manifest,output=root/'manifest.json',root/'candidate.zip'
            manifest.write_text(json.dumps({'entrypoint':'Game.exe','files':files}))
            receipt=package(root,manifest,output)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()),{'LLM-2K5/'+name for name in files}|{'LLM-2K5/package-receipt.json'})
                for name in files:
                    self.assertEqual(hashlib.sha256(archive.read('LLM-2K5/'+name)).hexdigest(),receipt['sha256'][name])
