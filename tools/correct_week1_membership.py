"""Apply unambiguous dated transaction evidence to an isolated roster copy.

Names resolve through source GSIS identities. Unknown verbs, waived/injured,
temporary elevations and unordered same-day changes stay in review. Removing a
player never removes his prior club's retained-money review requirement.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import date
import hashlib
import json
import re
import unicodedata
from urllib.parse import urlsplit

from tools.reconcile_week1_contracts import CLUBS

VERBS = ('Signed|Re-signed|Waived|Released|Placed|Claimed|Acquired|Traded|Announced|'
         'Reinstated|Activated|Promoted|Elevated|Designated|Agreed|Tendered|Exercised|Terminated|'
         'Sign|Waive|Release|Place|Reverted|Reverts|Awarded|Reached')
ACTIVE = {'ACT','INA','RES','DEV','EXE'}
PRIMARY_DOMAINS = {'ARI': 'azcardinals.com', 'ATL': 'atlantafalcons.com', 'BAL': 'baltimoreravens.com', 'BUF': 'buffalobills.com', 'CAR': 'panthers.com', 'CHI': 'chicagobears.com', 'CIN': 'bengals.com', 'CLE': 'clevelandbrowns.com', 'DAL': 'dallascowboys.com', 'DEN': 'denverbroncos.com', 'DET': 'detroitlions.com', 'GB': 'packers.com', 'HOU': 'houstontexans.com', 'IND': 'colts.com', 'JAX': 'jaguars.com', 'KC': 'chiefs.com', 'LA': 'therams.com', 'LAC': 'chargers.com', 'LV': 'raiders.com', 'MIA': 'miamidolphins.com', 'MIN': 'vikings.com', 'NE': 'patriots.com', 'NO': 'neworleanssaints.com', 'NYG': 'giants.com', 'NYJ': 'newyorkjets.com', 'PHI': 'philadelphiaeagles.com', 'PIT': 'steelers.com', 'SEA': 'seahawks.com', 'SF': '49ers.com', 'TB': 'buccaneers.com', 'TEN': 'tennesseetitans.com', 'WAS': 'commanders.com'}


def club_table_rows(text, *, team, season_year, source_url):
    """Read a captured club table; caller declares its season, never its owner."""
    url = urlsplit(source_url)
    if (team not in CLUBS or url.scheme != 'https' or not url.hostname or
            url.hostname.removeprefix('www.') != PRIMARY_DOMAINS[team]
            or type(season_year) is not int):
        raise ValueError('Matching primary club source and explicit season required')
    years = re.findall(r'/((?:19|20)\d\d)(?:/|$)',url.path)
    if years and any(int(y) != season_year for y in years):
        raise ValueError('Source URL belongs to another season')
    for header in re.findall(r'(?m)^[^\n]+ \((https://[^)]+/team/transactions/[^)]*)\)\s*$', text):
        if urlsplit(header).hostname != url.hostname:
            raise ValueError('Split multi-document captures before assigning a source club')
    digest = hashlib.sha256(text.encode()).hexdigest()
    result = []
    for mm, dd, raw in re.findall(r'(?m)^L\d+: (\d\d)/(\d\d)\s*\|\s*(.+)',text):
        description = re.sub(r'cite[^†\n]*†([^\n]*)',r'\1',raw)
        split = re.match(r'^(.+?)\s+-\s+(.+)$',description)
        if split:
            actor, action = split.groups()
            if action.startswith('Practice Squad'):
                description = 'Signed '+actor+' to practice squad'
            elif action.startswith('Reserve/Injured'):
                description = 'Placed '+actor+' on injured reserve'
            elif re.match(r'^(?:Signed|Released|Waived|Terminated)\b',action,re.I):
                verb = action.split(',',1)[0]
                description = verb+' '+actor+' '+action[len(verb):]
        elif not re.match(r'^(?:'+VERBS+r')\b',description,re.I):
            postfix = re.match(r'^(.+?\([A-Z/]+\))\s+(signed|released|waived|placed)\b(.*)',description,re.I)
            if postfix:
                description = postfix[2]+' '+postfix[1]+postfix[3]
            else:
                description = re.sub(r'^(?:The\s+)?'+re.escape(CLUBS[team])+r'\s+(?:have\s+|has\s+)?',
                                     '',description,flags=re.I)
        result.append(dict(date=date(season_year,int(mm),int(dd)).isoformat(),team=team,
            description=description,raw_description=raw,primary_club_verified=True,
            verified_vested_termination='Terminated, Vested Veteran, all contracts' in raw,
            source_url=source_url,source_sha256=digest))
    return result


def primary_capture_rows(text, *, season_year):
    """Split rendered search documents by headers, not decorative separators.

    A web result can append its separator to the final body line. Treating that
    as a newline separator incorrectly attributes the next club to the first.
    """
    headers = list(re.finditer(r'(?m)^[^\n]+ \((https://[^)]+/team/transactions/[^)]*)\)\s*$',text))
    result = []
    inverse = {host:team for team,host in PRIMARY_DOMAINS.items()}
    for index, header in enumerate(headers):
        url = header[1]
        team = inverse.get((urlsplit(url).hostname or '').removeprefix('www.'))
        if team:
            page = text[header.start():headers[index+1].start() if index+1 < len(headers) else len(text)]
            result.extend(club_table_rows(page,team=team,season_year=season_year,source_url=url))
    return result


def _clauses(description, team):
    description = re.sub(r'\s+', ' ', description).strip()
    description = re.sub(r'^(?:The\s+)?(?:[A-Z][\w.-]*\s+){0,3}'+re.escape(CLUBS[team])+
                         r'\s+(?:have\s+|has\s+)?','',description)
    description = re.sub(r'\bThe team also\s+', '', description, flags=re.I)
    description = re.sub(r'(?<=\.)\s+(?=[A-Z][^.]+?\bcontract terminated\b)', '; ',description)
    clauses = re.split(r';\s*|(?:[.,]\s*(?:and\s+)?|\s+and\s+)(?=(?:'+VERBS+r')\b)',
                       description,flags=re.I)
    for clause in clauses:
        if not re.match(r'^(?:'+VERBS+r')\b',clause,re.I):
            postfix = re.match(r'^(.+?)\s+(signed|released|reverted|reverts|contract terminated)\b(.*)',clause,re.I)
            if postfix:
                clause = ('Terminated' if postfix[2].lower()=='contract terminated' else postfix[2])+' '+postfix[1]+postfix[3]
        clause = re.sub(r'^sign\b','Signed',clause,flags=re.I)
        clause = re.sub(r'^place\b','Placed',clause,flags=re.I)
        clause = re.sub(r'^waive\b','Waived',clause,flags=re.I)
        yield re.sub(r'^release\b','Released',clause,flags=re.I)


def _name(value):
    text = unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower()
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',text)).strip()


def transaction_events(rows, registry, *, start, cutoff, source_url, source_sha256):
    """Extract explicit membership actions; this is not a complete transaction feed."""
    day = date.fromisoformat(cutoff)
    first = date.fromisoformat(start)
    if first.year != day.year or first > day:
        raise ValueError('Explicit matching transaction interval required')
    if not source_url.startswith('https://') or not re.fullmatch('[a-f0-9]{64}',source_sha256):
        raise ValueError('Pinned transaction source required')
    aliases = defaultdict(set)
    player_positions = defaultdict(set)
    for player in registry:
        if not player.get('gsis_id'):
            continue
        if player.get('position'):
            player_positions[player['gsis_id']].add(player['position'])
        names = [player.get('full_name'),player.get('player')]
        if player.get('football_name') and player.get('last_name'):
            names.append(player['football_name']+' '+player['last_name'])
        for name in names:
            if name:
                aliases[_name(name)].add(player['gsis_id'])
    pattern = re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(n) for n in
                         sorted(aliases,key=lambda n:(-len(n),n)))+r')(?!\w)') if aliases else re.compile(r'(?!)')
    events = []
    for row in rows:
        when = date.fromisoformat(row['date'])
        if not first <= when <= day:
            continue
        team = {'LAR':'LA','WSH':'WAS'}.get(row['team'],row['team'])
        if team not in CLUBS:
            raise ValueError('Unsupported transaction club')
        if row.get('primary_club_verified') is True and (
                urlsplit(source_url).hostname not in (PRIMARY_DOMAINS[team],'www.'+PRIMARY_DOMAINS[team])):
            raise ValueError('Primary club attribution conflicts with source domain')
        clauses = _clauses(row['description'],team)
        for clause in clauses:
            normal = _name(clause)
            identities, ambiguous = set(), set()
            for match in pattern.finditer(normal):
                gsis = aliases[match[0]]
                if len(gsis) > 1:
                    before = normal[:match.start()].split()
                    after = normal[match.end():].split()
                    role = before[-1].upper() if before else ''
                    if role not in ('QB','RB','WR','TE','OL','G','T','C','DL','DT','DE','LB','DB','CB','S','K','P','LS','EDGE'):
                        role = after[0].upper() if after else ''
                    family = {'DT':{'DT','DL'},'DE':{'DE','DL','EDGE'},'CB':{'CB','DB'},
                              'S':{'S','DB'},'G':{'G','OL'},'T':{'T','OL'},'C':{'C','OL'}}.get(role,{role})
                    narrowed = {g for g in gsis if player_positions[g] & family}
                    if len(narrowed) == 1:
                        gsis = narrowed
                identities.update(gsis)
                if len(gsis) != 1:
                    ambiguous.update(gsis)
            state, reason = None, 'Unsupported transaction action'
            if re.match(r'^(?:Released|Terminated)\b',clause,re.I):
                state = 'CUT'
            elif re.match(r'^Waived\b',clause,re.I):
                if not re.search(r'\binjur',clause,re.I) or re.search(r'\bsettlement',clause,re.I):
                    state = 'CUT'
                else:
                    reason = 'Waived/injured requires clearance or reserve evidence'
            elif re.match(r'^Elevated\b',clause,re.I):
                state = 'TEMPORARY'
            elif re.match(r'^(?:Signed|Re-signed|Claimed|Awarded|Promoted|Activated|Reinstated)\b',clause,re.I):
                state = 'DEV' if re.search(r'\bto (?:[\w’\x27-]+\s+){0,3}practice squad',clause,re.I) else 'ACT'
                if re.search(r'standard elevation',clause,re.I):
                    state = 'TEMPORARY'
            elif re.match(r'^Revert(?:ed|s)\b',clause,re.I) and re.search('practice squad',clause,re.I):
                state = 'DEV'
            elif re.match(r'^Reached\b',clause,re.I) and re.search('injury settlements? with',clause,re.I):
                state = 'CUT'
            elif re.match(r'^Placed\b',clause,re.I) and re.search(
                    r'injured reserve|reserve/injured|physically unable|non.football injury|practice squad/injured',clause,re.I):
                state = 'DEV' if re.search('practice squad/injured',clause,re.I) else 'RES'
            elif re.match(r'^Announced\b',clause,re.I) and re.search(r'\bretirement\b',clause,re.I):
                state = 'RET'
            verb = re.match(r'^(?:'+VERBS+r')\b',clause,re.I)
            if verb and re.search(r'(?<![-/])\b(?:'+VERBS+r')\b(?![-/])',clause[verb.end():],re.I):
                state, reason = None, 'Mixed transaction actions require separate evidence'
            if re.search(r'reserve/futures|future contracts|extension|extended',clause,re.I):
                state, reason = 'AMENDMENT', 'Future contract or amendment does not establish current membership'
            for gsis in sorted(identities):
                player_state = None if gsis in ambiguous else state
                events.append(dict(gsis_id=gsis,team=team,date=row['date'],
                    status=player_state,reason=('Ambiguous name-to-GSIS identity' if gsis in ambiguous else
                                               reason if not state or state == 'AMENDMENT' else None),clause=clause,
                    source_url=source_url,source_sha256=source_sha256,
                    primary_club_verified=(row.get('primary_club_verified') is True and
                                           row.get('source_url') == source_url and
                                           row.get('source_sha256') == source_sha256),
                    unrestricted_release_verified=(state == 'CUT' and
                        row.get('verified_vested_termination') is True and
                        row.get('source_url') == source_url and row.get('source_sha256') == source_sha256)))
    return events


def correct_membership(weekly, events, *, cutoff):
    day = date.fromisoformat(cutoff)
    result = deepcopy(list(weekly))
    events = list(events)
    grouped = defaultdict(list)
    for event in events:
        when = date.fromisoformat(event['date'])
        if (when.year != day.year or when > day or event['team'] not in CLUBS
                or not event.get('gsis_id') or not event.get('source_url','').startswith('https://')
                or not re.fullmatch('[a-f0-9]{64}',event.get('source_sha256',''))):
            raise ValueError('Invalid/future transaction evidence')
        grouped[event['gsis_id']].append(event)
    corrections, reviews, retained, eligible, source_conflicts = [], [], [], [], []
    nonownership_events = []
    for gsis, history in sorted(grouped.items()):
        latest = max(r['date'] for r in history)
        last = [r for r in history if r['date'] == latest]
        primary = [r for r in last if r.get('primary_club_verified') is True]
        if primary:
            source_conflicts.extend(r for r in last if r not in primary and
                (r['team'],r['status']) not in {(p['team'],p['status']) for p in primary})
            last = primary
        states = {(r['team'],r['status']) for r in last}
        claims = [r for r in last if r.get('primary_club_verified') and r['status']=='ACT'
                  and re.match(r'^(?:Claimed|Awarded)\b',r['clause'],re.I)]
        if (len(claims) == 1 and all(r is claims[0] or
                r['status']=='CUT' and r['team']!=claims[0]['team'] and
                re.match(r'^Waived\b',r['clause'],re.I) for r in last)):
            last = claims
            states = {(claims[0]['team'],'ACT')}
        if len(states) != 1 or any(r['status'] is None for r in last):
            reviews.append(dict(gsis_id=gsis,date=latest,events=last,reason='Latest event needs review'))
            continue
        event = last[0];status = event['status']
        if status not in ACTIVE | {'CUT','RET','TEMPORARY','AMENDMENT'}:
            raise ValueError('Unsupported corrected status')
        members = [r for r in result if r.get('season') == day.year and r.get('week') == 1
                   and r.get('game_type') == 'REG' and r.get('gsis_id') == gsis]
        owners = [r for r in members if r['status'] in ACTIVE]
        if status in ('TEMPORARY','AMENDMENT'):
            if (len(owners) == 1 and owners[0]['team'] == event['team']
                    and (status == 'AMENDMENT' or owners[0]['status'] in ('DEV','EXE')
                         or re.search('from the practice squad|from practice squad',event['clause'],re.I))):
                if status == 'TEMPORARY' and owners[0]['status'] not in ('DEV','EXE'):
                    before = dict(team=owners[0]['team'],status=owners[0]['status'])
                    owners[0]['status'] = 'DEV'
                    corrections.append(dict(gsis_id=gsis,before=before,
                        after=dict(team=event['team'],status='DEV'),evidence=event))
                nonownership_events.append(dict(gsis_id=gsis,evidence=last,
                    ownership_preserved=True,contract_terms_review_required=status == 'AMENDMENT'))
            else:
                reviews.append(dict(gsis_id=gsis,events=last,reason='Nonownership event has no consistent base owner'))
            continue
        if len(owners) > 1:
            reviews.append(dict(gsis_id=gsis,events=last,reason='Multiple existing owners'))
            continue
        destination = [r for r in members if r['team'] == event['team']]
        if len(destination) > 1 or not members:
            reviews.append(dict(gsis_id=gsis,events=last,reason='Missing/duplicate source member'))
            continue
        if (owners and owners[0]['status'] in ('DEV','EXE') and status == 'ACT'
                and re.match(r'^(?:Activated|Promoted)\b',event['clause'],re.I)
                and not re.search(r'53.man|permanent',event['clause'],re.I)):
            reviews.append(dict(gsis_id=gsis,events=last,
                                reason='Practice-squad activation may be temporary'))
            continue
        if status in ('CUT','RET') and (not destination or owners and owners[0]['team'] != event['team']):
            reviews.append(dict(gsis_id=gsis,events=last,reason='Release does not match current owner'))
            continue
        if owners and status in ACTIVE and owners[0]['team'] != event['team'] and not event.get('primary_club_verified'):
            reviews.append(dict(gsis_id=gsis,events=last,
                                reason='Cross-club move requires independent confirmation'))
            continue
        member = destination[0] if destination else deepcopy(owners[0] if owners else members[0])
        if owners and (owners[0]['team'] != event['team'] or status in ('CUT','RET')):
            old = owners[0]
            retained.append(dict(gsis_id=gsis,team=old['team'],date=event['date'],
                                 charge_dollars=None,source=event,review_required=True))
            if old is not member:
                old['status'] = 'CUT'
        before = dict(team=member['team'],status=member['status'])
        if before != dict(team=event['team'],status=status):
            member.update(team=event['team'],status=status,membership_correction=event)
            if not destination:
                result.append(member)
            corrections.append(dict(gsis_id=gsis,before=before,after=dict(team=member['team'],status=status),
                                    evidence=event))
        if status == 'CUT' and all(r.get('unrestricted_release_verified') is True for r in last):
            eligible.append(dict(gsis_id=gsis,as_of=cutoff,evidence=last))
    return dict(cutoff=cutoff,rows=result,corrections=corrections,reviews=reviews,
                source_conflicts=source_conflicts,
                nonownership_events=nonownership_events,
                retained_liability_reviews=retained,verified_unrestricted_releases=eligible,
                membership_at_cutoff_verified=False,free_agent_pool_verified=False,
                writes_performed=False,signing_authorized=False,
                event_sha256=hashlib.sha256(json.dumps(events,sort_keys=True,allow_nan=False).encode()).hexdigest())


def classify_free_agent_candidates(candidates, membership, contracts, *, cutoff, identity_rows=(),
                                   archive_receipt=None):
    """Export an evidence-qualified subset; an unknown right is never a free player."""
    day = date.fromisoformat(cutoff)
    if membership.get('cutoff') != cutoff:
        raise ValueError('Matching membership cutoff required')
    dated_archive = (isinstance(archive_receipt,dict) and
        archive_receipt.get('archive_as_of','')[:10] == cutoff and
        archive_receipt.get('url','').startswith('https://') and
        re.fullmatch('[a-f0-9]{64}',archive_receipt.get('sha256','')) is not None)
    rows = [r for r in membership['rows'] if r.get('season') == day.year
            and r.get('week') == 1 and r.get('game_type') == 'REG']
    owners = {r['gsis_id'] for r in rows if r.get('gsis_id') and r['status'] in ACTIVE}
    retired = {r['gsis_id'] for r in rows if r.get('gsis_id') and r['status'] == 'RET'}
    disputed = {r['gsis_id'] for r in membership['reviews']}
    releases = {r['gsis_id']:r for r in membership['verified_unrestricted_releases']}
    active_contracts = {r['gsis_id'] for r in contracts if r.get('gsis_id') and r.get('is_active') is True}
    candidates = deepcopy(list(candidates))
    included = {g for c in candidates for g in c.get('archived_gsis_ids',[])}
    missing_release_identities = []
    for gsis in releases.keys()-included:
        matches = {(r['otc_id'],r['player']) for r in identity_rows
                   if r.get('gsis_id') == gsis and r.get('otc_id') is not None}
        if len(matches) != 1:
            missing_release_identities.append(gsis)
            continue
        otc, name = next(iter(matches))
        candidates.append(dict(player=name,otc_id=otc,archived_gsis_ids=[gsis],fatype='SFA'))
    classified, seen = [], set()
    for candidate in candidates:
        otc = candidate['otc_id']
        if otc in seen:
            raise ValueError('Duplicate free-agent candidate identity')
        seen.add(otc)
        ids = candidate.get('archived_gsis_ids', [])
        player = dict(player=candidate['player'],otc_id=otc,gsis_id=ids[0] if len(ids) == 1 else None,
                      eligible=False,evidence=None)
        gsis = player['gsis_id']
        if not gsis:
            reason = 'identity_review'
        elif gsis in owners:
            reason = 'club_owned'
        elif gsis in retired or candidate.get('historical_status') == 'retirement_review':
            reason = 'retired'
            player['evidence']=candidate.get('retirement_evidence')
        elif gsis in disputed:
            reason = 'unresolved_latest_transaction'
        elif gsis in releases:
            # Explicit current unrestricted termination supersedes a directory's
            # older tender label. Never infer this from the label alone.
            reason = 'verified_vested_termination'
            if (releases[gsis].get('qualification')=='explicit_nfl_termination' and
                    releases[gsis]['evidence']['transaction']['transaction']=='Terminated Via Waivers, all contracts'):
                reason='verified_waiver_termination'
            player.update(eligible=True,evidence=releases[gsis])
        elif candidate.get('fatype') in ('RFA','ERFA'):
            reason = 'restricted_or_exclusive_rights_review'
        elif gsis in active_contracts:
            reason = 'unrostered_active_contract_review'
        else:
            history = candidate.get('archived_history') or []
            latest = max((h.get('year_signed') or 0 for h in history),default=0)
            last = [h for h in history if h.get('year_signed') == latest]
            expired = (last and all(h.get('status') == 'Expired' and
                       type(h.get('year_signed')) is int and type(h.get('yrs')) is int and
                       h['year_signed']+h['yrs'] <= day.year for h in last))
            if (candidate.get('fatype') in ('UFA','SFA') and expired
                    and not candidate.get('dated_mentions')):
                reason = 'dated_expired_unrestricted_contract' if dated_archive else 'expired_contract_candidate_review'
                player.update(eligible=dated_archive,evidence=last)
            else:
                reason = 'availability_or_waiver_clearance_review'
        classified.append(dict(player,status=reason))
    return dict(cutoff=cutoff,players=classified,
                eligible=[p for p in classified if p['eligible']],
                missing_release_identities=sorted(missing_release_identities),
                contract_archive_receipt=archive_receipt,
                exhaustive_pool_verified=False,signing_authorized=False,writes_performed=False)
