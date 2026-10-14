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
    def __init__(self, store, *, provider, access_check, connection_check=lambda: None, guest_snapshot=None):
        if not callable(provider) or not callable(access_check):
            raise ValueError("Provider and remote access check required")
        self.store, self.provider, self.access_check = store, provider, access_check
        self.connection_check = connection_check
        if guest_snapshot is not None and (type(guest_snapshot) is not tuple or len(guest_snapshot) != 2
                or type(guest_snapshot[0]) is not dict or type(guest_snapshot[1]) is not bytes):
            raise ValueError('Pinned bindings and saved payload required')
        self.guest_snapshot = guest_snapshot

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
                operations = ["preview", "negotiate", "negotiate_proposal", "manual_sign", "manual_release", "manual_trade", "manual_restructure", "player_context", "contract_context"]
                if self.guest_snapshot is not None:
                    operations.append('signing_context')
                return self._reply(request_id, result={"ai_enabled": True, "operations": operations})
            if operation == 'signing_context':
                fields = {'protocol', 'request_id', 'operation', 'observation', 'expected_revision', 'timeout_ms'}
                optional = {'performance_format', 'guest_offer'}
                if not fields <= set(request) or set(request) - fields - optional:
                    raise ValueError('Complete signing checkpoint request required')
                if 'performance_format' in request and request['performance_format'] != 'saved_history_v1':
                    raise ValueError('Unsupported saved performance format')
                timeout = request['timeout_ms']
                if type(timeout) is not int or not 1 <= timeout <= 60000:
                    raise ValueError('Bounded signing checkpoint timeout required')
                if self.guest_snapshot is None:
                    raise Rejected('Pinned guest snapshot not configured')
                deadline = time.monotonic() + timeout / 1000
                self.connection_check()
                from tools.reconcile_signing_context import reconcile_signing_context
                try:
                    result = reconcile_signing_context(*self.guest_snapshot, request['observation'],
                        self.store, expected_revision=request['expected_revision'])
                    if 'performance_format' in request:
                        from tools.export_player_performance import saved_player_performance
                        performance = saved_player_performance(*self.guest_snapshot, result['source_slot'])
                        if performance['player_id'] != result['player_id']:
                            raise ValueError('Saved performance identity differs from signing checkpoint')
                        result['performance_context'] = performance
                    if 'guest_offer' in request:
                        raw=request['guest_offer']
                        if type(raw) is not dict or set(raw)!={'amount_word','flags_word'}:
                            raise ValueError('Complete raw guest offer required')
                        from franchise.guest_contracts import preview_guest_offer
                        result['offer_context']=preview_guest_offer(self.store,result['team_id'],result['player_id'],
                            **raw,expected_revision=request['expected_revision'])
                except ValueError as error:
                    raise Rejected(str(error)) from error
                self.connection_check()
                if time.monotonic() >= deadline:
                    raise TimeoutError('Signing checkpoint expired')
                self._require_frame(request_id, result)
                return self._reply(request_id, result=result)
            if operation == 'negotiate_proposal' and 'observation' in request:
                fields = {'protocol', 'request_id', 'operation', 'observation', 'guest_offer',
                          'expected_revision', 'timeout_ms'}
                if set(request) not in (fields, fields | {'promise_goals'}):
                    raise ValueError('Complete captured signing proposal required')
                timeout = request['timeout_ms']
                if type(timeout) is not int or not 1 <= timeout <= 60000:
                    raise ValueError('Bounded signing proposal timeout required')
                deadline = time.monotonic() + timeout / 1000
                self.connection_check()
                self.access_check()  # A read checkpoint alone never grants inference.
                checkpoint_request = {key: request[key] for key in fields}
                checkpoint_request.update(operation='signing_context', performance_format='saved_history_v1')
                checkpoint_reply = self.handle(checkpoint_request)
                if checkpoint_reply['error'] is not None:
                    return checkpoint_reply
                checkpoint = checkpoint_reply['result']
                inspected = checkpoint['offer_context']
                if inspected['outcome'] != 'eligible_preview':
                    raise Rejected(inspected['reason'])
                remaining = int((deadline-time.monotonic())*1000)
                if remaining < 1:
                    raise TimeoutError('Signing proposal checkpoint expired')
                actor = checkpoint['player_context']
                normalized = dict(protocol=PROTOCOL, request_id=request_id, operation=operation,
                    team_id=checkpoint['team_id'], offer=inspected['offer'],
                    expected_revision=request['expected_revision'], timeout_ms=remaining,
                    personality=actor['personality'], relationships=actor['relationships'],
                    performance=checkpoint['performance_context'], contract_format='original_fxg_v1')
                if 'promise_goals' in request:
                    normalized['promise_goals'] = request['promise_goals']
                reply = self.handle(normalized)
                if reply['error'] is None:
                    evidence = reply['result']['evidence']
                    if any(json.dumps(evidence[key],sort_keys=True,allow_nan=False) !=
                           json.dumps(normalized[key],sort_keys=True,allow_nan=False)
                           for key in ('personality','relationships','performance')):
                        raise Rejected('Recorded proposal evidence differs from captured signing checkpoint')
                    reply['result']['signing_checkpoint'] = checkpoint
                    if len(json.dumps(reply,allow_nan=False).encode('utf-8'))+1 > 65536:
                        return self._reply(request_id,error='context_too_large',
                            detail='Captured proposal reply exceeds pipe frame capacity; no contract committed')
                return reply
            if operation == 'manual_restructure':
                from datetime import date
                from franchise.cap import money
                from franchise.restructures import PreseasonRestructureScope
                calendar='calendar_format' in request
                base={'protocol','request_id','operation','team_id','player_id','expected_revision',
                      'timeout_ms','decision_mode','scope','converted_base'}
                allowed=(base|{'generation_id','calendar_format'},) if calendar else (base,base|{'generation_id'})
                if request_fields not in allowed or request['decision_mode'] != 'manual':
                    raise ValueError('Explicit complete manual restructure required')
                if any(type(request[key]) is not str or not request[key].strip() for key in ('team_id','player_id')):
                    raise ValueError('Stable team and player identities required')
                if type(request['expected_revision']) is not int or request['expected_revision'] < 0:
                    raise ValueError('Nonnegative integer client revision required')
                generation_id=request.get('generation_id')
                if 'generation_id' in request and not calendar and (type(generation_id) is not str or not generation_id.startswith('contract-gen:')
                        or len(generation_id)!=77 or any(c not in '0123456789abcdef' for c in generation_id[13:])):
                    raise ValueError('Canonical returned agreement identity required')
                if calendar and (type(generation_id) is not str or not generation_id.strip()):
                    raise ValueError('Exact calendar amendment generation required')
                if calendar and request['calendar_format'] not in ('calendar_v1','calendar_v2'):
                    raise ValueError('Supported calendar amendment format required')
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
                apply=(self.store.restructure_calendar_layered_preseason_veteran if calendar and request['calendar_format']=='calendar_v2'
                       else self.store.restructure_calendar_preseason_veteran if calendar
                       else self.store.restructure_preseason_veteran)
                receipt = apply(request['team_id'],request_id,request['player_id'],
                    scope=PreseasonRestructureScope(**scope),converted_base=converted,
                    expected_revision=request['expected_revision'],access_check=restructure_access,generation_id=generation_id,
                    **({} if calendar else {'require_return_generation_id':True}),
                    receipt_check=lambda receipt:self._require_frame(request_id,restructure_result(receipt)))
                return self._reply(request_id,result=restructure_result(receipt))
            if operation == 'manual_trade':
                from datetime import date
                from franchise.trades import PreseasonTradeScope
                base={'protocol','request_id','operation','seller','buyer','player_id','seller_revision',
                      'buyer_revision','timeout_ms','decision_mode','scope'}
                calendar='calendar_format' in request
                allowed=(base|{'seller_generation_id','buyer_previous_generation_id','calendar_format'},) if calendar else (base,base|{'seller_generation_id','buyer_previous_generation_id'})
                if request_fields not in allowed or request['decision_mode']!='manual':
                    raise ValueError('Explicit complete manual assignment required')
                if calendar and request['calendar_format'] not in ('calendar_v1','calendar_v2'):
                    raise ValueError('Unsupported calendar assignment format')
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
                        'trade':receipt['participants'] if identity else receipt,**identity,
                        **({'calendar_format':request['calendar_format'],'format':receipt['format'],'league_year':receipt['league_year'],
                            **({'amendment_history':receipt['amendment_history']} if request['calendar_format']=='calendar_v2' else {})} if calendar else {})})
                trade=(self.store.trade_calendar_layered_preseason_veteran if calendar and request['calendar_format']=='calendar_v2'
                       else self.store.trade_calendar_preseason_veteran if calendar else self.store.trade_preseason_veteran)
                receipt=trade(request_id,request['seller'],request['buyer'],request['player_id'],
                    scope=PreseasonTradeScope(**scope),seller_revision=request['seller_revision'],buyer_revision=request['buyer_revision'],
                    access_check=trade_access,seller_generation_id=seller_generation,
                    buyer_previous_generation_id=buyer_previous,
                    **({} if calendar else {'require_generation_ids':True,'include_generation_identity':True}),
                    receipt_check=lambda receipt:self._require_frame(request_id,trade_result(receipt)))
                return self._reply(request_id,result=trade_result(receipt))
            if operation == 'manual_release':
                from datetime import date
                from franchise.releases import PreseasonReleaseScope
                from franchise.guarantees import DiscountProfile
                from franchise.books import parse_amount
                fields={'protocol','request_id','operation','team_id','player_id','expected_revision','timeout_ms',
                        'decision_mode','scope','discount','payment_year_offsets'}
                calendar='calendar_format' in request
                if request_fields != fields | ({'calendar_format','generation_id'} if calendar else set()) or request['decision_mode'] != 'manual':
                    raise ValueError('Explicit complete manual release request required')
                if calendar and (request['calendar_format'] not in ('calendar_v1','calendar_v2') or type(request['generation_id']) is not str
                                 or not request['generation_id'].strip()):
                    raise ValueError('Explicit calendar release format and generation required')
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
                release=(self.store.release_calendar_layered_preseason_veteran if calendar and request['calendar_format']=='calendar_v2'
                         else self.store.release_calendar_preseason_veteran if calendar else self.store.release_preseason_veteran)
                receipt=release(request['team_id'],request_id,request['player_id'],
                    scope=PreseasonReleaseScope(**scope),discount=DiscountProfile(**discount),
                    payment_year_offsets=tuple(request['payment_year_offsets']),expected_revision=request['expected_revision'],
                    access_check=release_access,receipt_check=lambda receipt:self._require_frame(request_id,
                        release_result(receipt)),**({'generation_id':request['generation_id']} if calendar else {}))
                return self._reply(request_id,result=release_result(receipt))
            if operation == 'contract_context':
                fields = {'protocol','request_id','operation','team_id','generation_id','timeout_ms'}
                if set(request) not in (fields,fields | {'context_format'}):
                    raise ValueError('Unexpected contract context fields')
                if 'context_format' in request and request['context_format'] not in ('calendar_v1','calendar_v2','calendar_v3','calendar_v4'):
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
                if 'context_format' in request and request['context_format'] not in ('calendar_v1','calendar_v2','calendar_v3','calendar_v4'):
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
            if operation in ("negotiate", "negotiate_proposal"):
                fields |= {"personality", "performance", "relationships"}
            elif operation == "manual_sign":
                fields |= {"decision_mode"}
            elif operation != "preview":
                raise ValueError("Unsupported operation")
            if operation in ("negotiate", "negotiate_proposal") and "promise_goals" in request:
                fields |= {"promise_goals"}
            if 'contract_format' in request:
                from franchise.guest_contracts import GUEST_CONTRACT_FORMAT
                if operation != 'negotiate_proposal' or request['contract_format'] != GUEST_CONTRACT_FORMAT:
                    raise ValueError('Supported guest proposal contract format required')
                fields |= {'contract_format'}
            if "return_scope" in request:
                fields |= {"return_scope"}
                if operation == 'negotiate_proposal':
                    raise ValueError('Guest proposal return signing is not supported')
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
                    relationships=request["relationships"], access_check=guarded_access,
                    proposal_only=operation == 'negotiate_proposal',
                    contract_format=request.get('contract_format'))
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
