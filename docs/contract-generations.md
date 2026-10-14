# Contract generations: next franchise lifecycle prerequisite

Current engine guards prohibit a former club from signing or receiving an assigned
player again. These guards protect old debt; deleting them would overwrite the
one-player contract/archive and collide with `contract:player` cash history.
Actual multi-season franchise delivery requires separate contract identities.

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
