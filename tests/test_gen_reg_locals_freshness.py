"""Direct CMake builds must not silently compile a pre-patch locals copy."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class GeneratedLocalsFreshnessTests(unittest.TestCase):
    def test_check_detects_missing_payroll_hook_without_rewriting(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('reg_locals', root/'tools/gen-reg-locals.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/'gen', Path(directory)/'locals'
            source.mkdir()
            module.GEN, module.OUT = str(source), str(output)
            original = ('#define RECOMP_GENERATED_CODE\nvoid sub_000C3F00(void)\n{\n'
                        '    MEM32(ebp + 0x124) = eax;\n    return;\n}\n')
            path = source/'recomp_0005.c'
            path.write_text(original)
            with contextlib.redirect_stdout(io.StringIO()):
                with patch.object(module.sys, 'argv', ['gen-reg-locals', '--check']):
                    self.assertEqual(module.main(), 1)
                    self.assertFalse(output.exists())
                with patch.object(module.sys, 'argv', ['gen-reg-locals']):
                    self.assertEqual(module.main(), 0)
                old = (output/path.name).read_bytes()
                path.write_text(original.replace('    MEM32',
                    '    /* NFL2K5-GENPATCH:FRANCHISE_CAP_PAYROLL */\n'
                    '    { extern uint32_t nfl2k5_franchise_cap_payroll(uint32_t,uint32_t); '
                    'eax=nfl2k5_franchise_cap_payroll(ebp,eax); }\n    MEM32'))
                with patch.object(module.sys, 'argv', ['gen-reg-locals', '--check']):
                    self.assertEqual(module.main(), 1)
                    self.assertEqual((output/path.name).read_bytes(), old)
                with patch.object(module.sys, 'argv', ['gen-reg-locals']):
                    self.assertEqual(module.main(), 0)
                current = (output/path.name).read_bytes()
                self.assertIn(b'nfl2k5_franchise_cap_payroll', current)
                self.assertIn(b'recomp_patch_begin.h', current)
                with patch.object(module.sys, 'argv', ['gen-reg-locals', '--check']):
                    self.assertEqual(module.main(), 0)
                    self.assertEqual((output/path.name).read_bytes(), current)
                    (output/'obsolete.c').write_text('old')
                    self.assertEqual(module.main(), 1)
                    self.assertTrue((output/'obsolete.c').exists())
