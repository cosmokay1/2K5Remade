"""Experimental free-agent signing ledger, independent of Remade.

This is a configurable accounting model, not an NFL rules implementation.
Release, trade, restructure, guarantees, and game-save writes are unsupported.
All money is integer dollars. Only the current cap is binding; future charges
are reported without assuming future league caps.
"""
from dataclasses import asdict, dataclass
from fractions import Fraction
from threading import RLock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from franchise.rookie import RookieScale


def money(value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("Money must be a nonnegative integer")
    return value


@dataclass(frozen=True)
class Offer:
    player_id: str
    salaries: tuple[int, ...]
    signing_bonus: int

    def __post_init__(self):
        if not isinstance(self.player_id, str) or not self.player_id.strip():
            raise ValueError("A stable player ID is required")
        if type(self.salaries) is not tuple or not self.salaries:
            raise ValueError("At least one annual salary is required as a tuple")
        for salary in self.salaries:
            money(salary)
        money(self.signing_bonus)

    def charges(self, max_bonus_years: int) -> tuple[int, ...]:
        if type(max_bonus_years) is not int or not 1 <= max_bonus_years <= 5:
            raise ValueError("Bonus allocation limit must be between one and five years")
        years = min(len(self.salaries), max_bonus_years)
        amount, remainder = divmod(self.signing_bonus, years)
        # Allocate leftover dollars to earliest years; never lose bonus money.
        return tuple(salary + (amount + (i < remainder) if i < years else 0)
                     for i, salary in enumerate(self.salaries))


@dataclass(frozen=True)
class Signing:
    request_id: str
    offer: Offer
    charges: tuple[int, ...]
    revision: int


class Rejected(ValueError):
    pass


class Ledger:
    def __init__(self, *, cap: int, existing_charges: tuple[int, ...],
                 roster_reserve: int, max_bonus_years: int,
                 veteran_minimums: dict[str, tuple[int, ...]],
                 signed_player_ids: frozenset[str] = frozenset(),
                 rookies: dict[str, "RookieScale"] | None = None,
                 rookie_year_one_allocation: int | None = None,
                 rookie_total_allocation: int | None = None):
        self._cap = money(cap)
        self._roster_reserve = money(roster_reserve)
        if type(existing_charges) is not tuple or not existing_charges:
            raise ValueError("Existing obligations must include the current year")
        self._charges = tuple(money(value) for value in existing_charges)
        if type(max_bonus_years) is not int or not 1 <= max_bonus_years <= 5:
            raise ValueError("Bonus allocation limit must be between one and five years")
        self._max_bonus_years = max_bonus_years
        self._veteran_minimums = dict(veteran_minimums)
        for player_id, minimums in self._veteran_minimums.items():
            if type(player_id) is not str or not player_id.strip():
                raise ValueError("Veterans require stable player IDs")
            if type(minimums) is not tuple or not minimums:
                raise ValueError("Verified annual veteran minimums are required")
            if any(money(amount) == 0 for amount in minimums):
                raise ValueError("Veteran minimum salaries must be positive")
        self._players = set(signed_player_ids)
        self._requests: dict[str, Signing] = {}
        self.revision = 0
        self._lock = RLock()
        self._rookies = dict(rookies or {})
        if self._rookies.keys() & self._veteran_minimums.keys():
            raise ValueError("A player cannot be classified as both rookie and veteran")
        known = self._rookies.keys() | self._veteran_minimums.keys()
        if not self._players <= known:
            raise ValueError("Signed players must exist in the player registry")
        if self._rookies and (rookie_year_one_allocation is None
                              or rookie_total_allocation is None):
            raise ValueError("Drafted rookies require both club rookie allocations")
        self._rookie_year_one = Fraction(money(
            0 if rookie_year_one_allocation is None else rookie_year_one_allocation))
        self._rookie_total = money(
            0 if rookie_total_allocation is None else rookie_total_allocation)
        if self._players & self._rookies.keys():
            raise ValueError("Rookie registry must contain unsigned draft picks only")
        from franchise.rookie import RookieScale
        if any(not isinstance(scale, RookieScale) for scale in self._rookies.values()):
            raise ValueError("Rookie registry must contain verified RookieScale records")

    @property
    def cap(self) -> int:
        return self._cap

    @property
    def roster_reserve(self) -> int:
        return self._roster_reserve

    @property
    def max_bonus_years(self) -> int:
        return self._max_bonus_years

    def update_budget(self, *, cap: int, roster_reserve: int,
                      expected_revision: int) -> None:
        cap, roster_reserve = money(cap), money(roster_reserve)
        with self._lock:
            if type(expected_revision) is not int or expected_revision != self.revision:
                raise Rejected("Budget change was based on stale franchise state")
            if cap < self._charges[0]:
                raise Rejected("Budget change would put the team over the cap")
            if (cap, roster_reserve) != (self._cap, self._roster_reserve):
                self._cap, self._roster_reserve = cap, roster_reserve
                self.revision += 1

    @property
    def rookie_remaining(self) -> tuple[Fraction, int]:
        with self._lock:
            return self._rookie_year_one, self._rookie_total

    def negotiation_context(self, player_id: str) -> dict:
        with self._lock:
            if player_id not in self._rookies and player_id not in self._veteran_minimums:
                raise Rejected("Player is unknown or contract classification is missing")
            scale = self._rookies.get(player_id)
            return {"revision": self.revision, "cap": self.cap, "room": self.room,
                    "annual_team_charges": list(self._charges),
                    "roster_reserve": self.roster_reserve,
                    "veteran_minimum_salaries": self._veteran_minimums.get(player_id),
                    "rookie_scale": asdict(scale) if scale else None,
                    "rookie_year_one_remaining": str(self._rookie_year_one),
                    "rookie_total_remaining": self._rookie_total,
                    "max_bonus_years": 4 if scale else self.max_bonus_years}

    @property
    def charges(self) -> tuple[int, ...]:
        return self._charges

    @property
    def room(self) -> int:
        return self.cap - self._charges[0] - self.roster_reserve

    def sign(self, request_id: str, offer: Offer, expected_revision: int,
             *, access_check=None) -> Signing:
        """Commit an affordable offer, including registered draft-pick constraints.

        A personality/LLM acceptance is an input to this call, not cap authority.
        The lock serializes validation and cap/pool deductions in this process.
        """
        with self._lock:
            if access_check is not None:
                access_check()
            return self._sign(request_id, offer, expected_revision)

    def _sign(self, request_id: str, offer: Offer, expected_revision: int) -> Signing:
        if not isinstance(request_id, str) or not request_id.strip():
            raise Rejected("A request ID is required")
        prior = self._requests.get(request_id)
        if prior is not None:
            if prior.offer != offer:
                raise Rejected("Request ID was already used for a different offer")
            return prior
        if type(expected_revision) is not int or expected_revision != self.revision:
            raise Rejected("Offer was based on stale franchise state")
        if offer.player_id in self._players:
            raise Rejected("Player is already signed; extensions are unsupported")
        scale = self._rookies.get(offer.player_id)
        if scale is not None:
            scale.validate(offer, club_year_one_remaining=self._rookie_year_one,
                           club_total_remaining=self._rookie_total)
        else:
            minimums = self._veteran_minimums.get(offer.player_id)
            if minimums is None:
                raise Rejected("Player is unknown or contract classification is missing")
            if len(offer.salaries) > len(minimums):
                raise Rejected("Missing minimum salary rules for offered contract years")
            if any(salary < minimum for salary, minimum in zip(offer.salaries, minimums)):
                raise Rejected("Veteran offer is below an annual minimum salary")
        charges = offer.charges(4 if scale is not None else self.max_bonus_years)
        if charges[0] > self.room:
            raise Rejected(f"Offer exceeds available cap room by {charges[0] - self.room}")
        years = max(len(charges), len(self._charges))
        updated = tuple(
            (self._charges[i] if i < len(self._charges) else 0)
            + (charges[i] if i < len(charges) else 0)
            for i in range(years)
        )
        receipt = Signing(request_id, offer, charges, self.revision + 1)
        self._charges = updated
        self._players.add(offer.player_id)
        self._requests[request_id] = receipt
        if scale is not None:
            self._rookie_year_one -= offer.salaries[0] + Fraction(offer.signing_bonus, 4)
            self._rookie_total -= sum(offer.salaries) + offer.signing_bonus
        self.revision += 1
        return receipt
