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

An explicit `observed_player_ids` registry with source provenance may initialize
identities whose contract classification is still unknown. It does not supply a
zero-credit minimum or authorize a new owned modern contract. Their saved
personalities/relationships are readable with `classification_pending=true`;
manual acquisition rejects missing floors and negotiation rejects before model
inference. This separates verified roster identity from unverified financial
rules. Existing classified players retain their previous context/config shape.

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

An optional `cash` object imports opening compensation/payment history before
publication. When present it must cover every team exactly. Each value contains
`source`, `records` (serialized `CashObligation` records) and
`unknown_legacy_players` (explicit legacy IDs whose cash history is unavailable).
Existing cash reconciliation validates contract amounts and coverage. For example,
a team containing only preserved legacy player `legacy-id` may declare:

```json
"cash": {
  "team-id": {
    "source": "Legacy payment history unavailable in the declared source",
    "records": [],
    "unknown_legacy_players": ["legacy-id"]
  }
}
```

Unknown legacy totals remain null; this does not assert zero compensation or
payment. Omitting `cash` retains the previous behavior of unavailable cash books.
Any failed team import discards the unpublished database, including earlier teams'
successful imports and generated personalities. The receipt counts all registered
players (including legacy and classification-pending identities) and reports
`cash_initialized_teams`. Neither importing cash nor publishing a DB establishes
complete modern cap obligations, classification, native binding or write authority.


## Shared snapshot context

New registries use one intake path for the original game and compatible packs.
Provide verified calendar and money data explicitly when the saved scheduler's
coordinates differ from the logical season. For example, this context represents
season2026 at scheduler index0 with four display dollars per raw liability dollar:

```json
{
  "season_year": 2026,
  "season_index": 0,
  "money_scale": 4,
  "league_cap_raw": 75300
}
```

```sh
python3 -m tools.franchise_snapshot_bindings /path/to/SAVEGAME.DAT /path/to/new-bindings.json --create --game-context /path/to/context.json --game-xbe /path/to/default.xbe
```

The optional executable records source-image provenance; its name or hash never
selects calendar, units or rules. This digest describes the supplied source file,
not the host's engine.loaded-image.v1 digest after built-in file patches.
Without explicit context, creation uses the decoded scheduler year/index, raw cap
and unit factor1, and rejects a different scheduled-game year. Supported liability
unit factors are currently1 and4. The raw cap must match the save; null is allowed
only when the raw cap is unavailable. That permits identity inspection, not a
financial import. Logical year must match the inspected roster/schedule year.

Version2 registries persist this context with the original franchise namespace,
player UUIDs, biography guards and personality seed. Resolution checks membership,
biography, same-year identity and the pinned scheduler index/raw cap. Payroll and
contract export still require independent reconciliation; context is no proof of
complete modern obligations or active-franchise selection.

Existing version1 registries remain readable for durable recovery. Convert a copy
without rerolling any player identity, personality or contract schedule:

```sh
python3 -m tools.franchise_snapshot_bindings /path/to/SAVEGAME.DAT /path/to/existing-bindings.json --migrate-context /path/to/new-context-bindings.json
```

Both creation and conversion refuse an existing output. Historical named profiles
are decoded only for old-registry compatibility; new creation never emits them.
Conversion preserves their previously recorded calendar/units as explicit data.
Do not replace a live registry automatically: existing stores and recovery journals
may bind its original bytes/hash and need their own verified migration.

A copy conversion of MyNFL1 preserves2070 player identities/personalities and1693
active schedules across32 teams. The legacy exporter retains raw fitted terms and
source, applying the validated unit factor after guest rounding. The read-only
signing checkpoint compares live raw values to the save, then scaled obligations
and cap to the ledger. Neither context nor a matching checkpoint authorizes AI,
guest writes, cash assumptions or omitted non-roster liabilities. Calendar advance,
complete opening books and live service binding remain separate acceptance gates.


A separate source reconciliation command compares that registry to the pinned
authoring audit without creating a DB or changing a save:

```sh
python3 -m tools.reconcile_pack_contract_source /path/to/SAVEGAME.DAT /path/to/bindings.json /path/to/contract_audit.json
```

Its adjustment proposals carry exact year-by-year differences plus pinned source
provenance. They can be represented by existing OpeningBooks adjustment records
beside the preserved legacy deals. The report always marks complete_opening_books
false: this source audit omits a complete non-roster inventory, and estimates,
transfers, changed terms and ambiguous names require resolution. A matching raw
guest checkpoint cannot authorize writes against corrected external balances
until the guest and ledger enforce the same complete obligations.


New captured offers use the validated liability unit factor to select the existing
wire encoding original_fxg_v1 (1:1) or softdrink_fxg_v1 (4:1). These historical
encoding names do not select policy by mod identity. The raw amount/flags stay unchanged. Python and the native
response validator scale annual salary and nominal bonus after guest rounding,
then require exact modern allocation and exact reverse encoding. Proposal
contexts state the actual display-dollar salary unit (4000 for SOFTDRINK);
counteroffers and stored dialogue retain that format on replay. Format changes,
nonrepresentable salaries/guarantees and inexact bonus allocation reject. This
requires a matching service/native validator build; the old installed pair was
not replaced. These are proposal-only paths, without guest commit authorization.
