"""Bind an isolated fresh franchise to fitted contracts and all32 opening books.

Return a bootstrap and readonly cap plan inputs. Never overwrite a game, save or
existing DB. The caller must still verify real game load/signing/save/reload.
"""
from fractions import Fraction
from hashlib import sha256
from itertools import zip_longest
import json
import struct

from franchise.books import ChargeRecord,OpeningBooks
from franchise.cap import Ledger
from franchise.salary_rules import VeteranMinimumProfile
from tools.export_legacy_contracts import legacy_contracts
from tools.franchise_snapshot_bindings import create_bindings,resolve_bindings
from tools.franchise_game_context import raw_context
from tools.inspect_franchise_save import PLAYER_START,PLAYER_STRIDE,TEAMS,inspect_save
from tools.inspect_roster_save import inspect_roster
from tools.reconcile_week1_contracts import CLUBS
from tools.fit_week1_native_contracts import source_schedule


def rookie_amendment_hold(archive,gsis,team,year):
    rows=[r for r in archive if r.get('gsis_id')==gsis and r.get('is_active') is True]
    if len(rows)!=1:return False
    row=rows[0]
    if row.get('team')!=CLUBS[team] or row.get('year_signed')!=row.get('draft_year'):
        return False
    elapsed=year-int(row['year_signed'])
    if row.get('years')==4 and row.get('draft_round'):
        return elapsed<3
    if row.get('years')==3 and not row.get('draft_round'):
        return elapsed<2
    return False


