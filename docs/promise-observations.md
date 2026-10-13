# Observed promise fulfillment

`record_promise_performance` maps typed PerformanceEvidence to the goals saved with
a signed agreement, then records the computed score through the same durable score
transaction. The expected revision and agreement identity remain mandatory.

Mappings:

- Touches: observed rush attempts plus receptions. Both must be known; targets
  never substitute for receptions or missing carries.
- Starts: actual games_started, never inferred from snaps or games played.
- Yard goals: the exact receiving/rushing/passing yard counter, including negative
  net yardage; achievement is bounded at zero through one.
- Team wins: separate TeamResults with matching team/window/simulation mode.

Preserve source, coverage and supplied health/coaching context. Missing measurements
remain unknown. Adding a counter definition does not prove the original game records
it. All current tests use synthetic evidence; verified guest instrumentation/import
remains required.

The automatic adapter requires explicit PerformanceEvidence.team_id and
complete_window=True before player-goal data can finalize. TeamResults separately
requires complete_window=True for win goals. Known partial counters remain progress;
closing the calendar window cannot turn partial coverage into a final result or
irreversible final lock. Foreign club evidence rejects. The current batch adapter
supports one agreed observation window/mode at a time; multi-window automatic
contract evaluation remains unfinished.

Historically supplied GoalObservation records lack the completeness field and
retain their existing explicitly sourced evaluation semantics. Direct manual score
callers remain responsible for scope/coverage; the automatic adapter never assumes
that absent metadata establishes a complete window. Null optional completeness is
omitted from receipt serialization so historical retries do not conflict.

Scores persist, replay, feed player context and may source once-only bounded
relationship changes after final known fulfillment. They create no salary incentive,
cap charge or automatic blame for injuries/coaching/team outcomes.

Multiple declared goal windows can be mapped with `observe_promise_windows` using
an immutable tuple of player snapshots and optional tuple of team results. Supply
exactly one player snapshot per agreed window; duplicate windows (including mixed
simulation modes for the same window), absent windows and unrelated windows reject.
Snapshots are not summed: callers must provide sourced window totals, so overlapping
periods cannot accidentally double-count. Each window retains its own completeness,
team scope and simulation mode. Results follow agreement goal order. A final score
still requires every goal's evidence to be known and complete. The durable store's
`record_promise_performance` accepts this tuple form as well as the existing single
snapshot; missing team snapshots remain unknown. Real game instrumentation remains
required to produce verified observations.
