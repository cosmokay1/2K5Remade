"""Covered base-guarantee present-value component; no release authorization.

Published rule: CBA Article 13 section 6(d)(iv), Article 1 discount-rate definition.
Actual rate provenance and payment timing must be supplied. This component
supports whole annual compounding periods only; it never chooses a day-count rule.
"""
from dataclasses import dataclass
from fractions import Fraction
from franchise.books import ActiveContract, ChargeRecord
from franchise.cap import money
from franchise.minimums import SOURCE

RULE_VERSION = "2020-cba-article13-6div-covered-base-present-value"


@dataclass(frozen=True)
class DiscountProfile:
    league_year: int
    annual_rate: Fraction
    rate_source: str

    def __post_init__(self):
        if type(self.league_year) is not int or not 2020 <= self.league_year <= 2030:
            raise ValueError("Published CBA year required")
        if type(self.annual_rate) is not Fraction or self.annual_rate < 0:
            raise ValueError("Explicit nonnegative exact annual discount rate required")
        if type(self.rate_source) is not str or not self.rate_source.strip():
            raise ValueError("Discount rate provenance required")


@dataclass(frozen=True)
class GuaranteedBaseLiability:
    nominal_unpaid: int
    cap_charge: ChargeRecord
    discount_profile: DiscountProfile


def guaranteed_base_liability(contract: ActiveContract, *, unpaid_by_year: tuple[int, ...],
                              payment_year_offsets: tuple[int, ...], discount: DiscountProfile,
                              record_id: str) -> GuaranteedBaseLiability:
    """Value supplied covered unpaid bases, separately from retained bonus.

    Caller must verify covered termination and actual paid/offset/void facts.
    Timing values are explicit whole years, not inferred from salary-year index.
    Partial-year timing, conditional guarantees and offsets are unsupported here.
    """
    if not isinstance(contract, ActiveContract) or not isinstance(discount, DiscountProfile):
        raise ValueError("Original contract and explicit discount profile required")
    remaining = len(contract.offer.salaries) - contract.elapsed_years
    if (type(unpaid_by_year) is not tuple or type(payment_year_offsets) is not tuple
            or len(unpaid_by_year) != remaining or len(payment_year_offsets) != remaining):
        raise ValueError("Explicit unpaid bases and payment timing for all remaining years required")
    guarantees = contract.offer.guaranteed_salaries or (0,) * len(contract.offer.salaries)
    guarantees = guarantees[contract.elapsed_years:]
    value = Fraction(0)
    for amount, years, ceiling in zip(unpaid_by_year, payment_year_offsets, guarantees):
        if money(amount) > ceiling:
            raise ValueError("Unpaid guaranteed base exceeds original protected amount")
        if type(years) is not int or years < 0:
            raise ValueError("Whole nonnegative payment-year offsets required")
        value += Fraction(amount) / (1 + discount.annual_rate) ** years
    return GuaranteedBaseLiability(sum(unpaid_by_year),
        ChargeRecord(record_id, (value,), SOURCE + "#article-13-section-6-d-iv; " + RULE_VERSION), discount)
