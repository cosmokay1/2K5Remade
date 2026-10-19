"""Reconcile published rookie tables with the dated contract already on record.

These are annual source cap schedules, not offers or evidence of paid cash.
Drafted and replacement practice contracts must retain their separate lineage.
"""
from copy import deepcopy
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
import re
from urllib.parse import urlsplit

from tools.reconcile_week1_contracts import _dollars
from tools.resolve_week1_players import normalize_name


def _money(text):
    if not re.fullmatch(r'\$[\d,]+', text.strip()):
        raise ValueError('Explicit whole-dollar source amount required')
    return int(text.strip().replace('$', '').replace(',', ''))


def _cells(line):
    return [c.strip() for c in line.split('|')]


def _contract_fingerprint(row):
    fields = ('otc_id', 'gsis_id', 'player', 'draft_year', 'draft_round',
              'draft_overall', 'year_signed', 'years', 'is_active', 'value', 'contract_history')
    return hashlib.sha256(json.dumps({k:row.get(k) for k in fields},
        sort_keys=True, allow_nan=False).encode()).hexdigest()


def reconcile_rookie_page(text, archived, *, season_year):
    """Accept only matching identity, slot, original/replacement terms and total."""
    if (type(season_year) is not int or archived.get('draft_year') != season_year
            or archived.get('year_signed') != season_year or archived.get('is_active') is not True
            or archived.get('years') not in (1, 3, 4) or not archived.get('gsis_id')):
        raise ValueError('Unique active current-cohort contract required')
    url = re.search(r'\((https://overthecap\.com/player/[^)]+)\)', text)
    if not url or urlsplit(url[1]).path.rstrip('/').split('/')[-1] != str(archived['otc_id']):
        raise ValueError('Source belongs to another OTC identity')
    source_hash = hashlib.sha256(text.encode()).hexdigest()
    clean = re.sub(r'(?m)^L\d+: ?', '', text)
    clean = re.sub(r'cite[^†\n]*†([^\n]*)', r'\1', clean)
    name = re.search(r'(?m)^### ([^\n]+)$', clean)
    drafted = archived.get('draft_round') is not None
    slot = re.search(r'Entry: (\d{4}) Draft, Round ([1-7]), #(\d+) overall', clean)
    undrafted = re.search(r'Entry: (\d{4}) Undrafted Free Agent\b', clean)
    if not name or not (slot if drafted else undrafted):
        raise ValueError('Player heading or draft entry missing/truncated')
    if (normalize_name(name[1]) != normalize_name(archived['player'])
            or (drafted and tuple(map(int, slot.groups())) !=
                (season_year, archived['draft_round'], archived['draft_overall']))
            or (not drafted and int(undrafted[1]) != season_year)):
        raise ValueError('Source name, draft year, round or slot differs')
    history = [r for r in archived.get('contract_history', []) if r.get('status') == 'Active']
    if len(history) != 1:
        raise ValueError('Archived active contract lineage differs')
    kind = history[0].get('contract_type')
    allowed = ((kind == 'Drafted' and drafted and archived['years'] == 4)
        or (kind == 'UDFA' and not drafted and archived['years'] == 3)
        or (kind == 'Practice' and archived['years'] == 1)
        or (kind == 'SFA' and (archived['years'] == 1 or
                              (not drafted and archived['years'] == 3))))
    if not allowed:
        raise ValueError('Unsupported rookie contract term')
    if (history[0].get('year_signed') != season_year or history[0].get('yrs') != archived['years']
            or _dollars(history[0]['total']) != _dollars(archived['value'])):
        raise ValueError('Archived active contract lineage differs')
    section = clean.split('#### Current Contract\n', 1)
    if len(section) != 2 or not re.match(r'##### \('+kind+r', signed '+str(season_year)+r'\)', section[1]):
        raise ValueError('Published current contract is a different contract generation')
    annual_section = re.split(r'\n#### (?:Cash Flows|Contract Notes|Contract History)', section[1], 1)[0]
    lines = annual_section.splitlines()
    header = next((i for i, line in enumerate(lines) if line.startswith('Year  |') or line.startswith('Year |')), None)
    if header is None:
        raise ValueError('Annual contract table missing')
    headings = lines[header]
    if header+1 < len(lines) and lines[header+1].startswith('Number '):
        headings += lines[header+1]
    columns = [re.sub(r'\s+', '', c).casefold() for c in _cells(headings)]
    def cell(cells, key, *, required=False):
        if key not in columns:
            if required:raise ValueError('Required annual source column missing')
            return None
        at = columns.index(key)
        if at >= len(cells) or not cells[at]:
            if required:raise ValueError('Required annual amount missing')
            return None
        return _money(cells[at])
    annual = []
    for line in lines[header+1:]:
        if not re.match(r'^20\d\d\b.*\|', line):
            continue
        cells = _cells(line)
        year = int(cells[0][:4])
        if not season_year <= year < season_year+int(archived['years']):
            raise ValueError('Unsupported additional contract year or option')
        base = cell(cells, 'basesalary', required=True)
        bonus = cell(cells, 'proratedsigningbonus')
        cap = cell(cells, 'capnumber', required=True)
        other = {k:cell(cells, k) for k in ('rosterbonus','workoutbonus','optionbonus',
                                           'pergamerosterbonus','otherbonus')}
        if (kind == 'Drafted' and bonus is None) or (kind != 'Practice' and other['optionbonus']):
            raise ValueError('Unsupported drafted bonus allocation')
        components_match = cap == base + (bonus or 0) + sum(v for v in other.values() if v is not None)
        annual.append({'year':year, 'base_salary_dollars':base,
                       'allocated_bonus_dollars':bonus, 'cap_dollars':cap,
                       'guaranteed_salary_dollars':cell(cells, 'guaranteedsalary'),
                       'cash_components_reconcile':components_match, **other})
    years = list(range(season_year, season_year+int(archived['years'])))
    if [r['year'] for r in annual] != years:
        raise ValueError('Complete unique annual schedule required')
    total = _dollars(archived['value'])
    if sum(r['cap_dollars'] for r in annual) != total:
        raise ValueError('Annual cap total differs from archived signed value')
    first_cap = re.search(r'\b'+str(season_year)+r' Salary Cap Charge: (\$[\d,]+)', clean)
    if not first_cap or _money(first_cap[1]) != annual[0]['cap_dollars']:
        raise ValueError('Annual cap differs from published first-year summary')
    current_history = clean.split('#### Contract History\n', 1)
    active = []
    if len(current_history) == 2:
        for line in current_history[1].splitlines():
            cells = _cells(line)
            if len(cells) >= 6 and cells[2] == 'Active':active.append(cells)
    if not active:
        raise ValueError('Active contract history table missing/truncated')
    if (len(active) != 1 or active[0][:5] != [history[0]['team'],kind,'Active',str(season_year),str(int(archived['years']))]
            or _money(active[0][5]) != total):
        raise ValueError('Current ownership or active contract history differs')
    return {'otc_id':archived['otc_id'], 'gsis_id':archived['gsis_id'],
            'archived_contract_fingerprint':_contract_fingerprint(archived),
            'contract_type':kind, 'team':history[0]['team'], 'annual':annual,
            'source_url':url[1], 'rendered_source_sha256':source_hash,
            'scope':'matched published schedule; no paid-cash or full-book authority',
            'published_components_reconcile':all(r['cash_components_reconcile'] for r in annual),
            'historical_annual_schedule_verified':False,
            'paid_cash_verified':False, 'signing_authorized':False}


