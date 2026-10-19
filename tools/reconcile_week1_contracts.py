"""Compare Week 1 native contract charges with a dated source, without writes.

Cap numbers are not salary, signing bonus, guarantees or paid cash. This audit
does not invent retained charges, convert missing values to zero, or certify a
complete team book from its roster subtotal.
"""
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import re

from franchise.legacy_contracts import original_annual_rows
from tools.inspect_roster_save import inspect_roster
from tools.reconcile_roster_trial import _terms


def _dollars(value):
    if value is None or isinstance(value, bool):
        raise ValueError('Missing money is not zero')
    try:
        amount = Decimal(str(value))*1_000_000
        if not amount.is_finite() or amount < 0 or amount != amount.to_integral_value():
            raise ValueError('Nonnegative exact integer dollars required')
        return int(amount)
    except InvalidOperation as error:
        raise ValueError('Invalid source money') from error


def reconcile_week1(source_payload, identity_report, contract_rows, source_receipt, *, cutoff, money_scale):
    roster = inspect_roster(source_payload)
    if identity_report['source_sha256'] != roster['payload_sha256']:
        raise ValueError('Identity report belongs to another roster')
    day = date.fromisoformat(cutoff)
    if day.year != identity_report['season_year'] or money_scale != 4 or type(money_scale) is not int:
        raise ValueError('Explicit matching season and verified SOFTDRINK scale required')
    if (not re.fullmatch('[a-f0-9]{64}', source_receipt.get('sha256', ''))
            or not source_receipt.get('url', '').startswith('https://')):
        raise ValueError('Pinned dated contract source required')
    if date.fromisoformat(source_receipt['archive_as_of'][:10]) > day:
        raise ValueError('Later contract source cannot establish opening liabilities')
    by_gsis = defaultdict(list)
    for row in contract_rows:
        if row.get('gsis_id'):
            by_gsis[row['gsis_id']].append(row)
    by_slot = defaultdict(list)
    for gsis, player in identity_report['source_identities'].items():
        for slot in player['source_slots']:
            by_slot[slot].append(gsis)
    teams = {}
    for team, players in roster['teams'].items():
        entries = []
        for player in players:
            slot = player['source_slot'];entry = {**player, 'source_cap_dollars': None,
                'native_charge_dollars': None, 'proposed_cap_difference': None}
            ids = by_slot[slot]
            rows = (by_gsis[ids[0]] if len(ids) == 1 and
                    identity_report['source_identities'][ids[0]]['source_slots'] == [slot] else [])
            if len(ids) != 1 or len(rows) != 1:
                entry['status'] = 'unresolved_identity_or_contract'
                entries.append(entry);continue
            row = rows[0];entry.update(gsis_id=ids[0], otc_id=row.get('otc_id'))
            # Source team on a particular annual row determines ownership.
            seasons = [s for s in row.get('season_history', []) if str(s.get('year')) in
                       (str(day.year), str(day.year)+'.0')]
            normalized_team = 'Commanders' if team == 'Redskins' else team
            owned = [s for s in seasons if s.get('team') in (team, normalized_team)]
            unique = {repr(sorted(s.items())): s for s in owned}
            if len(unique) != 1 or row.get('is_active') is not True:
                entry['status'] = 'unresolved_current_year_ownership'
                entries.append(entry);continue
            annual = next(iter(unique.values()))
            try:
                cap = _dollars(annual.get('cap_number'))
            except ValueError:
                entry['status'] = 'unresolved_source_amount'
                entries.append(entry);continue
            entry['source_cap_dollars'] = cap
            terms = _terms(source_payload, slot)
            remaining, years = terms['remaining_years'], terms['original_years']
            try:
                if not 0 < remaining <= years:
                    raise ValueError('Unsupported native term')
                annual_native = original_annual_rows(terms['amount_word'], terms['bonus_code'],
                                                    terms['shape_code'], years)
                native = annual_native[years-remaining]['original_game_charge_dollars']*money_scale
                entry.update(native_charge_dollars=native, proposed_cap_difference=cap-native,
                             status='dated_source_comparison_only')
            except ValueError:
                entry['status'] = 'unresolved_native_schedule'
            entries.append(entry)
        complete = all(p['status'] == 'dated_source_comparison_only' for p in entries)
        teams[team] = {'players': entries, 'roster_contracts_compared':
            sum(p['status'] == 'dated_source_comparison_only' for p in entries),
            'known_source_roster_subtotal': sum(p['source_cap_dollars'] for p in entries
                                                if p['source_cap_dollars'] is not None),
            'complete_source_roster_subtotal': sum(p['source_cap_dollars'] for p in entries) if complete else None,
            'complete_opening_book': False, 'cap_room': None}
    return {'source_roster_sha256': hashlib.sha256(source_payload).hexdigest(),
            'contract_source': source_receipt, 'cutoff': cutoff, 'money_scale': money_scale,
            'teams': teams, 'retained_and_reserve_liabilities_verified': False,
            'club_rollover_and_adjustments_verified': False,
            'ready_for_franchise_test': False, 'signing_authorized': False, 'writes_performed': False}


