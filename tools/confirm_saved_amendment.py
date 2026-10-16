"""Verify saved native amendment effects and expose retained debt still to enforce.

No save/memory mutation, cash payment assumption, settlement or write authority.
A supplemental cap adapter is required before these native effects are usable.
"""
import hashlib
from fractions import Fraction

from franchise.cap import Offer,json_amount
from franchise.books import parse_amount
from franchise.legacy_amendments import RULE
from tools.franchise_snapshot_bindings import resolve_bindings,binding_money_scale
from tools.franchise_offer_state import expected_amended_state
from tools.franchise_finance_state import saved_finance_state
from tools.franchise_identity_state import saved_identity_state
from tools.export_legacy_contracts import legacy_contracts
from tools.inspect_franchise_cap import inspect_cap
from tools.inspect_franchise_save import TEAMS


def confirm_saved_amendment(bindings,before,after,*,expected_before_sha256,offer,guest_offer,team_id,comparison):
    """The comparison must be frozen to recorded consent by the coordinator."""
    if (type(before) is not bytes or type(after) is not bytes or before==after
            or type(expected_before_sha256) is not str
            or hashlib.sha256(before).hexdigest()!=expected_before_sha256):
        raise ValueError('Pinned distinct before/after amendment saves required')
    if not isinstance(offer,Offer) or team_id not in TEAMS:
        raise ValueError('Typed amendment and owning team required')
    if (type(comparison) is not dict or comparison.get('rule')!=RULE
            or comparison.get('requires_player_agreement') is not True
            or comparison.get('settlement_authorized') is not False
            or comparison.get('within_modeled_cap') is not True):
        raise ValueError('Noncommitting affordable amendment comparison required')
    old_cap=inspect_cap(before);new_cap=inspect_cap(after)
    old_team=old_cap['teams'][team_id];new_team=new_cap['teams'][team_id]
    accelerated=new_team['original_first_year_accumulator_dollars']!=old_team['original_first_year_accumulator_dollars']
    expected=expected_amended_state(bindings,before,offer=offer,guest_offer=guest_offer,team_id=team_id,
        native_bonus_accelerated=accelerated)
    original_state=(saved_finance_state(before),saved_identity_state(before))
    if expected==original_state:
        raise ValueError('Unchanged native terms cannot prove a new amendment')
    if (saved_finance_state(after),saved_identity_state(after))!=expected:
        raise ValueError('Saved native effects differ from the isolated amendment target')
    members=resolve_bindings(bindings,after)
    slot=next(slot for slot,p in members.items() if p['player_id']==offer.player_id)
    old=next(c for c in legacy_contracts(bindings,before)[team_id] if c.player_id==offer.player_id)
    from franchise.legacy_contracts import original_annual_rows
    rows=original_annual_rows(old.amount_word,old.bonus_code,old.shape_code,old.original_years)
    rows=rows[old.original_years-old.remaining_years:]
    native_old=old.charges();native_new=offer.charges(5)
    def amounts(name):
        values=comparison[name]
        if type(values) is not list or not 1<=len(values)<=15:
            raise ValueError('Complete bounded amendment charge schedule required')
        parsed=tuple(parse_amount(v) for v in values)
        if any(v<0 for v in parsed):
            raise ValueError('Negative amendment obligation')
        return parsed
    current=amounts('current_charges')
    carried=amounts('carried_bonus_charges')
    horizon=max(len(current),len(native_old))
    required=[]
    for i in range(horizon):
        native=native_old[i] if i<len(native_old) else 0
        extra=(current[i] if i<len(current) else 0)-native
        if extra<0:
            raise ValueError('Comparison discards existing native contract charges')
        required.append(extra+(rows[i]['allocated_bonus_dollars']*old.game_dollar_scale if i<len(rows) else 0))
    if carried!=tuple(required):
        raise ValueError('Amendment removed or rescheduled retained bonus debt')
    added=list(native_new)
    if 'earned_pay' in comparison:
        from franchise.legacy_amendments import InSeasonAmendmentScope,amendment_scope_from_dict
        earned=comparison['earned_pay']
        scope=amendment_scope_from_dict(earned['scope'])
        if not isinstance(scope,InSeasonAmendmentScope) or current!=native_old:
            raise ValueError('First in-season amendment requires an independently matched prior salary schedule')
        earned_base=Fraction((native_old[0]-rows[0]['allocated_bonus_dollars']*old.game_dollar_scale)*scope.elapsed_periods,scope.total_periods)
        remaining=scope.remaining_base(offer.salaries[0])
        if (parse_amount(earned['earned_base_obligation'])!=earned_base or
                parse_amount(earned['remaining_base_commitment'])!=remaining):
            raise ValueError('Saved amendment changed its earned salary obligation')
        added[0]+=earned_base+remaining-offer.salaries[0]
    if amounts('new_contract_charges')!=tuple(added):
        raise ValueError('Amendment changed new salary or bonus charges')
    horizon=max(len(required),len(added))
    combined=tuple((required[i] if i<len(required) else 0)+(added[i] if i<len(added) else 0) for i in range(horizon))
    if amounts('combined_player_charges')!=combined:
        raise ValueError('Combined amended charges disagree with retained debt')
    before_team=amounts('annual_team_charges_before')
    after_team=amounts('annual_team_charges_after')
    wanted=tuple((before_team[i] if i<len(before_team) else 0)-(current[i] if i<len(current) else 0)+
                 (combined[i] if i<len(combined) else 0) for i in range(max(len(before_team),len(current),len(combined))))
    if after_team!=wanted:
        raise ValueError('Amendment team posting disagrees with the saved change')
    cap=inspect_cap(after);scale=binding_money_scale(bindings)
    if comparison['cap']!=cap['league_cap_dollars']*scale or parse_amount(comparison['room_after'])!=comparison['cap']-after_team[0]-parse_amount(comparison['reserved_cap']):
        raise ValueError('Amendment cap or room changed')
    native_records=legacy_contracts(bindings,after)[team_id]
    native_team=tuple(sum((c.charges()[i] if i<len(c.charges()) else 0) for c in native_records)
                      for i in range(max(map(lambda c:len(c.charges()),native_records),default=1)))
    debt=tuple((after_team[i] if i<len(after_team) else 0)-(native_team[i] if i<len(native_team) else 0)
               for i in range(max(len(after_team),len(native_team))))
    if 'earned_pay' not in comparison and any(v<0 for v in debt):
        raise ValueError('Supplemental cap debt cannot erase native charges')
    from franchise.native_cap import amendment_payroll_projection
    projection=amendment_payroll_projection(comparison,
        native_payroll_before_raw=old_team['roster_payroll_dollars']//1000,
        native_old_charge=native_old[0],native_new_charge=native_new[0],
        native_old_unamortized_bonus=sum(row['allocated_bonus_dollars'] for row in rows)*scale,
        native_accumulator_before_raw=old_team['original_first_year_accumulator_dollars']//1000,
        native_accumulator_after_raw=new_team['original_first_year_accumulator_dollars']//1000,
        team_adjustment_applies=bool(new_team['original_team_flag_raw']),game_dollar_scale=scale)
    return dict(cap_projection=projection,format='saved-amendment-effects-v1',franchise_id=bindings['franchise_id'],player_id=offer.player_id,
        source_slot=slot,team_id=team_id,before_payload_sha256=expected_before_sha256,
        after_payload_sha256=hashlib.sha256(after).hexdigest(),offer=offer.to_dict(),
        native_annual_team_charges_after=list(native_team),
        required_retained_team_charges=[json_amount(v) for v in debt],
        combined_player_charges=[json_amount(v) for v in combined],
        cap_enforcement_verified=False,write_authorized=False,
        scope='isolated saved native effects; supplemental cap enforcement and application authority unverified')
