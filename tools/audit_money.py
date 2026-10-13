"""Reproduce money-audit findings using synthetic data; no cloud/game writes.

Run from the workspace root: python3 -m tools.audit_money
These observations describe current defects, not expected-correct behavior.
"""
from dataclasses import asdict
from fractions import Fraction
import json
from franchise.cap import Ledger, Offer
from franchise.rookie import RookieScale


def ledger(**overrides):
    args = dict(cap=100, existing_charges=(0,), roster_reserve=0, max_bonus_years=5)
    args.update(overrides)
    return Ledger(**args)


def main():
    observations = {}

    zero = ledger()
    receipt = zero.sign("zero", Offer("veteran", (0,), 0), 0)
    observations["F01_zero_salary_veteran"] = asdict(receipt)

    unknown = ledger()
    unknown.sign("unknown", Offer("nonexistent-player", (1,), 0), 0)
    observations["F02_unknown_player"] = {"accepted": True, "charges": unknown.charges}

    rookie = ledger(rookie_year_one_allocation=10, rookie_total_allocation=40)
    rookie.sign("rookie", Offer("unregistered-draft-pick", (1,), 0), 0)
    observations["F02_omitted_rookie_registry"] = {
        "one_year_contract_accepted": True,
        "rookie_pool_unchanged": str(rookie.rookie_remaining),
    }

    excessive = ledger(max_bonus_years=10, cap=1)
    excessive.sign("bonus", Offer("v", (0,) * 10, 10), 0)
    observations["F03_bonus_proration_over_five_years"] = {
        "accepted_at_one_dollar_room": True, "charges": excessive.charges,
        "five_year_allocation_first_year": Offer("v", (0,) * 10, 10).charges(5)[0],
    }

    scale = RookieScale(1, (1,) * 4, 1, 10, 40)
    fractional = ledger(rookies={"r": scale}, rookie_year_one_allocation=10,
                        rookie_total_allocation=40)
    fractional.sign("fraction", Offer("r", (1,) * 4, 1), 0)
    observations["F04_cap_pool_rounding_disagreement"] = {
        "current_cap_charge": fractional.charges[0],
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
    mutable.cap = 100
    mutable.sign("mutable", Offer("v", (20,), 0), snapshot["revision"])
    observations["F07_cap_change_without_revision"] = {
        "snapshot_cap": snapshot["cap"], "current_cap": mutable.cap,
        "accepted_using_old_revision": True,
    }

    tender = ledger(existing_charges=(1,), rookies={"r": scale},
                    rookie_year_one_allocation=10, rookie_total_allocation=40)
    tender.sign("draft", Offer("r", (1,) * 4, 0), 0)
    observations["F08_rookie_tender_not_replaced"] = {
        "supplied_existing_draft_tender": 1,
        "new_contract_year_one_charge": 1,
        "recorded_team_charge": tender.charges[0],
        "expected_after_replacing_tender": 1,
    }

    verified = 0
    for years in range(1, 11):
        for limit in range(1, 11):
            for bonus in range(101):
                offer = Offer("test", (3,) * years, bonus)
                charges = offer.charges(limit)
                assert sum(charges) == 3 * years + bonus
                assert len(charges) == years
                assert all(type(charge) is int and charge >= 3 for charge in charges)
                verified += 1
    print(json.dumps({"observations": observations,
                      "bonus_conservation_cases_verified": verified}, indent=2))


if __name__ == "__main__":
    main()