def build_opening(payload,roster,fit_receipt,assembly,charges,cap_book,archive,*,seed):
    if sha256(roster).hexdigest()!=fit_receipt['output_sha256'] or set(charges['teams'])!=set(CLUBS) or set(cap_book['teams'])!=set(CLUBS):
        raise ValueError('Pinned fitted roster and complete all-team modeled books required')
    if (charges['input_sha256']!=cap_book['salary_input_sha256'] or charges['season_year']!=2026
            or cap_book['calibration_policy']!='published_room_target'):
        raise ValueError('Matching authorized opening calibration required')
    current=inspect_save(payload);expected=inspect_roster(roster)
    for team in (*TEAMS,'free_agents'):
        a=expected['free_agents'] if team=='free_agents' else expected['teams'][team]
        b=current['free_agents'] if team=='free_agents' else current['teams'][team]
        if a!=b:raise ValueError('Fresh franchise did not load the fitted hybrid membership/names')
        for player in a:
            slot=player['source_slot'];r=0xAFA8+slot*PLAYER_STRIDE;f=PLAYER_START+slot*PLAYER_STRIDE
            for start,end in ((4,8),(10,12),(25,28),(36,40)):
                if roster[r+start:r+end]!=payload[f+start:f+end]:
                    raise ValueError('Fresh player biography/contract fields differ from the pinned hybrid')
    context=raw_context(payload);context.update(season_year=charges['season_year'],money_scale=fit_receipt['game_dollar_scale'])
    if context['league_cap_raw']*1000*context['money_scale']!=charges['league_cap']:
        raise ValueError('Fresh franchise league cap differs from modeled scale')
    bindings=create_bindings(payload,seed=seed,game_context=context)
    members=resolve_bindings(bindings,payload);legacy=legacy_contracts(bindings,payload)
    slots=assembly['bindings'];ids={g:members[s]['player_id'] for g,s in slots.items()}
    if set(members)!=set(slots.values()):raise ValueError('Unexpected fresh player identity or missing binding')
    source='week1-opening:'+charges['input_sha256']+':proxy:'+cap_book['proxy_source']['as_of']
    all_free={p['player_id'] for p in members.values() if p['team']=='free_agents'}
    teams={};cash={};report={}
    for code,team_model in cap_book['teams'].items():
        team='Redskins' if code=='WAS' else CLUBS[code]
        selected=charges['teams'][code]['players']
        active=[r for r in selected if r['roster_status'] in ('ACT','INA')]
        if {ids[r['gsis_id']] for r in active}!={c.player_id for c in legacy[team]}:
            raise ValueError('All-team saved contract inventory differs from opening charges')
        adjustments=[];retained=[]
        for row in selected:
            gsis=row['gsis_id']
            liability_id=gsis or 'unbound-'+sha256((code+':'+row['player']).encode()).hexdigest()
            schedule,_,basis=source_schedule(row,archive,charges['season_year']) if gsis and row['cap_dollars'] else ([row['cap_dollars']],None,'source_current_only')
            if row['roster_status'] in ('ACT','INA'):
                original=next(c for c in legacy[team] if c.player_id==ids[gsis])
                fit=fit_receipt['players'][gsis]
                if list(original.charges())!=fit['represented_cap_dollars'] or schedule!=fit['source_cap_dollars']:
                    raise ValueError('Saved native contract differs from the fit/source witness')
                from franchise.legacy_contracts import original_annual_rows
                native_rows=original_annual_rows(original.amount_word,original.bonus_code,original.shape_code,original.original_years)[-original.remaining_years:]
                base=tuple(v-r['salary_dollars']*original.game_dollar_scale for v,r in zip(fit['source_base_dollars'],native_rows))
                other=tuple(v-r['allocated_bonus_dollars']*original.game_dollar_scale for v,r in zip(fit['source_nonbase_dollars'],native_rows))
                if any(base):adjustments.append(ChargeRecord('native-base:'+ids[gsis],base,source+':'+basis))
                if any(other):adjustments.append(ChargeRecord('native-nonbase:'+ids[gsis],other,source+':'+basis))
            else:
                retained.append(ChargeRecord('off-roster:'+liability_id,tuple(schedule),source+':'+row['roster_status']))
        retained.append(ChargeRecord('retained:'+code,(team_model['retained_dollars'],),source+':'+team_model['retained_basis']))
        adjustments.append(ChargeRecord('adjustment:'+code,(-team_model['net_adjustment_dollars'],),source+':'+team_model['adjustment_basis']))
        books=OpeningBooks(retained=tuple(retained),adjustments=tuple(adjustments),legacy_contracts=legacy[team])
        # Completed-season salary rule approved by user. Signed rookies remain
        # unclassified for amendments, hence held until a separate rookie action.
        eligible={c.player_id for c in legacy[team]}|all_free;salary=[];rookies=[]
        locked={ids[r['gsis_id']] for r in active if rookie_amendment_hold(archive,r['gsis_id'],code,2026)}
        for slot,member in members.items():
            if member['player_id'] not in eligible:continue
            raw=(struct.unpack_from('<I',payload,PLAYER_START+slot*PLAYER_STRIDE+36)[0]>>8)&31
            if raw<=1 or member['player_id'] in locked:rookies.append(member['player_id']);continue
            salary.append((member['player_id'],tuple(raw-1+i for i in range(5)),('active_inactive',)*5))
        profile=VeteranMinimumProfile(2026,tuple(salary))
        ledger=Ledger.from_opening(books,cap=charges['league_cap'],roster_reserve=0,max_bonus_years=5,
            veteran_minimums=profile.floors(),veteran_minimum_profile=profile,
            observed_player_ids=frozenset(all_free),observed_player_source=source)
        expected_room=team_model['modeled_cap_room_dollars']
        if ledger.room!=expected_room:raise ValueError('Exact source opening room disagrees with saved/typed books')
        teams[team]=ledger.bootstrap_config()
        cash[team]=dict(source=source+':legacy-cash-unknown',records=[],unknown_legacy_players=sorted(c.player_id for c in legacy[team]))
        report[team]=dict(room_dollars=expected_room,opening_charges=charges['league_cap']-expected_room,
            native_contracts=len(legacy[team]),off_roster_obligations=len(retained)-1,
            rookie_or_unknown_amendments_held=len(rookies),original_rookie_contracts_locked=len(locked))
    return dict(format=1,source=source,seed=seed,teams=teams,cash=cash),bindings,dict(
        teams=report,free_agents=len(all_free),free_agent_pool_exhaustive=False,
        game_verified=False,signing_authorized=False,source_roster_sha256=fit_receipt['output_sha256'])
