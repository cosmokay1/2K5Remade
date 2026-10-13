import json
from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks,ActiveContract
from franchise.cap import Ledger,Offer,Rejected
from franchise.store import FranchiseStore
from tools.create_franchise import create_from_file


class BootstrapCommandTests(unittest.TestCase):
    def config(self,player):
        return Ledger.from_opening(OpeningBooks(contracts=(ActiveContract(Offer(player,(10,),0),'synthetic roster'),)),
            cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={'p':(1,),'q':(1,)}).bootstrap_config()
    def bundle(self):
        return {'format':1,'source':'synthetic initialization fixture','seed':'fixture-world',
                'teams':{'a':self.config('p'),'b':self.config('q')}}

    def test_publish_verified_engine_state_and_never_overwrite_existing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source,destination=root/'input.json',root/'franchise.sqlite'
            source.write_text(json.dumps(self.bundle()))
            receipt=create_from_file(source,destination)
            self.assertEqual((receipt['teams'],receipt['players']),(2,2))
            self.assertFalse(receipt['game_runtime_verified'])
            store=FranchiseStore(destination)
            self.assertEqual(set(store.load_team('a')._actors),{'p','q'})
            from franchise.initialization import initial_actor
            self.assertEqual(store.load_team('a')._actors['p'],initial_actor('fixture-world','p'))
            self.assertEqual(store.load_team('b').charges[0],10)
            before=destination.read_bytes()
            with self.assertRaises(FileExistsError):create_from_file(source,destination)
            self.assertEqual(destination.read_bytes(),before)
            self.assertFalse(list(root.glob('.2k5-bootstrap-*')))

    def test_failed_creation_publishes_no_database_and_leaves_no_build_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source,destination=root/'input.json',root/'franchise.sqlite'
            bundle=self.bundle()
            bundle['teams']['b']=self.config('p')
            source.write_text(json.dumps(bundle))
            with self.assertRaises(Rejected):create_from_file(source,destination)
            self.assertFalse(destination.exists())
            self.assertFalse(list(root.glob('.2k5-bootstrap-*')))

    def test_duplicate_fields_and_boolean_version_reject_before_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source,destination=root/'input.json',root/'franchise.sqlite'
            for raw in ('{"format":1,"format":1}',json.dumps({**self.bundle(),'format':True})):
                source.write_text(raw)
                with self.assertRaises(ValueError):create_from_file(source,destination)
                self.assertFalse(destination.exists())

    def test_nonobject_config_rejects_and_concurrent_winner_is_preserved(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source,destination=root/'input.json',root/'franchise.sqlite'
            bundle=self.bundle()
            bundle['teams']['a']=list(bundle['teams']['a'].items())
            source.write_text(json.dumps(bundle))
            with self.assertRaises(ValueError):create_from_file(source,destination)
            source.write_text(json.dumps(self.bundle()))
            def concurrent_winner(_building,target):
                Path(target).write_bytes(b'concurrent winner must survive')
                raise FileExistsError('simulated competing publisher')
            with patch('tools.create_franchise.os.link',side_effect=concurrent_winner):
                with self.assertRaises(FileExistsError):create_from_file(source,destination)
            self.assertEqual(destination.read_bytes(),b'concurrent winner must survive')
            self.assertFalse(list(root.glob('.2k5-bootstrap-*')))

    def test_dangling_destination_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source,destination=root/'input.json',root/'franchise.sqlite'
            source.write_text(json.dumps(self.bundle()))
            try:
                destination.symlink_to(root/'absent.sqlite')
            except (OSError,NotImplementedError):
                self.skipTest('Symlink creation unavailable on this runner')
            with self.assertRaises(FileExistsError):create_from_file(source,destination)
            self.assertTrue(destination.is_symlink())
            self.assertFalse((root/'absent.sqlite').exists())
