"""Experimental free-agent signing ledger, independent of Remade.

This is a configurable accounting model, not an NFL rules implementation.
Release, trade, restructure, guarantees, and game-save writes are unsupported.
Offers use integer dollars; internal allocations use exact rational dollars. Only the current cap is binding; future charges
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


def json_amount(value: int | Fraction) -> int | str:
    """Exact JSON dollars: an integer or a numerator/denominator string."""
    value = Fraction(value)
    return value.numerator if value.denominator == 1 else str(value)


def money_text(value: int | Fraction) -> str:
    value = Fraction(value)
    if value.denominator == 1:
        return f"{value.numerator:,}"
    return f"{value.numerator:,}/{value.denominator:,}"


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

    def charges(self, max_bonus_years: int) -> tuple[Fraction, ...]:
        if type(max_bonus_years) is not int or not 1 <= max_bonus_years <= 5:
            raise ValueError("Bonus allocation limit must be between one and five years")
        years = min(len(self.salaries), max_bonus_years)
        amount = Fraction(self.signing_bonus, years)
        return tuple(Fraction(salary) + (amount if i < years else 0)
                     for i, salary in enumerate(self.salaries))


@dataclass(frozen=True)
class Signing:
    request_id: str
    offer: Offer
    charges: tuple[Fraction, ...]
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
                 rookie_total_allocation: int | None = None,
                 rookie_tenders: dict[str, int] | None = None,
                 opening_books=None, veteran_minimum_profile=None):
        self._cap = money(cap)
        self._roster_reserve = money(roster_reserve)
        if type(existing_charges) is not tuple or not existing_charges:
            raise ValueError("Existing obligations must include the current year")
        for value in existing_charges:
            if isinstance(value, Fraction):
                if value < 0:
                    raise ValueError("Existing charges cannot be negative")
            else:
                money(value)
        self._charges = tuple(existing_charges)
        self._opening_books = opening_books
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
        self._veteran_minimum_profile = veteran_minimum_profile
        if veteran_minimum_profile is not None:
            from franchise.salary_rules import VeteranMinimumProfile
            if not isinstance(veteran_minimum_profile, VeteranMinimumProfile):
                raise ValueError("Typed veteran salary profile required")
            if self._veteran_minimums != veteran_minimum_profile.floors():
                raise ValueError("Veteran minimums disagree with annual source profile")
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
        from franchise.rookie import RookieScale
        if any(not isinstance(scale, RookieScale) for scale in self._rookies.values()):
            raise ValueError("Rookie registry must contain verified RookieScale records")
        self._tenders = dict(rookie_tenders or {})
        if not self._tenders.keys() <= self._rookies.keys() or self._tenders.keys() & self._players:
            raise ValueError("Rookie tenders require registered unsigned draft picks")
        for amount in self._tenders.values():
            money(amount)
        if any(amount != self._rookies[player].minimum_salaries[0]
               for player, amount in self._tenders.items()):
            raise ValueError("Rookie tender must match the supplied first-year minimum salary")
        if sum(self._tenders.values()) > self._charges[0]:
            raise ValueError("Declared tenders exceed existing current-year charges")
        if opening_books is not None:
            from franchise.books import OpeningBooks
            if not isinstance(opening_books, OpeningBooks):
                raise ValueError("Typed opening books required")
            if (self._charges != opening_books.charges()
                    or self._players != {item.offer.player_id for item in opening_books.contracts}
                    or self._tenders != {item.player_id: item.amount for item in opening_books.tenders}):
                raise ValueError("Opening balances, ownership or tenders disagree with source books")

    @classmethod
    def from_opening(cls, books, **rules):
        return cls(existing_charges=books.charges(),
                   signed_player_ids=frozenset(item.offer.player_id for item in books.contracts),
                   rookie_tenders={item.player_id: item.amount for item in books.tenders},
                   opening_books=books, **rules)

    @property
    def cap(self) -> int:
        return self._cap

    def bootstrap_config(self) -> dict:
        """Export only a pristine ledger; committed history belongs in the store."""
        with self._lock:
            if self.revision != 0:
                raise ValueError("Create durable state before committing transactions")
            return {"cap": self.cap, "existing_charges": [json_amount(value) for value in self._charges],
                    "roster_reserve": self.roster_reserve,
                    "max_bonus_years": self.max_bonus_years,
                    "veteran_minimums": {key: list(value) for key, value
                                         in self._veteran_minimums.items()},
                    "signed_player_ids": sorted(self._players),
                    "rookies": {key: asdict(value) for key, value in self._rookies.items()},
                    "rookie_year_one_allocation": int(self._rookie_year_one),
                    "rookie_total_allocation": self._rookie_total,
                    "rookie_tenders": dict(self._tenders),
                    "veteran_minimum_profile": self._veteran_minimum_profile.to_dict() if self._veteran_minimum_profile else None,
                    "opening_books": self._opening_books.to_dict() if self._opening_books else None}

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
            return {"revision": self.revision, "cap": self.cap, "room": json_amount(self.room),
                    "annual_team_charges": [json_amount(value) for value in self._charges],
                    "roster_reserve": self.roster_reserve,
                    "veteran_minimum_salaries": self._veteran_minimums.get(player_id),
                    "salary_floor_profile": ({"start_year": self._veteran_minimum_profile.start_year,
                                              "rule_version": self._veteran_minimum_profile.rule_version,
                                              "source": self._veteran_minimum_profile.source}
                                             if self._veteran_minimum_profile else None),
                    "existing_player_tender": self._tenders.get(player_id, 0),
                    "room_for_replacing_player_tender": json_amount(self.room + self._tenders.get(player_id, 0)),
                    "rookie_scale": asdict(scale) if scale else None,
                    "rookie_year_one_remaining": str(self._rookie_year_one),
                    "rookie_total_remaining": self._rookie_total,
                    "max_bonus_years": 4 if scale else self.max_bonus_years}

    @property
    def charges(self) -> tuple[int | Fraction, ...]:
        return self._charges

    @property
    def room(self) -> int | Fraction:
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

    def commit_negotiation(self, request_id: str, offer: Offer, expected_revision: int,
                           *, access_check, story: dict):
        """In-memory commit; the durable adapter persists story with finances."""
        return self.sign(request_id, offer, expected_revision, access_check=access_check)

    def bind_actor(self, player_id, personality, relationships, *, access_check):
        self.negotiation_context(player_id)  # Require a registered player.
        return {"personality": personality, "relationships": relationships}

    def negotiation_history(self, player_id: str):
        return []

    def record_negotiation(self, event: dict, *, access_check):
        access_check()  # In-memory sessions retain their own dialogue.
        return event

    def recalled_negotiation(self, request_id: str, offer: Offer):
        return None  # In-memory sessions retain their own replies.

    def financial_snapshot(self) -> dict:
        with self._lock:
            return {"revision": self.revision, "cap": self.cap,
                    "roster_reserve": self.roster_reserve,
                    "charges": [json_amount(value) for value in self._charges], "signed_players": sorted(self._players),
                    "rookie_year_one_remaining": str(self._rookie_year_one),
                    "rookie_total_remaining": self._rookie_total,
                    "rookie_tenders": dict(self._tenders)}

    def _validate_offer(self, offer: Offer, expected_revision: int):
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
        tender = self._tenders.get(offer.player_id, 0)
        if charges[0] - tender > self.room:
            raise Rejected(f"Offer exceeds available cap room by {charges[0] - tender - self.room}")
        years = max(len(charges), len(self._charges))
        updated = tuple(
            (self._charges[i] if i < len(self._charges) else 0)
            + (charges[i] if i < len(charges) else 0)
            - (tender if i == 0 else 0)
            for i in range(years)
        )
        return charges, tender, updated, scale

    def preview_offer(self, offer: Offer, expected_revision: int) -> dict:
        """Validate current terms without reserving room or committing ownership.

        A preview is advisory: final signing must revalidate its revision.
        """
        with self._lock:
            charges, tender, updated, scale = self._validate_offer(offer, expected_revision)
            return {"revision": self.revision,
                    "contract_charges": [json_amount(value) for value in charges],
                    "replaced_tender": tender,
                    "annual_team_charges_after": [json_amount(value) for value in updated],
                    "room_after": json_amount(self.cap - updated[0] - self.roster_reserve),
                    "contract_cash": sum(offer.salaries) + offer.signing_bonus,
                    "rookie_year_one_after": json_amount(self._rookie_year_one - charges[0]) if scale else None,
                    "rookie_total_after": self._rookie_total - sum(offer.salaries) - offer.signing_bonus if scale else None}

    def _sign(self, request_id: str, offer: Offer, expected_revision: int) -> Signing:
        if not isinstance(request_id, str) or not request_id.strip():
            raise Rejected("A request ID is required")
        prior = self._requests.get(request_id)
        if prior is not None:
            if prior.offer != offer:
                raise Rejected("Request ID was already used for a different offer")
            return prior
        charges, tender, updated, scale = self._validate_offer(offer, expected_revision)
        receipt = Signing(request_id, offer, charges, self.revision + 1)
        self._charges = updated
        self._players.add(offer.player_id)
        self._requests[request_id] = receipt
        self._tenders.pop(offer.player_id, None)
        if scale is not None:
            self._rookie_year_one -= offer.salaries[0] + Fraction(offer.signing_bonus, 4)
            self._rookie_total -= sum(offer.salaries) + offer.signing_bonus
        self.revision += 1
        return receipt
