from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.rookie import RookieScale, UndraftedScale
from franchise.store import FranchiseStore


class UndraftedTests(unittest.TestCase):
    def ledger(self, cap=100):
        return Ledger.from_opening(OpeningBooks(), cap=cap, roster_reserve=0, max_bonus_years=5,
            veteran_minimums={}, rookies={"d": RookieScale(2, (10,) * 4, 10, 20, 100),
                                         "u": UndraftedScale((10,) * 3), "u2": UndraftedScale((10,) * 3)},
            rookie_year_one_allocation=12, rookie_total_allocation=60,
            undrafted_bonus_reservation=3, undrafted_reservation_source="synthetic annual reservation")

    def test_shared_reservation_and_cap_commit_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FranchiseStore(Path(directory) / "state.sqlite")
            store.create_team("a", self.ledger(cap=22))
            drafted = Offer("d", (11,) * 4, 0)
            store.sign("a", "drafted", drafted, 0)
            undrafted = Offer("u", (10,) * 3, 3, (0, 10, 5))
            preview = store.preview_offer("a", undrafted, 1)
            self.assertEqual(preview["rookie_year_one_after"], 0)
            receipt = store.sign("a", "undrafted", undrafted, 1)
            reopened = FranchiseStore(store.path)
            ledger = reopened.load_team("a")
            self.assertEqual(ledger.charges, (22, 22, 22, 11))
            self.assertEqual(ledger.rookie_remaining, (0, 13))
            self.assertEqual(ledger.financial_snapshot()["undrafted_bonus_remaining"], 0)
            self.assertEqual(reopened.sign("a", "undrafted", undrafted, 1), receipt)
            with self.assertRaisesRegex(Rejected, "cap room"):
                reopened.sign("a", "minimum-only", Offer("u2", (10,) * 3, 0), 2)
            self.assertEqual(reopened.load_team("a").revision, 2)

    def test_drafted_player_cannot_spend_reserved_share(self):
        ledger = self.ledger()
        before = ledger.financial_snapshot()
        with self.assertRaisesRegex(Rejected, "allocation"):
            ledger.sign("d", Offer("d", (12,) * 4, 0), 0)
        self.assertEqual(ledger.financial_snapshot(), before)

    def test_minimum_salary_is_cap_cost_but_not_udfa_pool_cost(self):
        ledger = self.ledger()
        ledger.sign("u", Offer("u", (10,) * 3, 0), 0)
        self.assertEqual(ledger.charges, (10,) * 3)
        self.assertEqual(ledger.rookie_remaining, (12, 60))
        self.assertEqual(ledger.financial_snapshot()["undrafted_bonus_remaining"], 3)

    def test_udfa_term_raise_bonus_and_guarantee_rejections_are_atomic(self):
        for offer in (Offer("u", (10,) * 4, 0), Offer("u", (10, 11, 11), 3),
                      Offer("u", (10,) * 3, 4), Offer("u", (10,) * 3, 0, (0, 0, 1))):
            ledger = self.ledger()
            before = ledger.financial_snapshot()
            with self.subTest(offer=offer), self.assertRaises(Rejected):
                ledger.sign("bad", offer, 0)
            self.assertEqual(ledger.financial_snapshot(), before)

    def test_fractional_bonus_pool_basis_remains_exact(self):
        ledger = self.ledger()
        ledger.sign("u", Offer("u", (10,) * 3, 1), 0)
        self.assertEqual(ledger.rookie_remaining, (Fraction(35, 3), 59))
        self.assertEqual(ledger.charges, (Fraction(31, 3),) * 3)
