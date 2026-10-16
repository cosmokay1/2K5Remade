"""Experimental free-agent signing ledger, independent of Remade.

This is a configurable accounting model, not an NFL rules implementation.
Sourced healthy preseason veteran releases and explicit base guarantees are supported.
Supported preseason veteran assignments preserve bonus debt and inherited base terms.
Other release protections, trade consideration, restructures and game-save writes remain unsupported.
Offers use integer dollars; internal allocations use exact rational dollars. Only the current cap is binding; future charges
are reported without assuming future league caps.
"""
from dataclasses import asdict, dataclass, replace
from fractions import Fraction
from threading import RLock
import hashlib
import json
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
                 undrafted_bonus_reservation=None, undrafted_reservation_source=None, rookie_pool_opening=None, management_profile=None,
                 observed_player_ids=frozenset(), observed_player_source=None):
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
        self._legacy_contracts = {item.player_id: item for item in opening_books.legacy_contracts} if opening_books else {}
        self._legacy_amendments = {}
        self._legacy_amendment_requests = {}
        if type(observed_player_ids) is not frozenset or any(type(p) is not str or not p.strip() for p in observed_player_ids):
            raise ValueError('Immutable observed player identities required')
        if observed_player_ids:
            if type(observed_player_source) is not str or not observed_player_source.strip():
                raise ValueError('Observed player registry requires source provenance')
        elif observed_player_source is not None:
            raise ValueError('Observed registry source requires player identities')
        self._observed_player_ids = observed_player_ids
        self._observed_player_source = observed_player_source
        self._released = {}
        self._last_transaction_date = None
        self._traded_out = {}
        self._traded_in = {}
        self._restructures = {}
        self._team_identity = None
        self._generation_calendar_views = {}
        self._generation_calendar_anchor = None
        self._year_transition_source = None
        self._generation_agreements = {}
        self._generation_identities = {}
        self._generation_by_player = {}
        self._active_generation_ids = {}
        self._cash = None
        self._actors = {}
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
        if self._legacy_contracts.keys() & self._rookies.keys():
            raise ValueError('Preserved legacy contracts cannot use a modern rookie cohort')
        self._draft_reservations = {}
        self._draft_rights = {}
        self._promise_agreements = {}
        self._promise_scores = []
        if self._rookies.keys() & self._veteran_minimums.keys():
            raise ValueError("A player cannot be classified as both rookie and veteran")
        known = self._rookies.keys() | self._veteran_minimums.keys() | self._legacy_contracts.keys()
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
                    or self._players != {item.offer.player_id for item in opening_books.contracts} | self._legacy_contracts.keys()
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
                   signed_player_ids=frozenset({item.offer.player_id for item in books.contracts} | {item.player_id for item in books.legacy_contracts}),
                   rookie_tenders={item.player_id: item.amount for item in books.tenders},
                   opening_books=books, **rules)

    def active_contract(self, player_id):
        with self._lock:
            if player_id not in self._active_contracts:
                raise Rejected("Original active contract and elapsed years unavailable")
            if self._team_identity is not None:
                gid=self.contract_identity(player_id).generation_id
                if gid in self._generation_calendar_views:
                    return self._generation_calendar_views[gid].current_contract
                return self.generation_accounting(gid).contract
            return self._active_contracts[player_id]

    @property
    def registered_player_ids(self):
        return self._rookies.keys() | self._veteran_minimums.keys() | self._legacy_contracts.keys() | self._observed_player_ids

    def bind_team_identity(self, team_id):
        from franchise.generations import legacy_identity
        if type(team_id) is not str or not team_id.strip():
            raise ValueError('Stable team identity required')
        with self._lock:
            if self._team_identity is not None:
                if self._team_identity != team_id:
                    raise Rejected('Contract generation team identity cannot change')
                if (set(self._generation_by_player) != set(self._contracts)
                        or set(self._active_generation_ids) != self._players - self._legacy_contracts.keys()):
                    raise Rejected('Existing contract generation mapping is inconsistent')
                self.generation_agreements()
                for player in self._contracts:
                    self.contract_identity(player)
                return
            if not self._players - self._legacy_contracts.keys() <= self._contracts.keys():
                raise Rejected('Original contracts required to bind owned generations')
            identities = {player:legacy_identity(team_id,player) for player in self._contracts}
            self._team_identity = team_id
            self._generation_identities = {item.generation_id:item for item in identities.values()}
            self._generation_by_player = {player:item.generation_id for player,item in identities.items()}
            self._active_generation_ids = {player:identities[player].generation_id for player in self._players - self._legacy_contracts.keys()}
            for player in identities:
                self._refresh_generation_agreement(player)

    def contract_identity(self, player_id):
        from franchise.generations import GenerationIdentity, legacy_identity, generation_identity
        with self._lock:
            if player_id not in self._contracts:
                raise Rejected('Known historical contract required')
            if self._team_identity is None:
                return None
            generation_id = self._generation_by_player.get(player_id)
            if generation_id is None or generation_id not in self._generation_identities:
                raise Rejected('Contract generation identity is unavailable')
            identity = self._generation_identities[generation_id]
            agreement=self._generation_agreements.get(generation_id)
            expected=agreement.canonical_identity(self._team_identity) if agreement is not None else legacy_identity(self._team_identity,player_id)
            if (not isinstance(identity, GenerationIdentity) or identity.generation_id != generation_id
                    or identity != expected):
                raise Rejected('Contract generation identity disagrees with source team/player')
            if player_id in self._players and self._active_generation_ids.get(player_id) != generation_id:
                raise Rejected('Active contract generation disagrees with ownership')
            if player_id not in self._players and player_id in self._active_generation_ids:
                raise Rejected('Closed contract still has an active generation')
            return identity

    def contract_cash_id(self, player_id):
        identity = self.contract_identity(player_id)
        return identity.cash_obligation_id if identity is not None else 'contract:' + player_id

    def _register_contract_identity(self, player_id):
        if self._team_identity is not None:
            from franchise.generations import legacy_identity
            identity = legacy_identity(self._team_identity,player_id)
            self._generation_identities[identity.generation_id] = identity
            self._generation_by_player[player_id] = identity.generation_id
            self._active_generation_ids[player_id] = identity.generation_id

    def _refresh_generation_agreement(self, player_id):
        from franchise.generations import GenerationAgreement
        if self._team_identity is None:
            return
        identity = self.contract_identity(player_id)
        previous = self._generation_agreements.get(identity.generation_id)
        if self._generation_calendar_anchor is not None and previous is not None:
            raise Rejected('Post-transition amendment of existing agreement is unsupported')
        release = self._released.get(player_id)
        outgoing = self._traded_out.get(player_id)
        restructure = self._restructures.get(player_id)
        contract = self._active_contracts.get(player_id)
        if contract is None:
            contract = release.original_contract if release is not None else outgoing.original_contract
        original = previous.original_contract if previous is not None else (
            restructure.original_contract if restructure is not None else contract)
        self._generation_agreements[identity.generation_id] = GenerationAgreement(
            identity, original, contract, release, outgoing, self._traded_in.get(player_id), restructure,
            previous.return_request_id if previous is not None else None,
            previous.return_scope if previous is not None else None,
            previous.assignment_request_id if previous is not None else None,
            previous.assigned_from_team if previous is not None else None,
            previous.assigned_from_generation_id if previous is not None else None)
        if self._generation_calendar_anchor is not None:
            from franchise.generations import GenerationCalendarView
            self._generation_calendar_views[identity.generation_id]=GenerationCalendarView(
                self._generation_agreements[identity.generation_id],self._league_year,self._league_year)

    def generation_accounting(self, generation_id):
        with self._lock:
            agreement = self._generation_agreements.get(generation_id)
            if agreement is None:
                raise Rejected('Known contract generation required')
            from franchise.generations import legacy_identity, generation_identity
            expected=agreement.canonical_identity(self._team_identity)
            if (agreement.identity.generation_id != generation_id
                    or self._generation_identities.get(generation_id) != agreement.identity
                    or agreement.identity != expected):
                raise Rejected('Archived agreement identity disagrees with contract generation')
            return agreement

    def generation_agreements(self):
        with self._lock:
            if set(self._generation_agreements) != set(self._generation_identities):
                raise Rejected('Generation agreement archive coverage is inconsistent')
            return tuple(self.generation_accounting(key) for key in sorted(self._generation_agreements))

    def generation_cash(self, generation_id):
        with self._lock:
            agreement = self.generation_accounting(generation_id)
            return self._cash.records.get(agreement.identity.cash_obligation_id) if self._cash is not None else None

    def generation_guarantee_cash(self, generation_id):
        with self._lock:
            agreement = self.generation_accounting(generation_id)
            return self._guarantee_cash(agreement.identity.player_id, agreement=agreement)

    def _require_pretransition_operations(self):
        if self._generation_calendar_anchor is not None:
            raise Rejected('Post-transition contract mutations require calendar-aware lifecycle support')

    def generation_calendar_view(self, generation_id):
        from franchise.generations import GenerationCalendarView
        with self._lock:
            agreement=self.generation_accounting(generation_id)
            if generation_id in self._generation_calendar_views:
                return self._generation_calendar_views[generation_id]
            year=getattr(self,'_league_year',None)
            if year is None:
                raise Rejected('Anchored league year required')
            return GenerationCalendarView(agreement,year,year)

    def generation_calendar_snapshot(self):
        with self._lock:
            return {'format':1,'league_year':getattr(self,'_league_year',None),
                'anchor_year':self._generation_calendar_anchor,'source':self._year_transition_source,
                'generations':[{'generation_id':a.identity.generation_id,
                    'anchor_year':self.generation_calendar_view(a.identity.generation_id).anchor_year,
                    'current_year':self.generation_calendar_view(a.identity.generation_id).current_year,
                    'status':self.generation_calendar_view(a.identity.generation_id).status,
                    'scheduled_term_complete':self.generation_calendar_view(a.identity.generation_id).scheduled_term_complete,
                    'expiry_source':self.generation_calendar_view(a.identity.generation_id).expiry_source,
                    'current_contract':self.generation_calendar_view(a.identity.generation_id).current_contract.to_dict()
                        if self.generation_calendar_view(a.identity.generation_id).current_contract is not None else None,
                    'annual_charges':[json_amount(v) for v in self.generation_calendar_view(a.identity.generation_id).annual_charges()]}
                    for a in self.generation_agreements()]}

    def apply_year_transition(self, *, from_year, to_year, expected_revision, next_cap,
                              roster_reserve, next_minimum_profile, source,
                              expired_generation_ids=()):
        from franchise.generations import GenerationCalendarView
        from franchise.salary_rules import VeteranMinimumProfile
        with self._lock:
            if self._legacy_contracts:
                raise Rejected('Legacy schedule aging requires verified calendar migration')
            if (type(from_year) is not int or type(to_year) is not int or to_year!=from_year+1
                    or getattr(self,'_league_year',None)!=from_year
                    or type(expected_revision) is not int or expected_revision!=self.revision):
                raise Rejected('Anchored consecutive year and current revision required')
            if (not isinstance(next_minimum_profile,VeteranMinimumProfile)
                    or next_minimum_profile.start_year!=to_year
                    or type(source) is not str or not source.strip()):
                raise ValueError('Sourced next-year minimum profile and transition source required')
            if (self._veteran_minimum_profile is not None
                    and self._veteran_minimum_profile.start_year!=from_year):
                raise Rejected('Current salary profile disagrees with anchored outgoing year')
            current_economy = (self._veteran_minimum_profile.economy
                               if self._veteran_minimum_profile is not None else None)
            if current_economy != next_minimum_profile.economy:
                raise Rejected('Year transition cannot change the historical economy without verified migration')
            cap,reserve=money(next_cap),money(roster_reserve)
            floors=next_minimum_profile.floors()
            if set(floors)!=set(self._veteran_minimums):
                raise Rejected('Next-year veteran registry must preserve all known players')
            if (self._team_identity is None or self._cash is None or self._rookies
                    or self._tenders or self._draft_reservations or self._draft_rights
                    or self._rookie_pool_opening is not None or self._undrafted_bonus_initial is not None
                    or self._prior_rookie_players or self._rookie_year_one or self._rookie_total):
                raise Rejected('Supported transition requires bound veteran-only allocated books')
            if (type(expired_generation_ids) is not tuple
                    or any(type(g) is not str for g in expired_generation_ids)
                    or len(set(expired_generation_ids))!=len(expired_generation_ids)):
                raise ValueError('Unique explicit expiry generation identities required')
            anchor=self._generation_calendar_anchor if self._generation_calendar_anchor is not None else from_year
            views={}; expiring=set(); active={}
            for agreement in self.generation_agreements():
                gid=agreement.identity.generation_id
                cash=self.generation_cash(gid)
                ceilings=agreement.payment_ceilings()
                if (cash is None or cash.paid_components is None
                        or cash.player_id!=agreement.identity.player_id
                        or cash.amount!=sum(ceilings.values())):
                    raise Rejected('Known allocated generation cash matching obligations required')
                paid=dict(cash.paid_components)
                if any(k not in ceilings or v>ceilings[k] for k,v in paid.items()):
                    raise Rejected('Generation cash allocations exceed preserved payment rights')
                previous=self._generation_calendar_views.get(gid)
                agreement_anchor=previous.anchor_year if previous is not None else anchor
                if previous is not None and previous.authoritative_expired:
                    view=GenerationCalendarView(agreement,agreement_anchor,to_year,True,cash,previous.expiry_source)
                else:
                    view=GenerationCalendarView(agreement,agreement_anchor,to_year)
                    if agreement.status=='active':
                        outgoing_index=agreement.contract.elapsed_years+(from_year-agreement_anchor)
                        required={k:v for k,v in ceilings.items() if not k.startswith('base:')
                            or int(k[5:])<=outgoing_index}
                        if any(paid.get(k,0)!=v for k,v in required.items()):
                            raise Rejected('Outgoing base and all bonus components must be settled explicitly')
                        if view.scheduled_term_complete:
                            expiring.add(gid)
                            if gid in expired_generation_ids:
                                view=GenerationCalendarView(agreement,agreement_anchor,to_year,True,cash,source)
                        else:
                            contract=view.current_contract
                            remaining=contract.offer.salaries[contract.elapsed_years:]
                            player=agreement.identity.player_id
                            if len(floors[player])<len(remaining) or any(v<f for v,f in zip(remaining,floors[player])):
                                raise Rejected('Surviving contract violates sourced next-year salary floors')
                            active[player]=contract
                views[gid]=view
            if set(expired_generation_ids)!=expiring:
                raise Rejected('Exact explicit eligibility required for newly exhausted generations')
            # All validation precedes the first mutation; cash and economic archives remain immutable.
            self._generation_calendar_anchor=anchor
            self._generation_calendar_views=views
            self._active_contracts=active
            self._players=set(active)
            self._active_generation_ids={p:self._generation_by_player[p] for p in active}
            self._charges=self._charges[1:] or (Fraction(0),)
            self._cap,self._roster_reserve=cap,reserve
            self._veteran_minimum_profile=next_minimum_profile
            self._veteran_minimums=floors
            self._league_year=to_year
            self._year_transition_source=source
            self.revision+=1
            return self.generation_calendar_snapshot()

    def apply_preseason_release(self, player_id, *, scope, discount, payment_year_offsets,
                               record_id, expected_revision):
        return self._apply_preseason_release(player_id,scope=scope,discount=discount,
            payment_year_offsets=payment_year_offsets,record_id=record_id,
            expected_revision=expected_revision,calendar_generation_id=None)

    def apply_calendar_preseason_release(self, player_id, *, generation_id,scope,discount,
                                        payment_year_offsets,record_id,expected_revision):
        if type(generation_id) is not str or not generation_id.strip():
            raise Rejected('Exact calendar release generation required')
        return self._apply_preseason_release(player_id,scope=scope,discount=discount,
            payment_year_offsets=payment_year_offsets,record_id=record_id,
            expected_revision=expected_revision,calendar_generation_id=generation_id)

    def _apply_preseason_release(self, player_id, *, scope,discount,payment_year_offsets,
                                record_id,expected_revision,calendar_generation_id):
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
            previous=None
            if calendar_generation_id is not None:
                if (self._generation_calendar_anchor is None
                        or self._active_generation_ids.get(player_id) != calendar_generation_id):
                    raise Rejected('Current owned advanced-calendar agreement required')
                previous=self.generation_accounting(calendar_generation_id)
                view=self.generation_calendar_view(calendar_generation_id)
                if view.current_contract != contract or view.current_year != self._league_year:
                    raise Rejected('Release cursor disagrees with authoritative calendar view')
            cash_id = self.contract_cash_id(player_id)
            if self._cash is None or cash_id not in self._cash.records:
                raise Rejected('Allocated original cash required for release')
            cash = self._cash.records[cash_id]
            plan = calculate_preseason_release(contract, cash, scope=scope, discount=discount,
                payment_year_offsets=payment_year_offsets, record_id=record_id, expected_cash_id=cash_id)
            self._check_transaction_date(scope.league_year,scope.removed_on,
                calendar_release=calendar_generation_id is not None)
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
            updated=None
            if previous is not None:
                from franchise.generations import GenerationCalendarView
                updated=replace(previous,release=plan,release_calendar_year=scope.league_year)
                updated_view=GenerationCalendarView(updated,scope.league_year,scope.league_year)
            # Acceleration may exceed the cap. Subsequent signing checks remain
            # binding; an overage does not erase a valid retained obligation.
            self._charges = charges
            self._released[player_id] = plan
            self._last_transaction_date=scope.removed_on
            del self._active_contracts[player_id]
            self._players.remove(player_id)
            self._active_generation_ids.pop(player_id,None)
            self._cash.records[cash.obligation_id] = plan.cash_obligation
            self._cash.revision += 1
            self.revision += 1
            if updated is not None:
                self._generation_agreements[calendar_generation_id]=updated
                self._generation_calendar_views[calendar_generation_id]=updated_view
            else:
                self._refresh_generation_agreement(player_id)
            return plan

    def _check_transaction_date(self,year,on,*,calendar_release=False,calendar_trade=False,calendar_amendment=False):
        advanced=calendar_release or calendar_trade or calendar_amendment
        if advanced:
            if self._generation_calendar_anchor is None or self._league_year != year:
                raise Rejected('Transaction year must match the advanced league calendar')
        else:
            self._require_pretransition_operations()
        known_years=[]
        if getattr(self, '_league_year', None) is not None:
            known_years.append(self._league_year)
        if self._veteran_minimum_profile is not None:
            known_years.append(self._veteran_minimum_profile.start_year)
        if self._rookie_pool_opening is not None:
            known_years.append(self._rookie_pool_opening.league_year)
        if self._last_transaction_date is not None:
            if not advanced:
                known_years.append(self._last_transaction_date.year)
            if on < self._last_transaction_date:
                raise Rejected('Dated transaction precedes established franchise chronology')
        if any(known != year for known in known_years):
            raise Rejected('Transaction requires an unsupported league-year transition')

    def _retained_record_ids(self):
        ids = {record.record_id for agreement in self._generation_agreements.values() for record in agreement.retained_records}
        ids.update(record.record_id for plan in self._released.values() for record in plan.retained)
        ids.update(plan.retained_bonus.record_id for plan in self._traded_out.values())
        if self._opening_books is not None:
            ids.update(record.record_id for record in (*self._opening_books.retained, *self._opening_books.adjustments))
        return ids

    def apply_preseason_restructure(self, player_id, *, scope, converted_base, record_id, expected_revision):
        return self._apply_preseason_restructure(player_id,scope=scope,converted_base=converted_base,
            record_id=record_id,expected_revision=expected_revision,calendar_generation_id=None)

    def apply_calendar_preseason_restructure(self,player_id,*,generation_id,scope,converted_base,record_id,expected_revision):
        if type(generation_id) is not str or not generation_id.strip():
            raise Rejected('Exact calendar amendment generation required')
        return self._apply_preseason_restructure(player_id,scope=scope,converted_base=converted_base,
            record_id=record_id,expected_revision=expected_revision,calendar_generation_id=generation_id)

    def apply_calendar_layered_preseason_restructure(self,player_id,*,generation_id,scope,converted_base,record_id,expected_revision):
        if type(generation_id) is not str or not generation_id.strip():
            raise Rejected('Exact calendar amendment generation required')
        return self._apply_preseason_restructure(player_id,scope=scope,converted_base=converted_base,
            record_id=record_id,expected_revision=expected_revision,calendar_generation_id=generation_id,layered=True)

    def _apply_preseason_restructure(self,player_id,*,scope,converted_base,record_id,expected_revision,calendar_generation_id,layered=False):
        from franchise.restructures import calculate_preseason_restructure,calculate_layered_preseason_restructure,PreseasonRestructureScope
        with self._lock:
            if type(expected_revision) is not int or expected_revision != self.revision:
                raise Rejected('Restructure used stale franchise state')
            if player_id in self._rookies or player_id not in self._veteran_minimums:
                raise Rejected('Supported veteran classification required for restructure')
            if player_id not in self._players:
                raise Rejected('Player has no active owned contract to restructure')
            contract = self.active_contract(player_id)
            previous=None
            if calendar_generation_id is not None:
                if (self._generation_calendar_anchor is None
                        or self._active_generation_ids.get(player_id)!=calendar_generation_id):
                    raise Rejected('Current owned advanced-calendar agreement required')
                previous=self.generation_accounting(calendar_generation_id)
                view=self.generation_calendar_view(calendar_generation_id)
                if view.current_contract!=contract or view.current_year!=self._league_year:
                    raise Rejected('Amendment cursor disagrees with authoritative calendar view')
            if layered and (previous is None or previous.restructure is None or not contract.bonus_layers
                    or not isinstance(scope,PreseasonRestructureScope)
                    or scope.league_year<=previous.restructure.scope.league_year):
                raise Rejected('Layered amendment requires a sourced prior conversion and strictly later calendar year')
            cash_id = self.contract_cash_id(player_id)
            cash = self._cash.records.get(cash_id) if self._cash is not None else None
            if cash is None:
                raise Rejected('Allocated original cash required for restructure')
            years = len(contract.offer.salaries) - contract.elapsed_years
            minimums = self._veteran_minimums[player_id][:years]
            calculate=calculate_layered_preseason_restructure if layered else calculate_preseason_restructure
            plan = calculate(contract, cash, scope=scope, converted_base=converted_base,
                annual_minimums=minimums, record_id=record_id, expected_cash_id=cash_id)
            self._check_transaction_date(scope.league_year, scope.amended_on,calendar_amendment=calendar_generation_id is not None)
            if (self._veteran_minimum_profile is not None
                    and scope.minimum_source != self._veteran_minimum_profile.source):
                raise Rejected('Restructure minimum source disagrees with salary profile')
            layer_ids = {layer.record_id for agreement in self._generation_agreements.values() for layer in agreement.contract.bonus_layers}
            layer_ids.update(prior.bonus_layer.record_id for prior in self._restructures.values())
            for active in self._active_contracts.values():
                layer_ids.update(layer.record_id for layer in active.bonus_layers)
            for prior in (*self._released.values(), *self._traded_out.values(), *self._traded_in.values()):
                layer_ids.update(layer.record_id for layer in prior.original_contract.bonus_layers)
            if record_id in layer_ids or record_id in self._retained_record_ids():
                raise Rejected('Restructure bonus layer identity already exists')
            old, amended = contract.charges(), plan.contract.charges()
            horizon = max(len(self._charges), len(old), len(amended))
            charges = tuple((self._charges[i] if i < len(self._charges) else Fraction(0))
                - (old[i] if i < len(old) else Fraction(0))
                + (amended[i] if i < len(amended) else Fraction(0)) for i in range(horizon))
            if any(value < 0 for value in charges):
                raise Rejected('Restructure credits exceed recorded obligations')
            updated=None
            if previous is not None:
                from franchise.generations import GenerationCalendarView
                updated=replace(previous,contract=plan.contract,restructure=plan,restructure_calendar_year=scope.league_year,
                    **({'prior_restructures':previous.prior_restructures+(previous.restructure,)} if layered else {}))
                updated_view=GenerationCalendarView(updated,scope.league_year,scope.league_year)
            self._charges = charges
            self._contracts[player_id] = plan.contract.offer
            self._active_contracts[player_id] = plan.contract
            self._restructures[player_id] = plan
            self._cash.records[cash.obligation_id] = plan.cash_obligation
            self._cash.revision += 1
            self._last_transaction_date = scope.amended_on
            self.revision += 1
            if updated is not None:
                self._generation_agreements[calendar_generation_id]=updated
                self._generation_calendar_views[calendar_generation_id]=updated_view
            else:
                self._refresh_generation_agreement(player_id)
            return plan

    @staticmethod
    def _restructure_snapshot(plan):
        scope = plan.scope
        return {'original_contract': plan.original_contract.to_dict(), 'original_cash': plan.original_cash.to_dict(),
            'scope': {'league_year': scope.league_year, 'amended_on': scope.amended_on.isoformat(),
                'first_regular_season_game': scope.first_regular_season_game.isoformat(),
                'current_year_earned_base': scope.current_year_earned_base, 'healthy': scope.healthy,
                'consent': scope.consent, 'renegotiation_eligible': scope.renegotiation_eligible,
                'exclusions': sorted(scope.exclusions), 'minimum_source': scope.minimum_source, 'source': scope.source},
            'annual_minimums': list(plan.annual_minimums), 'converted_base': plan.converted_base,
            'bonus_layer': asdict(plan.bonus_layer), 'contract': plan.contract.to_dict(),
            'cash_obligation': plan.cash_obligation.to_dict()}

    def apply_preseason_trade_out(self, player_id, *, scope, record_id, expected_revision,buyer_cash_id=None):
        return self._apply_preseason_trade_out(player_id,scope=scope,record_id=record_id,
            expected_revision=expected_revision,buyer_cash_id=buyer_cash_id,calendar_generation_id=None)

    def apply_calendar_preseason_trade_out(self,player_id,*,generation_id,scope,record_id,expected_revision,buyer_cash_id=None):
        if type(generation_id) is not str or not generation_id.strip():
            raise Rejected('Exact calendar assignment generation required')
        return self._apply_preseason_trade_out(player_id,scope=scope,record_id=record_id,
            expected_revision=expected_revision,buyer_cash_id=buyer_cash_id,calendar_generation_id=generation_id)

    def _apply_preseason_trade_out(self,player_id,*,scope,record_id,expected_revision,buyer_cash_id,calendar_generation_id):
        from franchise.trades import calculate_preseason_trade
        with self._lock:
            if type(expected_revision) is not int or expected_revision != self.revision:
                raise Rejected('Trade used stale franchise state')
            if player_id in self._rookies or player_id not in self._veteran_minimums:
                raise Rejected('Supported veteran classification required for trade')
            if player_id not in self._players or player_id in self._traded_out:
                raise Rejected('Player has no active owned contract to trade')
            contract = self.active_contract(player_id)
            previous=None
            if calendar_generation_id is not None:
                if (self._generation_calendar_anchor is None
                        or self._active_generation_ids.get(player_id)!=calendar_generation_id):
                    raise Rejected('Current owned advanced-calendar agreement required')
                previous=self.generation_accounting(calendar_generation_id)
                view=self.generation_calendar_view(calendar_generation_id)
                if view.current_contract!=contract or view.current_year!=self._league_year:
                    raise Rejected('Assignment cursor disagrees with authoritative calendar view')
            cash_id = self.contract_cash_id(player_id)
            if self._team_identity is not None and self.contract_identity(player_id).generation_id.startswith('contract-gen:') and buyer_cash_id is None:
                raise Rejected('Explicit destination generation cash identity required for assignment')
            cash = self._cash.records.get(cash_id) if self._cash is not None else None
            if cash is None:
                raise Rejected('Allocated original cash required for trade')
            plan = calculate_preseason_trade(contract, cash, scope=scope, record_id=record_id, expected_cash_id=cash_id,buyer_cash_id=buyer_cash_id)
            self._check_transaction_date(scope.league_year,scope.traded_on,calendar_trade=calendar_generation_id is not None)
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
            updated=None
            if previous is not None:
                from franchise.generations import GenerationCalendarView
                updated=replace(previous,outgoing_trade=plan,outgoing_trade_calendar_year=scope.league_year)
                updated_view=GenerationCalendarView(updated,scope.league_year,scope.league_year)
            self._charges = charges
            self._traded_out[player_id] = plan
            self._last_transaction_date=scope.traded_on
            del self._active_contracts[player_id]
            self._players.remove(player_id)
            self._active_generation_ids.pop(player_id,None)
            self._cash.records[cash.obligation_id] = plan.seller_cash
            self._cash.revision += 1
            self.revision += 1
            if updated is not None:
                self._generation_agreements[calendar_generation_id]=updated
                self._generation_calendar_views[calendar_generation_id]=updated_view
            else:
                self._refresh_generation_agreement(player_id)
            return plan

    def apply_preseason_trade_in(self, plan, *, expected_revision,assignment_request_id=None,
                                 assigned_from_team=None,assigned_from_generation_id=None):
        return self._apply_preseason_trade_in(plan,expected_revision=expected_revision,
            assignment_request_id=assignment_request_id,assigned_from_team=assigned_from_team,
            assigned_from_generation_id=assigned_from_generation_id,calendar_assignment=False)

    def apply_calendar_preseason_trade_in(self,plan,*,expected_revision,assignment_request_id,
                                         assigned_from_team,assigned_from_generation_id):
        return self._apply_preseason_trade_in(plan,expected_revision=expected_revision,
            assignment_request_id=assignment_request_id,assigned_from_team=assigned_from_team,
            assigned_from_generation_id=assigned_from_generation_id,calendar_assignment=True)

    def _apply_preseason_trade_in(self,plan,*,expected_revision,assignment_request_id,
                                assigned_from_team,assigned_from_generation_id,calendar_assignment):
        from franchise.trades import TradePlan, calculate_preseason_trade
        from franchise.books import ChargeRecord, ActiveContract
        with self._lock:
            if type(expected_revision) is not int or expected_revision != self.revision:
                raise Rejected('Trade used stale franchise state')
            if (not isinstance(plan, TradePlan) or not isinstance(plan.retained_bonus, ChargeRecord)
                    or not isinstance(plan.buyer_contract, ActiveContract)):
                raise ValueError('Typed sourced trade plan required')
            suffix = ':seller-bonus'
            if not plan.retained_bonus.record_id.endswith(suffix):
                raise ValueError('Trade record identity is invalid')
            player = plan.buyer_contract.offer.player_id
            from franchise.generations import legacy_identity,assignment_identity,GenerationAgreement
            metadata=(assignment_request_id,assigned_from_team,assigned_from_generation_id)
            versioned=any(value is not None for value in metadata)
            if calendar_assignment and (not versioned or self._generation_calendar_anchor is None):
                raise Rejected('Advanced buyer calendar and explicit assignment identities required')
            identity=None
            if versioned:
                if self._team_identity is None or any(type(value) is not str or not value.strip() for value in metadata):
                    raise ValueError('Bound buyer and complete assignment source identities required')
                if assigned_from_team==self._team_identity:
                    raise Rejected('Assignment requires distinct source and destination clubs')
                source_legacy=legacy_identity(assigned_from_team,player)
                if assigned_from_generation_id==source_legacy.generation_id:
                    source_cash_id=source_legacy.cash_obligation_id
                elif (assigned_from_generation_id.startswith('contract-gen:') and len(assigned_from_generation_id)==77
                        and all(c in '0123456789abcdef' for c in assigned_from_generation_id[13:])):
                    source_cash_id=assigned_from_generation_id
                else:
                    raise ValueError('Canonical source agreement identity required')
                if plan.original_cash.obligation_id!=source_cash_id:
                    raise ValueError('Assignment original cash disagrees with source generation')
                identity=assignment_identity(self._team_identity,player,assignment_request_id)
                expected_buyer_cash=identity.cash_obligation_id
            else:
                expected_buyer_cash = legacy_identity(self._team_identity,player).cash_obligation_id if self._team_identity is not None else 'contract:' + player
            recalculated = calculate_preseason_trade(plan.original_contract, plan.original_cash,
                scope=plan.scope, record_id=plan.retained_bonus.record_id[:-len(suffix)],
                expected_cash_id=plan.original_cash.obligation_id,buyer_cash_id=expected_buyer_cash)
            if recalculated != plan:
                raise ValueError('Trade plan disagrees with original obligations')
            self._check_transaction_date(plan.scope.league_year,plan.scope.traded_on,calendar_trade=calendar_assignment)
            if plan.buyer_cash.obligation_id != expected_buyer_cash:
                raise Rejected('Incoming contract cash identity disagrees with receiving team')
            if player in self._rookies or player not in self._veteran_minimums:
                raise Rejected('Supported veteran classification required for trade')
            if player in self._contracts or player in self._traded_out:
                if not versioned:
                    raise Rejected('Trade return requires separate contract generation IDs')
                previous=self.generation_accounting(self.contract_identity(player).generation_id)
                expired=(calendar_assignment and self.generation_calendar_view(previous.identity.generation_id).authoritative_expired)
                if (previous.status not in ('released','assigned') and not expired) or player in self._players:
                    raise Rejected('Closed prior agreement required for assignment return')
                if self.generation_cash(previous.identity.generation_id) is None:
                    raise Rejected('Known prior agreement cash required for assignment return')
            if versioned and identity.generation_id in self._generation_identities:
                raise Rejected('Assignment generation identity already exists')
            if self._cash is None or plan.buyer_cash.obligation_id in self._cash.records:
                raise Rejected('Known cash book without prior player obligation required')
            if (self._veteran_minimum_profile is not None
                    and self._veteran_minimum_profile.start_year != plan.scope.league_year):
                raise Rejected('Trade year disagrees with salary profile')
            _, _, charges, scale = self._validate_offer(plan.buyer_contract.offer, expected_revision,
                returning=versioned,calendar_assignment=calendar_assignment)
            if scale is not None:
                raise Rejected('Rookie assignment is unsupported')
            agreement=GenerationAgreement(identity,plan.buyer_contract,plan.buyer_contract,incoming_trade=plan,
                assignment_request_id=assignment_request_id,assigned_from_team=assigned_from_team,
                assigned_from_generation_id=assigned_from_generation_id) if versioned else None
            calendar_view=None
            if calendar_assignment:
                from franchise.generations import GenerationCalendarView
                calendar_view=GenerationCalendarView(agreement,plan.scope.league_year,plan.scope.league_year)
            if not versioned:
                self._register_contract_identity(player)
            else:
                self._generation_identities[identity.generation_id]=identity
                self._generation_agreements[identity.generation_id]=agreement
                self._generation_by_player[player]=identity.generation_id
                self._active_generation_ids[player]=identity.generation_id
                for mapping in (self._released,self._traded_out,self._traded_in,self._restructures):
                    mapping.pop(player,None)
            self._charges = charges
            self._contracts[player] = plan.buyer_contract.offer
            self._active_contracts[player] = plan.buyer_contract
            self._players.add(player)
            self._traded_in[player] = plan
            self._last_transaction_date=plan.scope.traded_on
            self._cash.records[plan.buyer_cash.obligation_id] = plan.buyer_cash
            self._cash.revision += 1
            self.revision += 1
            if calendar_view is not None:
                self._generation_calendar_views[identity.generation_id]=calendar_view
            else:
                self._refresh_generation_agreement(player)
            return plan

    @staticmethod
    def _trade_snapshot(plan):
        def contract_data(contract):
            return contract.to_dict()
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
        return {'original_contract': contract.to_dict(),
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
            if self._team_identity is not None:
                agreement = self.generation_accounting(self.contract_identity(player_id).generation_id)
                result = agreement.contract.offer.to_dict()
                if agreement.contract.bonus_layers:
                    result['bonus_layers'] = [asdict(layer) for layer in agreement.contract.bonus_layers]
                return result
            result = self._contracts[player_id].to_dict()
            contract = self._active_contracts.get(player_id)
            if contract is None and player_id in self._released:
                contract = self._released[player_id].original_contract
            if contract is None and player_id in self._traded_out:
                contract = self._traded_out[player_id].original_contract
            if contract is not None and contract.bonus_layers:
                result['bonus_layers'] = [asdict(layer) for layer in contract.bonus_layers]
            return result

    def guarantee_cash(self, player_id):
        with self._lock:
            if self._team_identity is not None:
                return self.generation_guarantee_cash(self.contract_identity(player_id).generation_id)
            return self._guarantee_cash(player_id)

    def _guarantee_cash(self, player_id, *, agreement=None):
        with self._lock:
            offer = agreement.contract.offer if agreement is not None else self._contracts.get(player_id)
            if offer is None:
                raise Rejected("Original contract terms are unavailable")
            if (agreement.status == 'assigned' if agreement is not None else player_id in self._traded_out):
                layers = agreement.contract.bonus_layers if agreement is not None else self._traded_out[player_id].original_contract.bonus_layers
                return {'unpaid_guaranteed_base_by_original_year': [0] * len(offer.salaries),
                        'unpaid_signing_bonus': 0,
                        **({'unpaid_original_signing_bonus': 0,
                            'unpaid_bonus_layers': {layer.cash_component: 0 for layer in layers}} if layers else {})}
            cash_id = agreement.identity.cash_obligation_id if agreement is not None else self.contract_cash_id(player_id)
            record = self._cash.records.get(cash_id) if self._cash is not None else None
            if record is None or record.paid_components is None:
                return None
            paid = dict(record.paid_components)
            guarantees = offer.guaranteed_salaries or (0,) * len(offer.salaries)
            contract = agreement.contract if agreement is not None else self._active_contracts.get(player_id)
            if contract is None and player_id in self._released:
                contract = self._released[player_id].original_contract
            layers = {layer.cash_component: max(0, layer.amount - paid.get(layer.cash_component, 0))
                      for layer in contract.bonus_layers} if contract is not None else {}
            return {"unpaid_guaranteed_base_by_original_year": [max(0, guarantee - paid.get("base:" + str(i), 0))
                        for i, guarantee in enumerate(guarantees)],
                    "unpaid_signing_bonus": max(0, offer.signing_bonus - paid.get("signing_bonus", 0)) + sum(layers.values()),
                    **({'unpaid_bonus_layers': layers,
                        'unpaid_original_signing_bonus': max(0, offer.signing_bonus - paid.get('signing_bonus', 0))} if layers else {}),
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
                    **({'observed_player_ids':sorted(self._observed_player_ids),
                        'observed_player_source':self._observed_player_source} if self._observed_player_ids else {}),
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

    def initialize_salary_classification(self, profile, *, source, expected_revision):
        """Add declared salary inputs without replacing contracts or actor identities."""
        from franchise.salary_rules import VeteranMinimumProfile
        with self._lock:
            if not isinstance(profile, VeteranMinimumProfile) or not profile.players:
                raise ValueError('Nonempty typed salary classification required')
            if type(source) is not str or not source.strip():
                raise ValueError('Salary credit-input provenance required')
            if type(expected_revision) is not int or expected_revision != self.revision:
                raise Rejected('Salary classification used stale franchise state')
            floors = profile.floors()
            if not floors.keys() <= self.registered_player_ids or floors.keys() & self._rookies.keys():
                raise Rejected('Salary classification requires known non-rookie identities')
            if getattr(self, '_league_year', None) is not None and profile.start_year != self._league_year:
                raise Rejected('Salary classification differs from the current league year')
            if ((self._rookie_pool_opening is not None and self._rookie_pool_opening.league_year != profile.start_year)
                    or (self._last_transaction_date is not None and self._last_transaction_date.year != profile.start_year)):
                raise Rejected('Salary classification differs from established financial chronology')
            if profile.economy is not None and profile.economy.target_cap != self.cap:
                raise Rejected('Salary conversion differs from the established cap scale')
            if any(floors.get(player) != values for player, values in self._veteran_minimums.items()):
                raise Rejected('Salary initialization cannot replace existing minimums')
            previous = self._veteran_minimum_profile
            if previous is not None:
                old = {row[0]: row for row in previous.players}
                new = {row[0]: row for row in profile.players}
                if (previous.start_year != profile.start_year or previous.economy != profile.economy
                        or any(new.get(player) != row for player, row in old.items())):
                    raise Rejected('Salary initialization cannot replace existing credit inputs')
            self._veteran_minimum_profile = profile
            self._veteran_minimums = floors
            self._salary_classification_source = source
            self.revision += 1

    def management_context(self) -> dict:
        """Private team decision input; not exposed in player/agent prompts."""
        with self._lock:
            return {"management_profile": self._management_profile.to_dict() if self._management_profile else None,
                    "accounting": self.financial_snapshot()}

    def negotiation_context(self, player_id: str) -> dict:
        with self._lock:
            if player_id not in self.registered_player_ids:
                raise Rejected("Player is unknown or contract classification is missing")
            scale = self._rookies.get(player_id)
            _, reserved_one, reserved_total = self._draft_reserved(except_player=player_id)
            cash_summary=self.cash_snapshot()
            if cash_summary is not None:
                cash_summary.pop('obligations')
                unknown=cash_summary.pop('unknown_legacy_players',())
                if unknown: cash_summary['unknown_legacy_contract_count']=len(unknown)
            return {"revision": self.revision, "cap": self.cap, "room": json_amount(self.room),
                    **({'classification_pending':True,'observed_player_source':self._observed_player_source}
                       if player_id not in self._rookies and player_id not in self._veteran_minimums and player_id not in self._legacy_contracts else {}),
                    **({'legacy_contract': self._legacy_contracts[player_id].to_dict(),
                        'legacy_liability_scope': 'original cap schedule; cash/protections/lifecycle unverified'}
                       if player_id in self._legacy_contracts else {}),
                    "promise_history": self.promise_history(player_id),
                    "annual_team_charges": [json_amount(value) for value in self._charges],
                    "roster_reserve": self.roster_reserve,
                    "cash_summary": cash_summary,
                    "veteran_minimum_salaries": self._veteran_minimums.get(player_id),
                    "salary_floor_profile": ({"start_year": self._veteran_minimum_profile.start_year,
                                              "rule_version": self._veteran_minimum_profile.rule_version,
                                              "source": self._veteran_minimum_profile.source,
                                              **({'classification_source':self._salary_classification_source}
                                                 if hasattr(self, '_salary_classification_source') else {}),
                                              **({"economy": self._veteran_minimum_profile.economy.to_dict()}
                                                 if self._veteran_minimum_profile.economy is not None else {})}
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
        import copy
        from franchise.negotiation import validate_performance
        if type(personality) is not dict or type(relationships) is not dict:
            raise ValueError('Actor fields must be JSON objects')
        declared = {'personality': personality, 'relationships': relationships}
        validate_performance(declared)
        json.dumps(declared, allow_nan=False)
        with self._lock:
            actor = self._actors.setdefault(player_id, copy.deepcopy(declared))
            return copy.deepcopy(actor)

    def validate_scouting_personality(self, player_id, personality):
        self.negotiation_context(player_id)
        actor = getattr(self, '_actors', {}).get(player_id)
        if actor is not None and personality != actor['personality']:
            raise Rejected('Scouting personality differs from saved player personality')

    def negotiation_inputs(self, player_id, actor):
        with self._lock:
            return actor, {**self.negotiation_context(player_id),
                           "current_contract_owned": player_id in self._players}

    def negotiation_history(self, player_id: str):
        return []

    def record_negotiation(self, event: dict, *, access_check):
        from franchise.negotiation_reactions import apply_reaction
        with self._lock:
            access_check()  # In-memory sessions retain their own dialogue.
            apply_reaction(self._actors.get(event['offer']['player_id']), event)
        return event

    def recalled_negotiation(self, request_id: str, offer: Offer):
        return None  # In-memory sessions retain their own replies.

    def financial_snapshot(self) -> dict:
        with self._lock:
            return {"revision": self.revision, "cap": self.cap,
                    **({'legacy_amendments':{player:agreement.to_dict() for player,agreement in sorted(self._legacy_amendments.items())}}
                       if self._legacy_amendments else {}),
                    **({'legacy_schedule_count':len(self._legacy_contracts),
                        'legacy_schedule_sha256':hashlib.sha256(json.dumps(
                            [self._legacy_contracts[key].to_dict() for key in sorted(self._legacy_contracts)],
                            sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()}
                       if self._legacy_contracts else {}),
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
                    **({'restructures': {player: self._restructure_snapshot(plan)
                        for player, plan in self._restructures.items()}} if self._restructures else {}),
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

    def _validate_offer(self, offer: Offer, expected_revision: int, *, returning=False,calendar_assignment=False):
        if calendar_assignment and (self._generation_calendar_anchor is None or not returning
                or offer.player_id in self._rookies or offer.player_id not in self._veteran_minimums):
            raise Rejected('Calendar assignment requires a registered veteran and explicit receiving generation')
        if not calendar_assignment and self._generation_calendar_anchor is not None and (returning
                or offer.player_id in self._contracts or offer.player_id in self._rookies
                or offer.player_id not in self._veteran_minimums):
            raise Rejected('Post-transition signing requires a never-held registered veteran')
        if type(expected_revision) is not int or expected_revision != self.revision:
            raise Rejected("Offer was based on stale franchise state")
        if offer.player_id in self._players:
            raise Rejected("Player is already signed; extensions are unsupported")
        if not returning and offer.player_id in self._released:
            raise Rejected('Released player re-signing requires separate contract generation IDs')
        if not returning and offer.player_id in self._traded_out:
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

    def preview_legacy_amendment(self, offer: Offer, expected_revision: int) -> dict:
        """Full-year simulation comparison, conditional on player agreement.

        Preserve imported bonus charges on their original schedule; replace only
        remaining base. This is not a signing preview or settlement authority:
        earned pay, cash payment history and guest application are unverified.
        """
        from franchise.legacy_contracts import original_annual_rows
        with self._lock:
            if type(expected_revision) is not int or expected_revision != self.revision:
                raise Rejected('Amendment was based on stale franchise state')
            original = self._legacy_contracts.get(offer.player_id)
            if original is None or offer.player_id not in self._players:
                raise Rejected('Active imported contract required for amendment comparison')
            minimums = self._veteran_minimums.get(offer.player_id)
            if minimums is None or len(minimums) < len(offer.salaries):
                raise Rejected('Salary classification required for all proposed years')
            if any(salary < minimum for salary, minimum in zip(offer.salaries, minimums)):
                raise Rejected('Veteran amendment is below an annual minimum salary')
            rows = original_annual_rows(original.amount_word, original.bonus_code,
                                       original.shape_code, original.original_years)
            remaining = rows[original.original_years-original.remaining_years:]
            old = original.charges()
            carried = tuple(row['allocated_bonus_dollars'] * original.game_dollar_scale for row in remaining)
            previous=self._legacy_amendments.get(offer.player_id)
            if previous is not None:
                old,carried=previous.charges(),previous.bonus_charges()
            proposed = offer.charges(self.max_bonus_years)
            horizon = max(len(old), len(proposed))
            after = tuple((proposed[i] if i < len(proposed) else 0) +
                          (carried[i] if i < len(carried) else 0) for i in range(horizon))
            updated = tuple((self._charges[i] if i < len(self._charges) else 0) -
                            (old[i] if i < len(old) else 0) +
                            (after[i] if i < len(after) else 0)
                            for i in range(max(horizon, len(self._charges))))
            room = self.cap - updated[0] - self.roster_reserve - self._draft_reserved()[0]
            return {'revision': self.revision, 'rule': 'legacy_bonus_carry_v1',
                    'original_contract': original.to_dict(),
                    'cap': self.cap, 'reserved_cap': json_amount(self.roster_reserve + self._draft_reserved()[0]),
                    'annual_team_charges_before': [json_amount(v) for v in self._charges],
                    'current_charges': [json_amount(v) for v in old], 'carried_bonus_charges': [json_amount(v) for v in carried],
                    'new_contract_charges': [json_amount(v) for v in proposed],
                    'combined_player_charges': [json_amount(v) for v in after],
                    'annual_team_charges_after': [json_amount(v) for v in updated],
                    'room_before': json_amount(self.room), 'room_after': json_amount(room),
                    'within_modeled_cap': room >= 0,
                    'requires_player_agreement': True, 'settlement_authorized': False}

    def apply_legacy_amendment(self,request_id,offer,expected_revision,*,proposal_request_id,source,scope):
        """Engine-only full-year agreement; the Store must verify saved consent.

        Ownership remains unchanged. Historical cash is not marked paid and no
        guest state is changed. Legacy lifecycle gates remain in force.
        """
        from franchise.legacy_amendments import LegacyAmendment
        from franchise.books import parse_amount
        with self._lock:
            if type(expected_revision) is not int:
                raise Rejected('Explicit amendment financial revision required')
            prior=self._legacy_amendment_requests.get(request_id)
            if prior is not None:
                if (prior.offer!=offer or prior.proposal_request_id!=proposal_request_id or prior.source!=source
                        or prior.scope!=scope or self._requests[request_id].revision!=expected_revision+1):
                    raise Rejected('Amendment request reused with different terms')
                return prior
            if request_id in self._requests:
                raise Rejected('Request already used for another financial operation')
            preview=self.preview_legacy_amendment(offer,expected_revision)
            if not preview['within_modeled_cap']:
                raise Rejected('Amendment exceeds available cap room')
            agreement=LegacyAmendment(request_id,proposal_request_id,offer,
                tuple(parse_amount(v) for v in preview['carried_bonus_charges']),source,scope,self.max_bonus_years)
            self._charges=tuple(parse_amount(v) for v in preview['annual_team_charges_after'])
            self._legacy_amendments[offer.player_id]=agreement
            self._legacy_amendment_requests[request_id]=agreement
            self.revision+=1
            self._requests[request_id]=Signing(request_id,offer,agreement.charges(),self.revision)
            return agreement

    def preview_return(self,offer,expected_revision,*,scope):
        from franchise.returns import PreseasonReturnScope
        with self._lock:
            if not isinstance(scope,PreseasonReturnScope) or not isinstance(offer,Offer):
                raise ValueError('Typed veteran offer and return scope required')
            if self._team_identity is None:
                raise Rejected('Bound team identity required for return signing')
            if offer.player_id in self._rookies or offer.player_id not in self._veteran_minimums:
                raise Rejected('Supported veteran classification required for return signing')
            previous=self.generation_accounting(self.contract_identity(offer.player_id).generation_id)
            if previous.status not in ('released','assigned') or offer.player_id in self._players:
                raise Rejected('Closed prior agreement required; extensions are unsupported')
            if self._cash is None or self.generation_cash(previous.identity.generation_id) is None:
                raise Rejected('Known cash obligations required for return signing')
            self._check_transaction_date(scope.league_year,scope.signed_on)
            charges,tender,updated,scale=self._validate_offer(offer,expected_revision,returning=True)
            return {'revision':self.revision,'contract_charges':[json_amount(v) for v in charges],
                'replaced_tender':tender,'annual_team_charges_after':[json_amount(v) for v in updated],
                'room_after':json_amount(self.cap-updated[0]-self.roster_reserve-self._draft_reserved(except_player=offer.player_id)[0]),
                'contract_cash':sum(offer.salaries)+offer.signing_bonus,
                'fully_guaranteed_base':sum(offer.guaranteed_salaries),
                'rookie_year_one_after':None,'rookie_total_after':None}

    def return_sign(self, request_id, offer, expected_revision, *, scope):
        from franchise.returns import PreseasonReturnScope
        from franchise.generations import generation_identity, GenerationAgreement
        from franchise.books import ActiveContract
        from franchise.cash import CashObligation
        with self._lock:
            if type(request_id) is not str or not request_id.strip() or not isinstance(scope,PreseasonReturnScope):
                raise ValueError('Typed return scope and signing request required')
            if not isinstance(offer,Offer):
                raise ValueError('Typed veteran offer required')
            if self._team_identity is None:
                raise Rejected('Bound team identity required for return signing')
            identity=generation_identity(self._team_identity,offer.player_id,request_id)
            prior=self._requests.get(request_id)
            if prior is not None:
                agreement=self._generation_agreements.get(identity.generation_id)
                if agreement is None or agreement.original_contract.offer != offer or prior.offer != offer or agreement.return_scope != scope:
                    raise Rejected('Return signing request already used for a different agreement')
                return prior
            if offer.player_id in self._rookies or offer.player_id not in self._veteran_minimums:
                raise Rejected('Supported veteran classification required for return signing')
            previous=self.generation_accounting(self.contract_identity(offer.player_id).generation_id)
            if previous.status not in ('released','assigned') or offer.player_id in self._players:
                raise Rejected('Closed prior agreement required; extensions are unsupported')
            if self._cash is None or self.generation_cash(previous.identity.generation_id) is None:
                raise Rejected('Known cash obligations required for return signing')
            self._check_transaction_date(scope.league_year,scope.signed_on)
            if (self._veteran_minimum_profile is not None
                    and self._veteran_minimum_profile.start_year != scope.league_year):
                raise Rejected('Return signing year disagrees with salary profile')
            charges,_,updated,scale=self._validate_offer(offer,expected_revision,returning=True)
            if scale is not None:
                raise Rejected('Rookie return signing is unsupported')
            if identity.generation_id in self._generation_identities or identity.cash_obligation_id in self._cash.records:
                raise Rejected('Return signing generation identity already exists')
            contract=ActiveContract(offer,'return-sign:'+request_id,bonus_years=self.max_bonus_years)
            agreement=GenerationAgreement(identity,contract,contract,return_request_id=request_id,return_scope=scope)
            obligation=CashObligation(identity.cash_obligation_id,offer.player_id,contract.nominal_cash,0,contract.source,())
            receipt=Signing(request_id,offer,charges,self.revision+1)
            self._charges=updated
            self._contracts[offer.player_id]=offer
            self._active_contracts[offer.player_id]=contract
            self._players.add(offer.player_id)
            self._generation_identities[identity.generation_id]=identity
            self._generation_agreements[identity.generation_id]=agreement
            self._generation_by_player[offer.player_id]=identity.generation_id
            self._active_generation_ids[offer.player_id]=identity.generation_id
            for mapping in (self._released,self._traded_out,self._traded_in,self._restructures):
                mapping.pop(offer.player_id,None)
            self._cash.records[identity.cash_obligation_id]=obligation
            self._cash.revision+=1
            self._requests[request_id]=receipt
            self._last_transaction_date=scope.signed_on
            self.revision+=1
            return receipt

    def generation_snapshot(self, *, history_format=1):
        if type(history_format) is not int or history_format not in (1,2):
            raise ValueError('Explicit supported integer generation history format required')
        with self._lock:
            if history_format==1 and any(agreement.prior_restructures for agreement in self._generation_agreements.values()):
                raise Rejected('Layered amendment history requires versioned generation posting')
            if self._team_identity is None:
                raise Rejected('Bound team identity required for generation posting')
            return {'format':history_format,'team_id':self._team_identity,'financial':self.financial_snapshot(),
                'current_generation_ids':dict(sorted(self._generation_by_player.items())),
                'active_generation_ids':dict(sorted(self._active_generation_ids.items())),
                'agreements':[{'identity':asdict(a.identity),'status':a.status,
                    'return_request_id':a.return_request_id,
                    **({'release_calendar_year':a.release_calendar_year}
                        if a.release_calendar_year is not None else {}),
                    **({'outgoing_trade_calendar_year':a.outgoing_trade_calendar_year}
                        if a.outgoing_trade_calendar_year is not None else {}),
                    **({'restructure_calendar_year':a.restructure_calendar_year}
                        if a.restructure_calendar_year is not None else {}),
                    **({'assignment_request_id':a.assignment_request_id,
                        'assigned_from_team':a.assigned_from_team,
                        'assigned_from_generation_id':a.assigned_from_generation_id}
                        if a.assignment_request_id is not None else {}),
                    'return_scope':{'league_year':a.return_scope.league_year,'signed_on':a.return_scope.signed_on.isoformat(),
                        'first_regular_season_game':a.return_scope.first_regular_season_game.isoformat(),
                        'healthy':a.return_scope.healthy,'exclusions':sorted(a.return_scope.exclusions),
                        'source':a.return_scope.source} if a.return_scope is not None else None,
                    'original_contract':a.original_contract.to_dict(),'contract':a.contract.to_dict(),
                    'release':self._release_snapshot(a.release) if a.release is not None else None,
                    'outgoing_trade':self._trade_snapshot(a.outgoing_trade) if a.outgoing_trade is not None else None,
                    'incoming_trade':self._trade_snapshot(a.incoming_trade) if a.incoming_trade is not None else None,
                    'restructure':self._restructure_snapshot(a.restructure) if a.restructure is not None else None,
                    **({'amendment_history':a.amendment_history_snapshot()} if history_format==2 else {}),
                    'annual_charges':[json_amount(v) for v in a.annual_charges()],
                    'cash_obligation':self.generation_cash(a.identity.generation_id).to_dict() if self.generation_cash(a.identity.generation_id) is not None else None}
                    for a in self.generation_agreements()], 'cash':self.cash_snapshot()}

    def _sign(self, request_id: str, offer: Offer, expected_revision: int) -> Signing:
        if not isinstance(request_id, str) or not request_id.strip():
            raise Rejected("A request ID is required")
        if request_id in self._legacy_amendment_requests:
            raise Rejected('Request belongs to an amendment, not a new signing')
        prior = self._requests.get(request_id)
        if prior is not None:
            if prior.offer != offer:
                raise Rejected("Request ID was already used for a different offer")
            return prior
        charges, tender, updated, scale = self._validate_offer(offer, expected_revision)
        receipt = Signing(request_id, offer, charges, self.revision + 1)
        self._register_contract_identity(offer.player_id)
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
        self._refresh_generation_agreement(offer.player_id)
        return receipt
