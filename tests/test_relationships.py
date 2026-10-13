import json
from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.negotiation import Negotiation
from franchise.store import FranchiseStore, StoredLedger


class RelationshipTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = FranchiseStore(Path(directory.name) / "state.sqlite")
        self.store.create_team("a", Ledger.from_opening(OpeningBooks(), cap=100, roster_reserve=0,
            max_bonus_years=5, veteran_minimums={"v": (1,)}))
        self.session = Negotiation(StoredLedger(self.store, "a"), player_id="v", personality={},
            performance={}, relationships={"trust": 0.6}, access_check=lambda: None)
        self.reject = lambda _: json.dumps(dict(action="reject", reason="No", salaries=None, signing_bonus=None))
        self.session.respond("first", Offer("v", (10,), 0), self.reject)

    def update(self, **changes):
        return self.store.update_relationship("a", changes.get("request_id", "trust-1"), "v", "trust",
            changes.get("delta", -0.1), source_request_id=changes.get("source", "first"),
            expected_revision=changes.get("revision", 0))

    def test_consequence_persists_refreshes_live_session_and_applies_once(self):
        actor = self.update()
        self.assertEqual(actor["relationships"]["trust"], 0.5)
        self.assertEqual(self.update(), actor)
        with self.assertRaisesRegex(Rejected, "already applied"):
            self.update(request_id="duplicate", revision=1)
        seen = []
        def provider(context):
            seen.append(context)
            return self.reject(context)
        self.session.respond("next", Offer("v", (10,), 0), provider)
        self.assertEqual(seen[0]["relationships"]["trust"], 0.5)
        reopened = FranchiseStore(self.store.path)
        actor = reopened.bind_actor("a", "v", {}, {"trust": 0.9}, access_check=lambda: None)
        self.assertEqual(actor["relationships"]["trust"], 0.5)
        self.assertEqual(reopened.load_team("a").charges, (0,))

    def test_unknown_source_excess_change_and_stale_context_are_rejected(self):
        with self.assertRaisesRegex(Rejected, "consequence required"):
            self.update(source="invented")
        with self.assertRaises(ValueError):
            self.update(delta=-0.2)
        def provider(_):
            self.update()
            return json.dumps(dict(action="counter", reason="More", salaries=[12], signing_bonus=0))
        with self.assertRaisesRegex(Rejected, "stale franchise context"):
            self.session.respond("inflight", Offer("v", (10,), 0), provider)
        self.assertEqual(len(self.store.negotiation_history("a", "v")), 1)
        self.assertEqual(self.store.load_team("a").revision, 1)
