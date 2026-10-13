from fractions import Fraction
import unittest
from franchise.books import ActiveContract
from franchise.cap import Offer
from franchise.guarantees import DiscountProfile, guaranteed_base_liability


class GuaranteeLiabilityTests(unittest.TestCase):
    def contract(self):
        return ActiveContract(Offer("v", (100, 200, 300), 90, (100, 150, 250)),
                              "synthetic original protected terms", elapsed_years=1)

    def liability(self, **changes):
        inputs = dict(unpaid_by_year=(100, 200), payment_year_offsets=(0, 1),
            discount=DiscountProfile(2026, Fraction(1, 20), "synthetic five-percent rate fixture"), record_id="guarantee:v")
        return guaranteed_base_liability(self.contract(), **{**inputs, **changes})

    def test_nominal_cash_and_present_value_cap_are_distinct(self):
        liability = self.liability()
        self.assertEqual(liability.nominal_unpaid, 300)
        self.assertEqual(liability.cap_charge.annual_charges, (Fraction(6100, 21),))
        # The signing bonus is intentionally absent from this separate base component.
        self.assertLess(liability.cap_charge.annual_charges[0], 300)

    def test_explicit_payment_timing_not_contract_year_index(self):
        self.assertEqual(self.liability(payment_year_offsets=(0, 0)).cap_charge.annual_charges, (300,))
        self.assertEqual(self.liability(unpaid_by_year=(0, 200), payment_year_offsets=(0, 2)).cap_charge.annual_charges,
                         (Fraction(80000, 441),))

    def test_unverified_or_impossible_inputs_fail_closed(self):
        for changes in (dict(unpaid_by_year=(151, 200)), dict(unpaid_by_year=(100,)),
                        dict(payment_year_offsets=(0, 0.5)), dict(unpaid_by_year=(True, 200))):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.liability(**changes)
        for rate in (0.05, -1, None):
            with self.assertRaises(ValueError):
                DiscountProfile(2026, rate, "fixture")
