"""One player's negotiation history and a strict model-response boundary."""
import json
from dataclasses import asdict, dataclass
from threading import RLock
from franchise.cap import Ledger, Offer, Rejected


DECISION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "action": {"type": "string", "enum": ["accept", "reject", "counter"]},
        "reason": {"type": "string"},
        "salaries": {"type": ["array", "null"], "items": {"type": "integer"}},
        "signing_bonus": {"type": ["integer", "null"]},
    },
    "required": ["action", "reason", "salaries", "signing_bonus"],
}


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    counter: Offer | None

    @classmethod
    def parse(cls, text: str, player_id: str):
        data = json.loads(text)
        if type(data) is not dict or set(data) != set(DECISION_SCHEMA["required"]):
            raise ValueError("Unexpected model decision fields")
        if data["action"] not in ("accept", "reject", "counter"):
            raise ValueError("Unknown negotiation action")
        if type(data["reason"]) is not str or not data["reason"].strip():
            raise ValueError("Decision must include a reason")
        counter = None
        if data["action"] == "counter":
            if type(data["salaries"]) is not list:
                raise ValueError("Counteroffer requires annual salaries")
            counter = Offer(player_id, tuple(data["salaries"]), data["signing_bonus"])
        elif data["salaries"] is not None or data["signing_bonus"] is not None:
            raise ValueError("Accept/reject cannot silently change offered terms")
        return cls(data["action"], data["reason"], counter)


class Negotiation:
    def __init__(self, ledger: Ledger, *, player_id: str, personality: dict,
                 performance: dict, relationships: dict, access_check):
        if not callable(access_check):
            raise ValueError("An access handshake is required")
        self._access_check = access_check
        self._access_check()
        validate_performance(performance)
        self.ledger = ledger
        self.player_id = player_id
        # Freeze the provided context as JSON so outside edits cannot alter history.
        self._actor = json.dumps({"personality": personality, "performance": performance,
                                  "relationships": relationships})
        self._events: list[dict] = []
        self._replies: dict[str, tuple[Offer, dict]] = {}
        self._signed = False
        self._lock = RLock()

    @property
    def events(self) -> list[dict]:
        with self._lock:
            return json.loads(json.dumps(self._events))

    def respond(self, request_id: str, offer: Offer, provider) -> dict:
        with self._lock:
            return self._respond(request_id, offer, provider)

    def _respond(self, request_id: str, offer: Offer, provider) -> dict:
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
        if self._signed:
            raise ValueError("Negotiation is already signed")
        snapshot = self.ledger.negotiation_context(self.player_id)
        context = {"player_id": self.player_id, **json.loads(self._actor),
                   "offer": asdict(offer), "accounting": snapshot,
                   "history": self.events}
        decision = Decision.parse(provider(context), self.player_id)
        self._access_check()
        event = {"request_id": request_id, "offer": asdict(offer),
                 "action": decision.action, "reason": decision.reason,
                 "counter": asdict(decision.counter) if decision.counter else None,
                 "outcome": "pending"}
        if decision.action == "accept":
            try:
                receipt = self.ledger.sign(request_id, offer, snapshot["revision"],
                                           access_check=self._access_check)
            except Rejected as exc:
                event["outcome"] = "accounting_rejected"
                event["accounting_reason"] = str(exc)
            else:
                event["outcome"] = "signed"
                event["charges"] = list(receipt.charges)
                self._signed = True
        elif decision.action == "counter":
            event["outcome"] = "counteroffer"
        else:
            event["outcome"] = "player_rejected"
        # Model narration is a attributed reason, not a fabricated transaction.
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
