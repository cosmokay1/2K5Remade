"""Self-checking offline personality/history fixture; no live model or game runtime."""
import json
from pathlib import Path
import tempfile
from franchise.books import OpeningBooks
from franchise.cap import Ledger,Offer
from franchise.initialization import initial_actor
from franchise.negotiation import Negotiation
from franchise.performance import PerformanceEvidence,Observation
from franchise.store import FranchiseStore,StoredLedger


def main():
    seed='authored-personality-continuity-fixture-v1'
    candidates=[('fictional-player-'+str(i).zfill(2),initial_actor(seed,'fictional-player-'+str(i).zfill(2))) for i in range(16)]
    low=min(candidates,key=lambda row:row[1]['personality']['money'])
    high=max(candidates,key=lambda row:row[1]['personality']['money'])
    players=(low[0],high[0])
    initial={player:actor['personality'] for player,actor in (low,high)}
    threshold=(initial[low[0]]['money']+initial[high[0]]['money'])/2
    assert low[0]!=high[0] and initial[low[0]]['money']<initial[high[0]]['money']
    observations=(Observation('receptions',50,'synthetic shared observed fixture'),
        Observation('receiving_yards',700,'synthetic shared observed fixture'),
        Observation('targets',None,'synthetic shared observed fixture','Targets are not measured in this fixture'),
        Observation('pressures',None,'synthetic shared observed fixture','Pressures are not measured in this fixture'))
    provider_calls=0
    with tempfile.TemporaryDirectory(prefix='2k5-personality-continuity-') as directory:
        database=Path(directory)/'synthetic.sqlite'
        store=FranchiseStore(database)
        store.create_franchise({'fixture-team':Ledger.from_opening(OpeningBooks(),cap=100,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={player:(1,) for player in players})},seed=seed)
        before_priority={player:store.player_context('fixture-team',player)['personality'] for player in players}
        assert before_priority==initial

        def session(database_store,player):
            context=database_store.player_context('fixture-team',player)
            return Negotiation(StoredLedger(database_store,'fixture-team'),player_id=player,
                personality=context['personality'],relationships=context['relationships'],
                performance=PerformanceEvidence(player,'synthetic common observation window','cpu_played',observations,
                    'Authored fixture coverage; opportunity counters unavailable',team_id='fixture-team',complete_window=False),
                access_check=lambda:None)

        def scripted(context):
            nonlocal provider_calls
            provider_calls+=1
            player=context['player_id']
            assert context['personality']==initial[player]
            assert context['performance']['window']=='synthetic common observation window'
            assert context['performance']['mode']=='cpu_played' and context['performance']['team_id']=='fixture-team'
            assert context['performance']['observations']=={o.counter:{'value':o.value,'source':o.source,
                'unavailable_reason':o.unavailable_reason} for o in observations}
            assert context['performance']['observations']['targets']['value'] is None
            assert context['performance']['observations']['pressures']['value'] is None
            requested=20 if context['personality']['money']<threshold else 30
            if not context['history']:
                assert context['offer']['salaries']==[10]
                return json.dumps({'action':'counter','reason':'Authored fixture money priority requests '+str(requested)+'.',
                    'salaries':[requested],'signing_bonus':0,'guaranteed_salaries':[0],'promise_goals':[]})
            previous=context['history'][0]
            assert previous['request_id']=='week1:'+player and previous['counter']['salaries']==[requested]
            assert context['relationships']['trust']==0.55 and context['offer']['salaries']==[20]
            accepted=context['offer']['salaries'][0]>=previous['counter']['salaries'][0]
            return json.dumps({'action':'accept' if accepted else 'reject',
                'reason':'Authored fixture remembers its prior counter and saved money priority.',
                'salaries':None,'signing_bonus':None,'guaranteed_salaries':None,'promise_goals':None})

        week1={player:session(store,player).respond('week1:'+player,Offer(player,(10,),0),scripted,
            expected_revision=store.load_team('fixture-team').revision) for player in players}
        assert [week1[player]['counter']['salaries'][0] for player in players]==[20,30]
        assert all(event['outcome']=='counteroffer' for event in week1.values())
        assert store.load_team('fixture-team').charges==(0,)
        for player in players:
            # This explicit fixture consequence is manually authored, not inferred
            # from counteroffers or production. It cites the real saved event.
            store.update_relationship('fixture-team','authored-trust:'+player,player,'trust',0.05,
                source_request_id='week1:'+player,expected_revision=store.load_team('fixture-team').revision)
        restarted=FranchiseStore(database)
        for player in players:
            context=restarted.player_context('fixture-team',player)
            assert context['personality']==initial[player] and context['relationships']['trust']==0.55
            assert context['negotiation_history']==[week1[player]]
        week2={player:session(restarted,player).respond('week2:'+player,Offer(player,(20,),0),scripted,
            expected_revision=restarted.load_team('fixture-team').revision) for player in players}
        assert week2[low[0]]['outcome']=='signed' and week2[high[0]]['outcome']=='player_rejected'
        assert provider_calls==4
        final=FranchiseStore(database)
        ledger=final.load_team('fixture-team')
        assert ledger.charges==(20,) and ledger.cap==100 and ledger.room==80
        assert ledger._players=={low[0]}
        before_recall=ledger.generation_snapshot()
        database_before=database.read_bytes()

        def no_regeneration(_):
            raise AssertionError('A durable historical reply must not call a provider again')

        for player in players:
            recalled=session(final,player)
            assert recalled.respond('week1:'+player,Offer(player,(10,),0),no_regeneration)==week1[player]
            assert recalled.respond('week2:'+player,Offer(player,(20,),0),no_regeneration)==week2[player]
            context=final.player_context('fixture-team',player)
            assert context['personality']==initial[player] and context['relationships']['trust']==0.55
        assert final.load_team('fixture-team').generation_snapshot()==before_recall
        assert database.read_bytes()==database_before and provider_calls==4
        print(json.dumps({'scope':'Synthetic scripted local persistence scenario; not a live model, game advance, Windows or Deck runtime',
            'seed':seed,'candidate_ids_examined':16,'money_units':'Authored fixture units; not published NFL salary rules',
            'initial_priorities':initial,'same_observed_performance':{
                'window':'synthetic common observation window','mode':'cpu_played',
                'observations':{o.counter:{'value':o.value,'source':o.source,'unavailable_reason':o.unavailable_reason} for o in observations}},
            'same_week1_offer':[10],'week1_counter_salaries':{p:week1[p]['counter']['salaries'] for p in players},
            'same_week2_offer':[20],'week2_outcomes':{p:week2[p]['outcome'] for p in players},
            'trust_consequence_source':'Explicit manually authored fixture +0.05; each update references its saved week1 counter',
            'trust_after_authored_consequence':{p:0.55 for p in players},
            'cap':100,'team_charge':20,'room':80,'scripted_provider_call_count':provider_calls,
            'live_model_calls':0,'calls_during_restart_recall':0,'priorities_regenerated':False,
            'historical_replies_identical':True,'recall_preserved_database_and_ownership':True},indent=2))


if __name__=='__main__':main()
