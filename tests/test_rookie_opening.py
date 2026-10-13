from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks, ActiveContract, ChargeRecord
from franchise.cap import Ledger, Offer, Rejected
from franchise.rookie import RookieScale, UndraftedScale
from franchise.rookie_opening import RookiePoolOpening
from franchise.store import FranchiseStore


class RookieOpeningTests(unittest.TestCase):
    def registry(self):
        return {"d": RookieScale(2, (10,) * 4, 10, 20, 100), "u": UndraftedScale((10,) * 3),
                "n": RookieScale(2, (10,) * 4, 10, 20, 100)}

    def ledger(self, books, profile, **changes):
        return Ledger.from_opening(books, cap=100, roster_reserve=0, max_bonus_years=5,
            veteran_minimums={}, rookies=self.registry(), rookie_pool_opening=profile, **changes)

    def test_signed_current_cohort_usage_is_derived_and_replayed_without_rounding(self):
        books = OpeningBooks(contracts=(ActiveContract(Offer("d", (11,) * 4, 4), "fixture drafted"),
                                        ActiveContract(Offer("u", (10,) * 3, 1), "fixture UDFA")))
        profile = RookiePoolOpening(2026, frozenset({"d", "u", "n"}), 30, 100, 3, "synthetic annual cohort", ())
        ledger = self.ledger(books, profile)
        self.assertEqual(ledger.rookie_remaining, (Fraction(53, 3), 51))
        self.assertEqual(ledger.financial_snapshot()["undrafted_bonus_remaining"], 2)
        self.assertEqual(ledger.bootstrap_config()["rookie_year_one_allocation"], 30)
        with tempfile.TemporaryDirectory() as directory:
            store = FranchiseStore(Path(directory) / "state.sqlite")
            store.create_team("a", ledger)
            store.sign("a", "next", Offer("n", (12,) * 4, 0), 0)
            reopened = FranchiseStore(store.path)
            self.assertEqual(reopened.load_team("a").rookie_remaining, (Fraction(17, 3), 3))
            self.assertEqual(reopened.load_team("a").financial_snapshot()["undrafted_bonus_remaining"], 2)

    def test_prior_cut_contract_still_consumes_pool_and_cannot_be_resigned_as_new(self):
        prior = ActiveContract(Offer("u", (10,) * 3, 1), "synthetic prior signed UDFA")
        profile = RookiePoolOpening(2026, frozenset({"d", "u", "n"}), 30, 100, 3, "synthetic cohort", (prior,))
        books = OpeningBooks(retained=(ChargeRecord("rookie-prior:u", (1,), "synthetic retained bonus settlement"),))
        ledger = self.ledger(books, profile)
        self.assertEqual(ledger.rookie_remaining, (Fraction(89, 3), 99))
        with self.assertRaisesRegex(Rejected, "release/re-sign"):
            ledger.sign("repeat", Offer("u", (10,) * 3, 0), 0)
        with self.assertRaisesRegex(ValueError, "retained cap"):
            self.ledger(OpeningBooks(), profile)

    def test_inconsistent_source_cohort_and_overspent_opening_reject(self):
        books = OpeningBooks(contracts=(ActiveContract(Offer("d", (12,) * 4, 0), "fixture"),))
        profile = RookiePoolOpening(2026, frozenset({"d", "u", "n"}), 12, 60, 3, "synthetic cohort", ())
        with self.assertRaisesRegex(ValueError, "allocation/reservation"):
            self.ledger(books, profile)
        with self.assertRaisesRegex(ValueError, "disagree"):
            self.ledger(books, profile, rookie_year_one_allocation=13)
        incomplete = RookiePoolOpening(2026, frozenset({"d"}), 30, 100, 3, "synthetic cohort", ())
        with self.assertRaisesRegex(ValueError, "Unsigned rookie"):
            self.ledger(books, incomplete)

    def test_imported_proration_and_missing_durable_cohort_source_reject(self):
        offer = Offer("d", (11,) * 4, 4)
        profile = RookiePoolOpening(2026, frozenset({"d", "u", "n"}), 30, 100, 3, "synthetic cohort", ())
        wrong = OpeningBooks(contracts=(ActiveContract(offer, "wrong original bonus horizon", bonus_years=2),))
        with self.assertRaisesRegex(ValueError, "proration disagrees"):
            self.ledger(wrong, profile)
        books = OpeningBooks(contracts=(ActiveContract(offer, "synthetic original contract"),))
        legacy = Ledger.from_opening(books, cap=100, roster_reserve=0, max_bonus_years=5,
            veteran_minimums={}, rookies=self.registry(), rookie_year_one_allocation=30, rookie_total_allocation=100,
            undrafted_bonus_reservation=3, undrafted_reservation_source="synthetic reservation")
        with tempfile.TemporaryDirectory() as directory:
            store = FranchiseStore(Path(directory) / "state.sqlite")
            with self.assertRaisesRegex(ValueError, "cohort/pool source"):
                store.create_team("a", legacy)
