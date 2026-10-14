"""Preserved original-game schedules; never reinterpret them as modern deals.

Raw terms reconstruct the original static cap calculations; actual calendar
aging remains unverified. No paid cash or modern base protection is inferred.
Lifecycle conversion remains unsupported.
"""
from dataclasses import asdict, dataclass
import struct

def _float32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def original_annual_rows(amount_word: int, bonus_code: int, shape_code: int, years: int) -> list:
    """Original E6020/E6040 rules in whole thousands, not modern accounting.

    Raw schedule codes0..7. Only codes1/2 have calibrated UI style names.
    Explicit float stores and final truncation match
    the guest's x87/SSE conversion boundaries. No rounding residual is repaired.
    """
    if any(type(value) is not int for value in (amount_word, bonus_code, shape_code, years)):
        raise ValueError('Original contract inputs must be integers')
    if not 1 <= amount_word <= 65535 or not 0 <= bonus_code <= 10 or not 0 <= shape_code <= 7 or not 1 <= years <= 15:
        raise ValueError('Unsupported original contract inputs')
    average = int(_float32(amount_word * 10 / years))
    bonus = amount_word * bonus_code // years
    base = average - bonus
    rows = []
    for index in range(years):
        salary = base
        position, midpoint = index + 0.5, years * 0.5
        if shape_code in (0, 7):
            factor = 12 if position < midpoint else 8 if position > midpoint else 10
            if shape_code == 7:
                factor = 20 - factor
            salary = base * factor // 10
        elif shape_code in (1, 6):
            fraction = _float32(2 * ((index + 0.5) / years) - 1)
            direction = -1 if shape_code == 1 else 1
            salary = int(_float32(base + direction * (base // 2) * fraction))
        elif shape_code in (3, 4) and years > 1:
            offset = position if position <= midpoint else position - midpoint
            fraction = _float32(2 * offset / midpoint - 1)
            direction = 1 if position <= midpoint else -1
            if shape_code == 4:
                direction = -direction
            salary = int(_float32(base + direction * (base // 2) * fraction))
        elif shape_code == 5 and years > 1:
            salary = base * (12 if index % 2 == 0 else 8) // 10
        rows.append({'contract_year_index': index, 'salary_dollars': salary * 1000,
                     'allocated_bonus_dollars': bonus * 1000,
                     'original_game_charge_dollars': (salary + bonus) * 1000})
    return rows



@dataclass(frozen=True)
class LegacyContract:
    player_id: str
    amount_word: int
    bonus_code: int
    shape_code: int
    original_years: int
    remaining_years: int
    source: str

    def __post_init__(self):
        if any(type(value) is not str or not value.strip() for value in (self.player_id, self.source)):
            raise ValueError('Stable legacy player identity and source required')
        original_annual_rows(self.amount_word, self.bonus_code, self.shape_code, self.original_years)
        if type(self.remaining_years) is not int or not 1 <= self.remaining_years <= self.original_years:
            raise ValueError('Legacy active contract requires supported remaining term')

    def charges(self):
        rows = original_annual_rows(self.amount_word, self.bonus_code, self.shape_code, self.original_years)
        return tuple(row['original_game_charge_dollars'] for row in rows[self.original_years-self.remaining_years:])

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        if type(data) is not dict or set(data) != {'player_id','amount_word','bonus_code','shape_code',
                                                 'original_years','remaining_years','source'}:
            raise ValueError('Complete original legacy contract record required')
        return cls(**data)
