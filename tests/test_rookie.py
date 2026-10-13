import unittest
from franchise.cap import Offer, Rejected
from franchise.rookie import RookieScale


class RookieTests(unittest.TestCase):
    def scale(self, draft_round=2):
        # Synthetic amounts; not published draft-slot values.
        return RookieScale(draft_round, (100, 110, 120, 130), 100, 1000, 10000)

    def validate(self, offer, **kwargs):
        self.scale().validate(offer, club_year_one_remaining=kwargs.get("year_one", 1000),
                              club_total_remaining=kwargs.get("total", 10000))

    def test_fixed_four_year_term(self):
        for salaries in [(100,) * 3, (100,) * 5]:
            with self.assertRaisesRegex(Rejected, "four years"):
                self.validate(Offer("p", salaries, 0))

    def test_25_percent_uses_original_year_one_and_includes_bonus(self):
        # Year-one charge 600; permitted annual increment 150, never compounding.
        self.validate(Offer("p", (500, 650, 800, 950), 400))
        with self.assertRaisesRegex(Rejected, "25%"):
            self.validate(Offer("p", (500, 650, 837, 1000), 400))

    def test_salary_floor_slot_bounds_and_pool_constraints(self):
        for offer, kwargs in [
            (Offer("p", (99, 110, 120, 130), 0), {}),
            (Offer("p", (1000,) * 4, 400), {}),
            (Offer("p", (500,) * 4, 400), {"year_one": 599}),
            (Offer("p", (500,) * 4, 400), {"total": 2399}),
        ]:
            with self.subTest(offer=offer, kwargs=kwargs), self.assertRaises(Rejected):
                self.validate(offer, **kwargs)

    def test_minimum_only_exception(self):
        scale = RookieScale(7, (100, 200, 300, 400), 100, 100, 1000)
        scale.validate(Offer("p", (100, 200, 300, 400), 0),
                       club_year_one_remaining=100, club_total_remaining=1000)

    def test_fifth_year_is_eligibility_not_extra_initial_salary(self):
        self.assertTrue(self.scale(1).fifth_year_option_eligible)
        self.assertFalse(self.scale(2).fifth_year_option_eligible)


if __name__ == "__main__":
    unittest.main()


class RookieGuaranteeChainTests(unittest.TestCase):
    def test_third_and_fourth_year_protection_requires_full_prior_year(self):
        scale = RookieScale(1, (10,) * 4, 10, 100, 400)
        for guarantees in ((0, 0, 1, 0), (0, 10, 5, 1), (0, 5, 10, 0)):
            with self.subTest(guarantees=guarantees), self.assertRaisesRegex(Rejected, "preceding-year"):
                scale.validate(Offer("r", (10,) * 4, 0, guarantees),
                               club_year_one_remaining=100, club_total_remaining=400)
        scale.validate(Offer("r", (10,) * 4, 0, (0, 10, 10, 5)),
                       club_year_one_remaining=100, club_total_remaining=400)
        scale.validate(Offer("r", (10,) * 4, 0, (0, 5, 0, 0)),
                       club_year_one_remaining=100, club_total_remaining=400)
