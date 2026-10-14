"""Durable cumulative token admission with a synthetic SDK; no cloud calls."""
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock
from franchise.inference_budget import InferenceBudget, BudgetExceeded
from franchise.vertex_provider import VertexProvider


class VertexCumulativeBudgetTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'budget.sqlite'

    def provider(self, *, count=10, metadata=None, token_limit=110):
        budget=InferenceBudget(self.path,scope='synthetic-season',request_limit=10,token_limit=token_limit)
        models=SimpleNamespace(count_tokens=Mock(return_value=SimpleNamespace(total_tokens=count)),
            generate_content=Mock(return_value=SimpleNamespace(text='{}',
                candidates=[SimpleNamespace(finish_reason='STOP')],usage_metadata=metadata)))
        provider=VertexProvider(project='synthetic',location='global',model='synthetic-model',
            client=SimpleNamespace(models=models),request_budget=budget,max_input_tokens=10,max_output_tokens=100)
        return provider,models

    def test_exact_request_and_full_reservation_exhaust_next_attempt_after_restart(self):
        provider,models=self.provider(metadata=SimpleNamespace(prompt_token_count=10,
            candidates_token_count=5,thoughts_token_count=2,total_token_count=17))
        self.assertEqual(provider({'performance':'synthetic'}),'{}')
        count=models.count_tokens.call_args.kwargs;generation=models.generate_content.call_args.kwargs
        self.assertEqual((count['model'],count['contents']),(generation['model'],generation['contents']))
        self.assertEqual(count['config']['system_instruction'],generation['config']['system_instruction'])
        self.assertEqual(count['config']['generation_config'],{k:v for k,v in generation['config'].items() if k!='system_instruction'})
        status=provider.request_budget.status()
        self.assertEqual((status['reserved_tokens'],status['remaining_tokens'],status['attempts']),(110,0,1))
        # Lower actual usage never refunds the explicitly admitted ceiling.
        restarted,restarted_models=self.provider()
        with self.assertRaises(BudgetExceeded):restarted({})
        self.assertEqual(models.generate_content.call_count,1)
        self.assertEqual(restarted.request_budget.status()['attempts'],1)
        restarted_models.generate_content.assert_not_called()

    def test_unknown_usage_leaves_all_capacity_spent(self):
        provider,models=self.provider();provider({})
        status=provider.request_budget.status()
        self.assertEqual((status['reserved_tokens'],status['unknown_usage_count'],status['completed']),(110,1,1))
        with self.assertRaises(BudgetExceeded):provider({})
        self.assertEqual(models.generate_content.call_count,1)

    def test_sdk_failure_retains_capacity_without_private_error(self):
        provider,models=self.provider();models.generate_content.side_effect=RuntimeError('PRIVATE SDK ERROR')
        with self.assertRaisesRegex(RuntimeError,'Vertex AI request failed') as error:provider({})
        self.assertNotIn('PRIVATE',str(error.exception))
        self.assertEqual(provider.request_budget.status()['reserved_tokens'],110)
        with self.assertRaises(BudgetExceeded):provider({})
        self.assertEqual(models.generate_content.call_count,1)

    def test_missing_invalid_or_overlimit_count_never_reserves_or_generates(self):
        for count in (None,True,-1,1.5,11):
            with self.subTest(count=count):
                provider,models=self.provider(count=count)
                with self.assertRaisesRegex(ValueError,'token count'):provider({})
                models.generate_content.assert_not_called()
                status=provider.request_budget.status()
                self.assertEqual((status['attempts'],status['reserved_tokens']),(0,0))

    def test_observed_overrun_is_persisted_and_prevents_return_and_later_generation(self):
        provider,models=self.provider(metadata=SimpleNamespace(prompt_token_count=10,total_token_count=111))
        with self.assertRaises(ValueError):provider({})
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT completed,total_token_count FROM attempts').fetchall(),[(1,111)])
            self.assertEqual(db.execute('SELECT input_tokens,output_tokens FROM token_reservations').fetchall(),[(10,100)])
        with self.assertRaises(ValueError):provider({})
        self.assertEqual(models.generate_content.call_count,1)

    def test_overrun_cannot_commit_a_financial_decision(self):
        from franchise.cap import Ledger,Offer
        from franchise.negotiation import Negotiation
        provider,models=self.provider(metadata=SimpleNamespace(total_token_count=111))
        ledger=Ledger(cap=100,existing_charges=(0,),roster_reserve=0,max_bonus_years=5,veteran_minimums={'p':(1,)})
        session=Negotiation(ledger,player_id='p',personality={},performance={'source':'synthetic'},relationships={},access_check=lambda:None)
        before=ledger.financial_snapshot()
        with self.assertRaises(ValueError):session.respond('overrun',Offer('p',(10,),0),provider,expected_revision=0)
        self.assertEqual(ledger.financial_snapshot(),before)
        self.assertEqual(models.generate_content.call_count,1)

    def test_kill_after_reserve_prevents_generation_and_does_not_refund(self):
        provider,models=self.provider();checks=[]
        def access():
            checks.append(True)
            if len(checks)==2:raise RuntimeError('synthetic disabled after reservation')
        with self.assertRaisesRegex(RuntimeError,'disabled after reservation'):provider({},before_generate=access)
        models.generate_content.assert_not_called()
        status=provider.request_budget.status()
        self.assertEqual((status['reserved_tokens'],status['completed'],status['pending']),(110,1,0))
        self.assertFalse(provider.last_usage['sdk_invoked'])
        with self.assertRaises(BudgetExceeded):provider({})
        models.generate_content.assert_not_called()

    def test_cumulative_token_budget_requires_input_preflight(self):
        budget=InferenceBudget(self.path,scope='synthetic-season',request_limit=10,token_limit=110)
        with self.assertRaises(ValueError):
            VertexProvider(project='synthetic',location='global',model='synthetic-model',
                client=SimpleNamespace(),request_budget=budget)
