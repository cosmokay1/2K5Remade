"""Exact scaling and actual ledger constraints; allocation fixtures are authored."""
from fractions import Fraction
import unittest

from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.historical_economy import HistoricalEconomy
from franchise.minimums import minimum_schedule
from franchise.rookie import RookieScale


class HistoricalEconomyTests(unittest.TestCase):
    def test_minimum_and_ceiling_posting_preserve_exact_bound_direction(self):
        economy = HistoricalEconomy(80500000)
        self.assertEqual(economy.ratio, Fraction(805, 3012))
        self.assertEqual(economy.minimum(885000), 237000)
        self.assertEqual(economy.ceiling(885000), 236000)
        for amount in (0, 1, 885000, 1300000, 123456789):
            exact = amount * economy.ratio
            self.assertGreaterEqual(economy.minimum(amount), exact)
            self.assertLessEqual(economy.ceiling(amount), exact)
        for invalid in (-1, True, 1.5, '885000'):
            with self.assertRaises(ValueError): economy.minimum(invalid)
        with self.assertRaises(ValueError): HistoricalEconomy(True)

    def test_scaled_veteran_floor_is_enforced_without_changing_cap(self):
        economy = HistoricalEconomy(80500000)
        floors = economy.minimum_schedule(2004, (7,), ('active_inactive',))
        self.assertEqual(floors, (348000,))
        ledger = Ledger.from_opening(OpeningBooks(), cap=80500000, roster_reserve=0,
                                    max_bonus_years=5, veteran_minimums={'v': floors})
        with self.assertRaises(Rejected): ledger.preview_offer(Offer('v', (347000,), 0), 0)
        ledger.preview_offer(Offer('v', (348000,), 0), 0)
        self.assertEqual(ledger.charges, (0,))
        self.assertEqual(ledger.cap, 80500000)
        with self.assertRaises(ValueError): economy.minimum_schedule(2009, (0,), ('active_inactive',))

    def test_rookie_scale_and_pool_ceiling_reject_illegal_offers(self):
        economy = HistoricalEconomy(80500000)
        minimums = minimum_schedule(2026, (0,)*4, ('active_inactive',)*4)
        modern = RookieScale(2, minimums, 885000, 1500000, 6000000)
        scale = economy.drafted_rookie(modern)
        self.assertEqual(scale.minimum_salaries, (237000, 249000, 261000, 273000))
        offer = Offer('r', scale.minimum_salaries, 0)
        scale.validate(offer, club_year_one_remaining=scale.year_one_maximum,
                       club_total_remaining=scale.total_maximum)
        with self.assertRaises(Rejected):
            scale.validate(offer, club_year_one_remaining=236000,
                           club_total_remaining=scale.total_maximum)
        with self.assertRaises(Rejected):
            scale.validate(Offer('r', (236000, *scale.minimum_salaries[1:]), 0),
                           club_year_one_remaining=scale.year_one_maximum,
                           club_total_remaining=scale.total_maximum)
        self.assertEqual(economy.undrafted_rookie().minimum_salaries, (237000, 249000, 261000))
        with self.assertRaises(ValueError):
            economy.drafted_rookie(RookieScale(2, (1,)*4, 1, 2, 8))
