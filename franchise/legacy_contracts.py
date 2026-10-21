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
    game_dollar_scale: int = 1

    def __post_init__(self):
        if any(type(value) is not str or not value.strip() for value in (self.player_id, self.source)):
            raise ValueError('Stable legacy player identity and source required')
        if type(self.game_dollar_scale) is not int or self.game_dollar_scale not in (1, 4):
            raise ValueError('Supported original or verified four-to-one money scale required')
        original_annual_rows(self.amount_word, self.bonus_code, self.shape_code, self.original_years)
        if type(self.remaining_years) is not int or not 1 <= self.remaining_years <= self.original_years:
            raise ValueError('Legacy active contract requires supported remaining term')

    def charges(self):
        rows = original_annual_rows(self.amount_word, self.bonus_code, self.shape_code, self.original_years)
        return tuple(row['original_game_charge_dollars'] * self.game_dollar_scale
                     for row in rows[self.original_years-self.remaining_years:])

    def to_dict(self):
        result = asdict(self)
        # Preserve existing checkpoint hashes and wire records at retail scale.
        if self.game_dollar_scale == 1:
            del result['game_dollar_scale']
        return result

    @classmethod
    def from_dict(cls, data):
        fields = {'player_id','amount_word','bonus_code','shape_code',
                  'original_years','remaining_years','source'}
        if type(data) is not dict or set(data) not in (fields, fields | {'game_dollar_scale'}):
            raise ValueError('Complete original legacy contract record required')
        return cls(**data)


def imported_components(books, contract):
    """Source-backed base/non-base differences from the native approximation.

    These named opening records belong to the original agreement only. Once it
    is amended, the agreement carries its non-base obligations and replaces the
    base; replay must not apply either representation correction a second time.
    """
    raw=original_annual_rows(contract.amount_word,contract.bonus_code,contract.shape_code,contract.original_years)[-contract.remaining_years:]
    zero=(0,)*len(raw)
    values={r.record_id:r.annual_charges for r in books.adjustments}
    base=values.get('native-base:'+contract.player_id,zero)
    nonbase=values.get('native-nonbase:'+contract.player_id,zero)
    if len(base)!=len(raw) or len(nonbase)!=len(raw):
        raise ValueError('Imported correction horizon differs from remaining native agreement')
    salary=tuple(r['salary_dollars']*contract.game_dollar_scale+b for r,b in zip(raw,base))
    other=tuple(r['allocated_bonus_dollars']*contract.game_dollar_scale+b for r,b in zip(raw,nonbase))
    if any(s<0 or s+o<0 for s,o in zip(salary,other)):
        raise ValueError('Imported source cannot create negative salary or cap liability')
    return salary,other
