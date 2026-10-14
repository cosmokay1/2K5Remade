from contextlib import closing
from pathlib import Path
import hashlib
import json
import os
import sqlite3
import stat
import tempfile
import unittest
from unittest.mock import patch
from franchise.store import FranchiseStore, GenerationPreflightError
from tests import test_trade_store


class GenerationPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        fixture=test_trade_store.TradeStoreTests()
        self.store=fixture.setup_store(self.temp.name)
        fixture.trade(self.store)

    def tables(self, path):
        with closing(sqlite3.connect(path)) as db:
            names=[name for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            return {name:db.execute('SELECT * FROM "'+name+'" ORDER BY rowid').fetchall() for name in names}

    def assert_unlocked(self):
        with closing(sqlite3.connect(self.store.path,timeout=0)) as db:
            db.execute('BEGIN IMMEDIATE')
            db.rollback()

    def test_private_consistent_backup_and_full_replay_without_source_or_format_changes(self):
        original=Path(self.store.path).read_bytes()
        tables=self.tables(self.store.path)
        before={team:(self.store.load_team(team).financial_snapshot(),self.store.load_team(team).cash_snapshot())
                for team in ('a','b','c')}
        result=FranchiseStore.prepare_generation_migration(self.store.path)
        self.assertEqual((result['format'],result['status'],result['source_database_version']),(1,'preflight_only',3))
        backup=Path(result['backup_path'])
        self.assertEqual(backup.parent,self.root)
        self.assertIn('.generation-backup-',backup.name)
        self.assertEqual(hashlib.sha256(backup.read_bytes()).hexdigest(),result['backup_sha256'])
        if os.name=='posix':
            self.assertEqual(stat.S_IMODE(backup.stat().st_mode),0o600)
        self.assertEqual(self.tables(backup),tables)
        self.assertEqual(Path(self.store.path).read_bytes(),original)
        for team,(financial,cash) in before.items():
            self.assertEqual(result['teams'][team]['financial'],financial)
            self.assertEqual(result['teams'][team]['cash'],cash)
            self.assertEqual(result['teams'][team]['contracts'],self.store.contract_generations(team))
        with closing(sqlite3.connect(backup)) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],3)
        self.assert_unlocked()

    def test_failed_replay_preserves_consistent_backup_and_unchanged_corrupt_source(self):
        with closing(sqlite3.connect(self.store.path)) as db:
            row=db.execute("SELECT id,payload FROM events WHERE kind='trade_out'").fetchone()
            corrupted=json.loads(row[1]);corrupted['posting']['cap']=999
            db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(corrupted),row[0]));db.commit()
        original=Path(self.store.path).read_bytes()
        tables=self.tables(self.store.path)
        with self.assertRaises(GenerationPreflightError) as caught:
            FranchiseStore.prepare_generation_migration(self.store.path)
        backup=Path(caught.exception.backup_path)
        self.assertTrue(backup.is_file())
        self.assertIn(str(backup),str(caught.exception))
        self.assertEqual(hashlib.sha256(backup.read_bytes()).hexdigest(),caught.exception.backup_sha256)
        self.assertEqual(self.tables(backup),tables)
        self.assertEqual(Path(self.store.path).read_bytes(),original)
        with closing(sqlite3.connect(self.store.path)) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],3)
        self.assert_unlocked()

    def test_missing_and_wrong_version_sources_do_not_create_or_relabel(self):
        missing=self.root/'missing.sqlite'
        with self.assertRaises(ValueError):
            FranchiseStore.prepare_generation_migration(missing)
        self.assertFalse(missing.exists())
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute('PRAGMA user_version=2');db.commit()
        original=Path(self.store.path).read_bytes()
        with self.assertRaisesRegex(ValueError,'only database format 3'):
            FranchiseStore.prepare_generation_migration(self.store.path)
        self.assertEqual(Path(self.store.path).read_bytes(),original)
        self.assertEqual(list(self.root.glob('*.generation-backup-*.sqlite')),[])
        self.assert_unlocked()

    def test_backup_open_failure_releases_source_reservation_without_partial_backup(self):
        original=Path(self.store.path).read_bytes()
        with patch.object(Path,'open',side_effect=PermissionError('synthetic backup creation failure')):
            with self.assertRaises(PermissionError):
                FranchiseStore.prepare_generation_migration(self.store.path)
        self.assertEqual(Path(self.store.path).read_bytes(),original)
        self.assertEqual(list(self.root.glob('*.generation-backup-*.sqlite')),[])
        self.assert_unlocked()

    def test_existing_only_connection_refuses_raced_missing_path(self):
        source=Path(self.store.path)
        original_is_file=Path.is_file
        def raced(path):
            result=original_is_file(path)
            if path==source:
                source.unlink()
            return result
        with patch.object(Path,'is_file',raced):
            with self.assertRaises(sqlite3.OperationalError):
                FranchiseStore.prepare_generation_migration(source)
        self.assertFalse(source.exists())
        self.assertEqual(list(self.root.glob('*.generation-backup-*.sqlite')),[])

    def test_league_validation_holds_one_write_reservation_and_uses_no_nested_public_reads(self):
        original=FranchiseStore._load_teams
        observed=[]
        def verify(instance,db,teams):
            observed.append(tuple(teams))
            with closing(sqlite3.connect(self.store.path,timeout=0)) as contender:
                with self.assertRaisesRegex(sqlite3.OperationalError,'locked'):
                    contender.execute('BEGIN IMMEDIATE')
            return original(instance,db,teams)
        with patch.object(FranchiseStore,'_load_teams',verify), \
             patch.object(FranchiseStore,'contract_generations',side_effect=AssertionError('Nested public read forbidden')):
            result=FranchiseStore.prepare_generation_migration(self.store.path)
        self.assertEqual(observed,[('a','b','c')])
        self.assertEqual(set(result['teams']),{'a','b','c'})
        self.assert_unlocked()

    def test_orphan_ownership_and_events_fail_after_preserving_backup(self):
        scenarios=(('ownership',"INSERT INTO ownership VALUES ('orphan','missing-team')"),
                   ('events',"INSERT INTO events (team_id,request_key,kind,payload) VALUES ('missing-team','orphan','budget','{}')"))
        for table,statement in scenarios:
            with self.subTest(table=table):
                with closing(sqlite3.connect(self.store.path)) as db:
                    db.execute(statement);db.commit()
                original=Path(self.store.path).read_bytes()
                with self.assertRaises(GenerationPreflightError) as caught:
                    FranchiseStore.prepare_generation_migration(self.store.path)
                self.assertIn('foreign-key',str(caught.exception.__cause__))
                self.assertEqual(self.tables(caught.exception.backup_path),self.tables(self.store.path))
                self.assertEqual(Path(self.store.path).read_bytes(),original)
                with closing(sqlite3.connect(self.store.path)) as db:
                    db.execute("DELETE FROM "+table+" WHERE team_id='missing-team'");db.commit()
                self.assert_unlocked()

    def test_every_unused_draft_order_is_parsed_and_identity_columns_must_match(self):
        valid={'draft_id':'unused','league_year':2026,'source':'synthetic unpicked order',
               'slots':[{'overall_pick':1,'draft_round':1,'team_id':'a'}],'player_ids':['prospect']}
        cases=(('unused',2026,{}),('different',2026,valid),('unused',2027,valid),('unused','broken',valid))
        for draft_id,year,config in cases:
            with self.subTest(draft_id=draft_id,year=year,config=config):
                with closing(sqlite3.connect(self.store.path)) as db:
                    db.execute('INSERT INTO draft_orders VALUES (?,?,?)',(draft_id,year,json.dumps(config)));db.commit()
                original=Path(self.store.path).read_bytes()
                with self.assertRaises(GenerationPreflightError) as caught:
                    FranchiseStore.prepare_generation_migration(self.store.path)
                self.assertTrue(Path(caught.exception.backup_path).is_file())
                self.assertEqual(Path(self.store.path).read_bytes(),original)
                self.assertEqual(self.tables(caught.exception.backup_path),self.tables(self.store.path))
                with closing(sqlite3.connect(self.store.path)) as db:
                    db.execute('DELETE FROM draft_orders');db.commit()
                self.assert_unlocked()

    def test_empty_league_still_validates_global_personality_origin(self):
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'empty.sqlite')
            with closing(sqlite3.connect(store.path)) as db:
                db.execute("INSERT INTO franchise_metadata VALUES ('personality-origin','{}')");db.commit()
            original=Path(store.path).read_bytes()
            with self.assertRaises(GenerationPreflightError) as caught:
                FranchiseStore.prepare_generation_migration(store.path)
            self.assertIn('personality origin',str(caught.exception.__cause__))
            self.assertEqual(Path(store.path).read_bytes(),original)
            self.assertEqual(self.tables(caught.exception.backup_path),self.tables(store.path))
