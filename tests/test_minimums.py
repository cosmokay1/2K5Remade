import unittest
from franchise.minimums import minimum_salary, minimum_schedule


class MinimumTests(unittest.TestCase):
    def test_published_2026_active_rows_and_unit_conversion(self):
        self.assertEqual([minimum_salary(2026, cs, "active_inactive") for cs in (0, 1, 2, 3, 4, 6, 7, 12)],
                         [885000, 1005000, 1075000, 1145000, 1215000, 1215000, 1300000, 1300000])

    def test_inactive_category_and_table_boundaries(self):
        self.assertEqual(minimum_salary(2026, 0, "not_active_inactive"), 515000)
        self.assertEqual(minimum_salary(2020, 0, "active_inactive"), 610000)
        self.assertEqual(minimum_salary(2030, 7, "active_inactive"), 1480000)

    def test_future_schedule_does_not_assume_a_credited_season(self):
        self.assertEqual(minimum_schedule(2026, (0, 0, 1), ("active_inactive",) * 3),
                         (885000, 930000, 1095000))

    def test_unknown_year_category_or_invalid_seasons_rejects(self):
        for args in [(2031, 0, "active_inactive"), (2004, 0, "active_inactive"),
                     (2026, True, "active_inactive"), (2026, -1, "active_inactive"),
                     (2026, 0, "practice_squad")]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                minimum_salary(*args)
        with self.assertRaises(ValueError):
            minimum_schedule(2026, (0,), ("active_inactive", "active_inactive"))
