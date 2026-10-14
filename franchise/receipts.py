"""Opt-in native receipts; full durable transaction receipts remain authoritative."""
from copy import deepcopy
import json
from franchise.cap import money
from franchise.cash import CashObligation

TARGET_FORMAT='target_v1'


def _canonical(value):
    return json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':'))


def _participant(receipt,player,map_name,cash_name,expected_cash=None):
    financial,cash=receipt['financial'],receipt['cash']
    archive=financial[map_name][player]
    if archive['original_contract']['offer']['player_id']!=player:
        raise ValueError('Lifecycle archive belongs to another player')
    target=CashObligation.from_dict(archive[cash_name])
    if target.player_id!=player or target.paid_components is None:
        raise ValueError('Complete allocated target cash required')
    identity=target.obligation_id
    if expected_cash is not None and identity!=expected_cash:
        raise ValueError('Target cash disagrees with explicit agreement identity')
    if identity!='contract:'+player and (not identity.startswith('contract-gen:') or len(identity)!=77
            or any(c not in '0123456789abcdef' for c in identity[13:])):
        raise ValueError('Canonical lifecycle cash identity required')
    records=[CashObligation.from_dict(row) for row in cash['obligations']]
    if len({record.obligation_id for record in records})!=len(records):
        raise ValueError('Duplicate source cash obligation')
    matches=[record for record in records if record.obligation_id==identity]
    if len(matches)!=1 or _canonical(matches[0].to_dict())!=_canonical(target.to_dict()):
        raise ValueError('Target cash differs from lifecycle archive')
    totals={name:money(cash[name]) for name in ('nominal_total','paid_total','unpaid_total')}
    if totals!={'nominal_total':sum(record.amount for record in records),
                'paid_total':sum(record.paid for record in records),
                'unpaid_total':sum(record.amount-record.paid for record in records)}:
        raise ValueError('Source cash totals disagree with obligations')
    other=[record for record in records if record.obligation_id!=identity]
    compact_cash={'revision':money(cash['revision']),**totals,'obligations':[target.to_dict()],
        'other_obligations':{'count':len(other),'nominal_total':sum(r.amount for r in other),
            'paid_total':sum(r.paid for r in other),'unpaid_total':sum(r.amount-r.paid for r in other)}}
    compact_financial={name:deepcopy(financial[name]) for name in ('revision','charges','signed_players')}
    compact_financial[map_name]={player:deepcopy(archive)}
    return {'financial':compact_financial,'cash':compact_cash}



def _identity_cash(generation,player):
    if type(generation) is not str:
        raise ValueError('Canonical agreement identity required')
    prefix='contract-gen:' if generation.startswith('contract-gen:') else 'legacy-contract:'
    if (not generation.startswith(prefix) or len(generation)!=len(prefix)+64
            or any(c not in '0123456789abcdef' for c in generation[len(prefix):])):
        raise ValueError('Canonical agreement identity required')
    return generation if prefix=='contract-gen:' else 'contract:'+player

def compact_lifecycle_result(result,operation):
    """Project the exact fresh or historical receipt, never current league state."""
    player=result['player_id']
    projected={**result,'receipt_format':TARGET_FORMAT}
    if operation=='manual_release':
        archive=result['release']['financial']['released_contracts'][player]
        original=CashObligation.from_dict(archive['original_cash'])
        if original.player_id!=player or original.paid_components is None:
            raise ValueError('Allocated original release cash required')
        projected['release']=_participant(result['release'],player,'released_contracts','cash_obligation',original.obligation_id)
        if 'format' in result['release']:
            receipt=result['release']
            if type(receipt['format']) is not int or receipt['format']!=2 or type(receipt['league_year']) is not int:
                raise ValueError('Invalid calendar release receipt')
            if original.obligation_id!=_identity_cash(receipt['generation_id'],player):
                raise ValueError('Calendar release cash identity mismatch')
            projected['release'].update(format=2,generation_id=receipt['generation_id'],league_year=receipt['league_year'])
        target=CashObligation.from_dict(projected['release']['cash']['obligations'][0])
        if target.paid!=original.paid or target.paid_components!=original.paid_components or target.amount>original.amount:
            raise ValueError('Release changed settled cash or increased nominal liability')
    elif operation=='manual_restructure':
        expected=_identity_cash(result['generation_id'],player) if 'generation_id' in result else 'contract:'+player
        projected['restructure']=_participant(result['restructure'],player,'restructures','cash_obligation',expected)
    elif operation=='manual_trade':
        seller,buyer=result['seller'],result['buyer']
        if seller==buyer or set(result['trade'])!={seller,buyer}:
            raise ValueError('Exact paired trade participants required')
        source=_identity_cash(result['seller_generation_id'],player) if 'seller_generation_id' in result else 'contract:'+player
        destination=_identity_cash(result['buyer_generation_id'],player) if 'buyer_generation_id' in result else 'contract:'+player
        projected['trade']={seller:_participant(result['trade'][seller],player,'outgoing_trades','seller_cash',source),
            buyer:_participant(result['trade'][buyer],player,'incoming_trades','buyer_cash',destination)}
        outgoing=projected['trade'][seller]['financial']['outgoing_trades'][player]
        incoming=projected['trade'][buyer]['financial']['incoming_trades'][player]
        if _canonical(outgoing)!=_canonical(incoming):
            raise ValueError('Paired lifecycle archives disagree')
    else:
        raise ValueError('Compact receipt unsupported for this operation')
    return projected
