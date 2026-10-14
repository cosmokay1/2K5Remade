"""Approved 2004-dollar adaptation of sourced modern rule amounts.

This is a simulation conversion, not an NFL rule. Original contracts/cap are
not rewritten. Future game-calendar synchronization remains the adapter's job.
"""
from dataclasses import dataclass
from fractions import Fraction

from franchise.minimums import minimum_schedule
from franchise.rookie import RookieScale, UndraftedScale

REFERENCE_YEAR = 2026
REFERENCE_CAP = 301200000
CAP_SOURCE = 'https://www.nfl.com/news/nfl-announces-2026-salary-cap-set-at-301-2-million-per-team'
POLICY = '2004-economy-2026-reference-v1'


@dataclass(frozen=True)
class HistoricalEconomy:
    target_cap: int

    def __post_init__(self):
        if type(self.target_cap) is not int or self.target_cap <= 0:
            raise ValueError('Verified positive integer franchise cap required')

    @property
    def ratio(self):
        return Fraction(self.target_cap, REFERENCE_CAP)

    def _post(self, amount, *, round_up):
        if type(amount) is not int or amount < 0:
            raise ValueError('Nonnegative integer sourced dollar amount required')
        units = Fraction(amount * self.target_cap, REFERENCE_CAP * 1000)
        # Original annual charges post in thousands. Ceil minimums; floor
        # spending ceilings so conversion cannot silently loosen either bound.
        count = units.numerator // units.denominator
        if round_up and units.numerator % units.denominator:
            count += 1
        return count * 1000

    def minimum(self, amount):
        return self._post(amount, round_up=True)

    def ceiling(self, amount):
        return self._post(amount, round_up=False)

    def minimum_schedule(self, game_start_year, credited_seasons, roster_categories):
        if type(game_start_year) is not int or game_start_year < 2004:
            raise ValueError('Supported game season starts at 2004')
        source_year = REFERENCE_YEAR + game_start_year - 2004
        return tuple(self.minimum(amount) for amount in
                     minimum_schedule(source_year, credited_seasons, roster_categories))

    def drafted_rookie(self, modern: RookieScale):
        if not isinstance(modern, RookieScale):
            raise ValueError('Typed sourced rookie allotment required')
        minimums = minimum_schedule(REFERENCE_YEAR, (0,)*4, ('active_inactive',)*4)
        if modern.minimum_salaries != minimums:
            raise ValueError('Rookie inputs must use the reference-year published minimums')
        return RookieScale(modern.draft_round, tuple(self.minimum(v) for v in minimums),
                           self.minimum(modern.year_one_minimum),
                           self.ceiling(modern.year_one_maximum), self.ceiling(modern.total_maximum))

    def undrafted_rookie(self):
        return UndraftedScale(self.minimum_schedule(2004, (0,)*3, ('active_inactive',)*3))

    def to_dict(self):
        return {'policy': POLICY, 'target_cap_dollars': self.target_cap,
                'reference_year': REFERENCE_YEAR, 'reference_cap_dollars': REFERENCE_CAP,
                'reference_cap_source': CAP_SOURCE,
                'posting': '1000-dollar units; minimums up, ceilings down',
                'scope': 'simulation adaptation; no original contract rewrite or game synchronization'}

    @classmethod
    def from_dict(cls, data):
        if type(data) is not dict or 'target_cap_dollars' not in data:
            raise ValueError('Complete historical economy policy required')
        economy = cls(data['target_cap_dollars'])
        if data != economy.to_dict():
            raise ValueError('Unsupported historical economy version, source or posting policy')
        return economy
