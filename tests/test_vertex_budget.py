from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock,patch
from franchise.inference_budget import InferenceBudget,BudgetExceeded,TOKEN_FIELDS
from franchise.vertex_provider import VertexProvider


class VertexBudgetTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'usage.sqlite'

    def provider(self,client,limit=1,**options):
        return VertexProvider(project='p',location='global',model='m',client=client,
            request_budget=InferenceBudget(self.path,scope='franchise:season-2026',request_limit=limit),**options)

    def client(self,**changes):
        response=dict(candidates=[SimpleNamespace(finish_reason='STOP')],text='{}',
            usage_metadata=SimpleNamespace(prompt_token_count=100,candidates_token_count=20,total_token_count=125,
                cached_content_token_count=0,thoughts_token_count=5,tool_use_prompt_token_count=0))
        response.update(changes)
        return SimpleNamespace(models=SimpleNamespace(generate_content=Mock(return_value=SimpleNamespace(**response))))

    def test_restart_cannot_reset_ceiling_and_usage_is_durable(self):
        client=self.client();first=self.provider(client)
        self.assertEqual(first({'player_id':'PRIVATE PLAYER'}),'{}')
        status=first.request_budget.status()
        self.assertEqual((status['attempts'],status['completed'],status['pending']),(1,1,0))
        self.assertEqual(status['known_token_usage']['thoughts_token_count'],5)
        self.assertEqual(status['known_token_usage']['total_token_count'],125)
        self.assertEqual(status['unknown_usage_count'],0)
        restarted=self.provider(client)
        with self.assertRaises(BudgetExceeded):restarted({})
        self.assertEqual(client.models.generate_content.call_count,1)
        self.assertFalse(restarted.last_usage['sdk_invoked'])
        self.assertNotIn(b'PRIVATE PLAYER',self.path.read_bytes())

    def test_sdk_failure_and_blocked_response_still_consume_reserved_attempt(self):
        client=self.client();client.models.generate_content.side_effect=RuntimeError('SECRET CLOUD ERROR')
        provider=self.provider(client)
        with self.assertRaisesRegex(RuntimeError,'Vertex AI request failed'):provider({})
        self.assertEqual(provider.request_budget.status()['attempts'],1)
        self.assertEqual(provider.request_budget.status()['unknown_usage_count'],1)
        with self.assertRaises(BudgetExceeded):self.provider(client)({})
        self.assertEqual(client.models.generate_content.call_count,1)
        self.assertNotIn(b'SECRET CLOUD ERROR',self.path.read_bytes())
        other=Path(str(self.path)+'.blocked')
        budget=InferenceBudget(other,scope='season',request_limit=1)
        blocked=self.client(candidates=[SimpleNamespace(finish_reason='SAFETY')])
        provider=VertexProvider(project='p',location='global',model='m',client=blocked,request_budget=budget)
        with self.assertRaises(ValueError):provider({})
        self.assertEqual(budget.status()['completed'],1)
        with self.assertRaises(BudgetExceeded):provider({})
        self.assertEqual(blocked.models.generate_content.call_count,1)

    def test_context_preflight_and_rate_denial_do_not_consume_durable_attempt(self):
        client=self.client();provider=self.provider(client,limit=2,max_context_bytes=2,max_requests_per_minute=1)
        with self.assertRaisesRegex(ValueError,'size limit'):provider({'too':'large'})
        self.assertEqual(provider.request_budget.status()['attempts'],0)
        with patch('franchise.vertex_provider.time.monotonic',return_value=100):
            provider({})
            with self.assertRaisesRegex(ValueError,'rate exceeded'):provider({})
        self.assertEqual(provider.request_budget.status()['attempts'],1)
        self.assertEqual(client.models.generate_content.call_count,1)

    def test_completion_failure_prevents_return_and_pending_reservation_stays_spent(self):
        provider=self.provider(self.client())
        with patch.object(provider.request_budget,'complete',side_effect=RuntimeError('synthetic persistence failure')):
            with self.assertRaisesRegex(RuntimeError,'persistence failure'):provider({})
        self.assertEqual(provider.request_budget.status()['pending'],1)
        with self.assertRaises(BudgetExceeded):self.provider(self.client())({})
