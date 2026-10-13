"""Explicit, source-bound veteran salary floors; not a complete league ruleset."""
from dataclasses import dataclass
from franchise.minimums import minimum_schedule, RULE_VERSION, SOURCE


@dataclass(frozen=True)
class VeteranMinimumProfile:
    start_year: int
    # Tuple records prevent caller mutation after financial state is created.
    players: tuple[tuple[str, tuple[int, ...], tuple[str, ...]], ...]
    rule_version: str = RULE_VERSION
    source: str = SOURCE

    def __post_init__(self):
        if self.rule_version != RULE_VERSION or self.source != SOURCE:
            raise ValueError("Unsupported salary-floor source or rule version")
        if type(self.start_year) is not int or not 2020 <= self.start_year <= 2030:
            raise ValueError("Salary profile requires a published modern league year")
        if type(self.players) is not tuple:
            raise ValueError("Immutable player salary inputs required")
        seen = set()
        for record in self.players:
            if type(record) is not tuple or len(record) != 3:
                raise ValueError("Player, annual credits and annual categories required")
            player, credits, categories = record
            if type(player) is not str or not player.strip() or player in seen:
                raise ValueError("Unique stable veteran IDs required")
            seen.add(player)
            minimum_schedule(self.start_year, credits, categories)

    def floors(self) -> dict[str, tuple[int, ...]]:
        return {player: minimum_schedule(self.start_year, credits, categories)
                for player, credits, categories in self.players}

    def to_dict(self) -> dict:
        return {"start_year": self.start_year, "rule_version": self.rule_version,
                "source": self.source,
                "players": [{"player_id": player, "credited_seasons": list(credits),
                             "roster_categories": list(categories)}
                            for player, credits, categories in self.players]}

    @classmethod
    def from_dict(cls, data: dict):
        if type(data) is not dict or set(data) != {"start_year", "rule_version", "source", "players"}:
            raise ValueError("Invalid salary profile fields")
        if type(data["players"]) is not list:
            raise ValueError("Salary profile player list required")
        records = []
        for record in data["players"]:
            if type(record) is not dict or set(record) != {"player_id", "credited_seasons", "roster_categories"}:
                raise ValueError("Invalid annual player inputs")
            if type(record["credited_seasons"]) is not list or type(record["roster_categories"]) is not list:
                raise ValueError("Annual player inputs must be lists")
            records.append((record["player_id"], tuple(record["credited_seasons"]),
                            tuple(record["roster_categories"])))
        return cls(data["start_year"], tuple(records), data["rule_version"], data["source"])
