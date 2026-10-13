import unittest
from fractions import Fraction
from franchise.cap import Ledger, Offer, Rejected


class CapTests(unittest.TestCase):
    def ledger(self):
        return Ledger(cap=100, existing_charges=(80, 70), roster_reserve=5,
                      max_bonus_years=2, veteran_minimums={p: (1,) * 10 for p in ("p", "p1", "p2")})

    def test_exact_cap_allowed_and_one_dollar_over_rejected(self):
        accepted = self.ledger()
        accepted.sign("a", Offer("p", (10, 20), 10), 0)
        self.assertEqual(accepted.room, 0)
        self.assertEqual(accepted.charges, (95, 95))
        rejected = self.ledger()
        with self.assertRaises(Rejected):
            rejected.sign("b", Offer("p", (11, 20), 10), 0)
        self.assertEqual(rejected.charges, (80, 70))
        self.assertEqual(rejected.revision, 0)

    def test_bonus_allocation_preserves_every_dollar(self):
        offer = Offer("p", (0, 0, 0, 0), 11)
        self.assertEqual(offer.charges(3), (Fraction(11, 3),) * 3 + (0,))
        self.assertEqual(sum(offer.charges(3)), 11)

    def test_competing_acceptances_recheck_latest_state(self):
        ledger = self.ledger()
        ledger.sign("a", Offer("p1", (10,), 0), 0)
        with self.assertRaisesRegex(Rejected, "stale"):
            ledger.sign("b", Offer("p2", (10,), 0), 0)
        with self.assertRaisesRegex(Rejected, "cap room"):
            ledger.sign("b", Offer("p2", (10,), 0), 1)
        self.assertEqual(ledger.charges, (90, 70))

    def test_retry_is_idempotent_and_conflicting_retry_rejected(self):
        ledger = self.ledger()
        offer = Offer("p", (10,), 0)
        receipt = ledger.sign("a", offer, 0)
        self.assertEqual(ledger.sign("a", offer, 0), receipt)
        self.assertEqual(ledger.revision, 1)
        with self.assertRaisesRegex(Rejected, "different offer"):
            ledger.sign("a", Offer("p", (9,), 0), 1)

    def test_signed_player_cannot_be_added_twice(self):
        ledger = self.ledger()
        ledger.sign("a", Offer("p", (1,), 0), 0)
        with self.assertRaisesRegex(Rejected, "already signed"):
            ledger.sign("b", Offer("p", (1,), 0), 1)

    def test_invalid_money_and_allocation_inputs(self):
        for value in [-1, 1.5, True, "10"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                Offer("p", (value,), 0)
        with self.assertRaises(ValueError):
            Offer("p", (), 0)
        with self.assertRaises(ValueError):
            Offer("p", (1,), 0).charges(0)


if __name__ == "__main__":
    unittest.main()
