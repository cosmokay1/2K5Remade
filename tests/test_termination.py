from datetime import date
from fractions import Fraction
import unittest
from franchise.books import ActiveContract
from franchise.cap import Offer
from franchise.termination import signing_bonus_acceleration


class BonusAccelerationTests(unittest.TestCase):
    def contract(self):
        return ActiveContract(Offer("v", (10, 20, 30, 40), 12), "synthetic original contract", elapsed_years=1)

    def retained(self, when, year=2026, contract=None):
        return signing_bonus_acceleration(contract or self.contract(), league_year=year,
                                          removed_on=when, record_id="release:v").annual_charges

    def test_june_first_boundary_and_original_elapsed_proration(self):
        self.assertEqual(self.retained(date(2026, 6, 1)), (9,))
        self.assertEqual(self.retained(date(2026, 6, 2)), (3, 6))
        # All remaining bonus survives either timing; no new cash is inferred.
        self.assertEqual(sum(self.retained(date(2026, 6, 2))), 9)

    def test_final_cba_year_has_no_next_year_deferral(self):
        self.assertEqual(self.retained(date(2030, 6, 2), 2030), (9,))

    def test_fractional_bonus_and_exhausted_proration_are_preserved(self):
        fractional = ActiveContract(Offer("v", (1, 1, 1), 1), "fixture", elapsed_years=1)
        self.assertEqual(self.retained(date(2026, 6, 2), contract=fractional), (Fraction(1, 3), Fraction(1, 3)))
        exhausted = ActiveContract(Offer("v", (1,) * 6, 5), "fixture", elapsed_years=5)
        self.assertEqual(self.retained(date(2026, 6, 2), contract=exhausted), (0, 0))

    def test_unknown_year_and_unmapped_calendar_date_reject(self):
        with self.assertRaises(ValueError):
            self.retained(date(2031, 5, 1), 2031)
        with self.assertRaises(ValueError):
            self.retained(date(2027, 1, 1))
