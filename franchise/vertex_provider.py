"""Gemini on Google Cloud Vertex AI, using Application Default Credentials."""
import json
import subprocess
import time
from collections import deque
from threading import Lock
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
                 instructions=INSTRUCTIONS, response_schema=None, max_context_bytes=1048576,
                 max_requests_per_minute=20, request_budget=None,
                 max_input_tokens=None, max_output_tokens=4096):
        if not all(type(value) is str and value.strip() for value in (project, location, model)):
            raise ValueError("GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, and GEMINI_MODEL are required")
        if credentials is not None and use_gcloud_login:
            raise ValueError("Runtime credentials cannot fall back to owner gcloud login")
        if type(instructions) is not str or not instructions.strip():
            raise ValueError('Model instructions required')
        schema = VERTEX_SCHEMA if response_schema is None else response_schema
        if type(schema) is not dict:
            raise ValueError('Structured decision schema required')
        if type(max_context_bytes) is not int or max_context_bytes <= 0:
            raise ValueError("Positive integer model context byte limit required")
        self.max_context_bytes = max_context_bytes
        for name,value in (("max_input_tokens",max_input_tokens),("max_output_tokens",max_output_tokens)):
            if name=='max_input_tokens' and value is None:continue
            if type(value) is not int or not 0<value<=2**31-1:
                raise ValueError('Positive integer model token limit required')
        self.max_input_tokens=max_input_tokens
        self.max_output_tokens=max_output_tokens
        if type(max_requests_per_minute) is not int or max_requests_per_minute <= 0:
            raise ValueError("Positive integer inference rate limit required")
        self.max_requests_per_minute = max_requests_per_minute
        if request_budget is not None:
            from franchise.inference_budget import InferenceBudget
            if not isinstance(request_budget,InferenceBudget):
                raise ValueError('Typed persistent inference budget required')
        self.request_budget = request_budget
        self._request_times = deque()
        self._rate_lock = Lock()
        self.instructions = instructions
        self.response_schema = json.loads(json.dumps(schema, allow_nan=False))
        self.model = model
        self._last_usage = None
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

    @property
    def last_usage(self):
        """Last completed call; diagnostic only, not durable billing or deal attribution."""
        return json.loads(json.dumps(self._last_usage))

    def __call__(self, context: dict, *, before_generate=None) -> str:
        token_fields=("prompt_token_count","candidates_token_count","total_token_count",
                      "cached_content_token_count","thoughts_token_count","tool_use_prompt_token_count")
        usage={"model":self.model,"sdk_invoked":False,"outcome":"preflight_rejected",
                          "context_bytes":None,"tokens":{field:None for field in token_fields},"estimated_cost":None}
        reservation = None
        try:
            if type(context) is not dict:
                raise ValueError("Model context must be an object; no inference submitted")
            contents = json.dumps(context, allow_nan=False)
            usage["context_bytes"] = len(contents.encode("utf-8"))
            if usage["context_bytes"] > self.max_context_bytes:
                raise ValueError("Model context exceeds request size limit; no inference submitted")
            with self._rate_lock:
                now = time.monotonic()
                while self._request_times and self._request_times[0] <= now - 60:
                    self._request_times.popleft()
                if len(self._request_times) >= self.max_requests_per_minute:
                    raise ValueError("Inference request rate exceeded; no inference submitted")
                # Failed/blocked calls still consume their attempted SDK slot.
                self._request_times.append(now)
            generation_config={"response_mime_type":"application/json",
                "response_schema":self.response_schema,"max_output_tokens":self.max_output_tokens}
            if self.max_input_tokens is not None:
                try:
                    count=self._client.models.count_tokens(model=self.model,contents=contents,
                        config={"system_instruction":self.instructions,"generation_config":generation_config})
                except Exception:
                    raise RuntimeError('Vertex AI token counting failed; no inference submitted') from None
                total=getattr(count,'total_tokens',None)
                if type(total) is not int or not 0<=total<=self.max_input_tokens:
                    raise ValueError('Model input token count missing or exceeds limit; no inference submitted')
            # Counting adds a network wait: recheck this request's deadline and
            # remote grant before authorizing a new paid generation attempt.
            if before_generate is not None:
                before_generate()
            if self.request_budget is not None:
                reservation = self.request_budget.reserve(model=self.model)
                usage['outcome']='request_failed'
                # SQLite admission may itself wait for another process.
                if before_generate is not None:
                    before_generate()
            usage.update(sdk_invoked=True,outcome="request_failed")
            try:
                result = self._client.models.generate_content(
                    model=self.model, contents=contents,
                    config={"system_instruction": self.instructions,**generation_config})
            except Exception:
                # Avoid echoing credentials or raw cloud error bodies.
                raise RuntimeError("Vertex AI request failed; no deal committed") from None
            metadata=getattr(result,"usage_metadata",None)
            for field in token_fields:
                value=getattr(metadata,field,None)
                if type(value) is int and value >= 0:
                    usage["tokens"][field]=value
            usage["outcome"]="response_rejected"
            candidates = result.candidates or []
            if len(candidates) != 1 or candidates[0].finish_reason != "STOP":
                raise ValueError("Gemini response was blocked or incomplete; no deal committed")
            text = result.text
            if type(text) is not str or not text.strip():
                raise ValueError("Gemini returned no decision; no deal committed")
            usage["outcome"]="response_accepted"
            return text
        finally:
            self._last_usage = usage
            if reservation is not None:
                self.request_budget.complete(reservation,outcome=usage['outcome'],tokens=usage['tokens'])
