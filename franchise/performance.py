"""Observed production with explicit coverage; no hidden-rating estimates."""
from dataclasses import dataclass

# Supported counters only: additions require an actual observation definition.
COUNTERS = frozenset({"games", "games_started", "snaps", "targets", "receptions", "receiving_yards",
                      "drops", "dropbacks", "pass_attempts", "completions",
                      "passing_yards", "interceptions", "sacks", "pressures",
                      "rush_attempts", "rushing_yards", "touchdowns"})
MODES = frozenset({"played", "cpu_played", "fast_sim"})


@dataclass(frozen=True)
class Observation:
    counter: str
    value: int | None
    source: str
    unavailable_reason: str | None = None

    def __post_init__(self):
        if self.counter not in COUNTERS:
            raise ValueError("Unsupported observed counter")
        if type(self.source) is not str or not self.source.strip():
            raise ValueError("Observed counters require source provenance")
        if self.value is None:
            if type(self.unavailable_reason) is not str or not self.unavailable_reason.strip():
                raise ValueError("Unavailable evidence requires a reason")
        else:
            if type(self.value) is not int:
                raise ValueError("Observed counters require integer values")
            if self.value < 0 and self.counter not in {"receiving_yards", "passing_yards", "rushing_yards"}:
                raise ValueError("Counts cannot be negative")
            if self.unavailable_reason is not None:
                raise ValueError("Available evidence cannot also be unavailable")


@dataclass(frozen=True)
class PerformanceEvidence:
    player_id: str
    window: str
    mode: str
    observations: tuple[Observation, ...]
    coverage: str
    team_id: str | None = None
    complete_window: bool | None = None

    def __post_init__(self):
        for text in (self.player_id, self.window, self.coverage):
            if type(text) is not str or not text.strip():
                raise ValueError("Stable player, observation window and coverage required")
        if self.team_id is not None and (type(self.team_id) is not str or not self.team_id.strip()):
            raise ValueError('Explicit team identity required when supplied')
        if self.complete_window is not None and type(self.complete_window) is not bool:
            raise ValueError('Explicit coverage completeness flag required')
        if self.mode not in MODES:
            raise ValueError("Separate played, CPU-played and fast-sim evidence required")
        if type(self.observations) is not tuple or any(not isinstance(item, Observation) for item in self.observations):
            raise ValueError("Immutable observed counter records required")
        values = {item.counter: item.value for item in self.observations}
        if len(values) != len(self.observations):
            raise ValueError("Duplicate counters in one observation window")
        # Both values must cover the same declared window. Missing opportunity
        # counts never become zero or get estimated from outcome counts.
        for smaller, larger in (("receptions", "targets"), ("completions", "pass_attempts"), ("games_started", "games")):
            if values.get(smaller) is not None and values.get(larger) is not None:
                if values[smaller] > values[larger]:
                    raise ValueError("Outcomes exceed observed opportunities")

    def to_context(self) -> dict:
        return {"player_id": self.player_id, "window": self.window,
                "mode": self.mode, "coverage": self.coverage,
                **({"team_id": self.team_id} if self.team_id is not None else {}),
                **({"complete_window": self.complete_window} if self.complete_window is not None else {}),
                "observations": {item.counter: {"value": item.value, "source": item.source,
                                                "unavailable_reason": item.unavailable_reason}
                                 for item in self.observations},
                "missing_counters": sorted(COUNTERS - {item.counter for item in self.observations})}
