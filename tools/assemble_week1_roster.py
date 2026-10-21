"""Assemble a private roster compatibility trial, never install or certify money.

Requires the pinned MIT 2K Football Mod Tools codec (Noah and contributors;
record research credits Flying Finn and BAD_AL). Source inputs stay immutable.
Missing gameplay profiles require explicit sourced estimates; generic create-player
defaults are refused. Cap projections
remain separate until a real fresh franchise can be reconciled.
"""
from datetime import date
from hashlib import sha256

from tools.inspect_roster_save import inspect_roster
from tools.inspect_franchise_save import TEAMS
from tools.reconcile_week1_contracts import CLUBS


def gameplay_profile(codec, assignment, gsis, season_year):
    """Refuse unsourced defaults and future-season performance in a new record."""
    estimate = assignment.get('gameplay_estimate', {})
    ratings = estimate.get('ratings', {})
    basis = estimate.get('basis', {})
    sources = estimate.get('sources', [])
    if (estimate.get('gsis_id') != gsis or estimate.get('position') != assignment['position']
            or set(ratings) != set(codec.RATING_BYTE_ORDER)
            or any(type(v) is not int or not 0 <= v <= 99 for v in ratings.values())
            or type(basis.get('season')) is not int or basis['season'] >= season_year
            or not basis.get('model') or not sources
            or any(not isinstance(s, dict) or not s.get('source_url')
                   or len(s.get('sha256', '')) != 64
                   or any(c not in '0123456789abcdef' for c in s['sha256']) for s in sources)):
        raise ValueError('Complete, identity-bound sourced gameplay estimate required')
    return dict(ratings)


