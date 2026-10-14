# Contract generations: next franchise lifecycle prerequisite

General signing and incoming assignment retain their former-club guards. An
explicit supported same-year veteran return operation now creates a separate
agreement while preserving old debt. General AI negotiation, incoming return
trades and multi-season delivery still require further integration.

Player identity and exclusive ownership remain stable. Contract identity identifies
one team-book agreement, its effective terms, cash obligation, and closed status.
The active player mapping points to one agreement; older agreements and retained
charges remain payable and inspectable. Personality and lifetime stories belong to
the player, not a contract. Trades must link outgoing and incoming book agreements.

## Ordered implementation

1. Introduce immutable generation identifiers and active-player mapping. Derive a
   deterministic legacy generation for each existing team/player; preserve old
   `contract:player` payment IDs and historical signing receipts permanently.
2. Add a backed-up, reconciled format migration. Existing format3 postings must
   replay with their original serialization view. New versioned events contain
   full generational postings; adding metadata must not invalidate old receipts.
3. Validate payments against their own generation and lifecycle settlement,
   including old unpaid cash after a new agreement. Archive maps use generation
   identity rather than overwriting player keys. Aggregate all retained debt.
4. Enable sourced veteran return signing atomically: add new cap charges, create
   new cash obligations, and acquire exclusive ownership. Do not infer offsets,
   cancel old guarantees, reuse old request IDs, or broaden rookie rules silently.
5. Scope terminal negotiation state to current ownership/generation, retaining
   all lifetime stories and immutable receipts. Current ownership now determines
   free-agent availability; the financial generation guards remain in force.
6. Expose current and historical agreement accounting distinctly for inspection
   and payments. Then implement supported extensions and dated year progression.

Extensions also need frozen original bonus allocation: Offer.charges currently
uses min(term,bonus_years). Extending a short original term without freezing its
allocation would spread old bonus into new years. Rollover needs sourced calendar
anchors for every active and retained schedule; none may be guessed from array
indices alone.

Acceptance includes release/return/second release, trade-away/return, payment of
old obligations after new signing, old receipt retry after a new agreement,
competing clubs, migration rollback, and conservation of all original bonus,
guarantee, cash and retained-charge histories. These are implementation requirements,
not claims of completed game integration or a decoded guest contract format.

## Read-only legacy inventory foundation

FranchiseStore.contract_generations(team_id), also available through authenticated
GET /api/contracts for the configured team, reads one freshly validated snapshot.
The format1 response identifies legacy generations with `legacy-contract:` plus
SHA-256 of compact UTF-8 JSON `[team_id,player_id]` (ensure_ascii=false). Mutable
terms, payments and lifecycle status never enter this identity. Format3 permits only one
book agreement per team/player; explicit format4 returns can add further records.

The view includes effective typed contracts, known cash or null, and retained
records from supported release/assignment archives. Unassigned opening debt and
credits, prior cohort contracts, unsigned tenders and unmatched cash obligations
remain explicit separate records. Unknown cash coverage stays null; known empty
unmatched cash is an empty list. No relationship or generation is guessed from
record names.

This inventory does not rewrite events, change database format3, enable new
agreements, or replace the full original configuration/history needed for migration.
Backups and exact old/new replay reconciliation remain required before format
advancement. Actual guest contract identification remains unverified.

## Backup and reconciliation preflight

Run `python3 -m tools.prepare_generation_migration /path/to/franchise.sqlite`
against an existing format3 database. The command holds a write reservation,
creates an exclusive sibling SQLite backup with private file permissions, hashes
its completed contents, and replays every team from the same reserved snapshot.
It also checks database integrity, foreign keys, global creation metadata and
all draft orders, including orders without picks. The JSON report contains the
backup path/hash and each team's financial, cash and legacy agreement inventory.

