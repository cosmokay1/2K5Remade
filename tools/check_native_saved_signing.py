"""Actual Windows C client/sidecar saved-settlement check with authored inputs only."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import Mock

from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger
from franchise.store import FranchiseStore
from tools.export_legacy_contracts import legacy_contracts
from tools.inspect_franchise_calendar import inspect_calendar
from tools.inspect_franchise_save import TEAMS
from tools.franchise_finance_state import saved_finance_state
from tools.franchise_identity_state import saved_identity_state


def fixture(root, *, runtime_image=None):
    # Existing authored FXG fixture, never a retail file or caller-selected game save.
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
    import test_confirm_saved_signing as authored
    sample=authored.SavedSigningConfirmationTests();sample.setUp()
    if runtime_image is not None:
        sample.bindings['game_context']['loaded_image_sha256']=runtime_image
    path=root/'native saved signing.sqlite';store=FranchiseStore(path)
    contracts=legacy_contracts(sample.bindings,sample.before)
    teams={team:Ledger.from_opening(OpeningBooks(legacy_contracts=contracts[team]),
        cap=80500000,roster_reserve=0,max_bonus_years=5,veteran_minimums={sample.player:(1000,)*15}) for team in TEAMS}
    store.create_franchise(teams,seed=sample.bindings['personality_seed'])
    for team in TEAMS:
        store.initialize_cash(team,(),source='Authored explicit legacy cash scope',
            unknown_legacy_players=tuple(c.player_id for c in contracts[team]))
    calendar=inspect_calendar(sample.before)
    observation={'biography':dict(source_slot=1,first_name='Authored',last_name='Freeagent',pbp_photo_raw='00000000',dob_region_raw='000000'),
        'team':dict(table_index=0,table_mode=2,payroll_raw=4766,league_cap_raw=80500,team_flag_raw=0,first_year_accumulator_raw=0),
        'calendar':{key:calendar[key] for key in ('season_index','display_year','phase_01_raw','phase_02_raw','step_04_raw','step_05_raw','counter_08_raw')}}
    request=dict(protocol=1,request_id='native-captured',operation='negotiate_proposal',timeout_ms=10000,
        observation=observation,guest_offer=sample.raw,expected_revision=1)
    provider=Mock(return_value=json.dumps(dict(action='accept',reason='Authored native saved-signing acceptance',salaries=None,signing_bonus=None)))
    if runtime_image is not None:
        from franchise.snapshot_origin import bind
        bind(store,sample.bindings,sample.before)
    bridge=Bridge(store,provider=provider,access_check=lambda:None,guest_snapshot=(sample.bindings,sample.before))
    if runtime_image is not None:
        assert bridge.handle(dict(protocol=1,request_id='fixture-hello',operation='hello',loaded_image_sha256=runtime_image))['error'] is None
    reply=bridge.handle(request)
    assert reply['error'] is None and reply['result']['outcome']=='accepted_proposal',reply
    replay=bridge.handle(request)
    assert replay['error'] is None and replay['result']['evidence']==reply['result']['evidence']
    reply=replay # Checkpoint history now includes the already recorded proposal.
    provider.assert_called_once()
    paths={key:root/name for key,name in (('save','current.dat'),('after','authored after.dat'),('bindings','bindings.json'),('proposal','proposal.json'),('finance','finance.dat'),('identity','identity.dat'),('after_finance','after-finance.dat'),('after_identity','after-identity.dat'))}
    paths['save'].write_bytes(sample.before);paths['after'].write_bytes(sample.after)
    paths['bindings'].write_text(json.dumps(sample.bindings));paths['proposal'].write_text(json.dumps(request))
    paths['finance'].write_bytes(saved_finance_state(sample.before))
    paths['identity'].write_bytes(saved_identity_state(sample.before))
    paths['after_finance'].write_bytes(saved_finance_state(sample.after))
    paths['after_identity'].write_bytes(saved_identity_state(sample.after))
    return dict(database=path,store=store,sample=sample,provider=provider,paths=paths,reply=reply)


def main():
    if len(sys.argv) not in (2,3) or (len(sys.argv)==3 and sys.argv[2]!='--runtime-bound'):
        raise ValueError('Expected native checker path and optional --runtime-bound')
    executable=Path(sys.argv[1]).resolve()
    runtime_image='a'*64 if len(sys.argv)==3 else None
    with tempfile.TemporaryDirectory(prefix='native saved signing ') as directory:
        data=fixture(Path(directory),runtime_image=runtime_image);paths=data['paths']
        environment={key:value for key,value in os.environ.items() if not key.startswith('NFL2K5_FRANCHISE_')}
        environment.update(NFL2K5_FRANCHISE_GUEST_SIGNING='1',NFL2K5_FRANCHISE_GUEST_SAVE=str(paths['save']),
            NFL2K5_FRANCHISE_GUEST_BINDINGS=str(paths['bindings']),GOOGLE_APPLICATION_CREDENTIALS=str(Path(directory)/'missing-adc.json'))
        result=subprocess.run([str(executable),sys.executable,str(data['database']),str(paths['proposal']),str(paths['after']),str(paths['save']),str(paths['finance']),str(paths['identity']),str(paths['after_finance']),str(paths['after_identity'])]+([runtime_image] if runtime_image is not None else []),
            env=environment,text=True,capture_output=True,timeout=60)
        assert result.returncode==0,(result.returncode,result.stdout,result.stderr)
        replies=[json.loads(line) for line in result.stdout.splitlines()]
        if runtime_image is not None:
            assert len(replies)==18,replies
            observed=replies.pop(0)
            assert observed['error'] is None and observed['result']['ai_enabled'] is False
            assert observed['result']['operations']==['signing_context']
            assert observed['result']['runtime_binding']['franchise_id']==data['sample'].bindings['franchise_id']
            assert replies[0]['error']=='invalid_request' and replies[1]['error']=='state_rejected'
            assert replies.pop(-3)['error']=='state_rejected'  # Failed re-handshake revokes native grant.
            replies=replies[2:]
            binding=replies[0]['result']['runtime_binding']
            assert binding['loaded_image_sha256']==runtime_image and binding['franchise_id']==data['sample'].bindings['franchise_id']
        assert len(replies)==14,replies
        assert replies[1]==data['reply']
        assert replies[2]['error']=='state_rejected' and replies[3]==data['reply']
        assert replies[4]['error']=='state_rejected' and replies[5]==data['reply']
        assert replies[6]['result']['state']=='prepared' and replies[7]['result']['save_position']=='before'
        assert replies[8]['result']['save_position']=='before' and replies[8]['result']['live_application_matches'] is True
        assert replies[9]['result']['save_position']=='candidate_after' and replies[9]['result']['live_application_matches'] is True
        assert replies[10]['result']['state']=='settled'
        assert replies[11]['result']['save_position']=='confirmed_after' and replies[12]['error']=='ai_disabled'
        assert replies[13]['result']['save_position']=='confirmed_after'
        ledger=FranchiseStore(data['database']).load_team('49ers')
        assert ledger.revision==2 and ledger.cash_snapshot()['nominal_total'] is None
        assert ledger.cash_snapshot()['known_totals']['nominal_total']==sum(data['sample'].offer.salaries)+data['sample'].offer.signing_bonus
        assert len(ledger.cash_snapshot()['obligations'])==1
        assert paths['save'].read_bytes()==data['sample'].after
        assert len(data['store'].negotiation_history('49ers',data['sample'].player))==2
        data['provider'].assert_called_once()
        assert replies[10]['result']['after_payload_sha256']==hashlib.sha256(data['sample'].after).hexdigest()
    print('Native captured acceptance, saved candidate, ledger confirmation and disabled restart recovery passed (authored files only).')


if __name__=='__main__':main()
