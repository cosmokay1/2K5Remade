from contextlib import closing
from dataclasses import replace
from datetime import date
from fractions import Fraction
import json
from pathlib import Path
import shutil
import sqlite3
import unittest
from franchise.books import ActiveContract
from franchise.cap import Offer,Rejected
from franchise.restructures import PreseasonRestructureScope,EXCLUDED_RESTRUCTURE_TERMS
from franchise.store import FranchiseStore
from tests import test_calendar_release_history as history_fixture


class CalendarRestructureStoreTests(unittest.TestCase):
    def setUp(self):
        fixture=history_fixture.CalendarReleaseHistoryTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.fixture=fixture;self.store=fixture.store;self.path=fixture.path
        fixture.create('a',ActiveContract(Offer('v',(2000000,)*3,3000000,(0,2000000,0)),'synthetic immutable original'))
        fixture.pay('a','base:0',2000000);fixture.anchor(('a',));fixture.roll(('a',),2026)
        ledger=self.store.load_team('a');self.gid=ledger.contract_identity('v').generation_id
        self.inputs=dict(generation_id=self.gid,converted_base=100000,expected_revision=ledger.revision,
            scope=PreseasonRestructureScope(2027,date(2027,6,1),date(2027,9,10),0,True,True,True,
                EXCLUDED_RESTRUCTURE_TERMS,fixture.profile(2027).source,'synthetic guaranteed calendar conversion'),
            access_check=lambda:None)

    def amend(self,**changes):
        return self.store.restructure_calendar_preseason_veteran('a','convert-2027','v',**{**self.inputs,**changes})

    def test_durable_conversion_preserves_birth_cash_indices_and_retry_after_next_year(self):
        before=self.store.load_team('a');original=before.generation_accounting(self.gid)
        result=self.amend()
        self.assertEqual(result['format'],2);self.assertEqual(result['generation_id'],self.gid)
        self.assertEqual(result['league_year'],2027)
        self.assertEqual(result['financial']['charges'],[2950000,3050000])
        self.assertEqual(result['cash']['nominal_total'],9000000);self.assertEqual(result['cash']['paid_total'],5000000)
        restarted=FranchiseStore(self.path);ledger=restarted.load_team('a')
        agreement=ledger.generation_accounting(self.gid)
        self.assertEqual(agreement.original_contract,original.original_contract)
        self.assertEqual(agreement.contract.elapsed_years,1)
        self.assertEqual(agreement.contract.offer.salaries,(2000000,1900000,2000000))
        self.assertEqual(agreement.contract.offer.guaranteed_salaries,(0,1900000,0))
        self.assertEqual(agreement.restructure_calendar_year,2027)
        self.assertEqual(ledger.generation_calendar_view(self.gid).anchor_year,2027)
        raw=self.path.read_bytes();self.assertEqual(self.amend(),result);self.assertEqual(self.path.read_bytes(),raw)
        self.fixture.pay('a','bonus:calendar-restructure:convert-2027',100000)
        self.fixture.pay('a','base:1',1900000);self.fixture.roll(('a',),2027)
        final=FranchiseStore(self.path).load_team('a')
        self.assertEqual(final.active_contract('v').elapsed_years,2)
        self.assertEqual(final.charges,(Fraction(3050000),))
        self.assertEqual(final.generation_accounting(self.gid).original_contract,original.original_contract)
        raw=self.path.read_bytes();self.assertEqual(self.amend(),result);self.assertEqual(self.path.read_bytes(),raw)

    def test_exact_scope_generation_revision_and_final_callbacks_fail_atomically(self):
        before=self.path.read_bytes()
        def reject():raise TimeoutError('synthetic final disconnect')
        def reject_receipt(_):raise ValueError('synthetic receipt too large')
        for changes in ({'generation_id':'foreign'},{'expected_revision':True},{'expected_revision':0},
                        {'scope':replace(self.inputs['scope'],amended_on=date(2026,6,1),first_regular_season_game=date(2026,9,10),league_year=2026)},
                        {'converted_base':True},{'access_check':reject},{'receipt_check':reject_receipt}):
            with self.subTest(changes=changes),self.assertRaises((ValueError,Rejected,TimeoutError)):
                self.amend(**changes)
            self.assertEqual(self.path.read_bytes(),before)
        order=[]
        self.amend(receipt_check=lambda receipt:order.append('receipt'),access_check=lambda:order.append('access'))
        self.assertEqual(order,['receipt','access'])
        raw=self.path.read_bytes()
        with self.assertRaises(TimeoutError):self.amend(access_check=reject)
        self.assertEqual(self.path.read_bytes(),raw)
        for changes in ({'converted_base':99999},{'generation_id':'foreign'},
                        {'scope':replace(self.inputs['scope'],source='different recorded source')}):
            with self.assertRaises(Rejected):self.amend(**changes)
            self.assertEqual(self.path.read_bytes(),raw)
        with self.assertRaises(Rejected):
            self.store.restructure_preseason_veteran('a','ordinary','v',**{k:v for k,v in self.inputs.items() if k!='generation_id'})
        self.assertEqual(self.path.read_bytes(),raw)

    def test_replay_rejects_changed_calendar_original_cash_or_extra_fields(self):
        self.amend()
        for field in ('before_calendar','after_calendar','original_contract','original_cash','cash_type','extra','date'):
            path=self.path.with_name(field+'.sqlite');shutil.copy2(self.path,path)
            with closing(sqlite3.connect(path)) as db:
                row=db.execute("SELECT id,payload FROM events WHERE kind='calendar_restructure'").fetchone()
                payload=json.loads(row[1])
                if field=='before_calendar':payload['before_calendar_posting']['league_year']=2026
                elif field=='after_calendar':payload['calendar_posting']['league_year']=2028
                elif field=='original_contract':payload['original_contract']['elapsed_years']=0
                elif field=='original_cash':payload['original_cash']['paid']=0
                elif field=='cash_type':payload['cash_posting']['revision']=float(payload['cash_posting']['revision'])
                elif field=='extra':payload['unexpected']=True
                else:payload['scope']['amended_on']='20270601'
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),row[0]));db.commit()
            with self.subTest(field=field),self.assertRaises((ValueError,Rejected)):
                FranchiseStore(path).load_team('a')
