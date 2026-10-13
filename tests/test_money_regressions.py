import json
import unittest
from franchise.cap import Ledger, Offer, Rejected
from franchise.negotiation import Negotiation
from franchise.rookie import RookieScale


class MoneyRegressionTests(unittest.TestCase):
    def ledger(self, **overrides):
        args = dict(cap=100, existing_charges=(0,), roster_reserve=0,
                    max_bonus_years=5, veteran_minimums={"v": (10,) * 10})
        args.update(overrides)
        return Ledger(**args)

    def test_zero_or_under_minimum_salary_cannot_be_hidden_by_bonus(self):
        for salary in (0, 9):
            ledger = self.ledger()
            with self.assertRaisesRegex(Rejected, "minimum salary"):
                ledger.sign("a", Offer("v", (salary,), 20), 0)
            self.assertEqual(ledger.revision, 0)
            self.assertEqual(ledger.charges, (0,))

    def test_missing_player_or_rookie_classification_rejects(self):
        ledger = self.ledger()
        with self.assertRaisesRegex(Rejected, "classification"):
            ledger.sign("a", Offer("missing-rookie", (10,), 0), 0)
        with self.assertRaises(Rejected):
            ledger.negotiation_context("missing-rookie")

    def test_every_contract_year_requires_a_known_floor(self):
        ledger = self.ledger(veteran_minimums={"v": (10, 20)})
        with self.assertRaisesRegex(Rejected, "Missing minimum"):
            ledger.sign("a", Offer("v", (10, 20, 30), 0), 0)
        with self.assertRaisesRegex(Rejected, "minimum salary"):
            ledger.sign("a", Offer("v", (10, 19), 0), 0)
        ledger.sign("a", Offer("v", (10, 20), 0), 0)

    def test_no_modern_bonus_limit_can_exceed_five_years(self):
        with self.assertRaises(ValueError):
            self.ledger(max_bonus_years=6)
        with self.assertRaises(ValueError):
            Offer("v", (10,) * 10, 10).charges(6)
        self.assertEqual(Offer("v", (10,) * 6, 30).charges(5), (16,) * 5 + (10,))

    def test_config_is_read_only_and_budget_changes_invalidate_offers(self):
        ledger = self.ledger()
        for field in ("cap", "roster_reserve", "max_bonus_years"):
            with self.assertRaises(AttributeError):
                setattr(ledger, field, 200)
        ledger.update_budget(cap=200, roster_reserve=5, expected_revision=0)
        with self.assertRaisesRegex(Rejected, "stale"):
            ledger.sign("a", Offer("v", (10,), 0), 0)
        ledger.sign("a", Offer("v", (10,), 0), 1)

    def test_invalid_or_stale_budget_change_does_not_mutate(self):
        ledger = self.ledger(existing_charges=(50,))
        for args in [dict(cap=49, roster_reserve=0, expected_revision=0),
                     dict(cap=100, roster_reserve=0, expected_revision=1)]:
            with self.assertRaises(Rejected):
                ledger.update_budget(**args)
        self.assertEqual(ledger.cap, 100)
        self.assertEqual(ledger.revision, 0)

    def test_budget_change_while_model_runs_prevents_acceptance(self):
        ledger = self.ledger()
        session = Negotiation(ledger, player_id="v", personality={}, performance={},
                              relationships={}, access_check=lambda: None)

        def provider(_):
            ledger.update_budget(cap=200, roster_reserve=0, expected_revision=0)
            return json.dumps({"action": "accept", "reason": "Deal", "salaries": None,
                               "signing_bonus": None})

        result = session.respond("a", Offer("v", (10,), 0), provider)
        self.assertEqual(result["outcome"], "accounting_rejected")
        self.assertEqual(ledger.charges, (0,))

    def test_registration_is_copied_and_classifications_cannot_overlap(self):
        registry = {"v": (10,)}
        ledger = self.ledger(veteran_minimums=registry)
        registry["v"] = (1,)
        with self.assertRaises(Rejected):
            ledger.sign("a", Offer("v", (1,), 0), 0)
        with self.assertRaises(ValueError):
            self.ledger(rookies={"v": RookieScale(1, (1,) * 4, 1, 10, 40)})


if __name__ == "__main__":
    unittest.main()
