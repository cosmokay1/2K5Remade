import json
import struct
import unittest

import test_inspect_player_history as history_fixtures
from franchise.cap import Ledger, Offer
from franchise.negotiation import Negotiation
from tools.franchise_snapshot_bindings import create_bindings
from tools.inspect_franchise_save import PLAYER_START
from tools.export_player_performance import saved_player_performance


class SavedPerformanceTests(unittest.TestCase):
    def fixture(self):
        payload = history_fixtures.InspectPlayerHistoryTests().fixture()
        payload[0x2E0:0x2E4] = b'ROST'; payload[0x30C:0x310] = b'ROST'
        struct.pack_into('<I', payload, 0x2E4, 0x91020)
        payload[0x91320] = 2; payload[0x91323] = 32; payload[0x91326] = 22
        struct.pack_into('<I', payload, PLAYER_START+0x24, 7 << 8)
        struct.pack_into('<II', payload, 0x41D54, (1 << 23) | (6 << 16) | 478,
                         0x80000000 | (1 << 23) | (8 << 16) | 3216)
        return payload

    def test_pinned_history_reaches_actual_negotiation_without_ratings_or_aggregation(self):
        payload = bytes(self.fixture()); bindings = create_bindings(payload, seed='authored')
        performance = saved_player_performance(bindings, payload, 0)
        player = performance['player_id']
        ledger = Ledger(cap=100, existing_charges=(0,), roster_reserve=0,
            max_bonus_years=5, veteran_minimums={player: (1,)})
        session = Negotiation(ledger, player_id=player, personality={}, relationships={},
            performance=performance, access_check=lambda: None, proposal_only=True)
        seen = []
        def provider(context):
            seen.append(context)
            return json.dumps(dict(action='reject', reason='Historical evidence only', salaries=None, signing_bonus=None))
        session.respond('history', Offer(player, (10,), 0), provider, expected_revision=0)
        self.assertEqual(seen[0]['performance'], performance)
        self.assertEqual([row['value'] for row in performance['saved_history']], [478, 3216])
        self.assertTrue(all(row['candidate_calendar_year']==2020 for row in performance['saved_history']))
        self.assertIn('completions', performance['missing_named_metrics'])
        self.assertEqual(ledger.revision, 0)
        self.assertEqual(bytes(self.fixture()), payload)

    def test_receiving_seasons_preserve_exact_signed_yards_and_no_missing_zeros(self):
        payload=self.fixture();bank=0x41D54
        values=((1,12,70),(1,13,900),(1,14,4),(2,12,2),(2,13,-3))
        struct.pack_into('<I',payload,0x360,len(values))
        for i,(period,code,value) in enumerate(values):
            word=(period<<23)|(code<<16)|(value&0xFFFF)
            if i==len(values)-1:word|=0x80000000
            struct.pack_into('<I',payload,bank+4*i,word)
        before=bytes(payload);performance=saved_player_performance(create_bindings(before),before,0)
        rows=performance['saved_history']
        self.assertEqual([(r['metric'],r['value'],r['period_code_raw']) for r in rows],
            [('receptions',70,1),('receiving_yards',900,1),('receiving_touchdowns',4,1),
             ('receptions',2,2),('receiving_yards',-3,2)])
        self.assertEqual(len([r for r in rows if r['metric']=='receiving_touchdowns']),1)
        self.assertEqual(bytes(payload),before)
        self.assertNotIn('targets',{r['metric'] for r in rows})

    def test_franchise_calendar_is_separate_from_raw_title_year(self):
        from tools.franchise_game_context import raw_context
        payload=self.fixture()
        payload[0x917EF]+=22  # Explicit schedule epoch differs from raw scheduler.
        payload=bytes(payload)
        context=raw_context(payload)
        context['season_year']+=22
        bindings=create_bindings(payload,game_context=context)
        performance=saved_player_performance(bindings,payload,0)
        self.assertEqual(performance['franchise_season_year'],context['season_year'])
        self.assertEqual(performance['saved_display_year'],context['season_year']-22)
        self.assertEqual(performance['saved_history'][0]['candidate_calendar_year'],2020)

    def test_physical_profile_uses_saved_values_and_season_age_without_injury_rating(self):
        payload=self.fixture();record=PLAYER_START
        payload[record+0x2A]=75;payload[record+0x2B]=74
        payload[record+0x19]=5<<4;payload[record+0x1A]=(3<<5)|13;payload[record+0x1B]=0
        payload=bytes(payload)
        profile=saved_player_performance(create_bindings(payload),payload,0)['player_profile']
        self.assertEqual(profile,dict(height_inches=74,weight_pounds=225,age_years=23,injury_tendency=None))
        empty=self.fixture();empty[record+0x2B]=0
        unknown=saved_player_performance(create_bindings(bytes(empty)),bytes(empty),0)['player_profile']
        self.assertIsNone(unknown['height_inches']);self.assertIsNone(unknown['age_years'])

    def test_foreign_player_performance_cannot_enter_model_context(self):
        payload = bytes(self.fixture()); bindings = create_bindings(payload)
        performance = saved_player_performance(bindings, payload, 0)
        ledger = Ledger(cap=100, existing_charges=(0,), roster_reserve=0,
            max_bonus_years=5, veteran_minimums={'other': (1,)})
        with self.assertRaisesRegex(ValueError, 'another player'):
            Negotiation(ledger, player_id='other', personality={}, relationships={},
                performance=performance, access_check=lambda: None)

    def test_missing_history_is_unknown_and_keeps_pinned_identity(self):
        payload = bytes(self.fixture()); bindings = create_bindings(payload)
        performance = saved_player_performance(bindings, payload, 1)
        self.assertFalse(performance['history_present'])
        self.assertEqual(performance['saved_history'], [])
        self.assertEqual(len(performance['missing_named_metrics']), 13)
        self.assertNotEqual(performance['player_id'], saved_player_performance(bindings, payload, 0)['player_id'])

    def test_deleted_unmapped_and_unknown_flags_never_become_named_production(self):
        for word, reason in ((0x90000000 | (1<<23) | (6<<16) | 123, 'deleted'),
                             (0xC0000000 | (1<<23) | (6<<16) | 123, 'unknown_bit30'),
                             (0x80000000 | (1<<23) | (18<<16) | 123, 'unmapped_code'),
                             (0x80000000 | (1<<23) | (6<<16) | 0xFFFF, 'negative_count'),
                             (0x80000000 | (1<<23) | (19<<16) | 0xFFFF, 'negative_count')):
            payload = self.fixture(); struct.pack_into('<I', payload, 0x41D54, word)
            bindings = create_bindings(bytes(payload))
            performance = saved_player_performance(bindings, bytes(payload), 0)
            self.assertEqual(performance['saved_history'], [])
            self.assertEqual(performance['excluded_entries'][reason], 1)

    def test_signed_yards_raw_modes_and_unknown_years_remain_explicit(self):
        payload = self.fixture()
        struct.pack_into('<I', payload, PLAYER_START+0x24, 0)
        struct.pack_into('<I', payload, 0x41D54, 0xA0000000 | (1<<23) | (8<<16) | 0xFFFE)
        bindings = create_bindings(bytes(payload))
        performance = saved_player_performance(bindings, bytes(payload), 0)
        self.assertEqual(performance['saved_history'][0]['value'], -2)
        self.assertEqual(performance['saved_history'][0]['mode_code_raw'], 1)
        self.assertIsNone(performance['saved_history'][0]['candidate_calendar_year'])
        self.assertNotIn('observed_efficiency', performance)

    def test_sacks_are_not_doubled_or_rounded_into_whole_counts(self):
        payload = self.fixture()
        struct.pack_into('<I', payload, 0x41D54, 0x80000000 | (1<<23) | (19<<16) | 5)
        bindings = create_bindings(bytes(payload))
        performance = saved_player_performance(bindings, bytes(payload), 0)
        row = performance['saved_history'][0]
        self.assertEqual((row['metric'], row['unit'], row['value']), ('sacks', 'sacks', 2.5))
        self.assertEqual(row['raw_half_sack_units'], 5)
        self.assertIn('inferred', row['mapping_scope'])
        self.assertNotIn('sacks', performance['missing_named_metrics'])
        self.assertIn('pressures', performance['unmapped_requested_metrics'])

    def test_changed_biography_or_bad_slot_refuses_export(self):
        payload = self.fixture(); bindings = create_bindings(bytes(payload))
        payload[PLAYER_START+4] ^= 1
        with self.assertRaises(ValueError): saved_player_performance(bindings, bytes(payload), 0)
        for slot in (True, -1, 0.0, 999999):
            with self.assertRaises(ValueError): saved_player_performance(bindings, bytes(self.fixture()), slot)
