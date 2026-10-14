from contextlib import closing
from dataclasses import FrozenInstanceError,replace
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from franchise.cap import Offer,Rejected
from franchise.performance import PerformanceEvidence,Observation
from franchise.promises import PromiseCircumstances,GoalObservation,score_promises
from franchise.store import FranchiseStore
from tests import test_promise_scores


class PromiseCircumstancesTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.fixture=test_promise_scores.PromiseScoreTests();self.store=self.fixture.setup_store(temp.name)

    def circumstances(self,**changes):
        return replace(PromiseCircumstances('p','a','fixture season','cpu_played',16,12,4,2,
            'synthetic availability report','synthetic full window',True,None),**changes)

    def score(self,**changes):
        args=dict(window_closed=True,expected_revision=1,source='synthetic period evaluation',circumstances=(self.circumstances(),))
        args.update(changes)
        return self.store.record_promise_score('a','score','deal',self.fixture.observation(4),**args)

    def test_context_preserved_raw_score_relationship_and_money_unadjusted(self):
        before=self.store.load_team('a');charges=before.charges;actor=before._actors['p']
        goals=self.store.load_team('a')._promise_agreements['deal']['goals']
        from franchise.promises import goals_from_list
        expected=score_promises(goals_from_list(goals),self.fixture.observation(4),window_closed=True)
        result=self.score()
        self.assertEqual(result['score'],expected)
        self.assertEqual(result['score']['final_achievement_score'],'1/2')
        self.assertEqual(result['circumstances'],[self.circumstances().to_dict()])
        reopened=FranchiseStore(self.store.path);ledger=reopened.load_team('a')
        self.assertEqual(ledger.charges,charges);self.assertEqual(ledger._actors['p'],actor)
        self.assertEqual(ledger.negotiation_context('p')['promise_history'],[result])
        self.assertEqual(reopened.player_context('a','p')['promise_history'],[result])
        self.assertEqual(self.score(),result)
        with self.assertRaises(Rejected):self.score(circumstances=None)
        with self.assertRaises(Rejected):self.score(circumstances=(self.circumstances(source='changed'),))
        with closing(sqlite3.connect(self.store.path)) as db:
            payload=json.loads(db.execute("SELECT payload FROM events WHERE kind='promise_score'").fetchone()[0])
            self.assertEqual(payload['format'],1);self.assertEqual(payload['circumstances'],result['circumstances'])

    def test_unknown_counts_remain_unknown_without_altering_final_achievement(self):
        context=self.circumstances(available_games=None,injury_unavailable_games=None,coaching_dnp_games=None,
            complete_window=False,unavailable_reason='No availability collector supplied')
        result=self.score(circumstances=(context,))
        self.assertIsNone(result['circumstances'][0]['available_games'])
        self.assertEqual(result['score']['final_achievement_score'],'1/2')
        self.assertEqual(result['score']['goals'][0]['observed'],4)

    def test_invalid_counts_provenance_bounds_and_types_reject(self):
        for changes in ({'total_games':True},{'total_games':-1},{'available_games':17},
                        {'coaching_dnp_games':13},{'injury_unavailable_games':5},
                        {'available_games':None},{'source':''},{'complete_window':1},
                        {'mode':'invented'},{'unavailable_reason':'known but missing'}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.circumstances(**changes)
        with self.assertRaises(FrozenInstanceError):self.circumstances().source='changed'
        data=self.circumstances().to_dict();data['unexpected']='value'
        with self.assertRaises(ValueError):PromiseCircumstances.from_dict(data)

    def test_foreign_duplicate_and_unagreed_window_reject_without_events(self):
        before=Path(self.store.path).read_bytes()
        for contexts in ((self.circumstances(player_id='other'),),(self.circumstances(team_id='other'),),
                         (self.circumstances(window='other'),),(self.circumstances(),self.circumstances()),()):
            with self.subTest(contexts=contexts),self.assertRaises(ValueError):self.score(circumstances=contexts)
            self.assertEqual(Path(self.store.path).read_bytes(),before)

    def test_performance_adapter_checks_source_mode_team_player_and_window(self):
        performance=PerformanceEvidence('p','fixture season','cpu_played',(Observation('games_started',4,'synthetic starts'),),
            'synthetic full season',team_id='a',complete_window=True)
        for context in (self.circumstances(mode='fast_sim'),self.circumstances(team_id='other'),self.circumstances(window='other')):
            with self.assertRaises(ValueError):
                self.store.record_promise_performance('a','score','deal',performance,window_closed=True,
                    expected_revision=1,source='synthetic score',context='Authored context',circumstances=(context,))
        for invalid in ({},(performance,{})):
            with self.assertRaises(ValueError):
                self.store.record_promise_performance('a','invalid','deal',invalid,window_closed=True,
                    expected_revision=1,source='synthetic score',context='Authored context',circumstances=(self.circumstances(),))
        result=self.store.record_promise_performance('a','score','deal',performance,window_closed=True,
            expected_revision=1,source='synthetic score',context='Authored context',circumstances=(self.circumstances(),))
        self.assertEqual(result['score']['final_achievement_score'],'1/2')
        self.assertEqual(FranchiseStore(self.store.path).load_team('a').promise_history('p'),[result])

    def test_strict_versioned_result_and_source_tampering_rejected(self):
        self.score()
        with closing(sqlite3.connect(self.store.path)) as db:
            original=db.execute("SELECT payload FROM events WHERE kind='promise_score'").fetchone()[0]
        for scenario in ('bool_count','foreign','window','duplicate','unknown_field','result_type','format'):
            data=json.loads(original)
            if scenario=='bool_count':data['circumstances'][0]['coaching_dnp_games']=True
            if scenario=='foreign':data['circumstances'][0]['team_id']='other'
            if scenario=='window':data['circumstances'][0]['window']='other'
            if scenario=='duplicate':data['circumstances'].append(data['circumstances'][0])
            if scenario=='unknown_field':data['unexpected']=1
            if scenario=='result_type':data['result']['circumstances'][0]['coaching_dnp_games']=True
            if scenario=='format':data['format']=True
            with closing(sqlite3.connect(self.store.path)) as db,db:
                db.execute("UPDATE events SET payload=? WHERE kind='promise_score'",(json.dumps(data),))
            with self.subTest(scenario=scenario),self.assertRaises((ValueError,Rejected)):self.store.load_team('a')
            with closing(sqlite3.connect(self.store.path)) as db,db:
                db.execute("UPDATE events SET payload=? WHERE kind='promise_score'",(original,))

    def test_legacy_event_receipt_shape_remains_unchanged(self):
        result=self.fixture.score(self.store)
        self.assertNotIn('circumstances',result)
        with closing(sqlite3.connect(self.store.path)) as db:
            payload=json.loads(db.execute("SELECT payload FROM events WHERE kind='promise_score'").fetchone()[0])
        self.assertNotIn('format',payload);self.assertNotIn('circumstances',payload)
        with self.assertRaises(Rejected):self.score()

    def test_sourced_circumstances_reach_provider_after_release_without_adjusting_achievement(self):
        from franchise.cash import CashObligation
        from franchise.negotiation import Negotiation
        from franchise.store import StoredLedger
        from tests import test_releases,test_return_sign_ledger
        self.store.initialize_cash('a',(CashObligation('contract:p','p',20,0,'synthetic explicit contract cash',()),),
            source='synthetic complete source cash')
        score=self.score(expected_revision=2)
        release=test_releases.PreseasonReleaseTests().plan()
        self.store.release_preseason_veteran('a','release','p',scope=release.scope,discount=release.discount,
            payment_year_offsets=(0,),expected_revision=3,access_check=lambda:None)
        FranchiseStore.migrate_generations(self.store.path)
        session=Negotiation(StoredLedger(self.store,'a',return_scope=test_return_sign_ledger.ReturnSigningLedgerTests().scope()),
            player_id='p',personality={},performance={},relationships={'trust':0.6},access_check=lambda:None)
        contexts=[]
        def provider(context):
            contexts.append(context)
            return json.dumps({'action':'reject','reason':'synthetic context review','salaries':None,'signing_bonus':None})
        session.respond('return-review',Offer('p',(20,),0),provider,expected_revision=4)
        self.assertEqual(contexts[0]['accounting']['promise_history'],[score])
        self.assertEqual(contexts[0]['accounting']['promise_history'][0]['score']['final_achievement_score'],'1/2')
        self.assertEqual(contexts[0]['accounting']['promise_history'][0]['circumstances'][0]['injury_unavailable_games'],4)
        self.assertEqual(self.store.load_team('a')._actors['p']['relationships']['trust'],0.6)
