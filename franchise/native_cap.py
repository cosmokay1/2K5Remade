"""Current-year native payroll projection for an imported-contract amendment.

A projection is arithmetic, not a signing permit. The coordinator must bind its
inputs to consent and uninterrupted guest ownership before installing it. Native
bonus acceleration is offset once in payroll, preserving unrelated native debt.
"""
from fractions import Fraction

from franchise.books import parse_amount
from franchise.cap import json_amount
from franchise.legacy_amendments import RULE


def amendment_payroll_projection(comparison, *, native_payroll_before_raw,
        native_old_charge, native_new_charge, native_old_unamortized_bonus,
        native_accumulator_before_raw, native_accumulator_after_raw,
        team_adjustment_applies, game_dollar_scale):
    """Keep the league ceiling fixed and account for both native cap branches.

    Native recalculation includes the replacement's full annual salary, not the
    earned-old plus remaining-new salary. The resulting payroll correction may
    therefore be negative. Quantize the total liability up, never each player,
    retaining the exact difference as evidence rather than inventing cap room.
    """
    if (type(comparison) is not dict or comparison.get('rule')!=RULE
            or comparison.get('requires_player_agreement') is not True
            or comparison.get('settlement_authorized') is not False):
        raise ValueError('Bound noncommitting amendment comparison required')
    if type(game_dollar_scale) is not int or game_dollar_scale not in (1,4):
        raise ValueError('Verified original or scaled guest money units required')
    for value,limit in ((native_payroll_before_raw,0x7fffffff),
                        (native_accumulator_before_raw,65535),(native_accumulator_after_raw,65535)):
        if type(value) is not int or not 0<=value<=limit:
            raise ValueError('Bounded exact native payroll and accumulators required')
    if type(team_adjustment_applies) is not bool:
        raise ValueError('Explicit native cap-accessor branch required')
    def amount(value):
        result=parse_amount(value) if not isinstance(value,Fraction) else value
        if not 0<=result<=10**15:
            raise ValueError('Bounded exact nonnegative cap obligation required')
        return result
    quantum=1000*game_dollar_scale
    old,new,unamortized=map(amount,(native_old_charge,native_new_charge,native_old_unamortized_bonus))
    if any((v/quantum).denominator!=1 for v in (old,new,unamortized)):
        raise ValueError('Observed native contracts must exactly represent guest money')
    before=amount(comparison['annual_team_charges_before'][0])
    after=amount(comparison['annual_team_charges_after'][0])
    current=amount(comparison['current_charges'][0]);combined=amount(comparison['combined_player_charges'][0])
    cap=amount(comparison['cap']);reserve=amount(comparison['reserved_cap'])
    if (after!=before-current+combined or
            parse_amount(comparison['room_before'])!=cap-before-reserve or
            parse_amount(comparison['room_after'])!=cap-after-reserve or
            comparison['within_modeled_cap']!=(cap-after-reserve>=0)):
        raise ValueError('Amendment cap posting or affordability disagrees')
    native_before=native_payroll_before_raw*quantum
    # Caller supplies a reconciled native roster total. Prior supplemental debt
    # may be present in before; only this amendment's raw contract delta changes
    # the native recomputation. Do not discard any previous ledger charges.
    if native_before<old or before<current:
        raise ValueError('Player charge exceeds team payroll')
    native_after=native_before-old+new
    acceleration=(native_accumulator_after_raw-native_accumulator_before_raw)*quantum
    if acceleration<0 or acceleration not in (0,unamortized):
        raise ValueError('Unexplained native bonus accumulator change')
    if acceleration and not team_adjustment_applies:
        raise ValueError('Native bonus acceleration requires the adjusted cap branch')
    withheld_before=native_accumulator_before_raw*quantum if team_adjustment_applies else 0
    withheld_after=native_accumulator_after_raw*quantum if team_adjustment_applies else 0
    # Keep the pre-existing accumulator intact. The new native acceleration
    # already withholds this amount, so subtract it from payroll exactly once.
    required=after+reserve-acceleration
    if required<0:
        raise ValueError('Corrected native payroll is not representable; hold application')
    raw=required/quantum
    rounded=(raw.numerator+raw.denominator-1)//raw.denominator
    if rounded>0x7ffffffe or (cap/quantum).denominator!=1:
        raise ValueError('Cap projection exceeds native signed currency range')
    exact_room=cap-after-reserve-withheld_before
    native_room=cap-withheld_after-rounded*quantum
    return dict(format='native-amendment-payroll-v1',game_dollar_scale=game_dollar_scale,
        league_cap_raw=int(cap/quantum),native_payroll_after_raw=int(native_after/quantum),
        enforced_payroll_raw=rounded,baseline_accumulator_raw=native_accumulator_before_raw,
        expected_accumulator_raw=native_accumulator_after_raw,team_adjustment_applies=team_adjustment_applies,
        exact_required_payroll=json_amount(required),rounding_charge=json_amount(rounded*quantum-required),
        exact_room_after=json_amount(exact_room),native_room_after=json_amount(native_room),
        within_cap=exact_room>=0 and native_room>=0,write_authorized=False)
