import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from franchise.books import OpeningBooks
from franchise.cap import Ledger
from franchise.control import AccessDisabled
from franchise.store import FranchiseStore
from franchise.bridge import Bridge


class BridgeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = FranchiseStore(Path(directory.name) / "state.sqlite")
        self.store.create_team("a", Ledger.from_opening(OpeningBooks(), cap=100,
            roster_reserve=0, max_bonus_years=5, veteran_minimums={"v": (1,)}))
        self.calls = 0
        def provider(_):
            self.calls += 1
            return json.dumps(dict(action="accept", reason="Yes", salaries=None, signing_bonus=None))
        self.bridge = Bridge(self.store, provider=provider, access_check=lambda: None)

    def request(self, **changes):
        return {**dict(protocol=1, request_id="one", operation="negotiate", team_id="a",
            offer=dict(player_id="v", salaries=[10], signing_bonus=0), expected_revision=0,
            timeout_ms=1000, personality={}, performance={}, relationships={}), **changes}

    def test_sign_and_retry_are_durable_wire_results(self):
        result = self.bridge.handle(self.request())
        self.assertEqual(result["result"]["outcome"], "signed")
        self.assertEqual(self.bridge.handle(self.request()), result)
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.store.load_team("a").charges, (10,))

    def test_protocol_stale_revision_and_timeout_do_not_commit(self):
        self.assertEqual(self.bridge.handle(self.request(protocol=2))["error"], "protocol_mismatch")
        self.assertEqual(self.bridge.handle(self.request(expected_revision=1))["error"], "state_rejected")
        with patch("franchise.bridge.time.monotonic", side_effect=[0, 0, 0, 0, 0, 0, 2]):
            self.assertEqual(self.bridge.handle(self.request())["error"], "timeout")
        self.assertEqual(self.store.load_team("a").revision, 0)

    def test_disabled_ai_retains_financial_preview(self):
        def disabled():
            raise AccessDisabled("Disabled")
        self.bridge.access_check = disabled
        self.assertEqual(self.bridge.handle(self.request())["error"], "ai_disabled")
        request = self.request(operation="preview")
        for field in ("personality", "performance", "relationships"):
            del request[field]
        self.assertEqual(self.bridge.handle(request)["result"]["room_after"], 90)
        self.assertEqual(self.store.load_team("a").revision, 0)
        self.assertEqual(self.calls, 0)

    def test_provider_failure_does_not_leak_detail_or_commit(self):
        def failure(_):
            raise RuntimeError("SECRET")
        self.bridge.provider = failure
        result = self.bridge.handle(self.request())
        self.assertEqual(result["error"], "service_failure")
        self.assertNotIn("SECRET", json.dumps(result))
        self.assertEqual(self.store.load_team("a").revision, 0)

    def test_manual_sign_when_ai_disabled_still_enforces_cap_and_retries(self):
        def disabled():
            raise AccessDisabled("Disabled")
        self.bridge.access_check = disabled
        request = self.request(operation="manual_sign", decision_mode="manual")
        for field in ("personality", "performance", "relationships"):
            del request[field]
        too_large = {**request, "offer": {**request["offer"], "salaries": [101]}}
        self.assertEqual(self.bridge.handle(too_large)["error"], "state_rejected")
        self.assertEqual(self.store.load_team("a").revision, 0)
        result = self.bridge.handle(request)
        self.assertEqual(result["result"]["decision_mode"], "manual")
        self.assertEqual(self.bridge.handle(request), result)
        self.assertEqual(self.store.load_team("a").charges, (10,))
        self.assertEqual(self.calls, 0)

    def test_manual_sign_requires_explicit_mode_and_active_connection(self):
        request = self.request(operation="manual_sign", decision_mode="automatic")
        for field in ("personality", "performance", "relationships"):
            del request[field]
        self.assertEqual(self.bridge.handle(request)["error"], "invalid_request")
        def disconnected():
            raise AccessDisabled("Disconnected")
        self.bridge.connection_check = disconnected
        request["decision_mode"] = "manual"
        self.assertEqual(self.bridge.handle(request)["error"], "ai_disabled")
        self.assertEqual(self.store.load_team("a").revision, 0)
