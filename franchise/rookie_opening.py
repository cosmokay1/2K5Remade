"""Explicit current draft-class allocation and original-contract reconciliation."""
from dataclasses import dataclass
from fractions import Fraction
from franchise.cap import money
from franchise.rookie import UndraftedScale
from franchise.books import ActiveContract, OpeningBooks


@dataclass(frozen=True)
class RookiePoolOpening:
    league_year: int
    cohort_player_ids: frozenset[str]
    year_one_allocation: int
    total_allocation: int
    undrafted_reservation: int
    source: str
    prior_contracts: tuple[ActiveContract, ...]

    def __post_init__(self):
        if type(self.league_year) is not int or not 2020 <= self.league_year <= 2030:
            raise ValueError("Published CBA cohort year required")
        if type(self.cohort_player_ids) is not frozenset or any(type(player) is not str or not player.strip() for player in self.cohort_player_ids):
            raise ValueError("Explicit immutable cohort identities required")
        if type(self.prior_contracts) is not tuple or any(not isinstance(item, ActiveContract) for item in self.prior_contracts):
            raise ValueError("Explicit prior current-cohort contract records required")
        if len({item.offer.player_id for item in self.prior_contracts}) != len(self.prior_contracts):
            raise ValueError("Multiple prior contracts for a rookie require unsupported reconciliation")
        if not {item.offer.player_id for item in self.prior_contracts} <= self.cohort_player_ids:
            raise ValueError("Prior contract is outside declared cohort")
        for value in (self.year_one_allocation, self.total_allocation, self.undrafted_reservation):
            money(value)
        if type(self.source) is not str or not self.source.strip():
            raise ValueError("Annual rookie allocation/cohort provenance required")
        if (self.undrafted_reservation > self.total_allocation
                or Fraction(self.undrafted_reservation, 3) > self.year_one_allocation):
            raise ValueError("Reservation exceeds full club allocations")

    def derive_remaining(self, contracts, rookies):
        if not self.cohort_player_ids <= rookies.keys():
            raise ValueError("Cohort contains unregistered rookies")
        if not (rookies.keys() - contracts.keys()) <= self.cohort_player_ids:
            raise ValueError("Unsigned rookie lacks current cohort classification")
        contracts = dict(contracts)
        for contract in self.prior_contracts:
            if contract.offer.player_id in contracts:
                raise ValueError("Active and prior rookie contracts overlap; replacement history unsupported")
            contracts[contract.offer.player_id] = contract
        used_one = Fraction(0)
        used_total = drafted_total = drafted_one = bonus_used = 0
        for player in self.cohort_player_ids & contracts.keys():
            contract, scale = contracts[player], rookies[player]
            if contract.elapsed_years != 0:
                raise ValueError("Current cohort contract has elapsed league years")
            if contract.charges() != contract.offer.charges(4):
                raise ValueError("Current rookie contract proration disagrees with required term")
            arguments = dict(club_year_one_remaining=self.year_one_allocation,
                             club_total_remaining=self.total_allocation)
            if isinstance(scale, UndraftedScale):
                arguments["club_undrafted_bonus_remaining"] = self.undrafted_reservation
            scale.validate(contract.offer, **arguments)
            charges = scale.pool_charges(contract.offer)
            used_one += charges[0]
            used_total += int(sum(charges))
            if isinstance(scale, UndraftedScale):
                bonus_used += contract.offer.signing_bonus
            else:
                drafted_one += charges[0]
                drafted_total += int(sum(charges))
        if (used_one > self.year_one_allocation or used_total > self.total_allocation
                or bonus_used > self.undrafted_reservation
                or drafted_one > self.year_one_allocation - Fraction(self.undrafted_reservation, 3)
                or drafted_total > self.total_allocation - self.undrafted_reservation):
            raise ValueError("Opening rookie contracts exceed source allocation/reservation")
        return (Fraction(self.year_one_allocation) - used_one,
                self.total_allocation - used_total, self.undrafted_reservation - bonus_used)

    def to_dict(self):
        return {"league_year": self.league_year, "cohort_player_ids": sorted(self.cohort_player_ids),
                "year_one_allocation": self.year_one_allocation, "total_allocation": self.total_allocation,
                "undrafted_reservation": self.undrafted_reservation, "source": self.source,
                "prior_contracts": [{"offer": item.offer.to_dict(), "source": item.source,
                                     "elapsed_years": item.elapsed_years, "bonus_years": item.bonus_years}
                                    for item in self.prior_contracts]}

    @classmethod
    def from_dict(cls, data):
        if type(data) is not dict or set(data) != {"league_year", "cohort_player_ids", "year_one_allocation", "total_allocation", "undrafted_reservation", "source", "prior_contracts"}:
            raise ValueError("Invalid rookie opening fields")
        players = data["cohort_player_ids"]
        if type(players) is not list or any(type(player) is not str for player in players) or len(set(players)) != len(players):
            raise ValueError("Unique cohort identity list required")
        prior = OpeningBooks.from_dict({"contracts": data["prior_contracts"], "retained": [], "adjustments": [], "tenders": []}).contracts
        return cls(**{**data, "cohort_player_ids": frozenset(players), "prior_contracts": prior})
