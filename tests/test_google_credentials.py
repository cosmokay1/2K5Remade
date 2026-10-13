import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from franchise.google_credentials import runtime_credentials
from franchise.control import GoogleControl, AccessDisabled
from franchise.vertex_provider import VertexProvider


class RuntimeCredentialTests(unittest.TestCase):
    def test_short_lived_target_credentials_use_source_adc_without_keys(self):
        source, credential = object(), object()
        factory = Mock(return_value=credential)
        auth = SimpleNamespace(default=Mock(return_value=(source, "llm-2k5")),
                               impersonated_credentials=SimpleNamespace(Credentials=factory))
        with patch.dict("sys.modules", {"google": SimpleNamespace(auth=auth), "google.auth": auth}):
            result = runtime_credentials("llm-2k5", "franchise-runtime@llm-2k5.iam.gserviceaccount.com")
        self.assertIs(result, credential)
        self.assertIs(factory.call_args.kwargs["source_credentials"], source)
        self.assertEqual(factory.call_args.kwargs["lifetime"], 900)

    def test_invalid_target_or_adc_failure_cannot_fall_back_or_leak(self):
        with self.assertRaises(ValueError):
            runtime_credentials("llm-2k5", "other@other-project.iam.gserviceaccount.com")
        auth = SimpleNamespace(default=Mock(side_effect=RuntimeError("SECRET")),
                               impersonated_credentials=SimpleNamespace(Credentials=Mock()))
        with patch.dict("sys.modules", {"google": SimpleNamespace(auth=auth), "google.auth": auth}):
            with self.assertRaises(RuntimeError) as caught:
                runtime_credentials("llm-2k5", "franchise-runtime@llm-2k5.iam.gserviceaccount.com")
        self.assertNotIn("SECRET", str(caught.exception))
        self.assertFalse(auth.impersonated_credentials.Credentials.called)

    def test_owner_cli_and_runtime_credentials_are_mutually_exclusive(self):
        with self.assertRaises(ValueError):
            GoogleControl(project="p", bucket="b", object_name="o", credentials=object(), use_gcloud_login=True)
        with self.assertRaises(ValueError):
            VertexProvider(project="p", location="global", model="m", client=object(), credentials=object(), use_gcloud_login=True)

    def test_vertex_sdk_receives_selected_runtime_credentials(self):
        credentials = object()
        client_factory = Mock(return_value=object())
        google = SimpleNamespace(genai=SimpleNamespace(Client=client_factory))
        with patch.dict("sys.modules", {"google": google}):
            VertexProvider(project="p", location="global", model="m", credentials=credentials)
        self.assertIs(client_factory.call_args.kwargs["credentials"], credentials)

    def control_modules(self, http=None):
        auth = SimpleNamespace(default=Mock(side_effect=AssertionError("Owner ADC fallback")))
        request_factory = Mock(return_value=http or Mock())
        return {"google": SimpleNamespace(auth=auth), "google.auth": auth,
                "google.auth.transport.requests": SimpleNamespace(Request=request_factory)}, auth, request_factory

    def test_cached_runtime_token_never_caches_enabled_switch_grant(self):
        credentials = SimpleNamespace(valid=True, token="synthetic-runtime-token", refresh=Mock())
        modules, auth, _ = self.control_modules()
        enabled = dict(protocol=1, enabled=True, expires_at="2099-01-01T00:00:00+00:00")
        disabled = {**enabled, "enabled": False}
        control = GoogleControl(project="p", bucket="b", object_name="o", credentials=credentials)
        with patch.dict("sys.modules", modules), patch("franchise.control.urlopen", side_effect=[
                io.StringIO(json.dumps(enabled)), io.StringIO(json.dumps(disabled)), TimeoutError()]) as fetch:
            control()
            with self.assertRaises(AccessDisabled):
                control()
            with self.assertRaises(AccessDisabled):
                control()
        self.assertEqual(fetch.call_count, 3)
        self.assertFalse(auth.default.called)
        self.assertFalse(credentials.refresh.called)

    def test_runtime_refresh_timeout_is_bounded_and_expired_result_denies(self):
        http = Mock()
        modules, auth, _ = self.control_modules(http)
        credentials = SimpleNamespace(valid=False, token="stale", refresh=None)
        def refresh(request):
            request("synthetic-iam-endpoint", method="POST", timeout=120)
            # A refresh that leaves credentials expired must never send old token.
        credentials.refresh = refresh
        control = GoogleControl(project="p", bucket="b", object_name="o", credentials=credentials)
        with patch.dict("sys.modules", modules), patch("franchise.control.urlopen") as fetch:
            with self.assertRaisesRegex(AccessDisabled, "expired"):
                control()
        self.assertEqual(http.call_args.kwargs["timeout"], 15)
        self.assertFalse(fetch.called)
        self.assertFalse(auth.default.called)

    def test_runtime_refresh_error_is_redacted_and_never_falls_back(self):
        modules, auth, _ = self.control_modules()
        credentials = SimpleNamespace(valid=False, token="stale", refresh=Mock(side_effect=RuntimeError("SECRET")))
        control = GoogleControl(project="p", bucket="b", object_name="o", credentials=credentials)
        with patch.dict("sys.modules", modules):
            with self.assertRaises(AccessDisabled) as caught:
                control()
        self.assertNotIn("SECRET", str(caught.exception))
        self.assertFalse(auth.default.called)
