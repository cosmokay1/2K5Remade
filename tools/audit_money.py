"""Reproduce money-audit findings using synthetic data; no cloud/game writes.

Run from the workspace root: python3 -m tools.audit_money
Resolved findings are rechecked; open findings remain synthetic reproductions.
"""
from dataclasses import asdict
from fractions import Fraction
import json
from pathlib import Path
import tempfile
from franchise.books import OpeningBooks, ChargeRecord
from franchise.store import FranchiseStore
from franchise.cap import Ledger, Offer, Rejected, json_amount
from franchise.rookie import RookieScale


def ledger(**overrides):
    args = dict(cap=100, existing_charges=(0,), roster_reserve=0, max_bonus_years=5, veteran_minimums={p: (1,) * 10 for p in ("veteran", "v", "same-player")})
    args.update(overrides)
    return Ledger(**args)


def durable_findings():
    """Audit the deployed engine path, separately from in-memory limitations."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "audit.sqlite"
        store = FranchiseStore(path)
        for team in ("a", "b"):
            opening = OpeningBooks(retained=(ChargeRecord("retained:" + team, (80, 70), "synthetic audit source"),))
            store.create_team(team, Ledger.from_opening(opening, cap=100,
                roster_reserve=5, max_bonus_years=2, veteran_minimums={"v": (1, 1)}))
        offer = Offer("v", (10, 20), 10)
        story = {"reason": "Synthetic durable audit agreement"}
        receipt = store.sign("a", "agreement", offer, 0, story=story)
        reopened = FranchiseStore(path)
        assert reopened.sign("a", "agreement", offer, 0, story=story) == receipt
        assert reopened.load_team("a").charges == (95, 95)
        assert reopened.load_team("a").revision == 1
        assert reopened.stories("a") == [story]
        before = reopened.load_team("b").financial_snapshot()
        try:
            reopened.sign("b", "competing", offer, 0)
        except Rejected:
            pass
        else:
            raise AssertionError("Durable duplicate league ownership accepted")
        assert reopened.load_team("b").financial_snapshot() == before
        return {"F05_restart_receipts": "restart retry returned identical receipt; revision stayed 1",
                "F06_exclusive_ownership": "competing team rejected; finances unchanged",
                "exact_annual_charges": [95, 95], "current_room": 0,
                "story_retained": True,
                "scope": "Synthetic durable signings; not original game or complete NFL lifecycle"}


def main():
    observations = {}

    for finding, player in [("F01_zero_salary_veteran", "veteran"),
                            ("F02_unknown_player", "nonexistent-player"),
                            ("F02_omitted_rookie_registry", "unregistered-draft-pick")]:
        try:
            ledger().sign("probe", Offer(player, (0,), 0), 0)
        except Rejected as error:
            observations[finding] = {"status": "rejected", "reason": str(error)}
        else:
            raise AssertionError(f"Regression: {finding} accepted")
    try:
        ledger(max_bonus_years=10)
    except ValueError:
        observations["F03_bonus_proration_over_five_years"] = {"status": "rejected"}
    else:
        raise AssertionError("Regression: excess bonus allocation accepted")

    scale = RookieScale(1, (1,) * 4, 1, 10, 40)
    fractional = ledger(rookies={"r": scale}, rookie_year_one_allocation=10,
                        rookie_total_allocation=40)
    fractional.sign("fraction", Offer("r", (1,) * 4, 1), 0)
    observations["F04_cap_pool_rounding_disagreement"] = {
        "current_cap_charge": str(fractional.charges[0]),
        "year_one_rookie_pool_charge": str(Fraction(10) - fractional.rookie_remaining[0]),
    }

    old = ledger()
    old.sign("same", Offer("v", (10,), 0), 0)
    rebuilt = ledger()
    rebuilt.sign("same", Offer("v", (10,), 0), 0)
    observations["F05_recreated_state_loses_receipts"] = {
        "fresh_ledger_accepts_same_request_again": True,
        "original_revision": old.revision, "new_revision": rebuilt.revision,
    }

    team_a, team_b = ledger(), ledger()
    for team, request in [(team_a, "a"), (team_b, "b")]:
        team.sign(request, Offer("same-player", (10,), 0), 0)
    observations["F06_two_teams_can_sign_same_player"] = {
        "team_a_revision": team_a.revision, "team_b_revision": team_b.revision,
    }

    mutable = ledger(cap=10)
    snapshot = mutable.negotiation_context("v")
    mutable.update_budget(cap=100, roster_reserve=0, expected_revision=0)
    try:
        mutable.sign("mutable", Offer("v", (20,), 0), snapshot["revision"])
    except Rejected:
        observations["F07_cap_change_without_revision"] = {"status": "stale offer rejected"}
    else:
        raise AssertionError("Regression: stale budget offer accepted")

    tender = ledger(existing_charges=(1,), rookies={"r": scale},
                    rookie_year_one_allocation=10, rookie_total_allocation=40, rookie_tenders={"r": 1})
    tender.sign("draft", Offer("r", (1,) * 4, 0), 0)
    observations["F08_rookie_tender_not_replaced"] = {
        "supplied_existing_draft_tender": 1,
        "new_contract_year_one_charge": 1,
        "recorded_team_charge": tender.charges[0],
        "expected_after_replacing_tender": 1,
    }

    verified = 0
    for years in range(1, 11):
        for limit in range(1, 6):
            for bonus in range(101):
                offer = Offer("test", (3,) * years, bonus)
                charges = offer.charges(limit)
                assert sum(charges) == 3 * years + bonus
                assert len(charges) == years
                assert all(isinstance(charge, Fraction) and charge >= 3 for charge in charges)
                verified += 1
    print(json.dumps({"observations": observations,
                      "durable_path": durable_findings(),
                      "unimplemented_accounting": ["cash payments and guarantees", "complete releases and trades",
                          "extensions and restructures", "top-51/roster phases", "season rollover and carryover",
                          "complete rookie options/escalators", "verified game import/posting"],
                      "bonus_conservation_cases_verified": verified}, indent=2, default=json_amount))


if __name__ == "__main__":
    main()
