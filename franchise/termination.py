"""Signing-bonus acceleration component; not a complete release transaction.

Base guarantees, earned salary, injury protections, termination pay and roster
replacement costs must be added before this can authorize a real release.
"""
from datetime import date
from fractions import Fraction
from franchise.books import ActiveContract, ChargeRecord
from franchise.minimums import SOURCE

RULE_VERSION = "2020-cba-article13-6bii-bonus-acceleration"


def signing_bonus_acceleration(contract: ActiveContract, *, league_year: int,
                               removed_on: date, record_id: str) -> ChargeRecord:
    """Retain exact original bonus layers, applying actual June-1 timing only.

    This version deliberately excludes early post-June-1 designations and dates
    in the following calendar year, which require a verified league calendar.
    Final CBA year 2030 accelerates all remaining bonus into the current year.
    """
    if not isinstance(contract, ActiveContract):
        raise ValueError("Original active contract required")
    if type(league_year) is not int or not 2020 <= league_year <= 2030:
        raise ValueError("Published CBA league year required")
    if type(removed_on) is not date or removed_on.year != league_year:
        raise ValueError("Removal date must be in the declared calendar year")
    salaries = contract.offer.salaries[contract.elapsed_years:]
    bonus = tuple(charge - salary for charge, salary in zip(contract.charges(), salaries))
    if any(value < 0 for value in bonus):
        raise ValueError("Original bonus allocation disagrees with contract")
    if removed_on <= date(league_year, 6, 1) or league_year == 2030:
        retained = (sum(bonus, Fraction(0)),)
    else:
        retained = (bonus[0], sum(bonus[1:], Fraction(0)))
    return ChargeRecord(record_id, retained, SOURCE + "#article-13-section-6-b-ii; " + RULE_VERSION)
