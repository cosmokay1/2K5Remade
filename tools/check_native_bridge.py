"""Execute asset-free Windows C++ pipe client against a synthetic database."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from franchise.books import OpeningBooks
from franchise.cap import Ledger
from franchise.store import FranchiseStore


def main():
    with tempfile.TemporaryDirectory(prefix="bridge fixture ") as directory:
        path = Path(directory) / "state with spaces.sqlite"
        store = FranchiseStore(path)
        store.create_team("a", Ledger.from_opening(OpeningBooks(), cap=100,
            roster_reserve=0, max_bonus_years=5, veteran_minimums={"v": (1,)}))
        for _ in range(2):
            result = subprocess.run([sys.argv[1], sys.executable, str(path)],
                                    text=True, capture_output=True, timeout=20, check=True)
            responses = [json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses) == 3
            assert all(response["error"] is None for response in responses)
            assert responses[0]["result"]["ai_enabled"] is True
            assert responses[1]["result"]["room_after"] == 90
            assert responses[2]["result"]["outcome"] == "player_rejected"
        assert store.load_team("a").revision == 0
        assert len(store.negotiation_history("a", "v")) == 1
        print("Native Windows pipe handshake, preview, dialogue and restart verified (synthetic).")


if __name__ == "__main__":
    main()