def apply_rookie_schedules(contracts, reports):
    """Fill absent source rows; conflicting existing evidence is never overwritten."""
    result = deepcopy(contracts)
    seen = set()
    for report in reports:
        if report['otc_id'] in seen:
            raise ValueError('Duplicate rookie source report')
        seen.add(report['otc_id'])
        matches = [r for r in result if r.get('otc_id') == report['otc_id']
                   and r.get('gsis_id') == report['gsis_id']]
        if len(matches) != 1:
            raise ValueError('Unique archived contract identity required')
        row = matches[0]
        if _contract_fingerprint(row) != report['archived_contract_fingerprint']:
            raise ValueError('Archived contract changed since source reconciliation')
        for annual in report['annual']:
            year = annual['year']
            prior = [s for s in row['season_history'] if str(s.get('year')) in (str(year),str(year)+'.0')]
            if any(s.get('cap_number') is not None and
                   (_dollars(s['cap_number']) != annual['cap_dollars'] or s.get('team') != report['team']) for s in prior):
                raise ValueError('Published rookie schedule conflicts with dated annual evidence')
            if any(s.get('cap_number') is not None for s in prior):
                continue
            row['season_history'] = [s for s in row['season_history']
                if str(s.get('year')) not in (str(year),str(year)+'.0')]
            row['season_history'].append({'year':str(year), 'team':report['team'],
                'cap_number':str(Decimal(annual['cap_dollars'])/1_000_000),
                'source_url':report['source_url'], 'source_sha256':report['rendered_source_sha256'],
                'historical_annual_schedule_verified':False,
                'cash_paid':None})
    return result


