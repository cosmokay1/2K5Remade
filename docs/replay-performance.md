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
