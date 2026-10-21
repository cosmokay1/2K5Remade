"""Apply explicit, source-pinned adjudications to an isolated membership report.

Adjudication closes a parser/identity question, not every legal right. An injury
rights hold stays unavailable; no decision here authorizes signing or erases debt.
"""
from copy import deepcopy
from datetime import date
from hashlib import sha256
import json
from urllib.parse import urlsplit

from tools.correct_week1_membership import ACTIVE, PRIMARY_DOMAINS


def review_digest(review):
    return sha256(json.dumps(review,sort_keys=True,allow_nan=False).encode()).hexdigest()


def adjudicate(report, decisions, sources):
    result = deepcopy(report)
    cutoff = date.fromisoformat(report['cutoff'])
    pending = {r['gsis_id']:r for r in result['reviews']}
    if len(pending) != len(result['reviews']):
        raise ValueError('Duplicate pending identity')
    closed = []
    for decision in decisions:
        gsis = decision['gsis_id']
        review = pending.get(gsis)
        if not review or decision['review_sha256'] != review_digest(review):
            raise ValueError('Missing, duplicate or changed review')
        team = decision['team']
        if team not in {e['team'] for e in review['events']}:
            raise ValueError('Decision club differs from reviewed event')
        if date.fromisoformat(decision['effective_date']) > cutoff or not decision.get('rationale'):
            raise ValueError('Dated explanation required; no future roster change')
        proofs = decision.get('proofs',[])
        if not proofs:
            raise ValueError('Pinned club evidence required')
        for proof in proofs:
            body = sources.get(proof['sha256'])
            host = (urlsplit(proof['url']).hostname or '').removeprefix('www.')
            if (not proof['url'].startswith('https://') or body is None
                    or sha256(body).hexdigest() != proof['sha256']):
                raise ValueError('Source bytes do not match pinned evidence')
            if host != PRIMARY_DOMAINS[team]:
                raise ValueError('Adjudication requires the reviewed club primary domain')
        members = [r for r in result['rows'] if r.get('season')==cutoff.year
            and r.get('week')==1 and r.get('game_type')=='REG' and r.get('gsis_id')==gsis]
        owners = [r for r in members if r['status'] in ACTIVE]
        if len(owners)>1 or not members:
            raise ValueError('Missing or multiply owned reviewed identity')
        kind = decision['decision']
        if kind == 'reject_name_association':
            # A different player with the same name signed; do not move this one.
            pass
        else:
            status = {'signed_active':'ACT','signed_practice':'DEV','temporary_elevation':'DEV',
                      'waived_from_reserve':'CUT','practice_squad_injured':'DEV',
                      'preserve_injury_rights_hold':'RES'}.get(kind)
            if status is None:
                raise ValueError('Unsupported adjudication')
            destination = [r for r in members if r['team']==team]
            if len(destination)>1:
                raise ValueError('Duplicate destination member')
            if kind=='preserve_injury_rights_hold' and (
                    len(owners)!=1 or owners[0]['team']!=team or owners[0]['status']!='RES'):
                raise ValueError('Rights hold requires an independently recorded reserve owner')
            member = destination[0] if destination else deepcopy(owners[0] if owners else members[0])
            before = dict(team=member['team'],status=member['status'])
            if owners and (owners[0]['team']!=team or status=='CUT'):
                old=owners[0]
                result['retained_liability_reviews'].append(dict(gsis_id=gsis,team=old['team'],
                    date=decision['effective_date'],charge_dollars=None,review_required=True,source=decision))
                if old is not member:
                    old['status']='CUT'
            member.update(team=team,status=status,membership_adjudication=decision)
            if kind in ('preserve_injury_rights_hold','practice_squad_injured'):
                member['availability_rights_hold']=True
            if not destination:
                result['rows'].append(member)
            if before != dict(team=team,status=status):
                result['corrections'].append(dict(gsis_id=gsis,before=before,
                    after=dict(team=team,status=status),evidence=decision))
        closed.append(decision)
        del pending[gsis]
    result['reviews'] = list(pending.values())
    result['adjudications'] = result.get('adjudications', []) + closed
    result['free_agent_pool_verified'] = False
    result['membership_at_cutoff_verified'] = False
    result['signing_authorized'] = False
    return result
