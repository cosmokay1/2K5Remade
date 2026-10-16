"""Compile the owned cap patch around a minimal native payroll assignment."""
import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


class NativeCapHookTests(unittest.TestCase):
    def test_recalculation_patch_is_idempotent_and_controls_the_original_store(self):
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('cap_payroll_patch',root/'tools/apply-gen-patches.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.PATCHES=[row for row in module.PATCHES if row[0]=='FRANCHISE_CAP_PAYROLL'];module.LENIENT=False
        self.assertEqual(len(module.PATCHES),1)
        with tempfile.TemporaryDirectory() as temporary:
            module.GEN=temporary;source=Path(temporary)/'recomp_fixture.c'
            source.write_text('void sub_000C3F00(void)\n{\n    MEM32(ebp + 0x124) = eax;\n}\n')
            with patch.object(sys,'argv',['cap-patch']),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(module.main(),0)
            once=source.read_text()
            with patch.object(sys,'argv',['cap-patch','--check']),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(module.main(),0)
            self.assertEqual(source.read_text(),once)
            compiler=shutil.which('cc')
            if compiler is None:self.skipTest('C compiler unavailable; source patch checks passed')
            source.write_text('''#include <stdint.h>
static uint32_t eax,ebp,payroll,answer,queried_team;
#define MEM32(address) payroll
uint32_t nfl2k5_franchise_cap_payroll(uint32_t team,uint32_t computed){queried_team=team;return answer?answer:computed;}
'''+once+'''
int main(void){
 ebp=0x1234;eax=2000;answer=3658;sub_000C3F00();
 if(payroll!=3658 || eax!=3658 || queried_team!=ebp)return 1;
 eax=2000;sub_000C3F00();if(payroll!=3658)return 2;
 answer=0;eax=2000;sub_000C3F00();if(payroll!=2000)return 3;
 answer=INT32_MAX;eax=2000;sub_000C3F00();if(payroll!=INT32_MAX)return 4;
 return 0;
}
''')
            executable=Path(temporary)/'cap-patch-check'
            subprocess.run([compiler,'-std=c11',str(source),'-o',str(executable)],check=True,capture_output=True)
            subprocess.run([str(executable)],check=True,capture_output=True,timeout=10)
