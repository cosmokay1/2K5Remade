"""Authored generated functions prove old stage-ambiguous caches upgrade safely."""
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class SigningPatchUpgradeTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('signing_patch_fixture',Path(__file__).resolve().parents[1]/'tools/apply-gen-patches.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.module.PATCHES=[row for row in self.module.PATCHES if row[0] in ('FRANCHISE_SIGN_HOLD_JUDGMENT','FRANCHISE_SIGN_HOLD_COMMIT')]
        self.module.LENIENT=False
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.module.GEN=directory.name;self.path=Path(directory.name)/'recomp_authored.c'

    def source(self,kind='fresh',newline='\n'):
        lines=['void sub_00323D80(void)','{']
        for pid,_,anchor,_,code in self.module.PATCHES:
            lines.append(anchor)
            if kind!='fresh':
                lines.append('    '+self.module.marker(pid))
                if kind=='old': body='{ extern int nfl2k5_franchise_hold_signing(uint32_t); if(nfl2k5_franchise_hold_signing(esi)) goto loc_00323E99; }'
                elif kind=='custom' and pid.endswith('JUDGMENT'): body='/* user modified gate */'
                else: body=code.strip()
                lines.append('    '+body)
        lines+=['}','']
        self.path.write_bytes(newline.join(lines).encode())

    def run_patch(self,check=False):
        with patch.object(self.module.sys,'argv',['apply-gen-patches.py']+(['--check'] if check else [])),redirect_stdout(StringIO()),redirect_stderr(StringIO()):
            return self.module.main()

    def assert_current(self):
        text=self.path.read_text()
        self.assertIn('hold_signing_at(1u, esi)',text)
        self.assertIn('hold_signing_at(2u, esi)',text)
        self.assertNotIn('hold_signing(esi)',text)
        for row in self.module.PATCHES:self.assertEqual(text.count(self.module.marker(row[0])),1)

    def test_fresh_patch_and_repeat_are_stage_specific_and_idempotent(self):
        self.source();self.assertEqual(self.run_patch(),0);self.assert_current()
        before=self.path.read_bytes()
        self.assertEqual(self.run_patch(True),0);self.assertEqual(self.run_patch(),0)
        self.assertEqual(self.path.read_bytes(),before)

    def test_recognized_v1_marker_requires_upgrade_and_does_not_mask_old_code(self):
        self.source('old');before=self.path.read_bytes()
        self.assertEqual(self.run_patch(True),1);self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(self.run_patch(),0);self.assert_current();self.assertEqual(self.run_patch(True),0)

    def test_unknown_edited_body_fails_without_replacing_user_code(self):
        self.source('custom');before=self.path.read_bytes()
        self.assertEqual(self.run_patch(),1);self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(self.run_patch(True),1);self.assertEqual(self.path.read_bytes(),before)

    def test_old_windows_cache_keeps_crlf_during_upgrade(self):
        self.source('old','\r\n');self.assertEqual(self.run_patch(),0);self.assert_current()
        data=self.path.read_bytes()
        self.assertNotIn(b'\n',data.replace(b'\r\n',b''))


class CPUSigningPatchUpgradeTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('cpu_upgrade_fixture',Path(__file__).resolve().parents[1]/'tools/apply-gen-patches.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.module.PATCHES=[row for row in self.module.PATCHES if row[0]=='FRANCHISE_SIGN_CPU_HOLD']
        self.module.LENIENT=False
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.module.GEN=directory.name;self.path=Path(directory.name)/'recomp_authored.c'
        self.old='{ extern int nfl2k5_franchise_hold_signing_at(uint32_t, uint32_t); extern int nfl2k5_franchise_signing_was_held(uint32_t); if(nfl2k5_franchise_hold_signing_at(2u, esi)) { nfl2k5_franchise_signing_was_held(0); goto loc_00324169; } }'

    def source(self,body=None,newline='\n',anchor=True):
        text=['void sub_00324060(void)','{']
        if anchor:text+=['loc_00324072: ;','    /* dispatch */']
        text+=['loc_00324088: ;','    '+self.module.marker('FRANCHISE_SIGN_CPU_HOLD'),
               '    '+(self.old if body is None else body),'    /* original accepted branch */',
               'loc_00324173: ;','    /* original cleanup */','}','']
        self.path.write_bytes(newline.join(text).encode())

    def run_patch(self,check=False):
        with patch.object(self.module.sys,'argv',['apply-gen-patches.py']+(['--check'] if check else [])),redirect_stdout(StringIO()),redirect_stderr(StringIO()):
            return self.module.main()

    def test_recognized_old_gate_moves_before_dispatch_and_is_idempotent(self):
        self.source();before=self.path.read_bytes()
        self.assertEqual(self.run_patch(True),1);self.assertEqual(before,self.path.read_bytes())
        self.assertEqual(self.run_patch(),0)
        text=self.path.read_text()
        self.assertLess(text.index(self.module.marker('FRANCHISE_SIGN_CPU_HOLD')),text.index('loc_00324088: ;'))
        self.assertIn('hold_signing_at(2u, 0)',text);self.assertIn('goto loc_00324173;',text)
        self.assertNotIn(self.old,text)
        self.assertEqual(text.count(self.module.marker('FRANCHISE_SIGN_CPU_HOLD')),1)
        upgraded=self.path.read_bytes()
        self.assertEqual(self.run_patch(True),0);self.assertEqual(self.run_patch(),0)
        self.assertEqual(upgraded,self.path.read_bytes())

    def test_custom_body_wrong_location_or_missing_anchor_never_overwrites(self):
        for body,anchor in [('/* user gate */',True),(self.module.PATCHES[0][4].strip(),True),(None,False)]:
            with self.subTest(body=body,anchor=anchor):
                self.source(body,anchor=anchor);before=self.path.read_bytes()
                self.assertEqual(self.run_patch(),1);self.assertEqual(before,self.path.read_bytes())

    def test_windows_cache_preserves_crlf_during_relocation(self):
        self.source(newline='\r\n');self.assertEqual(self.run_patch(),0)
        self.assertNotIn(b'\n',self.path.read_bytes().replace(b'\r\n',b''))
