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



def release_history_benchmark(*,generation_checkpoint=False):
    from fractions import Fraction
    from franchise.bridge import Bridge
    from franchise.guarantees import DiscountProfile
    from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
    started=perf_counter()
    with tempfile.TemporaryDirectory(prefix='2k5-release-replay-benchmark-') as directory:
        store=FranchiseStore(Path(directory)/'synthetic.sqlite')
        contracts=tuple(ActiveContract(Offer('player-'+str(i),(1000000,)*3,9000000,(0,1000000,1000000)),
            'synthetic benchmark original') for i in range(53))
        store.create_team('team',Ledger.from_opening(OpeningBooks(contracts=contracts),cap=300000000,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={c.offer.player_id:(1,)*3 for c in contracts}))
        store.initialize_cash('team',tuple(CashObligation('contract:'+c.offer.player_id,c.offer.player_id,12000000,9000000,
            'synthetic benchmark paid bonus',(('signing_bonus',9000000),)) for c in contracts),source='synthetic complete cash')
        scope=PreseasonReleaseScope(2026,date(2026,6,1),date(2026,9,10),EXCLUDED_LIABILITIES,
            True,True,0,'synthetic supported preseason release')
        discount=DiscountProfile(2026,Fraction(0),'synthetic zero discount rate')
        for index,contract in enumerate(contracts[:30]):
            store.release_preseason_veteran('team','release-'+str(index),contract.offer.player_id,
                scope=scope,discount=discount,payment_year_offsets=(0,1,2),expected_revision=index+1,access_check=lambda:None)
        fixture_build_ms=(perf_counter()-started)*1000
        checkpoint_ms=None
        if generation_checkpoint:
            checkpoint_started=perf_counter()
            FranchiseStore.migrate_generations(store.path)
            checkpoint_ms=(perf_counter()-checkpoint_started)*1000
        before=store.load_team('team').generation_snapshot()
        database_before=Path(store.path).read_bytes()
        expected_cash={'nominal_total':606000000,'paid_total':477000000,'unpaid_total':129000000}
        read_samples=[]
        for _ in range(5):
            read_started=perf_counter();ledger=store.load_team('team')
            read_samples.append((perf_counter()-read_started)*1000)
            # Each released contract retains9m bonus+2m guaranteed base inyear0;
            # 23 active contracts retain4m annually. No retail figures inferred.
            assert ledger.charges==(422000000,92000000,92000000) and ledger.revision==31
            assert {key:ledger.cash_snapshot()[key] for key in expected_cash}==expected_cash
            assert len(ledger._players)==23 and len(ledger._released)==30
        def forbidden(*_):
            raise AssertionError('Local manual benchmark must not call cloud/model')
        bridge=Bridge(store,provider=forbidden,access_check=forbidden)
        request={'protocol':1,'request_id':'release-29','operation':'manual_release','team_id':'team','player_id':'player-29',
            'expected_revision':30,'timeout_ms':60000,'decision_mode':'manual',
            'scope':{'league_year':2026,'removed_on':'2026-06-01','first_regular_season_game':'2026-09-10',
                'exclusions':sorted(scope.exclusions),'covered_guarantees':True,'healthy':True,'current_year_earned_base':0,
                'source':scope.source},
            'discount':{'league_year':2026,'annual_rate':0,'rate_source':discount.rate_source},'payment_year_offsets':[0,1,2]}
        full_receipt=store.release_preseason_veteran('team','release-29','player-29',scope=scope,discount=discount,
            payment_year_offsets=(0,1,2),expected_revision=30,access_check=lambda:None)
        full_reply=Bridge._reply('release-29',result={'decision_mode':'manual','player_id':'player-29','release':full_receipt})
        full_bytes=len(json.dumps(full_reply,allow_nan=False).encode('utf-8'))+1
        request['receipt_format']='target_v1'
        retry_samples=[];original_reply=None
        for _ in range(5):
            retry_started=perf_counter();reply=bridge.handle(request)
            retry_samples.append((perf_counter()-retry_started)*1000)
            assert reply['error'] is None and reply['result']['receipt_format']=='target_v1'
            if original_reply is None:original_reply=reply
            assert reply==original_reply
        compact_bytes=len(json.dumps(original_reply,allow_nan=False).encode('utf-8'))+1
        assert full_bytes>65536 and compact_bytes<=65536
        assert json.dumps(store.load_team('team').generation_snapshot(),sort_keys=True)==json.dumps(before,sort_keys=True)
        assert Path(store.path).read_bytes()==database_before
        return {'scope':'Synthetic local SQLite replay; not game, Windows or Deck acceptance',
            'profile':'53 synthetic contracts and 30 sourced preseason releases; no cloud/model or guest writes',
            'database_format':4 if generation_checkpoint else 3,'teams':1,'contracts':53,'release_events':30,
            'fixture_build_ms':fixture_build_ms,'checkpoint_ms':checkpoint_ms,
            'read_samples_ms':read_samples,'median_ms':median(read_samples),'max_ms':max(read_samples),
            'compact_retry_samples_ms':retry_samples,'compact_retry_median_ms':median(retry_samples),
            'full_reply_bytes':full_bytes,'compact_reply_bytes':compact_bytes,'frame_limit_bytes':65536,
            'expected_cap_charges':[422000000,92000000,92000000],'expected_nominal_cash':expected_cash,
            'records_verified':True,'retries_preserved_exact_state':True,'provider':'none; explicit manual historical retry'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--teams',type=int,default=32)
    parser.add_argument('--stories-per-team',type=int,default=20)
    parser.add_argument('--recorded-context',action='store_true',help='Use scripted negotiation evidence and promise proposals; no cloud calls')
    parser.add_argument('--release-history',action='store_true',help='Measure fixed 53-contract/30-release local fixture and compact native retries')
    parser.add_argument('--generation-checkpoint',action='store_true',help='Migrate the synthetic fixture to format4 before measuring reads')
    args=parser.parse_args()
    if not 2 <= args.teams <= 64 or not 0 <= args.stories_per_team <= 1000:
        parser.error('Use 2–64 teams and 0–1000 stories per team')
    if args.release_history:
        if args.recorded_context:
            parser.error('--release-history uses manual receipts; --recorded-context is incompatible')
        print(json.dumps(release_history_benchmark(generation_checkpoint=args.generation_checkpoint),indent=2))
        return
    with tempfile.TemporaryDirectory(prefix='2k5-replay-benchmark-') as directory:
        store=FranchiseStore(Path(directory)/'synthetic.sqlite')
        names=['team-'+str(index) for index in range(args.teams)]
        original=ActiveContract(Offer('v',(10,20,30),9,(0,20,10)),'synthetic benchmark contract')
        for index,team in enumerate(names):
            store.create_team(team,Ledger.from_opening(OpeningBooks(contracts=(original,)) if index==0 else OpeningBooks(),
                cap=1000,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3,'n':(1,)*3}))
            records=(CashObligation('contract:v','v',69,9,'synthetic complete bank',(('signing_bonus',9),)),) if index==0 else ()
            store.initialize_cash(team,records,source='synthetic benchmark cash')
            session=None
            if args.recorded_context:
                from franchise.negotiation import Negotiation
                from franchise.store import StoredLedger
                from franchise.performance import PerformanceEvidence,Observation
                from franchise.promises import PromiseGoal
                evidence=PerformanceEvidence('n','synthetic season','cpu_played',(
                    Observation('receptions',50,'synthetic fixture'),
                    Observation('targets',None,'synthetic fixture','Not measured'),
                    Observation('pressures',None,'synthetic fixture','Not measured')),'Synthetic benchmark coverage')
                session=Negotiation(StoredLedger(store,team),player_id='n',personality={'money':0.7},
                    performance=evidence.to_context(),relationships={'trust':0.5},access_check=lambda:None)
            for story in range(args.stories_per_team):
                if session is not None:
                    session.respond('story-'+str(story),Offer('n',(10,),0),lambda _:json.dumps({
                        'action':'reject','reason':'Scripted benchmark decision','salaries':None,'signing_bonus':None}),
                        expected_revision=1,promise_goals=(PromiseGoal('starts','starts',8,80,'synthetic season','synthetic proposal'),))
                else:
                    store.record_negotiation(team,{'request_id':'story-'+str(story),'offer':Offer('n',(10,),0).to_dict(),
                        'action':'reject','reason':'Synthetic benchmark dialogue','counter':None,'outcome':'player_rejected'},access_check=lambda:None)
        scope=PreseasonTradeScope(2026,date(2026,6,1),date(2026,9,10),date(2026,9,11),EXCLUDED_TRADE_LIABILITIES,
                                 True,0,True,True,'synthetic benchmark assignment')
        original_receipt=store.trade_preseason_veteran('assignment',names[0],names[1],'v',scope=scope,
                                     seller_revision=1,buyer_revision=1,access_check=lambda:None)
        if args.generation_checkpoint:
            FranchiseStore.migrate_generations(store.path)
        elapsed=[]
        for _ in range(5):
            started=perf_counter()
            ledger=store.load_team(names[1])
            elapsed.append((perf_counter()-started)*1000)
            assert ledger.charges==(10,20,30) and ledger.revision==2
        retry_elapsed=[]
        for _ in range(5):
            started=perf_counter()
            receipt=store.trade_preseason_veteran('assignment',names[0],names[1],'v',scope=scope,
                seller_revision=1,buyer_revision=1,access_check=lambda:None)
            retry_elapsed.append((perf_counter()-started)*1000)
            assert receipt==original_receipt
        count=sum(len(store.negotiation_history(team,'n')) for team in names)
        assert count==args.teams*args.stories_per_team
        print(json.dumps({'scope':'Synthetic local SQLite replay; not game, Windows or Deck acceptance',
            'database_format':4 if args.generation_checkpoint else 3,
            'teams':args.teams,'dialogue_events':count,'read_samples_ms':elapsed,'median_ms':median(elapsed),
            'max_ms':max(elapsed),'all_team_replay_enabled':True,'records_verified':True,
            'paired_retry_samples_ms':retry_elapsed,'paired_retry_median_ms':median(retry_elapsed),
            'history_payload':'recorded negotiation evidence' if args.recorded_context else 'short legacy dialogue',
            'provider':'scripted local fixture; no model inference'},indent=2))


if __name__=='__main__':main()
