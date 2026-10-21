import unittest
from tools.qualify_week1_releases import qualify_releases
from tools.correct_week1_membership import classify_free_agent_candidates


class ReleaseQualificationTests(unittest.TestCase):
    def sample(self):
        membership=dict(cutoff='2026-09-10',rows=[],reviews=[],verified_unrestricted_releases=[])
        event=dict(gsis_id='one',date='2026-08-31',status='CUT',primary_club_verified=True,
                   clause='Released Player One',unrestricted_release_verified=False)
        participation={'one':[dict(season=y,regular_season_weeks=list(range(1,7))) for y in range(2022,2026)]}
        return membership,event,participation

    def test_four_actual_seasons_qualify_without_assuming_age_or_waiver_clearance(self):
        m,e,p=self.sample();r=qualify_releases(m,[e],p,cutoff=m['cutoff'])
        self.assertEqual(len(r['additional_release_qualifications']),1)
        self.assertEqual(m['verified_unrestricted_releases'],[])
        self.assertFalse(r['free_agent_pool_verified']);self.assertFalse(r['signing_authorized'])

    def test_three_seasons_repeated_weeks_injury_and_later_signing_are_held(self):
        m,e,p=self.sample()
        p['one'][0]['regular_season_weeks']=[1]*6
        self.assertFalse(qualify_releases(m,[e],p,cutoff=m['cutoff'])['additional_release_qualifications'])
        m,e,p=self.sample();e['clause']='Waived/injured Player One'
        self.assertFalse(qualify_releases(m,[e],p,cutoff=m['cutoff'])['additional_release_qualifications'])
        m,e,p=self.sample();later={**e,'date':'2026-09-02','status':'DEV'}
        self.assertFalse(qualify_releases(m,[e,later],p,cutoff=m['cutoff'])['additional_release_qualifications'])

    def test_explicit_primary_vested_termination_does_not_need_inferred_experience(self):
        m,e,p=self.sample();e['unrestricted_release_verified']=True
        self.assertEqual(len(qualify_releases(m,[e],{},cutoff=m['cutoff'])['additional_release_qualifications']),1)
        e['primary_club_verified']=False
        self.assertFalse(qualify_releases(m,[e],p,cutoff=m['cutoff'])['additional_release_qualifications'])

    def test_verified_current_termination_supersedes_stale_tender_directory_label(self):
        m,e,p=self.sample()
        m=qualify_releases(m,[e],p,cutoff=m['cutoff'])
        candidate=dict(player='Player One',otc_id=1,archived_gsis_ids=['one'],fatype='RFA')
        result=classify_free_agent_candidates([candidate],m,[],cutoff=m['cutoff'])
        self.assertEqual(result['eligible'][0]['status'],'verified_vested_termination')
        m['verified_unrestricted_releases']=[]
        result=classify_free_agent_candidates([candidate],m,[],cutoff=m['cutoff'])
        self.assertFalse(result['eligible'])
        self.assertEqual(result['players'][0]['status'],'restricted_or_exclusive_rights_review')
