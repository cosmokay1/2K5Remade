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


def release_findings():
    from datetime import date
    from franchise.books import ActiveContract
    from franchise.cash import CashObligation
    from franchise.guarantees import DiscountProfile
    from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
    findings={}
    for day,expected in ((date(2026,6,1),(39,0,0)),(date(2026,6,2),(33,6,0))):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'release.sqlite'
            store=FranchiseStore(path)
            contract=ActiveContract(Offer('v',(10,20,30),9,(0,20,10)),'synthetic audit original')
            store.create_team('a',Ledger.from_opening(OpeningBooks(contracts=(contract,)),cap=30,
                roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3,'free':(1,)*3}))
            store.initialize_cash('a',(CashObligation('contract:v','v',69,9,'synthetic bank',(('signing_bonus',9),)),),
                                  source='synthetic complete payment coverage')
            inputs=dict(scope=PreseasonReleaseScope(2026,day,date(2026,9,10),EXCLUDED_LIABILITIES,True,True,0,
                'synthetic verified exclusions'),discount=DiscountProfile(2026,Fraction(0),'synthetic zero discount'),
                payment_year_offsets=(0,1,2),expected_revision=1,access_check=lambda:None)
            receipt=store.release_preseason_veteran('a','release','v',**inputs)
            reopened=FranchiseStore(path)
            assert reopened.release_preseason_veteran('a','release','v',**inputs) == receipt
            current=reopened.load_team('a')
            assert current.charges == expected and current.revision == 2
            assert current.financial_snapshot()['signed_players'] == []
            assert current.cash_snapshot()['nominal_total'] == 39 and current.cash_snapshot()['unpaid_total'] == 30
            before=current.financial_snapshot()
            try:
                reopened.sign('a','unaffordable',Offer('free',(1,),0),2)
            except Rejected:
                pass
            else:
                raise AssertionError('Release-induced cap debt allowed a new signing')
            assert reopened.load_team('a').financial_snapshot() == before
            findings[day.isoformat()]={'annual_cap':list(expected),'current_room':json_amount(current.room),
                'nominal_cash':39,'paid_cash':9,'unpaid_cash':30,'cancelled_unearned_base':30,
                'ownership_removed':True,'restart_receipt_identical':True,'unaffordable_signing_rejected':True}
    return {'scenarios':findings,'scope':'Synthetic supported healthy preseason veteran release; zero rate is not a published rate; game/runtime and complete NFL lifecycle unverified'}


