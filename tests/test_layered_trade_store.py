"""Paired assignments preserve seller amendment history and separate buyer cash."""
from contextlib import closing
from dataclasses import replace
from datetime import date
from fractions import Fraction
import json
import sqlite3
import unittest
from franchise.books import ActiveContract
from franchise.cap import Offer,Rejected
from franchise.guarantees import DiscountProfile
from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
from franchise.restructures import PreseasonRestructureScope,EXCLUDED_RESTRUCTURE_TERMS
from franchise.salary_rules import VeteranMinimumProfile
from franchise.store import FranchiseStore
from franchise.trades import PreseasonTradeScope,EXCLUDED_TRADE_LIABILITIES
from tests import test_calendar_release_history


class LayeredTradeStoreTests(unittest.TestCase):
    def setUp(self):
        fixture=test_calendar_release_history.CalendarReleaseHistoryTests();fixture.setUp()
        self.addCleanup(fixture.doCleanups);self.fixture=fixture;self.store=fixture.store;self.path=fixture.path
        fixture.profile=lambda year:VeteranMinimumProfile(year,(('v',(7,)*min(4,2031-year),
            ('active_inactive',)*min(4,2031-year)),))
        fixture.create('a',ActiveContract(Offer('v',(2000000,)*4,3000000,(0,2000000,2000000,0)),'synthetic original'))
        fixture.create('b');fixture.pay('a','base:0',2000000);fixture.anchor(('a','b'));fixture.roll(('a','b'),2026)
        ledger=self.store.load_team('a');self.gid=ledger.contract_identity('v').generation_id
        scope=PreseasonRestructureScope(2027,date(2027,6,1),date(2027,9,10),0,True,True,True,
            EXCLUDED_RESTRUCTURE_TERMS,fixture.profile(2027).source,'synthetic first conversion')
        self.store.restructure_calendar_preseason_veteran('a','first','v',generation_id=self.gid,scope=scope,
            converted_base=100000,expected_revision=ledger.revision,access_check=lambda:None)
        fixture.pay('a','bonus:calendar-restructure:first',100000);fixture.pay('a','base:1',1900000)
        fixture.roll(('a','b'),2027)
        self.store.restructure_calendar_layered_preseason_veteran('a','second','v',generation_id=self.gid,
            scope=replace(scope,league_year=2028,amended_on=date(2028,6,1),first_regular_season_game=date(2028,9,10),
                minimum_source=fixture.profile(2028).source,source='synthetic second conversion'),
            converted_base=200000,expected_revision=self.store.load_team('a').revision,access_check=lambda:None)
        fixture.pay('a','bonus:calendar-layered-restructure:second',200000)
        self.original=self.store.load_team('a').generation_accounting(self.gid)
        self.inputs=dict(scope=PreseasonTradeScope(2028,date(2028,7,1),date(2028,9,10),date(2028,9,10),
            EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'synthetic layered assignment'),
            seller_revision=self.store.load_team('a').revision,buyer_revision=self.store.load_team('b').revision,
            seller_generation_id=self.gid,buyer_previous_generation_id=None,access_check=lambda:None)

    def trade(self,**changes):
        return self.store.trade_calendar_layered_preseason_veteran('assignment','a','b','v',**{**self.inputs,**changes})

    def test_full_chain_separate_buyer_payroll_roll_release_and_historical_retry(self):
        result=self.trade();self.assertEqual(set(result),{'format','participants','seller_generation_id',
            'buyer_generation_id','buyer_previous_generation_id','league_year','amendment_history'})
        self.assertEqual(result['format'],3)
        self.assertEqual(result['amendment_history'],self.original.amendment_history_snapshot())
        seller=FranchiseStore(self.path).load_team('a');buyer=self.store.load_team('b');buyerid=result['buyer_generation_id']
        archived=seller.generation_accounting(self.gid)
        self.assertEqual(archived.original_contract,self.original.original_contract)
        self.assertEqual(archived.contract,self.original.contract)
        self.assertEqual(archived.prior_restructures,self.original.prior_restructures)
        self.assertEqual(archived.restructure,self.original.restructure)
        self.assertEqual(archived.outgoing_trade_calendar_year,2028)
        self.assertEqual(archived.payment_ceilings()['base:0'],2000000)
        self.assertEqual(archived.payment_ceilings()['base:1'],1900000)
        self.assertEqual(archived.payment_ceilings()['base:2'],0)
        self.assertEqual(seller.generation_cash(self.gid).amount,7200000)
        self.assertEqual(seller.generation_cash(self.gid).paid,7200000)
        self.assertEqual(seller.charges,(Fraction(2650000,3),)*2)
        incoming=buyer.generation_accounting(buyerid)
        self.assertEqual(incoming.contract.offer.salaries,(1800000,2000000))
        self.assertEqual(incoming.contract.offer.guaranteed_salaries,(1800000,0))
        self.assertEqual(incoming.contract.bonus_layers,())
        self.assertEqual(incoming.prior_restructures,())
        self.assertIsNone(incoming.restructure)
        self.assertEqual(buyer.generation_cash(buyerid).amount,3800000)
        self.assertEqual(buyer.generation_cash(buyerid).paid_components,())
        self.fixture.pay('b','base:0',1800000);self.fixture.roll(('a','b'),2028)
        buyer=self.store.load_team('b');self.assertEqual(buyer.active_contract('v').elapsed_years,1)
        self.assertEqual(self.store.load_team('a').charges,(Fraction(2650000,3),))
        self.store.release_calendar_preseason_veteran('b','buyer-release','v',generation_id=buyerid,
            scope=PreseasonReleaseScope(2029,date(2029,6,1),date(2029,9,10),EXCLUDED_LIABILITIES,
                True,True,0,'synthetic buyer release'),discount=DiscountProfile(2029,Fraction(0),'synthetic rate'),
            payment_year_offsets=(0,),expected_revision=buyer.revision,access_check=lambda:None)
        self.store=FranchiseStore(self.path)
        self.assertEqual(self.store.load_team('b').generation_cash(buyerid).amount,1800000)
        self.assertEqual(self.store.load_team('a').generation_accounting(self.gid),archived)
        before=self.path.read_bytes();self.assertEqual(self.trade(),result);self.assertEqual(self.path.read_bytes(),before)

    def test_old_writer_and_final_callbacks_are_atomic(self):
        before=self.path.read_bytes()
        with self.assertRaises(Rejected):self.store.trade_calendar_preseason_veteran('old','a','b','v',**self.inputs)
        self.assertEqual(self.path.read_bytes(),before)
        def denied():raise TimeoutError('synthetic shutdown')
        def bad(_):raise ValueError('synthetic native receipt rejection')
        for changes in ({'seller_generation_id':'foreign'},{'buyer_previous_generation_id':'foreign'},
                        {'buyer_revision':True},{'access_check':denied},{'receipt_check':bad}):
            with self.subTest(changes=changes),self.assertRaises((Rejected,ValueError,TimeoutError)):self.trade(**changes)
            self.assertEqual(self.path.read_bytes(),before)

    def test_unpaid_existing_layer_cannot_be_assigned(self):
        # Rebuild a source snapshot with the last legitimate payment event removed.
        with closing(sqlite3.connect(self.path)) as db:
            event_id=db.execute("SELECT id FROM events WHERE team_id='a' AND kind='cash_payment' ORDER BY id DESC LIMIT 1").fetchone()[0]
            db.execute('DELETE FROM events WHERE id=?',(event_id,));db.commit()
        self.inputs['seller_revision']=self.store.load_team('a').revision
        before=self.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'bonus layer'):self.trade()
        self.assertEqual(self.path.read_bytes(),before)

    def test_second_event_failure_restores_owner_and_both_postings(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TRIGGER reject_layered_buyer BEFORE INSERT ON events WHEN NEW.kind='calendar_layered_trade_in' BEGIN SELECT RAISE(ABORT,'synthetic reject'); END");db.commit()
        before=self.path.read_bytes()
        with self.assertRaises(sqlite3.IntegrityError):self.trade()
        self.assertEqual(self.path.read_bytes(),before)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT team_id FROM ownership WHERE player_id='v'").fetchone(),('a',))
            self.assertEqual(db.execute("SELECT count(*) FROM events WHERE kind LIKE 'calendar_layered_trade_%'").fetchone()[0],0)

    def test_peer_source_history_and_version_tampering_reject_replay(self):
        self.trade();original=self.path.read_bytes()
        for scenario in ('format','before_history','after_history','source_cursor','peer','calendar_type'):
            path=self.path.with_name('trade-'+scenario+'.sqlite');path.write_bytes(original)
            with closing(sqlite3.connect(path)) as db:
                rows=db.execute("SELECT id,payload FROM events WHERE kind LIKE 'calendar_layered_trade_%'").fetchall()
                for index,(event_id,serialized) in enumerate(rows):
                    payload=json.loads(serialized);common=payload['trade']
                    if scenario=='format':common['format']=1
                    elif scenario=='before_history':common['before_generations']['a']['agreements'][0]['amendment_history']['prior_restructures']=[]
                    elif scenario=='after_history':common['after_generations']['a']['agreements'][0]['amendment_history']['prior_restructures']=[]
                    elif scenario=='source_cursor':common['original_contract']['elapsed_years']=1
                    elif scenario=='peer' and index==0:common['scope']['source']='different peer source'
                    elif scenario=='calendar_type':common['after_calendars']['b']['league_year']=2028.0
                    db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),event_id))
                db.commit()
            with self.subTest(scenario=scenario),self.assertRaises((ValueError,Rejected)):
                FranchiseStore(path).load_team('a')

    def test_receiving_club_keeps_its_own_prior_layered_archive_on_return_assignment(self):
        fixture=test_calendar_release_history.CalendarReleaseHistoryTests();fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.profile=lambda year:VeteranMinimumProfile(year,(('v',(7,)*min(5,2031-year),
            ('active_inactive',)*min(5,2031-year)),))
        fixture.create('b',ActiveContract(Offer('v',(2000000,)*5,3000000,(0,2000000,2000000,2000000,2000000)),
            'synthetic five-year original'))
        fixture.create('a');fixture.pay('b','base:0',2000000)
        fixture.anchor(('a','b'));fixture.roll(('a','b'),2026)
        store=fixture.store
        def amend(team,year,amount,layered):
            ledger=store.load_team(team)
            scope=PreseasonRestructureScope(year,date(year,6,1),date(year,9,10),0,True,True,True,
                EXCLUDED_RESTRUCTURE_TERMS,fixture.profile(year).source,'synthetic '+team+' conversion '+str(year))
            method=store.restructure_calendar_layered_preseason_veteran if layered else store.restructure_calendar_preseason_veteran
            method(team,'conversion-'+str(year),'v',generation_id=ledger.contract_identity('v').generation_id,
                scope=scope,converted_base=amount,expected_revision=ledger.revision,access_check=lambda:None)
            prefix='calendar-layered-restructure:' if layered else 'calendar-restructure:'
            fixture.pay(team,'bonus:'+prefix+'conversion-'+str(year),amount)
        def assign(source,target,year,request):
            seller=store.load_team(source);buyer=store.load_team(target)
            return store.trade_calendar_layered_preseason_veteran(request,source,target,'v',
                scope=PreseasonTradeScope(year,date(year,7,1),date(year,9,10),date(year,9,10),
                    EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'synthetic return assignment'),
                seller_revision=seller.revision,buyer_revision=buyer.revision,
                seller_generation_id=seller.contract_identity('v').generation_id,
                buyer_previous_generation_id=buyer.contract_identity('v').generation_id if 'v' in buyer._contracts else None,
                access_check=lambda:None)
        amend('b',2027,100000,False);fixture.pay('b','base:1',1900000);fixture.roll(('a','b'),2027)
        amend('b',2028,200000,True);first=assign('b','a',2028,'first-assignment')
        old_id=first['seller_generation_id'];old_archive=store.load_team('b').generation_accounting(old_id)
        old_cash=store.load_team('b').generation_cash(old_id)
        fixture.pay('a','base:0',1800000);fixture.roll(('a','b'),2028)
        amend('a',2029,100000,False);fixture.pay('a','base:1',1900000);fixture.roll(('a','b'),2029)
        amend('a',2030,200000,True);receipt=assign('a','b',2030,'return-assignment')
        restarted=FranchiseStore(fixture.path);buyer=restarted.load_team('b')
        self.assertEqual(buyer.generation_accounting(old_id),old_archive)
        self.assertEqual(buyer.generation_cash(old_id),old_cash)
        self.assertEqual(receipt['buyer_previous_generation_id'],old_id)
        new=buyer.generation_accounting(receipt['buyer_generation_id'])
        self.assertEqual(new.contract.offer.salaries,(1800000,))
        self.assertEqual(new.prior_restructures,())
        self.assertEqual(new.contract.bonus_layers,())
        self.assertEqual(len(buyer.generation_snapshot(history_format=2)['agreements']),2)
