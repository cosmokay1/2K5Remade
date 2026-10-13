"""Drafted-rookie proposal checks for the base salary + signing bonus subset.

Annual allotments/minimums must be supplied from a verified season ruleset.
Ledger uses this validator before its atomic team-cap/club-pool commit.
Guarantees, incentives, options, and escalators need separate implementations.
"""
from dataclasses import dataclass
from fractions import Fraction
from franchise.cap import Offer, Rejected, money


@dataclass(frozen=True)
class RookieScale:
    draft_round: int
    minimum_salaries: tuple[int, int, int, int]
    year_one_minimum: int
    year_one_maximum: int
    total_maximum: int

    def __post_init__(self):
        if type(self.draft_round) is not int or not 1 <= self.draft_round <= 7:
            raise ValueError("This validator supports drafted rookies in rounds 1-7")
        if type(self.minimum_salaries) is not tuple or len(self.minimum_salaries) != 4:
            raise ValueError("Four verified annual minimum salaries are required")
        for amount in (*self.minimum_salaries, self.year_one_minimum,
                       self.year_one_maximum, self.total_maximum):
            money(amount)
        if self.year_one_minimum > self.year_one_maximum:
            raise ValueError("Year-one minimum exceeds maximum")

    @property
    def fifth_year_option_eligible(self) -> bool:
        return self.draft_round == 1

    def validate(self, offer: Offer, *, club_year_one_remaining: int | Fraction,
                 club_total_remaining: int) -> None:
        if isinstance(club_year_one_remaining, Fraction):
            if club_year_one_remaining < 0:
                raise ValueError("Rookie allocation cannot be negative")
        else:
            money(club_year_one_remaining)
        money(club_total_remaining)
        if len(offer.salaries) != 4:
            raise Rejected("Drafted rookie contracts must cover exactly four years")
        if any(salary < minimum for salary, minimum
               in zip(offer.salaries, self.minimum_salaries)):
            raise Rejected("Rookie offer is below an annual minimum salary")
        # Fractions keep the 25% boundary exact, including fractional bonus shares.
        charges = tuple(Fraction(salary) + Fraction(offer.signing_bonus, 4)
                        for salary in offer.salaries)
        if not self.year_one_minimum <= charges[0] <= self.year_one_maximum:
            raise Rejected("Rookie offer is outside its year-one allotment bounds")
        total = sum(offer.salaries) + offer.signing_bonus
        if total > self.total_maximum:
            raise Rejected("Rookie offer exceeds total compensation limit")
        minimum_only = offer.signing_bonus == 0 and offer.salaries == self.minimum_salaries
        if not minimum_only and any(charges[i] - charges[i - 1] > charges[0] / 4
                                    for i in range(1, 4)):
            raise Rejected("Rookie raise exceeds 25% of year-one rookie salary")
        if charges[0] > club_year_one_remaining or total > club_total_remaining:
            raise Rejected("Rookie offer exceeds remaining club rookie allocation")
