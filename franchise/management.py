"""Authored team/GM priorities, independent of player ratings and cap authority."""
from dataclasses import dataclass
import math

PRIORITIES = frozenset({'win_now', 'development', 'continuity', 'financial_flexibility', 'risk_tolerance'})


@dataclass(frozen=True)
class ManagementProfile:
    manager_id: str
    source: str
    priorities: tuple[tuple[str, int | float], ...]

    def __post_init__(self):
        if any(type(value) is not str or not value.strip() for value in (self.manager_id, self.source)):
            raise ValueError('Stable manager identity and authored-priority provenance required')
        if type(self.priorities) is not tuple or not self.priorities:
            raise ValueError('Immutable management priorities required')
        seen = set()
        for item in self.priorities:
            if type(item) is not tuple or len(item) != 2:
                raise ValueError('Priority name/value pair required')
            key, value = item
            if type(key) is not str or key not in PRIORITIES or key in seen:
                raise ValueError('Unknown or duplicate management priority')
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError('Management priorities must be finite values from zero to one')
            seen.add(key)

    def to_dict(self):
        return {'manager_id': self.manager_id, 'source': self.source, 'priorities': dict(self.priorities)}

    @classmethod
    def from_dict(cls, data):
        if type(data) is not dict or set(data) != {'manager_id', 'source', 'priorities'} or type(data['priorities']) is not dict:
            raise ValueError('Invalid management profile fields')
        return cls(data['manager_id'], data['source'], tuple(data['priorities'].items()))
