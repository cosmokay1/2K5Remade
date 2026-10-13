"""Gemini on Google Cloud Vertex AI, using Application Default Credentials."""
import json
import subprocess
from franchise.prompt import INSTRUCTIONS
from franchise.promises import METRICS


VERTEX_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "action": {"type": "STRING", "enum": ["accept", "reject", "counter"]},
        "reason": {"type": "STRING"},
        "salaries": {"type": "ARRAY", "nullable": True, "items": {"type": "INTEGER"}},
        "signing_bonus": {"type": "INTEGER", "nullable": True},
        "promise_goals": {"type":"ARRAY", "nullable":True, "items":{"type":"OBJECT",
            "properties":{"goal_id":{"type":"STRING"},"metric":{"type":"STRING","enum":sorted(METRICS)},
                          "target":{"type":"INTEGER"},"importance":{"type":"INTEGER"},
                          "window":{"type":"STRING"},"source":{"type":"STRING"}},
            "required":["goal_id","metric","target","importance","window","source"]}},
        "guaranteed_salaries": {"type": "ARRAY", "nullable": True, "items": {"type": "INTEGER"}},
    },
    "required": ["action", "reason", "salaries", "signing_bonus", "guaranteed_salaries", "promise_goals"],
}


class VertexProvider:
    def __init__(self, *, project: str, location: str, model: str, client=None,
                 use_gcloud_login: bool = False, credentials=None,
                 instructions=INSTRUCTIONS, response_schema=None):
        if not all(type(value) is str and value.strip() for value in (project, location, model)):
            raise ValueError("GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, and GEMINI_MODEL are required")
        if credentials is not None and use_gcloud_login:
            raise ValueError("Runtime credentials cannot fall back to owner gcloud login")
        if type(instructions) is not str or not instructions.strip():
            raise ValueError('Model instructions required')
        schema = VERTEX_SCHEMA if response_schema is None else response_schema
        if type(schema) is not dict:
            raise ValueError('Structured decision schema required')
        self.instructions = instructions
        self.response_schema = json.loads(json.dumps(schema, allow_nan=False))
        self.model = model
        if client is None:
            try:
                from google import genai
            except ImportError:
                raise RuntimeError("Install requirements-google.txt for Vertex AI support") from None
            try:
                if use_gcloud_login:
                    # Local CLI demo only: keep its short-lived token in memory.
                    from google.oauth2.credentials import Credentials
                    token = subprocess.run(
                        ["gcloud", "auth", "print-access-token", "--project", project],
                        capture_output=True, text=True, check=True, timeout=30).stdout.strip()
                    if not token:
                        raise ValueError("Google Cloud login returned no token")
                    credentials = Credentials(token=token, quota_project_id=project)
                client = genai.Client(vertexai=True, project=project, location=location,
                                      credentials=credentials,
                                      http_options={"api_version": "v1", "timeout": 45000,
                                                    "retry_options": {"attempts": 1}})
            except Exception:
                raise RuntimeError("Could not initialize Vertex AI; check Google credentials") from None
        self._client = client

    def __call__(self, context: dict) -> str:
        try:
            result = self._client.models.generate_content(
                model=self.model, contents=json.dumps(context),
                config={"system_instruction": self.instructions,
                        "response_mime_type": "application/json",
                        "response_schema": self.response_schema,
                        "max_output_tokens": 4096})
        except Exception:
            # Avoid echoing credentials or raw cloud error bodies.
            raise RuntimeError("Vertex AI request failed; no deal committed") from None
        candidates = result.candidates or []
        if len(candidates) != 1 or candidates[0].finish_reason != "STOP":
            raise ValueError("Gemini response was blocked or incomplete; no deal committed")
        text = result.text
        if type(text) is not str or not text.strip():
            raise ValueError("Gemini returned no decision; no deal committed")
        return text
