import json
import unittest
from franchise.cap import Ledger, Offer
from franchise.negotiation import Negotiation
from franchise.performance import Observation, PerformanceEvidence


class ObservationTests(unittest.TestCase):
    def evidence(self, **changes):
        inputs = dict(player_id="v", window="2026 weeks 1-4", mode="fast_sim",
                      coverage="Four completed simulated games; engine targets/pressures unverified",
                      observations=(Observation("receptions", 12, "synthetic save fixture"),
                                    Observation("targets", None, "synthetic engine capability fixture", "Counter not exposed"),
                                    Observation("pressures", None, "synthetic engine capability fixture", "No observed pressure events")))
        return PerformanceEvidence(**{**inputs, **changes})

    def session(self, performance, **changes):
        inputs = dict(player_id="v", personality={}, performance=performance,
                      relationships={}, access_check=lambda: None)
        return Negotiation(Ledger(cap=100, existing_charges=(0,), roster_reserve=0,
            max_bonus_years=5, veteran_minimums={"v": (1,)}), **{**inputs, **changes})

    def test_provider_sees_unavailable_not_zero_with_provenance_and_coverage(self):
        seen = []
        def provider(context):
            seen.append(context)
            return json.dumps(dict(action="reject", reason="Insufficient opportunities evidence",
                                   salaries=None, signing_bonus=None))
        self.session(self.evidence()).respond("one", Offer("v", (1,), 0), provider)
        performance = seen[0]["performance"]
        self.assertIsNone(performance["observations"]["targets"]["value"])
        self.assertEqual(performance["mode"], "fast_sim")
        self.assertIn("snaps", performance["missing_counters"])
        self.assertIn("source", performance["observations"]["pressures"])

    def test_real_zero_is_distinct_and_inconsistent_opportunities_reject(self):
        zero = self.evidence(observations=(Observation("pressures", 0, "synthetic play-event fixture"),))
        self.assertEqual(zero.to_context()["observations"]["pressures"]["value"], 0)
        with self.assertRaisesRegex(ValueError, "opportunities"):
            self.evidence(observations=(Observation("receptions", 12, "fixture"), Observation("targets", 11, "fixture")))
        with self.assertRaises(ValueError):
            Observation("targets", None, "fixture")
        with self.assertRaises(ValueError):
            Observation("catching_skill", 99, "fixture")

    def test_hidden_ratings_cannot_enter_through_other_actor_fields(self):
        for field in ("personality", "relationships"):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "ratings"):
                self.session(self.evidence(), **{field: {"overall": 90}})
        with self.assertRaisesRegex(ValueError, "another player"):
            self.session(self.evidence(player_id="other"))
