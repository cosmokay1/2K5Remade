from copy import deepcopy
from hashlib import sha256
import unittest
from tools.adjudicate_week1_reviews import adjudicate,review_digest


class ReviewAdjudicationTests(unittest.TestCase):
    def inputs(self,status='RES'):
        review=dict(gsis_id='authored',events=[dict(team='NYG',date='2026-09-03')],reason='authored review')
        report=dict(cutoff='2026-09-10',rows=[dict(gsis_id='authored',team='NYG',status=status,
            season=2026,week=1,game_type='REG')],reviews=[review],corrections=[],retained_liability_reviews=[])
        body=b'authored primary evidence';digest=sha256(body).hexdigest()
        decision=dict(gsis_id='authored',team='NYG',decision='waived_from_reserve',
            review_sha256=review_digest(review),effective_date='2026-09-03',rationale='Explicit authored release',
            proofs=[dict(url='https://www.giants.com/team/transactions/',sha256=digest)])
        return report,decision,{digest:body}

    def test_release_preserves_debt_review_and_does_not_grant_eligibility(self):
        report,decision,sources=self.inputs();before=deepcopy(report)
        result=adjudicate(report,[decision],sources)
        self.assertEqual(report,before);self.assertEqual(result['rows'][0]['status'],'CUT')
        self.assertFalse(result['reviews']);self.assertFalse(result['signing_authorized'])
        self.assertIsNone(result['retained_liability_reviews'][0]['charge_dollars'])
        self.assertFalse(result['free_agent_pool_verified'])

    def test_cutoff_reserve_hold_stays_owned_and_unavailable(self):
        report,decision,sources=self.inputs();decision['decision']='preserve_injury_rights_hold'
        result=adjudicate(report,[decision],sources)
        self.assertEqual(result['rows'][0]['status'],'RES')
        self.assertTrue(result['rows'][0]['availability_rights_hold'])
        report['rows'][0]['status']='ACT'
        with self.assertRaises(ValueError):adjudicate(report,[decision],sources)

    def test_wrong_name_association_does_not_move_original_player(self):
        report,decision,sources=self.inputs('CUT');decision['decision']='reject_name_association'
        result=adjudicate(report,[decision],sources)
        self.assertEqual(result['rows'],report['rows']);self.assertFalse(result['reviews'])

    def test_changed_review_wrong_source_duplicate_and_future_change_fail(self):
        report,decision,sources=self.inputs()
        for field,value in [('review_sha256','f'*64),('effective_date','2026-09-11'),('rationale','')]:
            bad=deepcopy(decision);bad[field]=value
            with self.assertRaises(ValueError):adjudicate(report,[bad],sources)
        with self.assertRaises(ValueError):adjudicate(report,[decision,decision],sources)
        with self.assertRaises(ValueError):adjudicate(report,[decision],{})
        decision['proofs'][0]['url']='https://www.jets.com/team/transactions/'
        with self.assertRaises(ValueError):adjudicate(report,[decision],sources)
