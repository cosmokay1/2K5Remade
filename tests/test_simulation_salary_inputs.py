import contextlib
import hashlib
import io
from pathlib import Path
import struct
import tempfile
import unittest

from franchise.books import OpeningBooks
from franchise.cap import Ledger
from franchise.store import FranchiseStore
from tools import franchise_snapshot_bindings as bindings_tool
from tools.export_simulation_salary_inputs import salary_inputs
from tools.import_salary_classification import import_inputs, main
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE
import test_softdrink_snapshot as snapshots


class SimulationSalaryInputTests(unittest.TestCase):
    def setUp(self):
        fixture=snapshots.SoftdrinkSnapshotTests();fixture.setUp()
        self.payload=bytearray(fixture.payload)
        for slot,period in ((0,1),(1,9)):
            struct.pack_into('<I',self.payload,PLAYER_START+slot*PLAYER_STRIDE+0x24,period<<8)
        self.payload=bytes(self.payload)
        self.bindings=bindings_tool.create_bindings(self.payload,seed='retained',game_context={
            'season_year':2026,'season_index':0,'money_scale':4,'league_cap_raw':75300})
        self.members=bindings_tool.resolve_bindings(self.bindings,self.payload)

    def test_rookie_and_veteran_projection_are_explicit_and_rating_independent(self):
        batch,report=salary_inputs(self.bindings,self.payload,expected_revisions={'a':0},years=5)
        player=self.members[1]['player_id']
        self.assertEqual(batch['profile']['players'],[{'player_id':player,'credited_seasons':[8,9,10,11,12],
            'roster_categories':['active_inactive']*5}])
        self.assertEqual(report['rookies_requiring_separate_rules'],[self.members[0]['player_id']])
        self.assertFalse(report['actual_nfl_service_verified'])
        ratings_changed=bytearray(self.payload)
        ratings_changed[PLAYER_START+PLAYER_STRIDE+0x30]^=0x7f
        same_floors,_=salary_inputs(self.bindings,bytes(ratings_changed),expected_revisions={'a':0},years=5)
        self.assertEqual(same_floors['profile'],batch['profile'])
        with self.assertRaises(ValueError):salary_inputs(self.bindings,self.payload,expected_revisions={'a':0},years=6)

    def test_preview_is_read_only_and_import_preserves_actors(self):
        with tempfile.TemporaryDirectory() as directory:
            database=Path(directory)/'state.sqlite';store=FranchiseStore(database)
            ids=frozenset(p['player_id'] for p in self.members.values())
            store.create_franchise({'a':Ledger.from_opening(OpeningBooks(),cap=301200000,roster_reserve=0,
                max_bonus_years=5,veteran_minimums={},observed_player_ids=ids,observed_player_source='fixture')},seed='retained')
            batch,_=salary_inputs(self.bindings,self.payload,expected_revisions={'a':0},years=5)
            digest=lambda:hashlib.sha256(database.read_bytes()).hexdigest()
            before=digest();actors=store.player_context('a',self.members[1]['player_id'])
            result=import_inputs(database,batch)
            self.assertFalse(result['applied']);self.assertEqual(before,digest())
            self.assertTrue(import_inputs(database,batch,apply=True)['applied'])
            self.assertEqual(actors['personality'],FranchiseStore(database).player_context('a',self.members[1]['player_id'])['personality'])
            self.assertTrue(import_inputs(database,batch,apply=True)['applied'])

    def test_cli_duplicate_or_unknown_input_does_not_create_or_mutate_a_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'input.json';missing=root/'missing.sqlite'
            source.write_text('{"format":1,"format":1}')
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                main([str(missing),str(source),'--apply'])
            self.assertFalse(missing.exists())

    def test_zero_period_stays_unknown_instead_of_becoming_a_rookie_or_veteran(self):
        payload=bytearray(self.payload);struct.pack_into('<I',payload,PLAYER_START+PLAYER_STRIDE+0x24,0)
        batch,report=salary_inputs(self.bindings,bytes(payload),expected_revisions={'a':0},years=5)
        self.assertEqual(batch['profile']['players'],[])
        self.assertEqual(report['unknown_season_inputs'],[self.members[1]['player_id']])

    def test_original_calendar_uses_approved_historical_reference_without_rewriting_save(self):
        payload=bytearray(self.payload);payload[0x917EF]=4
        bindings=bindings_tool.create_bindings(bytes(payload),seed='retained',game_context={
            'season_year':2004,'season_index':0,'money_scale':1,'league_cap_raw':75300})
        before=bytes(payload)
        batch,report=salary_inputs(bindings,before,expected_revisions={'a':0},years=5)
        from franchise.salary_rules import VeteranMinimumProfile
        floors=VeteranMinimumProfile.from_dict(batch['profile']).floors()
        self.assertEqual(list(floors.values())[0][0],325000)
        self.assertEqual(report['game_year'],2004)
        self.assertEqual(report['salary_rule_start_year'],2026)
        self.assertEqual(bytes(payload),before)