def assemble(codec, payloads, plan):
    """Plan contains verified GSIS assignments and explicit reusable FA slots.

    Every input hash, including the XBE, is pinned. No unassigned or draft slot
    can be reused. Classic-team and reserve references are protected too.
    """
    if any(sha256(payloads[k]).hexdigest()!=h for k,h in plan['input_sha256'].items()):
        raise ValueError('Source changed since planning')
    year=plan['season_year'];base=payloads['native']
    docs={key:codec.RosterDocument(data,base=0x20,base_year=year,reference_year=year)
          for key,data in payloads.items() if key!='xbe'}
    for key,doc in docs.items():
        if doc.to_body(normalise_commentary=False)!=payloads[key]:
            raise ValueError('Codec must round-trip every source losslessly')
    doc=docs['native'];primary=doc.by_pool('primary');by_slot={p.index:p for p in primary}
    before_records={p.offset:(p.record.encode(),p.first,p.last) for p in doc.players}
    assignments=plan['assignments'];groups=plan['clubs'];free=plan['free_agents']
    if set(groups)!=set(CLUBS) or any(not 42 <= len(ids) <= 54 for ids in groups.values()):
        raise ValueError('Complete supported all-team active lists required')
    owned=[g for ids in groups.values() for g in ids]
    selected=owned+free
    if len(selected)!=len(set(selected)) or set(selected)!=set(assignments):
        raise ValueError('Unique, complete active/free identities required')
    protected=set(plan['protected_native_slots'])
    for team in doc.teams[32:]:
        protected.update(doc.by_offset[off].index for off in team.slots)
    for indices in doc.reserves.values():protected.update(indices)
    used=set()
    for gsis,a in assignments.items():
        if a['origin']=='native':
            slot=a['slot']
            if slot not in by_slot or slot in used:raise ValueError('Duplicate/missing native binding')
            used.add(slot);protected.add(slot)
    reusable=plan['reusable_native_slots']
    native_free={doc.by_offset[off].index for off in doc.free_agents}
    if len(set(reusable))!=len(reusable) or not set(reusable)<=native_free or set(reusable)&protected:
        raise ValueError('Reuse requires explicit unprotected free-agent records')
    reusable=iter(reusable);bound={};created=[];foreign=[];unknown_colleges=[]
    # Long identities first give the existing string allocator the best chance.
    order=sorted(assignments,key=lambda g:-len(assignments[g]['biography']['last_name']))
    for gsis in order:
        a=assignments[gsis];bio=a['biography'];origin=a['origin']
        if origin=='native':target=by_slot[a['slot']]
        else:
            try:slot=next(reusable)
            except StopIteration:raise ValueError('Not enough proven reusable native records') from None
            target=by_slot[slot]
            if origin=='created':
                target.record=codec.PlayerRecord.decode(bytes(0x54),reference_year=year)
                target.record.values['hand']=1
                target.record.values['position']=a['position']
                target.record.values.update(gameplay_profile(codec,a,gsis,year))
                target.record.values['height']=a['profile']['height']
                target.record.weight=a['profile']['weight']
                # This is a display projection for the trial, not the modern ledger.
                for key in ('contract_value','contract_length','contract_remaining','contract_type','contract_bonus'):
                    target.record.values[key]=a['native_contract_projection'][key]
                created.append(gsis)
            else:
                source=docs[origin].by_pool('primary')[a['slot']]
                codec.copy_player(source.record,target.record,mode='all')
                foreign.append(gsis)
            # Never transfer another person's history, ordinal, commentary or college pointer.
            target.record.values['history_pointer']=0
            target.record.values['pbp_id']=0
            target.record.values['college_pointer']=0
            target.record.values['unknown_52']=0
            college=a.get('college_index')
            if college is not None:doc.set_college(target,college)
            else:unknown_colleges.append(gsis)
        if origin != 'native':
            # Preserve creator spellings and legal engine name lengths. GSIS, not
            # display text, remains identity authority. Never silently truncate.
            names = a.get('display_names') or (bio if origin == 'created' else dict(first_name=source.first, last_name=source.last))
            doc.set_name(target,'first',names['first_name'])
            doc.set_name(target,'last',names['last_name'])
        target.record.birth_date=date.fromisoformat(bio['birth_date'])
        target.record.values['photo_id']=a['photo_id']
        target.record.values['jersey']=int(bio['jersey_number'] or 0)
        target.record.values['years_pro']=min(31,max(1,int(bio['years_exp'])+1))
        # Exactly the native active flag; clear stale retired/prospect bits.
        target.record.values['player_type']=(target.record.values['player_type']&~0x18)|4
        bound[gsis]=target
    offsets={p.offset for p in bound.values()}
    if len(offsets)!=len(bound):raise ValueError('Duplicate destination record')
    for code,ids in groups.items():
        team=doc.teams[TEAMS.index('Redskins' if code == 'WAS' else CLUBS[code])]
        # Preserve source depth order within position, with incoming players at the end.
        old={off:i for i,off in enumerate(team.original_slots)}
        players=sorted((bound[g] for g in ids),key=lambda p:(p.record.values['position'],old.get(p.offset,9999),
                       p.record.values['depth_rank'],p.index))
        team.slots=[p.offset for p in players]
        ranks={}
        for player in players:
            pos=player.record.values['position'];rank=ranks.get(pos,0);ranks[pos]=rank+1
            player.record.values['depth_rank']=min(rank,codec.DEPTH_ROW_CAP)
            player.record.values['depth_side']=min(codec.DEPTH_SIDE_FOR_RANK.get(rank,rank),codec.DEPTH_ROW_CAP)
    # This legacy source has no reserve table. Do not discard one to fit this trial.
    if any(doc.reserves.values()):raise ValueError('Existing native reserve ownership requires a separate migration')
    doc.free_agents=[bound[g].offset for g in free]
    output=doc.to_body(normalise_commentary=False)
    reread=codec.RosterDocument(output,base=0x20,base_year=year,reference_year=year)
    if reread.to_body(normalise_commentary=False)!=output or len(output)!=len(base):
        raise ValueError('Output fails fixed-size lossless reload')
    reloaded={p.index:p for p in reread.by_pool('primary')}
    bound_offsets={p.offset for p in bound.values()}
    for player in reread.players:
        if player.offset not in bound_offsets:
            if (player.record.encode(),player.first,player.last)!=before_records[player.offset]:
                raise ValueError('Unassigned or classic player changed')
    for gsis,player in bound.items():
        actual=reloaded[player.index];a=assignments[gsis]
        if actual.record.birth_date.isoformat()!=a['biography']['birth_date']:
            raise ValueError('Reloaded biography differs from sourced identity')
        if actual.record.values['photo_id']!=a['photo_id']:
            raise ValueError('Reloaded portrait binding changed')
        if a['origin']=='created' and actual.record.ratings()!=a['gameplay_estimate']['ratings']:
            raise ValueError('Reloaded gameplay estimate changed')
    inspected=inspect_roster(output)
    for code,ids in groups.items():
        if {x['source_slot'] for x in inspected['teams']['Redskins' if code == 'WAS' else CLUBS[code]]}!={bound[g].index for g in ids}:
            raise ValueError('Serialized membership differs from verified plan')
    if {x['source_slot'] for x in inspected['free_agents']}!={bound[g].index for g in free}:
        raise ValueError('Serialized free-agent pool differs from qualified subset')
    return output,dict(output_sha256=sha256(output).hexdigest(),bindings={g:p.index for g,p in bound.items()},
        created_estimated_profiles=created,copied_community_profiles=foreign,unknown_native_colleges=unknown_colleges,
        input_sha256=dict(plan['input_sha256']),
        gameplay_estimates={g:assignments[g]['gameplay_estimate'] for g in created},
        display_name_aliases={g:a['display_names'] for g,a in assignments.items() if a.get('display_names')},
        roster_roundtrip_verified=True,roster_membership_verified=True,
        free_agent_pool_exhaustive=False,native_contracts_are_display_projections=True,
        modern_cap_reconciled=False,game_load_verified=False,signing_authorized=False)
