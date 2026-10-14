import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger
from franchise.store import FranchiseStore


class GenerationPreflightCliTests(unittest.TestCase):
    def run_cli(self,path):
        return subprocess.run([sys.executable,'-m','tools.prepare_generation_migration',str(path)],
            cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=20)

    def test_cli_reports_backup_for_existing_franchise_without_advancing_format(self):
        with tempfile.TemporaryDirectory(prefix='generation CLI ') as directory:
            path=Path(directory)/'source with spaces.sqlite'
            store=FranchiseStore(path)
            store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
                max_bonus_years=5,veteran_minimums={}))
            before=store.load_team('a').financial_snapshot()
            result=self.run_cli(path)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)
            self.assertEqual(report['status'],'preflight_only')
            self.assertEqual(report['source_database_version'],3)
            backup=Path(report['backup_path'])
            self.assertEqual(hashlib.sha256(backup.read_bytes()).hexdigest(),report['backup_sha256'])
            self.assertEqual(report['teams']['a']['financial'],before)
            self.assertEqual(store.load_team('a').financial_snapshot(),before)

    def test_missing_source_fails_without_creating_database_or_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'missing.sqlite'
            result=self.run_cli(path)
            self.assertEqual(result.returncode,2)
            self.assertEqual(list(Path(directory).iterdir()),[])
