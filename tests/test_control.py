import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from franchise.cap import Ledger, Offer
from franchise.control import AccessDisabled, validate_control
from franchise.negotiation import Negotiation


class ControlTests(unittest.TestCase):
    def enabled(self):
        return {"enabled": True, "protocol": 1,
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}

    def ledger(self):
        return Ledger(cap=100, existing_charges=(90,), roster_reserve=0, max_bonus_years=5, veteran_minimums={"p": (1,) * 4})

    def test_switch_requires_true_and_supported_protocol(self):
        validate_control(self.enabled())
        for value in [{}, {"enabled": False, "protocol": 1},
                      {"enabled": "true", "protocol": 1},
                      {"enabled": True, "protocol": 2}]:
            with self.assertRaises(AccessDisabled):
                validate_control(value)

    def test_expired_or_missing_grants_are_denied(self):
        for expiry in [None, "bad", "2000-01-01T00:00:00+00:00", "2100-01-01"]:
            state = self.enabled()
            state["expires_at"] = expiry
            with self.assertRaises(AccessDisabled):
                validate_control(state)

    def session(self, ledger, check):
        return Negotiation(ledger, player_id="p", personality={}, performance={},
                           relationships={}, access_check=check)

    def test_initial_disabled_handshake_prevents_session(self):
        with self.assertRaises(AccessDisabled):
            self.session(self.ledger(), Mock(side_effect=AccessDisabled("off")))

    def test_shutdown_during_inference_prevents_commit(self):
        ledger = self.ledger()
        state = self.enabled()
        session = self.session(ledger, lambda: validate_control(state))

        def provider(_):
            state["enabled"] = False
            return json.dumps({"action": "accept", "reason": "Deal", "salaries": None,
                               "signing_bonus": None})

        with self.assertRaises(AccessDisabled):
            session.respond("a", Offer("p", (10,), 0), provider)
        self.assertEqual(ledger.charges, (90,))
        self.assertEqual(ledger.revision, 0)
        self.assertEqual(session.events, [])

    def test_final_commit_handshake_prevents_late_shutdown(self):
        ledger = self.ledger()
        check = Mock(side_effect=[None, None, None, AccessDisabled("off")])
        session = self.session(ledger, check)
        provider = lambda _: json.dumps({"action": "accept", "reason": "Deal",
                                        "salaries": None, "signing_bonus": None})
        with self.assertRaises(AccessDisabled):
            session.respond("a", Offer("p", (10,), 0), provider)
        self.assertEqual(ledger.revision, 0)

    def test_disabled_switch_prevents_model_call(self):
        ledger = self.ledger()
        check = Mock(side_effect=[None, AccessDisabled("unavailable")])
        session = self.session(ledger, check)
        provider = Mock()
        with self.assertRaises(AccessDisabled):
            session.respond("a", Offer("p", (10,), 0), provider)
        provider.assert_not_called()
