import unittest
from tools.inspect_simulation_totals import summarize, inspect_totals, FIELDS


class SimulationTotalsTests(unittest.TestCase):
    def test_zero_games_are_unmeasured_not_zero_per_game(self):
        self.assertTrue(all(x is None for x in summarize([])['per_team_game'].values()))

    def test_unequal_games_use_weighted_league_denominator(self):
        teams = [{'games_recorded': n, 'totals': dict.fromkeys(FIELDS, y)}
                 for n, y in [(1, 100), (3, 900)]]
        self.assertEqual(summarize(teams)['per_team_game']['passing_yards'], 250)
        self.assertEqual(summarize(teams)['team_games'], 4)

    def test_unsupported_save_is_rejected(self):
        with self.assertRaises(ValueError):
            inspect_totals(bytes(736))


class ScheduleTemplateTests(unittest.TestCase):
    def fixture(self):
        from tests.test_inspect_franchise_calendar import CalendarTests
        import struct
        data=CalendarTests().fixture()
        start=0x80000
        struct.pack_into('<Ii', data, 0x348, 272, start-0x34c+1)
        for i in range(272):
            struct.pack_into('8B', data, start+i*8, 0, (i%16)*2, (i%16)*2+1, 9, 1, 0, 1, 0)
        return data

    def test_template_has_actual_seventeen_games_per_team(self):
        from tools.inspect_simulation_totals import inspect_schedule_template
        result=inspect_schedule_template(bytes(self.fixture()))
        self.assertEqual(result['scheduled_games'],272)
        self.assertEqual(set(result['games_per_team'].values()),{17})

    def test_bad_or_unbalanced_matchup_and_pointer_rejected(self):
        import struct
        from tools.inspect_simulation_totals import inspect_schedule_template
        for case in range(3):
            data=self.fixture()
            if case==0:data[0x80002]=data[0x80001]
            if case==1:data[0x80001]=2
            if case==2:struct.pack_into('<i',data,0x34c,-0x34c)
            with self.subTest(case=case),self.assertRaises(ValueError):
                inspect_schedule_template(bytes(data))


class RegularScoresTests(unittest.TestCase):
    def test_preseason_is_not_reported_as_regular_season(self):
        from tools.inspect_simulation_totals import inspect_regular_scores
        self.assertIsNone(inspect_regular_scores(bytes(ScheduleTemplateTests().fixture())))

    def test_combined_score_and_actual_games_exclude_unplayed_and_playoffs(self):
        from tools.inspect_simulation_totals import inspect_regular_scores
        data=ScheduleTemplateTests().fixture()
        data[0x91321]=8
        for index,points in [(0,(7,3)), (17,(20,17)), (18*17,(40,40))]:
            pos=0x91320+0x4ca+index*8
            data[pos:pos+8]=bytes([3,0,1,9,1,0,1,0])
            pos=0x91320+0x107a+index*10
            data[pos:pos+10]=bytes([points[0],0,0,0,0,points[1],0,0,0,0])
        result=inspect_regular_scores(bytes(data))
        self.assertEqual(result['completed_games'],2)
        self.assertEqual(result['combined_points'],47)
        self.assertEqual(result['points_per_team_game'],11.75)
        self.assertFalse(result['regular_season_complete'])


class ActualSeasonMappingRegression(unittest.TestCase):
    def test_mislabelled_field_cannot_replace_combined_yardage(self):
        import struct
        from tests.test_inspect_franchise_save import InspectFranchiseSaveTests
        data=InspectFranchiseSaveTests().fixture()
        template=ScheduleTemplateTests().fixture()
        data[0x91320:]=template[0x91320:]
        data[0x348:0x350]=template[0x348:0x350]
        data[0x80000:0x80000+272*8]=template[0x80000:0x80000+272*8]
        for offset,value in [(0x1aa,3562),(0x1ac,2161),(0x1d2,427),(0x1dc,17)]:
            struct.pack_into('<H',data,0x44a8+offset,value)
        result=inspect_totals(bytes(data))
        self.assertNotIn('total_yards',result['league']['totals'])
        self.assertEqual(result['league']['totals']['passing_plus_rushing_yards'],5723)
        self.assertNotIn(0x1d2,FIELDS.values())
