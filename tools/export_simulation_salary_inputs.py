"""Explicit completed-game-season salary policy; never real NFL service verification."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from franchise.salary_rules import VeteranMinimumProfile
from franchise.historical_economy import HistoricalEconomy, REFERENCE_YEAR
from tools.franchise_snapshot_bindings import resolve_bindings, migrate_context
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE

POLICY='game-completed-seasons-v1'


def salary_inputs(bindings, payload, *, expected_revisions, years):
    members=resolve_bindings(bindings,payload)
    context=migrate_context(bindings,payload)['game_context']
    game_year=context['season_year']
    year=game_year if game_year>=2020 else REFERENCE_YEAR+game_year-2004
    if year<2020 or year>2030:
        raise ValueError('Explicit calendar is outside supported salary-rule years')
    if type(years) is not int or not 1<=years<=2031-year:
        raise ValueError('Salary horizon must fit the published minimum table through 2030')
    # The generic saved career-period field starts at one in a rookie season.
    # Mapping it to completed seasons is an explicitly adopted simulation policy,
    # not an inference of NFL paid/eligible roster weeks or performance.
    records=[];rookies=[];unknown=[]
    for slot,player in sorted(members.items()):
        raw=(struct.unpack_from('<I',payload,PLAYER_START+slot*PLAYER_STRIDE+0x24)[0]>>8)&31
        if raw==0:
            unknown.append(player['player_id'])
        elif raw==1:
            rookies.append(player['player_id'])
        else:
            records.append((player['player_id'],tuple(raw-1+i for i in range(years)),('active_inactive',)*years))
    economy=HistoricalEconomy(context['league_cap_raw']*1000*context['money_scale']) if game_year<2020 else None
    profile=VeteranMinimumProfile(year,tuple(records),economy=economy)
    digest=hashlib.sha256(payload).hexdigest()
    source=POLICY+':'+digest
    batch={'format':1,'request_id':POLICY+'-'+digest[:16],
           'source':source,'profile':profile.to_dict(),'expected_revisions':expected_revisions}
    report={'policy':POLICY,'completed_seasons':'saved career-period counter minus one',
            'future_minimum_projection':'one additional completed franchise season per scheduled year',
            'compensation_category':'active_inactive new-contract projection',
            'actual_nfl_service_verified':False,'classified_veterans':len(records),
            'source_payload_sha256':digest,
            'game_year':game_year,'salary_rule_start_year':year,
            'rookies_requiring_separate_rules':rookies,'unknown_season_inputs':unknown,
            'ai_authorized':False,'guest_write_authorized':False}
    return batch,report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save',type=Path);parser.add_argument('bindings',type=Path)
    parser.add_argument('revisions',type=Path,help='Explicit team-to-revision JSON')
    parser.add_argument('output',type=Path);parser.add_argument('--years',type=int,default=5)
    args=parser.parse_args(argv)
    try:
        batch,report=salary_inputs(json.loads(args.bindings.read_text()),args.save.read_bytes(),
            expected_revisions=json.loads(args.revisions.read_text()),years=args.years)
        with args.output.open('x') as output:json.dump(batch,output,indent=2);output.write('\n')
    except (OSError,ValueError) as error:parser.exit(2,f'export_simulation_salary_inputs: {error}\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
