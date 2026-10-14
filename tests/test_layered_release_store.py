"""History-aware releases retain all amendment plans and unpaid liabilities."""
from contextlib import closing
from dataclasses import replace
from datetime import date
from fractions import Fraction
import json
import sqlite3
import unittest
from franchise.cap import Rejected
from franchise.cap import Offer
from franchise.books import ActiveContract
from franchise.guarantees import DiscountProfile
from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
from franchise.salary_rules import VeteranMinimumProfile
from franchise.store import FranchiseStore
from tests import test_layered_restructure_store
from tests import test_calendar_release_history


class LayeredReleaseStoreTests(unittest.TestCase):
    def setUp(self):
        fixture=test_layered_restructure_store.LayeredRestructureStoreTests();fixture.setUp()
        self.addCleanup(fixture.doCleanups);self.fixture=fixture;self.store=fixture.store;self.path=fixture.path
        self.amendment=fixture.amend();self.gid=fixture.gid
        ledger=self.store.load_team('a');self.original=ledger.generation_accounting(self.gid)
        self.inputs=dict(generation_id=self.gid,scope=PreseasonReleaseScope(2028,date(2028,6,1),date(2028,9,10),
            EXCLUDED_LIABILITIES,True,True,0,'synthetic healthy layered release'),
            discount=DiscountProfile(2028,Fraction(0),'synthetic discount'),payment_year_offsets=(0,),
            expected_revision=ledger.revision,access_check=lambda:None)

    def release(self,**changes):
        return self.store.release_calendar_layered_preseason_veteran('a','layered-release','v',**{**self.inputs,**changes})

    def next_year(self):
        teams={team:dict(expected_revision=self.store.load_team(team).revision,next_cap=20000000,
            next_cap_source='synthetic cap',roster_reserve=0,reserve_source='synthetic reserve',
            next_minimum_profile=VeteranMinimumProfile(2029,(('v',(7,7),('active_inactive',)*2),)).to_dict(),
            expired_generation_ids=[],exclusions=sorted(FranchiseStore.YEAR_TRANSITION_EXCLUSIONS),
            source='synthetic closing retained debt') for team in ('a','b')}
        self.store.advance_league_year(request_id='released-close',from_year=2028,to_year=2029,
            source='synthetic league closing',teams=teams)

    def test_unpaid_new_bonus_and_guaranteed_base_remain_with_all_history(self):
        result=self.release();self.assertEqual(result['format'],3)
        self.assertEqual(result['amendment_history'],self.amendment['amendment_history'])
        ledger=FranchiseStore(self.path).load_team('a');agreement=ledger.generation_accounting(self.gid)
        self.assertEqual(agreement.original_contract,self.original.original_contract)
        self.assertEqual(agreement.contract,self.original.contract)
        self.assertEqual(agreement.prior_restructures,self.original.prior_restructures)
        self.assertEqual(agreement.restructure,self.original.restructure)
        self.assertEqual(agreement.release_calendar_year,2028)
        self.assertEqual(agreement.release.original_contract.elapsed_years,2)
        self.assertEqual(agreement.release.retained[0].annual_charges,(Fraction(1250000),))
        self.assertEqual(agreement.release.retained[1].annual_charges,(Fraction(1800000),))
        self.assertEqual(agreement.payment_ceilings(),self.original.payment_ceilings())
        self.assertEqual(ledger.cash_snapshot()['nominal_total'],9000000)
        self.assertEqual(ledger.cash_snapshot()['paid_total'],7000000)
        self.assertEqual(ledger.generation_guarantee_cash(self.gid)['unpaid_signing_bonus'],200000)
        self.assertEqual(ledger.generation_guarantee_cash(self.gid)['unpaid_guaranteed_base_by_original_year'],[0,0,1800000])
        self.next_year();self.store=FranchiseStore(self.path)
        final=self.store.load_team('a');self.assertEqual(final.generation_accounting(self.gid),agreement)
        self.assertEqual(final.cash_snapshot()['unpaid_total'],2000000)
        self.assertEqual(final.generation_calendar_view(self.gid).annual_charges(),())
        self.store.record_payment('a','new-bonus-after-close','contract:v',200000,
            expected_cash_revision=final.cash_snapshot()['revision'],source='synthetic payroll',
            payment_reference='new bonus payment',component='bonus:calendar-layered-restructure:second-2028')
        final=self.store.load_team('a')
        self.store.record_payment('a','protected-base-after-close','contract:v',1800000,
            expected_cash_revision=final.cash_snapshot()['revision'],source='synthetic payroll',
            payment_reference='protected base payment',component='base:2')
        before=self.path.read_bytes();self.assertEqual(self.release(),result);self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(FranchiseStore(self.path).load_team('a').cash_snapshot()['unpaid_total'],0)

    def test_actual_post_june_timing_keeps_current_and_future_schedule_separate(self):
        scope=PreseasonReleaseScope(2028,date(2028,7,1),date(2028,9,10),EXCLUDED_LIABILITIES,
            True,True,0,'synthetic actual post-June release')
        self.release(scope=scope)
        agreement=self.store.load_team('a').generation_accounting(self.gid)
        self.assertEqual(agreement.release.retained[0].annual_charges,(Fraction(1250000),Fraction(0)))
        self.assertEqual(self.store.load_team('a').charges,(Fraction(3050000),Fraction(0)))

    def test_actual_june_boundary_with_nonzero_future_bonus_layers(self):
        for removed in (date(2028,6,1),date(2028,7,1)):
            fixture=test_calendar_release_history.CalendarReleaseHistoryTests();fixture.setUp()
            self.addCleanup(fixture.doCleanups)
            fixture.profile=lambda year:VeteranMinimumProfile(year,(('v',(7,)*min(4,2031-year),
                ('active_inactive',)*min(4,2031-year)),))
            fixture.create('a',ActiveContract(Offer('v',(2000000,)*4,3000000,(0,2000000,2000000,0)),
                'synthetic four-year original'))
            fixture.pay('a','base:0',2000000);fixture.anchor(('a',));fixture.roll(('a',),2026)
            store=fixture.store;ledger=store.load_team('a');gid=ledger.contract_identity('v').generation_id
            first_scope=self.fixture.first_inputs['scope']
            store.restructure_calendar_preseason_veteran('a','first','v',generation_id=gid,scope=first_scope,
                converted_base=100000,expected_revision=ledger.revision,access_check=lambda:None)
            fixture.pay('a','bonus:calendar-restructure:first',100000);fixture.pay('a','base:1',1900000)
            fixture.roll(('a',),2027)
            second_scope=replace(self.fixture.inputs['scope'],minimum_source=fixture.profile(2028).source)
            store.restructure_calendar_layered_preseason_veteran('a','second','v',generation_id=gid,scope=second_scope,
                converted_base=200000,expected_revision=store.load_team('a').revision,access_check=lambda:None)
            scope=replace(self.inputs['scope'],removed_on=removed)
            store.release_calendar_layered_preseason_veteran('a','release','v',generation_id=gid,scope=scope,
                discount=self.inputs['discount'],payment_year_offsets=(0,1),
                expected_revision=store.load_team('a').revision,access_check=lambda:None)
            plan=store.load_team('a').generation_accounting(gid).release
            expected=(Fraction(5300000,3),) if removed.month==6 else (Fraction(2650000,3),Fraction(2650000,3))
            with self.subTest(removed=removed):
                self.assertEqual(plan.retained[0].annual_charges,expected)
                self.assertEqual(plan.cancelled_unearned_base,2000000)
                self.assertEqual(plan.cash_obligation.amount,9000000)
                self.assertEqual(plan.cash_obligation.paid,7000000)

    def test_legacy_route_and_final_callbacks_fail_without_mutation(self):
        before=self.path.read_bytes()
        with self.assertRaises(Rejected):
            self.store.release_calendar_preseason_veteran('a','legacy','v',**self.inputs)
        self.assertEqual(self.path.read_bytes(),before)
        def denied():raise TimeoutError('synthetic access revoked')
        def bad_receipt(_):raise ValueError('synthetic unsupported native format')
        for changes in ({'generation_id':'foreign'},{'expected_revision':True},{'access_check':denied},{'receipt_check':bad_receipt}):
            with self.subTest(changes=changes),self.assertRaises((ValueError,Rejected,TimeoutError)):self.release(**changes)
            self.assertEqual(self.path.read_bytes(),before)

    def test_event_insert_failure_restores_ownership_and_money(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TRIGGER reject_layered_release BEFORE INSERT ON events WHEN NEW.kind='calendar_layered_release' BEGIN SELECT RAISE(ABORT,'synthetic reject'); END");db.commit()
        before=self.path.read_bytes()
        with self.assertRaises(sqlite3.IntegrityError):self.release()
        self.assertEqual(self.path.read_bytes(),before)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT team_id FROM ownership WHERE player_id='v'").fetchone(),('a',))

    def test_replay_rejects_root_history_calendar_and_source_downgrades(self):
        self.release();original=self.path.read_bytes()
        for scenario in ('format','history','generation','calendar','date','kind'):
            path=self.path.with_name('release-'+scenario+'.sqlite');path.write_bytes(original)
            with closing(sqlite3.connect(path)) as db:
                event_id,serialized=db.execute("SELECT id,payload FROM events WHERE kind='calendar_layered_release'").fetchone()
                payload=json.loads(serialized)
                if scenario=='format':payload['format']=1
                elif scenario=='history':payload['generation_posting']['agreements'][0]['amendment_history']['prior_restructures']=[]
                elif scenario=='generation':payload['before_generation_posting']['format']=True
                elif scenario=='calendar':payload['calendar_posting']['league_year']=2028.0
                elif scenario=='date':payload['scope']['removed_on']='20280601'
                else:db.execute("UPDATE events SET kind='calendar_release' WHERE id=?",(event_id,))
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),event_id));db.commit()
            with self.subTest(scenario=scenario),self.assertRaises((ValueError,Rejected)):
                FranchiseStore(path).load_team('a')
