from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from franchise.vertex_provider import VertexProvider


class VertexTests(unittest.TestCase):
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
