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
    def setup_store(self,directory):
        store=FranchiseStore(Path(directory)/'state.sqlite')
        store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={'p':(1,)}))
        session=Negotiation(StoredLedger(store,'a'),player_id='p',personality={},performance={'source':'synthetic'},relationships={'trust':0.6},access_check=lambda:None)
        session.respond('deal',Offer('p',(20,),0),lambda _:json.dumps({'action':'accept','reason':'Starting role','salaries':None,'signing_bonus':None}),
            promise_goals=(PromiseGoal('starts','starts',8,80,'fixture season','authored proposal'),))
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