def club_source_coverage(weekly_rows, contract_rows, *, team_code, team_name, season_year):
    """Audit all club lists, including reserve/PS, before attempting an import.

    This is coverage of the supplied snapshots, not a dated membership correction
    or a full cap book. Transactions, retained charges and adjustments are separate.
    """
    if type(season_year) is not int or not team_code or not team_name:
        raise ValueError('Explicit club identity and season required')
    weekly = [r for r in weekly_rows if str(r.get('season')) == str(season_year)
              and str(r.get('week')) == '1' and r.get('game_type') == 'REG']
    members = [r for r in weekly if r.get('team') == team_code]
    if not members:
        raise ValueError('Club absent from supplied Week 1 snapshot')
    by_gsis = defaultdict(list)
    for row in contract_rows:
        if row.get('gsis_id'):
            by_gsis[row['gsis_id']].append(row)
    club_statuses = {'ACT', 'INA', 'RES', 'DEV', 'EXE'}
    counts = defaultdict(int)
    entries, excluded = [], []
    for member in members:
        status, gsis = member.get('status'), member.get('gsis_id')
        counts[status] += 1
        entry = {'gsis_id': gsis, 'name': member.get('full_name'),
                 'roster_status': status, 'cap_dollars': None}
        if status in ('CUT', 'RET'):
            excluded.append({**entry, 'retained_charge_verified': False})
            continue
        if status not in club_statuses:
            raise ValueError('Unknown roster status cannot be silently excluded')
        owners = [r for r in weekly if gsis and r.get('gsis_id') == gsis
                  and r.get('status') in club_statuses]
        contracts = by_gsis[gsis]
        if not gsis or len(owners) != 1 or len(contracts) != 1:
            entry['status'] = 'unresolved_identity_or_contract'
        else:
            row = contracts[0]
            annual = [s for s in row.get('season_history', [])
                      if str(s.get('year')) in (str(season_year), str(season_year)+'.0')
                      and s.get('team') == team_name]
            unique = {repr(sorted(s.items())):s for s in annual}
            if row.get('is_active') is not True or len(unique) != 1:
                entry['status'] = 'unresolved_current_year_ownership'
            else:
                try:
                    entry['cap_dollars'] = _dollars(next(iter(unique.values())).get('cap_number'))
                    entry['status'] = 'source_comparison_only'
                except ValueError:
                    entry['status'] = 'unresolved_source_amount'
        entries.append(entry)
    return {'team_code': team_code, 'team_name': team_name, 'season_year': season_year,
            'source_status_counts': dict(counts), 'players': entries, 'excluded_members': excluded,
            'contracts_compared': sum(p['cap_dollars'] is not None for p in entries),
            'known_roster_subtotal': sum(p['cap_dollars'] for p in entries if p['cap_dollars'] is not None),
            'complete_roster_subtotal': (sum(p['cap_dollars'] for p in entries)
                                        if all(p['cap_dollars'] is not None for p in entries) else None),
            'membership_at_cutoff_verified': False, 'complete_opening_book': False,
            'cap_room': None, 'signing_authorized': False, 'writes_performed': False}
