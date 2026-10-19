import unittest

from tools.reconcile_week1_contracts import CLUBS, league_source_coverage


class LeagueCoverageTests(unittest.TestCase):
    def inputs(self):
        weekly, contracts = [], []
        for index, (code, name) in enumerate(CLUBS.items()):
            gsis = f'authored-{index}'
            weekly.append(dict(season=2026, week=1, game_type='REG', team=code,
                               status='ACT', full_name=gsis, gsis_id=gsis))
            contracts.append(dict(gsis_id=gsis, is_active=True,
                season_history=[dict(year='2026', team=name, cap_number=1)]))
        return weekly, contracts

    def audit(self, weekly, contracts):
        return league_source_coverage(weekly, contracts, season_year=2026)

    def test_all_clubs_share_the_pipeline_and_complete_rows_do_not_certify_books(self):
        weekly, contracts = self.inputs()
        report = self.audit(iter(weekly), iter(contracts))
        self.assertEqual(report['clubs_audited'],32)
        self.assertEqual(report['contracts_compared'],32)
        self.assertEqual(report['known_roster_subtotal'],32_000_000)
        self.assertTrue(report['all_roster_schedules_present'])
        self.assertEqual(report['teams']['WAS']['team_name'],'Commanders')
        self.assertEqual(report['teams']['LA']['team_name'],'Rams')
        for key in ('complete_opening_books','free_agent_pool_verified',
                    'ready_for_franchise_test','signing_authorized','writes_performed'):
            self.assertFalse(report[key])

    def test_missing_club_unknown_club_and_later_week_cannot_pass_as_whole_league(self):
        for change in ('missing', 'unknown', 'week'):
            weekly, contracts = self.inputs()
            if change == 'missing':weekly.pop()
            elif change == 'unknown':weekly[-1]['team']='UNKNOWN'
            else:weekly[-1]['week']=2
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.audit(weekly, contracts)

    def test_one_team_gap_or_duplicate_owner_blocks_aggregate_coverage(self):
        weekly, contracts = self.inputs();contracts.pop()
        report = self.audit(weekly, contracts)
        self.assertEqual(report['unresolved_club_members'],1)
        self.assertFalse(report['all_roster_schedules_present'])
        weekly, contracts = self.inputs()
        weekly.append({**weekly[0], 'team':'NYG'})
        report = self.audit(weekly, contracts)
        self.assertEqual(report['unresolved_club_members'],2)
        self.assertFalse(report['all_roster_schedules_present'])

    def test_reserves_and_practice_squad_cannot_disappear_from_any_club(self):
        weekly, contracts = self.inputs()
        for status in ('RES','DEV'):
            weekly.append({**weekly[0], 'gsis_id':status, 'status':status})
        report = self.audit(weekly, contracts)
        self.assertEqual(report['club_members'],34)
        self.assertEqual(report['unresolved_club_members'],2)
        self.assertEqual(len(report['teams']['ARI']['players']),3)
