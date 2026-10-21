"""Opening liability estimates and explicitly authorized room calibration.

Later published club totals are proxies, not backdated facts. Known complete
totals take precedence. Independent-budget mode leaves deficits in place; room
calibration is separately labeled and never rewrites known obligations.
"""
from datetime import date
import hashlib
import json
import re

from tools.reconcile_week1_contracts import CLUBS


def published_club_proxies(text, *, season_year, base_cap, as_of):
    if season_year != 2026 or type(season_year) is not int or base_cap != 301_200_000:
        raise ValueError('This capture adapter supports the explicit 2026 base cap only')
    if date.fromisoformat(as_of).year != season_year:
        raise ValueError('Explicit source observation date required')
    url = 'https://overthecap.com/salary-cap-space'
    if '('+url+')' not in text:
        raise ValueError('Matching published cap-space source required')
    clean = re.sub(r'(?m)^L\d+: ?','',text)
    clean = re.sub(r'cite[^†\n]*†([^\n]*)',r'\1',clean)
    sections = clean.split('#### Base Salary Cap: ')
    if len(sections) < 2 or not sections[1].startswith('$301,200,000\n'):
        raise ValueError('Published first table is not the expected 2026 cap')
    inv = {v:k for k,v in CLUBS.items()}
    def money(value):
        if not re.fullmatch(r'\$[\d,]+|\(\$[\d,]+\)',value):
            raise ValueError('Explicit published whole-dollar amount required')
        return int(value.strip('()').replace('$','').replace(',','')) * (-1 if value.startswith('(') else 1)
    clubs = {}
    for line in sections[1].splitlines():
        cells = [v.strip() for v in line.split('|')]
        if len(cells) != 6 or cells[0] not in inv:
            continue
        code = inv[cells[0]]
        if code in clubs:
            raise ValueError('Duplicate club in published cap table')
        room, active, dead = (money(cells[i]) for i in (1,4,5))
        if min(active,dead) < 0:
            raise ValueError('Negative spending/debt is not supported')
        clubs[code] = dict(observed_active=active,observed_dead=dead,observed_room=room,
                           implied_net_adjustment=room+active+dead-base_cap)
    if set(clubs) != set(CLUBS):
        raise ValueError('All 32 independent club observations required')
    return dict(season_year=season_year,base_cap=base_cap,as_of=as_of,clubs=clubs,
                source_url=url,source_sha256=hashlib.sha256(text.encode()).hexdigest())


