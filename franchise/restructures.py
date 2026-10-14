"""Pure preseason guaranteed-base conversion; no durable mutation authority."""
from dataclasses import dataclass, replace
from datetime import date
from franchise.books import ActiveContract, BonusLayer
from franchise.cap import money
from franchise.cash import CashObligation


EXCLUDED_RESTRUCTURE_TERMS = frozenset({'rookie_rules', 'salary_benefits', 'other_compensation',
    'guarantee_offsets', 'guarantee_voids', 'conditional_guarantees', 'extension', 'void_years',
    'unpaid_old_bonus', 'deferred_new_bonus', 'injury_liability', 'grievance'})


@dataclass(frozen=True)
class PreseasonRestructureScope:
    league_year: int
    amended_on: date
    first_regular_season_game: date
    current_year_earned_base: int
    healthy: bool
    consent: bool
    renegotiation_eligible: bool
    exclusions: frozenset[str]
    minimum_source: str
    source: str

    def __post_init__(self):
        if type(self.league_year) is not int or not 2020 <= self.league_year <= 2030:
            raise ValueError('Published CBA league year required')
        if (type(self.amended_on) is not date or type(self.first_regular_season_game) is not date
                or self.amended_on.year != self.league_year or self.first_regular_season_game.year != self.league_year
                or self.amended_on >= self.first_regular_season_game):
            raise ValueError('Sourced current-year preseason amendment required')
        if type(self.current_year_earned_base) is not int or self.current_year_earned_base != 0:
            raise ValueError('Verified zero earned current base required')
        if self.healthy is not True or self.consent is not True or self.renegotiation_eligible is not True:
            raise ValueError('Explicit player consent and renegotiation eligibility required')
        if type(self.exclusions) is not frozenset or self.exclusions != EXCLUDED_RESTRUCTURE_TERMS:
            raise ValueError('Explicit absence of unsupported restructure terms required')
        if any(type(value) is not str or not value.strip() for value in (self.minimum_source, self.source)):
            raise ValueError('Amendment and annual-floor provenance required')


@dataclass(frozen=True)
class RestructurePlan:
    original_contract: ActiveContract
    original_cash: CashObligation
    scope: PreseasonRestructureScope
    annual_minimums: tuple[int, ...]
    converted_base: int
    bonus_layer: BonusLayer
    contract: ActiveContract
    cash_obligation: CashObligation


def calculate_preseason_restructure(contract, cash, *, scope, converted_base, annual_minimums, record_id, expected_cash_id=None):
    return _calculate_preseason_restructure(contract, cash, scope=scope, converted_base=converted_base, annual_minimums=annual_minimums, record_id=record_id, expected_cash_id=expected_cash_id, layered=False)


def calculate_layered_preseason_restructure(contract, cash, *, scope, converted_base, annual_minimums, record_id, expected_cash_id=None):
    """Pure reconciliation only; durable history authority is a separate operation."""
    return _calculate_preseason_restructure(contract, cash, scope=scope, converted_base=converted_base, annual_minimums=annual_minimums, record_id=record_id, expected_cash_id=expected_cash_id, layered=True)


def _calculate_preseason_restructure(contract, cash, *, scope, converted_base, annual_minimums, record_id, expected_cash_id, layered):
    if not isinstance(contract, ActiveContract) or not isinstance(cash, CashObligation) or not isinstance(scope, PreseasonRestructureScope):
        raise ValueError('Typed original contract, allocated cash and amendment scope required')
    if contract.bonus_layers and not layered:
        raise ValueError('Repeated layered restructure requires separate reconciliation')
    if type(record_id) is not str or not record_id.strip() or money(converted_base) == 0:
        raise ValueError('Identified positive base conversion required')
    if layered and (not contract.bonus_layers or any(layer.original_start_index>contract.elapsed_years for layer in contract.bonus_layers)):
        raise ValueError('Existing current or earlier bonus layers required')
    if any(layer.record_id==record_id for layer in contract.bonus_layers):
        raise ValueError('New conversion requires a unique bonus identity')
    expected_cash_id = 'contract:' + contract.offer.player_id if expected_cash_id is None else expected_cash_id
    if type(expected_cash_id) is not str or not expected_cash_id.strip():
        raise ValueError('Explicit expected cash identity required')
    offer, elapsed = contract.offer, contract.elapsed_years
    remaining = len(offer.salaries) - elapsed
    if scope.league_year + remaining - 1 > 2030:
        raise ValueError('Cross-final-CBA-year amendment is unsupported')
    if type(annual_minimums) is not tuple or len(annual_minimums) != remaining or any(money(value) == 0 for value in annual_minimums):
        raise ValueError('Explicit positive annual floors for all remaining years required')
    if (cash.player_id != offer.player_id or cash.obligation_id != expected_cash_id
            or cash.amount != contract.nominal_cash or cash.paid_components is None):
        raise ValueError('Allocated original nominal contract cash required')
    paid = dict(cash.paid_components)
    ceilings = contract.compensation_components()
    if any(key not in ceilings or value > ceilings[key] for key, value in paid.items()):
        raise ValueError('Paid allocations disagree with original contract')
    if paid.get('signing_bonus', 0) != offer.signing_bonus:
        raise ValueError('Original signing bonus must already be fully paid')
    if any(paid.get(layer.cash_component,0)!=layer.amount for layer in contract.bonus_layers):
        raise ValueError('Every existing bonus layer must already be fully paid')
    for i, salary in enumerate(offer.salaries):
        value = paid.get('base:' + str(i), 0)
        if (i < elapsed and value != salary) or (i >= elapsed and value != 0):
            raise ValueError('Past bases must be settled and remaining bases unpaid')
    if not offer.guaranteed_salaries or offer.guaranteed_salaries[elapsed] != offer.salaries[elapsed]:
        raise ValueError('Current base must already be fully and unconditionally guaranteed')
    if converted_base > offer.salaries[elapsed] - annual_minimums[0]:
        raise ValueError('Conversion reduces current base below verified annual minimum')
    salaries, guarantees = list(offer.salaries), list(offer.guaranteed_salaries)
    salaries[elapsed] -= converted_base
    guarantees[elapsed] -= converted_base
    if any(salary < minimum for salary, minimum in zip(salaries[elapsed:], annual_minimums)):
        raise ValueError('Remaining salary falls below verified annual minimum')
    layer = BonusLayer(record_id, converted_base, elapsed, min(remaining, 5), scope.source)
    amended_offer = replace(offer, salaries=tuple(salaries), guaranteed_salaries=tuple(guarantees))
    amended = replace(contract, offer=amended_offer, bonus_layers=contract.bonus_layers+(layer,),
                      source=contract.source + '; base conversion: ' + scope.source)
    amended_cash = replace(cash, source=cash.source + '; base conversion: ' + scope.source)
    if amended.nominal_cash != cash.amount:
        raise ValueError('Converted base and bonus fail nominal cash reconciliation')
    if sum(amended.charges()) != sum(contract.charges()):
        raise ValueError('Remaining base and original/new bonus charges fail reconciliation')
    return RestructurePlan(contract, cash, scope, annual_minimums, converted_base, layer, amended, amended_cash)
