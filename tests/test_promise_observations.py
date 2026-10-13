import unittest
from franchise.performance import PerformanceEvidence,Observation
from franchise.promises import PromiseGoal,TeamResults,observe_promises,score_promises


class PromiseObservationTests(unittest.TestCase):
    def evidence(self,observations,player='p'):
        return PerformanceEvidence(player,'fixture season','cpu_played',observations,'synthetic season coverage',team_id='a',complete_window=True)
    def goal(self,metric):
        return PromiseGoal(metric,metric,20,1,'fixture season','authored agreement')
    def observe(self,goals,performance,team=None):
        return observe_promises(goals,performance,player_id='p',team_id='a',context='Synthetic health/coaching context',team_results=team)

    def test_touches_use_carries_and_receptions_not_targets(self):
        evidence=self.evidence((Observation('rush_attempts',5,'fixture carries'),Observation('receptions',10,'fixture catches'),Observation('targets',100,'fixture targets')))
        observations=self.observe((self.goal('touches'),),evidence)
        self.assertEqual(observations[0].value,15)
        self.assertIn('fixture carries',observations[0].source)
        self.assertEqual(score_promises((self.goal('touches'),),observations,window_closed=True)['final_achievement_score'],'3/4')

    def test_missing_carries_and_starts_stay_unknown(self):
        evidence=self.evidence((Observation('receptions',10,'fixture catches'),Observation('snaps',500,'fixture snaps'),Observation('games',16,'fixture games')))
        observations=self.observe((self.goal('touches'),self.goal('starts')),evidence)
        self.assertEqual([o.value for o in observations],[None,None])
        self.assertIn('rush_attempts: not recorded',observations[0].context)
        self.assertIsNone(score_promises((self.goal('touches'),self.goal('starts')),observations,window_closed=True)['final_achievement_score'])

    def test_team_wins_require_matching_team_window_and_mode(self):
        evidence=self.evidence(())
        team=TeamResults('a','fixture season','cpu_played',10,16,'fixture standings','synthetic standings')
        self.assertEqual(self.observe((self.goal('team_wins'),),evidence,team)[0].value,10)
        with self.assertRaises(ValueError):
            self.observe((self.goal('team_wins'),),evidence,TeamResults('b','fixture season','cpu_played',10,16,'fixture','fixture'))
        with self.assertRaises(ValueError):
            self.observe((self.goal('touches'),),self.evidence((),player='other'))
        with self.assertRaises(ValueError):
            self.evidence((Observation('games',2,'fixture'),Observation('games_started',3,'fixture')))

    def test_partial_or_unscoped_known_evidence_cannot_finalize(self):
        for complete,team in ((False,'a'),(True,None)):
            evidence=PerformanceEvidence('p','fixture season','cpu_played',(Observation('games_started',8,'fixture'),),
                                         'partial fixture',team_id=team,complete_window=complete)
            observations=self.observe((self.goal('starts'),),evidence)
            result=score_promises((self.goal('starts'),),observations,window_closed=True)
            self.assertIsNone(result['final_achievement_score'])
            self.assertEqual(result['goals'][0]['status'],'incomplete')
        with self.assertRaises(ValueError):
            self.observe((self.goal('starts'),),PerformanceEvidence('p','fixture season','cpu_played',(),
                         'foreign club',team_id='b',complete_window=True))

    def test_multiple_windows_preserve_goals_and_partial_coverage(self):
        from franchise.promises import observe_promise_windows
        goals=(PromiseGoal('early','starts',4,1,'early','agreement'),
               PromiseGoal('season','team_wins',10,1,'season','agreement'))
        early=PerformanceEvidence('p','early','played',(Observation('games_started',4,'starts'),),
                                  'early coverage',team_id='a',complete_window=True)
        season=PerformanceEvidence('p','season','cpu_played',(),'season coverage',team_id='a',complete_window=True)
        team=TeamResults('a','season','cpu_played',10,17,'standings','season coverage',complete_window=True)
        result=observe_promise_windows(goals,(season,early),player_id='p',team_id='a',context='fixture',team_results=(team,))
        self.assertEqual([o.goal_id for o in result],['early','season'])
        self.assertEqual(score_promises(goals,result,window_closed=True)['final_achievement_score'],'1')
        partial=TeamResults('a','season','cpu_played',10,17,'standings','partial')
        result=observe_promise_windows(goals,(early,season),player_id='p',team_id='a',context='fixture',team_results=(partial,))
        self.assertIsNone(score_promises(goals,result,window_closed=True)['final_achievement_score'])
        for snapshots in ((early,), (early,season,season)):
            with self.assertRaises(ValueError):
                observe_promise_windows(goals,snapshots,player_id='p',team_id='a',context='fixture')

    def test_unneeded_team_results_still_require_matching_scope(self):
        from franchise.promises import observe_promise_windows
        evidence=self.evidence((Observation('games_started',10,'fixture'),))
        goals=(self.goal('starts'),)
        for team in (TeamResults('a','other period','cpu_played',1,1,'fixture','fixture'),
                     TeamResults('a','fixture season','played',1,1,'fixture','fixture')):
            with self.assertRaises(ValueError): self.observe(goals,evidence,team)
            with self.assertRaises(ValueError):
                observe_promise_windows(goals,(evidence,),player_id='p',team_id='a',context='fixture',team_results=(team,))

        foreign=PerformanceEvidence('p','fixture season','cpu_played',(Observation('games_started',10,'fixture'),),
                                    'fixture',team_id='b',complete_window=True)
        with self.assertRaises(ValueError):
            observe_promise_windows(goals,(foreign,),player_id='p',team_id='a',context='fixture')
