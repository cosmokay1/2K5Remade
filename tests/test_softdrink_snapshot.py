"""Authored fixtures exercise the explicit pinned-pack intake, never game assets."""
import copy
import hashlib
import json
import struct
import unittest
import tempfile
from pathlib import Path

from franchise.books import OpeningBooks
from franchise.cap import Ledger
from franchise.store import FranchiseStore
from tools.inspect_franchise_calendar import inspect_calendar
from tools.reconcile_signing_context import reconcile_signing_context
from unittest.mock import patch

import test_legacy_contracts as fixtures
from tools import franchise_snapshot_bindings as bindings_tool
from tools.export_legacy_contracts import legacy_contracts


class SoftdrinkSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.xbe=b'authored executable hash fixture; not an Xbox asset'
        self.pin=patch.object(bindings_tool,'SOFTDRINK_XBE_SHA256',hashlib.sha256(self.xbe).hexdigest())
        self.pin.start();self.addCleanup(self.pin.stop)
        self.payload=fixtures.LegacyContractsTests().fixture()
        self.payload[:4]=b'\x01\0\0\0'
        self.payload[0x91326]=0
        struct.pack_into('<i',self.payload,0x91320+0x83DC+0x15D0,75300)

    def create(self):
        return bindings_tool.create_bindings(bytes(self.payload),seed='authored',game_xbe=self.xbe)

    def test_explicit_pack_identity_and_export_preserve_scaled_schedules(self):
        before=bytes(self.payload);bindings=self.create()
        restored=json.loads(json.dumps(bindings))
        self.assertEqual(restored['baseline_year'],2026)
        members=bindings_tool.resolve_bindings(restored,before)
        self.assertEqual(len(members),2)
        self.assertEqual(bindings_tool.initial_profiles(bindings,before),
                         bindings_tool.initial_profiles(restored,before))
        records=legacy_contracts(restored,before)
        self.assertEqual(records['49ers'][0].charges(),(19064000,14092000))
        self.assertEqual(records['49ers'][0].game_dollar_scale,4)
        self.assertEqual(records['49ers'][0].player_id,members[0]['player_id'])
        self.assertEqual(bytes(self.payload),before)

    def test_scaled_checkpoint_reaches_persisted_context_without_authorizing_writes(self):
        payload=bytes(self.payload);bindings=self.create()
        members=bindings_tool.resolve_bindings(bindings,payload)
        records=legacy_contracts(bindings,payload)
        calendar=inspect_calendar(payload)
        # The native read-only probe reports retail scheduler coordinates.
        # Profile-based logical season must not rewrite this live evidence.
        observation={'biography':{'source_slot':1,'first_name':'Authored',
            'last_name':'Freeagent','pbp_photo_raw':'00000000','dob_region_raw':'000000'},
            'team':{'table_index':0,'table_mode':2,'payroll_raw':4766,
                    'league_cap_raw':75300,'team_flag_raw':0,'first_year_accumulator_raw':0},
            'calendar':{k:calendar[k] for k in ('season_index','display_year','phase_01_raw',
                'phase_02_raw','step_04_raw','step_05_raw','counter_08_raw')}}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'state.sqlite'
            store=FranchiseStore(path)
            store.create_franchise({'49ers':Ledger.from_opening(
                OpeningBooks(legacy_contracts=records['49ers']),cap=301200000,
                roster_reserve=0,max_bonus_years=5,veteran_minimums={},
                observed_player_ids=frozenset(p['player_id'] for p in members.values()),
                observed_player_source='authored pinned snapshot')},seed=bindings['personality_seed'])
            before=store.load_team('49ers').financial_snapshot()
            result=reconcile_signing_context(bindings,payload,observation,
                FranchiseStore(path),expected_revision=0)
            self.assertEqual(result['player_id'],members[1]['player_id'])
            self.assertTrue(result['player_context']['initialized'])
            self.assertFalse(result['ai_authorized']);self.assertFalse(result['write_authorized'])
            self.assertEqual(store.load_team('49ers').financial_snapshot(),before)
            observation['team']['payroll_raw']*=4
            with self.assertRaises(ValueError):
                reconcile_signing_context(bindings,payload,observation,store,expected_revision=0)

    def test_no_implicit_pack_guessing_or_unknown_executable(self):
        with self.assertRaises(ValueError):bindings_tool.create_bindings(bytes(self.payload))
        for xbe in (b'unknown',bytearray(self.xbe),'not bytes'):
            with self.subTest(xbe=type(xbe)),self.assertRaises(ValueError):
                bindings_tool.create_bindings(bytes(self.payload),game_xbe=xbe)

    def test_opening_profile_rejects_season_cap_payroll_and_year_drift(self):
        bindings=self.create()
        for case in range(4):
            payload=bytearray(self.payload)
            if case==0:payload[0x91326]=1
            if case==1:payload[0x917EF]=27
            if case==2:struct.pack_into('<i',payload,0x91320+0x83DC+0x15D0,80500)
            if case==3:struct.pack_into('<I',payload,0x44A8+0x124,4765)
            with self.subTest(case=case),self.assertRaises(ValueError):
                bindings_tool.resolve_bindings(bindings,bytes(payload))

    def test_profile_tampering_rejects(self):
        bindings=self.create()
        for profile in (None,{},'softdrink',{'id':bindings_tool.SOFTDRINK_PROFILE,'xbe_sha256':'0'*64},
                        {**bindings['game_profile'],'money_scale':1}):
            changed=copy.deepcopy(bindings);changed['game_profile']=profile
            with self.subTest(profile=profile),self.assertRaises(ValueError):
                bindings_tool.resolve_bindings(changed,bytes(self.payload))
