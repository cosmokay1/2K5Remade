from contextlib import closing
from fractions import Fraction
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from franchise.cap import Ledger, Offer, Rejected
from franchise.rookie import RookieScale
from franchise.store import FranchiseStore


class PostingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "franchise.sqlite"
        self.store = FranchiseStore(self.path)
        self.store.create_team("a", Ledger(cap=10, existing_charges=(0,), roster_reserve=0,
            max_bonus_years=5, veteran_minimums={},
            rookies={"r": RookieScale(1, (1,) * 4, 1, 10, 40)},
            rookie_year_one_allocation=10, rookie_total_allocation=40))

    def sign(self):
        return self.store.sign("a", "one", Offer("r", (1,) * 4, 1), 0)

    def test_one_bonus_fraction_drives_team_and_rookie_pool(self):
        self.sign()
        ledger = FranchiseStore(self.path).load_team("a")
        self.assertEqual(ledger.charges, (Fraction(5, 4),) * 4)
        self.assertEqual(Fraction(10) - ledger.rookie_remaining[0], ledger.charges[0])
        self.assertEqual(ledger.financial_snapshot()["charges"], ["5/4"] * 4)

    def test_changed_or_missing_posting_prevents_load_and_writes(self):
        self.sign()
        with closing(sqlite3.connect(self.path)) as db, db:
            payload = json.loads(db.execute("SELECT payload FROM events").fetchone()[0])
            payload["posting"]["charges"][0] = 0
            db.execute("UPDATE events SET payload=?", (json.dumps(payload),))
        with self.assertRaisesRegex(ValueError, "posting"):
            self.store.load_team("a")
        with self.assertRaises(ValueError):
            self.store.update_budget("a", cap=20, roster_reserve=0, expected_revision=1)

    def test_modified_contract_charge_is_detected(self):
        self.sign()
        with closing(sqlite3.connect(self.path)) as db, db:
            payload = json.loads(db.execute("SELECT payload FROM events").fetchone()[0])
            payload["contract_charges"] = [1] * 4
            db.execute("UPDATE events SET payload=?", (json.dumps(payload),))
        with self.assertRaisesRegex(ValueError, "contract charges"):
            self.store.load_team("a")

    def test_missing_ownership_is_detected(self):
        self.sign()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DELETE FROM ownership")
        with self.assertRaisesRegex(ValueError, "Ownership"):
            self.store.load_team("a")

    def test_old_format_is_preserved_and_requires_explicit_migration(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("PRAGMA user_version=1")
        with self.assertRaisesRegex(ValueError, "version"):
            FranchiseStore(self.path)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT count(*) FROM teams").fetchone()[0], 1)

    def test_fractional_charge_cannot_hide_under_a_whole_dollar_cap(self):
        ledger = Ledger(cap=1, existing_charges=(0,), roster_reserve=0, max_bonus_years=5,
                       veteran_minimums={}, rookies={"r": RookieScale(1, (1,) * 4, 1, 10, 40)},
                       rookie_year_one_allocation=10, rookie_total_allocation=40)
        with self.assertRaises(Rejected):
            ledger.sign("one", Offer("r", (1,) * 4, 1), 0)
        self.assertEqual(ledger.charges, (0,))
