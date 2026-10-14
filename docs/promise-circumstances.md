# Sourced promise circumstances

Promise achievement remains the observed value divided by the original target,
weighted by agreed importance. Injury, availability and coaching context never
rewrite those values, targets, cap charges or cash obligations.

`PromiseCircumstances` records one declared player/team/window/simulation-mode
context with source, coverage and explicit window completeness. Its count fields
are `total_games`, `available_games`, `injury_unavailable_games` and
`coaching_dnp_games`. Each is an observed nonnegative integer or `None`. Unknown
counts require `unavailable_reason`; known zero is distinct from unknown.

Available means healthy and eligible, including games in which the coach did not
use the player. Injury-unavailable games and available games are disjoint;
coaching DNPs are a subset of available games. Known counts must fit known total
games, but the engine does not assume those categories explain all absences.
It does not classify suspensions, rest or other causes by subtraction.

A synthetic example, not a report about a real player:

```python
from franchise.promises import PromiseCircumstances

circumstances = (PromiseCircumstances(
    player_id="v", team_id="a", window="2026-season", mode="cpu_played",
    total_games=17, available_games=12, injury_unavailable_games=5,
    coaching_dnp_games=3, source="synthetic fixture",
    coverage="all seventeen team games", complete_window=True,
    unavailable_reason=None,
),)
```

Pass the tuple through `record_promise_performance(..., circumstances=...)` or
`record_promise_score(..., circumstances=...)`. The performance mapper additionally
requires matching typed player/team/window/mode evidence. Direct scoring retains
its caller-sourced observation boundary; it does not establish a verified guest
counter or independent simulation mode. Typed performance consistency is checked
when recording; replay retains projected observations and declared circumstances,
not an independent raw collector snapshot proving the original simulation mode.

The optional format-1 promise-score envelope stores circumstances alongside the
raw score. Omitting circumstances preserves historical event/result shapes.
Replay validates the records and original agreement identities. Exact retries
retain the same context; changing it requires a separate supported evaluation,
and already-final scores still cannot be corrected through this API.

Recorded promise history supplies this context to later negotiation together
with persistent player priorities and relationships. The model must retain
unknown coverage and cannot infer fault from a missed goal or automatically
adjust trust. Relationship changes remain explicit, bounded, once-only sourced
transactions. A context-aware consequence policy and actual game capture/UI
remain unfinished; this evidence format does not prove injuries or coaching
choices were captured from the game.
