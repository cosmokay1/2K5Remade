"""Offline asking prices from explicit annual-value comparables, never cap fits.

An authored simulator policy, not an NFL contract appraisal. Inputs are owned by
an importer/operator, never supplied by the offer being negotiated. No writes,
ratings, network, team-room discounts or signing authority.
"""
from fractions import Fraction
from hashlib import sha256
import json
from math import gcd

from franchise.guest_contracts import GuestContractTerms, guest_money_scale
from franchise.performance import PerformanceEvidence

VERSION = 'local-position-market-v1'
METRICS = {'QB':'passing_yards', 'WR':'receiving_yards', 'TE':'receiving_yards',
           'RB':'rushing_yards', 'DE':'sacks', 'DT':'sacks', 'OLB':'sacks'}
POSITIONS = frozenset(('QB','K','P','WR','CB','FS','SS','RB','FB','TE','OLB','ILB','C','G','T','DT','DE'))


def positive(value):
    if type(value) is not int or value <= 0:
        raise ValueError('Positive integer dollars/counts required')
    return value


def text(value):
    if type(value) is not str or not value.strip():
        raise ValueError('Explicit identity and provenance required')
    return value


def rate(data, player, metric):
    if data is None:
        return None
    evidence = PerformanceEvidence.from_context(data)
    if evidence.player_id != player:
        raise ValueError('Performance belongs to another player')
    values = evidence.to_context()['observations']
    games = values.get('games', {}).get('value')
    value = values.get(metric, {}).get('value')
    if evidence.complete_window is not True or games is None or games < 8 or value is None:
        return None
    return (evidence.window, evidence.mode, Fraction(value, games))


def native_demand(player, annual_value, minimums, years, bonus_code, contract_format):
    """Least balanced representable contract meeting price AND every base floor."""
    if type(years) is not int or not 1 <= years <= 5:
        raise ValueError('One to five explicit asking years required')
    if type(bonus_code) is not int or not 0 <= bonus_code <= 10:
        raise ValueError('Supported explicit bonus percentage code required')
    if type(minimums) is not list or len(minimums) < years:
        raise ValueError('Verified annual minimums required for the entire asking term')
    for minimum in minimums:
        positive(minimum)
    positive(annual_value)
    guest_money_scale(contract_format)
    step = years // gcd(years, bonus_code) if bonus_code else 1

    def offer(units):
        return GuestContractTerms(units * step, bonus_code, 2, years).to_offer(
            player, contract_format=contract_format)

    def sufficient(value):
        return (all(base >= floor for base, floor in zip(value.salaries, minimums))
                and sum(value.salaries) + value.signing_bonus >= annual_value * years)

    low, high = 1, 65535 // step
    if not sufficient(offer(high)):
        raise ValueError('Asking price or minimum cannot fit native contract encoding')
    while low < high:
        mid = (low + high) // 2
        if sufficient(offer(mid)):
            high = mid
        else:
            low = mid + 1
    return offer(low)