def model_opening_cap(charges, proxies, *, cutoff, allow_modeled_missing_obligations=False,
                      known_totals=None, calibrate_to_published_room=False):
    """Use observed external club budgets, not the opening roster's cap deficit.

    known_totals contains dated complete totals and/or retained_components.
    Partial player debt establishes a floor, never a complete club debt total.
    """
    day = date.fromisoformat(cutoff)
    if (not allow_modeled_missing_obligations or charges['season_year'] != day.year
            or proxies['season_year'] != day.year or charges['league_cap'] != proxies['base_cap']
            or set(charges['teams']) != set(CLUBS) or set(proxies['clubs']) != set(CLUBS)
            or charges['unresolved'] != 0):
        raise ValueError('Authorized model, matching season and complete all-team charges required')
    known_totals = {} if known_totals is None else known_totals
    if not set(known_totals) <= set(CLUBS):
        raise ValueError('Unknown club in known totals')
    teams = {}
    for code in CLUBS:
        source = proxies['clubs'][code];known = known_totals.get(code,{})
        if known and (not known.get('source') or not known.get('as_of')
                      or date.fromisoformat(known['as_of']) > day):
            raise ValueError('Dated provenance required for known opening totals')
        components = known.get('retained_components', [])
        seen, floor = set(), 0
        for component in components:
            identity = component.get('obligation_id')
            amount = component.get('dollars')
            if (not identity or identity in seen or type(amount) is not int or amount < 0
                    or not component.get('source') or not component.get('as_of')
                    or date.fromisoformat(component['as_of']) > day):
                raise ValueError('Unique dated retained obligations with integer amounts required')
            seen.add(identity)
            floor += amount
        retained = known.get('retained_dollars',max(floor,source['observed_dead']))
        adjustment = known.get('net_adjustment_dollars',source['implied_net_adjustment'])
        if type(retained) is not int or retained < 0 or type(adjustment) is not int:
            raise ValueError('Integer debt and signed net-adjustment totals required')
        if retained < floor:
            raise ValueError('Known complete total contradicts retained obligations')
        salary = charges['teams'][code]['roster_charge_subtotal']
        if type(salary) is not int or salary < 0:
            raise ValueError('Complete nonnegative club roster charge required')
        independent_adjustment = adjustment
        if calibrate_to_published_room and 'net_adjustment_dollars' not in known:
            # Explicit simulation policy: reconcile to an external room target.
            # This is not a claim about actual rollover, credits or NFL liabilities.
            adjustment = salary+retained+source['observed_room']-charges['league_cap']
        budget = charges['league_cap']+adjustment
        if budget <= 0:
            raise ValueError('Club adjusted budget must remain positive')
        room = budget-salary-retained
        teams[code] = dict(roster_charge_dollars=salary,retained_dollars=retained,
            net_adjustment_dollars=adjustment,adjusted_budget_dollars=budget,
            modeled_cap_room_dollars=room,requires_cap_compliance=room < 0,
            retained_basis='known_complete_total' if 'retained_dollars' in known else 'later_published_debt_proxy',
            confirmed_retained_components=components,
            confirmed_retained_subtotal_dollars=floor,
            unallocated_retained_dollars=retained-floor,
            retained_proxy_raised_to_known_floor=('retained_dollars' not in known and floor > source['observed_dead']),
            adjustment_basis=('known_complete_total' if 'net_adjustment_dollars' in known else
                              'simulation_room_calibration' if calibrate_to_published_room else
                              'independent_published_budget_proxy'),
            published_room_target_dollars=source['observed_room'],
            room_difference_from_target_dollars=room-source['observed_room'],
            simulation_calibration_dollars=adjustment-independent_adjustment,
            known_source=known or None)
    return dict(cutoff=cutoff,teams=teams,proxy_source=proxies,
                calibration_policy=('published_room_target' if calibrate_to_published_room else 'independent_budget_proxy'),
                salary_input_sha256=charges['input_sha256'],
                over_cap_clubs=[code for code,t in teams.items() if t['requires_cap_compliance']],
                complete_historical_books_verified=False,free_agent_pool_verified=False,
                native_identity_binding_verified=False,ready_for_franchise_test=False,
                signing_authorized=False,writes_performed=False)


if __name__ == '__main__':
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('charges', type=Path, help='Complete modeled opening charges JSON')
    parser.add_argument('capture', type=Path, help='Captured published 2026 all-team cap table')
    parser.add_argument('--cutoff', required=True)
    parser.add_argument('--observed-on', required=True, help='Actual later source date, never backdated')
    parser.add_argument('--known-totals', type=Path, help='Dated complete totals and/or retained_components by club')
    parser.add_argument('--allow-modeled-missing-obligations', action='store_true')
    parser.add_argument('--calibrate-to-published-room', action='store_true',
                        help='Explicit simulation calibration; preserve known adjustments and report conflicts')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inputs = [args.charges, args.capture] + ([args.known_totals] if args.known_totals else [])
    if args.output.resolve() in {path.resolve() for path in inputs}:
        parser.error('Model output cannot replace a source input')
    charges = json.loads(args.charges.read_text())
    proxies = published_club_proxies(args.capture.read_text(), season_year=charges['season_year'],
                                    base_cap=charges['league_cap'], as_of=args.observed_on)
    result = model_opening_cap(charges, proxies, cutoff=args.cutoff,
        allow_modeled_missing_obligations=args.allow_modeled_missing_obligations,
        calibrate_to_published_room=args.calibrate_to_published_room,
        known_totals=json.loads(args.known_totals.read_text()) if args.known_totals else None)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(clubs=len(result['teams']),over_cap_clubs=result['over_cap_clubs'],
                          ready_for_franchise_test=False,signing_authorized=False)))
