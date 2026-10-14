"""Pure supported preseason contract assignment; no team/ownership authority."""
from dataclasses import dataclass
from datetime import date
from franchise.books import ActiveContract, ChargeRecord
from franchise.cap import Offer
from franchise.cash import CashObligation
from franchise.termination import signing_bonus_acceleration


EXCLUDED_TRADE_LIABILITIES = frozenset({
    'unpaid_or_deferred_bonus', 'other_compensation', 'guarantee_offsets',
    'guarantee_voids', 'seller_retained_guarantees', 'waiver_transfer',
    'early_june1_designation', 'conditional_consideration', 'injury_liability',
    'grievance',
})


@dataclass(frozen=True)
class PreseasonTradeScope:
    league_year: int
    traded_on: date
    seller_first_regular_season_game: date
    buyer_first_regular_season_game: date
    exclusions: frozenset[str]
    healthy: bool
    current_year_earned_base: int
    assignment_consent: bool
    transaction_eligible: bool
    source: str

    def __post_init__(self):
        if type(self.league_year) is not int or not 2020 <= self.league_year <= 2030:
            raise ValueError('Published CBA league year required')
        dates = (self.traded_on, self.seller_first_regular_season_game, self.buyer_first_regular_season_game)
        if (any(type(value) is not date or value.year != self.league_year for value in dates)
                or self.traded_on >= min(dates[1:])):
            raise ValueError('Actual preseason trade before both sourced first regular-season games required')
        if type(self.exclusions) is not frozenset or self.exclusions != EXCLUDED_TRADE_LIABILITIES:
            raise ValueError('Explicit absence of every unsupported trade liability required')
        if self.healthy is not True or self.assignment_consent is not True or self.transaction_eligible is not True:
            raise ValueError('Verified health, assignment consent and transaction eligibility required')
        if type(self.current_year_earned_base) is not int or self.current_year_earned_base != 0:
            raise ValueError('Verified zero current-year earned base required')
        if type(self.source) is not str or not self.source.strip():
            raise ValueError('Trade scope provenance required')


@dataclass(frozen=True)
class TradePlan:
    original_contract: ActiveContract
    original_cash: CashObligation
    scope: PreseasonTradeScope
    retained_bonus: ChargeRecord
    seller_cash: CashObligation
    buyer_contract: ActiveContract
    buyer_cash: CashObligation
    assigned_base: int


def calculate_preseason_trade(contract, cash, *, scope, record_id, expected_cash_id=None, buyer_cash_id=None):
    """Assign remaining bases and their guarantees; retain paid bonus history.

No covered-release present-value acceleration applies here. The supported scope
requires bonus fully paid and all remaining base obligations assigned intact.
Veteran identity, rights, counterpart funding and atomic publication are caller
responsibilities; this plan does not validate trade consideration or guest state.
"""
    if not isinstance(contract, ActiveContract) or not isinstance(cash, CashObligation) or not isinstance(scope, PreseasonTradeScope):
        raise ValueError('Typed original contract, allocated cash and trade scope required')
    if type(record_id) is not str or not record_id.strip():
        raise ValueError('Stable trade calculation identity required')
    expected_cash_id = 'contract:' + contract.offer.player_id if expected_cash_id is None else expected_cash_id
    if type(expected_cash_id) is not str or not expected_cash_id.strip():
        raise ValueError('Explicit expected cash identity required')
    buyer_cash_id = expected_cash_id if buyer_cash_id is None else buyer_cash_id
    if type(buyer_cash_id) is not str or not buyer_cash_id.strip():
        raise ValueError('Explicit buyer cash identity required')
    offer = contract.offer
    if (cash.obligation_id != expected_cash_id or cash.player_id != offer.player_id
            or cash.amount != contract.nominal_cash or cash.paid_components is None):
        raise ValueError('Allocated original nominal contract cash required')
    paid = dict(cash.paid_components)
    ceilings = contract.compensation_components()
    if any(key not in ceilings or amount > ceilings[key] for key, amount in paid.items()):
        raise ValueError('Payment allocations disagree with original contract')
    bonuses = {'signing_bonus': offer.signing_bonus,
               **{layer.cash_component: layer.amount for layer in contract.bonus_layers}}
    if any(paid.get(key, 0) != amount for key, amount in bonuses.items()):
        raise ValueError('Every signing bonus layer must already be fully paid')
    for i, salary in enumerate(offer.salaries):
        amount = paid.get('base:' + str(i), 0)
        if i < contract.elapsed_years:
            if amount != salary:
                raise ValueError('All prior base salary must be fully settled')
        elif amount != 0:
            raise ValueError('Current/future base payments require separate assignment reconciliation')
    retained = signing_bonus_acceleration(contract, league_year=scope.league_year,
        removed_on=scope.traded_on, record_id=record_id + ':seller-bonus')
    salaries = offer.salaries[contract.elapsed_years:]
    guarantees = offer.guaranteed_salaries[contract.elapsed_years:] if offer.guaranteed_salaries else ()
    assigned = sum(salaries)
    provenance = '; preseason assignment: ' + scope.source + '; ' + record_id
    seller_cash = CashObligation(cash.obligation_id, cash.player_id, cash.paid, cash.paid,
                                 cash.source + provenance, cash.paid_components)
    buyer_contract = ActiveContract(Offer(offer.player_id, salaries, 0, guarantees),
        contract.source + provenance + '; original signing bonus remains with assigning club',
        bonus_years=contract.bonus_years)
    buyer_cash = CashObligation(buyer_cash_id, cash.player_id, assigned, 0,
                                cash.source + provenance + '; assigned remaining base', ())
    if seller_cash.amount + buyer_cash.amount != cash.amount:
        raise ValueError('Assigned and retained nominal cash do not reconcile')
    if sum(retained.annual_charges) + sum(buyer_contract.charges()) != sum(contract.charges()):
        raise ValueError('Assigned base and retained original bonus do not reconcile')
    return TradePlan(contract, cash, scope, retained, seller_cash, buyer_contract, buyer_cash, assigned)
