# Work progress

## October 13, 2026 — Baseline and ongoing work configured

Fork: `cosmokay1/2K5Remade`, branch `codex/franchise-negotiation`.
Latest implementation commit: `7c49a18`.

Completed: structured negotiation boundary, Google Cloud adapter/live smoke,
mandatory remote AI control, money audit, and four initial audit repairs.
Validation: 46 portable tests pass; offline cap and story examples pass.
F01/F02/F03/F07 addressed at the prototype boundary. F04/F05/F06/F08 remain open.
Live smoke accepted a counter but rejected its over-cap commit; details in
`live-google-test.md`. Real disabled/enabled control reads were verified.

No actual game binary/save is available, and no Windows game execution occurred.
No claim of integrated gameplay or full modern NFL financial compliance is made.
Upstream redistribution permission remains unresolved; maintainer draft unsent.

Created hourly continuation `build-nfl-2k5-franchise-ai` in this chat. Local runs
depend on the machine/app and workspace being available and their permissions.

Next unblocked work: M0 portable CI, then M1 authoritative contract accounting,
precision consistency, durability, ownership and tender replacement. Prefer
small validated changes with evidence over expanding the roadmap.

User clarified that hidden skill ratings break immersion. Franchise decisions
must use observable stats/performance, opportunities/context and uncertainty.
Added this to the delivery target, M3 acceptance, and model instructions; added
a guardrail rejecting recognizable hidden rating fields, including nested fields.
This is not yet the completed observation/scouting model.

Record each continuation's completed items, commit, validation, and remaining
gates here. Keep historical observations labeled with their actual revision.

## October 13, 2026 — Portable CI prepared; publication blocked

Prepared Linux/Windows engine CI in commit `bd1f801`, preserved on local branch
`codex/ci-workflow-setup`. It runs the portable suite, money-audit regression
checks and both offline examples without game assets, credentials or paid calls.
48 local tests pass; no remote CI run exists.

GitHub rejected the workflow push because the active OAuth credential lacks
`workflow` scope. Existing SSH authentication was checked using host keys from
GitHub's official metadata and failed with publickey denial. No global SSH
settings or authentication permissions were changed. The development branch was
returned to its previously pushed head; the unpublished CI commit remains on
its named local branch, so subsequent source pushes are unblocked.

User authentication step: `gh auth refresh -h github.com -s workflow`.
After authorization, cherry-pick `bd1f801`, resolve the progress-log addition if
needed, push, and verify real workflow results before checking the M0 item.
While B05 remains, continue M1 work rather than retrying the same failed push.

## October 13, 2026 — Portable CI

Added `Franchise AI checks` on Linux and Windows/Python 3.12. It runs the unit
suite, audited money regression/conservation checks, and both offline examples.
It needs no game assets, cloud credentials, SDK installation or paid inference.
This is engine validation only; native bridge compilation and actual Windows
game execution are still separate worklist gates.

Local validation: 48 tests and both offline examples pass. Remote CI result must
be recorded after the workflow actually executes; a pushed workflow is not a
green CI result.

The user completed workflow authorization. Applied the preserved workflow; remote validation is pending.

## October 13, 2026 — Portable CI verified

B05 is resolved. Workflow published in `589a2bd`. GitHub run
[38457090392](https://github.com/cosmokay1/2K5Remade/actions/runs/38457090392)
completed successfully: Linux in 19 seconds, Windows in 32 seconds. Both ran
the 48-test suite, money regression/conservation checks, and offline examples.
Marked the portable CI worklist item complete. This verifies portable engine
behavior, not native game build or gameplay. Continue M1 accounting work;
asset-free native bridge checks can be added when a bridge implementation exists.

## October 13, 2026 — Durable supported transactions

Added `FranchiseStore` (SQLite) and `StoredLedger`. Persistent initial rules and
supported signing/budget events reconstruct cap, rookie allocations, membership,
revisions and request receipts. Player ownership is unique across teams using
one database. Financial signing and optional story commit atomically. The
negotiation path uses the adapter and recalls a committed agreement after restart
without calling the model again. Basic in-memory Ledger behavior remains available.

Validation includes independent competing connections, separate Python-process
reload, injected event-write failure, abrupt subprocess exit before commit,
conflicting retries/stories, disabled new commits with readable old state, and
unsupported database versions. Added offline persistent demo to Linux/Windows CI.
Local suite: 60 tests. Remote result is pending until the new commit executes.

This addresses F05 and F06 for supported operations through the shared store,
not every game/standalone path. Aggregate bootstrap balances, F04 precision and
F08 tender replacement remain open. Active negotiations/relationship changes,
full contract lifecycle and actual game-save synchronization remain incomplete.

First CI run `38458788876`: Linux passed; Windows failed during cleanup of two
test-owned SQLite connections. The store's connection lifecycle was not the
failure. Fixed explicit test connection closure; a new remote run must verify
the correction before claiming Windows persistence checks pass.

Verified corrected commit `98c4555` in
[CI run 38458986651](https://github.com/cosmokay1/2K5Remade/actions/runs/38458986651):
Linux and Windows both passed all 60 tests, money checks and offline examples,
including durable negotiation replay and abrupt-process recovery. Next: recorded
financial posting/reconciliation, precision consistency and tender replacement.

## October 13, 2026 — Exact allocations, tender replacement, posting reconciliation

Unified cap and rookie bonus allocation on exact rational dollars (F04).
Offers remain integer-dollar terms; JSON uses canonical integer or rational-string
amounts, never binary floating-point money. Added declared rookie-tender replacement
(F08), including over-cap rejection and restart/idempotent replay tests. Tender
extraction from the game remains unverified; bootstrap association must be explicit.

Format-2 store events record committed contract charges and resulting financial
state. Replay checks the recorded result and ownership; mismatches stop load/writes.
Format-1 databases are retained but rejected until explicitly migrated, because
they did not record posting evidence. No user database is deleted or overwritten.

Local validation: 70 tests, money audit checks and all three offline demos pass.
New tests include fractional cap boundaries, equal cap/pool charges, altered
postings/charges, lost ownership, old-format preservation, and tender replacement.
Remote results must be recorded after the new code executes.

Verified `5628e06` in
[CI run 38460444346](https://github.com/cosmokay1/2K5Remade/actions/runs/38460444346):
Linux and Windows passed all 70 tests, money checks and offline demos.

The user explicitly requested uninterrupted continued work. Set an active
delivery goal for the actual integrated Windows game; it remains incomplete.
Continue automatically through unblocked work rather than waiting for another
user message. The hourly follow-up also remains available. Game assets/saves,
Windows runtime access and redistribution permission are still external gates.

## October 13, 2026 — Derived opening obligations and verified migration

Added `OpeningBooks`, active original contracts with elapsed years, explicit
retained charges/adjustments with provenance, and unsigned rookie tenders. Balances
derive from records; old bonuses are sliced from their original allocation instead
of being restarted. New durable teams reject opaque aggregate-only totals. Reload
reconciles source records against the recorded opening balance and ownership.
Already-signed rookies can exist in a starting roster but cannot retain an unsigned
tender. Real imported values are still unavailable/unverified.

Format 3 requires source books. The explicit format-2 migration backs up committed
state, requires every team's source books, and verifies all financial results before
committing. Failed migrations preserve version and balances. Format 1 remains
unsupported because posting evidence is absent. No automatic guessed migration.

Local suite: 80 tests, plus the durable offline demo. Tests cover elapsed bonus
years, fractional original terms, duplicate obligations, signed-rookie ownership,
source/aggregate mismatches, verified migration backup and rollback. Remote CI
results remain pending until the implementation commit executes.
