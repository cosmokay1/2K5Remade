"""Authored fictional personalities generated once for a new franchise."""
import hashlib
import random
import json

VERSION = 'franchise-personality-v1'
PRIORITIES = ('money','security','playing_time','winning','loyalty','patience','risk_tolerance')
STYLES = {
    'security_first': (0.6,0.85,0.5,0.5,0.6,0.7,0.2),
    'ambitious': (0.65,0.45,0.85,0.75,0.35,0.4,0.7),
    'team_rooted': (0.45,0.65,0.6,0.7,0.85,0.7,0.4),
    'market_driven': (0.85,0.55,0.65,0.5,0.3,0.45,0.6),
    'competitive': (0.55,0.5,0.75,0.9,0.5,0.55,0.65),
}


def validate_seed(seed):
    if type(seed) is not str or not seed.strip() or len(seed.encode('utf-8')) > 256:
        raise ValueError('Nonempty franchise seed of at most 256 UTF-8 bytes required')


def initial_actor(seed,player_id):
    validate_seed(seed)
    if type(player_id) is not str or not player_id.strip():
        raise ValueError('Stable player identity required')
    # Independent streams: roster order, team assignment and unrelated new players
    # cannot reroll an existing player's personality.
    material = json.dumps([VERSION,seed,player_id],ensure_ascii=False,separators=(',',':')).encode('utf-8')
    rng = random.Random(int.from_bytes(hashlib.sha256(material).digest(),'big'))
    style = rng.choice(sorted(STYLES))
    values = {key:round(max(0.05,min(0.95,base+rng.uniform(-0.15,0.15))),6)
              for key,base in zip(PRIORITIES,STYLES[style])}
    return {'personality':{**values,'negotiation_style':style,'generation_version':VERSION,
                           'source':'authored fictional franchise personality'},
            'relationships':{'trust':0.5,'respect':0.5,'team_connection':0.5}}
