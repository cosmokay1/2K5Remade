"""One player's negotiation history and a strict model-response boundary."""
import json
from dataclasses import asdict, dataclass
from threading import RLock
from franchise.cap import Ledger, Offer, Rejected, json_amount


DECISION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "action": {"type": "string", "enum": ["accept", "reject", "counter"]},
        "reason": {"type": "string"},
        "salaries": {"type": ["array", "null"], "items": {"type": "integer"}},
        "signing_bonus": {"type": ["integer", "null"]},
        "guaranteed_salaries": {"type": ["array", "null"], "items": {"type": "integer"}},
    },
    "required": ["action", "reason", "salaries", "signing_bonus", "guaranteed_salaries"],
}


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    counter: Offer | None

    @classmethod
    def parse(cls, text: str, player_id: str):
        data = json.loads(text)
        required = set(DECISION_SCHEMA["required"])
        if type(data) is not dict or set(data) not in (required, required - {"guaranteed_salaries"}):
            raise ValueError("Unexpected model decision fields")
        if data["action"] not in ("accept", "reject", "counter"):
            raise ValueError("Unknown negotiation action")
        if type(data["reason"]) is not str or not data["reason"].strip():
            raise ValueError("Decision must include a reason")
        counter = None
        if data["action"] == "counter":
            if type(data["salaries"]) is not list:
                raise ValueError("Counteroffer requires annual salaries")
            guarantees = data.get("guaranteed_salaries")
            if guarantees is not None and type(guarantees) is not list:
                raise ValueError("Annual counter guarantees required")
            counter = Offer(player_id, tuple(data["salaries"]), data["signing_bonus"], tuple(guarantees or ()))
        elif data["salaries"] is not None or data["signing_bonus"] is not None or data.get("guaranteed_salaries") is not None:
            raise ValueError("Accept/reject cannot silently change offered terms")
        return cls(data["action"], data["reason"], counter)


class Negotiation:
    def __init__(self, ledger: Ledger, *, player_id: str, personality: dict,
                 performance: dict, relationships: dict, access_check):
        if not callable(access_check):
            raise ValueError("An access handshake is required")
        self._access_check = access_check
        self._access_check()
        from franchise.performance import PerformanceEvidence
        if isinstance(performance, PerformanceEvidence):
            if performance.player_id != player_id:
                raise ValueError("Performance evidence belongs to another player")
            performance = performance.to_context()
        if any(type(value) is not dict for value in (personality, performance, relationships)):
            raise ValueError("Actor context fields must be JSON objects")
        # Other actor fields must not provide a back door for hidden ratings.
        validate_performance({"personality": personality, "performance": performance,
                              "relationships": relationships})
        self.ledger = ledger
        self.player_id = player_id
        actor = ledger.bind_actor(player_id, personality, relationships,
                                  access_check=self._access_check)
        # Durable priorities survive restart; current observed production may change.
        self._actor = json.dumps({**actor, "performance": performance}, allow_nan=False)
        self._events: list[dict] = ledger.negotiation_history(player_id)
        self._replies: dict[str, tuple[Offer, dict]] = {}
        self._signed = any(event["outcome"] == "signed" for event in self._events)
        self._lock = RLock()

    @property
    def events(self) -> list[dict]:
        with self._lock:
            return json.loads(json.dumps(self._events))

    def respond(self, request_id: str, offer: Offer, provider, *, expected_revision=None) -> dict:
        with self._lock:
            return self._respond(request_id, offer, provider, expected_revision=expected_revision)

    def _respond(self, request_id: str, offer: Offer, provider, *, expected_revision=None) -> dict:
        self._access_check()
        if offer.player_id != self.player_id:
            raise ValueError("Offer belongs to another player")
        if type(request_id) is not str or not request_id.strip():
            raise ValueError("A negotiation request ID is required")
        prior = self._replies.get(request_id)
        if prior is not None:
            if prior[0] != offer:
                raise ValueError("Negotiation request ID reused with different terms")
            return json.loads(json.dumps(prior[1]))
        recorded = self.ledger.recalled_negotiation(request_id, offer)
        if recorded is not None:
            self._replies[request_id] = (offer, recorded)
            if not any(event["request_id"] == request_id for event in self._events):
                self._events.append(recorded)
            self._signed = self._signed or recorded["outcome"] == "signed"
            return json.loads(json.dumps(recorded))
        fresh = self.ledger.negotiation_history(self.player_id)
        if fresh:
            self._events = fresh
            self._signed = any(event["outcome"] == "signed" for event in fresh)
        if self._signed:
            raise ValueError("Negotiation is already signed")
        snapshot = self.ledger.negotiation_context(self.player_id)
        if expected_revision is not None and (type(expected_revision) is not int or expected_revision != snapshot["revision"]):
            raise Rejected("Offer was based on stale client franchise state")
        context = {"player_id": self.player_id, **json.loads(self._actor),
                   "offer": offer.to_dict(), "accounting": snapshot,
                   "history": self.events}
        decision = Decision.parse(provider(context), self.player_id)
        self._access_check()
        event = {"request_id": request_id, "offer": offer.to_dict(),
                 "action": decision.action, "reason": decision.reason,
                 "counter": decision.counter.to_dict() if decision.counter else None,
                 "outcome": "pending",
                 "evidence": {**json.loads(self._actor), "financial_revision": snapshot["revision"]},
                 "history_request_ids": [entry["request_id"] for entry in context["history"]]}
        if decision.action == "accept":
            try:
                receipt = self.ledger.commit_negotiation(
                    request_id, offer, snapshot["revision"],
                    access_check=self._access_check, story={**event, "outcome": "signed"})
            except Rejected as exc:
                event["outcome"] = "accounting_rejected"
                event["accounting_reason"] = str(exc)
            else:
                event["outcome"] = "signed"
                event["charges"] = [json_amount(value) for value in receipt.charges]
                self._signed = True
        elif decision.action == "counter":
            event["outcome"] = "counteroffer"
        else:
            event["outcome"] = "player_rejected"
        if event["outcome"] != "signed":
            event = self.ledger.record_negotiation(event, access_check=self._access_check)
        # Model narration is an attributed reason, not a fabricated transaction.
        self._events.append(event)
        self._replies[request_id] = (offer, event)
        return json.loads(json.dumps(event))


def validate_performance(value):
    """Keep recognizable hidden game-rating fields out of performance evidence."""
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_").replace(" ", "_")
            if (normalized in {"overall", "ovr", "rating", "ratings", "potential",
                               "catching", "catching_skill", "skill_ratings"}
                    or normalized.endswith(("_rating", "_ratings"))):
                raise ValueError("Performance evidence cannot contain hidden game ratings")
            validate_performance(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            validate_performance(item)
