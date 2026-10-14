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
from franchise.bridge import Bridge
from franchise.control import AccessDisabled
from datetime import date
from fractions import Fraction
from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
from franchise.guarantees import DiscountProfile


class StoredYearTransitionTests(unittest.TestCase):
    def calendar_release_request(self):
        inputs=self.calendar_release_inputs()
        from dataclasses import asdict
        scope=asdict(inputs['scope']);scope.update(exclusions=sorted(scope['exclusions']),
            removed_on=scope['removed_on'].isoformat(),first_regular_season_game=scope['first_regular_season_game'].isoformat())
        return dict(protocol=1,request_id='bridge-calendar-release',operation='manual_release',
            team_id='a',player_id='a',expected_revision=inputs['expected_revision'],timeout_ms=1000,
            decision_mode='manual',calendar_format='calendar_v1',generation_id=inputs['generation_id'],
            scope=scope,discount=dict(league_year=2027,annual_rate=0,rate_source='synthetic discount'),
            payment_year_offsets=list(inputs['payment_year_offsets']))

    def test_calendar_release_bridge_is_explicit_manual_and_retryable_with_ai_off(self):
        self.store.advance_league_year(**self.inputs)
        def forbidden(_):raise AssertionError('Manual release invoked inference')
        def disabled():raise AccessDisabled('synthetic shutdown')
        bridge=Bridge(self.store,provider=forbidden,access_check=disabled)
        request=self.calendar_release_request()
        before=self.path.read_bytes()
        for changes in ({'calendar_format':True},{'generation_id':'foreign'},{'expected_revision':True}):
            self.assertIsNotNone(bridge.handle({**request,**changes})['error'])
            self.assertEqual(self.path.read_bytes(),before)
        legacy={key:value for key,value in request.items() if key not in ('calendar_format','generation_id')}
        self.assertIsNotNone(bridge.handle(legacy)['error'])
        self.assertEqual(self.path.read_bytes(),before)
        reply=bridge.handle(request)
        self.assertIsNone(reply['error'])
        self.assertEqual(reply['result']['release']['generation_id'],request['generation_id'])
        self.assertEqual(reply['result']['release']['format'],2)
        self.assertEqual(reply['result']['release']['league_year'],2027)
        self.assertEqual(reply['result']['release']['financial']['signed_players'],[])
        compact={**request,'receipt_format':'target_v1'}
        compact_reply=Bridge(FranchiseStore(self.path),provider=forbidden,access_check=disabled).handle(compact)
        self.assertIsNone(compact_reply['error'])
        self.assertEqual(compact_reply['result']['release']['generation_id'],request['generation_id'])
        self.assertEqual(compact_reply['result']['release']['league_year'],2027)
        self.assertEqual(bridge.handle(request),reply)

    def test_calendar_release_bridge_disconnect_and_oversized_receipt_rollback(self):
        self.store.advance_league_year(**self.inputs)
        request=self.calendar_release_request();before=self.path.read_bytes();calls=[]
        def disconnect():
            calls.append(1)
            if len(calls)>1:raise TimeoutError('synthetic disconnect')
        bridge=Bridge(self.store,provider=lambda _:None,access_check=lambda:None,connection_check=disconnect)
        self.assertEqual(bridge.handle(request)['error'],'timeout')
        self.assertEqual(self.path.read_bytes(),before)
        from unittest.mock import patch
        from franchise.bridge import ResponseTooLarge
        bridge.connection_check=lambda:None
        with patch.object(bridge,'_require_frame',side_effect=ResponseTooLarge('synthetic full frame')):
            self.assertIsNotNone(bridge.handle(request)['error'])
        self.assertEqual(self.path.read_bytes(),before)

    def calendar_release_inputs(self):
        return dict(generation_id=self.store.load_team('a').contract_identity('a').generation_id,
            scope=PreseasonReleaseScope(2027,date(2027,7,1),date(2027,9,10),EXCLUDED_LIABILITIES,
                True,True,0,'synthetic verified healthy release'),
            discount=DiscountProfile(2027,Fraction(0),'synthetic discount'),payment_year_offsets=(0,1),
            expected_revision=3,access_check=lambda:None)

    def test_calendar_release_replays_retained_money_and_historical_retry(self):
        self.store.advance_league_year(**self.inputs)
        release=self.calendar_release_inputs()
        receipt=self.store.release_calendar_preseason_veteran('a','later','a',**release)
        self.assertEqual(receipt['format'],2)
        self.assertEqual(receipt['league_year'],2027)
        restarted=FranchiseStore(self.path)
        self.assertEqual(restarted.load_team('a').charges,(1000011,1000013))
        self.assertEqual(restarted.load_team('a').cash_snapshot()['unpaid_total'],0)
        self.assertEqual(restarted.load_team('a').financial_snapshot()['signed_players'],[])
        self.assertEqual(restarted.release_calendar_preseason_veteran('a','later','a',**release),receipt)
        inputs=copy.deepcopy(self.inputs);inputs.update(request_id='roll-after-release',from_year=2027,to_year=2028)
        for team in ('a','b'):
            inputs['teams'][team].update(expected_revision=restarted.load_team(team).revision,
                expired_generation_ids=[],next_minimum_profile=self.minimum_profile(2028,team,2).to_dict())
        restarted.advance_league_year(**inputs)
        self.assertEqual(FranchiseStore(self.path).load_team('a').charges,(1000013,))
        self.assertEqual(restarted.release_calendar_preseason_veteran('a','later','a',**release),receipt)
        with self.assertRaises(Rejected):restarted.calendar_contract_context('a',release['generation_id'])

    def test_calendar_release_access_and_receipt_failures_rollback(self):
        self.store.advance_league_year(**self.inputs)
        inputs=self.calendar_release_inputs();before=self.path.read_bytes()
        def denied():raise AccessDisabled('synthetic shutdown')
        def reject(_):raise ValueError('synthetic native rejection')
        for changes in ({'access_check':denied},{'receipt_check':reject},{'generation_id':'foreign'}):
            with self.assertRaises((AccessDisabled,ValueError,Rejected)):
                self.store.release_calendar_preseason_veteran('a','fail','a',**{**inputs,**changes})
            self.assertEqual(self.path.read_bytes(),before)
            self.assertEqual(self.store.load_team('a').financial_snapshot()['signed_players'],['a'])

    def test_calendar_release_replay_rejects_type_downgrade_and_cursor_tampering(self):
        self.store.advance_league_year(**self.inputs)
        self.store.release_calendar_preseason_veteran('a','later','a',**self.calendar_release_inputs())
        original=self.path.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            for scenario in range(6):
                path=Path(directory)/('tamper-'+str(scenario)+'.sqlite');path.write_bytes(original)
                with closing(sqlite3.connect(path)) as db:
                    row=db.execute("SELECT id,payload FROM events WHERE kind='calendar_release'").fetchone()
                    payload=json.loads(row[1])
                    if scenario==0:payload['calendar_format']=True
                    if scenario==1:payload['before_calendar_posting']['league_year']=2027.0
                    if scenario==2:payload['generation_posting']['agreements'][0]['release_calendar_year']=2026
                    if scenario==3:payload['scope']['removed_on']='20270701'
                    if scenario==4:payload['discount']['annual_rate']='0/1'
                    if scenario==5:payload['extra']='unsupported'
                    db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),row[0]));db.commit()
                with self.subTest(scenario=scenario),self.assertRaises((ValueError,Rejected)):
                    FranchiseStore(path).load_team('a')

    def test_calendar_v2_reads_release_cursor_without_rewriting_archived_terms(self):
        self.store.advance_league_year(**self.inputs)
        inputs=self.calendar_release_inputs()
        self.store.release_calendar_preseason_veteran('a','later','a',**inputs)
        before=self.path.read_bytes()
        context=self.store.calendar_contract_context('a',inputs['generation_id'],context_format='calendar_v2')
        self.assertEqual(context['format'],3)
        self.assertEqual(context['release_calendar'],dict(league_year=2027,elapsed_years=1,source=inputs['scope'].source))
        self.assertEqual(context['economic_archive']['contract']['elapsed_years'],0)
        self.assertEqual(context['calendar_accounting']['status'],'released')
        self.assertFalse(context['calendar_accounting']['ownership_current'])
        self.assertEqual(context['economic_archive']['cash_obligation']['paid_components'],
            [['signing_bonus',3000000],['base:0',2000000]])
        def unexpected(_):raise AssertionError('Read invoked inference')
        def disabled():raise AccessDisabled('synthetic shutdown')
        bridge=Bridge(self.store,provider=unexpected,access_check=disabled)
        request=dict(protocol=1,request_id='released',operation='contract_context',team_id='a',
            generation_id=inputs['generation_id'],timeout_ms=1000,context_format='calendar_v2')
        self.assertEqual(bridge.handle(request)['result'],context)
        profile={key:value for key,value in request.items() if key!='generation_id'}
        profile.update(operation='player_context',player_id='a')
        result=bridge.handle(profile)
        self.assertIsNone(result['error'])
        self.assertEqual(result['result']['calendar_contract_context'],context)
        ordinary=self.store.calendar_contract_context('b',self.store.load_team('b').contract_identity('b').generation_id,
            context_format='calendar_v2')
        self.assertIsNone(ordinary['release_calendar'])
        self.assertEqual(self.path.read_bytes(),before)
        next_year=copy.deepcopy(self.inputs)
        next_year.update(request_id='inspect-later',from_year=2027,to_year=2028)
        for team in ('a','b'):
            next_year['teams'][team].update(expected_revision=self.store.load_team(team).revision,
                expired_generation_ids=[],next_minimum_profile=self.minimum_profile(2028,team,2).to_dict())
        self.store.advance_league_year(**next_year)
        later=FranchiseStore(self.path).calendar_contract_context('a',inputs['generation_id'],context_format='calendar_v2')
        self.assertEqual(later['economic_archive'],context['economic_archive'])
        self.assertEqual(later['release_calendar'],context['release_calendar'])
        self.assertEqual(later['calendar_accounting']['annual_charges'],context['calendar_accounting']['annual_charges'][1:])
        self.assertEqual(later['league_year'],2028)

    def minimum_profile(self,year,team,term):
        players=(team,'new') if team=='a' else (team,)
        return VeteranMinimumProfile(year,tuple((player,(7,)*term,('active_inactive',)*term) for player in players))

    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'league.sqlite';self.store=FranchiseStore(self.path)
        for team,term in (('a',3),('b',1)):
            contract=ActiveContract(Offer(team,(2000000,)*term,3000000),'synthetic original')
            profile=self.minimum_profile(2026,team,term)
            self.store.create_team(team,Ledger.from_opening(OpeningBooks(contracts=(contract,),
                retained=(ChargeRecord('debt:'+team,(7,11,13),'synthetic retained schedule'),)),
                cap=10000000,roster_reserve=0,max_bonus_years=5,veteran_minimums=profile.floors(),veteran_minimum_profile=profile))
            self.store.initialize_cash(team,(CashObligation('contract:'+team,team,contract.nominal_cash,5000000,
                'synthetic payroll',(('signing_bonus',3000000),('base:0',2000000))),),source='synthetic complete cash')
        self.store.anchor_calendar(request_id='initial',league_year=2026,source='synthetic calendar',expected_revisions={'a':1,'b':1})
        self.store.migrate_generations(self.path)
        self.inputs=dict(request_id='roll-2027',from_year=2026,to_year=2027,source='synthetic declared league close',teams={})
        for team in ('a','b'):
            profile=self.minimum_profile(2027,team,3)
            self.inputs['teams'][team]=dict(expected_revision=2,next_cap=9000000,next_cap_source='synthetic next cap',
                roster_reserve=500,reserve_source='synthetic reserve',next_minimum_profile=profile.to_dict(),
                expired_generation_ids=[self.store.load_team(team).contract_identity(team).generation_id] if team=='b' else [],
                exclusions=sorted(FranchiseStore.YEAR_TRANSITION_EXCLUSIONS),source='synthetic explicit eligibility and closing exclusions')

    def test_versioned_player_context_tracks_calendar_without_relabeling_archive(self):
        before=self.store.player_context('a','a')
        self.store.advance_league_year(**self.inputs)
        for team in ('a','b'):
            context=self.store.player_context(team,team,context_format='calendar_v1')
            self.assertIsNone(context['contract_accounting'])
            nested=context['calendar_contract_context']
            self.assertEqual(nested['financial_revision'],context['financial_revision'])
            self.assertEqual(nested['league_year'],2027)
            self.assertEqual(nested['economic_archive']['contract']['elapsed_years'],0)
            self.assertEqual(nested,self.store.calendar_contract_context(team,nested['generation_id']))
            self.assertEqual(nested['calendar_accounting']['ownership_current'],team=='a')
            with self.assertRaises(Rejected): self.store.player_context(team,team)
        after=self.store.player_context('a','a',context_format='calendar_v1')
        for field in ('personality','relationships','promise_history','negotiation_history'):
            self.assertEqual(after[field],before[field])
        unknown=self.store.player_context('a','new',context_format='calendar_v1')
        self.assertIsNone(unknown['calendar_contract_context'])
        for value in (True,False,1,{},'unknown',''):
            with self.assertRaises(ValueError):
                self.store.player_context('a','a',context_format=value)

    def test_calendar_player_bridge_is_read_only_with_ai_disabled(self):
        self.store.advance_league_year(**self.inputs)
        def disabled(): raise AccessDisabled('synthetic shutdown')
        def unexpected(_): raise AssertionError('Read-only context invoked inference')
        bridge=Bridge(self.store,provider=unexpected,access_check=disabled)
        request=dict(protocol=1,request_id='calendar-player',operation='player_context',
            team_id='a',player_id='a',timeout_ms=1000,context_format='calendar_v1')
        before=self.path.read_bytes()
        result=bridge.handle(request)
        self.assertIsNone(result['error'])
        self.assertEqual(result['result'],self.store.player_context('a','a',context_format='calendar_v1'))
        self.assertEqual(bridge.handle({key:value for key,value in request.items() if key!='context_format'})['error'],
            'state_rejected')
        for value in (None,True,False,{},'unknown'):
            self.assertEqual(bridge.handle({**request,'context_format':value})['error'],'invalid_request')
        self.assertEqual(self.path.read_bytes(),before)

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
            item['next_minimum_profile']=self.minimum_profile(2028,team,2).to_dict()
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

    def test_calendar_wire_context_is_explicit_read_only_and_available_with_ai_off(self):
        from franchise.bridge import Bridge
        from franchise.control import AccessDisabled
        def forbidden(_): raise AssertionError('Read must not invoke inference')
        def disabled(): raise AccessDisabled('off')
        self.store.advance_league_year(**self.inputs)
        bridge=Bridge(self.store,provider=forbidden,access_check=disabled)
        raw=self.path.read_bytes()
        for team in ('a','b'):
            request=dict(protocol=1,request_id='calendar-'+team,operation='contract_context',
                team_id=team,generation_id=self.store.load_team(team).contract_identity(team).generation_id,
                timeout_ms=1000,context_format='calendar_v1')
            reply=bridge.handle(request)
            self.assertIsNone(reply['error'])
            self.assertEqual(reply['result']['format'],2)
            current=reply['result']['calendar_accounting']
            self.assertEqual(current['anchor_year'],2026)
            self.assertEqual(current['status'],'active' if team=='a' else 'expired')
            self.assertEqual(bridge.handle(dict(request,context_format='unknown'))['error'],'invalid_request')
            legacy=dict(request);del legacy['context_format']
            self.assertEqual(bridge.handle(legacy)['error'],'state_rejected')
        self.assertEqual(self.path.read_bytes(),raw)

    def test_postroll_new_signing_uses_birth_year_and_replays_through_next_transition(self):
        self.store.advance_league_year(**self.inputs)
        before=self.store.load_team('a').cash_snapshot()
        receipt=self.store.sign('a','new-2027',Offer('new',(2000000,2000000),1000000),3)
        restarted=FranchiseStore(self.path)
        ledger=restarted.load_team('a')
        gid=ledger.contract_identity('new').generation_id
        self.assertEqual(ledger.generation_calendar_view(gid).anchor_year,2027)
        self.assertEqual(ledger.active_contract('new').elapsed_years,0)
        self.assertEqual(ledger.charges,(5500011,5500013))
        self.assertEqual(ledger.cash_snapshot()['paid_total'],before['paid_total'])
        self.assertEqual(restarted.sign('a','new-2027',receipt.offer,3),receipt)
        for request,cash_id,component,amount in (('new-bonus','contract:new','signing_bonus',1000000),
                ('new-base','contract:new','base:0',2000000),('old-base','contract:a','base:1',2000000)):
            ledger=restarted.load_team('a')
            restarted.record_payment('a',request,cash_id,amount,expected_cash_revision=ledger._cash.revision,
                source='synthetic recorded payroll',payment_reference=request,component=component)
        inputs=copy.deepcopy(self.inputs);inputs.update(request_id='roll-2028-new',from_year=2027,to_year=2028)
        for team in ('a','b'):
            item=inputs['teams'][team];item['expected_revision']=restarted.load_team(team).revision
            item['expired_generation_ids']=[];item['next_minimum_profile']=self.minimum_profile(2028,team,2).to_dict()
        restarted.advance_league_year(**inputs)
        final=FranchiseStore(self.path).load_team('a')
        self.assertEqual(final.active_contract('a').elapsed_years,2)
        self.assertEqual(final.active_contract('new').elapsed_years,1)
        self.assertEqual(final.charges,(5500013,))
        self.assertEqual(final.cash_snapshot()['unpaid_total'],4000000)

    def test_postroll_bad_offer_and_calendar_posting_tamper_cannot_change_money(self):
        self.store.advance_league_year(**self.inputs)
        raw=self.path.read_bytes()
        for offer in (Offer('new',(1,),0),Offer('new',(20000000,),0)):
            with self.assertRaises(Rejected):self.store.sign('a','bad',offer,3)
            self.assertEqual(self.path.read_bytes(),raw)
        self.store.sign('a','good',Offer('new',(2000000,),0),3)
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute("SELECT id,payload FROM events WHERE request_key='sign:good'").fetchone()
            payload=json.loads(row[1]);payload['calendar_format']=True
            db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),row[0]));db.commit()
        with self.assertRaisesRegex(ValueError,'Calendar-aware'):self.store.load_team('a')

    def test_prior_unmarked_postroll_cash_history_keeps_exact_replay_compatibility(self):
        self.store.advance_league_year(**self.inputs)
        self.store.record_payment('a','prior-pay','contract:a',2000000,expected_cash_revision=0,
            source='synthetic recorded payroll',payment_reference='prior-pay',component='base:1')
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute("SELECT id,payload FROM events WHERE request_key='cash:payment:prior-pay'").fetchone()
            payload=json.loads(row[1]);del payload['calendar_format'];del payload['calendar_posting']
            db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),row[0]));db.commit()
        ledger=FranchiseStore(self.path).load_team('a')
        self.assertEqual(ledger.cash_snapshot()['paid_total'],7000000)
        self.assertEqual(ledger.active_contract('a').elapsed_years,1)
