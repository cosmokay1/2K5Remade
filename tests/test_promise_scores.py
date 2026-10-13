import json
from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger,Offer,Rejected
from franchise.negotiation import Negotiation
from franchise.promises import PromiseGoal,GoalObservation
from franchise.store import FranchiseStore,StoredLedger


class PromiseScoreTests(unittest.TestCase):
    def setup_store(self,directory,goals=None):
        store=FranchiseStore(Path(directory)/'state.sqlite')
        store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={'p':(1,)}))
        session=Negotiation(StoredLedger(store,'a'),player_id='p',personality={},performance={'source':'synthetic'},relationships={'trust':0.6},access_check=lambda:None)
        session.respond('deal',Offer('p',(20,),0),lambda _:json.dumps({'action':'accept','reason':'Starting role','salaries':None,'signing_bonus':None}),
            promise_goals=goals if goals is not None else (PromiseGoal('starts','starts',8,80,'fixture season','authored proposal'),))
        return store
    def observation(self,value):
        return (GoalObservation('starts','fixture season',value,'synthetic stats','full fixture coverage','No verified injury/coaching context'),)
    def score(self,store,request='score',value=4,closed=True,revision=1,agreement='deal'):
        return store.record_promise_score('a',request,agreement,self.observation(value),window_closed=closed,expected_revision=revision,source='synthetic period evaluation')

    def test_scores_persist_recall_and_feed_actor_context_without_money_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            before=store.load_team('a').charges
            result=self.score(store)
            self.assertEqual(result['score']['final_achievement_score'],'1/2')
            reopened=FranchiseStore(store.path)
            self.assertEqual(self.score(reopened),result)
            context=reopened.player_context('a','p')
            self.assertEqual(context['negotiation_history'],reopened.negotiation_history('a','p'))
            self.assertEqual(context['negotiation_history'][0]['outcome'],'signed')
            ledger=reopened.load_team('a')
            self.assertEqual(ledger.charges,before)
            self.assertEqual(ledger.negotiation_context('p')['promise_history'],[result])
            self.assertEqual(ledger.revision,2)
            with self.assertRaisesRegex(Rejected,'Final'):
                self.score(reopened,request='rewrite',value=8,revision=2)

    def test_missing_observations_are_unknown_then_can_be_resolved(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            progress=self.score(store,value=None,closed=False)
            self.assertIsNone(progress['score']['final_achievement_score'])
            self.assertEqual(progress['score']['goals'][0]['status'],'unknown')
            final=self.score(store,request='final',value=8,revision=2)
            self.assertEqual(final['score']['final_achievement_score'],'1')
            self.assertEqual(len(FranchiseStore(store.path).load_team('a').promise_history('p')),2)

    def test_unknown_agreement_stale_revision_and_changed_retry_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            with self.assertRaises(Rejected): self.score(store,agreement='invented')
            with self.assertRaises(Rejected): self.score(store,revision=0)
            self.assertEqual(store.load_team('a').revision,1)
            self.score(store)
            with self.assertRaises(Rejected): self.score(store,value=8)
            self.assertEqual(store.load_team('a').revision,2)

    def test_only_final_known_score_can_source_bounded_trust_consequence(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            self.score(store,request='unknown',value=None,closed=False)
            with self.assertRaises(Rejected):
                store.update_relationship('a','too-early','p','trust',-0.05,source_request_id='unknown',expected_revision=2)
            self.score(store,request='final',value=4,revision=2)
            actor=store.update_relationship('a','consequence','p','trust',-0.05,source_request_id='final',expected_revision=3)
            self.assertEqual(actor['relationships']['trust'],0.55)
            reopened=FranchiseStore(store.path)
            self.assertEqual(reopened.load_team('a').negotiation_context('p')['promise_history'][-1]['score']['final_achievement_score'],'1/2')
            with self.assertRaises(Rejected):
                reopened.update_relationship('a','duplicate','p','trust',-0.05,source_request_id='final',expected_revision=4)
            self.assertEqual(reopened.load_team('a').charges[0],20)

    def test_typed_performance_adapter_replay_and_partial_to_complete_window(self):
        from franchise.performance import PerformanceEvidence,Observation
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            def evidence(complete):
                return PerformanceEvidence('p','fixture season','cpu_played',(Observation('games_started',4,'synthetic starts'),),
                    'fixture season sample',team_id='a',complete_window=complete)
            def record(request,complete,revision):
                return store.record_promise_performance('a',request,'deal',evidence(complete),window_closed=True,
                    expected_revision=revision,source='synthetic closure',context='Synthetic health context')
            partial=record('partial',False,1)
            self.assertIsNone(partial['score']['final_achievement_score'])
            final=record('final',True,2)
            self.assertEqual(final['score']['final_achievement_score'],'1/2')
            store=FranchiseStore(store.path)
            self.assertEqual(record('final',True,2),final)
            with self.assertRaises(Rejected):record('stale',True,1)
            self.assertEqual(store.load_team('a').revision,3)

    def test_historical_six_field_observation_receipt_retries(self):
        import sqlite3
        from contextlib import closing
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            expected=self.score(store)
            with closing(sqlite3.connect(store.path)) as db:
                id,text=db.execute("SELECT id,payload FROM events WHERE kind='promise_score'").fetchone()
                payload=json.loads(text)
                for observation in payload['observations']:
                    observation.pop('complete_window',None)
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),id))
                db.commit()
            self.assertEqual(self.score(FranchiseStore(store.path)),expected)

    def test_multiple_windows_durable_retry_and_financial_conservation(self):
        from franchise.performance import PerformanceEvidence,Observation
        from franchise.promises import TeamResults
        with tempfile.TemporaryDirectory() as directory:
            goals=(PromiseGoal('early','starts',4,1,'early','proposal'),
                   PromiseGoal('wins','team_wins',10,1,'season','proposal'))
            store=self.setup_store(directory,goals)
            early=PerformanceEvidence('p','early','played',(Observation('games_started',4,'fixture'),),
                                      'early totals',team_id='a',complete_window=True)
            season=PerformanceEvidence('p','season','cpu_played',(),'season totals',team_id='a',complete_window=True)
            before=store.load_team('a').charges
            # Missing team results stay unknown, rather than becoming zero wins.
            progress=store.record_promise_performance('a','progress','deal',(early,season),window_closed=False,
                expected_revision=1,source='fixture evaluation',context='fixture health')
            self.assertIsNone(progress['score']['final_achievement_score'])
            team=TeamResults('a','season','cpu_played',10,17,'fixture standings','season totals',complete_window=True)
            def final(snapshot=early):
                return store.record_promise_performance('a','final','deal',(snapshot,season),window_closed=True,
                    expected_revision=2,source='fixture evaluation',context='fixture health',team_results=(team,))
            expected=final()
            self.assertEqual(expected['score']['final_achievement_score'],'1')
            store=FranchiseStore(store.path)
            self.assertEqual(final(),expected)
            changed=PerformanceEvidence('p','early','played',(Observation('games_started',3,'fixture'),),
                                        'early totals',team_id='a',complete_window=True)
            with self.assertRaises(Rejected): final(changed)
            ledger=store.load_team('a')
            self.assertEqual(ledger.charges,before)
            self.assertEqual(ledger.revision,3)
            self.assertEqual(ledger.promise_history('p'),[progress,expected])

    def test_player_context_recent_history_does_not_remove_saved_stories(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            # Signed player's independent negotiation attempts are recorded stories,
            # not new contracts; reject decisions leave the original cap untouched.
            for index in range(12):
                ledger=store.load_team('a')
                event={'request_id':'dialogue-'+str(index),'offer':Offer('p',(20,),0).to_dict(),
                       'action':'reject','reason':'Recorded fixture decision '+str(index),
                       'counter':None,'outcome':'player_rejected'}
                store.record_negotiation('a',event,access_check=lambda:None)
            context=FranchiseStore(store.path).player_context('a','p')
            full=store.negotiation_history('a','p')
            self.assertEqual(context['negotiation_history'],full[-10:])
            self.assertEqual(context['negotiation_history_total'],13)
            self.assertTrue(context['negotiation_history_has_more'])
            self.assertEqual(len(full),13)
            self.assertEqual(store.load_team('a').charges[0],20)

    def test_history_pages_remain_stable_when_new_stories_append(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            def append(index):
                store.record_negotiation('a',{'request_id':'page-'+str(index),'offer':Offer('p',(20,),0).to_dict(),
                    'action':'reject','reason':'Fixture '+str(index),'counter':None,'outcome':'player_rejected'},access_check=lambda:None)
            for index in range(5): append(index)
            first=store.negotiation_history_page('a','p',limit=2)
            self.assertEqual([e['story']['request_id'] for e in first['events']],['page-3','page-4'])
            append(5)
            second=store.negotiation_history_page('a','p',limit=2,before_event_id=first['next_before_event_id'])
            third=FranchiseStore(store.path).negotiation_history_page('a','p',limit=2,before_event_id=second['next_before_event_id'])
            self.assertEqual([e['story']['request_id'] for e in third['events']+second['events']+first['events']],
                             ['deal','page-0','page-1','page-2','page-3','page-4'])
            self.assertIsNone(third['next_before_event_id'])
            for invalid in (True,0,-1,'1',2**63):
                with self.assertRaises(ValueError):store.negotiation_history_page('a','p',before_event_id=invalid)
            self.assertEqual(store.load_team('a').charges[0],20)

    def test_history_pages_filter_other_players_and_nonstory_signings_before_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'mixed.sqlite')
            store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,max_bonus_years=5,
                veteran_minimums={'p':(1,),'q':(1,)}))
            for index,player in enumerate(('p','q','p','q','q')):
                store.record_negotiation('a',{'request_id':'mixed-'+str(index),'offer':Offer(player,(10,),0).to_dict(),
                    'action':'reject','reason':'Fixture','counter':None,'outcome':'player_rejected'},access_check=lambda:None)
            store.sign('a','manual',Offer('p',(10,),0),0)
            page=store.negotiation_history_page('a','p',limit=1)
            self.assertEqual([e['story']['request_id'] for e in page['events']],['mixed-2'])
            older=store.negotiation_history_page('a','p',limit=1,before_event_id=page['next_before_event_id'])
            self.assertEqual([e['story']['request_id'] for e in older['events']],['mixed-0'])
            self.assertIsNone(older['next_before_event_id'])
            self.assertEqual(store.load_team('a').charges[0],10)
