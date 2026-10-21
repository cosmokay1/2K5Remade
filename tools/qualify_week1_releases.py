"""Additional dated release evidence; no waiver clearance guessed from age.

A lower bound of four seasons with six actual REG appearances suffices for the
pre-deadline vested release rule. PS/IR, injury and ambiguous cases stay held.
This never claims that a candidate directory is an exhaustive historical pool.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import date
import re

from tools.correct_week1_membership import ACTIVE
from tools.correct_week1_membership import _name
from tools.reconcile_week1_contracts import CLUBS


def qualify_releases(membership, events, participation, *, cutoff):
    day=date.fromisoformat(cutoff)
    if membership['cutoff']!=cutoff or not (date(day.year,3,15)<=day<date(day.year,10,1)):
        raise ValueError('Explicit supported preseason/Week1 release interval required')
    owners={r['gsis_id'] for r in membership['rows'] if r.get('season')==day.year
            and r.get('week')==1 and r.get('game_type')=='REG' and r['status'] in ACTIVE}
    reviews={r['gsis_id'] for r in membership['reviews']}
    grouped=defaultdict(list)
    for event in events:
        if event.get('gsis_id') and date(day.year,2,15)<=date.fromisoformat(event['date'])<=day:
            grouped[event['gsis_id']].append(event)
    result=deepcopy(membership)
    known={r['gsis_id'] for r in result['verified_unrestricted_releases']}
    added=[];held=[]
    for gsis, rows in grouped.items():
        if gsis in known or gsis in owners or gsis in reviews:continue
        latest=max(r['date'] for r in rows);last=[r for r in rows if r['date']==latest]
        if any(r['status']!='CUT' or r.get('primary_club_verified') is not True for r in last):
            held.append(gsis);continue
        if any(re.search(r'injur|reserve|failed physical|settlement|practice squad',r['clause'],re.I) for r in last):
            held.append(gsis);continue
        years=set()
        for sample in participation.get(gsis,[]):
            year=sample['season'];weeks=sample['regular_season_weeks']
            if (type(year) is not int or not day.year-10<=year<day.year or
                    not isinstance(weeks,list) or any(type(w) is not int or not 1<=w<=18 for w in weeks)):
                raise ValueError('Exact prior-season regular participation required')
            if len(set(weeks))>=6:years.add(year)
        if not all(r.get('unrestricted_release_verified') is True for r in last) and len(years)<4:
            held.append(gsis);continue
        proof=dict(gsis_id=gsis,as_of=cutoff,evidence=last,
            qualification='explicit_club_vested_termination' if all(r.get('unrestricted_release_verified') for r in last)
                else 'four_season_participation_lower_bound',
            participation_seasons=sorted(years),actual_service_lower_bound_only=True)
        result['verified_unrestricted_releases'].append(proof);added.append(proof)
    result['additional_release_qualifications']=added
    result['release_rights_held']=sorted(held)
    result['free_agent_pool_verified']=False
    result['signing_authorized']=False
    return result


def qualify_wire_terminations(membership, pages, candidates, events, *, cutoff):
    """Use explicit NFL termination outcomes, never elapsed waiver time alone.

    Partial pages prove individual records only. Require independently bound club
    release evidence and reject any subsequent ownership/status ambiguity.
    """
    if membership['cutoff']!=cutoff:raise ValueError('Matching rights cutoff required')
    day=date.fromisoformat(cutoff)
    result=deepcopy(membership);added=[];held=[]
    aliases=defaultdict(set)
    for candidate in candidates:
        ids=candidate.get('archived_gsis_ids',[])
        if len(ids)==1:aliases[_name(candidate['player'])].add(ids[0])
    owners={r['gsis_id'] for r in membership['rows'] if r.get('season')==day.year
            and r.get('week')==1 and r.get('game_type')=='REG' and r['status'] in ACTIVE|{'RET'}}
    disputed={r['gsis_id'] for r in membership['reviews']}
    known={r['gsis_id'] for r in membership['verified_unrestricted_releases']}
    grouped=defaultdict(list)
    for event in events:
        if event.get('gsis_id') and event['date']<=cutoff:grouped[event['gsis_id']].append(event)
    for page in pages:
        if 'error' in page:continue
        if not re.fullmatch(r'https://www\.nfl\.com/transactions/league/(?:terminations|waivers)/'+str(day.year)+r'/(?:[1-9]|1[0-2])',page['url']) or not re.fullmatch('[a-f0-9]{64}',page['sha256']):
            raise ValueError('Pinned primary NFL transaction page required')
        for row in page['rows']:
            if row['date']>cutoff or row['transaction'] not in ('Terminated, Vested Veteran, all contracts','Terminated Via Waivers, all contracts'):continue
            if not row.get('profile') or not row['profile'].startswith('/players/') or row.get('to_club') is not None:continue
            identities=aliases[_name(row['player'])]
            if len(identities)!=1:continue
            gsis=next(iter(identities))
            if gsis in known or gsis in owners or gsis in disputed:continue
            history=grouped[gsis]
            if not history:held.append(gsis);continue
            last_date=max(e['date'] for e in history);last=[e for e in history if e['date']==last_date]
            interval=(date.fromisoformat(row['date'])-date.fromisoformat(last_date)).days
            if not 0<=interval<=3 or any(e['status']!='CUT' or e.get('primary_club_verified') is not True or
                    not (row.get('from_club','').startswith('/teams/') and
                         row['from_club'].rstrip('/').rsplit('-',1)[-1]==CLUBS[e['team']].lower()) or
                    re.search(r'injur|reserve|failed.physical|settlement|practice squad',e['clause'],re.I) for e in last):
                held.append(gsis);continue
            proof=dict(gsis_id=gsis,as_of=cutoff,qualification='explicit_nfl_termination',
                evidence=dict(transaction=row,source_url=page['url'],source_sha256=page['sha256'],club_release=last),
                complete_wire_history_verified=False)
            result['verified_unrestricted_releases'].append(proof);added.append(proof);known.add(gsis)
    result['additional_wire_qualifications']=added;result['wire_termination_held']=sorted(set(held))
    result['free_agent_pool_verified']=False;result['signing_authorized']=False
    return result
