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
