import json
from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks,ActiveContract
from franchise.cap import Ledger,Offer,Rejected
from franchise.store import FranchiseStore
from franchise.legacy_contracts import LegacyContract
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

    def test_declared_cash_and_all_registered_personalities_survive_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source,destination=root/'input.json',root/'franchise.sqlite'
            legacy=LegacyContract('legacy',10,4,2,6,2,'synthetic preserved terms')
            ledger=Ledger.from_opening(OpeningBooks(legacy_contracts=(legacy,)),cap=1000000,
                roster_reserve=0,max_bonus_years=5,veteran_minimums={},
                observed_player_ids=frozenset({'observed'}),observed_player_source='synthetic identity source')
            bundle=self.bundle()
            bundle['teams']['b']=ledger.bootstrap_config()
            bundle['cash']={
                'a':{'source':'synthetic complete payments','unknown_legacy_players':[],
                     'records':[{'obligation_id':'contract:p','player_id':'p','amount':10,'paid':3,
                                 'source':'synthetic payment receipt'}]},
                'b':{'source':'synthetic explicit unavailable legacy cash',
                     'unknown_legacy_players':['legacy'],'records':[]}}
            source.write_text(json.dumps(bundle))
            receipt=create_from_file(source,destination)
            self.assertEqual(receipt['players'],4)
            self.assertEqual(receipt['cash_initialized_teams'],2)
            reopened=FranchiseStore(destination)
            self.assertEqual(reopened.load_team('a').cash_snapshot()['unpaid_total'],7)
            b=reopened.load_team('b')
            self.assertEqual(set(b._actors),{'legacy','observed'})
            from franchise.initialization import initial_actor
            self.assertEqual(b._actors['observed'],initial_actor('fixture-world','observed'))
            self.assertEqual(b.charges,legacy.charges())
            self.assertIsNone(b.cash_snapshot()['unpaid_total'])
            self.assertEqual(b.cash_snapshot()['unknown_legacy_players'],['legacy'])
            with self.assertRaises(Rejected):b.preview_offer(Offer('observed',(1,),0),b.revision)
            self.assertFalse(list(root.glob('.2k5-bootstrap-*')))

    def test_cash_failure_after_first_team_does_not_publish_partial_franchise(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source,destination=root/'input.json',root/'franchise.sqlite'
            bundle=self.bundle()
            bundle['cash']={team:{'source':'synthetic cash','unknown_legacy_players':[],
                'records':[{'obligation_id':'contract:'+player,'player_id':player,'amount':amount,
                            'paid':0,'source':'synthetic cash'}]}
                for team,player,amount in (('a','p',10),('b','q',11))}
            source.write_text(json.dumps(bundle))
            with self.assertRaisesRegex(ValueError,'reconcile'):create_from_file(source,destination)
            self.assertFalse(destination.exists())
            self.assertFalse(list(root.glob('.2k5-bootstrap-*')))

    def test_cash_import_requires_exact_team_coverage_and_explicit_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source,destination=root/'input.json',root/'franchise.sqlite'
            complete={team:{'source':'synthetic cash','unknown_legacy_players':[],'records':[]}
                      for team in ('a','b')}
            for cash in (None,{}, {'a':complete['a']}, {**complete,'extra':complete['a']},
                         {**complete,'b':{'source':'synthetic cash','records':[]}}):
                source.write_text(json.dumps({**self.bundle(),'cash':cash}))
                with self.assertRaises(ValueError):create_from_file(source,destination)
                self.assertFalse(destination.exists())
                self.assertFalse(list(root.glob('.2k5-bootstrap-*')))
