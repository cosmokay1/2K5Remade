"""Versioned sidecar request boundary. No guest memory or game-save writes."""
import time
import json
from dataclasses import asdict
from franchise.cap import Offer, Rejected, json_amount
from franchise.control import AccessDisabled
from franchise.negotiation import Negotiation
from franchise.store import StoredLedger

PROTOCOL = 1


class ResponseTooLarge(ValueError):
    """A lifecycle receipt cannot fit the native protocol frame."""


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
            compact='receipt_format' in request
            if compact:
                from franchise.receipts import TARGET_FORMAT
                if operation not in ('manual_release','manual_trade','manual_restructure') or request['receipt_format']!=TARGET_FORMAT:
                    raise ValueError('Unsupported lifecycle receipt format')
            request_fields=set(request)-({'receipt_format'} if compact else set())
            def receipt_result(result):
                if compact:
                    from franchise.receipts import compact_lifecycle_result
                    return compact_lifecycle_result(result,operation)
                return result
            if operation == "hello":
                if set(request) != {"protocol", "request_id", "operation"}:
                    raise ValueError("Unexpected handshake fields")
                self.access_check()
                return self._reply(request_id, result={"ai_enabled": True, "operations": ["preview", "negotiate", "manual_sign", "manual_release", "manual_trade", "manual_restructure", "player_context", "contract_context"]})
            if operation == 'manual_restructure':
                from datetime import date
                from franchise.cap import money
                from franchise.restructures import PreseasonRestructureScope
                if request_fields not in ({'protocol','request_id','operation','team_id','player_id','expected_revision',
                                    'timeout_ms','decision_mode','scope','converted_base'},
                                    {'protocol','request_id','operation','team_id','player_id','expected_revision',
                                    'timeout_ms','decision_mode','scope','converted_base','generation_id'}) or request['decision_mode'] != 'manual':
                    raise ValueError('Explicit complete manual restructure required')
                if any(type(request[key]) is not str or not request[key].strip() for key in ('team_id','player_id')):
                    raise ValueError('Stable team and player identities required')
                if type(request['expected_revision']) is not int or request['expected_revision'] < 0:
                    raise ValueError('Nonnegative integer client revision required')
                generation_id=request.get('generation_id')
                if 'generation_id' in request and (type(generation_id) is not str or not generation_id.startswith('contract-gen:')
                        or len(generation_id)!=77 or any(c not in '0123456789abcdef' for c in generation_id[13:])):
                    raise ValueError('Canonical returned agreement identity required')
                converted = money(request['converted_base'])
                if converted == 0:
                    raise ValueError('Positive base conversion required')
                timeout = request['timeout_ms']
                if type(timeout) is not int or not 1 <= timeout <= 60000:
                    raise ValueError('Timeout must be 1-60000 milliseconds')
                deadline = time.monotonic() + timeout / 1000
                def restructure_access():
                    self.connection_check()
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Restructure request expired')
                restructure_access()
                fields = {'league_year','amended_on','first_regular_season_game','current_year_earned_base',
                          'healthy','consent','renegotiation_eligible','exclusions','minimum_source','source'}
                if type(request['scope']) is not dict or set(request['scope']) != fields:
                    raise ValueError('Complete sourced restructure scope required')
                scope = dict(request['scope'])
                exclusions = scope['exclusions']
                if type(exclusions) is not list or any(type(item) is not str for item in exclusions) or len(set(exclusions)) != len(exclusions):
                    raise ValueError('Unique explicit restructure exclusions required')
                scope['exclusions'] = frozenset(exclusions)
                for field in ('amended_on','first_regular_season_game'):
                    value = scope[field]
                    if type(value) is not str:
                        raise ValueError('Canonical YYYY-MM-DD restructure dates required')
                    parsed = date.fromisoformat(value)
                    if parsed.isoformat() != value:
                        raise ValueError('Canonical YYYY-MM-DD restructure dates required')
                    scope[field] = parsed
                def restructure_result(receipt):
                    return receipt_result({'decision_mode':'manual','team_id':request['team_id'],
                        'player_id':request['player_id'],'restructure':receipt,
                        **({'generation_id':generation_id} if generation_id is not None else {})})
                receipt = self.store.restructure_preseason_veteran(request['team_id'],request_id,request['player_id'],
                    scope=PreseasonRestructureScope(**scope),converted_base=converted,
                    expected_revision=request['expected_revision'],access_check=restructure_access,generation_id=generation_id,require_return_generation_id=True,
                    receipt_check=lambda receipt:self._require_frame(request_id,restructure_result(receipt)))
                return self._reply(request_id,result=restructure_result(receipt))
            if operation == 'manual_trade':
                from datetime import date
                from franchise.trades import PreseasonTradeScope
                base={'protocol','request_id','operation','seller','buyer','player_id','seller_revision',
                      'buyer_revision','timeout_ms','decision_mode','scope'}
                if request_fields not in (base,base|{'seller_generation_id','buyer_previous_generation_id'}) or request['decision_mode']!='manual':
                    raise ValueError('Explicit complete manual assignment required')
                seller_generation=request.get('seller_generation_id')
                buyer_previous=request.get('buyer_previous_generation_id')
                if 'seller_generation_id' in request:
                    for role,value in (('seller',seller_generation),('buyer',buyer_previous)):
                        if value is None and role=='buyer':
                            continue
                        if type(value) is not str:
                            raise ValueError('Canonical trade agreement identities required')
                        prefix='contract-gen:' if value.startswith('contract-gen:') else 'legacy-contract:'
                        if not value.startswith(prefix) or len(value)!=len(prefix)+64 or any(c not in '0123456789abcdef' for c in value[len(prefix):]):
                            raise ValueError('Canonical trade agreement identities required')
                timeout=request['timeout_ms']
                if type(timeout) is not int or not 1 <= timeout <= 60000:
                    raise ValueError('Timeout must be 1-60000 milliseconds')
                deadline=time.monotonic()+timeout/1000
                def trade_access():
                    self.connection_check()
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Assignment request expired')
                trade_access()
                if type(request['scope']) is not dict:
                    raise ValueError('Sourced assignment facts required')
                scope=dict(request['scope'])
                exclusions=scope['exclusions']
                if type(exclusions) is not list or any(type(item) is not str for item in exclusions) or len(set(exclusions)) != len(exclusions):
                    raise ValueError('Unique explicit assignment exclusions required')
                scope['exclusions']=frozenset(exclusions)
                for field in ('traded_on','seller_first_regular_season_game','buyer_first_regular_season_game'):
                    value=scope[field]
                    parsed=date.fromisoformat(value)
                    if parsed.isoformat() != value:
                        raise ValueError('Canonical YYYY-MM-DD assignment dates required')
                    scope[field]=parsed
                def trade_result(receipt):
                    identity={key:receipt[key] for key in ('seller_generation_id','buyer_generation_id','buyer_previous_generation_id')} if len(receipt)>2 else {}
                    return receipt_result({'decision_mode':'manual','player_id':request['player_id'],
                        'seller':request['seller'],'buyer':request['buyer'],
                        'trade':receipt['participants'] if identity else receipt,**identity})
                receipt=self.store.trade_preseason_veteran(request_id,request['seller'],request['buyer'],request['player_id'],
                    scope=PreseasonTradeScope(**scope),seller_revision=request['seller_revision'],buyer_revision=request['buyer_revision'],
                    access_check=trade_access,seller_generation_id=seller_generation,
                    buyer_previous_generation_id=buyer_previous,require_generation_ids=True,include_generation_identity=True,
                    receipt_check=lambda receipt:self._require_frame(request_id,trade_result(receipt)))
                return self._reply(request_id,result=trade_result(receipt))
            if operation == 'manual_release':
                from datetime import date
                from franchise.releases import PreseasonReleaseScope
                from franchise.guarantees import DiscountProfile
                from franchise.books import parse_amount
                if request_fields != {'protocol','request_id','operation','team_id','player_id','expected_revision','timeout_ms',
                                    'decision_mode','scope','discount','payment_year_offsets'} or request['decision_mode'] != 'manual':
                    raise ValueError('Explicit complete manual release request required')
                if type(request['team_id']) is not str or not request['team_id'].strip():
                    raise ValueError('Stable team required')
                timeout=request['timeout_ms']
                if type(timeout) is not int or not 1 <= timeout <= 60000:
                    raise ValueError('Timeout must be 1-60000 milliseconds')
                deadline=time.monotonic()+timeout/1000
                def release_access():
                    self.connection_check()
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Release request expired')
                release_access()
                if type(request['scope']) is not dict or type(request['discount']) is not dict or type(request['payment_year_offsets']) is not list:
                    raise ValueError('Typed release source records required')
                scope=dict(request['scope'])
                exclusions=scope['exclusions']
                if type(exclusions) is not list or any(type(item) is not str for item in exclusions) or len(set(exclusions)) != len(exclusions):
                    raise ValueError('Unique explicit release exclusions required')
                scope['exclusions']=frozenset(exclusions)
                for field in ('removed_on','first_regular_season_game'):
                    value=scope[field]
                    parsed=date.fromisoformat(value)
                    if parsed.isoformat() != value:
                        raise ValueError('Canonical YYYY-MM-DD release dates required')
                    scope[field]=parsed
                discount=dict(request['discount'])
                discount['annual_rate']=parse_amount(discount['annual_rate'])
                def release_result(receipt):
                    return receipt_result({'decision_mode':'manual','player_id':request['player_id'],'release':receipt})
                receipt=self.store.release_preseason_veteran(request['team_id'],request_id,request['player_id'],
                    scope=PreseasonReleaseScope(**scope),discount=DiscountProfile(**discount),
                    payment_year_offsets=tuple(request['payment_year_offsets']),expected_revision=request['expected_revision'],
                    access_check=release_access,receipt_check=lambda receipt:self._require_frame(request_id,
                        release_result(receipt)))
                return self._reply(request_id,result=release_result(receipt))
            if operation == 'contract_context':
                fields = {'protocol','request_id','operation','team_id','generation_id','timeout_ms'}
                if set(request) not in (fields,fields | {'context_format'}):
                    raise ValueError('Unexpected contract context fields')
                if 'context_format' in request and request['context_format'] not in ('calendar_v1','calendar_v2'):
                    raise ValueError('Unsupported contract context format')
                if any(type(request[key]) is not str or not request[key].strip() for key in ('team_id','generation_id')):
                    raise ValueError('Stable team and agreement identities required')
                timeout=request['timeout_ms']
                if type(timeout) is not int or not 1 <= timeout <= 60000:
                    raise ValueError('Timeout must be 1-60000 milliseconds')
                deadline=time.monotonic()+timeout/1000
                self.connection_check()
                context = self.store.calendar_contract_context if 'context_format' in request else self.store.contract_context
                result=context(request['team_id'],request['generation_id'],
                    **({'context_format':request['context_format']} if 'context_format' in request else {}))
                self.connection_check()
                if time.monotonic() >= deadline:
                    raise TimeoutError('Contract context request expired')
                reply=self._reply(request_id,result=result)
                if len(json.dumps(reply,allow_nan=False).encode('utf-8'))+1 > 65536:
                    return self._reply(request_id,error='context_too_large',detail='Contract context exceeds pipe frame capacity')
                return reply
            if operation == 'player_context':
                fields = {'protocol','request_id','operation','team_id','player_id','timeout_ms'}
                if set(request) not in (fields,fields | {'context_format'}):
                    raise ValueError('Unexpected player context fields')
                if 'context_format' in request and request['context_format'] not in ('calendar_v1','calendar_v2'):
                    raise ValueError('Unsupported player context format')
                if type(request['team_id']) is not str or not request['team_id'].strip():
                    raise ValueError('Stable team required')
                timeout = request['timeout_ms']
                if type(timeout) is not int or not 1 <= timeout <= 60000:
                    raise ValueError('Timeout must be 1-60000 milliseconds')
                deadline = time.monotonic() + timeout / 1000
                self.connection_check()
                result = self.store.player_context(request['team_id'],request['player_id'],
                    context_format=request.get('context_format'))
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
            if "return_scope" in request:
                fields |= {"return_scope"}
            if set(request) != fields:
                raise ValueError("Unexpected request fields")
            return_scope=self.store._return_scope(request["return_scope"]) if "return_scope" in request else None
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
            ledger = StoredLedger(self.store, request["team_id"],return_scope=return_scope)
            if operation == "preview":
                # AI-off clients retain cap enforcement and manual previews.
                local_access()
                result = ledger.preview_offer(offer, request["expected_revision"])
                local_access()
                if return_scope is not None:
                    result["return_scope"]=ledger.return_scope_context()
            elif operation == "manual_sign":
                if request["decision_mode"] != "manual":
                    raise ValueError("Explicit manual decision required")
                local_access()
                story = {"request_id": request_id, "offer": offer.to_dict(),
                         "action": "accept", "reason": "Explicit manual agreement",
                         "counter": None, "outcome": "signed", "decision_mode": "manual",
                         **({"return_scope":ledger.return_scope_context()} if return_scope is not None else {})}
                receipt = ledger.commit_negotiation(request_id,offer,request["expected_revision"],
                    access_check=local_access,story=story)
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
        except ResponseTooLarge:
            return self._reply(request_id,error='response_too_large',detail='Lifecycle receipt exceeds pipe frame capacity; transaction not changed')
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

    @classmethod
    def _require_frame(cls,request_id,result):
        if len(json.dumps(cls._reply(request_id,result=result),allow_nan=False).encode('utf-8'))+1 > 65536:
            raise ResponseTooLarge('Lifecycle receipt exceeds pipe frame capacity')

    @staticmethod
    def _reply(request_id, *, result=None, error=None, detail=None):
        return {"protocol": PROTOCOL, "request_id": request_id, "result": result,
                "error": error, "detail": detail}
