from fractions import Fraction
import unittest
from franchise.roster_accounting import RosterSalary, roster_charge


class RosterAccountingTests(unittest.TestCase):
    def entry(self, player, base, bonus=0, minimum=1, undrafted=False):
        return RosterSalary(player, base, Fraction(bonus), minimum, undrafted, "synthetic roster fixture")

    def test_excluded_thresholds_and_all_bonus_proration_survive_offseason(self):
        leaders = tuple(self.entry(str(i), 100) for i in range(51))
        extras = (self.entry("veteran", 5, 1, minimum=2), self.entry("undrafted", 5, 1, minimum=2, undrafted=True))
        result = roster_charge(leaders + extras, phase="offseason")
        self.assertEqual(result["counted_base"], 5104)  # 1 veteran excess + 3 UDFA excess.
        self.assertEqual(result["all_bonus_proration"], 2)
        self.assertEqual(result["supported_roster_charge"], 5106)
        self.assertEqual(roster_charge(leaders + extras, phase="regular_season")["supported_roster_charge"], 5112)

    def test_bonus_changes_valuation_and_below_cutoff_bonus_is_not_dropped(self):
        leaders = tuple(self.entry(str(i), 100) for i in range(51))
        large_bonus = self.entry("bonus-heavy", 1, 101)
        result = roster_charge(leaders + (large_bonus,), phase="offseason")
        self.assertIn("bonus-heavy", result["selected_players"])
        self.assertEqual(result["all_bonus_proration"], 101)

    def test_material_boundary_tie_requires_verified_selection(self):
        leaders = tuple(self.entry(str(i), 200) for i in range(50))
        tied = (self.entry("base", 100), self.entry("bonus", 1, 99))
        with self.assertRaisesRegex(ValueError, "Boundary tie"):
            roster_charge(leaders + tied, phase="offseason")
        selected = frozenset(str(i) for i in range(50)) | {"base"}
        self.assertEqual(roster_charge(leaders + tied, phase="offseason", selected_top51=selected)["supported_roster_charge"], 10199)
        with self.assertRaises(ValueError):
            roster_charge(leaders + tied, phase="regular_season", selected_top51=selected)
