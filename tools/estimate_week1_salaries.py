"""User-authorized opening cap estimates, separate from historical contract facts.

Never fit prices to team room, alter a known annual charge, or declare paid cash,
bonus debt or free-agent availability. These are cap projections, not new offers.
"""
from collections import Counter, defaultdict
from fractions import Fraction
from statistics import median
import hashlib
import json

from franchise.minimums import minimum_salary
from tools.reconcile_week1_contracts import CLUBS, _dollars, league_source_coverage

VERSION = 'week1-positional-estimates-v1'
STATUSES = {'ACT', 'INA', 'RES', 'DEV', 'EXE'}


def _status(member):
    return ('practice' if member['status'] in ('DEV', 'EXE') else
            'reserve' if member['status'] == 'RES' else 'active')


def _experience(member):
    years = member.get('years_exp')
    if isinstance(years, bool) or not isinstance(years, int) or years < 0:
        raise ValueError('Explicit nonnegative simulation experience required')
    return 0 if years == 0 else 1 if years <= 3 else 4 if years <= 6 else 7


def _position(member):
    return member.get('depth_chart_position') or member.get('position')


def _contract(rows, member, year):
    found = rows.get(member.get('gsis_id'), [])
    if len(found) != 1 or found[0].get('is_active') is not True:
        return None
    row = found[0]
    active = [r for r in row.get('contract_history', []) if r.get('status') == 'Active']
    if (len(active) != 1 or active[0].get('team') != CLUBS[member['team']]
            or active[0].get('year_signed') != row.get('year_signed')
            or active[0].get('yrs') != row.get('years')
            or not isinstance(row.get('year_signed'), (int, float))
            or not isinstance(row.get('years'), (int, float))
            or not row['year_signed'] <= year < row['year_signed'] + row['years']):
        return None
    try:
        if _dollars(active[0]['total']) != _dollars(row['value']) or _dollars(row['value']) == 0:
            return None
    except (KeyError, ValueError):
        return None
    return row


