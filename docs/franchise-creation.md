# Franchise creation and player identities

Use `FranchiseStore.create_franchise(teams, seed=None)` with source-backed pristine
Ledger objects keyed by stable team IDs. It creates teams, exclusive contract
ownership, initial player actors and saved generation metadata in one SQLite
transaction. Failure leaves no partially created league. The actual game franchise
creation hook and verified roster import still require the legal runtime inputs.

```python
origin = store.create_franchise(teams)  # teams contains verified opening ledgers
```

A fresh world receives a random seed unless explicitly supplied. The seed is saved
with generation version `franchise-personality-v1`. Each player has an independent
stream derived from an unambiguous encoding of version, seed and stable player ID;
roster order and team membership do not reroll personality. Fixed golden tests
protect the version's behavior. Recreating an existing franchise is rejected.

All registered veterans/rookies/free agents receive authored fictional money,
security, playing-time, winning, loyalty, patience and risk-tolerance priorities,
plus a negotiation style. These are simulation personalities, not claims about
real athletes, and use no ratings or fabricated performance. Team relationships
begin explicitly neutral: trust/respect/team connection 0.5. Subsequent bounded,
sourced consequences are separate history events.

Every contracted roster player must have a registered classification. Teams added
later via create_team receive the same initialization atomically. Player personality
follows stable identity across clubs; relationships remain team-specific. Existing
legacy databases without generation metadata retain their authored actors. Replay
checks generated original actors against saved origin and refuses incomplete actor
coverage; it does not repair missing records by rerolling or resetting trust.

This process currently runs in the independent franchise engine. It does not yet
read retail rosters, create a game save or demonstrate native-game playability.

## Bootstrap command

A verified game adapter can supply a bounded JSON bundle with exact top-level fields
`format` (integer 1), `source` (declared export provenance), `seed` (string or null),
and `teams` (team IDs mapped to `Ledger.bootstrap_config()` objects). Original source
books and classification/rules inputs remain mandatory; this command does not decode
raw retail saves or certify the export's game meaning.

Historical salary-floor profiles may include a typed `HistoricalEconomy` policy.
Their `start_year` remains the published modern rule year (2026 at game2004),
not the game's display year. The profile persists the exact conversion policy,
target cap, reference cap/year/source and posting direction; reload reconstructs
and compares the resulting floors. Unscaled profiles retain their previous JSON
shape. Negotiation context labels the adaptation beside the minimum source.
Year transitions require the same adaptation policy; switching economies needs
an explicit verified migration rather than silently changing salary floors.
Actual game-to-rule calendar binding remains an adapter requirement.

```sh
python3 -m tools.create_franchise --input /path/to/bootstrap.json --database /path/to/new-franchise.sqlite
```

The command rejects duplicate JSON fields, unsupported fields/types and existing
or symlink destinations. It creates a private temporary database beside the chosen
output, initializes players, stores the input SHA-256/source, replays every team,
then atomically publishes without replacement. Concurrent winners are preserved.
Failure removes only its own temporary artifacts. The receipt reports engine
creation counts and explicitly says game runtime verification is false. Existing
franchises are never rerolled by retrying creation.
