from contextlib import closing
from fractions import Fraction
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from franchise.books import ActiveContract, ChargeRecord, OpeningBooks, RookieTender
from franchise.cap import Ledger, Offer
from franchise.rookie import RookieScale
from franchise.store import FranchiseStore


class OpeningBookTests(unittest.TestCase):
    def books(self):
        return OpeningBooks(
            contracts=(ActiveContract(Offer("v", (100, 200, 300, 400), 80), "synthetic original contract", elapsed_years=2),),
            retained=(ChargeRecord("retained-1", (10, 5), "synthetic retained charges"),),
            adjustments=(ChargeRecord("credit-1", (-3, -2), "synthetic adjustment"),),
            tenders=(RookieTender("r", 10),))

    def ledger(self):
        return Ledger.from_opening(self.books(), cap=400, roster_reserve=0,
            max_bonus_years=5, veteran_minimums={"v": (1, 1)},
            rookies={"r": RookieScale(1, (10,) * 4, 10, 100, 400)},
            rookie_year_one_allocation=100, rookie_total_allocation=400)

    def test_remaining_original_bonus_and_all_obligations_derive_balance(self):
        self.assertEqual(self.books().charges(), (337, 423))
        ledger = self.ledger()
        self.assertEqual(ledger.charges, (337, 423))
        self.assertEqual(ledger.room, 63)
        ledger.sign("rookie", Offer("r", (40,) * 4, 0), 0)
        self.assertEqual(ledger.charges, (367, 463, 40, 40))

    def test_proration_does_not_restart_after_elapsed_years(self):
        contract = ActiveContract(Offer("v", (1,) * 6, 25), "synthetic", elapsed_years=4)
        self.assertEqual(contract.charges(), (6, 1))

    def test_original_fractional_bonus_survives_json_round_trip(self):
        books = OpeningBooks(contracts=(ActiveContract(Offer("v", (1,) * 3, 1), "synthetic", elapsed_years=1),))
        rebuilt = OpeningBooks.from_dict(json.loads(json.dumps(books.to_dict())))
        self.assertEqual(rebuilt.charges(), (Fraction(4, 3),) * 2)

    def test_duplicate_and_conflicting_obligations_are_rejected(self):
        contract = ActiveContract(Offer("v", (1,), 0), "synthetic")
        for args in [dict(contracts=(contract, contract)),
                     dict(contracts=(contract,), tenders=(RookieTender("v", 1),)),
                     dict(retained=(ChargeRecord("r", (-1,), "synthetic"),)),
                     dict(adjustments=(ChargeRecord("r", (-1,), "synthetic"),))]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                OpeningBooks(**args)

    def test_expired_contract_or_missing_provenance_rejects(self):
        with self.assertRaises(ValueError):
            ActiveContract(Offer("v", (1,), 0), "synthetic", elapsed_years=1)
        with self.assertRaises(ValueError):
            ActiveContract(Offer("v", (1,), 0), "")
        with self.assertRaises(ValueError):
            ChargeRecord("charge", (1.5,), "synthetic")

    def test_store_reconciles_source_records_and_preserves_tender_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite"
            store = FranchiseStore(path)
            store.create_team("a", self.ledger())
            store.sign("a", "rookie", Offer("r", (40,) * 4, 0), 0)
            self.assertEqual(FranchiseStore(path).load_team("a").charges, (367, 463, 40, 40))
            with closing(sqlite3.connect(path)) as db, db:
                config = json.loads(db.execute("SELECT config FROM teams").fetchone()[0])
                config["existing_charges"][0] += 1
                db.execute("UPDATE teams SET config=?", (json.dumps(config),))
            with self.assertRaisesRegex(ValueError, "source books"):
                store.load_team("a")

    def test_new_store_cannot_bootstrap_from_opaque_totals(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FranchiseStore(Path(directory) / "state.sqlite")
            ledger = Ledger(cap=100, existing_charges=(90,), roster_reserve=0,
                            max_bonus_years=5, veteran_minimums={})
            with self.assertRaisesRegex(ValueError, "opening books"):
                store.create_team("a", ledger)

    def test_verified_v2_migration_preserves_history_and_creates_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite"
            store = FranchiseStore(path)
            store.create_team("a", self.ledger())
            store.sign("a", "rookie", Offer("r", (40,) * 4, 0), 0)
            with closing(sqlite3.connect(path)) as db, db:
                config = json.loads(db.execute("SELECT config FROM teams").fetchone()[0])
                config.pop("opening_books")
                db.execute("UPDATE teams SET config=?", (json.dumps(config),))
                db.execute("PRAGMA user_version=2")
            backup = FranchiseStore.migrate_v2(path, {"a": self.books()})
            self.assertEqual(FranchiseStore(path).load_team("a").charges, (367, 463, 40, 40))
            with closing(sqlite3.connect(backup)) as db:
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 2)

    def test_failed_migration_does_not_rewrite_money_or_version(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite"
            store = FranchiseStore(path)
            store.create_team("a", self.ledger())
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("PRAGMA user_version=2")
            with self.assertRaises(ValueError):
                FranchiseStore.migrate_v2(path, {"a": OpeningBooks()})
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 2)
                config = json.loads(db.execute("SELECT config FROM teams").fetchone()[0])
                self.assertEqual(config["existing_charges"], [337, 423])

    def test_signed_rookie_can_exist_in_opening_roster_without_an_unsigned_tender(self):
        books = OpeningBooks(contracts=(ActiveContract(Offer("r", (2,) * 4, 4),
                                                       "synthetic signed rookie", elapsed_years=1),))
        ledger = Ledger.from_opening(books, cap=10, roster_reserve=0, max_bonus_years=5,
                                    veteran_minimums={},
                                    rookies={"r": RookieScale(1, (1,) * 4, 1, 5, 20)},
                                    rookie_year_one_allocation=5, rookie_total_allocation=20)
        self.assertEqual(ledger.charges, (3,) * 3)
        with self.assertRaises(ValueError):
            Ledger(cap=10, existing_charges=(3,), roster_reserve=0, max_bonus_years=5,
                   veteran_minimums={}, signed_player_ids=frozenset({"r"}),
                   rookies={"r": RookieScale(1, (1,) * 4, 1, 5, 20)},
                   rookie_year_one_allocation=5, rookie_total_allocation=20,
                   rookie_tenders={"r": 1})

    def test_failed_backup_open_closes_source_and_preserves_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite"
            store = FranchiseStore(path)
            store.create_team("a", self.ledger())
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("PRAGMA user_version=2")
            connect = sqlite3.connect
            readers = []

            def failing_connect(filename, **options):
                if ".v2-backup-" in str(filename):
                    raise sqlite3.OperationalError("injected backup destination failure")
                connection = connect(filename, **options)
                if not options:
                    readers.append(connection)
                return connection

            with patch("franchise.store.sqlite3.connect", side_effect=failing_connect):
                with self.assertRaises(sqlite3.OperationalError):
                    FranchiseStore.migrate_v2(path, {"a": self.books()})
            self.assertEqual(len(readers), 1)
            with self.assertRaises(sqlite3.ProgrammingError):
                readers[0].execute("SELECT 1")
            with closing(connect(path)) as db:
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 2)
