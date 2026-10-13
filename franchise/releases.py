"""Pure supported preseason release plan; no ownership or commit authority.

Scope facts are supplied assertions with provenance, not facts inferred from a
release date or player rating. A caller must separately verify veteran status.
"""
from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from franchise.books import ActiveContract, ChargeRecord
from franchise.cash import CashObligation
from franchise.guarantees import DiscountProfile, guaranteed_base_liability
from franchise.termination import signing_bonus_acceleration


EXCLUDED_LIABILITIES = frozenset({
    'injury_liability', 'grievance', 'additional_termination_pay',
    'other_compensation', 'guarantee_offsets', 'guarantee_voids',
    'early_june1_designation', 'waiver_transfer',
})


@dataclass(frozen=True)
class PreseasonReleaseScope:
    league_year: int
    removed_on: date
    first_regular_season_game: date
    exclusions: frozenset[str]
    covered_guarantees: bool
    healthy: bool
    current_year_earned_base: int
    source: str

    def __post_init__(self):
        if type(self.league_year) is not int or not 2020 <= self.league_year <= 2030:
            raise ValueError('Published CBA league year required')
        if (type(self.removed_on) is not date or type(self.first_regular_season_game) is not date
                or self.removed_on.year != self.league_year
                or self.first_regular_season_game.year != self.league_year
                or self.removed_on >= self.first_regular_season_game):
            raise ValueError('Actual release before sourced first regular-season game required')
        if type(self.exclusions) is not frozenset or self.exclusions != EXCLUDED_LIABILITIES:
            raise ValueError('Explicit absence of every unsupported release liability required')
        if self.covered_guarantees is not True:
            raise ValueError('Termination covered by original unconditional base guarantees required')
        if self.healthy is not True or type(self.current_year_earned_base) is not int or self.current_year_earned_base != 0:
            raise ValueError('Verified healthy player and no current-year earned base required')
        if type(self.source) is not str or not self.source.strip():
            raise ValueError('Release scope provenance required')


@dataclass(frozen=True)
class ReleasePlan:
    original_contract: ActiveContract
    original_cash: CashObligation
    scope: PreseasonReleaseScope
    discount: DiscountProfile
    payment_year_offsets: tuple[int, ...]
    retained: tuple[ChargeRecord, ...]
    cash_obligation: CashObligation
    cancelled_unearned_base: int

    def charges(self):
        years = max(len(record.annual_charges) for record in self.retained)
        return tuple(sum((Fraction(record.annual_charges[i]) for record in self.retained
                          if i < len(record.annual_charges)), Fraction(0)) for i in range(years))


def calculate_preseason_release(contract, cash, *, scope, discount, payment_year_offsets, record_id):
    """Retain original bonus layers and protected cash; cancel unearned bases.

Current/future base payments and unsettled prior bases are unsupported. Payment
offsets and discount rate must have independently verified provenance; neither
is chosen from salary indices. Callers must verify the scope assertions and
veteran classification before applying this plan to durable state.
"""
    if (not isinstance(contract, ActiveContract) or not isinstance(cash, CashObligation)
            or not isinstance(scope, PreseasonReleaseScope) or not isinstance(discount, DiscountProfile)):
        raise ValueError('Typed original contract, allocated cash, release scope and discount required')
    if type(record_id) is not str or not record_id.strip():
        raise ValueError('Identified release calculation required')
    if scope.league_year != discount.league_year:
        raise ValueError('Release and discount league years disagree')
    offer = contract.offer
    if (cash.player_id != offer.player_id or cash.obligation_id != 'contract:' + offer.player_id
            or cash.amount != sum(offer.salaries) + offer.signing_bonus or cash.paid_components is None):
        raise ValueError('Allocated original nominal contract cash required')
    paid = dict(cash.paid_components)
    ceilings = {'signing_bonus': offer.signing_bonus,
                **{'base:' + str(i): salary for i, salary in enumerate(offer.salaries)}}
    if any(key not in ceilings or amount > ceilings[key] for key, amount in paid.items()):
        raise ValueError('Payment allocation disagrees with original compensation')
    for i, salary in enumerate(offer.salaries):
        amount = paid.get('base:' + str(i), 0)
        if i < contract.elapsed_years:
            if amount != salary:
                raise ValueError('Prior base salary must be fully settled')
        elif amount != 0:
            raise ValueError('Current/future paid or earned base requires separate reconciliation')
    guarantees = offer.guaranteed_salaries or (0,) * len(offer.salaries)
    unpaid = guarantees[contract.elapsed_years:]
    bonus = signing_bonus_acceleration(contract, league_year=scope.league_year,
        removed_on=scope.removed_on, record_id=record_id + ':bonus')
    base = guaranteed_base_liability(contract, unpaid_by_year=unpaid,
        payment_year_offsets=payment_year_offsets, discount=discount, record_id=record_id + ':base')
    cancelled = sum(salary - protected for salary, protected in
                    zip(offer.salaries[contract.elapsed_years:], unpaid))
    settled_cash = CashObligation(cash.obligation_id, cash.player_id, cash.amount - cancelled,
        cash.paid, cash.source + '; preseason release: ' + scope.source, cash.paid_components)
    # Cash remains nominal. Present-value cap discount never erases cash owed.
    expected_unpaid = base.nominal_unpaid + offer.signing_bonus - paid.get('signing_bonus', 0)
    if settled_cash.amount - settled_cash.paid != expected_unpaid:
        raise ValueError('Retained nominal cash does not reconcile')
    return ReleasePlan(contract, cash, scope, discount, payment_year_offsets,
                       (bonus, base.cap_charge), settled_cash, cancelled)