Validation failure retains the completed backup and reports its path. A failed
backup copy removes only its own partial file. Missing databases are not created.
The source format, configuration, events and ownership are unchanged. This is
preparation only: it does not migrate to a new format or enable return signings.
Keep the report and backup private; they contain franchise history.

The native `player_context` response now includes this same `generation_id` in
non-null contract accounting. It remains stable across amendments, payments and
release; seller and buyer book identities differ. The C++ decoder accepts legacy
responses without the field and validates the canonical legacy identity shape
when present. This exposes agreement identity for in-game inspection without
requiring a browser. It does not enable multiple agreements or guest writes.

## Consumed accounting identity foundation

The ledger binds its team identity during durable replay, then tracks immutable
agreement/player/cash identities and the current active mapping. Closing an
agreement removes its active mapping without discarding its historical identity.
The cash resolver is used by accounting, lifecycle calculations, payment checks
and inspection. Standalone first-agreement ledgers retain the legacy cash IDs.
Existing serialized financial postings and receipts do not gain identity fields.

Release, assignment and restructure calculators accept an explicitly expected
cash ID; omission means the original `contract:player` identity. They still check
player identity, compensation totals and allocated payments. Assignment can
identify the receiving book's cash obligation separately. Cash creation refuses
ID collisions without replacing an earlier obligation. The explicit return operation now supplies versioned records and archived
lookup for a second agreement. General signing and incoming-trade guards remain.

## Agreement archives and native inspection

Bound ledgers retain typed immutable agreement versions keyed by generation ID:
the birth contract, effective contract and supported lifecycle plans. Amendments
and closure replace the current archive version while preserving birth terms;
cash settlement remains a live record under the agreement's own cash ID. Payment
validation iterates these records and applies each agreement's lifecycle ceilings.
Player context and the migration inventory use the same archive. Original
format3 financial snapshots and event serialization remain unchanged.

The native pipe supports `contract_context` with team_id, generation_id and
timeout_ms, returning the exact agreement's accounting and current financial
revision. It requires no model call or AI access. Unknown or foreign-team
agreements reject, disconnect/deadline checks apply, and oversized responses
return a bounded error. This is an inspection boundary for future in-game
screens; it is not a completed game screen or guest hook.

The legacy financial posting view remains for historical replay. Archives are
rebuilt from source history; format4 persists their migration checkpoint.
Explicit return records below support later agreements. General signing,
returned-player assignment and amendment still require further integration.

## Explicit format4 migration

`python3 -m tools.prepare_generation_migration /path/to/franchise.sqlite --migrate`
commits the backed-up format3→4 migration. Default invocation remains preflight
only. Both modes reserve the source snapshot through backup and reconciliation.
Migration records one checkpoint containing the old event boundary, source row
identities/hash and every team's financial, cash, birth/effective agreement and
retained-charge state. Existing config and event JSON stays byte-for-byte intact.

Every format4 connection validates the checkpoint before reads or writes, including
bootstrap writes and constructors. Historical prefix/config changes, duplicate
manifest keys and accounting type swaps reject. Subsequent valid events and new
teams are allowed; their current state still passes normal replay checks. Failed
installation rolls back to format3 and retains its backup. The returned report
provides the private backup path and SHA-256. Repeating migration rejects without
creating another backup. Keep the backup and report together for recovery.

Format4 preserves the legacy posting view for historical events. Explicit return,
release and payment records now validate generational postings and superseded
agreements. AI/native entry points and real guest saves remain unverified.

## Supported durable return agreements

`FranchiseStore.return_sign(team_id, request_id, offer, expected_revision,
scope=PreseasonReturnScope(...), access_check=...)` supports explicitly sourced
healthy same-year preseason veteran return agreements after format4 migration.
See [preseason-return.md](preseason-return.md) for scope and remaining boundaries.
Versioned return/release/payment records validate full generational postings.
Old agreements remain accessible by their own identity after a later return.
Normal signing and AI negotiation do not select this operation automatically.
