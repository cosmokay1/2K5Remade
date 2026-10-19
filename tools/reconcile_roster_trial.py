"""Read-only roster-to-fresh-franchise and native payroll comparison.

This is import evidence, not a modern opening book: imported legacy schedules,
including expired/malformed terms, must not become authoritative NFL contracts.
No identity registry, main save, cap, contract or ledger is written here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from franchise.legacy_contracts import original_annual_rows
from tools.inspect_franchise_calendar import inspect_calendar
from tools.inspect_franchise_save import TEAMS, PLAYER_STRIDE, inspect_save
from tools.inspect_roster_save import inspect_roster, inspect_trial_franchise_roster


def _terms(payload, slot):
    record=0xAFA8+slot*PLAYER_STRIDE
    amount=struct.unpack_from('<H',payload,record+0x0A)[0]
    packed=struct.unpack_from('<I',payload,record+0x24)[0]
    return {'amount_word':amount,'remaining_years':packed&15,'original_years':(packed>>24)&15,
            'bonus_code':(packed>>20)&15,'shape_code':(packed>>16)&15}


def _members(payload, roster):
    result={}
    for team, players in [*roster['teams'].items(),('free_agents',roster['free_agents'])]:
        for player in players:
            slot=player['source_slot'];record=0xAFA8+slot*PLAYER_STRIDE
            result[slot]={'team':team,**player,'biography_guard':
                         (payload[record+4:record+8]+payload[record+0x19:record+0x1C]).hex()}
    return result


def reconcile_trial(source_roster, fresh_franchise, *, money_scale):
    if type(money_scale) is not int or money_scale not in (1,4):
        raise ValueError('Explicit supported money scale required')
    before=inspect_roster(source_roster);calendar=inspect_calendar(fresh_franchise)
    raw=fresh_franchise[0x2E0:0x2E0+0x91040];after=inspect_trial_franchise_roster(fresh_franchise)
    try:
        inspect_save(fresh_franchise);strict_identity_supported=True
    except ValueError:
        strict_identity_supported=False
    old,new=_members(source_roster,before),_members(raw,after)
    differences=[{'source_slot':slot,'before':old.get(slot),'after':new.get(slot)}
                 for slot in sorted(old.keys()|new.keys()) if old.get(slot)!=new.get(slot)]
    changed=[{'source_slot':slot,'before':_terms(source_roster,slot),'after':_terms(raw,slot)}
             for slot in sorted(old.keys()&new.keys())
             if _terms(source_roster,slot)!=_terms(raw,slot)]
    scheduler=calendar['scheduler_offset'];cap_offset=scheduler+0x83DC+0x15D0
    raw_cap=struct.unpack_from('<i',fresh_franchise,cap_offset)[0]*1000
    if raw_cap<=0:raise ValueError('Positive native league cap required')
    teams={};unresolved=[]
    for index,team in enumerate(TEAMS):
        contracts=[];supported=True
        for player in after['teams'][team]:
            terms=_terms(raw,player['source_slot']);row={**player,'terms':terms}
            remaining,years=terms['remaining_years'],terms['original_years']
            if remaining==0:
                row.update(native_current_charge=0,status='inactive_native_terms')
                unresolved.append({'team':team,**row})
            else:
                try:
                    if remaining>years:raise ValueError('Remaining years exceed original years')
                    rows=original_annual_rows(terms['amount_word'],terms['bonus_code'],terms['shape_code'],years)
                    row['native_current_charge']=rows[years-remaining]['original_game_charge_dollars']*money_scale
                    row['status']='original_schedule_only'
                except ValueError as error:
                    supported=False;row.update(native_current_charge=None,status='unsupported',reason=str(error))
                    unresolved.append({'team':team,**row})
            contracts.append(row)
        stored=struct.unpack_from('<I',raw,0x41C8+index*0x1F4+0x124)[0]*1000*money_scale
        first_year_flag=struct.unpack_from('<I',fresh_franchise,scheduler+0xAC+index*4)[0]
        accumulator=struct.unpack_from('<H',raw,0x41C8+index*0x1F4+0x19C)[0]*1000*money_scale
        reconstructed=sum(r['native_current_charge'] for r in contracts) if supported else None
        teams[team]={'roster_count':len(contracts),'stored_roster_payroll':stored,
            'reconstructed_roster_payroll':reconstructed,'native_payroll_matches':
            stored==reconstructed if supported else None,'first_year_flag_raw':first_year_flag,
            'first_year_accumulator':accumulator,'room_without_adjustment':raw_cap*money_scale-stored,
            'room_with_adjustment':raw_cap*money_scale-stored-(accumulator if first_year_flag else 0),
            'contracts':contracts}
    return {'scope':'read-only actual saved native schedules; no modern opening-book authority',
        'source_roster_sha256':before['payload_sha256'],
        'fresh_franchise_sha256':hashlib.sha256(fresh_franchise).hexdigest(),
        'money_scale':money_scale,'saved_calendar':calendar,'league_cap':raw_cap*money_scale,
        'roster_membership_and_biography_preserved':not differences,'roster_differences':differences,
        'contract_word_changes':changed,'source_nonstandard_name_pointers':before['nonstandard_name_pointers'],
        'saved_nonstandard_name_pointers':after['nonstandard_name_pointers'],
        'strict_franchise_identity_supported':strict_identity_supported,
        'all_native_payrolls_match':all(t['native_payroll_matches'] is True for t in teams.values()),
        'unresolved_native_contracts':unresolved,'teams':teams,'modern_contracts_verified':False,
        'complete_opening_book':False,'signing_authorized':False,'writes_performed':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_roster',type=Path);p.add_argument('fresh_franchise',type=Path)
    p.add_argument('--money-scale',type=int,choices=(1,4),required=True)
    a=p.parse_args()
    try:r=reconcile_trial(a.source_roster.read_bytes(),a.fresh_franchise.read_bytes(),money_scale=a.money_scale)
    except (OSError,ValueError) as error:p.error(str(error))
    print(json.dumps(r,indent=2))


if __name__=='__main__':main()
