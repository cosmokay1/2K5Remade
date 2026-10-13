"""Supported base/prorated-bonus phase component, CBA Article 13 section 6(a).

Other contract components and retained obligations must be supplied separately.
No roster date, minimum, undrafted status or game field is inferred here.
"""
from dataclasses import dataclass
from fractions import Fraction
from franchise.cap import money, json_amount
from franchise.minimums import SOURCE

RULE_VERSION = "2020-cba-article13-6a-top51-base"


@dataclass(frozen=True)
class RosterSalary:
    player_id: str
    base_salary: int
    bonus_proration: Fraction
    active_inactive_minimum: int
    undrafted_rookie: bool
    source: str

    def __post_init__(self):
        if type(self.player_id) is not str or not self.player_id.strip() or type(self.source) is not str or not self.source.strip():
            raise ValueError("Roster salary identity/provenance required")
        money(self.base_salary)
        if money(self.active_inactive_minimum) == 0:
            raise ValueError("Explicit positive applicable minimum required")
        if type(self.bonus_proration) is not Fraction or self.bonus_proration < 0:
            raise ValueError("Exact nonnegative bonus proration required")
        if type(self.undrafted_rookie) is not bool:
            raise ValueError("Explicit undrafted-rookie classification required")

    @property
    def value(self):
        return self.base_salary + self.bonus_proration

    @property
    def excluded_base(self):
        threshold = self.active_inactive_minimum * (1 if self.undrafted_rookie else 2)
        return max(0, self.base_salary - threshold)


def roster_charge(entries: tuple[RosterSalary, ...], *, phase: str,
                  selected_top51: frozenset[str] | None = None) -> dict:
    if type(entries) is not tuple or any(not isinstance(entry, RosterSalary) for entry in entries):
        raise ValueError("Immutable supported roster salary entries required")
    by_id = {entry.player_id: entry for entry in entries}
    if len(by_id) != len(entries):
        raise ValueError("Duplicate roster salary identity")
    if phase not in {"offseason", "regular_season"}:
        raise ValueError("Explicit supported league phase required")
    if phase == "regular_season":
        if selected_top51 is not None:
            raise ValueError("Top-51 selection does not apply in regular season")
        selected = frozenset(by_id)
    else:
        ranked = sorted(entries, key=lambda entry: (-entry.value, entry.player_id))
        count = min(51, len(ranked))
        if selected_top51 is None:
            if len(ranked) > 51 and ranked[50].value == ranked[51].value:
                tied = [entry for entry in ranked if entry.value == ranked[50].value]
                savings = {entry.base_salary - entry.excluded_base for entry in tied}
                if len(savings) > 1:
                    raise ValueError("Boundary tie changes accounting; verified Top-51 selection required")
            selected = frozenset(entry.player_id for entry in ranked[:count])
        else:
            if type(selected_top51) is not frozenset or len(selected_top51) != count or not selected_top51 <= by_id.keys():
                raise ValueError("Complete valid Top-51 selection required")
            selected = selected_top51
            outside = [entry.value for entry in entries if entry.player_id not in selected]
            if outside and min(by_id[player].value for player in selected) < max(outside):
                raise ValueError("Selection excludes a higher-valued contract")
    bases = sum(entry.base_salary if entry.player_id in selected else entry.excluded_base for entry in entries)
    bonuses = sum((entry.bonus_proration for entry in entries), Fraction(0))
    return {"phase": phase, "selected_players": sorted(selected),
            "counted_base": bases, "all_bonus_proration": json_amount(bonuses),
            "supported_roster_charge": json_amount(bases + bonuses),
            "source": SOURCE, "rule_version": RULE_VERSION}
