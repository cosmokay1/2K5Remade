"""Consensual imported-contract simulation; old bonus debt never becomes new cash.

These full-year agreements do not establish earned pay, historical payments or
native save application. Imported contract lifecycle aging remains a separate gate.
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
class LegacyAmendment:
    request_id: str
    proposal_request_id: str
    offer: Offer
    carried_bonus_charges: tuple
    source: str
    scope: FullYearAmendmentScope
    bonus_years: int = 5

    def __post_init__(self):
        if any(type(v) is not str or not v.strip() for v in
               (self.request_id, self.proposal_request_id, self.source)):
            raise ValueError('Identified accepted amendment and source required')
        if self.request_id == self.proposal_request_id or not isinstance(self.offer, Offer):
            raise ValueError('Distinct proposal/settlement identities and typed offer required')
        if not isinstance(self.scope,FullYearAmendmentScope):
            raise ValueError('Explicit supported earned-pay scope required')
        self.offer.charges(self.bonus_years)
        if (type(self.carried_bonus_charges) is not tuple or not self.carried_bonus_charges
                or any(type(v) is not int and not isinstance(v, Fraction) for v in self.carried_bonus_charges)
                or any(v < 0 for v in self.carried_bonus_charges)):
            raise ValueError('Exact immutable retained bonus charges required')

    def charges(self):
        added=self.offer.charges(self.bonus_years)
        return tuple((added[i] if i<len(added) else 0) +
                     (self.carried_bonus_charges[i] if i<len(self.carried_bonus_charges) else 0)
                     for i in range(max(len(added),len(self.carried_bonus_charges))))

    def bonus_charges(self):
        return tuple(value-(self.offer.salaries[i] if i<len(self.offer.salaries) else 0)
                     for i,value in enumerate(self.charges()))

    def to_dict(self):
        return dict(rule=RULE,request_id=self.request_id,proposal_request_id=self.proposal_request_id,
            offer=self.offer.to_dict(),carried_bonus_charges=[json_amount(v) for v in self.carried_bonus_charges],
            combined_player_charges=[json_amount(v) for v in self.charges()],
            new_cash_commitment=sum(self.offer.salaries)+self.offer.signing_bonus,
            source=self.source,scope=self.scope.to_dict(),bonus_years=self.bonus_years)
