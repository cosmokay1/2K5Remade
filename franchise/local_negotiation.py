"""Local bargaining against an explicit asking contract, without model calls.

The caller supplies a priced demand; this module does not invent market prices
from missing performance evidence. Ledger remains the authority for minima,
rookie rules, earned pay, cap, guest encoding and commits.

history_start is an explicit cursor into the player's durable negotiation
history. It scopes one bargaining window. local_runtime persists that cursor in
the existing decision journal and reopens windows using saved simulation time;
recreating this provider does not clear history or expire a refusal.
"""
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math

from franchise.cap import Offer
from franchise.negotiation import Decision, validate_performance
from franchise.promises import goals_from_list


def _priority(values, key, default=0.5):
    value = values.get(key, default)
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f'Local negotiation requires {key} between zero and one')
    return Fraction(str(value))


def _annual_value(offer):
    return Fraction(sum(offer.salaries) + offer.signing_bonus, len(offer.salaries))


def _protected_value(offer):
    return offer.signing_bonus + sum(offer.guaranteed_salaries)


@dataclass(frozen=True)
class LocalNegotiationProvider:
    demand: Offer
    history_start: int = 0

    def __post_init__(self):
        if not isinstance(self.demand, Offer) or _annual_value(self.demand) <= 0:
            raise ValueError('An explicit positive asking contract is required')
        if type(self.history_start) is not int or self.history_start < 0:
            raise ValueError('A nonnegative bargaining-window history cursor is required')

    def __call__(self, context):
        if type(context) is not dict:
            raise ValueError('Negotiation context must be an object')
        validate_performance(context)
        offer = Offer.from_dict(context['offer'])
        if context['player_id'] != self.demand.player_id or offer.player_id != self.demand.player_id:
            raise ValueError('Asking contract and offer must belong to this player')
        personality, relationships = context['personality'], context['relationships']
        if type(personality) is not dict or type(relationships) is not dict:
            raise ValueError('Recorded personality and relationships are required')
        if 'respect' not in relationships:
            raise ValueError('Recorded respect is required for local offer reactions')
        money = _priority(personality, 'money')
        security = _priority(personality, 'security')
        patience = _priority(personality, 'patience')
        loyalty = _priority(personality, 'loyalty')
        trust = _priority(relationships, 'trust')
        respect = _priority(relationships, 'respect')
        history = context['history']
        if type(history) is not list or self.history_start > len(history):
            raise ValueError('Bargaining-window cursor exceeds recorded history')
        seen = set()
        for event in history:
            if (type(event) is not dict or type(event.get('request_id')) is not str
                    or not event['request_id'] or event['request_id'] in seen
                    or type(event.get('offer')) is not dict
                    or event['offer'].get('player_id') != self.demand.player_id):
                raise ValueError('Unique recorded negotiation history for this player is required')
            seen.add(event['request_id'])
        recent = history[self.history_start:]
        proposed = context.get('promise_goals', [])
        goals_from_list(proposed)  # Counteroffers preserve these proposals exactly.

        def reply(action, messages, *, reaction='none'):
            # Stable variation: retrying the same context cannot reroll its voice.
            material = json.dumps([self.demand.player_id, offer.to_dict(),
                                   [event['request_id'] for event in history], action, messages],
                                  sort_keys=True, allow_nan=False).encode()
            reason = messages[int.from_bytes(hashlib.sha256(material).digest()[:4], 'big') % len(messages)]
            counter = action == 'counter'
            result = dict(action=action, reason=reason, reaction=reaction,
                          salaries=list(self.demand.salaries) if counter else None,
                          signing_bonus=self.demand.signing_bonus if counter else None,
                          guaranteed_salaries=list(self.demand.guaranteed_salaries) if counter else None,
                          promise_goals=proposed if counter else None)
            text = json.dumps(result, allow_nan=False)
            Decision.parse(text, self.demand.player_id)
            return text

        if any(event.get('reaction') == 'offended' for event in recent):
            return reply('reject', (
                "We stepped away after the earlier offer. We're not reopening these talks in this window.",
                "Raising the number doesn't erase the earlier offer. We're not continuing these talks right now.",
            ))
        # Two to four submissions per explicitly scoped bargaining window.
        rounds = 2 + int(patience >= Fraction(1, 3)) + int(patience >= Fraction(2, 3))
        if len(recent) >= rounds:
            return reply('reject', (
                "We've been through enough revisions for now. We're stepping away from this round of talks.",
                "We aren't going to keep trading offers in this window. Let's leave it here for now.",
            ))
        if _annual_value(offer) < _annual_value(self.demand) * Fraction(13, 20):
            return reply('reject', (
                "That is well below what we're asking for. We're stepping away from these talks.",
                "That offer doesn't take our asking terms seriously. We're not continuing this round of talks.",
            ), reaction='offended')
        if len(offer.salaries) != len(self.demand.salaries):
            return reply('counter', (
                f"We're looking for a {len(self.demand.salaries)}-year agreement. These are the terms we'd discuss.",
            ))
        discount = Fraction(1, 20) * (1-money) * loyalty * trust * respect
        if _annual_value(offer) < _annual_value(self.demand) * (1-discount):
            return reply('counter', (
                "The money is still short of what we're seeking. We'd discuss this agreement at these terms.",
                "We can keep talking, but the value needs to come up. Here's what we're asking for.",
            ))
        security_floor = _protected_value(self.demand) * (Fraction(1, 2) + security/2)
        if _protected_value(offer) < security_floor:
            return reply('counter', (
                "We need more of this agreement protected. The headline value alone isn't enough for us.",
                "The value is workable, but we need more security in the agreement. These terms address that.",
            ))
        return reply('accept', (
            "Those are terms we can agree to. Let's move forward with the paperwork.",
            "We can agree to this offer. Let's get the agreement finalized.",
        ))
