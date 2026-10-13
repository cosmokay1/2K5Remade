import unittest
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from franchise.cap import Ledger, Offer, Rejected
from franchise.rookie import RookieScale


class RookieCommitTests(unittest.TestCase):
    def ledger(self, *, cap=2000, year_one=1000, total=4000):
        scale = RookieScale(1, (100, 100, 100, 100), 100, 1000, 4000)
        return Ledger(cap=cap, existing_charges=(0,), roster_reserve=0,
                      max_bonus_years=5, rookies={"r1": scale, "r2": scale},
                      rookie_year_one_allocation=year_one,
                      rookie_total_allocation=total)

    def test_rookie_cannot_use_veteran_term(self):
        ledger = self.ledger()
        with self.assertRaisesRegex(Rejected, "four years"):
            ledger.sign("a", Offer("r1", (100,), 0), 0)
        self.assertEqual(ledger.revision, 0)
        self.assertEqual(ledger.rookie_remaining, (1000, 4000))

    def test_pool_and_cap_commit_together(self):
        ledger = self.ledger(year_one=300, total=1200)
        offer = Offer("r1", (200,) * 4, 400)
        receipt = ledger.sign("a", offer, 0)
        self.assertEqual(receipt.charges, (300,) * 4)
        self.assertEqual(ledger.rookie_remaining, (0, 0))
        self.assertEqual(ledger.sign("a", offer, 0), receipt)
        self.assertEqual(ledger.rookie_remaining, (0, 0))

    def test_cap_rejection_leaves_pools_untouched(self):
        ledger = self.ledger(cap=299)
        with self.assertRaisesRegex(Rejected, "cap room"):
            ledger.sign("a", Offer("r1", (200,) * 4, 400), 0)
        self.assertEqual(ledger.charges, (0,))
        self.assertEqual(ledger.rookie_remaining, (1000, 4000))

    def test_pool_rejection_leaves_cap_untouched(self):
        ledger = self.ledger(year_one=299)
        with self.assertRaisesRegex(Rejected, "rookie allocation"):
            ledger.sign("a", Offer("r1", (200,) * 4, 400), 0)
        self.assertEqual(ledger.charges, (0,))
        self.assertEqual(ledger.rookie_remaining, (299, 4000))

    def test_second_rookie_cannot_reuse_spent_allocation(self):
        ledger = self.ledger(year_one=400)
        ledger.sign("a", Offer("r1", (200,) * 4, 400), 0)
        with self.assertRaisesRegex(Rejected, "rookie allocation"):
            ledger.sign("b", Offer("r2", (200,) * 4, 400), 1)
        self.assertEqual(ledger.rookie_remaining, (100, 2800))

    def test_veterans_do_not_spend_rookie_allocation(self):
        ledger = self.ledger()
        ledger.sign("a", Offer("v1", (300,), 0), 0)
        self.assertEqual(ledger.rookie_remaining, (1000, 4000))

    def test_fractional_bonus_pool_deduction_does_not_lose_money(self):
        ledger = self.ledger()
        ledger.sign("a", Offer("r1", (200,) * 4, 1), 0)
        self.assertEqual(ledger.rookie_remaining, (Fraction(3199, 4), 3199))

    def test_concurrent_offers_from_same_revision_only_commit_once(self):
        ledger = self.ledger()

        def attempt(player):
            try:
                ledger.sign(player, Offer(player, (200,) * 4, 400), 0)
                return True
            except Rejected:
                return False

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(attempt, ["r1", "r2"]))
        self.assertEqual(sum(outcomes), 1)
        self.assertEqual(ledger.revision, 1)
        self.assertEqual(ledger.rookie_remaining, (700, 2800))


if __name__ == "__main__":
    unittest.main()
