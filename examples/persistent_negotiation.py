"""Offline durable signing and restart demonstration; no model/cloud access."""
import json
from pathlib import Path
import tempfile
from franchise.cap import Ledger, Offer
from franchise.negotiation import Negotiation
from franchise.store import FranchiseStore, StoredLedger


def main():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "franchise.sqlite"
        store = FranchiseStore(path)
        store.create_team("example-team", Ledger(
            cap=100_000_000, existing_charges=(90_000_000,), roster_reserve=2_000_000,
            max_bonus_years=5, veteran_minimums={"receiver": (1_000_000,) * 3}))
        offer = Offer("receiver", (6_000_000,) * 3, 6_000_000)

        def session(database):
            return Negotiation(StoredLedger(database, "example-team"), player_id="receiver",
                               personality={"money": 0.8}, performance={"receiving_yards": 1100},
                               relationships={}, access_check=lambda: None)

        event = session(store).respond("contract-1", offer, lambda _: json.dumps(
            {"action": "accept", "reason": "This recognizes my production.",
             "salaries": None, "signing_bonus": None}))
        restarted = FranchiseStore(path)

        def no_regeneration(_):
            raise AssertionError("Recorded agreement should not call a model again")

        recalled = session(restarted).respond("contract-1", offer, no_regeneration)
        assert event == recalled
        print(json.dumps({"outcome": recalled["outcome"],
                          "charges_after_restart": restarted.load_team("example-team").charges,
                          "remaining_room": restarted.load_team("example-team").room,
                          "recorded_story": recalled["reason"],
                          "model_regenerated": False}, indent=2))


if __name__ == "__main__":
    main()