def build_pricebook(data):
    required = {'format','team_id','league_cap','contract_format','market','players'}
    if type(data) is not dict or set(data) != required or type(data['format']) is not int or data['format'] != 1:
        raise ValueError('Complete server-owned pricebook input required')
    text(data['team_id']); positive(data['league_cap']); guest_money_scale(data['contract_format'])
    market = data['market']
    if type(market) is not dict or set(market) != {'cap','as_of','source','comparables'}:
        raise ValueError('Explicit dated market and reference cap required')
    positive(market['cap']); text(market['source']); text(market['as_of'])
    if type(market['comparables']) is not list or not market['comparables'] or type(data['players']) is not list:
        raise ValueError('Market comparables and player profiles required')
    peers, identities = [], set()
    for row in market['comparables']:
        keys={'player_id','position','annual_value','rookie','source'}
        if (type(row) is not dict or not keys <= set(row) or set(row)-keys-{'performance'}
                or type(row['position']) is not str or row['position'] not in POSITIONS or type(row['rookie']) is not bool):
            raise ValueError('Comparable requires a position, actual APY and explicit rookie classification')
        text(row['player_id']); text(row['source']); positive(row['annual_value'])
        if row['player_id'] in identities:
            raise ValueError('Duplicate market player')
        identities.add(row['player_id'])
        rate(row.get('performance'),row['player_id'],METRICS.get(row['position']))
        if not row['rookie']:
            peers.append(row)
    digest=sha256(json.dumps(data,sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()
    quotes, reports, seen = {}, {}, set()
    for profile in data['players']:
        keys={'player_id','position','rookie','minimum_salaries','years','bonus_code','source'}
        if (type(profile) is not dict or not keys <= set(profile) or set(profile)-keys-{'performance'}
                or type(profile['position']) is not str or profile['position'] not in POSITIONS or type(profile['rookie']) is not bool):
            raise ValueError('Explicit supported player classification and asking structure required')
        player=text(profile['player_id']); text(profile['source'])
        if player in seen:
            raise ValueError('Duplicate player profile')
        seen.add(player)
        if profile['rookie']:
            reports[player]={'unpriced':'Rookie scale/options use their separate accounting path'}
            continue
        group=[r for r in peers if r['position']==profile['position']]
        own=next((r for r in group if r['player_id']==player),None)
        others=[r for r in group if r['player_id']!=player]
        if own is None and len(others)<3:
            reports[player]={'unpriced':'No own annual-value source and fewer than three positional comparables'}
            continue
        values=sorted(r['annual_value'] for r in others)
        anchor=Fraction(own['annual_value']) if own else (Fraction(values[(len(values)-1)//2])+values[len(values)//2])/2
        reason='own_sourced_annual_value' if own else 'positional_median_missing_complete_performance'
        production=rate(profile.get('performance'),player,METRICS.get(profile['position']))
        observed=[]
        if production is not None:
            for row in others:
                sample=rate(row.get('performance'),row['player_id'],METRICS.get(profile['position']))
                if sample is not None and sample[:2]==production[:2]:
                    observed.append((sample[2],row))
        if len(observed)>=3:
            # Midrank makes ties order-independent. Map production rank into the
            # observed veteran APY distribution, with exact rational interpolation.
            below=sum(value<production[2] for value,_ in observed)
            tied=sum(value==production[2] for value,_ in observed)
            rank=min(Fraction(1),Fraction(2*below+tied,2*len(observed)))
            prices=sorted(row['annual_value'] for _,row in observed)
            point=rank*(len(prices)-1);index=point.numerator//point.denominator
            anchor=Fraction(prices[index])
            if index+1<len(prices):anchor+=(prices[index+1]-prices[index])*(point-index)
            reason='complete_production_positional_market_rank'
        target=(anchor*Fraction(data['league_cap'],market['cap'])).__ceil__()
        demand=native_demand(player,target,profile['minimum_salaries'],profile['years'],
                             profile['bonus_code'],data['contract_format'])
        report={'rule_version':VERSION,'input_sha256':digest,'position':profile['position'],
                'market_as_of':market['as_of'],'market_source':market['source'],
                'reference_cap':market['cap'],'league_cap':data['league_cap'],
                'target_annual_value':target,'basis':reason,
                'comparable_player_ids':sorted(r['player_id'] for r in group),
                'minimum_source':profile['source'], 'reference_annual_value':[anchor.numerator,anchor.denominator],
                'represented_annual_value':[sum(demand.salaries)+demand.signing_bonus,profile['years']],
                'amount_above_reference':[sum(demand.salaries)+demand.signing_bonus-target*profile['years'],profile['years']]}
        if production is not None:
            report.update(performance=profile['performance'],matching_performance_peers=len(observed))
        # Keep the native 4 KiB response frame bounded. Full evidence stays in
        # the export report; the journal carries its reproducible content hash.
        compact={k:report[k] for k in ('rule_version','input_sha256','position','market_as_of',
                                      'reference_cap','league_cap','target_annual_value','basis')}
        quotes[player]={'offer':demand.to_dict(),'source':json.dumps(compact,sort_keys=True,allow_nan=False)}
        reports[player]=report
    if not quotes:
        raise ValueError('No supported veteran asking prices; local negotiation stays unconfigured')
    return {'policy':{'format':1,'enabled':True,'signing_enabled':False,
                      'team_id':data['team_id'],'quotes':quotes},'report':reports}
