from dataclasses import asdict,replace
from contextlib import closing
import json
import sqlite3
import unittest
from franchise.bridge import Bridge
from franchise.control import AccessDisabled
from franchise.store import FranchiseStore
from tests import test_return_store


class ReturnNegotiationTests(unittest.TestCase):
    def setUp(self):
        fixture=test_return_store.ReturnStoreTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.migrate();self.fixture=fixture;self.store=fixture.store
        self.contexts=[]
        def provider(context):
            self.contexts.append(context)
            return self.decision('accept')
        self.bridge=Bridge(self.store,provider=provider,access_check=lambda:None)
        scope=asdict(fixture.scope)
        scope.update(signed_on=fixture.scope.signed_on.isoformat(),
            first_regular_season_game=fixture.scope.first_regular_season_game.isoformat(),exclusions=sorted(fixture.scope.exclusions))
        self.scope=scope

    def decision(self,action,**changes):
        return json.dumps(dict(action=action,reason='synthetic sourced decision',salaries=None,
            signing_bonus=None,guaranteed_salaries=None,promise_goals=None,**changes))

    def request(self,**changes):
        return dict(protocol=1,operation='negotiate',request_id='return-ai',team_id='a',
            expected_revision=4,timeout_ms=1000,offer=self.fixture.offer.to_dict(),return_scope=self.scope,
            personality={},performance={},relationships={},**changes)

    def test_accept_promises_restart_recall_scope_and_historical_manual_exclusion(self):
        goal={'goal_id':'starts','metric':'starts','target':8,'importance':1,
            'window':'synthetic season','source':'synthetic agreement'}
        request=self.request();request['promise_goals']=[goal]
        result=self.bridge.handle(request)
        self.assertEqual(result['result']['outcome'],'signed',result)
        self.assertEqual(self.contexts[0]['return_scope'],self.scope)
        self.assertEqual(result['result']['evidence']['return_scope'],self.scope)
        ledger=self.store.load_team('a')
        self.assertIn('return-ai',ledger._promise_agreements)
        reopened=FranchiseStore(self.store.path)
        bridge=Bridge(reopened,provider=lambda _:self.fail('retry invoked provider'),access_check=lambda:None)
        self.assertEqual(bridge.handle(request),result)
        self.assertEqual(reopened.negotiation_history('a','v')[-1],result['result'])
        changed={**request,'return_scope':{**self.scope,'source':'changed'}}
        self.assertEqual(bridge.handle(changed)['error'],'state_rejected')
        ordinary=dict(request);ordinary.pop('return_scope')
        self.assertEqual(bridge.handle(ordinary)['error'],'state_rejected')

    def test_reject_counter_and_readonly_preview(self):
        preview=self.request();preview['operation']='preview'
        for key in ('personality','performance','relationships'):preview.pop(key)
        before=self.store.load_team('a').generation_snapshot()
        self.assertEqual(self.bridge.handle(preview)['result']['return_scope'],self.scope)
        self.assertEqual(self.store.load_team('a').generation_snapshot(),before)
        self.bridge.provider=lambda _:self.decision('reject')
        self.assertEqual(self.bridge.handle(self.request())['result']['outcome'],'player_rejected')
        self.bridge.provider=lambda _:json.dumps(dict(action='counter',reason='synthetic',salaries=[6,6,6],signing_bonus=3,
            guaranteed_salaries=[6,0,0],promise_goals=[]))
        counter=self.request();counter['request_id']='counter'
        result=self.bridge.handle(counter)
        self.assertEqual(result['result']['counter_validation']['status'],'eligible',result)
        self.assertEqual(self.store.load_team('a').generation_snapshot(),before)
        self.assertEqual(len(self.store.negotiation_history('a','v')),2)

    def test_kill_after_provider_and_ai_off_manual_return(self):
        enabled=[True]
        def access():
            if not enabled[0]:raise AccessDisabled('disabled')
        self.bridge.access_check=access
        def provider(_):enabled[0]=False;return self.decision('accept')
        self.bridge.provider=provider
        result=self.bridge.handle(self.request())
        self.assertEqual(result['error'],'ai_disabled')
        self.assertEqual(self.store.load_team('a').revision,4)
        manual=self.request();manual.update(operation='manual_sign',decision_mode='manual',request_id='manual-return')
        for key in ('personality','performance','relationships'):manual.pop(key)
        result=self.bridge.handle(manual)
        self.assertEqual(result['result']['outcome'],'signed',result)
        self.assertEqual(self.store.load_team('a').revision,5)
        self.assertEqual(self.bridge.handle(manual),result)

    def test_provider_revision_change_and_disconnect_never_commit_return(self):
        def provider(_):
            self.store.update_budget('a',cap=40,roster_reserve=0,expected_revision=4)
            return self.decision('accept')
        self.bridge.provider=provider
        result=self.bridge.handle(self.request())
        self.assertEqual(result['result']['outcome'],'accounting_rejected',result)
        self.assertEqual(len(self.store.contract_generations('a')['generations']),1)
        self.assertEqual(self.store.load_team('a').revision,5)
        disconnected=[False]
        def connection():
            if disconnected[0]:raise TimeoutError('client disconnected')
        self.bridge.connection_check=connection
        def provider(_):disconnected[0]=True;return self.decision('accept')
        self.bridge.provider=provider
        request=self.request();request.update(request_id='disconnected',expected_revision=5)
        self.assertEqual(self.bridge.handle(request)['error'],'timeout')
        self.assertEqual(len(self.store.contract_generations('a')['generations']),1)

    def test_return_manual_receipt_cannot_be_retried_as_ai_and_scope_cannot_change(self):
        manual=self.request();manual.update(operation='manual_sign',decision_mode='manual')
        for key in ('personality','performance','relationships'):manual.pop(key)
        self.assertEqual(self.bridge.handle(manual)['result']['outcome'],'signed')
        self.assertEqual(self.bridge.handle(self.request())['error'],'state_rejected')
        self.assertEqual(self.contexts,[])
        changed={**manual,'return_scope':{**self.scope,'source':'changed'}}
        self.assertEqual(self.bridge.handle(changed)['error'],'state_rejected')
