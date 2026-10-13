"""Experimental free-agent signing ledger, independent of Remade.

This is a configurable accounting model, not an NFL rules implementation.
Sourced healthy preseason veteran releases and explicit base guarantees are supported.
Supported preseason veteran assignments preserve bonus debt and inherited base terms.
Other release protections, trade consideration, restructures and game-save writes remain unsupported.
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
    guaranteed_salaries: tuple[int, ...] = ()

    def __post_init__(self):
        if not isinstance(self.player_id, str) or not self.player_id.strip():
            raise ValueError("A stable player ID is required")
        if type(self.salaries) is not tuple or not self.salaries:
            raise ValueError("At least one annual salary is required as a tuple")
        for salary in self.salaries:
            money(salary)
        money(self.signing_bonus)
        if type(self.guaranteed_salaries) is not tuple:
            raise ValueError("Annual guaranteed bases must be an immutable tuple")
        if self.guaranteed_salaries:
            if len(self.guaranteed_salaries) != len(self.salaries):
                raise ValueError("Guarantees must cover the same annual term")
            if any(money(guarantee) > salary for guarantee, salary in zip(self.guaranteed_salaries, self.salaries)):
                raise ValueError("Guaranteed base exceeds its annual salary")

    def to_dict(self):
        result = {"player_id": self.player_id, "salaries": list(self.salaries), "signing_bonus": self.signing_bonus}
        if self.guaranteed_salaries:
            result["guaranteed_salaries"] = list(self.guaranteed_salaries)
        return result

    @classmethod
    def from_dict(cls, data):
        base = {"player_id", "salaries", "signing_bonus"}
        if type(data) is not dict or set(data) not in (base, base | {"guaranteed_salaries"}):
            raise ValueError("Unexpected contract terms")
        if type(data["salaries"]) not in (list, tuple) or type(data.get("guaranteed_salaries", ())) not in (list, tuple):
            raise ValueError("Annual contract terms required")
        return cls(data["player_id"], tuple(data["salaries"]), data["signing_bonus"], tuple(data.get("guaranteed_salaries", ())))

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
                 rookies: dict[str, "RookieScale | UndraftedScale"] | None = None,
                 rookie_year_one_allocation: int | None = None,
                 rookie_total_allocation: int | None = None,
                 rookie_tenders: dict[str, int] | None = None,
                 opening_books=None, veteran_minimum_profile=None,
                 undrafted_bonus_reservation=None, undrafted_reservation_source=None, rookie_pool_opening=None, management_profile=None):
        from franchise.management import ManagementProfile
        if management_profile is not None and not isinstance(management_profile, ManagementProfile):
            raise ValueError('Typed management profile required')
        self._management_profile = management_profile
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
        self._contracts = {item.offer.player_id: item.offer for item in opening_books.contracts} if opening_books else {}
        self._active_contracts = {item.offer.player_id: item for item in opening_books.contracts} if opening_books else {}
        self._released = {}
        self._last_transaction_date = None
        self._traded_out = {}
        self._traded_in = {}
        self._cash = None
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
        self._draft_reservations = {}
        self._draft_rights = {}
        self._promise_agreements = {}
        self._promise_scores = []
        if self._rookies.keys() & self._veteran_minimums.keys():
            raise ValueError("A player cannot be classified as both rookie and veteran")
        known = self._rookies.keys() | self._veteran_minimums.keys()
        if not self._players <= known:
            raise ValueError("Signed players must exist in the player registry")
        if self._rookies and (rookie_year_one_allocation is None
                              or rookie_total_allocation is None):
            raise ValueError("Rookies require both club rookie allocations")
        self._rookie_year_one = Fraction(money(
            0 if rookie_year_one_allocation is None else rookie_year_one_allocation))
        self._rookie_total = money(
            0 if rookie_total_allocation is None else rookie_total_allocation)
        from franchise.rookie import RookieScale, UndraftedScale
        if any(not isinstance(scale, (RookieScale, UndraftedScale)) for scale in self._rookies.values()):
            raise ValueError("Rookie registry must contain typed drafted or undrafted records")
        self._rookie_pool_opening = rookie_pool_opening
        self._prior_rookie_players = set()
        self._undrafted_bonus_initial = undrafted_bonus_reservation
        self._undrafted_reservation_source = undrafted_reservation_source
        self._undrafted_bonus_remaining = undrafted_bonus_reservation
        if undrafted_bonus_reservation is not None:
            money(undrafted_bonus_reservation)
            if type(undrafted_reservation_source) is not str or not undrafted_reservation_source.strip():
                raise ValueError("Undrafted reservation provenance required")
            if (undrafted_bonus_reservation > self._rookie_total
                    or Fraction(undrafted_bonus_reservation, 3) > self._rookie_year_one):
                raise ValueError("Undrafted reservation exceeds supplied club allocations")
        elif (any(isinstance(scale, UndraftedScale) for scale in self._rookies.values())
              or (self._rookies and veteran_minimum_profile is not None)):
            raise ValueError("Modern/undrafted rookie registry requires explicit undrafted reservation")
        self._tenders = dict(rookie_tenders or {})
        if any(isinstance(self._rookies.get(player), UndraftedScale) for player in self._tenders):
            raise ValueError("Undrafted rookies cannot have drafted-player tenders")
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
            if any(item.bonus_layers for item in opening_books.contracts):
                raise ValueError("Layered contracts require durable restructure cash reconciliation")
            if (self._charges != opening_books.charges()
                    or self._players != {item.offer.player_id for item in opening_books.contracts}
                    or self._tenders != {item.player_id: item.amount for item in opening_books.tenders}):
                raise ValueError("Opening balances, ownership or tenders disagree with source books")

        if rookie_pool_opening is not None:
            from franchise.rookie_opening import RookiePoolOpening
            if not isinstance(rookie_pool_opening, RookiePoolOpening) or opening_books is None:
                raise ValueError("Typed cohort profile and original contracts required")
            if (rookie_year_one_allocation != rookie_pool_opening.year_one_allocation
                    or rookie_total_allocation != rookie_pool_opening.total_allocation
                    or undrafted_bonus_reservation != rookie_pool_opening.undrafted_reservation
                    or undrafted_reservation_source != rookie_pool_opening.source):
                raise ValueError("Supplied allocation fields disagree with cohort source")
            if veteran_minimum_profile is not None and veteran_minimum_profile.start_year != rookie_pool_opening.league_year:
                raise ValueError("Salary and rookie profile years disagree")
            self._prior_rookie_players = {item.offer.player_id for item in rookie_pool_opening.prior_contracts}
            retained_ids = {item.record_id for item in opening_books.retained}
            if any("rookie-prior:" + player not in retained_ids for player in self._prior_rookie_players):
                raise ValueError("Prior rookie contract requires explicit retained cap/settlement record")
            self._rookie_year_one, self._rookie_total, self._undrafted_bonus_remaining = rookie_pool_opening.derive_remaining(self._active_contracts, self._rookies)

    @classmethod
    def from_opening(cls, books, **rules):
        profile = rules.get("rookie_pool_opening")
        if profile is not None:
            from franchise.rookie_opening import RookiePoolOpening
            if not isinstance(profile, RookiePoolOpening):
                raise ValueError("Typed rookie cohort profile required")
            rules.setdefault("rookie_year_one_allocation", profile.year_one_allocation)
            rules.setdefault("rookie_total_allocation", profile.total_allocation)
            rules.setdefault("undrafted_bonus_reservation", profile.undrafted_reservation)
            rules.setdefault("undrafted_reservation_source", profile.source)
        return cls(existing_charges=books.charges(),
                   signed_player_ids=frozenset(item.offer.player_id for item in books.contracts),
                   rookie_tenders={item.player_id: item.amount for item in books.tenders},
                   opening_books=books, **rules)

    def active_contract(self, player_id):
        with self._lock:
            if player_id not in self._active_contracts:
                raise Rejected("Original active contract and elapsed years unavailable")
            return self._active_contracts[player_id]

    def apply_preseason_release(self, player_id, *, scope, discount, payment_year_offsets,
                               record_id, expected_revision):
        """Replace one supported veteran's active obligations, preserving debt."""
        from franchise.releases import calculate_preseason_release
        with self._lock:
            if type(expected_revision) is not int or expected_revision != self.revision:
                raise Rejected('Release used stale franchise state')
            if player_id in self._rookies or player_id not in self._veteran_minimums:
                raise Rejected('Supported veteran classification required for release')
            if player_id in self._released or player_id not in self._players:
                raise Rejected('Player has no active owned contract to release')
            contract = self.active_contract(player_id)
            if self._cash is None or 'contract:' + player_id not in self._cash.records:
                raise Rejected('Allocated original cash required for release')
            cash = self._cash.records['contract:' + player_id]
            plan = calculate_preseason_release(contract, cash, scope=scope, discount=discount,
                payment_year_offsets=payment_year_offsets, record_id=record_id)
            self._check_transaction_date(scope.league_year,scope.removed_on)
            existing_ids = self._retained_record_ids()
            if any(record.record_id in existing_ids for record in plan.retained):
                raise Rejected('Release retained-record identity already exists')
            if (self._veteran_minimum_profile is not None
                    and self._veteran_minimum_profile.start_year != scope.league_year):
                raise Rejected('Release year disagrees with salary profile')
            active, retained = contract.charges(), plan.charges()
            years = max(len(self._charges), len(active), len(retained))
            charges = tuple((self._charges[i] if i < len(self._charges) else Fraction(0))
                            - (active[i] if i < len(active) else Fraction(0))
                            + (retained[i] if i < len(retained) else Fraction(0)) for i in range(years))
            if any(value < 0 for value in charges):
                raise Rejected('Release credits exceed recorded obligations')
            # Acceleration may exceed the cap. Subsequent signing checks remain
            # binding; an overage does not erase a valid retained obligation.
            self._charges = charges
            self._released[player_id] = plan
            self._last_transaction_date=scope.removed_on
            del self._active_contracts[player_id]
            self._players.remove(player_id)
            self._cash.records[cash.obligation_id] = plan.cash_obligation
            self._cash.revision += 1
            self.revision += 1
            return plan

    def _check_transaction_date(self,year,on):
        known_years=[]
        if self._veteran_minimum_profile is not None:
            known_years.append(self._veteran_minimum_profile.start_year)
        if self._rookie_pool_opening is not None:
            known_years.append(self._rookie_pool_opening.league_year)
        if self._last_transaction_date is not None:
            known_years.append(self._last_transaction_date.year)
            if on < self._last_transaction_date:
                raise Rejected('Dated transaction precedes established franchise chronology')
        if any(known != year for known in known_years):
            raise Rejected('Transaction requires an unsupported league-year transition')

    def _retained_record_ids(self):
        ids = {record.record_id for plan in self._released.values() for record in plan.retained}
        ids.update(plan.retained_bonus.record_id for plan in self._traded_out.values())
        if self._opening_books is not None:
            ids.update(record.record_id for record in (*self._opening_books.retained, *self._opening_books.adjustments))
        return ids

    def apply_preseason_trade_out(self, player_id, *, scope, record_id, expected_revision):
        from franchise.trades import calculate_preseason_trade
        with self._lock:
            if type(expected_revision) is not int or expected_revision != self.revision:
                raise Rejected('Trade used stale franchise state')
            if player_id in self._rookies or player_id not in self._veteran_minimums:
                raise Rejected('Supported veteran classification required for trade')
            if player_id not in self._players or player_id in self._traded_out:
                raise Rejected('Player has no active owned contract to trade')
            contract = self.active_contract(player_id)
            cash = self._cash.records.get('contract:' + player_id) if self._cash is not None else None
            if cash is None:
                raise Rejected('Allocated original cash required for trade')
            plan = calculate_preseason_trade(contract, cash, scope=scope, record_id=record_id)
            self._check_transaction_date(scope.league_year,scope.traded_on)
            if plan.retained_bonus.record_id in self._retained_record_ids():
                raise Rejected('Trade retained-record identity already exists')
            if (self._veteran_minimum_profile is not None
                    and self._veteran_minimum_profile.start_year != scope.league_year):
                raise Rejected('Trade year disagrees with salary profile')
            old, retained = contract.charges(), plan.retained_bonus.annual_charges
            years = max(len(self._charges), len(old), len(retained))
            charges = tuple((self._charges[i] if i < len(self._charges) else Fraction(0))
                            - (old[i] if i < len(old) else Fraction(0))
                            + (retained[i] if i < len(retained) else Fraction(0)) for i in range(years))
            if any(value < 0 for value in charges):
                raise Rejected('Trade credits exceed recorded obligations')
            self._charges = charges
            self._traded_out[player_id] = plan
            self._last_transaction_date=scope.traded_on
            del self._active_contracts[player_id]
            self._players.remove(player_id)
            self._cash.records[cash.obligation_id] = plan.seller_cash
            self._cash.revision += 1
            self.revision += 1
            return plan

    def apply_preseason_trade_in(self, plan, *, expected_revision):
        from franchise.trades import TradePlan, calculate_preseason_trade
        from franchise.books import ChargeRecord
        with self._lock:
            if type(expected_revision) is not int or expected_revision != self.revision:
                raise Rejected('Trade used stale franchise state')
            if not isinstance(plan, TradePlan) or not isinstance(plan.retained_bonus, ChargeRecord):
                raise ValueError('Typed sourced trade plan required')
            suffix = ':seller-bonus'
            if not plan.retained_bonus.record_id.endswith(suffix):
                raise ValueError('Trade record identity is invalid')
            recalculated = calculate_preseason_trade(plan.original_contract, plan.original_cash,
                scope=plan.scope, record_id=plan.retained_bonus.record_id[:-len(suffix)])
            if recalculated != plan:
                raise ValueError('Trade plan disagrees with original obligations')
            self._check_transaction_date(plan.scope.league_year,plan.scope.traded_on)
            player = plan.buyer_contract.offer.player_id
            if player in self._rookies or player not in self._veteran_minimums:
                raise Rejected('Supported veteran classification required for trade')
            if player in self._contracts or player in self._traded_out:
                raise Rejected('Trade return requires separate contract generation IDs')
            if self._cash is None or plan.buyer_cash.obligation_id in self._cash.records:
                raise Rejected('Known cash book without prior player obligation required')
            if (self._veteran_minimum_profile is not None
                    and self._veteran_minimum_profile.start_year != plan.scope.league_year):
                raise Rejected('Trade year disagrees with salary profile')
            _, _, charges, scale = self._validate_offer(plan.buyer_contract.offer, expected_revision)
            if scale is not None:
                raise Rejected('Rookie assignment is unsupported')
            self._charges = charges
            self._contracts[player] = plan.buyer_contract.offer
            self._active_contracts[player] = plan.buyer_contract
            self._players.add(player)
            self._traded_in[player] = plan
            self._last_transaction_date=plan.scope.traded_on
            self._cash.records[plan.buyer_cash.obligation_id] = plan.buyer_cash
            self._cash.revision += 1
            self.revision += 1
            return plan

    @staticmethod
    def _trade_snapshot(plan):
        def contract_data(contract):
            return {'offer': contract.offer.to_dict(), 'source': contract.source,
                    'elapsed_years': contract.elapsed_years, 'bonus_years': contract.bonus_years}
        scope = plan.scope
        return {'original_contract': contract_data(plan.original_contract),
                'original_cash': plan.original_cash.to_dict(),
                'scope': {'league_year': scope.league_year, 'traded_on': scope.traded_on.isoformat(),
                    'seller_first_regular_season_game': scope.seller_first_regular_season_game.isoformat(),
                    'buyer_first_regular_season_game': scope.buyer_first_regular_season_game.isoformat(),
                    'exclusions': sorted(scope.exclusions), 'healthy': scope.healthy,
                    'current_year_earned_base': scope.current_year_earned_base,
                    'assignment_consent': scope.assignment_consent,
                    'transaction_eligible': scope.transaction_eligible, 'source': scope.source},
                'retained_bonus': {'record_id': plan.retained_bonus.record_id,
                    'annual_charges': [json_amount(value) for value in plan.retained_bonus.annual_charges],
                    'source': plan.retained_bonus.source},
                'seller_cash': plan.seller_cash.to_dict(), 'buyer_contract': contract_data(plan.buyer_contract),
                'buyer_cash': plan.buyer_cash.to_dict(), 'assigned_base': plan.assigned_base}

    @staticmethod
    def _release_snapshot(plan):
        contract, scope, discount = plan.original_contract, plan.scope, plan.discount
        return {'original_contract': {'offer': contract.offer.to_dict(), 'source': contract.source,
                    'elapsed_years': contract.elapsed_years, 'bonus_years': contract.bonus_years},
                'original_cash': plan.original_cash.to_dict(),
                'scope': {'league_year': scope.league_year, 'removed_on': scope.removed_on.isoformat(),
                    'first_regular_season_game': scope.first_regular_season_game.isoformat(),
                    'exclusions': sorted(scope.exclusions), 'covered_guarantees': scope.covered_guarantees,
                    'healthy': scope.healthy, 'current_year_earned_base': scope.current_year_earned_base,
                    'source': scope.source},
                'discount': {'league_year': discount.league_year, 'annual_rate': json_amount(discount.annual_rate),
                             'rate_source': discount.rate_source},
                'payment_year_offsets': list(plan.payment_year_offsets),
                'retained': [{'record_id': record.record_id,
                    'annual_charges': [json_amount(value) for value in record.annual_charges],
                    'source': record.source} for record in plan.retained],
                'cash_obligation': plan.cash_obligation.to_dict(),
                'cancelled_unearned_base': plan.cancelled_unearned_base}

    def contract_terms(self, player_id):
        with self._lock:
            if player_id not in self._contracts:
                raise Rejected("Original contract terms are unavailable")
            return self._contracts[player_id].to_dict()

    def guarantee_cash(self, player_id):
        with self._lock:
            offer = self._contracts.get(player_id)
            if offer is None:
                raise Rejected("Original contract terms are unavailable")
            if player_id in self._traded_out:
                return {'unpaid_guaranteed_base_by_original_year': [0] * len(offer.salaries),
                        'unpaid_signing_bonus': 0}
            record = self._cash.records.get("contract:" + player_id) if self._cash is not None else None
            if record is None or record.paid_components is None:
                return None
            paid = dict(record.paid_components)
            guarantees = offer.guaranteed_salaries or (0,) * len(offer.salaries)
            return {"unpaid_guaranteed_base_by_original_year": [max(0, guarantee - paid.get("base:" + str(i), 0))
                        for i, guarantee in enumerate(guarantees)],
                    "unpaid_signing_bonus": max(0, offer.signing_bonus - paid.get("signing_bonus", 0)),
                    "obligation_source": record.source}

    def cash_snapshot(self):
        return self._cash.snapshot() if self._cash is not None else None

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
                    "rookie_year_one_allocation": self._rookie_pool_opening.year_one_allocation if self._rookie_pool_opening else int(self._rookie_year_one),
                    "rookie_total_allocation": self._rookie_pool_opening.total_allocation if self._rookie_pool_opening else self._rookie_total,
                    "rookie_tenders": dict(self._tenders),
                    "undrafted_bonus_reservation": self._undrafted_bonus_initial,
                    "undrafted_reservation_source": self._undrafted_reservation_source,
                    "rookie_pool_opening": self._rookie_pool_opening.to_dict() if self._rookie_pool_opening else None,
                    "veteran_minimum_profile": self._veteran_minimum_profile.to_dict() if self._veteran_minimum_profile else None,
                    "opening_books": self._opening_books.to_dict() if self._opening_books else None,
                    "management_profile": self._management_profile.to_dict() if self._management_profile else None}

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

    def promise_history(self, player_id):
        import json
        return json.loads(json.dumps([record for record in self._promise_scores if record['player_id'] == player_id]))

    def scouting_history(self):
        return [dict(request_id=event['request_id'], decision=dict(event['decision']),
                     draft_round=event['evidence']['draft_round'], overall_pick=event['evidence']['overall_pick'])
                for event in getattr(self, '_scouting', [])]

    def recalled_scouting(self, request_id):
        return None

    def record_scouting(self, event, *, access_check):
        access_check()
        return event  # In-memory session cache; durable adapter records history.

    def management_context(self) -> dict:
        """Private team decision input; not exposed in player/agent prompts."""
        with self._lock:
            return {"management_profile": self._management_profile.to_dict() if self._management_profile else None,
                    "accounting": self.financial_snapshot()}

    def negotiation_context(self, player_id: str) -> dict:
        with self._lock:
            if player_id not in self._rookies and player_id not in self._veteran_minimums:
                raise Rejected("Player is unknown or contract classification is missing")
            scale = self._rookies.get(player_id)
            _, reserved_one, reserved_total = self._draft_reserved(except_player=player_id)
            return {"revision": self.revision, "cap": self.cap, "room": json_amount(self.room),
                    "promise_history": self.promise_history(player_id),
                    "annual_team_charges": [json_amount(value) for value in self._charges],
                    "roster_reserve": self.roster_reserve,
                    "cash_summary": ({key: value for key, value in self.cash_snapshot().items()
                                      if key != "obligations"} if self._cash is not None else None),
                    "veteran_minimum_salaries": self._veteran_minimums.get(player_id),
                    "salary_floor_profile": ({"start_year": self._veteran_minimum_profile.start_year,
                                              "rule_version": self._veteran_minimum_profile.rule_version,
                                              "source": self._veteran_minimum_profile.source}
                                             if self._veteran_minimum_profile else None),
                    "existing_player_tender": self._tenders.get(player_id, 0),
                    "room_for_replacing_player_tender": json_amount(self.room + self._tenders.get(player_id, 0) + self._draft_reserved(player_id_only=player_id)[0]),
                    "rookie_scale": asdict(scale) if scale else None,
                    "rookie_allocation_profile": ({"league_year": self._rookie_pool_opening.league_year,
                                                    "source": self._rookie_pool_opening.source}
                                                   if self._rookie_pool_opening else None),
                    "rookie_type": ("drafted" if hasattr(scale, "draft_round") else "undrafted") if scale else None,
                    "undrafted_bonus_remaining": self._undrafted_bonus_remaining,
                    "rookie_available_to_player": ({
                        "year_one": json_amount(max(0, self._rookie_year_one - reserved_one - (Fraction(self._undrafted_bonus_remaining or 0, 3) if hasattr(scale, "draft_round") else 0))),
                        "total": max(0, self._rookie_total - reserved_total - ((self._undrafted_bonus_remaining or 0) if hasattr(scale, "draft_round") else 0))} if scale else None),
                    "rookie_year_one_remaining": str(self._rookie_year_one),
                    "rookie_total_remaining": self._rookie_total,
                    "max_bonus_years": 4 if scale else self.max_bonus_years}

    @property
    def charges(self) -> tuple[int | Fraction, ...]:
        return self._charges

    @property
    def room(self) -> int | Fraction:
        return self.cap - self._charges[0] - self.roster_reserve - self._draft_reserved()[0]

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

    def validate_scouting_personality(self, player_id, personality):
        self.negotiation_context(player_id)
        actor = getattr(self, '_actors', {}).get(player_id)
        if actor is not None and personality != actor['personality']:
            raise Rejected('Scouting personality differs from saved player personality')

    def negotiation_inputs(self, player_id, actor):
        with self._lock:
            return actor, self.negotiation_context(player_id)

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
                    "rookie_tenders": dict(self._tenders),
                    **({'released_contracts': {player: self._release_snapshot(plan)
                        for player, plan in self._released.items()}} if self._released else {}),
                    **({'outgoing_trades': {player: self._trade_snapshot(plan)
                        for player, plan in self._traded_out.items()}} if self._traded_out else {}),
                    **({'incoming_trades': {player: self._trade_snapshot(plan)
                        for player, plan in self._traded_in.items()}} if self._traded_in else {}),
                    **({"draft_rights": dict(self._draft_rights)} if self._draft_rights else {}),
                    **({"draft_management_reservations": {player: {"offer": offer.to_dict(), "source": source}
                        for player, (offer, source) in self._draft_reservations.items()}} if self._draft_reservations else {}),
                    **({"undrafted_bonus_remaining": self._undrafted_bonus_remaining}
                       if self._undrafted_bonus_remaining is not None else {})}

    def _draft_reserved(self, *, except_player=None, player_id_only=None):
        cap = one = Fraction(0)
        total = 0
        for player, (offer, _) in self._draft_reservations.items():
            if player == except_player or (player_id_only is not None and player != player_id_only):
                continue
            charges = self._rookies[player].pool_charges(offer)
            cap += max(0, offer.charges(4)[0] - self._tenders.get(player, 0))
            one += charges[0]
            total += int(sum(charges))
        return cap, one, total

    def reserve_draft_funding(self, offer, expected_revision, *, source):
        """Management earmark only: no NFL salary charge, contract or pick right."""
        with self._lock:
            if type(source) is not str or not source.strip():
                raise ValueError('Draft estimate source required')
            from franchise.rookie import RookieScale
            if not isinstance(self._rookies.get(offer.player_id), RookieScale):
                raise Rejected('Drafted rookie estimate required')
            if offer.player_id in self._draft_reservations:
                raise Rejected('Draft funding already reserved; explicit withdrawal required')
            self._validate_offer(offer, expected_revision)
            self._draft_reservations[offer.player_id] = (offer, source)
            self.revision += 1

    def withdraw_draft_funding(self, player_id, expected_revision, *, source):
        with self._lock:
            if type(source) is not str or not source.strip():
                raise ValueError('Management withdrawal source required')
            if type(expected_revision) is not int or expected_revision != self.revision:
                raise Rejected('Draft funding withdrawal used stale franchise state')
            if player_id not in self._draft_reservations:
                raise Rejected('No draft funding reservation')
            del self._draft_reservations[player_id]
            self.revision += 1

    def _validate_offer(self, offer: Offer, expected_revision: int):
        if type(expected_revision) is not int or expected_revision != self.revision:
            raise Rejected("Offer was based on stale franchise state")
        if offer.player_id in self._players:
            raise Rejected("Player is already signed; extensions are unsupported")
        if offer.player_id in self._released:
            raise Rejected('Released player re-signing requires separate contract generation IDs')
        if offer.player_id in self._traded_out:
            raise Rejected('Traded player re-signing requires separate contract generation IDs')
        if offer.player_id in self._prior_rookie_players:
            raise Rejected("Prior cohort contract requires unsupported rookie release/re-sign reconciliation")
        reserved_cap, reserved_one, reserved_total = self._draft_reserved(except_player=offer.player_id)
        available_one = self._rookie_year_one - reserved_one
        available_total = self._rookie_total - reserved_total
        scale = self._rookies.get(offer.player_id)
        if scale is not None:
            from franchise.rookie import UndraftedScale
            if isinstance(scale, UndraftedScale):
                scale.validate(offer, club_year_one_remaining=available_one,
                    club_total_remaining=available_total,
                    club_undrafted_bonus_remaining=self._undrafted_bonus_remaining)
            else:
                reservation = self._undrafted_bonus_remaining or 0
                scale.validate(offer, club_year_one_remaining=max(0, available_one - Fraction(reservation, 3)),
                               club_total_remaining=max(0, available_total - reservation))
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
        available_room = self.cap - self._charges[0] - self.roster_reserve - reserved_cap
        if charges[0] - tender > available_room:
            raise Rejected(f"Offer exceeds available cap room by {charges[0] - tender - available_room}")
        years = max(len(charges), len(self._charges))
        updated = tuple(
            (self._charges[i] if i < len(self._charges) else 0)
            + (charges[i] if i < len(charges) else 0)
            - (tender if i == 0 else 0)
            for i in range(years)
        )
        return charges, tender, updated, scale

    def preview_draft_offer(self, offer, expected_revision):
        return self.preview_offer(offer, expected_revision)

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
                    "room_after": json_amount(self.cap - updated[0] - self.roster_reserve - self._draft_reserved(except_player=offer.player_id)[0]),
                    "contract_cash": sum(offer.salaries) + offer.signing_bonus,
                    "fully_guaranteed_base": sum(offer.guaranteed_salaries),
                    "rookie_year_one_after": json_amount(self._rookie_year_one - scale.pool_charges(offer)[0]) if scale else None,
                    "rookie_total_after": self._rookie_total - int(sum(scale.pool_charges(offer))) if scale else None}

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
        self._contracts[offer.player_id] = offer
        from franchise.books import ActiveContract
        self._active_contracts[offer.player_id] = ActiveContract(offer, "sign:" + request_id,
            bonus_years=4 if scale is not None else self.max_bonus_years)
        self._requests[request_id] = receipt
        self._tenders.pop(offer.player_id, None)
        self._draft_reservations.pop(offer.player_id, None)
        if scale is not None:
            pool_charges = scale.pool_charges(offer)
            self._rookie_year_one -= pool_charges[0]
            self._rookie_total -= int(sum(pool_charges))
            from franchise.rookie import UndraftedScale
            if isinstance(scale, UndraftedScale):
                self._undrafted_bonus_remaining -= offer.signing_bonus
        self.revision += 1
        return receipt
