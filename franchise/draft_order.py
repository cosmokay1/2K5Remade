"""Immutable, source-declared draft order and available prospect identities."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DraftSlot:
    overall_pick: int
    draft_round: int
    team_id: str

    def __post_init__(self):
        if type(self.overall_pick) is not int or self.overall_pick < 1 or type(self.draft_round) is not int or not 1 <= self.draft_round <= 7:
            raise ValueError('Explicit pick and round required')
        if type(self.team_id) is not str or not self.team_id.strip():
            raise ValueError('Stable drafting team required')


@dataclass(frozen=True)
class DraftOrder:
    draft_id: str
    league_year: int
    source: str
    slots: tuple[DraftSlot, ...]
    player_ids: frozenset[str]

    def __post_init__(self):
        if any(type(v) is not str or not v.strip() for v in (self.draft_id,self.source)):
            raise ValueError('Draft identity and order provenance required')
        if type(self.league_year) is not int or not 2020 <= self.league_year <= 2030:
            raise ValueError('Supported modern league year required')
        if type(self.slots) is not tuple or not self.slots or any(not isinstance(slot,DraftSlot) for slot in self.slots):
            raise ValueError('Immutable sourced draft slots required')
        if [slot.overall_pick for slot in self.slots] != list(range(1,len(self.slots)+1)):
            raise ValueError('Contiguous declared order starting with pick one required')
        if any(a.draft_round > b.draft_round for a,b in zip(self.slots,self.slots[1:])):
            raise ValueError('Draft rounds must not move backwards')
        if type(self.player_ids) is not frozenset or len(self.player_ids) < len(self.slots) or any(type(p) is not str or not p.strip() for p in self.player_ids):
            raise ValueError('Explicit available prospect identities required')

    def to_dict(self):
        return {'draft_id':self.draft_id,'league_year':self.league_year,'source':self.source,
                'slots':[{'overall_pick':s.overall_pick,'draft_round':s.draft_round,'team_id':s.team_id} for s in self.slots],
                'player_ids':sorted(self.player_ids)}

    @classmethod
    def from_dict(cls,data):
        if type(data) is not dict or set(data) != {'draft_id','league_year','source','slots','player_ids'}:
            raise ValueError('Invalid draft order fields')
        if type(data['slots']) is not list or type(data['player_ids']) is not list or len(set(data['player_ids'])) != len(data['player_ids']):
            raise ValueError('Invalid declared slots or prospect list')
        return cls(data['draft_id'],data['league_year'],data['source'],tuple(DraftSlot(**s) for s in data['slots']),frozenset(data['player_ids']))
