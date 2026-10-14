"""Live factories require explicit durable request ceilings before credentials."""
from contextlib import ExitStack
import io
import json
import os
import sqlite3
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock,patch
from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger
from franchise.inference_budget import BudgetExceeded,InferenceBudget
from franchise.runtime_budget import runtime_request_budget
from franchise.store import FranchiseStore


class RuntimeBudgetTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.directory=Path(directory.name);self.path=self.directory/'franchise.sqlite';self.budget_path=self.directory/'usage.sqlite'
        self.store=FranchiseStore(self.path)
        self.store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(1,)}))

    def budget(self,**changes):
        args=dict(database=self.path,budget_database=self.budget_path,scope='franchise/2028',request_limit=2)
        return runtime_request_budget(**{**args,**changes})

    def manual(self):
        return dict(protocol=1,request_id='manual',operation='manual_sign',team_id='a',
            offer=dict(player_id='v',salaries=[10],signing_bonus=0),expected_revision=0,timeout_ms=1000,decision_mode='manual')

    def budget_args(self):
        return ['--ai-budget-database',str(self.budget_path),'--ai-budget-scope','franchise/2028','--ai-request-limit','2']

    def test_helper_restart_immutable_policy_and_path_aliases(self):
        budget=self.budget();budget.reserve(model='synthetic-model')
        self.assertEqual(self.budget().status()['attempts'],1)
        with self.assertRaises(ValueError):self.budget(request_limit=3)
        before=self.path.read_bytes()
        symlink=self.directory/'symlink.sqlite';symlink.symlink_to(self.path)
        hardlink=self.directory/'hardlink.sqlite';os.link(self.path,hardlink)
        for path in (self.path,symlink,hardlink):
            with self.subTest(path=path),self.assertRaises(ValueError):self.budget(budget_database=path)
        for changes in ({'budget_database':None},{'scope':None},{'scope':''},{'request_limit':None},
                        {'request_limit':True},{'request_limit':0},{'budget_database':':memory:'}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.budget(**changes)
        self.assertEqual(self.path.read_bytes(),before)
        malformed=self.directory/'invalid.sqlite';malformed.write_text('not a SQLite database')
        with self.assertRaises(sqlite3.DatabaseError):self.budget(budget_database=malformed)

    def test_missing_or_invalid_sidecar_budget_never_creates_credentials_or_sdk(self):
        from franchise.sidecar import main
        for extra in ([],['--ai-budget-database',str(self.path),'--ai-budget-scope','franchise/2028','--ai-request-limit','2']):
            stdout=io.StringIO();stderr=io.StringIO()
            messages=[dict(protocol=1,request_id='hello',operation='hello'),self.manual()]
            with patch.object(sys,'argv',['sidecar','--database',str(self.path),'--provider','vertex','--impersonate-runtime',*extra]),\
                 patch.object(sys,'stdin',io.StringIO(''.join(json.dumps(item)+'\n' for item in messages))),\
                 patch.object(sys,'stdout',stdout),patch.object(sys,'stderr',stderr),\
                 patch('franchise.google_credentials.runtime_credentials') as credentials,\
                 patch('franchise.vertex_provider.VertexProvider') as sdk:
                main()
            self.assertFalse(credentials.called);self.assertFalse(sdk.called)
            replies=[json.loads(line) for line in stdout.getvalue().splitlines()]
            self.assertEqual(replies[0]['error'],'ai_disabled');self.assertIsNone(replies[1]['error'])
            self.assertEqual(replies[1]['result']['outcome'],'signed')
        self.assertFalse(self.budget_path.exists())

    def test_missing_web_budget_still_constructs_manual_server_without_credentials(self):
        from franchise.web import main
        server=MagicMock()
        with patch.object(sys,'argv',['web','--database',str(self.path),'--team','a','--ai','vertex-runtime']),\
             patch('franchise.web.make_server',return_value=server) as factory,\
             patch('franchise.google_credentials.runtime_credentials') as credentials,\
             patch('franchise.vertex_provider.VertexProvider') as sdk:
            main()
        self.assertFalse(credentials.called);self.assertFalse(sdk.called)
        server.serve_forever.assert_called_once();server.server_close.assert_called_once()
        args=factory.call_args.kwargs
        bridge=Bridge(self.store,provider=args['negotiation_provider'],access_check=args['ai_access_check'])
        self.assertEqual(bridge.handle(dict(protocol=1,request_id='hello',operation='hello'))['error'],'ai_disabled')
        self.assertIsNone(bridge.handle(self.manual())['error'])
        self.assertFalse(self.budget_path.exists())

    def test_both_live_factories_pass_distinct_instances_of_same_durable_scope(self):
        from franchise.sidecar import main as sidecar_main
        from franchise.web import main as web_main
        provider=MagicMock();server=MagicMock()
        with ExitStack() as stack:
            credentials=stack.enter_context(patch('franchise.google_credentials.runtime_credentials',return_value='synthetic credentials'))
            sdk=stack.enter_context(patch('franchise.vertex_provider.VertexProvider',return_value=provider))
            stack.enter_context(patch('franchise.sidecar.GoogleControl',return_value=lambda:None))
            stack.enter_context(patch('franchise.control.GoogleControl',return_value=lambda:None))
            serve=stack.enter_context(patch('franchise.sidecar.serve'))
            stack.enter_context(patch('franchise.web.make_server',return_value=server))
            with patch.object(sys,'argv',['sidecar','--database',str(self.path),'--provider','vertex','--impersonate-runtime',*self.budget_args()]):
                sidecar_main()
            sidecar_budget=sdk.call_args.kwargs['request_budget']
            self.assertIsInstance(sidecar_budget,InferenceBudget)
            self.assertIs(serve.call_args.args[0].provider,provider)
            sidecar_budget.reserve(model='synthetic-model')
            with patch.object(sys,'argv',['web','--database',str(self.path),'--team','a','--ai','vertex-runtime',*self.budget_args()]):
                web_main()
            web_budget=sdk.call_args.kwargs['request_budget']
            self.assertIsInstance(web_budget,InferenceBudget);self.assertIsNot(web_budget,sidecar_budget)
            self.assertEqual(web_budget.path,sidecar_budget.path);self.assertEqual(web_budget.scope,'franchise/2028')
            self.assertEqual(web_budget.request_limit,2);self.assertEqual(web_budget.status()['attempts'],1)
            web_budget.reserve(model='synthetic-model')
            with self.assertRaises(BudgetExceeded):sidecar_budget.reserve(model='synthetic-model')
            self.assertEqual(sdk.call_count,2);self.assertEqual(credentials.call_count,4)

    def test_offline_factories_do_not_need_or_create_budget(self):
        from franchise.sidecar import main as sidecar_main
        from franchise.web import main as web_main
        stdout=io.StringIO()
        with patch.object(sys,'argv',['sidecar','--database',str(self.path),'--provider','offline-fixture']),\
             patch.object(sys,'stdin',io.StringIO(json.dumps(dict(protocol=1,request_id='hello',operation='hello'))+'\n')),\
             patch.object(sys,'stdout',stdout),patch('franchise.runtime_budget.runtime_request_budget') as budget:
            sidecar_main()
        self.assertFalse(budget.called);self.assertIsNone(json.loads(stdout.getvalue())['error'])
        with patch.object(sys,'argv',['web','--database',str(self.path),'--team','a','--ai','disabled']),\
             patch('franchise.web.make_server',return_value=MagicMock()),\
             patch('franchise.runtime_budget.runtime_request_budget') as budget:
            web_main()
        self.assertFalse(budget.called);self.assertFalse(self.budget_path.exists())

    def test_explicit_token_policy_is_shared_by_both_live_runtime_factories(self):
        from franchise.sidecar import main as sidecar_main
        from franchise.web import main as web_main
        with ExitStack() as stack:
            stack.enter_context(patch('franchise.google_credentials.runtime_credentials',return_value='synthetic credentials'))
            sdk=stack.enter_context(patch('franchise.vertex_provider.VertexProvider',return_value=MagicMock()))
            stack.enter_context(patch('franchise.sidecar.GoogleControl',return_value=lambda:None))
            stack.enter_context(patch('franchise.control.GoogleControl',return_value=lambda:None))
            stack.enter_context(patch('franchise.sidecar.serve'))
            stack.enter_context(patch('franchise.web.make_server',return_value=MagicMock()))
            with patch.object(sys,'argv',['sidecar','--database',str(self.path),'--provider','vertex','--impersonate-runtime',*self.budget_args(),'--ai-token-limit','30']):
                sidecar_main()
            first=sdk.call_args.kwargs['request_budget']
            self.assertEqual(sdk.call_args.kwargs['max_input_tokens'],16384)
            first.reserve(model='synthetic-model',input_tokens=5,output_tokens=10)
            with patch.object(sys,'argv',['web','--database',str(self.path),'--team','a','--ai','vertex-runtime',*self.budget_args(),'--ai-token-limit','30']):
                web_main()
            second=sdk.call_args.kwargs['request_budget']
            self.assertEqual(second.token_limit,30)
            self.assertEqual(second.status()['reserved_tokens'],15)
            second.reserve(model='synthetic-model',input_tokens=5,output_tokens=10)
            self.assertEqual(first.status()['remaining_tokens'],0)
            with self.assertRaises(BudgetExceeded):first.reserve(model='synthetic-model',input_tokens=0,output_tokens=1)
