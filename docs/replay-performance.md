# Synthetic replay measurement

Run `python3 -m tools.benchmark_replay` for a temporary 32-team/640-dialogue fixture.
`--stories-per-team 100` uses3,200 dialogue events. Preparation writes only a new
private temporary database and removes it afterward; no existing franchise, cloud,
credentials or guest files are used. Teams2–64 and stories0–1000 are explicitly bounded.

The fixture performs a supported paired assignment, then times five validated team
reads with independent all-team replay enabled. It verifies expected recipient
charges/revision and exact retained dialogue count. These are deliberately short
synthetic legacy dialogues, not realistic model-evidence payloads or real game history.

October13 local Mac measurements:

| Teams | Dialogue events | Median validated read | Maximum of5 reads |
|---|---:|---:|---:|
|32|640|8.31 ms|8.96 ms|
|32|3,200|32.39 ms|33.07 ms|

No timing assertion is added to correctness tests; hardware/filesystem variability
makes one measurement unsuitable as a universal latency contract. These results do
not justify introducing persistent replay caching yet. Windows/Deck performance,
large sourced statistics/promise/history payloads and actual guest responsiveness
still require their own runtime measurements.

`--recorded-context` builds stories through the real Negotiation/StoredLedger path
using a scripted rejection provider, typed synthetic performance with unknown targets/
pressures, persisted actors, nonfinancial proposals and complete prior-request IDs.
No paid model or cloud calls occur. This measures heavier recorded evidence without
claiming realistic narrative length or real player data; fixture preparation is slower.

| Teams | Recorded evidence events | Median validated read | Maximum of5 reads |
|---|---:|---:|---:|
|32|640|22.55 ms|22.94 ms|
|32|3,200|111.76 ms|113.79 ms|

The short-dialogue baseline materially understates this workload. Multiple independent
reads during a request can accumulate this cost; actual Windows/Deck profiles and
normal game histories must be measured before promising a deadline. The benchmark
keeps full history validation and adds no stale-state cache.
