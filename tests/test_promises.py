import unittest
from franchise.promises import PromiseGoal,GoalObservation,score_promises


class PromiseTests(unittest.TestCase):
    def goal(self,id,metric,target,weight=1):
        return PromiseGoal(id,metric,target,weight,'synthetic season','synthetic agreement')
    def observation(self,id,value,window='synthetic season'):
        return GoalObservation(id,window,value,'synthetic counter','full-season fixture','Health/coaching context not independently verified')

    def test_importance_weighted_achievement_is_capped_and_nonfinancial(self):
        goals=(self.goal('touches','touches',100,3),self.goal('wins','team_wins',10,1))
        result=score_promises(goals,(self.observation('touches',50),self.observation('wins',12)),window_closed=True)
        self.assertEqual(result['final_achievement_score'],'5/8')
        self.assertEqual([g['status'] for g in result['goals']],['missed','achieved'])
        self.assertIsNone(result['financial_effect'])

    def test_unknown_targets_and_open_window_cannot_be_final_failure(self):
        goals=(self.goal('starts','starts',8),self.goal('yards','receiving_yards',800))
        result=score_promises(goals,(self.observation('starts',4),self.observation('yards',None)),window_closed=False)
        self.assertEqual(result['coverage'],'1/2')
        self.assertEqual(result['observed_progress'],'1/2')
        self.assertIsNone(result['final_achievement_score'])
        self.assertEqual([g['status'] for g in result['goals']],['in_progress','unknown'])
        self.assertIsNone(score_promises(goals,(self.observation('starts',4),),window_closed=True)['final_achievement_score'])

    def test_foreign_period_duplicate_goal_and_boolean_counter_reject(self):
        goal=self.goal('starts','starts',8)
        with self.assertRaises(ValueError):
            score_promises((goal,),(self.observation('starts',8,'other season'),),window_closed=True)
        with self.assertRaises(ValueError):
            score_promises((goal,goal),(),window_closed=True)
        with self.assertRaises(ValueError):
            self.observation('starts',True)
