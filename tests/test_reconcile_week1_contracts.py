import hashlib
import unittest
from tests import test_plan_hybrid_roster as fixtures
from tools.inspect_roster_save import inspect_roster
from tools.reconcile_week1_contracts import reconcile_week1, club_source_coverage


class Week1ContractTests(unittest.TestCase):
    def inputs(self):
        roster = bytes(fixtures.HybridPlanTests().roster())
        identity = dict(source_sha256=inspect_roster(roster)['payload_sha256'], season_year=2026,
                        source_identities={'test-player': dict(source_slots=[0])})
        source = dict(url='https://example.test/dated-contracts',sha256=hashlib.sha256(b'authored').hexdigest(),
                      archive_as_of='2026-09-10T18:28:09Z')
        annual = dict(year='2026', team='49ers', cap_number=1.123456)
        row = dict(gsis_id='test-player', otc_id=1, is_active=True, season_history=[annual])
        return roster,identity,[row],source

    def run_report(self, inputs):
        return reconcile_week1(*inputs, cutoff='2026-09-13', money_scale=4)

    def test_exact_source_cap_is_not_invented_salary_or_complete_book(self):
        report = self.run_report(self.inputs())
        player = report['teams']['49ers']['players'][0]
        self.assertEqual(player['source_cap_dollars'], 1123456)
        self.assertIsNone(report['teams']['49ers']['cap_room'])
        self.assertFalse(report['signing_authorized']);self.assertFalse(report['writes_performed'])
        self.assertNotIn('signing_bonus',player)

    def test_duplicate_history_is_deduplicated_and_conflicting_history_rejected(self):
        inputs = self.inputs();row = inputs[2][0]
        row['season_history'] *= 2
        report = self.run_report(inputs)
        self.assertEqual(report['teams']['49ers']['players'][0]['source_cap_dollars'],1123456)
        row['season_history'].append(dict(year='2026',team='49ers',cap_number=9))
        self.assertIsNone(self.run_report(inputs)['teams']['49ers']['players'][0]['source_cap_dollars'])

    def test_missing_or_wrong_team_never_becomes_zero(self):
        for field, value in (('cap_number',None),('cap_number',float('nan')),('team','Giants')):
            inputs=self.inputs();inputs[2][0]['season_history'][0][field]=value
            team=self.run_report(inputs)['teams']['49ers']
            self.assertIsNone(team['players'][0]['source_cap_dollars'])
            self.assertIsNone(team['complete_source_roster_subtotal'])

    def test_mismatched_identity_later_snapshot_and_duplicate_contract_deny(self):
        inputs=self.inputs();inputs[1]['source_sha256']='0'*64
        with self.assertRaises(ValueError):self.run_report(inputs)
        inputs=self.inputs();inputs[3]['archive_as_of']='2026-09-24T12:00:00Z'
        with self.assertRaises(ValueError):self.run_report(inputs)
        inputs=self.inputs();inputs[2].append(dict(inputs[2][0]))
        self.assertEqual(self.run_report(inputs)['teams']['49ers']['players'][0]['status'],
                         'unresolved_identity_or_contract')

    def test_player_duplicated_in_team_and_free_agents_cannot_supply_contract_authority(self):
        inputs=self.inputs()
        inputs[1]['source_identities']['test-player']['source_slots'].append(1)
        player=self.run_report(inputs)['teams']['49ers']['players'][0]
        self.assertEqual(player['status'],'unresolved_identity_or_contract')
        self.assertIsNone(player['source_cap_dollars'])

    def weekly(self):
        return [dict(season='2026', week='1', game_type='REG', team='SF',
                     gsis_id=gsis, full_name=gsis, status=status)
                for gsis, status in [('test-player','ACT'), ('reserve-player','RES'),
                                     ('practice-player','DEV'), ('cut-player','CUT')]]

    def coverage(self, rows=None, contracts=None):
        return club_source_coverage(self.weekly() if rows is None else rows,
            self.inputs()[2] if contracts is None else contracts,
            team_code='SF', team_name='49ers', season_year=2026)

    def test_club_coverage_counts_reserve_and_practice_squad_and_preserves_unknown_debt(self):
        report=self.coverage()
        self.assertEqual(len(report['players']),3)
        self.assertEqual(report['contracts_compared'],1)
        self.assertEqual(report['known_roster_subtotal'],1123456)
        self.assertIsNone(report['complete_roster_subtotal'])
        self.assertIsNone(report['cap_room'])
        self.assertFalse(report['excluded_members'][0]['retained_charge_verified'])
        self.assertFalse(report['complete_opening_book'])

    def test_duplicate_owner_missing_money_and_unknown_status_cannot_look_complete(self):
        rows=self.weekly();rows.append({**rows[0], 'team':'NYG'})
        self.assertEqual(self.coverage(rows)['contracts_compared'],0)
        contracts=self.inputs()[2];contracts[0]['season_history'][0]['cap_number']=None
        self.assertEqual(self.coverage(contracts=contracts)['contracts_compared'],0)
        rows=self.weekly();rows[1]['status']='UNKNOWN'
        with self.assertRaises(ValueError):self.coverage(rows)
