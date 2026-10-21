import hashlib
import hmac
import json
from pathlib import Path
import tempfile
import unittest

from franchise.opening_native import verify
from franchise.store import FranchiseStore
from tests import test_build_week1_opening as fixtures
from tools.prepare_week1_franchise import prepare


class FreshCopyPreparationTests(unittest.TestCase):
    def inputs(self, root, name='W1CAP'):
        fixture=fixtures.OpeningBundleTests();self.addCleanup(fixture.doCleanups)
        payload,roster,fit,assembly,charges,book,archive=fixture.inputs()
        container=root/'source';container.mkdir()
        (container/'SAVEGAME.DAT').write_bytes(payload)
        (container/'TYPE').write_bytes('FXG\0'.encode('utf-16le'))
        (container/'SaveMeta.xbx').write_bytes(('Name='+name+'\r\n').encode('utf-16'))
        (container/'EXTRA').write_bytes(hmac.digest(bytes(16),payload,'sha1'))
        (container/'.nfl2k5-save.ini').write_text('authored fixture manifest\n')
        roster_path=root/'roster.dat';roster_path.write_bytes(roster)
        paths=[]
        for label,value in zip(('fit','assembly','charges','book','archive'),(fit,assembly,charges,book,dict(rows=archive))):
            path=root/(label+'.json');path.write_text(json.dumps(value));paths.append(path)
        return [container/'SAVEGAME.DAT',roster_path,*paths,root/'prepared']

    def test_copy_has_bound_books_and_signature_without_touching_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            args=self.inputs(Path(temporary));source=args[0].parent
            before={p.name:p.read_bytes() for p in source.iterdir()}
            receipt=prepare(*args);output=args[-1]
            payload=(output/'save/SAVEGAME.DAT').read_bytes()
            self.assertEqual((output/'save/EXTRA').read_bytes(),hmac.digest(bytes(16),payload,'sha1'))
            self.assertEqual(receipt['output_save_sha256'],hashlib.sha256(payload).hexdigest())
            self.assertFalse(receipt['installed']);self.assertFalse(receipt['signing_authorized'])
            self.assertEqual({p.name:p.read_bytes() for p in source.iterdir()},before)
            store=FranchiseStore(output/'franchise.sqlite')
            with store._connection() as db:self.assertTrue(verify(store,db,payload))
            with self.assertRaises(ValueError):prepare(*args)

    def test_mynfl1_and_bad_signature_are_refused_before_output_creation(self):
        for name in ('MyNFL1','W1CAP'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as temporary:
                args=self.inputs(Path(temporary),name)
                if name=='W1CAP':(args[0].parent/'EXTRA').write_bytes(bytes(20))
                with self.assertRaises(ValueError):prepare(*args)
                self.assertFalse(args[-1].exists())
