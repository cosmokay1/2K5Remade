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
        self.assertEqual(len(performance['missing_named_metrics']), 9)
        self.assertNotEqual(performance['player_id'], saved_player_performance(bindings, payload, 0)['player_id'])

    def test_deleted_unmapped_and_unknown_flags_never_become_named_production(self):
        for word, reason in ((0x90000000 | (1<<23) | (6<<16) | 123, 'deleted'),
                             (0xC0000000 | (1<<23) | (6<<16) | 123, 'unknown_bit30'),
                             (0x80000000 | (1<<23) | (18<<16) | 123, 'unmapped_code'),
                             (0x80000000 | (1<<23) | (6<<16) | 0xFFFF, 'negative_count')):
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

    def test_changed_biography_or_bad_slot_refuses_export(self):
        payload = self.fixture(); bindings = create_bindings(bytes(payload))
        payload[PLAYER_START+4] ^= 1
        with self.assertRaises(ValueError): saved_player_performance(bindings, bytes(payload), 0)
        for slot in (True, -1, 0.0, 999999):
            with self.assertRaises(ValueError): saved_player_performance(bindings, bytes(self.fixture()), slot)
