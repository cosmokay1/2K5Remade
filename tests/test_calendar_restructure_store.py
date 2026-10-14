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

    def test_later_release_retains_both_bonus_layers_paid_indices_and_historical_amendment(self):
        from franchise.guarantees import DiscountProfile
        from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
        amendment_receipt=self.amend()
        amended=self.store.load_team('a').generation_accounting(self.gid)
        self.fixture.pay('a','bonus:calendar-restructure:convert-2027',100000)
        self.fixture.pay('a','base:1',1900000)
        self.fixture.roll(('a',),2027)
        ledger=self.store.load_team('a')
        cash_before=ledger.generation_cash(self.gid)
        release_inputs=dict(generation_id=self.gid,
            scope=PreseasonReleaseScope(2028,date(2028,5,1),date(2028,9,10),EXCLUDED_LIABILITIES,
                True,True,0,'synthetic healthy final-year release'),
            discount=DiscountProfile(2028,Fraction(0),'synthetic zero rate'),payment_year_offsets=(0,),
            expected_revision=ledger.revision,access_check=lambda:None)
        released_receipt=self.store.release_calendar_preseason_veteran('a','release-2028','v',**release_inputs)
        self.store=FranchiseStore(self.path);ledger=self.store.load_team('a')
        archived=ledger.generation_accounting(self.gid)
        self.assertEqual(archived.original_contract,amended.original_contract)
        self.assertEqual(archived.contract,amended.contract)
        self.assertEqual(archived.restructure,amended.restructure)
        self.assertEqual(archived.restructure_calendar_year,2027)
        self.assertEqual(archived.release_calendar_year,2028)
        self.assertEqual(archived.contract.elapsed_years,1)
        self.assertEqual(archived.release.original_contract.elapsed_years,2)
        self.assertEqual(archived.release.original_contract.bonus_layers,amended.contract.bonus_layers)
        # Original bonus has one $1m year left; the conversion has one $50k
        # year left. The unpaid, unprotected final $2m salary is cancelled.
        self.assertEqual(ledger.charges,(Fraction(1050000),))
        self.assertEqual(archived.release.retained[0].annual_charges,(Fraction(1050000),))
        self.assertEqual(archived.release.cancelled_unearned_base,2000000)
        cash=ledger.generation_cash(self.gid)
        self.assertEqual((cash.amount,cash.paid),(7000000,7000000))
        self.assertEqual(cash.paid_components,cash_before.paid_components)
        self.assertEqual(dict(cash.paid_components)['base:0'],2000000)
        self.assertEqual(dict(cash.paid_components)['base:1'],1900000)
        self.assertNotIn('base:2',dict(cash.paid_components))
        self.assertEqual(archived.payment_ceilings()['base:1'],1900000)
        self.assertEqual(archived.payment_ceilings()['base:2'],0)
        self.assertEqual(ledger.financial_snapshot()['signed_players'],[])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertIsNone(db.execute("SELECT 1 FROM ownership WHERE player_id='v'").fetchone())
        # The next league close slices cap debt without rewriting either plan
        # or its original base-payment indices.
        from franchise.salary_rules import VeteranMinimumProfile
        self.store.advance_league_year(request_id='roll-2028',from_year=2028,to_year=2029,
            source='synthetic common reconciled closing',teams={'a':dict(expected_revision=ledger.revision,
                next_cap=20000000,next_cap_source='synthetic next budget',roster_reserve=0,
                reserve_source='synthetic reserve',next_minimum_profile=VeteranMinimumProfile(2029,
                    (('v',(7,7),('active_inactive','active_inactive')),)).to_dict(),
                expired_generation_ids=[],exclusions=sorted(FranchiseStore.YEAR_TRANSITION_EXCLUSIONS),
                source='synthetic reconciled closing')})
        final=FranchiseStore(self.path).load_team('a')
        self.assertEqual(final.charges,(Fraction(0),))
        self.assertEqual(final.generation_accounting(self.gid),archived)
        self.assertEqual(final.generation_cash(self.gid),cash)
        self.assertEqual(final.generation_calendar_view(self.gid).annual_charges(),())
        raw=self.path.read_bytes()
        self.assertEqual(self.amend(),amendment_receipt)
        self.assertEqual(self.store.release_calendar_preseason_veteran('a','release-2028','v',**release_inputs),released_receipt)
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
