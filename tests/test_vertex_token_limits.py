"""Count full request before reserving paid generation; synthetic SDK only."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock
from franchise.inference_budget import InferenceBudget
from franchise.vertex_provider import VertexProvider


class VertexTokenLimitTests(unittest.TestCase):
    def provider(self,count=10,**options):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        budget=InferenceBudget(Path(directory.name)/'usage.sqlite',scope='season',request_limit=2)
        models=SimpleNamespace(count_tokens=Mock(return_value=SimpleNamespace(total_tokens=count)),
            generate_content=Mock(return_value=SimpleNamespace(candidates=[SimpleNamespace(finish_reason='STOP')],text='{}')))
        provider=VertexProvider(project='p',location='global',model='m',client=SimpleNamespace(models=models),
            request_budget=budget,max_input_tokens=10,max_output_tokens=100,**options)
        return provider,models

    def test_count_includes_exact_contents_instructions_and_schema(self):
        provider,models=self.provider()
        self.assertEqual(provider({'player':'synthetic'}),'{}')
        count=models.count_tokens.call_args.kwargs;generation=models.generate_content.call_args.kwargs
        self.assertEqual(count['model'],generation['model'])
        self.assertEqual(count['contents'],generation['contents'])
        self.assertEqual(count['config']['system_instruction'],generation['config']['system_instruction'])
        self.assertEqual(count['config']['generation_config'],{k:v for k,v in generation['config'].items() if k!='system_instruction'})
        self.assertEqual(generation['config']['max_output_tokens'],100)
        self.assertEqual(provider.request_budget.status()['attempts'],1)

    def test_invalid_overlimit_and_unknown_counts_never_generate_or_reserve(self):
        for value in (11,None,True,-1,1.5):
            with self.subTest(value=value):
                provider,models=self.provider(value)
                with self.assertRaisesRegex(ValueError,'token count'):provider({})
                models.generate_content.assert_not_called()
                self.assertEqual(provider.request_budget.status()['attempts'],0)
                self.assertFalse(provider.last_usage['sdk_invoked'])

    def test_count_failure_is_sanitized_and_byte_rejection_skips_count(self):
        provider,models=self.provider();models.count_tokens.side_effect=RuntimeError('PRIVATE CLOUD ERROR')
        with self.assertRaisesRegex(RuntimeError,'token counting failed') as error:provider({})
        self.assertNotIn('PRIVATE',str(error.exception));models.generate_content.assert_not_called()
        self.assertEqual(provider.request_budget.status()['attempts'],0)
        provider,models=self.provider(max_context_bytes=2)
        with self.assertRaisesRegex(ValueError,'size limit'):provider({'large':'context'})
        models.count_tokens.assert_not_called();models.generate_content.assert_not_called()

    def test_invalid_limits_reject_before_client_initialization(self):
        for field in ('max_input_tokens','max_output_tokens'):
            for value in (True,0,-1,1.5,2**31):
                with self.subTest(field=field,value=value),self.assertRaises(ValueError):
                    VertexProvider(project='p',location='global',model='m',**{field:value})

    def test_expired_access_after_count_cannot_start_paid_generation(self):
        provider,models=self.provider()
        def denied():
            self.assertEqual(models.count_tokens.call_count,1)
            raise RuntimeError('request expired or disabled')
        with self.assertRaisesRegex(RuntimeError,'expired or disabled'):
            provider({},before_generate=denied)
        models.generate_content.assert_not_called()
        self.assertEqual(provider.request_budget.status()['attempts'],0)

    def test_negotiation_rechecks_request_access_after_count_without_financial_change(self):
        from franchise.cap import Ledger,Offer
        from franchise.negotiation import Negotiation
        provider,models=self.provider()
        ledger=Ledger(cap=100,existing_charges=(0,),roster_reserve=0,max_bonus_years=5,veteran_minimums={'p':(1,)})
        def access():
            if models.count_tokens.called:raise RuntimeError('request disabled during count')
        session=Negotiation(ledger,player_id='p',personality={},performance={'source':'synthetic'},relationships={},access_check=access)
        before=ledger.financial_snapshot()
        with self.assertRaisesRegex(RuntimeError,'disabled during count'):
            session.respond('count-disabled',Offer('p',(10,),0),provider,expected_revision=0)
        models.generate_content.assert_not_called()
        self.assertEqual(ledger.financial_snapshot(),before)
        self.assertEqual(provider.request_budget.status()['attempts'],0)
        ledger.sign('manual',Offer('p',(10,),0),0)
        self.assertEqual(ledger.charges,(10,))

    def test_access_expiring_during_reservation_keeps_attempt_without_generation(self):
        provider,models=self.provider();checks=[]
        def access():
            checks.append(True)
            if len(checks)==2:raise RuntimeError('expired during reservation')
        with self.assertRaisesRegex(RuntimeError,'expired during reservation'):
            provider({},before_generate=access)
        models.generate_content.assert_not_called()
        self.assertFalse(provider.last_usage['sdk_invoked'])
        status=provider.request_budget.status()
        self.assertEqual((status['attempts'],status['completed'],status['pending']),(1,1,0))
        self.assertEqual(status['unknown_usage_count'],1)
