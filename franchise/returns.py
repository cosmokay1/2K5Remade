"""Explicit source scope for the supported same-year veteran return signing."""
from dataclasses import dataclass
from datetime import date

RETURN_EXCLUSIONS=frozenset({'extensions','rookie_contracts','guarantee_offsets','league_year_rollover'})


@dataclass(frozen=True)
class PreseasonReturnScope:
    league_year: int
    signed_on: date
    first_regular_season_game: date
    healthy: bool
    exclusions: frozenset[str]
    source: str

    def __post_init__(self):
        if (type(self.league_year) is not int or not 2020 <= self.league_year <= 2030
                or type(self.signed_on) is not date or type(self.first_regular_season_game) is not date
                or self.signed_on.year != self.league_year
                or self.first_regular_season_game.year != self.league_year
                or self.signed_on >= self.first_regular_season_game
                or self.healthy is not True or type(self.exclusions) is not frozenset
                or self.exclusions != RETURN_EXCLUSIONS
                or type(self.source) is not str or not self.source.strip()):
            raise ValueError('Explicit healthy same-year preseason veteran return scope required')
