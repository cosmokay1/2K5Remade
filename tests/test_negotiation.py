import json
import unittest
from franchise.cap import Ledger, Offer
from franchise.negotiation import Decision, Negotiation
from franchise.openai_provider import response_text


def decision(action="accept", salaries=None, bonus=None):
    return json.dumps({"action": action, "reason": "I value winning and stability.",
                       "salaries": salaries, "signing_bonus": bonus})


class NegotiationTests(unittest.TestCase):
    def session(self):
        ledger = Ledger(cap=100, existing_charges=(90,), roster_reserve=0,
                        max_bonus_years=5)
        return Negotiation(ledger, player_id="p", personality={"winning": 0.9},
                           performance={"yards": 1100}, relationships={"trust": 0.7},
                           access_check=lambda: None)

    def test_model_acceptance_cannot_overrule_cap(self):
        session = self.session()
        result = session.respond("a", Offer("p", (11,), 0), lambda _: decision())
        self.assertEqual(result["outcome"], "accounting_rejected")
        self.assertEqual(session.ledger.charges, (90,))

    def test_counter_is_not_automatically_signed_and_history_is_supplied(self):
        session = self.session()
        session.respond("a", Offer("p", (5,), 0),
                        lambda _: decision("counter", [10], 0))
        self.assertEqual(session.ledger.charges, (90,))

        def accept(context):
            self.assertEqual(context["history"][0]["outcome"], "counteroffer")
            self.assertEqual(context["performance"]["yards"], 1100)
            self.assertEqual(context["personality"]["winning"], 0.9)
            return decision()

        self.assertEqual(session.respond("b", Offer("p", (10,), 0), accept)["outcome"], "signed")

    def test_retry_does_not_call_model_or_charge_twice(self):
        session = self.session()
        offer = Offer("p", (10,), 0)
        original = session.respond("a", offer, lambda _: decision())

        def must_not_run(_):
            self.fail("Model called on an already completed negotiation request")

        self.assertEqual(session.respond("a", offer, must_not_run), original)
        self.assertEqual(session.ledger.revision, 1)
        self.assertEqual(len(session.events), 1)

    def test_cap_change_during_model_call_rejects_stale_acceptance(self):
        session = self.session()

        def delayed(_):
            session.ledger.sign("other", Offer("other", (5,), 0), 0)
            return decision()

        result = session.respond("a", Offer("p", (5,), 0), delayed)
        self.assertEqual(result["outcome"], "accounting_rejected")
        self.assertIn("stale", result["accounting_reason"])

    def test_malformed_or_failed_model_cannot_change_state(self):
        for reply in ["not json", decision("accept", [1], 0),
                      decision("counter", [-1], 0), decision("counter", [True], 0)]:
            session = self.session()
            with self.subTest(reply=reply), self.assertRaises(ValueError):
                session.respond("a", Offer("p", (10,), 0), lambda _: reply)
            self.assertEqual(session.events, [])
            self.assertEqual(session.ledger.revision, 0)

    def test_response_refusal_or_incomplete_is_not_a_decision(self):
        for result in [{"status": "incomplete"}, {"status": "completed", "output": []},
                       {"status": "completed", "output": [{"type": "message", "content":
                          [{"type": "refusal", "refusal": "no"}]}]}]:
            with self.assertRaises(ValueError):
                response_text(result)
