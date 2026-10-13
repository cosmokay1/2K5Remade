from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from franchise.books import OpeningBooks, ActiveContract
from franchise.cap import Ledger, Offer, Rejected
from franchise.cash import CashObligation
from franchise.store import FranchiseStore


class CashTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "cash.sqlite"
        self.store = FranchiseStore(self.path)
        books = OpeningBooks(contracts=(ActiveContract(Offer("old", (10, 20), 8), "synthetic contract", elapsed_years=1),))
        self.store.create_team("a", Ledger.from_opening(books, cap=100,
            roster_reserve=5, max_bonus_years=5, veteran_minimums={"old": (1,), "new": (1, 1)}))

    def initialize(self):
        self.store.initialize_cash("a", (CashObligation("contract:old", "old", 38, 18, "synthetic payment history"),),
                                   source="Synthetic complete nominal compensation fixture")

    def test_unknown_payment_history_is_not_zero_and_opening_terms_reconcile(self):
        self.assertIsNone(self.store.load_team("a").cash_snapshot())
        with self.assertRaisesRegex(Rejected, "unavailable"):
            self.store.record_payment("a", "pay", "contract:old", 1, expected_cash_revision=0, source="fixture")
        with self.assertRaisesRegex(ValueError, "reconcile"):
            self.store.initialize_cash("a", (), source="incomplete fixture")
        self.initialize()
        self.assertEqual(self.store.load_team("a").cash_snapshot()["unpaid_total"], 20)
        with self.assertRaisesRegex(Rejected, "reset"):
            self.initialize()

    def test_signing_and_payments_survive_restart_without_changing_cap(self):
        self.initialize()
        receipt = self.store.sign("a", "sign", Offer("new", (10, 20), 6), 1)
        before = self.store.load_team("a").financial_snapshot()
        cash = self.store.load_team("a").cash_snapshot()
        self.assertEqual(cash["unpaid_total"], 56)
        payment = self.store.record_payment("a", "bonus-paid", "contract:new", 6,
                                            expected_cash_revision=1, source="synthetic paid bonus")
        reopened = FranchiseStore(self.path)
        self.assertEqual(reopened.load_team("a").financial_snapshot(), {**before, "revision": before["revision"] + 1})
        self.assertEqual(reopened.load_team("a").cash_snapshot()["unpaid_total"], 50)
        self.assertEqual(reopened.record_payment("a", "bonus-paid", "contract:new", 6,
            expected_cash_revision=1, source="synthetic paid bonus"), payment)
        self.assertEqual(reopened.sign("a", "sign", receipt.offer, 1), receipt)
        self.assertEqual(reopened.load_team("a").cash_snapshot()["revision"], 2)
        with self.assertRaises(Rejected):
            reopened.record_payment("a", "overpay", "contract:new", 31, expected_cash_revision=2, source="fixture")
        with self.assertRaisesRegex(Rejected, "stale"):
            reopened.record_payment("a", "stale", "contract:new", 1, expected_cash_revision=1, source="fixture")
        self.assertEqual(reopened.load_team("a").financial_snapshot(), {**before, "revision": before["revision"] + 1})

    def test_payment_failure_rolls_back_and_corrupt_posting_fails_closed(self):
        self.initialize()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TRIGGER fail_payment BEFORE INSERT ON events WHEN NEW.kind='cash_payment' BEGIN SELECT RAISE(ABORT, 'failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.record_payment("a", "payment", "contract:old", 1, expected_cash_revision=0, source="fixture")
        self.assertEqual(self.store.load_team("a").cash_snapshot()["paid_total"], 18)
        with closing(sqlite3.connect(self.path)) as db, db:
            row = db.execute("SELECT id,payload FROM events WHERE kind='cash_open'").fetchone()
            payload = json.loads(row[1])
            payload["cash_posting"]["paid_total"] = 0
            db.execute("UPDATE events SET payload=? WHERE id=?", (json.dumps(payload), row[0]))
        with self.assertRaisesRegex(ValueError, "cash posting"):
            self.store.load_team("a")
