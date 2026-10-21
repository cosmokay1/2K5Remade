"""Fit opening cap schedules to native fields; exact source money stays separate.

The five-field representation is cap liability, not guaranteed money or paid
cash. Never infer a signing bonus from the guarantee total. No live/save writes.
"""
from decimal import Decimal
from hashlib import sha256
import math

from franchise.legacy_contracts import original_annual_rows
from tools.reconcile_week1_contracts import CLUBS

FIELDS = ('contract_value', 'contract_bonus', 'contract_type', 'contract_length', 'contract_remaining')


def dollars(value):
    amount = Decimal(str(value)) * 1000000
    if not amount.is_finite() or amount < 0 or amount != int(amount):
        raise ValueError('Exact nonnegative source dollars required')
    return int(amount)


def source_schedule(charge, archive, year):
    """Keep the accepted current charge fixed; append unambiguous owned years."""
    first = charge['cap_dollars']
    if type(first) is not int or first <= 0:
        raise ValueError('Positive opening charge required')
    candidates = [r for r in archive if r.get('gsis_id') == charge['gsis_id'] and r.get('is_active') is True]
    histories = []
    for contract in candidates:
        rows = [r for r in contract.get('season_history', []) if str(r.get('year')) == str(year)
                and r.get('team') == CLUBS[charge['team']]]
        if len(rows) == 1 and rows[0].get('cap_number') is not None and dollars(rows[0]['cap_number']) == first:
            histories.append((contract, rows[0]))
    if len(histories) != 1:
        return [first], None, 'accepted_current_charge_only'
    contract, opening = histories[0]
    schedule = [first]
    for season in range(year + 1, year + 15):
        rows = [r for r in contract['season_history'] if str(r.get('year')) == str(season)
                and r.get('team') == CLUBS[charge['team']]]
        if len(rows) != 1 or rows[0].get('cap_number') is None or dollars(rows[0]['cap_number']) == 0:
            break
        schedule.append(dollars(rows[0]['cap_number']))
    bonus = dollars(opening['prorated_bonus']) if opening.get('prorated_bonus') is not None else None
    return schedule, bonus, 'owned_source_annual_schedule'


def fit_fields(targets, *, scale, bonus_target=None):
    """Fit remaining liabilities, prioritizing current charge and known proration.

    Original-game bonus steps cannot express arbitrary dollars. Record residuals;
    don't silently discard a sourced positive bonus to improve a curve fit.
    """
    if (type(scale) is not int or scale not in (1, 4) or not 1 <= len(targets) <= 15
            or any(type(v) is not int or v <= 0 for v in targets)
            or (bonus_target is not None and (type(bonus_target) is not int or bonus_target < 0))):
        raise ValueError('Supported exact annual targets and bonus allocation required')
    n = len(targets); quantum = 1000 * scale; best = None
    for shape in range(8):
        for bonus in range(11):
            if bonus_target is not None and ((bonus_target > 0) != (bonus > 0)):
                continue
            probe = original_annual_rows(10000, bonus, shape, n)[0]['original_game_charge_dollars'] * scale
            if probe <= 0:
                continue
            center = targets[0] * 10000 / probe
            for value in range(max(1, math.floor(center) - 4), min(65535, math.ceil(center) + 4) + 1):
                rows = original_annual_rows(value, bonus, shape, n)
                actual = [r['original_game_charge_dollars'] * scale for r in rows]
                represented_bonus = rows[0]['allocated_bonus_dollars'] * scale
                # First-year rounding tolerance is one native display quantum.
                key = (max(0, abs(actual[0] - targets[0]) - quantum),
                       abs(represented_bonus - bonus_target) if bonus_target is not None else 0,
                       sum((a-b)**2 for a,b in zip(actual,targets)), bonus, shape != 2, value)
                if best is None or key < best[0]:
                    best = key, dict(zip(FIELDS, (value, bonus, shape, n, n))), actual, represented_bonus
    if best is None:
        raise ValueError('Schedule exceeds native contract range')
    _, fields, actual, represented_bonus = best
    return dict(fields=fields, source_cap_dollars=targets, represented_cap_dollars=actual,
                residual_dollars=[a-b for a,b in zip(targets, actual)],
                source_prorated_bonus_dollars=bonus_target, represented_bonus_dollars=represented_bonus,
                cash_or_guarantees_verified=False)


