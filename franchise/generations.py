"""Immutable team-book identity, independent of contract terms and payments."""
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from typing import TYPE_CHECKING


def project_agreement(agreement, *, years_forward):
    """Read-only schedule view; never expires ownership or changes payment rights."""
    from franchise.cap import json_amount
    if not isinstance(agreement, GenerationAgreement) or type(years_forward) is not int or years_forward < 0:
        raise ValueError('Typed agreement and nonnegative integer projection offset required')
    active = agreement.status == 'active'
    index = agreement.contract.elapsed_years + years_forward
    complete = active and index >= len(agreement.contract.offer.salaries)
    return {'generation_id':agreement.identity.generation_id,
            'player_id':agreement.identity.player_id,
            'recorded_status':agreement.status,
            'years_forward':years_forward,
            'projected_original_year_index':index if active else None,
            'scheduled_term_complete':complete,
            'remaining_charges':[json_amount(value) for value in agreement.annual_charges()[years_forward:]],
            # Closed payment ceilings must not turn cancelled bases back into earned salary.
            'unchanged_payment_ceilings':agreement.payment_ceilings()}

if TYPE_CHECKING:
    from franchise.books import ActiveContract
    from franchise.releases import ReleasePlan
    from franchise.trades import TradePlan
    from franchise.restructures import RestructurePlan
    from franchise.returns import PreseasonReturnScope
    from franchise.cash import CashObligation


@dataclass(frozen=True)
class GenerationIdentity:
    generation_id: str
    player_id: str
    cash_obligation_id: str

    def __post_init__(self):
        if any(type(value) is not str or not value.strip() for value in
               (self.generation_id,self.player_id,self.cash_obligation_id)):
            raise ValueError('Stable contract generation, player and cash identities required')


def legacy_identity(team_id, player_id):
    if any(type(value) is not str or not value.strip() for value in (team_id,player_id)):
        raise ValueError('Stable team and player identities required')
    material = json.dumps([team_id,player_id],ensure_ascii=False,separators=(',',':')).encode('utf-8')
    return GenerationIdentity('legacy-contract:' + hashlib.sha256(material).hexdigest(),
                              player_id,'contract:' + player_id)


def generation_identity(team_id, player_id, request_id):
    if any(type(value) is not str or not value.strip() for value in (team_id,player_id,request_id)):
        raise ValueError('Stable team, player and signing request identities required')
    material=json.dumps([team_id,player_id,request_id],ensure_ascii=False,separators=(',',':')).encode('utf-8')
    generation_id='contract-gen:' + hashlib.sha256(material).hexdigest()
    return GenerationIdentity(generation_id,player_id,generation_id)


def assignment_identity(team_id, player_id, request_id):
    if any(type(value) is not str or not value.strip() for value in (team_id,player_id,request_id)):
        raise ValueError('Stable assignment team, player and request identities required')
    material=json.dumps(['assignment',team_id,player_id,request_id],ensure_ascii=False,separators=(',',':')).encode('utf-8')
    generation_id='contract-gen:' + hashlib.sha256(material).hexdigest()
    return GenerationIdentity(generation_id,player_id,generation_id)


