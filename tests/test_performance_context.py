import unittest
from franchise.negotiation import validate_performance


class PerformanceContextTests(unittest.TestCase):
    def test_observable_production_and_opportunities_allowed(self):
        validate_performance({"receiving": {"targets": 90, "receptions": 60,
                              "receiving_yards": 900, "drops": 4, "catch_rate": 0.667},
                              "snaps": 500, "games": 12})

    def test_hidden_ratings_rejected_even_when_nested(self):
        for evidence in [{"catching_skill": 95}, {"overall": 90},
                         {"attributes": {"speed_rating": 99}},
                         {"players": [{"potential": 98}]}]:
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                validate_performance(evidence)
