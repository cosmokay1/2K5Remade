"""Two-turn synthetic negotiation; --provider vertex/openai enables live calls."""
import argparse
import json
import os
from pathlib import Path
from franchise.cap import Ledger, Offer, money_text
from franchise.negotiation import Negotiation
from franchise.openai_provider import OpenAIProvider
from franchise.vertex_provider import VertexProvider
from franchise.control import GoogleControl


def scripted(context):
    # A fixture, not an LLM or personality simulation.
    if not context["history"]:
        return json.dumps({"action": "counter", "reason": "I want more money up front.",
                           "salaries": [6_000_000] * 3, "signing_bonus": 6_000_000})
    return json.dumps({"action": "accept", "reason": "The revised bonus works for me.",
                       "salaries": None, "signing_bonus": None})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["scripted", "vertex", "openai"],
                        default="scripted",
                        help="Vertex/openai sends up to two paid requests with synthetic data")
    parser.add_argument("--gcloud-auth", action="store_true",
                        help="Use the existing gcloud login for this short local demo")
    args = parser.parse_args()
    try:
        defaults = json.loads((Path(__file__).resolve().parents[1]
                               / "config/google.json").read_text())
        access_check = (lambda: None)  # Explicitly offline/scripted mode only.
        if args.provider != "scripted":
            access_check = GoogleControl(
                project=defaults["project"], bucket=defaults["control_bucket"],
                object_name=defaults["control_object"], use_gcloud_login=args.gcloud_auth)
        if args.provider == "vertex":
            provider = VertexProvider(project=os.environ.get("GOOGLE_CLOUD_PROJECT", defaults["project"]),
                                      location=os.environ.get("GOOGLE_CLOUD_LOCATION", defaults["location"]),
                                      model=os.environ.get("GEMINI_MODEL", defaults["model"]),
                                      use_gcloud_login=args.gcloud_auth)
        elif args.provider == "openai":
            provider = OpenAIProvider(api_key=os.environ.get("OPENAI_API_KEY", ""),
                                      model=os.environ.get("OPENAI_MODEL", ""))
        else:
            provider = scripted
        ledger = Ledger(cap=100_000_000, existing_charges=(90_000_000, 80_000_000),
                        roster_reserve=2_000_000, max_bonus_years=5,
                        veteran_minimums={"receiver-01": (1_000_000,) * 3})
        session = Negotiation(ledger, player_id="receiver-01",
                              personality={"money": 0.9, "loyalty": 0.4, "winning": 0.7},
                              performance={"receiving_yards": 1100, "touchdowns": 8},
                              relationships={"team_trust": 0.6}, access_check=access_check)
        print(f"PROVIDER: {args.provider}")
        offer = Offer("receiver-01", (7_000_000,) * 3, 3_000_000)
        event = session.respond("round-1", offer, provider)
        print(json.dumps(event, indent=2))
        if event["outcome"] == "counteroffer":
            counter = event["counter"]
            # Demo team explicitly chooses to submit the counter back to the player.
            offer = Offer.from_dict(counter)
            print(json.dumps(session.respond("round-2", offer, provider), indent=2))
        print(f"Current cap room: ${money_text(ledger.room)}")
    except (ValueError, RuntimeError) as exc:
        parser.exit(2, f"negotiation: {exc}\n")


if __name__ == "__main__":
    main()