def reconcile_rookie_sources(contracts, pages, *, season_year):
    """Audit the full supplied rookie cohort, including unavailable/conflicting pages."""
    if type(season_year) is not int:
        raise ValueError('Explicit integer season required')
    cohort = defaultdict(list)
    for row in contracts:
        if row.get('draft_year') == season_year and row.get('year_signed') == season_year:
            cohort[row['otc_id']].append(row)
    reports, errors, conflicts = {}, defaultdict(set), set()
    for page in pages:
        url = re.search(r'\((https://overthecap\.com/player/[^)]+)\)', page)
        if not url:
            continue
        identity = urlsplit(url[1]).path.rstrip('/').split('/')[-1]
        if not identity.isdigit() or int(identity) not in cohort:
            continue
        otc = int(identity)
        if len(cohort[otc]) != 1:
            errors[otc].add('Duplicate archived OTC identity')
            continue
        try:
            report = reconcile_rookie_page(page, cohort[otc][0], season_year=season_year)
        except ValueError as error:
            errors[otc].add(str(error))
            continue
        if otc in reports and reports[otc]['annual'] != report['annual']:
            conflicts.add(otc)
        else:
            reports[otc] = report
    for otc in conflicts:
        reports.pop(otc, None)
        errors[otc].add('Conflicting published schedules')
    unresolved = []
    for otc, rows in cohort.items():
        if otc not in reports:
            unresolved.append({'otc_id':otc, 'player':rows[0]['player'],
                'reasons':sorted(errors[otc] or {'Source page unavailable'})})
    return {'season_year':season_year, 'requested':sum(map(len, cohort.values())),
            'matched_published_schedules':len(reports),
            'contract_types':dict(Counter(r['contract_type'] for r in reports.values())),
            'reports':list(reports.values()), 'unresolved':unresolved,
            'historical_annual_schedule_verified':False,
            'complete_opening_books':False, 'signing_authorized':False}


if __name__ == '__main__':
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contracts', type=Path, help='Dated archive JSON containing rows')
    parser.add_argument('--sources', type=Path, nargs='+', required=True,
                        help='Rendered OTC pages; each capture may contain multiple pages')
    parser.add_argument('--season-year', type=int, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--updated-contracts', type=Path,
                        help='Optional comparison copy; never an authorized opening ledger')
    args = parser.parse_args()
    inputs = {args.contracts.resolve(), *(path.resolve() for path in args.sources)}
    outputs = [path.resolve() for path in (args.report, args.updated_contracts) if path]
    if len(set(outputs)) != len(outputs) or inputs.intersection(outputs):
        parser.error('Report and comparison outputs must be separate from every input')
    contracts = json.loads(args.contracts.read_text())['rows']
    pages = [page for path in args.sources
             for page in re.split(r'\n-{5,}\n', path.read_text())]
    report = reconcile_rookie_sources(contracts, pages, season_year=args.season_year)
    report['archived_contracts_sha256'] = hashlib.sha256(args.contracts.read_bytes()).hexdigest()
    updated = apply_rookie_schedules(contracts, report['reports'])
    args.report.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    if args.updated_contracts:
        args.updated_contracts.write_text(json.dumps({'rows':updated}, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('reports','unresolved')}))
