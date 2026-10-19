"""Read-only adapter from the pinned opening contract audit to local asking prices.

Never use the pack's fitted amount word or remaining cap charges as APY. Unknown
identities, modeled sources, rookie deals and special tenders stay unpriced.
Position byte reference: BAD-AL/nfl2k5tool_dart at
 e3afeece61896380a95e506ab43ae1abda0ae8a5, PlayerOffsets.Position (0x35).
"""
import argparse
import json
from pathlib import Path

from franchise.guest_contracts import SOFTDRINK_CONTRACT_FORMAT
from franchise.market_pricing import build_pricebook
from franchise.salary_rules import VeteranMinimumProfile
from tools.export_simulation_salary_inputs import salary_inputs
from tools.franchise_snapshot_bindings import resolve_bindings, migrate_context
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE
from tools.reconcile_pack_contract_source import reconcile_source
from tools.create_franchise import MAX_INPUT, unique_object

POSITIONS=('QB','K','P','WR','CB','FS','SS','RB','FB','TE','OLB','ILB','C','G','T','DT','DE')
VETERAN_TYPES=frozenset(('UFA','SFA','Extension'))


def export_market(bindings,payload,audit_bytes,*,team_id,years=3,bonus_code=3,performance=None):
    report=reconcile_source(bindings,payload,audit_bytes)
    if report['start_year']!=2026:
        raise ValueError('This pinned market adapter supports its observed 2026 opening only')
    context=migrate_context(bindings,payload)['game_context']
    members=resolve_bindings(bindings,payload)
    if team_id not in report['teams']:raise ValueError('Unknown franchise club')
    batch,_=salary_inputs(bindings,payload,expected_revisions={},years=years)
    floors=VeteranMinimumProfile.from_dict(batch['profile']).floors()
    audit=json.loads(audit_bytes,object_pairs_hook=unique_object)
    rows={row['name']:row for row in audit['ledger']}
    by_player={p['player_id']:(slot,p) for slot,p in members.items()}
    performance={} if performance is None else performance
    if type(performance) is not dict or not set(performance)<=by_player.keys():
        raise ValueError('Performance must use this pinned franchise player registry')
    comparables,players,excluded=[],[],{}
    for team in report['teams'].values():
        for entry in team['matched']:
            player=entry['player_id'];slot,_=by_player[player];row=rows[entry['name']]
            active=[h for h in row['contract_history'] if h.get('status')=='Active'
                    and str(h.get('year_signed'))==str(row['year_signed'])]
            apy=(row.get('headline_dollars') or {}).get('apy')
            code=payload[PLAYER_START+slot*PLAYER_STRIDE+0x35]
            ordinary=len(active)==1 and active[0].get('contract_type') in VETERAN_TYPES
            # OTC retains acquisition labels on negotiated multi-year deals
            # (e.g. Burns's five-year deal is labelled Franchise). A one-year
            # tag/tender is still excluded; it is not an ordinary market deal.
            negotiated_special=(len(active)==1 and active[0].get('contract_type') in
                {'Franchise','Transition','RFA','ERFA'} and type(active[0].get('yrs')) is int
                and active[0]['yrs']>1 and active[0]['yrs']==row.get('source_years'))
            if not (ordinary or negotiated_special):
                excluded[player]='Not an unambiguous observed veteran market contract'
                continue
            if code>=len(POSITIONS) or type(apy) is not int or apy<=0:
                excluded[player]='Unsupported position or missing actual annual value'
                continue
            source=f"{row['source']}; audit={report['audit_sha256']}; as_of={report['as_of']}"
            comp=dict(player_id=player,position=POSITIONS[code],annual_value=apy,rookie=False,source=source)
            if player in performance:comp['performance']=performance[player]
            comparables.append(comp)
            # The adopted completed-season policy supplies base floors only;
            # it cannot declare an existing rookie deal a veteran market deal.
            if by_player[player][1]['team']==team_id and player in floors:
                target=dict(player_id=player,position=POSITIONS[code],rookie=False,
                    minimum_salaries=list(floors[player]),years=years,bonus_code=bonus_code,
                    source=batch['source'])
                if player in performance:target['performance']=performance[player]
                players.append(target)
        for entry in team['unresolved']:
            excluded[entry['player_id']]=entry['reason']
    for slot, member in members.items():
        player=member['player_id']
        if member['team']!='free_agents' or player not in floors:
            continue
        code=payload[PLAYER_START+slot*PLAYER_STRIDE+0x35]
        if code>=len(POSITIONS):
            excluded[player]='Unsupported free-agent position'
            continue
        target=dict(player_id=player,position=POSITIONS[code],rookie=False,
            minimum_salaries=list(floors[player]),years=years,bonus_code=bonus_code,
            source=batch['source'])
        if player in performance:target['performance']=performance[player]
        players.append(target)
    # Source year/cap are pinned by this adapter, not inferred from amount words.
    inputs=dict(format=1,team_id=team_id,league_cap=context['league_cap_raw']*1000*context['money_scale'],
        contract_format=SOFTDRINK_CONTRACT_FORMAT,market=dict(cap=301200000,
            as_of=report['as_of'],source=f"pinned-contract-audit:{report['audit_sha256']}",comparables=comparables),
        players=players)
    return {'inputs':inputs,'pricebook':build_pricebook(inputs),'excluded':excluded,
            'save_write_authorized':False,'signing_authorized':False}


def read_json(path):
    with path.open('rb') as stream:data=stream.read(MAX_INPUT+1)
    if len(data)>MAX_INPUT:raise ValueError('Input exceeds 16 MiB')
    return json.loads(data,object_pairs_hook=unique_object)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save',type=Path);parser.add_argument('bindings',type=Path)
    parser.add_argument('audit',type=Path);parser.add_argument('--team',required=True)
    parser.add_argument('--performance',type=Path);parser.add_argument('--years',type=int,default=3)
    parser.add_argument('--bonus-code',type=int,default=3);parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    try:
        result=export_market(read_json(args.bindings),args.save.read_bytes(),args.audit.read_bytes(),
            team_id=args.team,years=args.years,bonus_code=args.bonus_code,
            performance=read_json(args.performance) if args.performance else None)
        if args.output:
            with args.output.open('x',encoding='utf-8') as writer:
                json.dump(result['pricebook']['policy'],writer,indent=2,allow_nan=False);writer.write('\n')
    except (ValueError,OSError) as error:parser.exit(2,f'export_local_market: {error}\n')
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
