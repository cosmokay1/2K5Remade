"""Consensual imported-contract simulation; old bonus debt never becomes new cash.

Earned base is an obligation, never evidence of payment. Salary-period evidence
must be sourced before negotiation; native calendar mapping is a separate gate.
"""
from dataclasses import dataclass,asdict
from fractions import Fraction

from franchise.cap import Offer, json_amount

RULE = 'legacy_bonus_carry_v1'


@dataclass(frozen=True)
class FullYearAmendmentScope:
    current_year_earned_base: int
    source: str

    def __post_init__(self):
        if type(self.current_year_earned_base) is not int or self.current_year_earned_base!=0:
            raise ValueError('Verified zero earned base required; in-season proration is not supported')
        if type(self.source) is not str or not self.source.strip():
            raise ValueError('Earned-pay/calendar provenance required')

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls,value):
        if type(value) is not dict or set(value)!={'current_year_earned_base','source'}:
            raise ValueError('Complete earned-pay scope required')
        return cls(**value)


@dataclass(frozen=True)
class InSeasonAmendmentScope:
    league_year: int
    elapsed_periods: int
    total_periods: int
    source: str

    def __post_init__(self):
        if (type(self.league_year) is not int or not 1900 <= self.league_year <= 9999
                or type(self.elapsed_periods) is not int or type(self.total_periods) is not int
                or not 1 <= self.total_periods <= 366
                or not 0 <= self.elapsed_periods <= self.total_periods
                or type(self.source) is not str or not self.source.strip()):
            raise ValueError('Sourced league year and elapsed salary periods required')

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls,value):
        if type(value) is not dict or set(value)!={'league_year','elapsed_periods','total_periods','source'}:
            raise ValueError('Complete in-season salary-period scope required')
        return cls(**value)

    def remaining_base(self,annual_salary):
        return Fraction(annual_salary * (self.total_periods-self.elapsed_periods),self.total_periods)


def amendment_scope_from_dict(value):
    if type(value) is dict and 'elapsed_periods' in value:
        return InSeasonAmendmentScope.from_dict(value)
    return FullYearAmendmentScope.from_dict(value)


def amendment_earned_base(scope, original_base, previous=None):
    """Accrue each prior annual rate only over the periods it governed.

    No games-played, injury or bye adjustment: the explicit simulation clock
    measures salary periods, not player appearances. Never infer a clock here.
    """
    if scope is None or isinstance(scope,FullYearAmendmentScope):
        if previous is not None and isinstance(previous.scope,InSeasonAmendmentScope):
            raise ValueError('An in-season agreement cannot reset to zero earned pay')
        return 0
    if not isinstance(scope,InSeasonAmendmentScope):
        raise ValueError('Typed earned-pay scope required')
    elapsed=0;earned=0;base=original_base
    if previous is not None:
        base=previous.offer.salaries[0]
        if isinstance(previous.scope,InSeasonAmendmentScope):
            prior=previous.scope
            if (scope.league_year!=prior.league_year or scope.total_periods!=prior.total_periods
                    or scope.elapsed_periods<prior.elapsed_periods):
                raise ValueError('Earned-pay clock cannot change year, denominator or run backward')
            elapsed=prior.elapsed_periods;earned=previous.earned_base
    return earned + Fraction(base*(scope.elapsed_periods-elapsed),scope.total_periods)


@dataclass(frozen=True)
class LegacyAmendment:
    request_id: str
    proposal_request_id: str
    offer: Offer
    carried_bonus_charges: tuple
    source: str
    scope: FullYearAmendmentScope | InSeasonAmendmentScope
    bonus_years: int = 5
    earned_base: int | Fraction = 0

    def __post_init__(self):
        if any(type(v) is not str or not v.strip() for v in
               (self.request_id, self.proposal_request_id, self.source)):
            raise ValueError('Identified accepted amendment and source required')
        if self.request_id == self.proposal_request_id or not isinstance(self.offer, Offer):
            raise ValueError('Distinct proposal/settlement identities and typed offer required')
        if not isinstance(self.scope,(FullYearAmendmentScope,InSeasonAmendmentScope)):
            raise ValueError('Explicit supported earned-pay scope required')
        if (type(self.earned_base) is not int and not isinstance(self.earned_base,Fraction)) or self.earned_base<0:
            raise ValueError('Exact nonnegative earned base required')
        if isinstance(self.scope,FullYearAmendmentScope) and self.earned_base!=0:
            raise ValueError('Full-year scope cannot discard earned base')
        self.offer.charges(self.bonus_years)
        if (type(self.carried_bonus_charges) is not tuple or not self.carried_bonus_charges
                or any(type(v) is not int and not isinstance(v, Fraction) for v in self.carried_bonus_charges)
                or any(v < 0 for v in self.carried_bonus_charges)):
            raise ValueError('Exact immutable retained bonus charges required')

    def base_charges(self):
        base=list(self.offer.salaries)
        if isinstance(self.scope,InSeasonAmendmentScope):
            base[0]=self.earned_base+self.scope.remaining_base(base[0])
        return tuple(base)

    def charges(self):
        added=list(self.offer.charges(self.bonus_years))
        added[0]+=self.base_charges()[0]-self.offer.salaries[0]
        return tuple((added[i] if i<len(added) else 0) +
                     (self.carried_bonus_charges[i] if i<len(self.carried_bonus_charges) else 0)
                     for i in range(max(len(added),len(self.carried_bonus_charges))))

    def bonus_charges(self):
        return tuple(value-(self.base_charges()[i] if i<len(self.offer.salaries) else 0)
                     for i,value in enumerate(self.charges()))

    def to_dict(self):
        result=dict(rule=RULE,request_id=self.request_id,proposal_request_id=self.proposal_request_id,
            offer=self.offer.to_dict(),carried_bonus_charges=[json_amount(v) for v in self.carried_bonus_charges],
            combined_player_charges=[json_amount(v) for v in self.charges()],
            new_cash_commitment=json_amount(sum(self.base_charges())-self.earned_base+self.offer.signing_bonus),
            source=self.source,scope=self.scope.to_dict(),bonus_years=self.bonus_years)

        if isinstance(self.scope,InSeasonAmendmentScope):
            result['earned_base_obligation']=json_amount(self.earned_base)
            result['remaining_base_commitment']=json_amount(self.scope.remaining_base(self.offer.salaries[0]))
        return result
