"""Execute the production register-local patch wrapper on an authored stack."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class RecompPatchCallTests(unittest.TestCase):
    def test_nested_native_call_and_all_patch_exits(self):
        cc=shutil.which('cc')
        if not cc:self.skipTest('Native fixture requires C compiler')
        with tempfile.TemporaryDirectory() as directory:
            exe=Path(directory)/'patch-check'
            subprocess.run([cc,'-std=c11','-I'+str(ROOT/'src/recomp/gen'),'-I'+str(ROOT/'src'),str(ROOT/'tests/recomp_patch/check.c'),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True,capture_output=True,timeout=10)
