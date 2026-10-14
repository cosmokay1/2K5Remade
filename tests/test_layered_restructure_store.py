"""Explicit versioned repeated amendments survive payroll, expiry and replay."""
from contextlib import closing
from dataclasses import replace
from datetime import date
from pathlib import Path
import json
import sqlite3
import unittest
from franchise.books import ActiveContract
from franchise.cap import Offer,Rejected
from franchise.restructures import PreseasonRestructureScope,EXCLUDED_RESTRUCTURE_TERMS
from franchise.store import FranchiseStore
from franchise.salary_rules import VeteranMinimumProfile
from tests import test_calendar_release_history


class LayeredRestructureStoreTests(unittest.TestCase):
    def setUp(self):
        fixture=test_calendar_release_history.CalendarReleaseHistoryTests();fixture.setUp()
        self.addCleanup(fixture.doCleanups);self.fixture=fixture;self.store=fixture.store;self.path=fixture.path
        fixture.create('a',ActiveContract(Offer('v',(2000000,)*3,3000000,(0,2000000,2000000)),'synthetic original'))
        fixture.create('b');fixture.pay('a','base:0',2000000);fixture.anchor(('a','b'));fixture.roll(('a','b'),2026)
        ledger=self.store.load_team('a');self.gid=ledger.contract_identity('v').generation_id
        firstscope=PreseasonRestructureScope(2027,date(2027,6,1),date(2027,9,10),0,True,True,True,
            EXCLUDED_RESTRUCTURE_TERMS,fixture.profile(2027).source,'synthetic first conversion')
        self.first_inputs=dict(generation_id=self.gid,scope=firstscope,converted_base=100000,
            expected_revision=ledger.revision,access_check=lambda:None)
        self.first=self.store.restructure_calendar_preseason_veteran('a','first-2027','v',**self.first_inputs)
        fixture.pay('a','bonus:calendar-restructure:first-2027',100000);fixture.pay('a','base:1',1900000)
        fixture.roll(('a','b'),2027)
        self.inputs=dict(generation_id=self.gid,scope=replace(firstscope,league_year=2028,
            amended_on=date(2028,6,1),first_regular_season_game=date(2028,9,10),source='synthetic second conversion',
            minimum_source=fixture.profile(2028).source),converted_base=200000,
            expected_revision=self.store.load_team('a').revision,access_check=lambda:None)

    def amend(self,**changes):
        return self.store.restructure_calendar_layered_preseason_veteran('a','second-2028','v',**{**self.inputs,**changes})

    def expire(self):
        self.fixture.pay('a','bonus:calendar-layered-restructure:second-2028',200000)
        self.fixture.pay('a','base:2',1800000)
        teams={team:dict(expected_revision=self.store.load_team(team).revision,next_cap=20000000,
            next_cap_source='synthetic cap',roster_reserve=0,reserve_source='synthetic reserve',
            next_minimum_profile=VeteranMinimumProfile(2029,(('v',(7,7),('active_inactive',)*2),)).to_dict(),expired_generation_ids=[self.gid] if team=='a' else [],
            exclusions=sorted(FranchiseStore.YEAR_TRANSITION_EXCLUSIONS),source='synthetic complete closing') for team in ('a','b')}
        return self.store.advance_league_year(request_id='expiry-2028',from_year=2028,to_year=2029,
            source='synthetic settled common closing',teams=teams)

    def test_history_cash_expiry_mixed_team_roll_and_old_receipts_survive_restart(self):
        result=self.amend();self.assertEqual(result['format'],3)
        self.assertEqual(result['amendment_history']['format'],1)
        self.assertEqual(len(result['amendment_history']['prior_restructures']),1)
        ledger=FranchiseStore(self.path).load_team('a');agreement=ledger.generation_accounting(self.gid)
        self.assertEqual(agreement.original_contract.elapsed_years,0)
        self.assertEqual(agreement.contract.elapsed_years,2)
        self.assertEqual(len(agreement.contract.bonus_layers),2)
        self.assertEqual(ledger.cash_snapshot()['nominal_total'],9000000)
        self.assertEqual(ledger.cash_snapshot()['paid_total'],7000000)
        self.assertEqual(ledger.generation_snapshot(history_format=2)['format'],2)
        with self.assertRaises(Rejected):ledger.generation_snapshot()
        self.expire();self.store=FranchiseStore(self.path);self.fixture.store=self.store
        final=self.store.load_team('a');self.assertEqual(final.generation_accounting(self.gid),agreement)
        self.assertTrue(final.generation_calendar_view(self.gid).authoritative_expired)
        self.assertEqual(final.cash_snapshot()['unpaid_total'],0)
        before=self.path.read_bytes();self.assertEqual(self.amend(),result)
        self.assertEqual(self.store.restructure_calendar_preseason_veteran('a','first-2027','v',**self.first_inputs),self.first)
        self.assertEqual(self.path.read_bytes(),before)
        with closing(sqlite3.connect(self.path)) as db:
            payments=[json.loads(row[0]) for row in db.execute("SELECT payload FROM events WHERE team_id='a' AND kind='cash_payment'")]
            self.assertEqual([p['format'] for p in payments if 'format' in p],[2,2])
            rows=db.execute("SELECT team_id,payload FROM events WHERE request_key='year:expiry-2028'").fetchall()
            for team,serialized in rows:
                payload=json.loads(serialized)
                if team=='a':self.assertEqual(payload['generation_format'],2)
                else:self.assertNotIn('generation_format',payload)

    def test_invalid_retry_and_final_callbacks_are_atomic(self):
        def denied():raise TimeoutError('synthetic disconnect')
        def bad_receipt(_):raise ValueError('synthetic unsupported native format')
        before=self.path.read_bytes()
        for changes in ({'generation_id':'foreign'},{'expected_revision':True},{'access_check':denied},{'receipt_check':bad_receipt}):
            with self.subTest(changes=changes),self.assertRaises((Rejected,ValueError,TimeoutError)):self.amend(**changes)
            self.assertEqual(self.path.read_bytes(),before)
        result=self.amend();before=self.path.read_bytes()
        with self.assertRaises(Rejected):self.amend(converted_base=1)
        self.assertEqual(self.path.read_bytes(),before)
        with self.assertRaises((Rejected,ValueError)):
            self.store.restructure_calendar_preseason_veteran('a','wrong-first','v',**self.inputs)
        self.assertEqual(self.path.read_bytes(),before)

    def test_history_and_payment_downgrades_reject_replay(self):
        self.amend();self.fixture.pay('a','bonus:calendar-layered-restructure:second-2028',200000)
        original=self.path.read_bytes()
        for scenario in ('history','event_format','payment_format','missing_payment_post'):
            path=self.path.with_name(scenario+'.sqlite');path.write_bytes(original)
            with closing(sqlite3.connect(path)) as db:
                kind='calendar_layered_restructure' if scenario in ('history','event_format') else 'cash_payment'
                event_id,serialized=db.execute('SELECT id,payload FROM events WHERE kind=? ORDER BY id DESC LIMIT 1',(kind,)).fetchone()
                payload=json.loads(serialized)
                if scenario=='history':payload['generation_posting']['agreements'][0]['amendment_history']['prior_restructures']=[]
                elif scenario=='event_format':payload['format']=True
                elif scenario=='payment_format':payload['format']=1
                else:payload.pop('generation_posting')
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),event_id));db.commit()
            with self.subTest(scenario=scenario),self.assertRaises((ValueError,Rejected)):
                FranchiseStore(path).load_team('a')

    def test_second_event_insert_failure_rolls_back_all_books(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TRIGGER reject_layered BEFORE INSERT ON events WHEN NEW.kind='calendar_layered_restructure' BEGIN SELECT RAISE(ABORT,'synthetic reject'); END")
            db.commit()
        before=self.path.read_bytes()
        with self.assertRaises(sqlite3.IntegrityError):self.amend()
        self.assertEqual(self.path.read_bytes(),before)

    def test_year_history_wrapper_cannot_drop_or_retype_chain(self):
        self.amend();self.expire();original=self.path.read_bytes()
        for scenario in ('drop','bool','history'):
            path=self.path.with_name('year-'+scenario+'.sqlite');path.write_bytes(original)
            with closing(sqlite3.connect(path)) as db:
                event_id,serialized=db.execute("SELECT id,payload FROM events WHERE team_id='a' AND request_key='year:expiry-2028'").fetchone()
                payload=json.loads(serialized)
                if scenario=='drop':
                    for field in ('generation_format','before_generation_posting','generation_posting'):payload.pop(field)
                elif scenario=='bool':payload['generation_format']=True
                else:payload['generation_posting']['agreements'][0]['amendment_history']['prior_restructures']=[]
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),event_id));db.commit()
            with self.subTest(scenario=scenario),self.assertRaises((ValueError,Rejected)):
                FranchiseStore(path).load_team('a')
