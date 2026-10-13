"""Versioned sidecar request boundary. No guest memory or game-save writes."""
import time
import json
from dataclasses import asdict
from franchise.cap import Offer, Rejected, json_amount
from franchise.control import AccessDisabled
from franchise.negotiation import Negotiation
from franchise.store import StoredLedger

PROTOCOL = 1


class Bridge:
    def __init__(self, store, *, provider, access_check, connection_check=lambda: None):
        if not callable(provider) or not callable(access_check):
            raise ValueError("Provider and remote access check required")
        self.store, self.provider, self.access_check = store, provider, access_check
        self.connection_check = connection_check

    def handle(self, request):
        request_id = request.get("request_id") if type(request) is dict else None
        try:
            if type(request) is not dict or type(request_id) is not str or not request_id.strip():
                raise ValueError("Request object and stable request ID required")
            if type(request.get("protocol")) is not int or request["protocol"] != PROTOCOL:
                return self._reply(request_id, error="protocol_mismatch")
            operation = request.get("operation")
            if operation == "hello":
                if set(request) != {"protocol", "request_id", "operation"}:
                    raise ValueError("Unexpected handshake fields")
                self.access_check()
                return self._reply(request_id, result={"ai_enabled": True, "operations": ["preview", "negotiate", "manual_sign", "player_context"]})
            if operation == 'player_context':
                if set(request) != {'protocol','request_id','operation','team_id','player_id','timeout_ms'}:
                    raise ValueError('Unexpected player context fields')
                if type(request['team_id']) is not str or not request['team_id'].strip():
                    raise ValueError('Stable team required')
                timeout = request['timeout_ms']
                if type(timeout) is not int or not 1 <= timeout <= 60000:
                    raise ValueError('Timeout must be 1-60000 milliseconds')
                deadline = time.monotonic() + timeout / 1000
                self.connection_check()
                result = self.store.player_context(request['team_id'],request['player_id'])
                self.connection_check()
                if time.monotonic() >= deadline:
                    raise TimeoutError('Player context request expired')
                reply=self._reply(request_id,result=result)
                if len(json.dumps(reply,allow_nan=False).encode('utf-8'))+1 > 65536:
                    return self._reply(request_id,error='context_too_large',detail='Player context exceeds pipe frame capacity')
                return reply
            fields = {"protocol", "request_id", "operation", "team_id", "offer", "expected_revision", "timeout_ms"}
            if operation == "negotiate":
                fields |= {"personality", "performance", "relationships"}
            elif operation == "manual_sign":
                fields |= {"decision_mode"}
            elif operation != "preview":
                raise ValueError("Unsupported operation")
            if operation == "negotiate" and "promise_goals" in request:
                fields |= {"promise_goals"}
            if set(request) != fields:
                raise ValueError("Unexpected request fields")
            if type(request["team_id"]) is not str or not request["team_id"].strip():
                raise ValueError("Stable team ID required")
            timeout = request["timeout_ms"]
            if type(timeout) is not int or not 1 <= timeout <= 60_000:
                raise ValueError("Timeout must be 1-60000 milliseconds")
            deadline = time.monotonic() + timeout / 1000
            def local_access():
                self.connection_check()
                if time.monotonic() >= deadline:
                    raise TimeoutError("Request expired")
            def guarded_access():
                local_access()
                self.access_check()
                if time.monotonic() >= deadline:
                    raise TimeoutError("Request expired")
            data = request["offer"]
            if type(data) is not dict or set(data) not in ({"player_id", "salaries", "signing_bonus"}, {"player_id", "salaries", "signing_bonus", "guaranteed_salaries"}) or type(data["salaries"]) is not list:
                raise ValueError("Complete offer required")
            offer = Offer.from_dict(data)
            ledger = StoredLedger(self.store, request["team_id"])
            if operation == "preview":
                # AI-off clients retain cap enforcement and manual previews.
                result = ledger.preview_offer(offer, request["expected_revision"])
            elif operation == "manual_sign":
                if request["decision_mode"] != "manual":
                    raise ValueError("Explicit manual decision required")
                local_access()
                story = {"request_id": request_id, "offer": offer.to_dict(),
                         "action": "accept", "reason": "Explicit manual agreement",
                         "counter": None, "outcome": "signed", "decision_mode": "manual"}
                receipt = self.store.sign(request["team_id"], request_id, offer,
                    request["expected_revision"], access_check=local_access, story=story)
                result = {**story, "charges": [json_amount(value) for value in receipt.charges]}
            else:
                guarded_access()
                if type(request["expected_revision"]) is not int:
                    raise ValueError("Integer client revision required")
                session = Negotiation(ledger, player_id=offer.player_id,
                    personality=request["personality"], performance=request["performance"],
                    relationships=request["relationships"], access_check=guarded_access)
                from franchise.promises import goals_from_list
                result = session.respond(request_id, offer, self.provider,
                                         expected_revision=request["expected_revision"],
                                         promise_goals=goals_from_list(request.get("promise_goals", [])))
            return self._reply(request_id, result=result)
        except AccessDisabled:
            return self._reply(request_id, error="ai_disabled")
        except TimeoutError:
            return self._reply(request_id, error="timeout")
        except Rejected as exc:
            return self._reply(request_id, error="state_rejected", detail=str(exc))
        except (ValueError, KeyError, TypeError):
            return self._reply(request_id, error="invalid_request")
        except Exception:
            # Never put cloud credentials, provider internals or tracebacks on wire.
            return self._reply(request_id, error="service_failure")

    @staticmethod
    def _reply(request_id, *, result=None, error=None, detail=None):
        return {"protocol": PROTOCOL, "request_id": request_id, "result": result,
                "error": error, "detail": detail}
