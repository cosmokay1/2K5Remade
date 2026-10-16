"""Bounded fictional offer reactions; no clock, cap or participation effects."""
import math


def reaction_effect(relationships, reaction):
    if reaction == 'none':
        return None
    if reaction != 'offended':
        raise ValueError('Unknown negotiation reaction')
    before = relationships.get('respect')
    if type(before) not in (int, float) or not math.isfinite(before) or not 0 <= before <= 1:
        raise ValueError('Recorded respect required for an offended reaction')
    return dict(policy='offer-reaction-v1', relationship='respect', before=before,
                after=round(max(0, before - 0.05), 6))


def apply_reaction(actor, event):
    reaction = event.get('reaction', 'none')
    evidence = event.get('evidence', {})
    effect = reaction_effect(evidence.get('relationships', {}), reaction)
    if effect is None:
        if 'reaction_effect' in event:
            raise ValueError('Neutral negotiation cannot claim an opinion change')
        return
    # Narrative cannot supply arbitrary relationship deltas or alter another
    # actor. Exact recorded inputs also protect against concurrent opinion edits.
    import json
    canonical = lambda value: json.dumps(value, sort_keys=True, allow_nan=False)
    if canonical(event.get('reaction_effect')) != canonical(effect):
        raise ValueError('Negotiation reaction effect disagrees with its policy')
    if actor is None or any(canonical(actor[key]) != canonical(evidence.get(key))
                            for key in ('personality', 'relationships')):
        raise ValueError('Negotiation reaction actor context changed')
    actor['relationships']['respect'] = effect['after']