def trade_findings():
    from datetime import date
    from franchise.books import ActiveContract
    from franchise.cash import CashObligation
    from franchise.trades import PreseasonTradeScope,EXCLUDED_TRADE_LIABILITIES
    scenarios={}
    for day,expected in ((date(2026,6,1),(9,0,0)),(date(2026,6,2),(3,6,0))):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'assignment.sqlite'
            store=FranchiseStore(path)
            contract=ActiveContract(Offer('v',(10,20,30),9,(0,20,10)),'synthetic audit original')
            for team in ('seller','buyer'):
                store.create_team(team,Ledger.from_opening(OpeningBooks(contracts=(contract,)) if team=='seller' else OpeningBooks(),
                    cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
                records=(CashObligation('contract:v','v',69,9,'synthetic bank',(('signing_bonus',9),)),) if team=='seller' else ()
                store.initialize_cash(team,records,source='synthetic complete cash')
            inputs=dict(scope=PreseasonTradeScope(2026,day,date(2026,9,10),date(2026,9,11),
                EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'synthetic assignment facts'),
                seller_revision=1,buyer_revision=1,access_check=lambda:None)
            receipt=store.trade_preseason_veteran('audit','seller','buyer','v',**inputs)
            reopened=FranchiseStore(path)
            assert reopened.trade_preseason_veteran('audit','seller','buyer','v',**inputs)==receipt
            seller,buyer=reopened.load_team('seller'),reopened.load_team('buyer')
            assert seller.charges==expected and buyer.charges==(10,20,30)
            assert seller.financial_snapshot()['signed_players']==[] and buyer.financial_snapshot()['signed_players']==['v']
            assert buyer.contract_terms('v')['guaranteed_salaries']==[0,20,10]
            assert seller.cash_snapshot()['unpaid_total']==0 and buyer.cash_snapshot()['unpaid_total']==60
            assert seller.cash_snapshot()['nominal_total']+buyer.cash_snapshot()['nominal_total']==69
            assert seller.revision==buyer.revision==2
            scenarios[day.isoformat()]={'seller_cap':list(expected),'buyer_cap':[10,20,30],
                'seller_paid_cash':9,'buyer_unpaid_cash':60,'combined_nominal_cash':69,
                'buyer_protected_base':[0,20,10],'exclusive_buyer_ownership':True,'restart_receipt_identical':True}
    return {'scenarios':scenarios,'scope':'Synthetic supported preseason contract assignment; consideration and real game/runtime unverified'}


def restructure_findings():
    from datetime import date
    from franchise.books import ActiveContract
    from franchise.cash import CashObligation
    from franchise.restructures import (EXCLUDED_RESTRUCTURE_TERMS,
        PreseasonRestructureScope, calculate_preseason_restructure)
    contract = ActiveContract(Offer('v', (10,10,10,20,30,40,50), 10,
        (10,10,10,20,0,0,0)), 'synthetic original', elapsed_years=2)
    cash = CashObligation('contract:v','v',180,30,'synthetic allocated cash',
        (('signing_bonus',10),('base:0',10),('base:1',10)))
    scope = PreseasonRestructureScope(2026,date(2026,6,1),date(2026,9,10),0,
        True,True,True,EXCLUDED_RESTRUCTURE_TERMS,'synthetic floors','synthetic amendment')
    plan = calculate_preseason_restructure(contract,cash,scope=scope,
        converted_base=8,annual_minimums=(2,)*5,record_id='audit:conversion')
    expected = tuple(Fraction(n,5) for n in (28,118,168,208,258))
    assert plan.contract.charges() == expected
    assert sum(expected) == sum(contract.charges())
    assert plan.cash_obligation.amount == cash.amount and plan.cash_obligation.paid == cash.paid
    assert plan.bonus_layer.cash_component not in dict(plan.cash_obligation.paid_components)
    from dataclasses import replace
    from franchise.releases import EXCLUDED_LIABILITIES, PreseasonReleaseScope, calculate_preseason_release
    from franchise.guarantees import DiscountProfile
    from franchise.trades import EXCLUDED_TRADE_LIABILITIES, PreseasonTradeScope, calculate_preseason_trade
    released = calculate_preseason_release(plan.contract,plan.cash_obligation,
        scope=PreseasonReleaseScope(2026,date(2026,6,2),date(2026,9,10),EXCLUDED_LIABILITIES,
            True,True,0,'synthetic layered release'),discount=DiscountProfile(2026,Fraction(0),'synthetic zero rate'),
        payment_year_offsets=(0,1,2,3,4),record_id='audit:release')
    assert released.charges() == (Fraction(128,5),Fraction(52,5))
    assert (released.cash_obligation.amount,released.cash_obligation.paid) == (60,30)
    settled = replace(plan.cash_obligation,paid=38,
        paid_components=plan.cash_obligation.paid_components+((plan.bonus_layer.cash_component,8),))
    traded = calculate_preseason_trade(plan.contract,settled,
        scope=PreseasonTradeScope(2026,date(2026,6,2),date(2026,9,10),date(2026,9,11),
            EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'synthetic layered assignment'),record_id='audit:trade')
    assert traded.retained_bonus.annual_charges == (Fraction(18,5),Fraction(52,5))
    assert (traded.seller_cash.amount,traded.buyer_cash.amount) == (38,142)
    return {'scope':'pure synthetic calculation; no durable amendment or game posting',
            'before_charges':contract.charges(),'after_charges':expected,
            'nominal_cash':cash.amount,'paid_cash':cash.paid,
            'new_unpaid_bonus':plan.bonus_layer.amount,
            'old_bonus_remaining':6,'new_bonus_component':plan.bonus_layer.cash_component,
            'layered_release_charges':released.charges(),'layered_release_cash':60,
            'layered_trade_seller_bonus':traded.retained_bonus.annual_charges,
            'layered_trade_cash':{'seller':38,'buyer':142}}


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
                      "supported_release_path": release_findings(),
                      "supported_assignment_path": trade_findings(),
                      "pure_restructure_calculation": restructure_findings(),
                      "implemented_component_scope": {
                          "cash": "Nominal sourced obligations, component-allocated payments and guarantee present-value projections; full settlement/vesting is incomplete.",
                          "guarantees": "Explicit fully guaranteed base salary terms; no partial injury/skill/cap protection or automatic vesting.",
                          "roster": "Read-only sourced top-51 and regular-season supported salary/bonus projections; not complete Team Salary or a phase transition.",
                          "termination": "Supported sourced healthy preseason veteran release with retained bonus/guarantee debt and nominal cash; other release liabilities remain unsupported.",
                          "assignment": "Atomic sourced preseason veteran contract assignment; seller bonus debt and buyer base/guarantees retained; consideration and other trade rules unsupported.",
                          "draft": "Durable ordered rights and management funding reservations; actual game pick/contract posting remains unverified.",
                      },
                      "unimplemented_accounting": ["complete cash settlement and guarantee protections/vesting", "complete releases and trades",
                          "extensions and durable restructures", "complete Team Salary and roster-phase transitions", "season rollover and carryover",
                          "complete rookie options/escalators", "verified game import/posting"],
                      "bonus_conservation_cases_verified": verified}, indent=2, default=json_amount))


if __name__ == "__main__":
    main()
