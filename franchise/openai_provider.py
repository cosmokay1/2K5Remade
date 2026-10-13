"""Responses API adapter. No SDK dependency and no automatic paid retries."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from franchise.negotiation import DECISION_SCHEMA


from franchise.prompt import INSTRUCTIONS


class OpenAIProvider:
    def __init__(self, *, api_key: str, model: str):
        if not api_key or not model:
            raise ValueError("OPENAI_API_KEY and OPENAI_MODEL are required for live mode")
        self._api_key = api_key
        self.model = model

    def __call__(self, context: dict) -> str:
        payload = {"model": self.model, "instructions": INSTRUCTIONS,
                   "input": json.dumps(context), "store": False,
                   "max_output_tokens": 2000,
                   "text": {"format": {"type": "json_schema", "name": "negotiation",
                                       "strict": True, "schema": DECISION_SCHEMA}}}
        request = Request("https://api.openai.com/v1/responses",
                          data=json.dumps(payload).encode(),
                          headers={"Authorization": f"Bearer {self._api_key}",
                                   "Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=45) as response:
                result = json.load(response)
        except HTTPError as exc:
            # Do not print raw response bodies, request headers, or credentials.
            raise RuntimeError(f"Model request failed with HTTP {exc.code}") from None
        except (URLError, TimeoutError):
            raise RuntimeError("Model request failed or timed out; no deal committed") from None
        return response_text(result)


def response_text(result: dict) -> str:
    if result.get("status") != "completed":
        raise ValueError("Model response did not complete; no deal committed")
    parts = []
    for item in result.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "refusal":
                raise ValueError("Model declined the negotiation; no deal committed")
            if content.get("type") == "output_text":
                parts.append(content["text"])
    if not parts:
        raise ValueError("Model returned no decision; no deal committed")
    return "".join(parts)