def fit_roster(codec, payload, assembly_receipt, charges, archive, *, scale):
    if sha256(payload).hexdigest() != assembly_receipt['output_sha256']:
        raise ValueError('Pinned assembled roster required')
    if set(charges['teams']) != set(CLUBS):
        raise ValueError('All32 source club books required')
    doc = codec.RosterDocument(payload, base=0x20, base_year=charges['season_year'], reference_year=charges['season_year'])
    if doc.to_body(normalise_commentary=False) != payload:
        raise ValueError('Lossless codec required')
    players = {p.index:p for p in doc.by_pool('primary')}
    bindings = assembly_receipt['bindings']; records = {}; allowed = set()
    for code, team in charges['teams'].items():
        for charge in team['players']:
            if charge['roster_status'] not in ('ACT', 'INA'):
                continue
            gsis = charge['gsis_id']
            if gsis in records or gsis not in bindings:
                raise ValueError('Unique bound active identity required')
            target = players[bindings[gsis]]
            schedule, bonus, basis = source_schedule(charge, archive, charges['season_year'])
            fit = fit_fields(schedule, scale=scale, bonus_target=bonus)
            target.record.values.update(fit['fields'])
            allowed.update(range(target.offset+10, target.offset+12))
            allowed.update(range(target.offset+36, target.offset+40))
            sources=[r for r in archive if r.get('gsis_id')==gsis and r.get('is_active') is True]
            source_base=[]
            for i,cap in enumerate(schedule):
                rows=[a for r in sources for a in r.get('season_history',[]) if str(a.get('year'))==str(charges['season_year']+i)
                      and a.get('team')==CLUBS[code] and a.get('cap_number') is not None and dollars(a['cap_number'])==cap]
                # Missing salary detail stays explicitly modeled, never paid cash.
                salary=(dollars(rows[0]['base_salary']) if len(rows)==1 and rows[0].get('base_salary') is not None
                        else max(0,cap-fit['represented_bonus_dollars']))
                source_base.append(salary)
            records[gsis] = dict(team=code,source_slot=target.index,basis=basis,
                source_base_dollars=source_base,source_nonbase_dollars=[cap-base for cap,base in zip(schedule,source_base)],**fit)
    # A qualified unsigned player has no active contract with the receiving club.
    # Clear stale creator-roster terms; prior-club debt stays in source books.
    free={g:players[s] for g,s in bindings.items() if players[s].offset in doc.free_agents}
    if set(free)!=set(bindings)-set(records) or len(free)!=len(doc.free_agents):
        raise ValueError('Complete qualified free-agent inventory required')
    unsigned=dict(zip(FIELDS,(0,0,2,0,0)))
    for player in free.values():
        player.record.values.update(unsigned)
        allowed.update(range(player.offset+10,player.offset+12))
        allowed.update(range(player.offset+36,player.offset+40))
    result = doc.to_body(normalise_commentary=False)
    if len(result) != len(payload) or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(payload,result))):
        raise ValueError('Non-contract roster bytes changed')
    reloaded = codec.RosterDocument(result,base=0x20,base_year=charges['season_year'],reference_year=charges['season_year'])
    if reloaded.to_body(normalise_commentary=False) != result:
        raise ValueError('Fitted contracts fail lossless reload')
    for gsis, record in records.items():
        actual = reloaded.by_pool('primary')[record['source_slot']].record.values
        if any(actual[k] != v for k,v in record['fields'].items()):
            raise ValueError('Reloaded native terms differ')
    for player in free.values():
        if any(reloaded.by_pool('primary')[player.index].record.values[k]!=v for k,v in unsigned.items()):
            raise ValueError('Qualified free agent retains an active contract')
    return result, dict(format='week1-native-contract-fit-v1',input_sha256=sha256(payload).hexdigest(),
        output_sha256=sha256(result).hexdigest(),game_dollar_scale=scale,players=records,
        cleared_free_agent_contracts=sorted(free),
        exact_sources_preserved=True,native_terms_are_approximations=True,
        game_load_verified=False,signing_authorized=False)
