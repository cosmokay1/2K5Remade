from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
import json
import subprocess
import sys
from franchise.cap import Ledger, Offer, Rejected
from franchise.books import OpeningBooks, ChargeRecord
from franchise.rookie import RookieScale
from franchise.store import FranchiseStore, StoredLedger
from franchise.negotiation import Negotiation
from franchise.control import AccessDisabled


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "franchise.sqlite"
        self.store = FranchiseStore(self.path)

    def ledger(self):
        return Ledger.from_opening(OpeningBooks(retained=(ChargeRecord("fixture", (10,), "synthetic retained fixture"),)), cap=100, roster_reserve=0, max_bonus_years=5,
                      veteran_minimums={"v": (1,) * 4},
                      rookies={"r": RookieScale(1, (1,) * 4, 1, 20, 80)},
                      rookie_year_one_allocation=20, rookie_total_allocation=80)

    def test_restart_restores_contract_pool_revision_and_receipt(self):
        self.store.create_team("a", self.ledger())
        offer = Offer("r", (4,) * 4, 4)
        story = {"reason": "More security"}
        receipt = self.store.sign("a", "one", offer, 0, story=story)
        reopened = FranchiseStore(self.path)
        ledger = reopened.load_team("a")
        self.assertEqual(ledger.charges, (15, 5, 5, 5))
        self.assertEqual(ledger.rookie_remaining, (15, 60))
        self.assertEqual(reopened.sign("a", "one", offer, 0, story=story), receipt)
        self.assertEqual(reopened.stories("a"), [story])

    def test_database_failure_rolls_back_ownership_and_story(self):
        self.store.create_team("a", self.ledger())
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TRIGGER fail_event BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.sign("a", "one", Offer("v", (10,), 0), 0, story={"reason": "Deal"})
        self.assertEqual(self.store.load_team("a").revision, 0)
        self.assertEqual(self.store.stories("a"), [])
        with closing(sqlite3.connect(self.path)) as db, db:
            self.assertEqual(db.execute("SELECT count(*) FROM ownership").fetchone()[0], 0)

    def test_two_process_connections_cannot_sign_same_player_to_two_teams(self):
        for team in ("a", "b"):
            self.store.create_team(team, self.ledger())

        def attempt(team):
            try:
                FranchiseStore(self.path).sign(team, "one", Offer("v", (10,), 0), 0)
                return True
            except Rejected:
                return False

        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(sum(executor.map(attempt, ("a", "b"))), 1)
        self.assertEqual(sum(self.store.load_team(team).revision for team in ("a", "b")), 1)

    def test_rejected_deal_cannot_write_anything(self):
        self.store.create_team("a", self.ledger())
        with self.assertRaises(Rejected):
            self.store.sign("a", "one", Offer("v", (91,), 0), 0)
        self.assertEqual(self.store.load_team("a").charges, (10,))

    def test_budget_revision_survives_restart_and_stale_offer_rejects(self):
        self.store.create_team("a", self.ledger())
        self.store.update_budget("a", cap=200, roster_reserve=5, expected_revision=0)
        reopened = FranchiseStore(self.path)
        self.assertEqual(reopened.load_team("a").cap, 200)
        with self.assertRaises(Rejected):
            reopened.sign("a", "one", Offer("v", (10,), 0), 0)

    def test_cannot_overwrite_team_or_change_committed_story(self):
        self.store.create_team("a", self.ledger())
        with self.assertRaises(Rejected):
            self.store.create_team("a", self.ledger())
        offer = Offer("v", (10,), 0)
        self.store.sign("a", "one", offer, 0, story={"reason": "Original"})
        with self.assertRaises(Rejected):
            self.store.sign("a", "one", offer, 0, story={"reason": "Changed"})

    def test_pristine_bootstrap_required(self):
        ledger = self.ledger()
        ledger.sign("one", Offer("v", (10,), 0), 0)
        with self.assertRaises(ValueError):
            self.store.create_team("a", ledger)

    def test_negotiation_commits_story_and_contract_durably(self):
        self.store.create_team("a", self.ledger())
        session = Negotiation(StoredLedger(self.store, "a"), player_id="v", personality={},
                              performance={"yards": 100}, relationships={}, access_check=lambda: None)
        event = session.respond("one", Offer("v", (10,), 0), lambda _: json.dumps(
            {"action": "accept", "reason": "My production deserves this deal",
             "salaries": None, "signing_bonus": None}))
        self.assertEqual(event["outcome"], "signed")
        reopened = FranchiseStore(self.path)
        self.assertEqual(reopened.load_team("a").charges, (20,))
        self.assertEqual(reopened.stories("a")[0]["outcome"], "signed")
        self.assertEqual(reopened.stories("a")[0]["reason"], event["reason"])
        restarted_session = Negotiation(StoredLedger(reopened, "a"), player_id="v",
                                        personality={}, performance={}, relationships={},
                                        access_check=lambda: None)

        def must_not_infer(_):
            self.fail("Committed negotiation regenerated after restart")

        self.assertEqual(restarted_session.respond("one", Offer("v", (10,), 0), must_not_infer), event)

    def test_disabled_new_commit_is_blocked_but_old_state_remains_readable(self):
        self.store.create_team("a", self.ledger())
        self.store.sign("a", "one", Offer("v", (10,), 0), 0)

        def disabled():
            raise AccessDisabled("off")

        with self.assertRaises(AccessDisabled):
            self.store.sign("a", "two", Offer("r", (1,) * 4, 0), 1, access_check=disabled)
        self.assertEqual(FranchiseStore(self.path).load_team("a").charges, (20,))

    def test_separate_python_process_reconstructs_committed_money(self):
        self.store.create_team("a", self.ledger())
        self.store.sign("a", "one", Offer("v", (10,), 0), 0)
        result = subprocess.run([sys.executable, "-c",
            "import json,sys; from franchise.store import FranchiseStore; "
            "ledger=FranchiseStore(sys.argv[1]).load_team('a'); "
            "print(json.dumps(ledger.financial_snapshot()))",
            str(self.path)], capture_output=True, text=True, check=True, timeout=10)
        self.assertEqual(json.loads(result.stdout)["charges"], [20])
        self.assertEqual(json.loads(result.stdout)["revision"], 1)

    def test_invalid_story_and_unknown_schema_cannot_modify_money(self):
        self.store.create_team("a", self.ledger())
        for story in (["bad"], {"value": float("nan")}):
            with self.assertRaises(ValueError):
                self.store.sign("a", "one", Offer("v", (10,), 0), 0, story=story)
        self.assertEqual(self.store.load_team("a").revision, 0)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("PRAGMA user_version=99")
        with self.assertRaisesRegex(ValueError, "version"):
            FranchiseStore(self.path)

    def test_abrupt_process_exit_before_commit_recovers_without_partial_ownership(self):
        self.store.create_team("a", self.ledger())
        result = subprocess.run([sys.executable, "-c",
            "import sqlite3,sys,os; db=sqlite3.connect(sys.argv[1]); "
            "db.execute('BEGIN IMMEDIATE'); "
            "db.execute(\"INSERT INTO ownership VALUES ('r','a')\"); os._exit(7)",
            str(self.path)], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 7)
        recovered = FranchiseStore(self.path)
        self.assertEqual(recovered.load_team("a").revision, 0)
        recovered.sign("a", "after-crash", Offer("r", (1,) * 4, 0), 0)
        self.assertEqual(recovered.load_team("a").revision, 1)
