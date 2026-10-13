import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tools.save_diff import compare,compare_controlled


class ControlledSaveDiffTests(unittest.TestCase):
    def test_control_bookkeeping_and_overlap_are_reported_without_discarding_transaction(self):
        before,after,control=b'abcdefghi',b'AbXYefGhI',b'aBcDefghi'
        report=compare_controlled(before,after,control)
        original=compare(before,after)
        self.assertEqual({key:report[key] for key in original},original)
        self.assertEqual(report['changed_bytes'],5)
        self.assertEqual(report['control_changed_bytes'],2)
        self.assertEqual(report['transaction_only_changed_bytes'],4)
        self.assertEqual(report['control_overlap_changed_bytes'],1)
        self.assertEqual([(s['offset'],s['length']) for s in report['spans']],[(0,1),(2,2),(6,1),(8,1)])
        self.assertEqual([(s['offset'],s['length']) for s in report['transaction_only_spans']],[(0,1),(2,1),(6,1),(8,1)])
        self.assertEqual(report['control_overlap_spans'],[{'offset':3,'offset_hex':'0x3','length':1,
            'before_hex':'64','after_hex':'59','control_after_hex':'44'}])
        self.assertEqual([(s['offset'],s['length']) for s in report['control_spans']],[(1,1),(3,1)])
        for key,raw in (('before_sha256',before),('after_sha256',after),('control_after_sha256',control)):
            self.assertEqual(report[key],hashlib.sha256(raw).hexdigest())

    def test_identical_control_overlap_and_no_transaction_edge_cases(self):
        report=compare_controlled(b'ab',b'XY',b'XY')
        self.assertEqual(report['transaction_only_changed_bytes'],0)
        self.assertEqual(report['control_overlap_changed_bytes'],2)
        self.assertEqual(report['control_overlap_spans'][0]['after_hex'],'5859')
        report=compare_controlled(b'ab',b'ab',b'XY')
        self.assertEqual(report['spans'],[])
        self.assertEqual(report['transaction_only_spans'],[])
        self.assertEqual(report['control_overlap_spans'],[])
        self.assertEqual(report['control_changed_bytes'],2)
        report=compare_controlled(b'ab',b'XY',b'ab')
        self.assertEqual(report['transaction_only_changed_bytes'],2)
        self.assertEqual(report['control_overlap_spans'],[])

    def test_matching_raw_sizes_and_zip_checks_apply_to_all_three_inputs(self):
        for inputs in ((b'ab',b'XY',b'a'),(b'ab',b'XY',b''),
                       (b'abcd',b'WXYZ',b'PK\x03\x04'),
                       (b'PK\x03\x04',b'abcd',b'efgh'),
                       (b'abcd',b'PK\x03\x04',b'efgh')):
            with self.subTest(inputs=inputs),self.assertRaises(ValueError):
                compare_controlled(*inputs)

    def test_cli_optional_control_report_preserves_default_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            before,after,control=(root/name for name in ('before.dat','after.dat','control.dat'))
            before.write_bytes(b'ab');after.write_bytes(b'XY');control.write_bytes(b'aY')
            command=[sys.executable,'-m','tools.save_diff',str(before),str(after)]
            default=subprocess.run(command,capture_output=True,text=True,check=True)
            controlled=subprocess.run(command+['--control-after',str(control)],capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(default.stdout),compare(b'ab',b'XY'))
            self.assertEqual(json.loads(controlled.stdout),compare_controlled(b'ab',b'XY',b'aY'))
