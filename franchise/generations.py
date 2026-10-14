"""Immutable team-book identity, independent of contract terms and payments."""
from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class GenerationIdentity:
    generation_id: str
    player_id: str
    cash_obligation_id: str

    def __post_init__(self):
        if any(type(value) is not str or not value.strip() for value in
               (self.generation_id,self.player_id,self.cash_obligation_id)):
            raise ValueError('Stable contract generation, player and cash identities required')


def legacy_identity(team_id, player_id):
    if any(type(value) is not str or not value.strip() for value in (team_id,player_id)):
        raise ValueError('Stable team and player identities required')
    material = json.dumps([team_id,player_id],ensure_ascii=False,separators=(',',':')).encode('utf-8')
    return GenerationIdentity('legacy-contract:' + hashlib.sha256(material).hexdigest(),
                              player_id,'contract:' + player_id)
