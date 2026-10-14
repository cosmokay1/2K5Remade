from contextlib import closing
from datetime import date
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
from franchise.trades import PreseasonTradeScope,EXCLUDED_TRADE_LIABILITIES


class CalendarTradeStoreTests(unittest.TestCase):
    def bridge_request(self):
        from dataclasses import asdict
        scope=asdict(self.inputs['scope']);scope.update(exclusions=sorted(scope['exclusions']))
        for field in ('traded_on','seller_first_regular_season_game','buyer_first_regular_season_game'):
            scope[field]=scope[field].isoformat()
        return dict(protocol=1,request_id='bridge-calendar-trade',operation='manual_trade',seller='a',buyer='b',
            player_id='v',seller_revision=self.inputs['seller_revision'],buyer_revision=self.inputs['buyer_revision'],
            seller_generation_id=self.inputs['seller_generation_id'],buyer_previous_generation_id=None,
            scope=scope,decision_mode='manual',calendar_format='calendar_v1',timeout_ms=1000)

    def test_explicit_calendar_trade_bridge_ai_off_full_compact_and_retry(self):
        from franchise.bridge import Bridge
        from franchise.control import AccessDisabled
        def forbidden(_):raise AssertionError('Manual trade invoked inference')
        def disabled():raise AccessDisabled('synthetic shutdown')
        bridge=Bridge(self.store,provider=forbidden,access_check=disabled)
        request=self.bridge_request();before=self.path.read_bytes()
        for changes in ({'calendar_format':True},{'seller_generation_id':None},{'buyer_revision':True}):
            self.assertIsNotNone(bridge.handle({**request,**changes})['error'])
            self.assertEqual(self.path.read_bytes(),before)
        legacy={key:value for key,value in request.items() if key!='calendar_format'}
        self.assertIsNotNone(bridge.handle(legacy)['error']);self.assertEqual(self.path.read_bytes(),before)
        reply=bridge.handle(request);self.assertIsNone(reply['error'])
        self.assertEqual(reply['result']['format'],2)
        self.assertEqual(reply['result']['league_year'],2027)
        self.assertEqual(reply['result']['calendar_format'],'calendar_v1')
        self.assertEqual(reply['result']['trade']['a']['financial']['signed_players'],[])
        compact=Bridge(FranchiseStore(self.path),provider=forbidden,access_check=disabled).handle({**request,'receipt_format':'target_v1'})
        self.assertIsNone(compact['error'])
        self.assertEqual(compact['result']['format'],2);self.assertEqual(compact['result']['league_year'],2027)
        self.assertEqual(compact['result']['seller_generation_id'],request['seller_generation_id'])
        self.assertEqual(bridge.handle(request),reply)

    def test_calendar_trade_bridge_connection_and_receipt_capacity_rollback(self):
        from franchise.bridge import Bridge,ResponseTooLarge
        from unittest.mock import patch
        request=self.bridge_request();before=self.path.read_bytes();calls=[]
        def disconnect():
            calls.append(1)
            if len(calls)>1:raise TimeoutError('synthetic disconnect')
        bridge=Bridge(self.store,provider=lambda _:None,access_check=lambda:None,connection_check=disconnect)
        self.assertEqual(bridge.handle(request)['error'],'timeout');self.assertEqual(self.path.read_bytes(),before)
        bridge.connection_check=lambda:None
        with patch.object(bridge,'_require_frame',side_effect=ResponseTooLarge('synthetic full native frame')):
            self.assertIsNotNone(bridge.handle(request)['error'])
        self.assertEqual(self.path.read_bytes(),before)

    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'calendar-trade.sqlite';self.store=FranchiseStore(self.path)
        contract=ActiveContract(Offer('v',(2000000,)*3,3000000),'synthetic source agreement')
        for team in ('a','b'):
            profile=self.profile(2026)
            books=OpeningBooks(contracts=(contract,) if team=='a' else (),
                retained=(ChargeRecord(team+'-debt',(7,11,13),'synthetic retained history'),))
            self.store.create_team(team,Ledger.from_opening(books,cap=10000000,roster_reserve=0,
                max_bonus_years=5,veteran_minimums=profile.floors(),veteran_minimum_profile=profile))
            records=(CashObligation('contract:v','v',9000000,5000000,'synthetic paid earned salary and bonus',
                (('signing_bonus',3000000),('base:0',2000000))),) if team=='a' else ()
            self.store.initialize_cash(team,records,source='synthetic complete cash')
        self.store.bind_actor('a','v',{'money':0.8},{'trust':0.6},access_check=lambda:None)
        self.store.bind_actor('b','v',{'money':0.8},{'trust':0.5},access_check=lambda:None)
        self.store.anchor_calendar(request_id='anchor',league_year=2026,source='synthetic league calendar',
            expected_revisions={team:self.store.load_team(team).revision for team in ('a','b')})
        self.store.migrate_generations(self.path)
        self.roll(2026)
        self.inputs=dict(scope=PreseasonTradeScope(2027,date(2027,6,2),date(2027,9,10),date(2027,9,10),
                EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'synthetic consenting calendar assignment'),
            seller_revision=self.store.load_team('a').revision,buyer_revision=self.store.load_team('b').revision,
            seller_generation_id=self.store.load_team('a').contract_identity('v').generation_id,
            buyer_previous_generation_id=None,access_check=lambda:None)

    def profile(self,year):
        return VeteranMinimumProfile(year,(('v',(7,7,7),('active_inactive',)*3),))

    def roll(self,year):
        terms={team:dict(expected_revision=self.store.load_team(team).revision,next_cap=9000000,
            next_cap_source='synthetic cap',roster_reserve=0,reserve_source='synthetic reserve',
            next_minimum_profile=self.profile(year+1).to_dict(),expired_generation_ids=[],
            exclusions=sorted(FranchiseStore.YEAR_TRANSITION_EXCLUSIONS),source='synthetic reconciled closing') for team in ('a','b')}
        self.store.advance_league_year(request_id='roll-'+str(year),from_year=year,to_year=year+1,
            source='synthetic common next year',teams=terms)

    def trade(self,**changes):
        return self.store.trade_calendar_preseason_veteran('assignment','a','b','v',**{**self.inputs,**changes})

    def test_atomic_trade_restart_personality_and_historical_retry_after_later_roll(self):
        original=self.store.load_team('a').generation_accounting(self.inputs['seller_generation_id'])
        receipt=self.trade();self.assertEqual(receipt['format'],2);self.assertEqual(receipt['league_year'],2027)
        self.store=FranchiseStore(self.path)
        source,target=self.store.load_team('a'),self.store.load_team('b')
        self.assertEqual(source.charges,(1000011,1000013));self.assertEqual(target.charges,(2000011,2000013))
        self.assertEqual(source.cash_snapshot()['nominal_total']+target.cash_snapshot()['nominal_total'],9000000)
        self.assertEqual(source.generation_accounting(self.inputs['seller_generation_id']).contract,original.contract)
        self.assertEqual(target.contract_identity('v').generation_id,receipt['buyer_generation_id'])
        self.assertEqual(target.generation_calendar_view(receipt['buyer_generation_id']).anchor_year,2027)
        self.assertEqual(self.store.player_context('b','v',context_format='calendar_v1')['personality'],{'money':0.8})
        self.assertEqual(self.store.player_context('b','v',context_format='calendar_v1')['relationships'],{'trust':0.5})
        self.assertEqual(self.trade(),receipt)
        with self.assertRaises(Rejected):self.store.calendar_contract_context('a',self.inputs['seller_generation_id'],context_format='calendar_v2')
        self.store.record_payment('b','pay-base',receipt['buyer_generation_id'],2000000,
            expected_cash_revision=target.cash_snapshot()['revision'],source='synthetic earned buyer salary',
            payment_reference='buyer-2027-base',component='base:0')
        self.roll(2027);self.store=FranchiseStore(self.path)
        self.assertEqual(self.store.load_team('a').charges,(1000013,))
        self.assertEqual(self.store.load_team('b').charges,(2000013,))
        self.assertEqual(self.store.load_team('b').active_contract('v').elapsed_years,1)
        self.assertEqual(self.trade(),receipt)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT team_id FROM ownership WHERE player_id=?',('v',)).fetchone(),('b',))

    def test_stale_identity_access_and_receipt_failure_roll_back_both_teams(self):
        before=self.path.read_bytes()
        def denied():raise RuntimeError('synthetic disconnect')
        def reject(_):raise ValueError('synthetic oversized native receipt')
        for changes in ({'seller_revision':True},{'buyer_revision':0},{'seller_generation_id':'foreign'},
                        {'buyer_previous_generation_id':'foreign'},{'access_check':denied},{'receipt_check':reject}):
            with self.subTest(changes=changes),self.assertRaises((ValueError,Rejected,RuntimeError)):
                self.trade(**changes)
            self.assertEqual(self.path.read_bytes(),before)
        with self.assertRaises(Rejected):
            self.store.trade_preseason_veteran('legacy','a','b','v',**self.inputs)
        self.assertEqual(self.path.read_bytes(),before)

    def test_calendar_v3_inspects_retained_seller_and_rebased_buyer_without_writes(self):
        receipt=self.trade();before=self.path.read_bytes()
        seller=self.store.calendar_contract_context('a',self.inputs['seller_generation_id'],context_format='calendar_v3')
        buyer=self.store.calendar_contract_context('b',receipt['buyer_generation_id'],context_format='calendar_v3')
        self.assertEqual(seller['format'],4)
        self.assertEqual(seller['trade_calendar'],dict(league_year=2027,elapsed_years=1,source=self.inputs['scope'].source))
        self.assertEqual(seller['economic_archive']['contract']['elapsed_years'],0)
        self.assertEqual(seller['economic_archive']['cash_obligation']['amount'],5000000)
        self.assertFalse(seller['calendar_accounting']['ownership_current'])
        self.assertIsNone(seller['release_calendar']);self.assertIsNone(buyer['trade_calendar'])
        self.assertEqual(buyer['calendar_accounting']['current_contract']['elapsed_years'],0)
        from franchise.bridge import Bridge
        from franchise.control import AccessDisabled
        def forbidden(_):raise AssertionError('Read invoked inference')
        def disabled():raise AccessDisabled('synthetic AI shutdown')
        bridge=Bridge(self.store,provider=forbidden,access_check=disabled)
        request=dict(protocol=1,request_id='inspect-seller',operation='contract_context',team_id='a',
            generation_id=self.inputs['seller_generation_id'],context_format='calendar_v3',timeout_ms=1000)
        self.assertEqual(bridge.handle(request)['result'],seller)
        request.pop('generation_id');request.update(operation='player_context',player_id='v')
        self.assertEqual(bridge.handle(request)['result']['calendar_contract_context'],seller)
        self.assertEqual(self.path.read_bytes(),before)

    def test_failed_second_event_rolls_back_ownership_and_first_event(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TRIGGER reject_calendar_buyer BEFORE INSERT ON events WHEN NEW.kind='calendar_trade_in' BEGIN SELECT RAISE(ABORT,'synthetic reject'); END");db.commit()
        before=self.path.read_bytes()
        with self.assertRaises(sqlite3.IntegrityError):self.trade()
        self.assertEqual(self.path.read_bytes(),before)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM events WHERE kind LIKE 'calendar_trade_%'").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT team_id FROM ownership WHERE player_id='v'").fetchone(),('a',))

    def test_paired_replay_rejects_calendar_type_scope_and_posting_tampering(self):
        self.trade();original=self.path.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            for scenario in range(10):
                path=Path(directory)/('tamper-'+str(scenario)+'.sqlite');path.write_bytes(original)
                with closing(sqlite3.connect(path)) as db:
                    rows=db.execute("SELECT id,payload FROM events WHERE kind LIKE 'calendar_trade_%'").fetchall()
                    for index,(event_id,serialized) in enumerate(rows):
                        payload=json.loads(serialized);common=payload['trade']
                        if scenario==0:common['calendar_format']=True
                        if scenario==1:common['before_calendars']['a']['league_year']=2027.0
                        if scenario==2:common['after_calendars']['b']['league_year']=2026
                        if scenario==3:common['expected_revisions']['b']=True
                        if scenario==4:common['before_calendars']['foreign']=copy.deepcopy(common['before_calendars']['a'])
                        if scenario==5 and index==0:common['scope']['source']='changed peer'
                        if scenario==6:common['after_generations']['a']['agreements'][0]['outgoing_trade_calendar_year']=2026
                        if scenario==7 and index==1:payload['unexpected']='foreign peer field'
                        db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),event_id))
                    if scenario==8:db.execute("DELETE FROM events WHERE kind='calendar_trade_in'")
                    if scenario==9:db.execute("UPDATE events SET kind='generation_trade_out' WHERE kind='calendar_trade_out'")
                    db.commit()
                with self.subTest(scenario=scenario),self.assertRaises((ValueError,Rejected)):
                    FranchiseStore(path).load_team('a')
