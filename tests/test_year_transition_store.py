from contextlib import closing
from pathlib import Path
import copy
import json
import sqlite3
import tempfile
import unittest
from franchise.books import ActiveContract,OpeningBooks,ChargeRecord
from franchise.cap import Ledger,Offer,Rejected
from franchise.cash import CashObligation
from franchise.salary_rules import VeteranMinimumProfile
from franchise.store import FranchiseStore


class StoredYearTransitionTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'league.sqlite';self.store=FranchiseStore(self.path)
        for team,term in (('a',3),('b',1)):
            contract=ActiveContract(Offer(team,(2000000,)*term,3000000),'synthetic original')
            profile=VeteranMinimumProfile(2026,((team,(7,)*term,('active_inactive',)*term),))
            self.store.create_team(team,Ledger.from_opening(OpeningBooks(contracts=(contract,),
                retained=(ChargeRecord('debt:'+team,(7,11,13),'synthetic retained schedule'),)),
                cap=10000000,roster_reserve=0,max_bonus_years=5,veteran_minimums=profile.floors(),veteran_minimum_profile=profile))
            self.store.initialize_cash(team,(CashObligation('contract:'+team,team,contract.nominal_cash,5000000,
                'synthetic payroll',(('signing_bonus',3000000),('base:0',2000000))),),source='synthetic complete cash')
        self.store.anchor_calendar(request_id='initial',league_year=2026,source='synthetic calendar',expected_revisions={'a':1,'b':1})
        self.store.migrate_generations(self.path)
        self.inputs=dict(request_id='roll-2027',from_year=2026,to_year=2027,source='synthetic declared league close',teams={})
        for team in ('a','b'):
            profile=VeteranMinimumProfile(2027,((team,(7,7,7),('active_inactive',)*3),))
            self.inputs['teams'][team]=dict(expected_revision=2,next_cap=9000000,next_cap_source='synthetic next cap',
                roster_reserve=500,reserve_source='synthetic reserve',next_minimum_profile=profile.to_dict(),
                expired_generation_ids=[self.store.load_team(team).contract_identity(team).generation_id] if team=='b' else [],
                exclusions=sorted(FranchiseStore.YEAR_TRANSITION_EXCLUSIONS),source='synthetic explicit eligibility and closing exclusions')

    def test_atomic_two_seasons_preserve_cash_archives_expiry_and_retries(self):
        before={team:self.store.load_team(team).cash_snapshot() for team in ('a','b')}
        receipt=self.store.advance_league_year(**self.inputs)
        restarted=FranchiseStore(self.path)
        self.assertEqual(restarted.league_calendar()['league_year'],2027)
        self.assertEqual(restarted.load_team('a').active_contract('a').elapsed_years,1)
        self.assertEqual(restarted.load_team('a').charges,(3000011,3000013))
        self.assertEqual(restarted.load_team('b').financial_snapshot()['signed_players'],[])
        self.assertEqual(restarted.load_team('b').charges,(11,13))
        a_id=restarted.load_team('a').contract_identity('a').generation_id
        b_id=restarted.load_team('b').contract_identity('b').generation_id
        current=restarted.calendar_contract_context('a',a_id)
        self.assertEqual(current['calendar_accounting']['current_contract']['elapsed_years'],1)
        self.assertEqual(current['economic_archive']['contract']['elapsed_years'],0)
        expired=restarted.calendar_contract_context('b',b_id)
        self.assertEqual(expired['calendar_accounting']['status'],'expired')
        self.assertFalse(expired['calendar_accounting']['ownership_current'])
        self.assertIsNone(expired['calendar_accounting']['current_contract'])
        with self.assertRaises(Rejected):restarted.contract_context('b',b_id)
        with self.assertRaises(Rejected):restarted.contract_generations('b')
        for team in ('a','b'):self.assertEqual(restarted.load_team(team).cash_snapshot(),before[team])
        raw=self.path.read_bytes()
        self.assertEqual(restarted.advance_league_year(**self.inputs),receipt)
        self.assertEqual(self.path.read_bytes(),raw)
        self.assertEqual(restarted.calendar_projection('a',target_year=2028)['modeled_remaining_charges'],[3000013])
        self.assertEqual(restarted.calendar_closing_state('a')['agreements'][0]['outgoing_year_original_index'],1)
        restarted.record_payment('a','pay-2027','contract:a',2000000,expected_cash_revision=0,
            source='synthetic actual allocated payroll',payment_reference='payroll-2027',component='base:1')
        next_inputs=copy.deepcopy(self.inputs)
        next_inputs.update(request_id='roll-2028',from_year=2027,to_year=2028)
        for team in ('a','b'):
            item=next_inputs['teams'][team];item['expected_revision']=restarted.load_team(team).revision
            item['expired_generation_ids']=[]
            item['next_minimum_profile']=VeteranMinimumProfile(2028,((team,(7,7),('active_inactive',)*2),)).to_dict()
        restarted.advance_league_year(**next_inputs)
        final=FranchiseStore(self.path)
        self.assertEqual(final.league_calendar()['league_year'],2028)
        self.assertEqual(final.load_team('a').active_contract('a').elapsed_years,2)
        self.assertEqual(final.load_team('a').cash_snapshot()['unpaid_total'],2000000)
        self.assertEqual(final.load_team('b').cash_snapshot(),before['b'])
        self.assertEqual(final.advance_league_year(**self.inputs),receipt)

    def test_stale_or_incomplete_closing_rolls_back_all_teams(self):
        raw=self.path.read_bytes()
        for change in ('stale','missing','eligibility','exclusions'):
            inputs=copy.deepcopy(self.inputs)
            if change=='stale':inputs['teams']['b']['expected_revision']=1
            elif change=='missing':del inputs['teams']['b']
            elif change=='eligibility':inputs['teams']['b']['expired_generation_ids']=[]
            else:inputs['teams']['b']['exclusions']=[]
            with self.subTest(change=change),self.assertRaises((Rejected,ValueError)):
                self.store.advance_league_year(**inputs)
            self.assertEqual(self.path.read_bytes(),raw)
            self.assertEqual(self.store.league_calendar()['league_year'],2026)

    def test_partial_transition_and_posting_type_tamper_reject_replay(self):
        self.store.advance_league_year(**self.inputs)
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute("SELECT id,payload FROM events WHERE team_id='b' AND kind='year_transition'").fetchone()
            payload=json.loads(row[1]);payload['posting']['revision']=3.0
            db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),row[0]));db.commit()
        with self.assertRaisesRegex(ValueError,'posting'):self.store.load_team('a')

    def test_missing_peer_transition_refuses_all_reads(self):
        self.store.advance_league_year(**self.inputs)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DELETE FROM events WHERE team_id='b' AND kind='year_transition'")
            db.commit()
        with self.assertRaisesRegex(ValueError,'Partial league'):
            self.store.load_team('a')
