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
