from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from franchise.store import FranchiseStore,GenerationPreflightError
from tests import test_trade_store


class GenerationMigrationTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        fixture=test_trade_store.TradeStoreTests()
        self.store=fixture.setup_store(temp.name);fixture.trade(self.store)

    def version(self):
        with closing(sqlite3.connect(self.store.path)) as db:
            return db.execute('PRAGMA user_version').fetchone()[0]

    def test_checkpoint_backup_reopen_and_later_legacy_events(self):
        before=self.store.contract_generations('a')
        result=FranchiseStore.migrate_generations(self.store.path)
        self.assertEqual(result['target_database_version'],4)
        self.assertEqual(self.version(),4)
        self.assertEqual(hashlib.sha256(Path(result['backup_path']).read_bytes()).hexdigest(),result['backup_sha256'])
        with closing(sqlite3.connect(result['backup_path'])) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],3)
        reopened=FranchiseStore(self.store.path)
        self.assertEqual(reopened.contract_generations('a'),before)
        ledger=reopened.load_team('a')
        reopened.update_budget('a',cap=300,roster_reserve=0,expected_revision=ledger.revision)
        self.assertEqual(FranchiseStore(self.store.path).load_team('a').cap,300)
        self.assertEqual(self.version(),4)
        with self.assertRaises(ValueError):FranchiseStore.migrate_generations(self.store.path)

    def test_valid_json_reformat_of_old_event_rejected(self):
        FranchiseStore.migrate_generations(self.store.path)
        with closing(sqlite3.connect(self.store.path)) as db:
            event,payload=db.execute('SELECT id,payload FROM events ORDER BY id LIMIT 1').fetchone()
            db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(json.loads(payload),indent=2),event));db.commit()
        with self.assertRaisesRegex(ValueError,'source history changed'):self.store.load_team('a')

    def test_accounting_type_swap_and_duplicate_manifest_rejected(self):
        FranchiseStore.migrate_generations(self.store.path)
        with closing(sqlite3.connect(self.store.path)) as db:
            original=db.execute('SELECT manifest FROM generation_checkpoint').fetchone()[0]
            manifest=json.loads(original);manifest['teams']['a']['financial']['revision']=True
            db.execute('UPDATE generation_checkpoint SET manifest=?',(json.dumps(manifest),));db.commit()
        with self.assertRaises(ValueError):self.store.load_team('a')
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute('UPDATE generation_checkpoint SET manifest=?',(original[:-1]+',"format":1}',));db.commit()
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.store.load_team('a')

    def test_failed_checkpoint_install_rolls_back_and_keeps_backup(self):
        original=Path(self.store.path).read_bytes()
        original_validator=FranchiseStore._validate_generation_checkpoint
        def fail_install(instance,db):
            if db.execute('PRAGMA user_version').fetchone()[0]==4:
                raise ValueError('injected')
            return original_validator(instance,db)
        with patch.object(FranchiseStore,'_validate_generation_checkpoint',new=fail_install):
            with self.assertRaises(GenerationPreflightError) as caught:
                FranchiseStore.migrate_generations(self.store.path)
        self.assertEqual(self.version(),3)
        self.assertEqual(Path(self.store.path).read_bytes(),original)
        self.assertTrue(Path(caught.exception.backup_path).is_file())
        with closing(sqlite3.connect(self.store.path)) as db:
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='generation_checkpoint'").fetchone())

    def test_corrupt_checkpoint_blocks_bootstrap_write_and_constructor(self):
        from franchise.books import OpeningBooks
        from franchise.cap import Ledger
        FranchiseStore.migrate_generations(self.store.path)
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute("UPDATE generation_checkpoint SET manifest='{}'");db.commit()
        original=Path(self.store.path).read_bytes()
        ledger=Ledger.from_opening(OpeningBooks(),cap=200,roster_reserve=0,max_bonus_years=5,veteran_minimums={})
        with self.assertRaises(ValueError):self.store.create_team('new',ledger)
        self.assertEqual(Path(self.store.path).read_bytes(),original)
        with self.assertRaises(ValueError):FranchiseStore(self.store.path)
        self.assertEqual(Path(self.store.path).read_bytes(),original)

    def test_missing_format_four_checkpoint_constructor_cannot_repair(self):
        FranchiseStore.migrate_generations(self.store.path)
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute('DROP TABLE generation_checkpoint');db.commit()
        original=Path(self.store.path).read_bytes()
        with self.assertRaises((ValueError,sqlite3.Error)):FranchiseStore(self.store.path)
        self.assertEqual(Path(self.store.path).read_bytes(),original)

    def test_later_release_payment_and_new_team_signing_preserve_checkpoint_history(self):
        from franchise.books import OpeningBooks
        from franchise.cap import Ledger,Offer
        from tests import test_releases
        FranchiseStore.migrate_generations(self.store.path)
        plan=test_releases.PreseasonReleaseTests().plan()
        buyer=self.store.load_team('b')
        self.store.release_preseason_veteran('b','later-release','v',scope=plan.scope,discount=plan.discount,
            payment_year_offsets=(0,1,2),expected_revision=buyer.revision,access_check=lambda:None)
        released=self.store.load_team('b')
        self.store.record_payment('b','later-payment','contract:v',2,
            expected_cash_revision=released.cash_snapshot()['revision'],source='synthetic settlement',
            payment_reference='later receipt',component='base:1')
        self.store.create_team('d',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
        self.store.initialize_cash('d',(),source='synthetic later team cash')
        self.store.sign('d','later-sign',Offer('v',(10,10,10),0),1)
        reopened=FranchiseStore(self.store.path)
        debt=reopened.contract_generations('b')['generations'][0]
        self.assertEqual(debt['status'],'released')
        self.assertEqual((debt['cash_obligation']['amount'],debt['cash_obligation']['paid']),(30,2))
        self.assertEqual(reopened.load_team('d').financial_snapshot()['signed_players'],['v'])
        self.assertEqual(self.version(),4)
