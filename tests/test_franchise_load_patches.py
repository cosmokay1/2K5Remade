"""All shared load interiors receive idempotent patches; no retail code fixture."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

class LoadPatchesTests(unittest.TestCase):
    def test_all_shared_exports_and_check_rejects_missing_checkpoint(self):
        spec=importlib.util.spec_from_file_location('load_patches',ROOT/'tools/apply-gen-patches.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.LENIENT=False
        module.PATCHES=[row for row in module.PATCHES if row[0].startswith('FRANCHISE_LOAD_')]
        self.assertEqual(len(module.PATCHES),20)
        functions=sorted({row[1] for row in module.PATCHES})
        self.assertEqual(functions,['sub_0016E1D0','sub_0016E290','sub_0016E350','sub_0016E3F0','sub_0016E540'])
        anchors=('loc_0016E6CA: ;','loc_0016E6DC: ;','loc_0016E70B: ;','loc_0016E81A: ;')
        with tempfile.TemporaryDirectory() as directory:
            module.GEN=directory;source=Path(directory)/'recomp_fixture.c'
            source.write_text('\n'.join('void '+fn+'(void)\n{\n'+'\n'.join(anchors)+'\n}\n' for fn in functions))
            with patch.object(sys,'argv',['patch-load']),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(module.main(),0)
            applied=source.read_bytes()
            for row in module.PATCHES:self.assertEqual(applied.count(module.marker(row[0]).encode()),1)
            with patch.object(sys,'argv',['patch-load']),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(module.main(),0)
            self.assertEqual(source.read_bytes(),applied)
            with patch.object(sys,'argv',['patch-load','--check']),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(module.main(),0)
            source.write_bytes(applied.replace(module.marker(module.PATCHES[0][0]).encode(),b'/* removed checkpoint */',1))
            # Remove its body too: an unmarked but exact existing patch is accepted.
            source.write_bytes(source.read_bytes().replace(module.PATCHES[0][4].strip().encode(),b'/* body absent */',1))
            with patch.object(sys,'argv',['patch-load','--check']),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):self.assertEqual(module.main(),1)

    def test_marked_body_is_checked(self):
        spec=importlib.util.spec_from_file_location('load_patches',ROOT/'tools/apply-gen-patches.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.LENIENT=False
        row=next(row for row in module.PATCHES if row[0].startswith('FRANCHISE_LOAD_'));module.PATCHES=[row]
        with tempfile.TemporaryDirectory() as directory:
            module.GEN=directory;source=Path(directory)/'recomp_fixture.c'
            source.write_text('void '+row[1]+'(void)\n{\n'+row[2]+'\n'+module.marker(row[0])+'\n/* tampered */\n}\n')
            with patch.object(sys,'argv',['patch-load','--check']),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):self.assertEqual(module.main(),1)
