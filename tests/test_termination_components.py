from datetime import date
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks, ActiveContract
from franchise.cap import Ledger, Offer, Rejected
from franchise.cash import CashObligation
from franchise.guarantees import DiscountProfile
from franchise.store import FranchiseStore


class TerminationComponentTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = FranchiseStore(Path(directory.name) / "state.sqlite")
        offer = Offer("v", (10, 20, 30), 9, (10, 15, 20))
        books = OpeningBooks(contracts=(ActiveContract(offer, "synthetic protected contract", elapsed_years=1),))
        self.store.create_team("a", Ledger.from_opening(books, cap=100, roster_reserve=0,
            max_bonus_years=5, veteran_minimums={"v": (1, 1)}))
        self.discount = DiscountProfile(2026, Fraction(1, 20), "synthetic rate fixture")

    def components(self):
        return self.store.termination_components("a", "v", removed_on=date(2026, 6, 2),
            discount=self.discount, payment_year_offsets=(0, 1))

    def test_components_use_original_elapsed_bonus_and_actual_base_payments_without_mutation(self):
        record = CashObligation("contract:v", "v", 69, 23, "synthetic paid records",
            (("base:0", 10), ("base:1", 4), ("signing_bonus", 9)))
        self.store.initialize_cash("a", (record,), source="synthetic reconciled allocations")
        before = self.store.load_team("a").financial_snapshot()
        result = self.components()
        self.assertEqual(result["bonus_retained_charges"], [3, 3])
        self.assertEqual(result["covered_base_present_value_charge"], "631/21")
        self.assertEqual(result["nominal_unpaid_protected_base"], 31)
        self.assertEqual(result["nominal_unpaid_signing_bonus"], 0)
        self.assertFalse(result["release_authorized"])
        self.assertEqual(self.store.load_team("a").financial_snapshot(), before)
        reopened = FranchiseStore(self.store.path)
        self.assertEqual(reopened.load_team("a").active_contract("v").elapsed_years, 1)

    def test_missing_allocations_and_unpaid_prior_year_guarantees_reject(self):
        with self.assertRaisesRegex(Rejected, "unavailable"):
            self.components()
        self.store.initialize_cash("a", (CashObligation("contract:v", "v", 69, 9, "fixture",
            (("signing_bonus", 9),)),), source="synthetic unpaid prior base")
        with self.assertRaisesRegex(Rejected, "prior-year"):
            self.components()
