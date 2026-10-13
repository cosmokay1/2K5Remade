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

    def pay(self, store, team, request_id, obligation_id, amount, **kwargs):
        kwargs.setdefault("payment_reference", request_id)
        if obligation_id == "contract:new":
            kwargs.setdefault("component", "signing_bonus")
        return store.record_payment(team, request_id, obligation_id, amount, **kwargs)

    def initialize(self):
        self.store.initialize_cash("a", (CashObligation("contract:old", "old", 38, 18, "synthetic payment history"),),
                                   source="Synthetic complete nominal compensation fixture")

    def test_unknown_payment_history_is_not_zero_and_opening_terms_reconcile(self):
        self.assertIsNone(self.store.load_team("a").cash_snapshot())
        with self.assertRaisesRegex(Rejected, "unavailable"):
            self.pay(self.store, "a", "pay", "contract:old", 1, expected_cash_revision=0, source="fixture")
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
        payment = self.pay(self.store, "a", "bonus-paid", "contract:new", 6,
                                            expected_cash_revision=1, source="synthetic paid bonus")
        reopened = FranchiseStore(self.path)
        self.assertEqual(reopened.load_team("a").financial_snapshot(), {**before, "revision": before["revision"] + 1})
        self.assertEqual(reopened.load_team("a").cash_snapshot()["unpaid_total"], 50)
        self.assertEqual(self.pay(reopened, "a", "bonus-paid", "contract:new", 6,
            expected_cash_revision=1, source="synthetic paid bonus"), payment)
        self.assertEqual(reopened.sign("a", "sign", receipt.offer, 1), receipt)
        self.assertEqual(reopened.load_team("a").cash_snapshot()["revision"], 2)
        with self.assertRaises(Rejected):
            self.pay(reopened, "a", "overpay", "contract:new", 31, expected_cash_revision=2, source="fixture")
        with self.assertRaisesRegex(Rejected, "stale"):
            self.pay(reopened, "a", "stale", "contract:new", 1, expected_cash_revision=1, source="fixture")
        self.assertEqual(reopened.load_team("a").financial_snapshot(), {**before, "revision": before["revision"] + 1})

    def test_payment_failure_rolls_back_and_corrupt_posting_fails_closed(self):
        self.initialize()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TRIGGER fail_payment BEFORE INSERT ON events WHEN NEW.kind='cash_payment' BEGIN SELECT RAISE(ABORT, 'failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.pay(self.store, "a", "payment", "contract:old", 1, expected_cash_revision=0, source="fixture")
        self.assertEqual(self.store.load_team("a").cash_snapshot()["paid_total"], 18)
        with closing(sqlite3.connect(self.path)) as db, db:
            row = db.execute("SELECT id,payload FROM events WHERE kind='cash_open'").fetchone()
            payload = json.loads(row[1])
            payload["cash_posting"]["paid_total"] = 0
            db.execute("UPDATE events SET payload=? WHERE id=?", (json.dumps(payload), row[0]))
        with self.assertRaisesRegex(ValueError, "cash posting"):
            self.store.load_team("a")

    def test_same_external_payment_cannot_be_credited_under_two_requests(self):
        self.initialize()
        first = self.pay(self.store, "a", "request-one", "contract:old", 4,
                         expected_cash_revision=0, source="synthetic settlement feed", payment_reference="receipt-42")
        reopened = FranchiseStore(self.path)
        with self.assertRaisesRegex(Rejected, "evidence already"):
            self.pay(reopened, "a", "request-two", "contract:old", 4,
                     expected_cash_revision=1, source="synthetic settlement feed", payment_reference="receipt-42")
        self.assertEqual(reopened.load_team("a").cash_snapshot(), first)
        with self.assertRaisesRegex(Rejected, "differently"):
            self.pay(reopened, "a", "request-one", "contract:old", 4,
                     expected_cash_revision=1, source="synthetic settlement feed", payment_reference="receipt-43")
        self.assertEqual(reopened.load_team("a").charges, (24,))

    def test_duplicate_payment_evidence_in_history_fails_replay(self):
        self.initialize()
        self.pay(self.store, "a", "first", "contract:old", 2,
                 expected_cash_revision=0, source="synthetic feed", payment_reference="receipt-1")
        self.pay(self.store, "a", "second", "contract:old", 2,
                 expected_cash_revision=1, source="synthetic feed", payment_reference="receipt-2")
        with closing(sqlite3.connect(self.path)) as db, db:
            row = db.execute("SELECT id,payload FROM events WHERE request_key='cash:payment:second'").fetchone()
            payload = json.loads(row[1])
            payload["payment_reference"] = "receipt-1"
            db.execute("UPDATE events SET payload=? WHERE id=?", (json.dumps(payload), row[0]))
        with self.assertRaisesRegex(ValueError, "Duplicate recorded"):
            self.store.load_team("a")

    def test_component_payments_preserve_exact_unpaid_guarantees(self):
        self.initialize()
        self.store.sign("a", "protected", Offer("new", (10, 20), 6, (10, 15)), 1)
        self.assertEqual(self.store.load_team("a").guarantee_cash("new")["unpaid_guaranteed_base_by_original_year"], [10, 15])
        self.pay(self.store, "a", "base-payment", "contract:new", 4, expected_cash_revision=1,
                 source="synthetic pay feed", component="base:0")
        self.pay(self.store, "a", "bonus-payment", "contract:new", 6, expected_cash_revision=2,
                 source="synthetic pay feed", component="signing_bonus")
        reopened = FranchiseStore(self.path)
        guarantee = reopened.load_team("a").guarantee_cash("new")
        self.assertEqual(guarantee["unpaid_guaranteed_base_by_original_year"], [6, 15])
        self.assertEqual(guarantee["unpaid_signing_bonus"], 0)
        self.assertEqual(reopened.load_team("a").charges, (37, 23))
        before = reopened.load_team("a").cash_snapshot()
        with self.assertRaisesRegex(ValueError, "Paid component"):
            self.pay(reopened, "a", "too-much-bonus", "contract:new", 1, expected_cash_revision=3,
                     source="synthetic pay feed", component="signing_bonus")
        self.assertEqual(reopened.load_team("a").cash_snapshot(), before)
        self.assertIsNone(reopened.load_team("a").guarantee_cash("old"))

    def test_opening_component_allocations_must_reconcile_total_and_original_years(self):
        with self.assertRaisesRegex(ValueError, "total paid"):
            CashObligation("contract:old", "old", 38, 18, "fixture", (("signing_bonus", 8),))
        invalid = CashObligation("contract:old", "old", 38, 18, "fixture", (("signing_bonus", 18),))
        with self.assertRaisesRegex(ValueError, "Paid component"):
            self.store.initialize_cash("a", (invalid,), source="fixture")
        valid = CashObligation("contract:old", "old", 38, 18, "fixture", (("signing_bonus", 8), ("base:0", 10)))
        self.store.initialize_cash("a", (valid,), source="fixture")
        self.assertEqual(self.store.load_team("a").guarantee_cash("old")["unpaid_signing_bonus"], 0)
