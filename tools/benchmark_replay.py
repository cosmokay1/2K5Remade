"""Bounded synthetic replay measurement; no cloud, guest or production writes."""
import argparse
from datetime import date
import json
from pathlib import Path
from statistics import median
import tempfile
from time import perf_counter
from franchise.books import ActiveContract,OpeningBooks
from franchise.cap import Ledger,Offer
from franchise.cash import CashObligation
from franchise.store import FranchiseStore
from franchise.trades import PreseasonTradeScope,EXCLUDED_TRADE_LIABILITIES


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--teams',type=int,default=32)
    parser.add_argument('--stories-per-team',type=int,default=20)
    parser.add_argument('--recorded-context',action='store_true',help='Use scripted negotiation evidence and promise proposals; no cloud calls')
    args=parser.parse_args()
    if not 2 <= args.teams <= 64 or not 0 <= args.stories_per_team <= 1000:
        parser.error('Use 2–64 teams and 0–1000 stories per team')
    with tempfile.TemporaryDirectory(prefix='2k5-replay-benchmark-') as directory:
        store=FranchiseStore(Path(directory)/'synthetic.sqlite')
        names=['team-'+str(index) for index in range(args.teams)]
        original=ActiveContract(Offer('v',(10,20,30),9,(0,20,10)),'synthetic benchmark contract')
        for index,team in enumerate(names):
            store.create_team(team,Ledger.from_opening(OpeningBooks(contracts=(original,)) if index==0 else OpeningBooks(),
                cap=1000,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
            records=(CashObligation('contract:v','v',69,9,'synthetic complete bank',(('signing_bonus',9),)),) if index==0 else ()
            store.initialize_cash(team,records,source='synthetic benchmark cash')
            session=None
            if args.recorded_context:
                from franchise.negotiation import Negotiation
                from franchise.store import StoredLedger
                from franchise.performance import PerformanceEvidence,Observation
                from franchise.promises import PromiseGoal
                evidence=PerformanceEvidence('v','synthetic season','cpu_played',(
                    Observation('receptions',50,'synthetic fixture'),
                    Observation('targets',None,'synthetic fixture','Not measured'),
                    Observation('pressures',None,'synthetic fixture','Not measured')),'Synthetic benchmark coverage')
                session=Negotiation(StoredLedger(store,team),player_id='v',personality={'money':0.7},
                    performance=evidence.to_context(),relationships={'trust':0.5},access_check=lambda:None)
            for story in range(args.stories_per_team):
                if session is not None:
                    session.respond('story-'+str(story),Offer('v',(10,),0),lambda _:json.dumps({
                        'action':'reject','reason':'Scripted benchmark decision','salaries':None,'signing_bonus':None}),
                        expected_revision=1,promise_goals=(PromiseGoal('starts','starts',8,80,'synthetic season','synthetic proposal'),))
                else:
                    store.record_negotiation(team,{'request_id':'story-'+str(story),'offer':Offer('v',(10,),0).to_dict(),
                        'action':'reject','reason':'Synthetic benchmark dialogue','counter':None,'outcome':'player_rejected'},access_check=lambda:None)
        scope=PreseasonTradeScope(2026,date(2026,6,1),date(2026,9,10),date(2026,9,11),EXCLUDED_TRADE_LIABILITIES,
                                 True,0,True,True,'synthetic benchmark assignment')
        store.trade_preseason_veteran('assignment',names[0],names[1],'v',scope=scope,
                                     seller_revision=1,buyer_revision=1,access_check=lambda:None)
        elapsed=[]
        for _ in range(5):
            started=perf_counter()
            ledger=store.load_team(names[1])
            elapsed.append((perf_counter()-started)*1000)
            assert ledger.charges==(10,20,30) and ledger.revision==2
        count=sum(len(store.negotiation_history(team,'v')) for team in names)
        assert count==args.teams*args.stories_per_team
        print(json.dumps({'scope':'Synthetic local SQLite replay; not game, Windows or Deck acceptance',
            'teams':args.teams,'dialogue_events':count,'read_samples_ms':elapsed,'median_ms':median(elapsed),
            'max_ms':max(elapsed),'all_team_replay_enabled':True,'records_verified':True,
            'history_payload':'recorded negotiation evidence' if args.recorded_context else 'short legacy dialogue',
            'provider':'scripted local fixture; no model inference'},indent=2))


if __name__=='__main__':main()