@dataclass(frozen=True)
class GenerationAgreement:
    """One immutable agreement version; cash settlement stays in its cash book."""
    identity: GenerationIdentity
    original_contract: "ActiveContract"
    contract: "ActiveContract"
    release: "ReleasePlan | None" = None
    outgoing_trade: "TradePlan | None" = None
    incoming_trade: "TradePlan | None" = None
    restructure: "RestructurePlan | None" = None
    return_request_id: str | None = None
    return_scope: "PreseasonReturnScope | None" = None
    assignment_request_id: str | None = None
    assigned_from_team: str | None = None
    assigned_from_generation_id: str | None = None
    release_calendar_year: int | None = None
    outgoing_trade_calendar_year: int | None = None
    restructure_calendar_year: int | None = None
    prior_restructures: tuple["RestructurePlan", ...] = ()

    def __post_init__(self):
        from franchise.books import ActiveContract
        assignment=(self.assignment_request_id,self.assigned_from_team,self.assigned_from_generation_id)
        if any(value is not None for value in assignment):
            if (any(type(value) is not str or not value.strip() for value in assignment)
                    or self.incoming_trade is None or self.return_request_id is not None or self.return_scope is not None):
                raise ValueError('Complete sourced assignment metadata and incoming plan required')

        from franchise.returns import PreseasonReturnScope
        if ((self.return_request_id is None) != (self.return_scope is None)
                or (self.return_scope is not None and not isinstance(self.return_scope,PreseasonReturnScope))):
            raise ValueError('Typed return signing scope required')
        if self.return_request_id is not None and (type(self.return_request_id) is not str or not self.return_request_id.strip()):
            raise ValueError('Return signing request identity required')
        if (not isinstance(self.identity, GenerationIdentity)
                or not isinstance(self.original_contract, ActiveContract)
                or not isinstance(self.contract, ActiveContract)
                or self.original_contract.offer.player_id != self.identity.player_id
                or self.contract.offer.player_id != self.identity.player_id
                or (self.release is not None and self.outgoing_trade is not None)):
            raise ValueError('Typed consistent generation agreement required')
        from franchise.releases import ReleasePlan
        from franchise.trades import TradePlan
        from franchise.restructures import RestructurePlan,PreseasonRestructureScope
        if (type(self.prior_restructures) is not tuple
                or any(not isinstance(plan,RestructurePlan) for plan in self.prior_restructures)
                or (self.prior_restructures and self.restructure is None)):
            raise ValueError('Immutable typed prior amendment history and latest plan required')
        for plan, kind in ((self.release, ReleasePlan), (self.outgoing_trade, TradePlan),
                           (self.incoming_trade, TradePlan), (self.restructure, RestructurePlan)):
            if plan is not None and not isinstance(plan, kind):
                raise ValueError('Typed generation lifecycle plan required')
        if self.assignment_request_id is not None:
            source=legacy_identity(self.assigned_from_team,self.identity.player_id)
            if self.assigned_from_generation_id==source.generation_id:
                source_cash=source.cash_obligation_id
            elif (self.assigned_from_generation_id.startswith('contract-gen:')
                    and len(self.assigned_from_generation_id)==77
                    and all(c in '0123456789abcdef' for c in self.assigned_from_generation_id[13:])):
                source_cash=self.assigned_from_generation_id
            else:
                raise ValueError('Canonical assignment source generation required')
            if self.incoming_trade.original_cash.obligation_id != source_cash:
                raise ValueError('Incoming plan cash disagrees with assignment source')
        release_contract=self.contract
        trade_contract=self.contract
        restructure_original=self.original_contract
        if self.restructure_calendar_year is not None:
            if (type(self.restructure_calendar_year) is not int or not 2020 <= self.restructure_calendar_year <= 2030
                    or self.restructure is None or not isinstance(self.restructure.scope,PreseasonRestructureScope)
                    or self.restructure.scope.league_year!=self.restructure_calendar_year
                    or self.restructure.original_contract.elapsed_years<self.original_contract.elapsed_years):
                raise ValueError('Explicit sourced calendar amendment cursor required')
            restructure_original=replace(self.original_contract,elapsed_years=self.restructure.original_contract.elapsed_years)
            if any(year is not None and (type(year) is not int or year<self.restructure_calendar_year)
                   for year in (self.release_calendar_year,self.outgoing_trade_calendar_year)):
                raise ValueError('Lifecycle year precedes calendar amendment')
        if self.prior_restructures:
            if self.restructure_calendar_year is None:
                raise ValueError('Repeated amendment requires explicit latest calendar year')
            self._validate_amendment_history()
            restructure_original=self.restructure.original_contract
            for plan,year in ((self.release,self.release_calendar_year),
                              (self.outgoing_trade,self.outgoing_trade_calendar_year)):
                if plan is not None and (year is None or
                        plan.original_contract.elapsed_years-self.contract.elapsed_years!=
                        year-self.restructure.scope.league_year):
                    raise ValueError('Closed amendment history year and economic cursor disagree')
        if self.release_calendar_year is not None:
            if (type(self.release_calendar_year) is not int or not 2020 <= self.release_calendar_year <= 2030
                    or self.release is None or self.release.scope.league_year != self.release_calendar_year
                    or self.release.original_contract.elapsed_years < self.contract.elapsed_years):
                raise ValueError('Explicit sourced calendar release cursor required')
            release_contract=replace(self.contract,elapsed_years=self.release.original_contract.elapsed_years)
        if self.outgoing_trade_calendar_year is not None:
            if (type(self.outgoing_trade_calendar_year) is not int or not 2020 <= self.outgoing_trade_calendar_year <= 2030
                    or self.outgoing_trade is None or self.outgoing_trade.scope.league_year != self.outgoing_trade_calendar_year
                    or self.outgoing_trade.original_contract.elapsed_years < self.contract.elapsed_years):
                raise ValueError('Explicit sourced calendar assignment cursor required')
            trade_contract=replace(self.contract,elapsed_years=self.outgoing_trade.original_contract.elapsed_years)
        if ((self.release is not None and self.release.original_contract != release_contract)
                or (self.outgoing_trade is not None and self.outgoing_trade.original_contract != trade_contract)
                or (self.restructure is not None and (self.restructure.contract != self.contract
                    or self.restructure.original_contract != restructure_original))
                or (self.incoming_trade is not None and self.incoming_trade.buyer_contract != self.original_contract)):
            raise ValueError('Generation lifecycle plan disagrees with agreement')

    def _validate_amendment_history(self):
        from franchise.books import ActiveContract,BonusLayer
        from franchise.cash import CashObligation
        from franchise.restructures import PreseasonRestructureScope,calculate_preseason_restructure,calculate_layered_preseason_restructure
        previous=None
        for plan in (*self.prior_restructures,self.restructure):
            if (not isinstance(plan.original_contract,ActiveContract) or not isinstance(plan.contract,ActiveContract)
                    or not isinstance(plan.original_cash,CashObligation) or not isinstance(plan.cash_obligation,CashObligation)
                    or not isinstance(plan.scope,PreseasonRestructureScope) or not isinstance(plan.bonus_layer,BonusLayer)):
                raise ValueError('Typed immutable amendment history components required')
            if previous is None:
                if (plan.original_contract.elapsed_years<self.original_contract.elapsed_years
                        or plan.original_contract!=replace(self.original_contract,elapsed_years=plan.original_contract.elapsed_years)):
                    raise ValueError('First amendment must preserve immutable birth economics')
            else:
                delta=plan.scope.league_year-previous.scope.league_year
                if (delta<=0 or plan.original_contract!=replace(previous.contract,
                        elapsed_years=previous.contract.elapsed_years+delta)):
                    raise ValueError('Amendment source years and economic cursors disagree')
                before,after=previous.cash_obligation,plan.original_cash
                if (before.obligation_id!=after.obligation_id or before.player_id!=after.player_id
                        or before.amount!=after.amount or before.source!=after.source
                        or before.paid_components is None or after.paid_components is None
                        or any(dict(after.paid_components).get(key,0)<amount for key,amount in before.paid_components)):
                    raise ValueError('Amendment history dropped or changed prior nominal cash and payments')
            calculate=calculate_layered_preseason_restructure if plan.original_contract.bonus_layers else calculate_preseason_restructure
            actual=calculate(plan.original_contract,plan.original_cash,scope=plan.scope,
                converted_base=plan.converted_base,annual_minimums=plan.annual_minimums,
                record_id=plan.bonus_layer.record_id,expected_cash_id=self.identity.cash_obligation_id)
            if actual!=plan:
                raise ValueError('Amendment plan disagrees with sourced conversion and payment history')
            previous=plan
        if previous.contract!=self.contract:
            raise ValueError('Latest amendment does not produce effective contract')

    def amendment_history_snapshot(self):
        """Versioned model archive; empty history preserves legacy serializers."""
        if not self.prior_restructures:
            return None
        def snapshot(plan):
            scope=asdict(plan.scope)
            scope.update(amended_on=plan.scope.amended_on.isoformat(),
                first_regular_season_game=plan.scope.first_regular_season_game.isoformat(),
                exclusions=sorted(plan.scope.exclusions))
            return {'original_contract':plan.original_contract.to_dict(),'original_cash':plan.original_cash.to_dict(),
                'scope':scope,'annual_minimums':list(plan.annual_minimums),'converted_base':plan.converted_base,
                'bonus_layer':asdict(plan.bonus_layer),'contract':plan.contract.to_dict(),
                'cash_obligation':plan.cash_obligation.to_dict()}
        return {'format':1,'prior_restructures':[snapshot(plan) for plan in self.prior_restructures],
            'latest_restructure':snapshot(self.restructure)}

    def canonical_identity(self, team_id):
        if self.assignment_request_id is not None:
            return assignment_identity(team_id,self.identity.player_id,self.assignment_request_id)
        if self.return_request_id is not None:
            return generation_identity(team_id,self.identity.player_id,self.return_request_id)
        return legacy_identity(team_id,self.identity.player_id)

    @property
    def status(self):
        return 'released' if self.release is not None else 'assigned' if self.outgoing_trade is not None else 'active'

    @property
    def retained_records(self):
        if self.release is not None:
            return self.release.retained
        return (self.outgoing_trade.retained_bonus,) if self.outgoing_trade is not None else ()

    def annual_charges(self):
        from fractions import Fraction
        if self.status == 'active':
            return self.contract.charges()
        records = self.retained_records
        return tuple(sum((r.annual_charges[i] if i < len(r.annual_charges) else Fraction(0)
                          for r in records), Fraction(0))
                     for i in range(max((len(r.annual_charges) for r in records), default=0)))

    def payment_ceilings(self):
        ceilings = self.contract.compensation_components()
        if self.status != 'active':
            guarantees = self.contract.offer.guaranteed_salaries or (0,) * len(self.contract.offer.salaries)
            cutoff=(self.release.original_contract.elapsed_years if self.release is not None else
                    self.outgoing_trade.original_contract.elapsed_years)
            for i in range(cutoff, len(guarantees)):
                ceilings['base:' + str(i)] = guarantees[i] if self.status == 'released' else 0
        return ceilings


