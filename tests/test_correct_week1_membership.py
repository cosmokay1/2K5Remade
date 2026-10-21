from copy import deepcopy
import unittest

from tools.correct_week1_membership import (club_table_rows, transaction_events, correct_membership,
                                          classify_free_agent_candidates, primary_capture_rows)


class MembershipTests(unittest.TestCase):
    def member(self, name='Authored Player', gsis='authored', team='CLE', status='DEV'):
        return dict(full_name=name,gsis_id=gsis,team=team,status=status,
                    season=2026,week=1,game_type='REG')

    def extract(self, rows, registry, url='https://www.espn.com/nfl/transactions', digest='a'*64):
        return transaction_events(rows,registry,start='2026-09-01',cutoff='2026-09-10',
                                  source_url=url,source_sha256=digest)

    def test_primary_club_attribution_overrides_conflicting_secondary_club(self):
        w=[self.member()];before=deepcopy(w)
        page='L1: 09/01 | Signed Authored Player to the practice squad.'
        url='https://www.clevelandbrowns.com/team/transactions/2026'
        rows=club_table_rows(page,team='CLE',season_year=2026,source_url=url)
        primary=self.extract(rows,w,url,rows[0]['source_sha256'])
        secondary=self.extract([dict(date='2026-09-01',team='DAL',
            description='Signed Authored Player to the practice squad.')],w)
        r=correct_membership(w,secondary+primary,cutoff='2026-09-10')
        self.assertEqual(r['rows'],w);self.assertEqual(w,before)
        self.assertEqual(len(r['source_conflicts']),1)
        self.assertFalse(r['membership_at_cutoff_verified'])

    def test_from_practice_to_active_is_not_misread_as_practice_destination(self):
        w=[self.member()]
        rows=[dict(date='2026-09-05',team='CLE',description=
                   'Signed Authored Player to the active roster from the practice squad.')]
        r=correct_membership(w,self.extract(rows,w),cutoff='2026-09-10')
        self.assertEqual(r['rows'][0]['status'],'ACT')

    def test_release_preserves_retained_review_and_requires_explicit_fa_evidence(self):
        w=[self.member(team='NYG',status='ACT')]
        url='https://www.giants.com/team/transactions/'
        rows=club_table_rows('L1: 09/07 | WR Authored Player - Terminated, Vested Veteran, all contracts',
                             team='NYG',season_year=2026,source_url=url)
        events=self.extract(rows,w,url,rows[0]['source_sha256'])
        r=correct_membership(w,events,cutoff='2026-09-10')
        self.assertEqual(r['rows'][0]['status'],'CUT')
        self.assertIsNone(r['retained_liability_reviews'][0]['charge_dollars'])
        self.assertEqual(len(r['verified_unrestricted_releases']),1)
        events[0]['unrestricted_release_verified']=False
        r=correct_membership(w,events,cutoff='2026-09-10')
        self.assertFalse(r['verified_unrestricted_releases'])

    def test_unordered_same_day_moves_and_temporary_activations_stay_in_review(self):
        w=[self.member()]
        for clauses in [('Signed Authored Player to practice squad.','Released Authored Player.'),
                        ('Activated Authored Player to active roster.',),
                        ('Waived Authored Player with injury designation.',)]:
            events=self.extract([dict(date='2026-09-05',team='CLE',description=c) for c in clauses],w)
            r=correct_membership(w,events,cutoff='2026-09-10')
            self.assertEqual(r['rows'],w);self.assertTrue(r['reviews'])

    def test_extensions_are_not_signed_membership_and_mixed_clauses_are_split(self):
        w=[self.member(),self.member('Another Player','other')]
        rows=[dict(date='2026-09-05',team='CLE',description=
              'Signed Authored Player to practice squad, and released Another Player.')]
        events=self.extract(rows,w)
        self.assertEqual({r['gsis_id']:r['status'] for r in events},{'authored':'DEV','other':'CUT'})
        events=self.extract([dict(date='2026-09-05',team='CLE',description=
             'Signed Authored Player to a two-year extension.')],w)
        self.assertEqual(events[0]['status'],'AMENDMENT')

    def test_wrong_club_year_future_evidence_and_ambiguous_names_fail_safely(self):
        with self.assertRaises(ValueError):
            club_table_rows('',team='DAL',season_year=2026,source_url='https://www.clevelandbrowns.com/team/transactions/')
        with self.assertRaises(ValueError):
            club_table_rows('',team='CLE',season_year=2026,source_url='https://www.clevelandbrowns.com/team/transactions/2025')
        w=[self.member(),self.member(gsis='different')]
        events=self.extract([dict(date='2026-09-05',team='CLE',description='Released Authored Player.')],w)
        self.assertTrue(all(e['status'] is None for e in events))
        event={**events[0],'date':'2026-09-11'}
        with self.assertRaises(ValueError):correct_membership(w,[event],cutoff='2026-09-10')

    def test_confirmed_release_enters_pool_even_when_later_directory_omitted_player(self):
        w=[self.member(team='NYG',status='ACT')]
        url='https://www.giants.com/team/transactions/'
        rows=club_table_rows('L1: 09/07 | WR Authored Player - Terminated, Vested Veteran, all contracts',
                             team='NYG',season_year=2026,source_url=url)
        m=correct_membership(w,self.extract(rows,w,url,rows[0]['source_sha256']),cutoff='2026-09-10')
        r=classify_free_agent_candidates([],m,[],cutoff='2026-09-10',
            identity_rows=[dict(gsis_id='authored',otc_id=123,player='Authored Player')])
        self.assertEqual(r['eligible'][0]['otc_id'],123)
        self.assertFalse(r['exhaustive_pool_verified']);self.assertFalse(r['signing_authorized'])

    def test_missing_rights_and_expired_contracts_do_not_become_free_by_default(self):
        m=correct_membership([self.member(gsis='owned',status='ACT')],[],cutoff='2026-09-10')
        base=dict(player='Candidate',otc_id=100,archived_gsis_ids=['candidate'],fatype='UFA',
                  archived_history=[dict(status='Expired',year_signed=2025,yrs=1)])
        candidates=[base,{**base,'otc_id':101,'archived_gsis_ids':['restricted'],'fatype':'RFA'},
            {**base,'otc_id':102,'archived_gsis_ids':['retired'],'historical_status':'retirement_review'},
            {**base,'otc_id':103,'archived_gsis_ids':['owned']},
            {**base,'otc_id':104,'archived_gsis_ids':[]}]
        r=classify_free_agent_candidates(candidates,m,[],cutoff='2026-09-10')
        self.assertFalse(r['eligible'])
        self.assertEqual([p['status'] for p in r['players']],['expired_contract_candidate_review',
            'restricted_or_exclusive_rights_review','retired','club_owned','identity_review'])
        receipt=dict(url='https://example.test/authored-archive',sha256='a'*64,
                     archive_as_of='2026-09-10T12:00:00Z')
        r=classify_free_agent_candidates(candidates,m,[],cutoff='2026-09-10',archive_receipt=receipt)
        self.assertEqual([p['otc_id'] for p in r['eligible']],[100])
        self.assertFalse(r['exhaustive_pool_verified'])
        receipt['archive_as_of']='2026-09-11T12:00:00Z'
        r=classify_free_agent_candidates(candidates,m,[],cutoff='2026-09-10',archive_receipt=receipt)
        self.assertFalse(r['eligible'])
        with self.assertRaises(ValueError):
            classify_free_agent_candidates(candidates+[base],m,[],cutoff='2026-09-10')

    def test_primary_pages_split_at_headers_even_with_inline_separators(self):
        capture=('Colts (https://www.colts.com/team/transactions/)\n'
                 'L1: 09/01 | Signed Authored Player. -----------------------\n'
                 'Jaguars (https://www.jaguars.com/team/transactions/)\n'
                 'L1: 09/01 | Signed Another Player.\n')
        rows=primary_capture_rows(capture,season_year=2026)
        self.assertEqual([r['team'] for r in rows],['IND','JAX'])
        with self.assertRaises(ValueError):
            club_table_rows(capture,team='IND',season_year=2026,
                            source_url='https://www.colts.com/team/transactions/')

    def test_unambiguous_batch_members_are_not_poisoned_by_one_ambiguous_name(self):
        w=[self.member(),self.member('Shared Name','one'),self.member('Shared Name','two')]
        rows=[dict(date='2026-09-05',team='CLE',description=
                   'Signed Authored Player and Shared Name to practice squad.')]
        events=self.extract(rows,w)
        self.assertEqual(next(e['status'] for e in events if e['gsis_id']=='authored'),'DEV')
        self.assertTrue(all(e['status'] is None for e in events if e['gsis_id']!='authored'))

    def test_present_postfix_narrative_actions_and_settlements_keep_actors_separate(self):
        w=[self.member(),self.member('Another Player','other',status='RES')]
        rows=[dict(date='2026-09-05',team='CLE',description=
            'The Cleveland Browns sign Authored Player to the active roster and waive Another Player from injured reserve with an injury settlement.')]
        events=self.extract(rows,w)
        self.assertEqual({e['gsis_id']:e['status'] for e in events},{'authored':'ACT','other':'CUT'})
        events=self.extract([dict(date='2026-09-05',team='CLE',description=
            'Authored Player and Another Player signed to the practice squad')],w)
        self.assertTrue(all(e['status']=='DEV' for e in events))

    def test_temporary_elevation_preserves_confirmed_practice_owner_without_fa_clearance(self):
        w=[self.member()]
        events=self.extract([dict(date='2026-09-05',team='CLE',description=
             'Elevated Authored Player from practice squad.')],w)
        r=correct_membership(w,events,cutoff='2026-09-10')
        self.assertEqual(r['rows'],w);self.assertFalse(r['reviews'])
        self.assertEqual(len(r['nonownership_events']),1)
        self.assertFalse(r['verified_unrestricted_releases'])
