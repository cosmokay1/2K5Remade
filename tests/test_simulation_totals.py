import unittest
from tools.inspect_simulation_totals import summarize, inspect_totals, FIELDS


class SimulationTotalsTests(unittest.TestCase):
    def test_zero_games_are_unmeasured_not_zero_per_game(self):
        self.assertTrue(all(x is None for x in summarize([])['per_team_game'].values()))

    def test_unequal_games_use_weighted_league_denominator(self):
        teams = [{'games_recorded': n, 'totals': dict.fromkeys(FIELDS, y)}
                 for n, y in [(1, 100), (3, 900)]]
        self.assertEqual(summarize(teams)['per_team_game']['total_yards'], 250)
        self.assertEqual(summarize(teams)['team_games'], 4)

    def test_unsupported_save_is_rejected(self):
        with self.assertRaises(ValueError):
            inspect_totals(bytes(736))
