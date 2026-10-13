"""Drafted-rookie proposal checks for the base salary + signing bonus subset.

Annual allotments/minimums must be supplied from a verified season ruleset.
Ledger uses this validator before its atomic team-cap/club-pool commit.
Full base guarantees include the required preceding-year protection rule.
Conditional protections, incentives, options and escalators remain incomplete.
"""
from dataclasses import dataclass
from fractions import Fraction
from franchise.cap import Offer, Rejected, money


def validate_rookie_guarantees(offer: Offer):
    """Article 7 section 3(h), base-plus-traditional-bonus subset only.

    Year-three/four protection requires fully protected preceding-year base;
    traditional signing bonus is already a committed component in this subset.
    Conditional bonus entitlement/forfeiture requires separate treatment.
    """
    guarantees = offer.guaranteed_salaries or (0,) * len(offer.salaries)
    for year in range(2, len(offer.salaries)):
        if guarantees[year] > 0 and guarantees[year - 1] != offer.salaries[year - 1]:
            raise Rejected("Later rookie guarantee requires full preceding-year protection")


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

    def pool_charges(self, offer: Offer):
        return offer.charges(4)

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
        validate_rookie_guarantees(offer)
        if any(salary < minimum for salary, minimum
               in zip(offer.salaries, self.minimum_salaries)):
            raise Rejected("Rookie offer is below an annual minimum salary")
        # Fractions keep the 25% boundary exact, including fractional bonus shares.
        charges = offer.charges(4)
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


@dataclass(frozen=True)
class UndraftedScale:
    minimum_salaries: tuple[int, int, int]

    def __post_init__(self):
        if type(self.minimum_salaries) is not tuple or len(self.minimum_salaries) != 3:
            raise ValueError("Three verified annual UDFA minimum salaries required")
        if any(money(value) == 0 for value in self.minimum_salaries):
            raise ValueError("UDFA minimum salaries must be positive")

    @property
    def fifth_year_option_eligible(self):
        return False

    def pool_charges(self, offer: Offer):
        return tuple(charge - minimum for charge, minimum in zip(offer.charges(4), self.minimum_salaries))

    def validate(self, offer: Offer, *, club_year_one_remaining, club_total_remaining,
                 club_undrafted_bonus_remaining):
        if len(offer.salaries) != 3:
            raise Rejected("Undrafted rookie contracts must cover exactly three years")
        if any(salary < minimum for salary, minimum in zip(offer.salaries, self.minimum_salaries)):
            raise Rejected("UDFA offer is below an annual minimum salary")
        validate_rookie_guarantees(offer)
        charges = self.pool_charges(offer)
        if any(charges[i] - charges[i - 1] > charges[0] / 4 for i in range(1, 3)):
            raise Rejected("UDFA raise exceeds 25% of year-one rookie salary")
        if charges[0] > club_year_one_remaining or sum(charges) > club_total_remaining:
            raise Rejected("UDFA offer exceeds remaining club rookie allocation")
        if offer.signing_bonus > club_undrafted_bonus_remaining:
            raise Rejected("UDFA signing bonus exceeds remaining undrafted reservation")