def _allocate(total, weights):
    """Whole dollars, deterministic residual; the supplied nominal total is preserved."""
    denominator = sum(weights)
    shares = [Fraction(total) * w / denominator for w in weights]
    values = [v.numerator // v.denominator for v in shares]
    order = sorted(range(len(values)), key=lambda i: (-(shares[i]-values[i]), i))
    for i in order[:total-sum(values)]:
        values[i] += 1
    return values


def estimate_opening_charges(weekly, contracts, rookie_reports, *, season_year, league_cap):
    """Fill comparison gaps with independently priced, explicitly modeled charges.

    Rating and team budget are absent from pricing inputs. league_cap is used
    only for diagnostics after every player's charge has been selected.
    """
    if type(league_cap) is not int or league_cap <= 0:
        raise ValueError('Explicit positive integer league cap required')
    weekly, contracts = list(weekly), list(contracts)
    rookie_reports = list(rookie_reports)
    template_ids = set()
    for report in rookie_reports:
        annual = report.get('annual', [])
        if (report['otc_id'] in template_ids or not annual or
                [a['year'] for a in annual] != list(range(season_year, season_year+len(annual)))
                or any(type(a.get('cap_dollars')) is not int or a['cap_dollars'] <= 0 for a in annual)):
            raise ValueError('Unique positive complete rookie comparison schedules required')
        template_ids.add(report['otc_id'])
    coverage = league_source_coverage(weekly, contracts, season_year=season_year)
    members = [r for r in weekly if r.get('season') == season_year and r.get('week') == 1
               and r.get('game_type') == 'REG' and r.get('status') in STATUSES]
    keys = [(m['team'], m['full_name']) for m in members]
    ids = [m['gsis_id'] for m in members if m.get('gsis_id')]
    if len(set(keys)) != len(keys) or len(set(ids)) != len(ids):
        raise ValueError('Duplicate roster identity/owner cannot be priced twice')
    by_gsis = defaultdict(list)
    for row in contracts:
        if row.get('gsis_id'):
            by_gsis[row['gsis_id']].append(row)
    observed, peers, zero_active = {}, [], set()
    for member in members:
        _experience(member)
        if not _position(member):
            raise ValueError('Explicit source position required')
        team = coverage['teams'][member['team']]
        entry = next(p for p in team['players'] if p['name'] == member['full_name'])
        key = (member['team'], member['full_name'])
        if entry['cap_dollars'] is None:
            continue
        if entry['cap_dollars'] == 0 and member['status'] in ('ACT', 'INA'):
            # A source placeholder is not a playable active salary. Keep the
            # archived zero as evidence while modeling the missing obligation.
            zero_active.add(key)
            continue
        row = by_gsis[member['gsis_id']][0]
        annual = next(s for s in row['season_history'] if str(s.get('year')) in
                      (str(season_year), str(season_year)+'.0') and s.get('team') == team['team_name'])
        observed[key] = (entry['cap_dollars'], 'published_matching_contract_estimate'
                        if annual.get('historical_annual_schedule_verified') is False
                        else 'archived_annual_source')
        contract = _contract(by_gsis, member, season_year)
        peers.append(dict(member=member, cap=entry['cap_dollars'],
                          apy=_dollars(contract['apy']) if contract and contract.get('apy') else None))
    results, unresolved = [], []
    for member in members:
        key = (member['team'], member['full_name'])
        entry = dict(team=member['team'], player=member['full_name'],
                     gsis_id=member.get('gsis_id'), position=_position(member),
                     roster_status=member['status'], source_identity_present=bool(member.get('gsis_id')),
                     native_identity_binding_verified=False,
                     paid_cash_verified=False, signing_authorized=False)
        if key in observed:
            cap, basis = observed[key]
            results.append(dict(entry, cap_dollars=cap, basis=basis))
            continue
        contract = _contract(by_gsis, member, season_year)
        if key in zero_active:
            entry['archived_zero_cap_placeholder_dollars'] = 0
            if contract and contract['years'] == 1 and contract['year_signed'] == season_year:
                results.append(dict(entry, cap_dollars=_dollars(contract['value']),
                    basis='modeled_one_year_nominal_charge', nominal_total_preserved=True,
                    method='positive_current_deal_with_zero_annual_placeholder'))
                continue
        # A signed rookie total is stronger evidence than a veteran positional APY.
        if contract and contract.get('draft_year') == season_year:
            years = int(contract['years'])
            matches = [r for r in rookie_reports if r['contract_type'] ==
                       next(h['contract_type'] for h in contract['contract_history'] if h['status'] == 'Active')
                       and len(r['annual']) == years]
            if years == 4 and contract.get('draft_overall'):
                slots = {r['otc_id']:r.get('draft_overall') for r in contracts if r.get('otc_id') is not None}
                matches = [r for r in matches if slots.get(r['otc_id']) is not None]
                matches = sorted(matches, key=lambda r: (abs(slots[r['otc_id']]-contract['draft_overall']),
                                                         r['otc_id']))[:4]
            elif years == 4:
                matches = []
            if len(matches) >= 3 or (years == 1 and matches):
                weights = [median([Fraction(r['annual'][i]['cap_dollars'],
                                            sum(a['cap_dollars'] for a in r['annual']))
                                   for r in matches]) for i in range(years)]
                total = _dollars(contract['value'])
                amounts = _allocate(total, weights)
                results.append(dict(entry, cap_dollars=amounts[0], basis='modeled_rookie_allocation',
                    signed_total_dollars=total, nominal_total_preserved=True,
                    annual_cap_projection=[dict(year=season_year+i, cap_dollars=v)
                                           for i,v in enumerate(amounts)],
                    comparable_otc_ids=sorted(r['otc_id'] for r in matches),
                    method='nearest_draft_slots' if years == 4 else 'same_rookie_contract_type'))
                continue
        group = [p for p in peers if _position(p['member']) == _position(member)
                 and _status(p['member']) == _status(member)]
        fallback = None
        if len(group) < 3 and _position(member) == 'LB':
            group = [p for p in peers if _position(p['member']) in ('ILB','MLB','OLB','LB')
                     and _status(p['member']) == _status(member)]
            fallback = 'linebacker_family'
        if len(group) < 3 and _status(member) == 'practice':
            # PS/exempt compensation is primarily an experience/roster-role tier.
            group = [p for p in peers if _status(p['member']) == 'practice']
            fallback = 'practice_experience_tier'
        if len(group) < 3 and _status(member) == 'reserve':
            # No unsupported injury/split discount when reserve peers are scarce.
            group = [p for p in peers if _position(p['member']) == _position(member)
                     and _status(p['member']) == 'active']
            fallback = 'reserve_full_salary_projection'
        narrowed = [p for p in group if _experience(p['member']) == _experience(member)]
        if len(narrowed) >= 3:
            group = narrowed
        if len(group) < 3:
            unresolved.append(dict(entry, reason='Fewer than three positional/status comparables'))
            continue
        apy = _dollars(contract['apy']) if contract and contract.get('apy') else None
        ratios = [Fraction(p['cap'], p['apy']) for p in group if p['apy']]
        own_apy = apy is not None and len(ratios) >= 3
        target = Fraction(apy) * median(ratios) if own_apy else median([Fraction(p['cap']) for p in group])
        floor = (minimum_salary(season_year, member['years_exp'], 'active_inactive')
                 if _status(member) == 'active' else min(p['cap'] for p in group))
        amount = max(floor, ((target.numerator + target.denominator*500)//(target.denominator*1000))*1000)
        results.append(dict(entry, cap_dollars=amount, basis='modeled_positional_charge',
                            method='own_apy_peer_cap_ratio' if own_apy else 'positional_status_median',
                            fallback=fallback,
                            comparable_gsis_ids=sorted(p['member']['gsis_id'] for p in group)))
    teams = {}
    for code in CLUBS:
        players = [r for r in results if r['team'] == code]
        gaps = [r for r in unresolved if r['team'] == code]
        subtotal = sum(p['cap_dollars'] for p in players)
        teams[code] = dict(players=players, unresolved=gaps,
            roster_charge_subtotal=subtotal if not gaps else None,
            known_and_estimated_subtotal=subtotal,
            gross_cap_less_roster_only=league_cap-subtotal if not gaps else None,
            cap_room=None, retained_and_adjustments_verified=False)
    return dict(version=VERSION, season_year=season_year, teams=teams,
                club_members=len(members), charge_basis_counts=dict(Counter(r['basis'] for r in results)),
                unresolved=len(unresolved), league_cap=league_cap,
                input_sha256=hashlib.sha256(json.dumps([weekly,contracts,rookie_reports],
                    sort_keys=True, allow_nan=False).encode()).hexdigest(),
                membership_at_cutoff_verified=False,
                rookie_contracts_without_week1_owner=[dict(player=r['player'],gsis_id=r.get('gsis_id'),
                    team=r.get('team'), rights_review_required=True) for r in contracts
                    if r.get('draft_year') == season_year and r.get('year_signed') == season_year
                    and r.get('gsis_id') not in ids],
                complete_opening_books=False, free_agent_pool_verified=False,
                ready_for_franchise_test=False, signing_authorized=False, writes_performed=False)


if __name__ == '__main__':
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('weekly', type=Path, help='Week 1 source JSON containing rows')
    parser.add_argument('contracts', type=Path, help='Contract comparison JSON containing rows')
    parser.add_argument('rookies', type=Path, help='Rookie source audit containing reports')
    parser.add_argument('--season-year', type=int, required=True)
    parser.add_argument('--league-cap', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in {args.weekly.resolve(), args.contracts.resolve(), args.rookies.resolve()}:
        parser.error('Estimate output cannot replace a source input')
    result = estimate_opening_charges(json.loads(args.weekly.read_text())['rows'],
        json.loads(args.contracts.read_text())['rows'], json.loads(args.rookies.read_text())['reports'],
        season_year=args.season_year, league_cap=args.league_cap)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'teams'}))
