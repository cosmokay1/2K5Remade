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
         'Reinstated|Activated|Promoted|Elevated|Designated|Agreed|Tendered|Exercised|Terminated')
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
    for player in registry:
        if not player.get('gsis_id'):
            continue
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
        clauses = re.split(r'(?:[.,;]\s*(?:and\s+)?|\s+and\s+)(?=(?:'+VERBS+r')\b)',
                           row['description'],flags=re.I)
        for clause in clauses:
            normal = _name(clause)
            identities, ambiguous = set(), False
            for match in pattern.finditer(normal):
                gsis = aliases[match[0]]
                identities.update(gsis)
                ambiguous |= len(gsis) != 1
            state, reason = None, 'Unsupported transaction action'
            if re.match(r'^(?:Released|Terminated)\b',clause,re.I):
                state = 'CUT'
            elif re.match(r'^Waived\b',clause,re.I):
                if not re.search(r'\binjur',clause,re.I):
                    state = 'CUT'
                else:
                    reason = 'Waived/injured requires clearance or reserve evidence'
            elif re.match(r'^Elevated\b',clause,re.I):
                reason = 'Temporary elevation is not permanent roster membership'
            elif re.match(r'^(?:Signed|Re-signed|Claimed|Promoted|Activated|Reinstated)\b',clause,re.I):
                state = 'DEV' if re.search(r'\bto (?:[\w’\x27-]+\s+){0,3}practice squad',clause,re.I) else 'ACT'
            elif re.match(r'^Placed\b',clause,re.I) and re.search(
                    r'injured reserve|reserve/injured|physically unable|non.football injury',clause,re.I):
                state = 'RES'
            elif re.match(r'^Announced\b',clause,re.I) and re.search(r'\bretirement\b',clause,re.I):
                state = 'RET'
            if ambiguous:
                state, reason = None, 'Ambiguous name-to-GSIS identity'
            verb = re.match(r'^(?:'+VERBS+r')\b',clause,re.I)
            if verb and re.search(r'\b(?:'+VERBS+r')\b',clause[verb.end():],re.I):
                state, reason = None, 'Mixed transaction actions require separate evidence'
            if re.search(r'reserve/futures|future contracts|extension|extended',clause,re.I):
                state, reason = None, 'Future contract or amendment does not establish current membership'
            for gsis in sorted(identities):
                events.append(dict(gsis_id=gsis,team=team,date=row['date'],
                    status=state,reason=None if state else reason,clause=clause,
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
    for gsis, history in sorted(grouped.items()):
        latest = max(r['date'] for r in history)
        last = [r for r in history if r['date'] == latest]
        primary = [r for r in last if r.get('primary_club_verified') is True]
        if primary:
            source_conflicts.extend(r for r in last if r not in primary and
                (r['team'],r['status']) not in {(p['team'],p['status']) for p in primary})
            last = primary
        states = {(r['team'],r['status']) for r in last}
        if len(states) != 1 or any(r['status'] is None for r in last):
            reviews.append(dict(gsis_id=gsis,date=latest,events=last,reason='Latest event needs review'))
            continue
        event = last[0];status = event['status']
        if status not in ACTIVE | {'CUT','RET'}:
            raise ValueError('Unsupported corrected status')
        members = [r for r in result if r.get('season') == day.year and r.get('week') == 1
                   and r.get('game_type') == 'REG' and r.get('gsis_id') == gsis]
        owners = [r for r in members if r['status'] in ACTIVE]
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
        elif gsis in disputed:
            reason = 'unresolved_latest_transaction'
        elif candidate.get('fatype') in ('RFA','ERFA'):
            reason = 'restricted_or_exclusive_rights_review'
        elif gsis in releases:
            reason = 'verified_vested_termination'
            player.update(eligible=True,evidence=releases[gsis])
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
