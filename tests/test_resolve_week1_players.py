"""Authored aliases must never silently repair a conflicting player identity."""
import unittest
from tests import test_plan_hybrid_roster as fixtures
from tools.resolve_week1_players import resolve_week1, normalize_name


class Week1IdentityTests(unittest.TestCase):
    def rows(self):
        return [dict(season='2026', week='1', game_type='REG', gsis_id='test-1',
                     full_name='Synthetic Starter', first_name='Legal', last_name='Starter',
                     football_name='Synthetic', birth_date='2000-01-02', team='NYG', status='ACT'),
                dict(season='2026', week='1', game_type='REG', gsis_id='test-2',
                     full_name='Authored Freeagent', first_name='Authored', last_name='Freeagent',
                     birth_date='2000-01-02', team='NYJ', status='ACT')]

    def test_normalization_and_sourced_aliases_keep_native_photo_mapping(self):
        self.assertEqual(normalize_name('D.J. Example Jr.'), normalize_name('DJ Example'))
        native = fixtures.HybridPlanTests().roster()
        report = resolve_week1(bytes(native), bytes(native), self.rows(), season_year=2026)
        self.assertEqual(len(report['matched']), 2)
        self.assertTrue(report['all_source_images_verified'])
        self.assertFalse(report['writes_performed'])
        self.assertFalse(report['contracts_reconciled'])
        self.assertFalse(report['free_agent_pool_verified'])
        self.assertEqual(report['free_agent_audit'][0]['blocker'], 'week1_club_status_conflict')

    def test_unknown_birth_date_and_later_week_cannot_supply_identity(self):
        native = fixtures.HybridPlanTests().roster()
        source = bytearray(native);source[0xAFA8+0x1A] = 3
        report = resolve_week1(bytes(native), bytes(source), self.rows(), season_year=2026)
        self.assertEqual(report['unresolved_source'][0]['reason'], 'birth_date_conflict')
        rows = self.rows();rows[0]['week'] = '2'
        report = resolve_week1(bytes(native), bytes(native), rows, season_year=2026)
        self.assertEqual(report['unresolved_source'][0]['reason'], 'unknown_name')

    def test_conflicting_authoritative_identity_and_empty_table_reject(self):
        native = bytes(fixtures.HybridPlanTests().roster())
        rows = self.rows();rows.append({**rows[0], 'birth_date': '2000-01-03'})
        with self.assertRaises(ValueError):resolve_week1(native, native, rows, season_year=2026)
        with self.assertRaises(ValueError):resolve_week1(native, native, [], season_year=2026)

    def test_profile_match_is_explicit_and_requires_independent_physical_evidence(self):
        native = fixtures.HybridPlanTests().roster()
        source = bytearray(native);source[0xAFA8+0x1A] = 3
        for data in (native, source):
            data[0xAFA8+0x2B] = 72;data[0xAFA8+0x2A] = 50
        rows = self.rows();rows[0].update(height='72',weight='200',position='QB')
        report=resolve_week1(bytes(native),bytes(source),rows,season_year=2026,
                             allow_biography_corrections=True)
        player=next(p for p in report['matched'] if p['gsis_id']=='test-1')
        self.assertEqual(player['sourced_birth_date'],'2000-01-02')
        self.assertEqual(player['birth_date'],'2000-01-03')
        self.assertEqual(player['source_identity_method'],'unique_sourced_name_and_physical_profile')
        source[0xAFA8+0x2B] = 73
        report=resolve_week1(bytes(native),bytes(source),rows,season_year=2026,
                             allow_biography_corrections=True)
        self.assertEqual(report['unresolved_source'][0]['reason'],'birth_date_conflict')

    def test_historical_identity_does_not_establish_week1_membership(self):
        native=bytes(fixtures.HybridPlanTests().roster())
        rows=self.rows();old={**rows.pop(),'season':'2025'}
        report=resolve_week1(native,native,rows,season_year=2026,historical_identity_rows=[old])
        player=report['source_identities']['test-2']
        self.assertEqual(player['identity_evidence_seasons'],[2025])
        self.assertEqual(player['statuses'],[])
        self.assertEqual(len(report['matched']),2)
        self.assertEqual(report['free_agent_audit'][0]['blocker'],
                         'missing_dated_availability_evidence')
        self.assertFalse(report['free_agent_audit'][0]['availability_verified'])

    def test_cut_status_and_missing_current_roster_are_not_free_agent_authority(self):
        native=bytes(fixtures.HybridPlanTests().roster())
        rows=self.rows();rows[1]['status']='CUT'
        report=resolve_week1(native,native,rows,season_year=2026)
        self.assertEqual(report['free_agent_audit'][0]['blocker'],
                         'missing_dated_availability_evidence')
        self.assertFalse(report['free_agent_pool_verified'])

    def test_college_corroboration_requires_unique_name_college_and_position_profile(self):
        import struct
        native=fixtures.HybridPlanTests().roster()
        source=bytearray(native)
        for data in (native,source):
            at=0xAFA8
            data[at+0x2B]=74;data[at+0x2A]=60
            struct.pack_into('<I',data,0x60,1)
            struct.pack_into('<i',data,0x64,0x75600-0x64+1)
            struct.pack_into('<i',data,at,0x75600-at+1)
            struct.pack_into('<i',data,0x75600,0x76000-0x75600+1)
            data[0x76000:0x76000+34]='Authored College'.encode('utf-16le')+b'\0\0'
        source[0xAFA8+0x1A]=3
        rows=self.rows();rows[0].update(height='72',weight='200',position='QB',college='Authored College')
        before=bytes(source)
        r=resolve_week1(bytes(native),bytes(source),rows,season_year=2026,
                         allow_biography_corrections=True,allow_profile_corroboration=True)
        self.assertEqual(next(x for x in r['matched'] if x['gsis_id']=='test-1')['source_identity_method'],
                         'unique_sourced_name_corroborated_profile')
        self.assertEqual(bytes(source),before)
        rows[0]['college']='Different College'
        r=resolve_week1(bytes(native),bytes(source),rows,season_year=2026,
                         allow_biography_corrections=True,allow_profile_corroboration=True)
        self.assertTrue(any(x['reason']=='birth_date_conflict' for x in r['unresolved_source']))

    def test_jersey_profile_corroboration_is_opt_in_bounded_and_preserves_source(self):
        import struct
        native=fixtures.HybridPlanTests().roster();source=bytearray(native)
        for data in (native,source):
            data[0xAFA8+0x2B]=74;data[0xAFA8+0x2A]=60
            struct.pack_into('<I',data,0xAFA8+0x20,15<<3)
        source[0xAFA8+0x1A]=3
        rows=self.rows();rows[0].update(height='72',weight='200',position='QB',jersey_number='15')
        before=bytes(source)
        def resolve():return resolve_week1(bytes(native),bytes(source),rows,season_year=2026,
            allow_biography_corrections=True,allow_profile_corroboration=True)
        r=resolve();self.assertEqual(len(r['matched']),2);self.assertEqual(bytes(source),before)
        rows[0]['jersey_number']='16'
        self.assertTrue(resolve()['unresolved_source'])
        rows[0]['jersey_number']='15';rows[0]['height']='71'
        self.assertTrue(resolve()['unresolved_source'])

    def test_excluding_corrupt_source_pool_keeps_duplicate_fa_out_of_club_identity(self):
        import struct
        native=bytes(fixtures.HybridPlanTests().roster());source=bytearray(native)
        for field in (0x10,0x14):
            origin=0xAFA8+field;dest=origin+0x54
            target=origin+struct.unpack_from('<i',source,origin)[0]-1
            struct.pack_into('<i',source,dest,target-dest+1)
        r=resolve_week1(native,bytes(source),self.rows(),season_year=2026,
                         include_source_free_agents=False)
        self.assertEqual(len(r['matched']),1);self.assertFalse(r['unresolved_source'])
        self.assertFalse(r['source_free_agents_included'])
        self.assertFalse(r['free_agent_pool_verified'])