@dataclass(frozen=True)
class GenerationCalendarView:
    """A calendar cursor over immutable economic terms and lifecycle records.

    This view grants no transaction or ownership authority. Scheduled exhaustion
    is distinct from expiry explicitly authorized by a future durable transition.
    The optional expiry facts must assert eligibility and prove allocated cash
    settlement; source authentication remains the transition caller's obligation.
    """
    agreement: GenerationAgreement
    anchor_year: int
    current_year: int
    expiry_eligible: bool | None = None
    expiry_cash: "CashObligation | None" = None
    expiry_source: str | None = None

    def __post_init__(self):
        if (not isinstance(self.agreement,GenerationAgreement)
                or type(self.anchor_year) is not int or type(self.current_year) is not int
                or not 2020 <= self.anchor_year <= self.current_year <= 2030):
            raise ValueError('Typed agreement and explicit current/future anchored calendar required')
        if (self.agreement.release_calendar_year is not None
                and self.anchor_year != self.agreement.release_calendar_year):
            raise ValueError('Retained calendar release charges must start at the actual release year')
        if (self.agreement.outgoing_trade_calendar_year is not None
                and self.anchor_year != self.agreement.outgoing_trade_calendar_year):
            raise ValueError('Retained calendar assignment charges must start at the actual trade year')
        if (self.agreement.status=='active' and self.agreement.restructure_calendar_year is not None
                and self.anchor_year!=self.agreement.restructure_calendar_year):
            raise ValueError('Amended calendar charges must start at the actual amendment year')
        facts=(self.expiry_eligible,self.expiry_cash,self.expiry_source)
        if not any(value is not None for value in facts):
            return
        from franchise.cash import CashObligation
        if (self.expiry_eligible is not True or not isinstance(self.expiry_cash,CashObligation)
                or type(self.expiry_source) is not str or not self.expiry_source.strip()
                or self.agreement.status!='active' or not self.scheduled_term_complete):
            raise ValueError('Explicit eligible, settled, sourced scheduled expiry facts required')
        cash=self.expiry_cash
        if (cash.obligation_id!=self.agreement.identity.cash_obligation_id
                or cash.player_id!=self.agreement.identity.player_id
                or cash.amount!=self.agreement.contract.nominal_cash or cash.paid!=cash.amount
                or cash.paid_components is None):
            raise ValueError('Expiry requires complete matching allocated nominal cash settlement')
        ceilings=self.agreement.payment_ceilings()
        paid_components=dict(cash.paid_components)
        if (any(key not in ceilings for key in paid_components)
                or any(paid_components.get(key,0)!=amount for key,amount in ceilings.items())):
            raise ValueError('Expiry payment allocations disagree with economic agreement')

    @property
    def years_forward(self):
        return self.current_year-self.anchor_year

    @property
    def scheduled_term_complete(self):
        return (self.agreement.status=='active' and
            self.agreement.contract.elapsed_years+self.years_forward>=len(self.agreement.contract.offer.salaries))

    @property
    def authoritative_expired(self):
        return self.expiry_source is not None

    @property
    def status(self):
        return 'expired' if self.authoritative_expired else self.agreement.status

    @property
    def current_contract(self):
        from dataclasses import replace
        if self.agreement.status!='active' or self.scheduled_term_complete:
            return None
        return replace(self.agreement.contract,
            elapsed_years=self.agreement.contract.elapsed_years+self.years_forward)

    def annual_charges(self):
        return self.agreement.annual_charges()[self.years_forward:]

    def payment_ceilings(self):
        return self.agreement.payment_ceilings()

    def to_projection(self):
        # Preserve the existing public projection shape and its explicit scope.
        return project_agreement(self.agreement,years_forward=self.years_forward)
