from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from franchise.vertex_provider import VertexProvider


class VertexTests(unittest.TestCase):
    def test_rate_window_blocks_sdk_and_preserves_failed_attempts(self):
        client = SimpleNamespace(models=SimpleNamespace(generate_content=Mock(side_effect=RuntimeError('private'))))
        provider = VertexProvider(project='p', location='global', model='m', client=client,
                                  max_requests_per_minute=1)
        with patch('franchise.vertex_provider.time.monotonic', return_value=100):
            with self.assertRaises(RuntimeError): provider({})
        with patch('franchise.vertex_provider.time.monotonic', return_value=159.999):
            with self.assertRaisesRegex(ValueError, 'rate exceeded'): provider({})
        self.assertEqual(client.models.generate_content.call_count, 1)
        self.assertFalse(provider.last_usage['sdk_invoked'])
        self.assertEqual(provider.last_usage['outcome'], 'preflight_rejected')
        with patch('franchise.vertex_provider.time.monotonic', return_value=160):
            with self.assertRaises(RuntimeError): provider({})
        self.assertEqual(client.models.generate_content.call_count, 2)

    def test_invalid_rate_limit_rejects_before_client_creation(self):
        for value in (True, 0, -1, 1.5, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                VertexProvider(project='p', location='global', model='m', max_requests_per_minute=value)

    def provider(self, response):
        client = SimpleNamespace(models=SimpleNamespace(generate_content=Mock(return_value=response)))
        return VertexProvider(project="test-project", location="global", model="test-model", client=client)

    def test_structured_response_uses_google_model_and_context(self):
        response = SimpleNamespace(candidates=[SimpleNamespace(finish_reason="STOP")], text='{"action":"reject"}')
        provider = self.provider(response)
        self.assertEqual(provider({"player_id": "p"}), response.text)
        call = provider._client.models.generate_content.call_args.kwargs
        self.assertEqual(call["model"], "test-model")
        self.assertEqual(call["config"]["response_mime_type"], "application/json")
        self.assertIn("p", call["contents"])

    def test_blocked_and_truncated_responses_rejected(self):
        for reason in ["SAFETY", "MAX_TOKENS", None]:
            provider = self.provider(SimpleNamespace(candidates=[SimpleNamespace(finish_reason=reason)], text="{}"))
            with self.assertRaises(ValueError):
                provider({})

    def test_cloud_failure_cannot_echo_sensitive_error(self):
        provider = self.provider(None)
        provider._client.models.generate_content.side_effect = RuntimeError("sensitive-value")
        with self.assertRaises(RuntimeError) as caught:
            provider({})
        self.assertNotIn("sensitive-value", str(caught.exception))

    def test_missing_configuration_rejected_before_sdk_import(self):
        with self.assertRaises(ValueError):
            VertexProvider(project="", location="global", model="test")

    def test_draft_schema_and_instructions_do_not_change_default_negotiation(self):
        from franchise.draft import DRAFT_INSTRUCTIONS, DRAFT_VERTEX_SCHEMA
        from franchise.vertex_provider import VERTEX_SCHEMA
        from franchise.prompt import INSTRUCTIONS
        response = SimpleNamespace(candidates=[SimpleNamespace(finish_reason="STOP")], text='{}')
        client = SimpleNamespace(models=SimpleNamespace(generate_content=Mock(return_value=response)))
        provider = VertexProvider(project='test', location='global', model='test', client=client,
                                  instructions=DRAFT_INSTRUCTIONS, response_schema=DRAFT_VERTEX_SCHEMA)
        provider({'purpose':'draft_comparison'})
        config = client.models.generate_content.call_args.kwargs['config']
        self.assertEqual(config['response_schema'], DRAFT_VERTEX_SCHEMA)
        self.assertEqual(config['system_instruction'], DRAFT_INSTRUCTIONS)
        default = self.provider(response)
        default({})
        config = default._client.models.generate_content.call_args.kwargs['config']
        self.assertEqual(config['response_schema'], VERTEX_SCHEMA)
        self.assertEqual(config['system_instruction'], INSTRUCTIONS)

    def test_context_preflight_enforces_exact_escaped_byte_limit_without_sdk_calls(self):
        import json
        response=SimpleNamespace(candidates=[SimpleNamespace(finish_reason='STOP')],text='{}')
        client=SimpleNamespace(models=SimpleNamespace(generate_content=Mock(return_value=response)))
        context={'source':'é'}
        size=len(json.dumps(context,allow_nan=False).encode('utf-8'))
        provider=VertexProvider(project='p',location='global',model='m',client=client,max_context_bytes=size)
        provider(context)
        self.assertEqual(client.models.generate_content.call_args.kwargs['contents'],json.dumps(context))
        client.models.generate_content.reset_mock()
        for invalid in ({'source':'éx'}, {'source':float('nan')}, [], {'source':object()}):
            with self.subTest(context=type(invalid).__name__),self.assertRaises((ValueError,TypeError)):
                provider(invalid)
            client.models.generate_content.assert_not_called()
        for invalid in (True,0,-1,1.0):
            with self.subTest(limit=invalid),self.assertRaises(ValueError):
                VertexProvider(project='p',location='global',model='m',client=client,max_context_bytes=invalid)

    def test_oversized_context_cannot_commit_deal_and_manual_cap_enforcement_remains(self):
        from franchise.cap import Ledger,Offer
        from franchise.negotiation import Negotiation
        ledger=Ledger(cap=100,existing_charges=(0,),roster_reserve=0,max_bonus_years=5,veteran_minimums={'p':(1,)})
        session=Negotiation(ledger,player_id='p',personality={},performance={'source':'synthetic'},relationships={},access_check=lambda:None)
        response=SimpleNamespace(candidates=[SimpleNamespace(finish_reason='STOP')],text='{}')
        client=SimpleNamespace(models=SimpleNamespace(generate_content=Mock(return_value=response)))
        provider=VertexProvider(project='p',location='global',model='m',client=client,max_context_bytes=4)
        before=ledger.financial_snapshot()
        with self.assertRaisesRegex(ValueError,'no inference submitted'):
            session.respond('too-large',Offer('p',(10,),0),provider,expected_revision=0)
        self.assertEqual(ledger.financial_snapshot(),before)
        client.models.generate_content.assert_not_called()
        ledger.sign('manual',Offer('p',(10,),0),0)
        self.assertEqual(ledger.charges,(10,))

    def test_usage_snapshot_preserves_unknown_counts_and_blocked_response_usage(self):
        metadata=SimpleNamespace(prompt_token_count=10,candidates_token_count=3,total_token_count=18,
            cached_content_token_count=None,thoughts_token_count=5,tool_use_prompt_token_count=0)
        response=SimpleNamespace(candidates=[SimpleNamespace(finish_reason='STOP')],text='{}',usage_metadata=metadata)
        provider=self.provider(response)
        self.assertIsNone(provider.last_usage)
        provider({'player_id':'p'})
        usage=provider.last_usage
        self.assertEqual(usage['tokens']['total_token_count'],18)
        self.assertEqual(usage['tokens']['thoughts_token_count'],5)
        self.assertIsNone(usage['tokens']['cached_content_token_count'])
        self.assertEqual(usage['outcome'],'response_accepted')
        self.assertIsNone(usage['estimated_cost'])
        usage['tokens']['prompt_token_count']=999
        self.assertEqual(provider.last_usage['tokens']['prompt_token_count'],10)
        response.candidates[0].finish_reason='MAX_TOKENS'
        with self.assertRaises(ValueError):provider({})
        self.assertEqual(provider.last_usage['outcome'],'response_rejected')
        self.assertEqual(provider.last_usage['tokens']['total_token_count'],18)
        provider._client.models.generate_content.side_effect=RuntimeError('SECRET')
        with self.assertRaises(RuntimeError):provider({})
        self.assertEqual(provider.last_usage['outcome'],'request_failed')
        self.assertTrue(provider.last_usage['sdk_invoked'])
        self.assertTrue(all(value is None for value in provider.last_usage['tokens'].values()))
        self.assertNotIn('SECRET',str(provider.last_usage))
        with self.assertRaises(ValueError):provider([])
        self.assertFalse(provider.last_usage['sdk_invoked'])
        self.assertEqual(provider.last_usage['outcome'],'preflight_rejected')

    def test_usage_invalid_or_missing_counters_stay_unknown_without_changing_decision(self):
        response=SimpleNamespace(candidates=[SimpleNamespace(finish_reason='STOP')],text='{}',
            usage_metadata=SimpleNamespace(prompt_token_count=True,candidates_token_count=-1,total_token_count=2.5))
        provider=self.provider(response)
        self.assertEqual(provider({}),'{}')
        self.assertTrue(all(value is None for value in provider.last_usage['tokens'].values()))
        self.assertNotIn('player_id',provider.last_usage)

    def test_concurrent_usage_is_published_as_one_completed_call_snapshot(self):
        import json
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        entered,released=Event(),Event()
        def generate(**kwargs):
            first=json.loads(kwargs['contents'])['tag']=='first'
            if first:
                entered.set()
                if not released.wait(2):raise RuntimeError('test wait expired')
            count=11 if first else 22
            return SimpleNamespace(candidates=[SimpleNamespace(finish_reason='STOP')],text='{}',
                usage_metadata=SimpleNamespace(total_token_count=count))
        client=SimpleNamespace(models=SimpleNamespace(generate_content=generate))
        provider=VertexProvider(project='p',location='global',model='m',client=client)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(provider,{'tag':'first'})
            try:
                self.assertTrue(entered.wait(2))
                self.assertIsNone(provider.last_usage)
                provider({'tag':'second'})
                second=provider.last_usage
                self.assertEqual(second['tokens']['total_token_count'],22)
            finally:released.set()
            self.assertEqual(future.result(timeout=2),'{}')
        self.assertEqual(provider.last_usage['tokens']['total_token_count'],11)
        self.assertEqual(second['tokens']['total_token_count'],22)
