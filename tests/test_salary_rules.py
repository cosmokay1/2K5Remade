import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.salary_rules import VeteranMinimumProfile
from franchise.store import FranchiseStore


class SalaryRuleTests(unittest.TestCase):
    def profile(self):
        return VeteranMinimumProfile(2026, (("v", (3, 3, 4), ("active_inactive",) * 3),))

    def ledger(self, profile):
        return Ledger.from_opening(OpeningBooks(), cap=10_000_000,
            roster_reserve=0, max_bonus_years=5,
            veteran_minimums=profile.floors(), veteran_minimum_profile=profile)

    def test_reload_enforces_explicit_annual_credits_without_auto_increment(self):
        profile = self.profile()
        self.assertEqual(profile.floors()["v"], (1_145_000, 1_190_000, 1_305_000))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite"
            store = FranchiseStore(path)
            store.create_team("a", self.ledger(profile))
            reloaded = FranchiseStore(path).load_team("a")
            self.assertEqual(reloaded.bootstrap_config()["veteran_minimum_profile"], profile.to_dict())
            with self.assertRaisesRegex(Rejected, "minimum"):
                reloaded.preview_offer(Offer("v", (1_145_000, 1_190_000, 1_304_999), 0), 0)
            reloaded.sign("ok", Offer("v", profile.floors()["v"], 0), 0)

    def test_profile_and_balance_disagreement_stops_reload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite"
            store = FranchiseStore(path)
            store.create_team("a", self.ledger(self.profile()))
            with closing(sqlite3.connect(path)) as db, db:
                config = json.loads(db.execute("SELECT config FROM teams").fetchone()[0])
                config["veteran_minimums"]["v"][0] = 1
                db.execute("UPDATE teams SET config=?", (json.dumps(config),))
            with self.assertRaisesRegex(ValueError, "disagree"):
                store.load_team("a")

    def test_unknown_era_version_and_annual_inputs_are_rejected(self):
        for year in (2004, 2031, True):
            with self.assertRaises(ValueError):
                VeteranMinimumProfile(year, ())
        for records in ((("v", (3,), ("practice_squad",)),),
                        (("v", (3,), ("active_inactive",)),) * 2):
            with self.assertRaises(ValueError):
                VeteranMinimumProfile(2026, records)
        data = self.profile().to_dict()
        data["rule_version"] = "future-guessed-rules"
        with self.assertRaises(ValueError):
            VeteranMinimumProfile.from_dict(data)
