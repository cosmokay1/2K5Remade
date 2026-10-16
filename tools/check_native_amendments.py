"""Check actual offline Bridge amendment replies in the native validator.

Only authored saves and isolated databases; no assets, game launch or inference.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import Mock

from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger
from franchise.legacy_amendments import RULE
from franchise.store import FranchiseStore
from tools.export_legacy_contracts import legacy_contracts
from tools.franchise_snapshot_bindings import create_bindings
from tools.inspect_franchise_calendar import inspect_calendar


def corpus():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
    from test_legacy_contracts import LegacyContractsTests
    payload=bytes(LegacyContractsTests().fixture())
    calendar=inspect_calendar(payload)
    samples=[]
    for scale in (1,4):
        bindings=create_bindings(payload,seed='native amendment replies',game_context=dict(
            season_year=calendar['display_year'],season_index=calendar['season_index'],money_scale=scale,league_cap_raw=80500))
        player=bindings['players'][0]['player_id']
        observation=dict(biography=dict(source_slot=0,first_name='Synthetic',last_name='Starter',
            pbp_photo_raw='00000000',dob_region_raw='000000'),
            team=dict(table_index=0,table_mode=2,payroll_raw=4766,league_cap_raw=80500,
                      team_flag_raw=0,first_year_accumulator_raw=0),
            calendar={key:calendar[key] for key in ('season_index','display_year','phase_01_raw',
                'phase_02_raw','step_04_raw','step_05_raw','counter_08_raw')})
        for action in ('accept','reject','counter'):
            with tempfile.TemporaryDirectory(prefix='amendment wire ') as directory:
                store=FranchiseStore(Path(directory)/'state.sqlite')
                store.create_franchise({'49ers':Ledger.from_opening(OpeningBooks(
                    legacy_contracts=legacy_contracts(bindings,payload)['49ers']),cap=80500000*scale,
                    roster_reserve=0,max_bonus_years=5,veteran_minimums={player:(1000000*scale,)*7})},
                    seed=bindings['personality_seed'])
                decision=dict(action=action,reason='The bonus and remaining term drive our decision.',
                    salaries=[3108000*scale,1865000*scale] if action=='counter' else None,
                    signing_bonus=3316000*scale if action=='counter' else None)
                provider=Mock(return_value=json.dumps(decision))
                bridge=Bridge(store,provider=provider,access_check=lambda:None,guest_snapshot=(bindings,payload))
                request=dict(protocol=1,request_id='amendment',operation='negotiate_proposal',
                    observation=observation,guest_offer=dict(amount_word=829,flags_word=(1<<29)|(2<<16)|4),
                    expected_revision=0,timeout_ms=5000,amendment_rule=RULE)
                before=store.load_team('49ers').financial_snapshot()
                for _ in range(2):
                    response=bridge.handle(request)
                    if response['error'] is not None:raise AssertionError(response)
                    samples.append(dict(request=request,response=response,valid=True))
                provider.assert_called_once()
                assert store.load_team('49ers').financial_snapshot()==before
                for field in ('carried_bonus_charges','combined_player_charges','room_after','settlement_authorized'):
                    bad=copy.deepcopy(response);basis=bad['result']['amendment_basis']
                    if field.endswith('charges'):basis[field][0]=0
                    elif field=='room_after':basis[field]+=1
                    else:basis[field]=True
                    samples.append(dict(request=request,response=bad,valid=False))
                bad=copy.deepcopy(response);bad['result']['decision_mode']='proposal'
                samples.append(dict(request=request,response=bad,valid=False))
    return samples


def main():
    build=Path(sys.argv[1]).resolve()
    executable=build/('Release/franchise_protocol_check.exe' if sys.platform=='win32' else 'franchise_protocol_check')
    if sys.platform=='win32' and not executable.is_file():executable=build/'franchise_protocol_check.exe'
    samples=corpus()
    result=subprocess.run([str(executable),'--amendment-replies'],
        input=''.join(json.dumps(sample)+'\n' for sample in samples),text=True,capture_output=True,
        check=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
    print(result.stdout,end='')


if __name__=='__main__':main()
