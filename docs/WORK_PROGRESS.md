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

Verified `05c0176` in
[CI run 38461479152](https://github.com/cosmokay1/2K5Remade/actions/runs/38461479152):
Linux and Windows passed all 80 tests, money checks and offline demos, including
source-book migration backup and rollback. Next work moves to verified annual
rules and the remaining contract lifecycle; the integrated-game goal stays active.

## October 13, 2026 — Published annual minimum table component

Read the executed NFL/NFLPA CBA Article 26, PDF page 187 (printed page 171), and
added its active/inactive and non-active/inactive salary-floor tables for 2020-2030.
Source and rule version are recorded in `franchise/minimums.py`. Lookup rejects
unknown years/categories, and projected schedules use explicit annual credited
season inputs rather than assuming experience automatically creates credit.

Local suite: 84 tests. This component does not yet establish a complete annual
rules profile, real player credited-season data, practice-squad treatment, future
CBA policy, or draft allotments. No real franchise calendar/economic conversion
has been chosen silently. Remote CI is pending for this addition.

Verified the annual lookup plus migration resource fix at `31c3562` in
[CI run 38462390974](https://github.com/cosmokay1/2K5Remade/actions/runs/38462390974):
Linux and Windows passed 85 tests, money checks and all offline examples.
The backup-open failure test confirms the source handle closes and the original
database version is preserved. Next: bind explicit annual rule/credited-season
profiles to durable state, then implement cash, guarantees and lifecycle operations.

## October 13, 2026 — Shared offer preview and signing validation

Added read-only offer previews for the in-memory and durable negotiation adapters.
Preview and signing share one validator for annual floors, cap room, bonus charges,
rookie limits, classification and revisions. Durable previews additionally check
league ownership inside the same read transaction as reconstructed finances.
Previews report exact resulting annual charges, room, tender replacement and rookie
pools, plus total contract cash (not a payment schedule or guarantee). They do not
reserve money; final signing still rechecks revision and global ownership.

Local validation: 88 tests pass, including competing-team ownership after preview,
nonmutation, stale previews, matching preview/commit charges and tender replacement.
Game UI integration remains unverified and externally gated.
Verified offer-preview commit `aad45ca` on Windows/Linux in
[run 38463144916](https://github.com/cosmokay1/2K5Remade/actions/runs/38463144916).

## October 13, 2026 — Durable source-bound veteran minimum profiles

Added immutable `VeteranMinimumProfile` records with a modern start year, explicit
annual credited-season/category inputs and exact published source/version. Ledger
creation and every durable reload reconcile supplied veteran floors against the
profile; mismatch rejects reconstruction. Negotiation context records the rule
source/year without exposing other players' inputs. The durable example now uses
a 2026 profile and survives restart. Existing synthetic/legacy explicit-floor
fixtures remain supported; they do not become verified annual rules automatically.

91 local tests pass. Coverage includes annual floors after reload, no automatic
credited-season advancement, floor/profile disagreement and rejection of unknown
years, versions, duplicate IDs and unsupported categories. Draft allotments, cap
profiles, historical economics and season rollover remain incomplete; this is
explicitly a salary-floor component, not a complete league ruleset.
Verified `91f140a` on Windows/Linux in
[run 38463370559](https://github.com/cosmokay1/2K5Remade/actions/runs/38463370559).

## October 13, 2026 — Provenance and missing-counter negotiation context

Added immutable `Observation`/`PerformanceEvidence` inputs: stable player, window,
played/CPU-played/fast-sim mode, coverage, source and explicit unavailable reason.
Null/missing counters stay unavailable, while an observed zero stays zero. Reject
duplicate counters, mismatched identity and receptions/completions exceeding known
opportunities. Negotiation accepts these records and the durable offline example
uses them. Shared model instructions now preserve coverage/mode uncertainty.

Closed a rating-context loophole: recognizable hidden rating fields in personality
or relationships are rejected as well as performance. This does not establish
trusted game instrumentation; sources/coverage must still be verified by import.
Legacy raw-dict fixtures remain supported. No real targets or pressures have been
claimed, inferred from outcomes, or fabricated from ratings.

Local validation: 94 tests pass, including provider-visible null provenance,
observed zero, inconsistent opportunities, actor-field ratings and player identity.
Actual game statistics and event attribution remain M5/M3 work. CI pending.

## October 13, 2026 — Durable counteroffers and rejections

Noncommitted negotiation events now persist alongside verified financial postings.
Restart restores a player's team-specific conversation history, including counters,
rejections and failed accounting acceptances. Request retries recall the recorded
response without inference; changed terms and signing/dialogue request-ID collisions
reject. Signed agreements retain their existing atomic contract/story transaction.
The write boundary checks AI access before recording dialogue. Replay validates
that dialogue did not mutate the recorded financial state.

Local validation: 96 tests pass. New cases exercise restarted counter/rejection
history, inference suppression, conflicting retries, shutdown at write and SQL
rollback. Actor personality updates, deadlines and multi-conversation lifecycle
remain incomplete. No game integration is claimed. Remote CI pending.

Verified prior performance-context commit `ea400fb` on Windows/Linux in
[run 38463545574](https://github.com/cosmokay1/2K5Remade/actions/runs/38463545574).

## October 13, 2026 — Persistent player priorities and team relationships

Durable sessions register initial actor context under the database write lock.
The player's original personality follows them across clubs; initial relationships
remain team-specific. Restart reuses recorded priorities instead of replacing them
with new caller defaults. Current observed performance can still refresh. Actor
registration records unchanged financial postings and checks remote access at its
write boundary. Reload validates actor shape and rejects hidden rating fields.

Local validation: 98 tests pass, including refreshed production with stable
priorities, cross-team identity/relationship separation and disabled registration
without state mutation. Bounded personality/relationship updates, agent/GM models
and season campaigns remain unimplemented. Existing source fixtures remain the
inputs; no actual-game extraction or playable-build evidence is claimed. CI pending.

Verified preceding dialogue persistence `80847b8` on Windows/Linux in
[run 38463714527](https://github.com/cosmokay1/2K5Remade/actions/runs/38463714527).

## October 13, 2026 — Reject obsolete model conversation responses

Model-backed responses record the prior conversation request IDs. Signing and
dialogue writes verify that sequence inside the same database write transaction.
Another session's counter/rejection invalidates an in-flight response even when
financial revision is unchanged. Active sessions refresh durable history before
new inference. No obsolete acceptance commits a contract or an obsolete dialogue.
Historical/manual events without the new context field remain replayable.

100 local tests pass, including interleaved acceptance/counter responses with a
concurrent rejection and a subsequent fresh request seeing the current history.
The prior actor-persistence commit `5573e4a` passed Windows/Linux in
[run 38463887477](https://github.com/cosmokay1/2K5Remade/actions/runs/38463887477).
This closes a prerequisite for asynchronous bridge work; game responsiveness and
actual native integration remain unimplemented/unverified. New CI pending.

## October 13, 2026 — Versioned bridge request boundary

Added protocol-1 hello/preview/negotiate handler over the durable store. Strict
fields, request IDs, integer client financial revisions and 1-60000ms deadlines
are validated. Negotiation rechecks the client's revision after session setup,
and deadline/remote access checks run through inference and final transaction
guards. Durable retries reuse committed responses despite advanced revision.
AI-off previews still enforce cap rules. Provider failures return a generic error
without credentials/stack details. No game or save mutation interface is exposed.

104 local tests pass: wire sign/retry, stale client revision, protocol mismatch,
expired request, disabled-AI preview and provider error redaction. This is the
request handler only: process transport, native client and asynchronous game-thread
integration remain required. No native/game acceptance claim. CI pending.

Verified prior conversation-consistency commit `db4fa98` on Windows/Linux in
[run 38464014062](https://github.com/cosmokay1/2K5Remade/actions/runs/38464014062).

## October 13, 2026 — Bounded process sidecar transport

Added stdin/stdout JSON-lines sidecar over the durable bridge. One inference worker,
no queued inference, explicit busy response, frame-size limits and disconnect
guards. Preview dispatch stays independent of inference. Live Vertex mode requires
ADC and remote control; offline fixture mode is explicit and makes no cloud calls.
Only existing databases may start; the transport cannot invent opening finances.

106 local tests pass. New tests launch a real sidecar subprocess twice to verify
handshake/dialogue/restart recall, and interrupt an in-flight acceptance after
busy rejection to prove disconnect preserves finances/history. Native pipe client,
Windows process execution evidence and real game integration remain required.
No paid inference or game assets used. CI pending for this implementation.

Verified preceding request-handler commit `3d1a095` on Windows/Linux in
[run 38464213438](https://github.com/cosmokay1/2K5Remade/actions/runs/38464213438).

## October 13, 2026 — Native Windows pipe client candidate

Added standalone asset-free C++17 Windows pipe client: explicit Python launch,
Windows argument quoting, isolated stdin/stdout pipes, one asynchronous request
with nonblocking ready/take polling, bounded frame/response sizes and timeout.
Transport failures close the process to prevent reuse with an old response.
This candidate launches only the offline rejection fixture. It does not parse
financial responses into game fields, carry production authentication or hook
guest memory. Startup/destruction are not yet intended for the game thread.

CI now compiles this client and executes it twice against a synthetic database,
verifying handshake, exact preview, durable dialogue and restart with spaced paths.
Windows compile/execution results are pending; local macOS cannot execute Win32.
All 106 portable tests still pass. Do not mark M0/native checks complete until
actual Windows execution succeeds.

Preceding sidecar `e0c7ba9` passed Windows/Linux (including real subprocess tests) in
[run 38464385703](https://github.com/cosmokay1/2K5Remade/actions/runs/38464385703).

## October 13, 2026 — Native execution failure and CRLF repair

Run 38464574968 compiled the C++ client on Windows and passed 106 portable tests,
but native execution failed while parsing output. Windows text-mode sidecar output
is CRLF; the raw client retained CR and then C++ text output added another CRLF,
producing empty splitlines in the verifier. Corrected the wire reader to consume
CRLF framing. Kept strict JSON verification rather than filtering empty output.
Extended the native fixture to require failure on missing database and nonexistent
Python executable, without changing the successful financial state.

The native milestone remains unverified until the repaired code executes on
Windows. This is a concrete failed runtime check, not a playable-game result.

## October 13, 2026 — Financially enforced explicit manual path

Bridge `manual_sign` requires explicit manual decision mode and commits via the
same durable financial gate, labeled as manual in persistent story history. It
works while remote AI is disabled without provider calls. Local deadline and
connection checks remain mandatory at the write boundary; AI errors never fall
through to this operation. Game UI selection and native cap-path replacement
remain unverified/pending.

108 local tests pass, including AI-off manual signing, over-cap rejection,
idempotent retry, missing explicit mode and disconnected-client rejection.
Repaired native Windows CI remains pending at this entry.

## October 13, 2026 — Source-checked termination bonus component

Read executed CBA Article 13 section 6(b)(ii), PDF page 126 (printed 110). Added
exact signing-bonus acceleration from original terms and elapsed proration.
Actual removal on/before June 1 places remaining bonus in current charges; actual
removal after June 1 retains current proration and accelerates future proration
into next-year charges, except final CBA year 2030. Source/version recorded.

112 local tests pass, including June-1/June-2 boundary, elapsed bonus conservation,
fractional allocations, exhausted five-year proration and final-year exception.
Dates requiring a following-calendar-year league mapping are rejected. Early
post-June-1 designations are not supported. This component does NOT authorize
release: base guarantees, earned salary, injury/termination protections and
roster replacement costs remain required before a full transaction exists.
No game fields were changed or guessed. Remote verification remains pending.

## October 13, 2026 — Verified native Windows transport; transaction fixture expansion

Repaired native client `dd1ed9e` passed actual Windows compilation/execution in
[run 38464795249](https://github.com/cosmokay1/2K5Remade/actions/runs/38464795249).
Verified handshake, exact preview, durable rejection/restart and failure exits for
missing database/nonexistent Python. Marked M0's asset-free native checks complete.
This proves a transport fixture only, not game build/playability or guest hooks.

Expanded the C++ requests and verifier to require an over-cap manual rejection,
legal manual signing, and identical agreement recall from a second native process.
The final database must have exactly one signing revision, ten dollars in charges
and the earlier rejection plus manual story. New Windows evidence pending; local
112 portable tests remain passing. Original build/rights/real-save gates persist.

## October 13, 2026 — Native parent/sidecar lifetime ownership

Native client now creates its sidecar in a noninherited Windows job with
KILL_ON_JOB_CLOSE, assigned atomically through PROC_THREAD_ATTRIBUTE_JOB_LIST.
This avoids starting inference before ownership assignment. Configuration failure
rejects launch; normal cleanup retains existing graceful pipe close before kill.
Requires Windows 10/Server 2016 or later, matching the current Windows CI target.
Primary API references: Microsoft Job Objects and UpdateProcThreadAttribute docs.

Expanded Windows fixture deliberately calls ExitProcess without C++ destructors.
The verifier opens the sidecar process handle before signaling parent exit, then
requires termination within five seconds, avoiding PID-reuse ambiguity. Actual
Windows compilation/execution of this addition is pending. 112 local portable
tests still pass; no cloud calls/game assets used.

## October 13, 2026 — Verified native transaction and recorded negotiation evidence

Native transaction fixture `d2d9e0b` passed on Windows in
[run 38465198052](https://github.com/cosmokay1/2K5Remade/actions/runs/38465198052):
over-cap rejection, legal manual signing and identical restart agreement recall.
The preceding manual path and bonus accounting also passed Windows/Linux at
`36c293b` (38464922375) and `eb38b90` (38465069203). M4 protocol design is complete;
production roles, actual game-thread behavior and game reconciliation are not.

Model-backed dialogue/contracts now record frozen actor/performance evidence and
the financial revision observed for that response. Persisted histories preserve
unavailable counters and provenance instead of only the model's reason. Reload
validates evidence shape and hidden-rating exclusion. Old/manual records have no
retroactively fabricated evidence. Actor context must be an object before inference.

113 local tests pass; new coverage checks caller mutation cannot change saved
evidence, restart retention and rejection of hidden rating fields in stored story
evidence. Native job lifetime and new evidence CI remain pending. No game
instrumentation, authenticity guarantee or playable build is claimed.

## October 13, 2026 — Keyless runtime identity and direct IAM separation

Created `franchise-runtime` in authorized project llm-2k5 with no user-managed
keys. Custom project inference role contains only endpoints.predict/services.use.
Custom bucket read role contains only objects.get, condition-restricted to the
control object. Read-only `tools.audit_runtime_iam` verified exact direct grants
and zero user keys without printing tokens or making model requests. Switch state
was not renewed/re-enabled; no ongoing service infrastructure was provisioned.

Authentication/federation/impersonation remains unimplemented; the sidecar's ADC
is not automatically switched to this identity. Inherited folder/organization
policy was not evaluated. M4 client/admin deployment separation remains incomplete
until runtime access is exercised. See docs/runtime-iam.md for exact scope.

Native job lifetime `fa21c87` passed Windows/Linux in run 38465395201, including
the abrupt-parent-exit process-handle assertion. Model-evidence CI is still pending.

## October 13, 2026 — Reassessed actual durable money path

Updated executable money audit to distinguish original in-memory F05/F06
reproductions from the supported durable bridge path. Durable audit now proves
restart receipt/story identity, unchanged retry revision and rejected competing
team ownership with no financial mutation. Captured current evidence and published
a scope table covering remaining cash/guarantee/lifecycle obligations. No complete
NFL/game accounting claim is made. Local 113 tests and money audit pass.

Model-evidence commit `bc69785` passed Windows/Linux plus native fixture in
[run 38465570806](https://github.com/cosmokay1/2K5Remade/actions/runs/38465570806).
Next financial dependency remains explicit cash/guarantee records before full
release/trade/season operations. Actual-game gates remain unchanged.

## October 13, 2026 — Separate durable nominal cash and payment ledger

Added source-required cash obligations, explicit paid amounts and unavailable
state for franchises without verified opening payment history. Opening records
reconcile every original active contract's nominal base-plus-bonus total; prior
paid amounts are not inferred from elapsed cap years. Additional retained cash
can be declared explicitly. Subsequent signings add nominal obligations in the
same contract/story transaction. Payments have cash revisions, receipt identities
and overpayment/conflicting retry checks.

Cash initialization/payments advance franchise revision to invalidate old offers,
but leave cap charges unchanged. Replay checks cash and financial postings, and
SQL failure rolls both back. Negotiation sees source-bound cash totals only when
available. 116 local tests pass: unknown history, missing opening contracts,
restart receipts, nominal/cap separation, stale/overpayment rejection, rollback
and corrupt-posting failure. Guarantees, payment calendars, owner budgets, offsets
and complete release/trade/year lifecycle remain incomplete. CI pending.

## October 13, 2026 — External payment evidence deduplication

Cash payments now require source-scoped external receipt/reference identity in
addition to request ID. The same evidence cannot be credited under a different
request, even with fresh cash revision; conflicting original-request references
reject. Replay rejects duplicate or invalid recorded references and missing source.
Historical events without references remain readable; retry requires audited
migration rather than fabricated receipt identity.

118 local tests pass, including duplicate receipt under a new request, conflicting
retry reference, restart state preservation and tampered duplicate-history failure.
This verifies receipt uniqueness, not authenticity of external payment evidence.
Guarantee/payment scheduling and full contract lifecycle remain pending.

## October 13, 2026 — Negotiated full base-salary guarantee terms

Offers optionally contain annual guaranteed base amounts, protected at signing
for skill/injury/cap termination. Amounts cannot exceed annual base salary; they
do not add compensation or change cap allocation. Structured provider schemas and
prompt now support counter guarantees; accept/reject cannot alter them. Central
contract parsing/serialization preserves terms through opening records, durable
signings, stories, bridge requests and reload. Old synthetic three-field terms
remain readable without retroactively inventing guarantees.

120 local tests pass, including security-driven scripted counter/acceptance,
provider-visible terms, restarted contracts/stories, invariant cap charges and
invalid/over-salary guarantees. This is contract-term persistence, not complete
guarantee settlement. Conditional/vesting/offset protections, paid-guarantee
allocation, release settlement and rookie option guarantee lifecycle remain
required. Original retail guarantee data is still unknown; not treated as verified
zero. Primary definition: NFL Football Operations contract-language glossary.
No paid inference/game assets used; new Windows/Linux CI pending.

## October 13, 2026 — Guarantee import/retry and native wire acceptance checks

New integration cases prove original annual guarantees survive elapsed-year
opening-book import and durable reload. A retry with identical salary/bonus but
reduced guarantees rejects, including through bridge requests, without changing
contract/revision. Expanded native Windows manual-sign fixture now sends and
verifies full base guarantee terms through wire, story, restart and contract readback.
New native execution remains pending. 122 local tests pass.

Verified preceding guarantee terms `ec05229` in
[run 38466915357](https://github.com/cosmokay1/2K5Remade/actions/runs/38466915357),
payment evidence `ed7a97a` in run 38466601230 and nominal cash ledger `72f9a15`
in run 38466351288. All passed Windows/Linux and native transport fixtures.
This evidence does not establish guarantee settlement, retail import or gameplay.

## October 13, 2026 — Bounded event-grounded relationship evolution

Added durable relationship updates for existing zero-to-one scores. Each change
is at most 0.1 (explicit simulation policy), requires an earlier recorded player
negotiation with the team, and applies once per source event/relationship. Request
retries preserve results; unknown sources, stale revisions and excessive changes
reject. Updates advance franchise revision without changing charges. Replay checks
chronology, duplicate consequences and the resulting actor state.

Live sessions refresh actor context; durable actor/accounting reads share a single
read transaction. Counters/rejections from obsolete financial/relationship context
reject at write. This prevents mixing old trust with a new accounting revision.
No model-generated story alone can authorize a trust update; the caller must
explicitly apply a bounded consequence backed by a recorded event.

124 local tests pass, including restart/live-session refresh, duplicate source
consequence rejection and concurrent update during inference. Player personality
evolution, agents/GM strategies and automatically defined consequence policies
remain pending. Native guarantee fixture `3d4eaf9` passed Windows/Linux in
[run 38467085483](https://github.com/cosmokay1/2K5Remade/actions/runs/38467085483).
New relationship implementation CI pending; no actual game integration claim.

## October 13, 2026 — Covered base-guarantee present-value liability component

Verified executed CBA Article 13 section 6(d)(iv), PDF page 138 (printed 122),
and Article 1 discount-rate definition, page 17. Future covered guaranteed base
liability is distinct from signing-bonus acceleration and nominal cash. Added
exact rational annual-compounding valuation with explicit league-year rate/source,
unpaid amounts bounded by original guarantees and explicit payment-year offsets.
No nominal cash amount is reduced by discounting; only the separate cap component
is valued. No rate or payment schedule is guessed.

127 local tests pass with independent synthetic five-percent examples, explicit
timing differences, original protected ceilings and unsupported-input rejection.
Rates in tests are declared synthetic; no published 2026 Treasury rate was fetched
or represented as verified. Whole annual periods only; partial-year conventions,
covered-release facts, paid allocation, offsets/voids and full settlement still
required. This component does not release a player or authorize game writes.
New Windows/Linux CI pending.

## October 13, 2026 — Component payment allocation and unpaid guarantee visibility

Cash obligations can carry exact paid allocations to signing_bonus/base:N using
original contract year indices. Imported allocations must sum to total paid and
stay within original component amounts. New post-change signings track zero paid
components explicitly; subsequent payments require their component. Unknown
historical allocations stay unavailable and cannot be retroactively filled by a
new payment. Legacy posting shapes remain replayable without invented allocations.

`ledger.guarantee_cash` exposes unpaid protected bases by original year and unpaid
signing bonus when allocation is known. Payments leave cap proration unchanged;
component overpayment rejects/rolls back. 129 local tests pass, including explicit
opening allocations, protected-base/bonus payments, restart, unchanged cap charges,
component overpayment and unknown history. This is owed/paid visibility, not
covered-release authorization, offsets/void settlement or dated vesting.
New Windows/Linux CI pending; actual game fields remain unmapped.

## October 13, 2026 — Explicit keyless runtime credential wiring

Added sidecar `--impersonate-runtime` for Vertex mode: authorized source ADC,
configured project-local runtime target, 900-second impersonated credentials.
Vertex and control readers receive separate credential objects; neither can mix
runtime credentials with owner gcloud-login fallback. No token/key is serialized
or printed. Control still fetches the switch on every check while reusing valid
authentication tokens (never reusing an enabled control grant).

133 local tests pass, including exact target/lifetime/source selection, failed ADC
redaction/no fallback, conflicting auth-mode rejection and SDK credential injection.
No live impersonation/model request, new impersonation grant or switch renewal
performed. Source ADC/IAM Credentials API/target permission and effective runtime
read/inference access remain unverified; M4 deployment separation stays incomplete.

## October 13, 2026 — Runtime credential/control failure-boundary checks

Control credential refresh requests now force a 15-second HTTP timeout. A refresh
that still leaves credentials expired denies before sending an old token. Valid
authentication tokens may be reused, but each handshake still retrieves the
remote object; disabled/unavailable state is never masked by a cached grant.

136 local tests pass. New cases use injected runtime credentials to prove fresh
switch reads across enabled→disabled→unavailable results, no owner ADC fallback,
forced refresh timeout, expired-refresh rejection and sensitive-error redaction.
These are offline credential-boundary tests, not effective live impersonation
verification. No cloud grants, switch writes or paid inference performed. CI pending.

## October 13, 2026 — Termination liability components from durable state

Ledger now retains original ActiveContract metadata through sign/replay, including
elapsed years and actual bonus horizon. Read-only `termination_components` joins
that contract with source-reconciled payment allocations and explicit discount
inputs. It reports retained bonus cap charges separately from nominal unpaid bonus
and covered base present value separately from nominal protected bases. Missing
allocations, unresolved prior-year protected bases and salary-profile/year mismatch
reject. No guesses from paid cash to cap proration or vice versa.

138 local tests pass, including an elapsed imported contract with a fully paid
bonus that still has retained cap proration, partial current base payment, exact
protected present value and unchanged financial/roster state. Result explicitly
sets release_authorized=false and lists unresolved covered-release/offset/void,
earned/termination/injury and roster-phase facts. This integrates the components
with authoritative records; a complete release transaction still remains.
New Windows/Linux CI pending; actual-game gates remain unchanged.

## October 13, 2026 — Source-checked offseason roster valuation component

Verified executed CBA Article 13 section 6(a)(i), PDF page 125 (printed 109).
Added supported base/prorated-bonus valuation for explicit offseason/regular-season
phases. Offseason excludes base only up to the applicable minimum for UDFAs or
twice that minimum for other players outside Top 51; all supplied bonus proration
remains counted. Rank uses full supported contract value. Material boundary ties
require an explicit verified selection rather than silently choosing a cheaper
classification. No phase date/minimum/UDFA status is inferred.

141 local tests pass, including threshold excesses, all bonus retention, bonus-heavy
rank entry and ambiguous boundary selection. This is a supported salary component,
not complete Team Salary. Tenders/Offer Sheets, deferred/other bonuses, roster
statuses, retained liabilities and verified calendar still require integration.
Existing signing ledger continues conservative all-contract accounting until the
complete phase transition path is implemented. New Windows/Linux CI pending.

## October 13, 2026 — Durable roster-phase projection and reconciliation

Connected roster valuation to original active contract/elapsed terms and declared
unsigned rookie tenders from durable state. Explicit current-year credited-season
and UDFA inputs cover every row; applicable minima derive from published table.
Retained liabilities/adjustments reconcile as the exact difference between current
authoritative charges and the gross active/tender rows, then remain counted in
each projected phase. Profile/year mismatch, missing classifications, unknown
phase and net-negative modeled liability reject. No signing authority or budget
is changed by projection.

143 local tests pass. A synthetic 52-contract fixture proves bonus/dead-charge
retention, offseason/regular-season difference and unchanged authoritative state.
Complete phase calendar, status/Offer Sheet/other compensation treatment and
atomic phase transitions remain required before projected room can authorize a
signing. New Windows/Linux CI pending; actual game inputs remain unavailable.

## October 13, 2026 — Native response envelope validation

Added C++ protocol decoder before the pipe client returns a response. It requires
exact envelope fields, integer protocol 1, matching nonempty request identity,
object success/null error or null result/nonempty error, and valid detail shape.
JSON parsing rejects duplicate fields, oversized frames and excessive nesting.
A malformed response closes the client rather than allowing a later request to
consume it. Operation-specific finance/game-field validation remains pending.

Uses nlohmann/json v3.12.0 release header pinned by published SHA-256; exact MIT
notice preserved and attribution updated. Build artifacts stay outside source.
Native protocol CMake/CTest now runs on both CI platforms; Windows additionally
runs the real process/transaction fixture. Locally compiled with AppleClang and
passed the C++ malformed-envelope suite; all 143 Python tests pass.
New Windows/Linux CI pending; no guest memory or game state writes introduced.

## October 13, 2026 — Native operation and contract-result validation

Native pipe responses now validate operation-specific handshake, preview revision,
submitted offer identity/terms, decision action/outcome and explicit manual mode.
Annual guarantees are normalized for missing/empty zero terms but cannot disappear
when positive. Integer money rejects floats/negative/out-of-range values; exact
charge fractions must be positive, reduced canonical numerator/denominator strings.
Signed/preview charge counts must match the offered annual term.

Compiled locally and passed C++ checks for changed guarantees, floating charges,
noncanonical rational values and mislabeled manual decisions. All 143 Python tests
remain passing. This validates wire types/identity, not independent cap calculation
or a guest-state commit. Actual game mapping, readback reconciliation and save
transactions remain required before writes. New Windows/Linux CI pending.

## October 13, 2026 — Counteroffer eligibility using shared financial validation

Player counteroffers now retain a current accounting preview or explicit
ineligibility reason. Demands remain attributed player decisions, never automatic
commitments. Preview uses the same revision, floors, cap/bonus, rookie and global
ownership gates as signing; it reserves no money. This gives future UI/team
strategy a concrete distinction between requested terms and currently eligible
terms. Final acceptance still rechecks current state.

144 local tests pass, including an unaffordable counter preserved as a demand
and an exact-cap eligible counter preview with unchanged charges/revision.
Native envelope/parser `2da51f2` passed Windows/Linux in
[run 38469551016](https://github.com/cosmokay1/2K5Remade/actions/runs/38469551016).
Operation-specific native and new counter-preview CI remain pending. Actual
franchise UI/game writes and complete financial lifecycle are still unfinished.

## October 13, 2026 — AI startup failure keeps financial enforcement available

Fixed recovery gap: failed Vertex/runtime initialization no longer terminates the
sidecar. AI requests deny explicitly; existing database-backed preview/manual
operations remain available. No scripted decision or owner-credential fallback
is selected after failure. Diagnostics are generic stderr text, never provider
secret/stack content.

Native PipeClient now requires an explicit service mode. Runtime mode launches
Vertex plus the configured keyless impersonation flag; the test executable stays
explicitly offline. 145 local tests pass, including injected startup failure,
AI-disabled response, deliberate cap-enforced manual signing and error redaction.
Live identity access/production credential permissions remain unverified.

Prior native result validation `f2674a4` passed Windows/Linux in
[run 38469873021](https://github.com/cosmokay1/2K5Remade/actions/runs/38469873021).
New native launch-mode build/execution CI pending. Real guest integration remains
unfinished; no game playability claim.

## October 13, 2026 — Verified impersonation source gate and safe denied-auth recovery

Actual `gcloud storage cat` under runtime impersonation failed with getAccessToken
permission denial before reading the switch. Automatic approval review rejected
a scoped Token Creator grant for the existing administrator as a persistent IAM
delegation; no grant applied. Requested explicit human approval, and will not
bypass it with owner fallback/keys/alternate identity. Live runtime read/inference
verification remains gated; independent finance/native work continues.

146 local tests pass. Added explicit runtime-denial startup case proving no owner
SDK initialization, AI-disabled response, over-cap manual rejection, legal manual
signing and secret redaction. Startup recovery `43f5181` passed Windows/Linux in
[run 38470323280](https://github.com/cosmokay1/2K5Remade/actions/runs/38470323280);
counter previews `2c21065` also passed run 38470077869. New test CI pending.

## October 13, 2026 — Rookie guarantee-chain correction from primary source

Executed CBA Article 7 section 3(h), PDF page 48 (printed 33), exposed a missing
condition in the drafted-rookie validator. Protected year-three/four base now
requires full preceding-year base protection in the supported base/traditional
bonus subset. Model instructions include this restriction. Preview and signing
share the check; illegal terms consume no cap or rookie pool.

148 local tests pass with partial/full prior-year protections and atomic rejected
preview/sign checks. UDFA three-year contracts and explicit shared/reserved pool
accounting remain next work; no claim that full rookie lifecycle is complete.
Prior denied-auth recovery `759bfac` passed Windows/Linux/native in
[run 38470751973](https://github.com/cosmokay1/2K5Remade/actions/runs/38470751973).
IAM delegation approval is still pending and has not been bypassed.

## October 13, 2026 — Undrafted rookie acquisition and shared reservation accounting

Verified CBA Article 7 definitions and three-year UDFA term. Added UndraftedScale
with annual floors, exact excess-over-minimum pool salary, 25% increase/guarantee
checks and explicit bonus reservation. Full salary/bonus remains in team cap.
Ledger/store support mixed rookie registries, shared pool deductions and persisted
reservation balance. Drafted offers preserve the unused reserved share; previews
use the same limits. Modern salary-profile/UDFA registries require a source-backed
reservation input; no annual published reservation is invented. Legacy unprofiled
drafted-only fixtures retain their supplied budget convention.

153 local tests pass, including mixed exact-cap signing/restart/retry, minimum-only
UDFA cap cost with zero pool cost, reserved-share protection, fractional bonus
conservation and atomic term/raise/bonus/guarantee rejections. Pool values are
synthetic fixtures, not verified real annual draft allotments. Initial imported
cohort/pool reconciliation, annual growth/rounding, incentive/non-base components,
options/escalators and full rookie lifecycle remain required.
Prior guarantee-chain `1b207fd` passed Windows/Linux in run 38471147416.
New acquisition implementation CI pending; game integration remains unfinished.

## October 13, 2026 — Imported rookie cohorts and Steam Deck scope

Added explicit source-backed RookiePoolOpening reconciliation for active and prior
current-cohort contracts, including UDFA reservations. New durable teams with
signed rookies require declared cohort history; previous cohorts are excluded
explicitly. All 159 tests pass locally, including package integrity/no-overwrite and invalid-path checks. Full release settlement remains
unsupported. Prior acquisition CI run 38471920428 passed.

Accepted draft evaluation and Steam Deck delivery into the worklist. Added a local
explicit-file streaming ZIP builder with hashes of archived bytes, no-overwrite behavior and Windows path checks, plus
Proton runtime and Deck acceptance requirements. No game binary or assets are
available to package; this is tooling, not a runnable game. Windows Python and
Win32 pipe/job behavior under Proton remain unverified.

## October 13, 2026 — Draft comparison input

Added read-only typed prospect comparison context with sourced competition, role,
personality, observation windows and contract estimates. Missing opportunity data
is retained as unknown; recognizable hidden rating fields reject across context.
Candidates require matching declared draft-round rookie classification and use the
existing shared cap/pool preview. Comparison detects stale financial revisions,
does not sign prospects or reserve funds, and does not imply all future picks fit.
Verified adapter slot assignment, AI selection, draft-wide pick/ownership and
reservation transactions, history, remote access enforcement at selection, and
real-game hooks remain unfinished. 163 local tests pass, including independent
cap/pool failures, unknown evidence, rating rejection and concurrent budget change.

Steam Deck/cohort source commit `a5c062c` passed Franchise AI checks on Windows
and Linux, including native protocol/pipe checks, in run 38473300500. Upstream
build check also passed in run 38473300526. These checks exercised no game assets
and establish no Proton or gameplay compatibility.

## October 13, 2026 — Cloudflare tunnel and HTTP origin

Used Cloudflare plugin to verify account/active zone and absent 2k5 hostname.
Dedicated llm-2k5 tunnel creation failed with Cloudflare authentication error
10000; no resources were created, and write-scope reconnection was requested.
Prepared loopback HTTP origin with bearer-authenticated existing-state inspection
and shared contract preview, bounded bodies/read timeouts and no financial writes
or inference routes. 164 tests pass, including actual loopback requests verifying
unauthorized rejection, exact preview, over-cap/stale rejection and no mutation.
Test required sandbox escalation solely to bind an ephemeral localhost port.
Browser UI, Access login, package downloads and external tunnel traffic remain
unimplemented/unverified; no claim of a live site or playable web game.

## October 13, 2026 — Live HTTPS/TLS tunnel

After user reconnect, Cloudflare writes succeeded: dedicated llm-2k5 tunnel,
proxied 2k5 hostname and hostname-scoped HTTP-to-HTTPS 308 rule. Started local
origin and connector. Origin uses TLS 1.2 minimum with explicit localhost
certificate verification in cloudflared; TLS verification remains enabled.
Trusted local TLS and public HTTPS health returned 200; public HTTP redirected
308 preserving query. Tunnel reported healthy/four active connections. Unauthenticated
franchise endpoint denial and authenticated unconfigured-state behavior were checked.
Tokens/key are private ignored local files. Current origin has no attached franchise
database; browser UI, package downloads, production startup/certificate renewal and
real-game integration remain outstanding. No paid inference or financial writes.

## October 13, 2026 — Durable HTTP negotiation boundary

Added token-authenticated HTTP negotiation through the existing Bridge, limited
to the configured franchise and negotiate operation, with one inference/no queue.
Default AI remains disabled. Explicit vertex-runtime startup uses restricted
impersonated credentials and remote GoogleControl; no owner fallback or IAM change.
165 tests pass locally. Actual loopback test verifies disabled-before-model,
shutdown-during-model acceptance with unchanged finances, durable sign/retry with
no regenerated model decision, restart revision and cross-team denial. Public
origin still has no database/model, and browser UI/live inference remain unfinished.
Prior a3a0949 Franchise AI CI passed; its inherited build check failed fetching the
xboxrecomp submodule because GitHub TCP connection timed out, before compilation.
Latest TLS 6440101 CI was still running when inspected; no full-game validation.

TLS commit `6440101` subsequently passed Franchise AI CI run 38474298115 and
inherited build check run 38474298056. The inherited timeout did not recur.

## October 13, 2026 — Private durable management priorities and TLS regression

Added ManagementProfile with stable manager identity, authored source and bounded
finite priorities for win-now, development, continuity, financial flexibility and
risk tolerance. Unknown/duplicate priorities, booleans and nonfinite weights reject.
Profiles persist in original team configuration, survive store replay and feed
private draft comparison context. Player/agent accounting prompts do not expose GM
priorities. Financial postings and cap authority are unchanged. Profile evolution,
actual CPU offer/draft selection and game hooks remain unfinished.

168 local tests pass. New TLS integration check rejects an untrusted origin and
wrong certificate hostname, then succeeds with the explicit trusted certificate.
OpenSSL generates ephemeral test credentials; no keys are committed. TLS fixture
check skips explicitly if OpenSSL CLI is unavailable. Existing persistent negotiation
example preserves agreement, exact balances and no regeneration after restart.
Prior HTTP negotiation commit 8463519 passed Franchise AI CI run 38474521864 and
inherited Build check run 38474521234. Browser framework choice remains open after
the user requested clarification of the term workspace; no UI stack was assumed.

## October 13, 2026 — Shutdown-guarded draft scouting advisor

Added strict recommend/defer model advice with eligible-shortlist identity checks,
required reason/uncertainty, frozen sourced context, stale financial/evidence
rejection and fresh access checks before/after inference. Same-session request
retries reuse recorded advice; all-ineligible boards defer without inference.
Vertex supports a dedicated draft schema/instructions while preserving the default
player negotiation schema. No paid calls were made. 172 local tests pass, including
model choice of an over-cap candidate, shutdown during inference, concurrent
budget changes, no-inference deferral and both provider schema paths.

This is read-only scouting advice, explicitly not an exercised draft pick or fund
reservation. Durable scouting history, league pick order/rights and atomic draft
commitments remain required before franchise draft integration. Same-session cache
is not restart persistence. This step does not satisfy the complete draft milestone.

Previous management/TLS commit `d396f59` passed Franchise AI run 38474883517
and inherited Build check run 38474883715.

## October 13, 2026 — Durable scouting memory

Recorded scouting advice as source events in FranchiseStore with unchanged financial
postings. Restart retries recall the original decision without inference, and later
model contexts receive compact chronological advice history. Writes check financial
revision, management context and history inside the transaction, then recheck remote
access. Replay verifies these contexts and exact eligible contract previews; tampering
fails closed. Advice grants no pick rights and changes no rookie pool/cap ownership.
174 tests pass locally, including restart/no-regeneration, story continuity,
concurrent-history rejection and tampered financial revision. Atomic draft ownership,
ordering and money reservations remain unfinished. The site is not game integration.

Prior advisor commit `b6dcef4` passed Franchise AI run 38475122079 and inherited
Build check run 38475122081.

## October 13, 2026 — Draft management funding reservations

Added explicit sourced management earmarks for drafted-rookie contract estimates.
Other signings preserve reserved current-year cap room and year-one/total rookie
allocation, including the reserved UDFA share. Existing draft tenders are credited
once. Earmarks change no NFL salary charges, actual rookie spending, cash owed or
pick rights; actual signing removes its own earmark and posts only real terms.
Explicit management withdrawal restores availability, without releasing a contract.
Store events replay/retry atomically; final access denial rolls back reservation.
179 local tests pass, including exact fractional funds, pool protection, signing
replacement, no double-counted tender, withdrawal, restart/retry and shutdown.
Draft ownership/order and verified game hooks remain required.

Durable scouting CI run 38475440449 passed Linux but failed Windows cleanup because
the corruption test kept a sqlite3 connection open after its transaction context.
Changed the test to close explicitly in isolated commit bdc1ce9; CI verification
is pending. The inherited build check run 38475440546 passed. This failure was not
reported as a green workflow.

## October 13, 2026 — Ordered draft rights and atomic funded picks

Added immutable source-declared draft orders/classes and globally exclusive pick
records. Pick commits validate order, team, prospect availability, assigned round,
financial revision and funding estimate, then record rights/funding together under
one transaction and final access check. Signing previews reject unselected class
members and another team's rights; draft comparison previews can evaluate unselected
prospects. Selected-prospect funding cannot be withdrawn as a casual management
reservation. Signing consumes real compensation without double-counting earmarks.
AI picks must cite the latest matching persisted recommendation and unchanged
contract estimate; manual mode is explicit. Restart/retry, out-of-order picks,
competing signing rights, over-cap/disabled rejection and AI recommendation binding
pass in offline tests. Source slot/economic import, draft trades, rights expiry,
year rollover and real guest hooks remain unsupported. This is engine transaction
integration, not evidence of game execution.

## October 13, 2026 — Promise vectors and achievement scoring

Accepted user-requested touches/starts/yards/wins as nonfinancial negotiated goals
and fulfillment as a scored consequence. Added typed PromiseGoal and GoalObservation,
with explicit window/source, positive targets and authored player importance.
Yard goals specify receiving/rushing/passing. Touches are observed carries plus
receptions, not targets. Fulfillment is exact, weighted and capped per goal; missing
coverage remains unknown and no final score is issued until the period closes with
complete observations. Context is preserved without inventing excuses/counter values.
These scores measure promises, not player ability, and produce no cash/cap effect.
185 local tests pass. Provider/pipe/HTTP negotiation terms, atomic promise agreement,
persistent scoring and story/relationship consequences remain to be wired; existing
live negotiation still does not offer promises. No actual game counters were observed.

## October 13, 2026 — Promise-aware negotiation and atomic agreements

Provider schemas/instructions, Negotiation and Python pipe/HTTP bridge accept typed
optional promise proposals. Model acceptance preserves them; counters explicitly
preserve/change/withdraw the full set. Accepted goals persist in the signing story
within the same transaction as finances. Restart retries recall both money/goals
without inference and reject changed promises under the same request ID. Guarantees,
cap validation, shutdown and legacy no-promise callers remain supported. 189 local
tests pass, including goal counter, pipe request/retry, atomic save/restart, over-cap
rejection and shutdown during acceptance. Promise score persistence and causal
relationship/story consequences, plus native/game/browser controls remain next.
No live inference, salary incentives or actual gameplay counters were added.
Prior draft/promise-core source commits passed both workflows: draft 78faf5d runs
38476541257/38476541340, core ca7fa4a runs 38476552766/38476552880. Funding f3f50a7
also passed both workflows 38475903638/38475903630, verifying the Windows cleanup fix.

## October 13, 2026 — Persistent promise scores and causal trust evidence

Committed agreements reconstruct their typed promises; score events reference a
real signed agreement and explicit observation/period-closure sources. Scores
recompute on replay, retry idempotently, reject stale state/conflicting reuse and
refuse overwriting a complete final result. Unknown/in-progress coverage is retained
and can later resolve. Player context contains recorded score history, and model
instructions distinguish promise fulfillment from ability/fault. Scoring advances
revision for stale-model protection without changing salary/cash balances.

Known final scores may source existing bounded once-only relationship updates;
unknown/in-progress scores cannot. No automatic blame/reward policy was introduced:
health/coaching/opportunity context remains required for actual story consequences.
Negative net yardage stays observed and scores at zero fulfillment; negative counts
remain invalid. Provider context is copied so acceptance cannot silently mutate
original offered promises. 195 local tests pass for persistence/restart, score-source
trust updates, duplicate prevention, source/revision errors, unknown-to-final results,
negative yardage and model-input isolation. No actual gameplay counters or UI exercised.
Prior promise-agreement a19d6cd passed Franchise AI run 38476915894 and Build check
38476915987. Current scoring CI is pending after push.

## October 13, 2026 — Franchise personality initialization and reviewed evidence mapping

User requested creation-time personality population and parallel agents. Added
atomic create_franchise with saved random/explicit seed and versioned per-player
streams, seven authored priorities, varied negotiation styles and neutral team
relationships. All registered veterans/rookies/free agents initialize; roster players
without classification reject. Late teams initialize too. Legacy authored actors
remain unchanged, and seeded replay verifies full initial actors/coverage.

Added typed promise performance mapping: carries+catches for touches, actual starts,
position-specific yards and separately sourced team wins. Automatic final scores
require certified complete-window/team scope; partial values remain progress.
The adapter currently covers one matching window/mode and observes no real game data.

Two read-only agents reviewed initialization and evidence independently. Fixed their
findings: late-team/missing actor coverage, seed NUL encoding ambiguity, initial trust
tampering, incomplete evidence finalization, absent player-team scope and historical
receipt retry compatibility. Added fixed traits, default-world variation, tampering,
late-team and durable partial-to-complete mapper tests. 208 local tests pass. New
creation/game hook, multi-window evidence and actual Deck/Windows gameplay remain
unfinished. Prior promise-score ac1a61c passed Franchise AI run 38477252097 and
Build check run 38477252142. No live inference or asset acquisition occurred.

## October 13, 2026 — Source-backed bootstrap command

Added bounded duplicate-key-rejecting JSON bootstrap command for source team configs.
Creation uses a private sibling database, saves provenance/input hash, initializes
players, replays all teams and atomically publishes via no-replace hard link. Existing
franchises, symlink destinations and competing creators are preserved; failure leaves
no published partial state or owned temp artifacts. The receipt explicitly reports
no game-runtime verification. A read-only parallel agent reviewed the path and found
nonobject team configs were normalized by dict(); explicit JSON-object validation
now rejects them. Added concurrency/symlink/seed publication verification.
213 local tests pass. Symlink test explicitly skips if a runner cannot create links.
This supplies the creation adapter boundary, not raw save parsing or a native guest
hook. Legal source exports/game addresses and actual Windows/Deck runtime remain
required. Previous initialization ab1b338 CI was still running when first inspected.

Initialization commit ab1b338 subsequently passed Franchise AI run 38478074874
and Build check run 38478074859.

## October 13, 2026 — Saved player context read boundary

Added a single validated database snapshot exposing saved personality, relationships,
signed promise goals and promise history. Protocol-1 player_context and authenticated
GET /api/player expose it without inference, actor rebinding or financial writes.
Strict query validation, unknown-player responses and native response identity/type
checks are covered. 215 Python tests and portable C++ protocol CTest pass locally.
The public running origin has no franchise database configured; no dashboard or
actual game menu integration is claimed. Bootstrap e8e9e95 passed Franchise AI run
38478464352 and Build check run 38478464544. Windows verification of this new source
is pending CI; game/Deck execution and legal source assets remain external gates.

## October 13, 2026 — Windows player-context transport fixture

Extended the existing Windows native pipe fixture to fetch saved player context after
signing, compare the complete result against the authoritative database read, then
fetch it again after client/sidecar restart and require identical context. Existing
cap rejection, idempotent signing and parent-death ownership checks remain. Python
syntax validation and 215 local tests pass; Win32 execution is delegated to CI and
remains synthetic rather than actual game integration. Player-context 4118b1d runs
38478945850 and 38478945789 were confirmed in progress at inspection.

## October 13, 2026 — Native negotiated-promise integrity

Native negotiation response validation now requires submitted promise goals to echo
unchanged alongside the original monetary offer, validates complete counter-goal
lists and rejects non-null counter promises for accept/reject. Goal metric, identity,
source, positive integer target, bounded importance and unique IDs are validated.
Portable C++ checks cover accepted terms, changed targets, missing promise echoes,
unexpected counter terms and boolean weights. CTest passes locally. No actual game
menu or guest write integration is claimed. Windows fixture fb62cfd CI runs
38479010675 and 38479010676 were in progress at inspection.

## October 13, 2026 — Counter-promise and saved-goal validation coverage

Applied shared typed-goal validation to saved player agreement reads. Added native
checks for a valid changed counter target, explicit empty-list withdrawal, null
counter lists, duplicate IDs, hidden-rating metrics, absent source, fractional targets
and malformed saved goals. Portable CTest passes. Player-context 4118b1d Franchise
AI run 38478945850 completed successfully; inspected Windows job confirms native
protocol and existing durable pipe fixture steps passed. The newer context-restart
fixture and promise-integrity commits still require their own CI results.

## October 13, 2026 — Windows player-context restart evidence

fb62cfd passed Franchise AI run 38479010675 and Build check run 38479010676.
Completed Windows logs explicitly report player context and restart verification;
215 tests passed on both Linux and Windows. Updated bridge protocol documentation
with read semantics, native promise validation and the precise synthetic evidence
boundary. Corrected the old statement that all promise scoring was unfinished:
source-backed scoring exists, while actual game counters/automatic consequences do
not. Newer promise-check CI remains pending and no gameplay claims are made.

## October 13, 2026 — Multiple promise observation windows

Added explicit multi-window mapping and connected it to durable performance scoring.
Exactly one sourced player snapshot per agreed window is required; duplicate/mixed
mode snapshots, missing or unrelated windows reject rather than summing uncertain
coverage. Team results remain separate per window and partial evidence prevents
finalization. Tests verify distinct windows/modes, stable goal ordering, complete
versus partial scores and ambiguous/missing snapshot rejection. 216 local tests pass.
Actual game instrumentation and automatic calendar transitions remain unfinished.

## October 13, 2026 — Durable multi-window scoring acceptance fixture

Added a committed two-window promise scenario through record_promise_performance:
early played starts plus season CPU-played wins. Missing team results remain unknown;
complete separately sourced standings finalize the score. Reopening the database
replays identical history, an identical request retries without revision changes,
and changed evidence under the same request rejects. Financial charges remain
unchanged throughout; exact revision progression is checked. 217 local tests pass.
This verifies durable engine behavior with synthetic evidence, not real game stats.

## October 13, 2026 — Reviewed multi-window evidence scope

Read-only parallel reviewer found no blocking defect in multi-window/durable scoring
and identified a scope-test gap. Added foreign-team and mismatched team window/mode
coverage through the batch API. Moved team window/mode validation ahead of goal
mapping so mismatched supplied standings reject even when no win goal consumes them.
Corrected obsolete single-window-only documentation. 218 local tests pass; no
inference, financial mutation or real game observation was performed. Multi-window
CI runs 38479318702/38479318522 and durable fixture 38479378828/38479379061 were
in progress at inspection.

## October 13, 2026 — Draft evidence duplication boundary

Prospect comparison now rejects repeated observation window/mode snapshots before
model inference, preventing duplicate supplied production from reinforcing a draft
recommendation. Separate simulation modes remain explicit records rather than being
summed. Regression verifies no provider call and unchanged financial state on rejection.
219 local tests pass. Actual scouting observations and guest draft integration remain
unfinished; the new boundary does not infer opportunity counters or hidden grades.

## October 13, 2026 — Durable scouting evidence reconstruction

Scouting write/replay validation now reconstructs typed PerformanceEvidence and
Observation records for every candidate, requiring player ownership, unique
window/mode identities and exact derived context metadata. This rejects duplicate
history snapshots, foreign player identity, impossible receptions/targets and
falsified missing-counter coverage rather than trusting persisted JSON containers.
Database-tampering regressions exercise all four cases; 220 local tests pass.
Durable multi-window c9133c2 passed Franchise AI run 38479378828 and Build check
38479379061. Recent draft/evidence commits still awaited their own CI at inspection.
No real-game observations or playable runtime were available.

## October 13, 2026 — Shared saved personality in draft scouting

Draft comparison and durable scouting replay now validate prospect personality
against an already saved player actor. Initialized franchises reject caller-supplied
replacement traits before inference; legacy players without saved actors retain
explicit sourced prospect inputs. No read generates or binds an actor. Added a seeded
franchise scouting fixture confirming canonical traits, rejected replacement before
provider call, reopened identity and unchanged financial revision. 221 local tests
pass. This connects creation-time personas to engine draft advice, not a verified
guest draft UI or real game hook.

## October 13, 2026 — Draft personality replay acceptance and review finding

Added database tampering regression for changed initialized prospect personality,
and a legacy sequence where scouting precedes actor binding. Historical advice
replays chronologically without applying future traits to old evidence. 222 local
tests pass. Independent read-only reviewer confirmed initialized ordering but found
an unresolved legacy cross-team gap: scouting on an unbound team does not yet check
an actor already saved on another team. Next work must enforce canonical prior
personality for new advice and chronological cross-team replay, preserving genuinely
unbound historical authored evidence. No game integration is inferred from tests.

## October 13, 2026 — Canonical cross-team legacy draft personality

Resolved the independent review finding. New scouting validates the first globally
saved actor personality before inference and again inside the write transaction.
Replay checks only actor events preceding the advice, preserving legacy chronology.
A second team cannot substitute priorities merely because it lacks a local binding.
No actor is generated or bound by scouting reads. Regression covers contradictory
cross-team input before provider call, canonical advice and tampered replay; prior
historical-before-binding fixture still passes. 223 local tests pass. Actual guest
integration remains unfinished and source CI is pending.

## October 13, 2026 — Cross-team chronology and in-flight personality acceptance

Added scenarios for actor binding on another team after existing advice and during
an in-flight provider call. Old advice remains readable because replay uses prior
event IDs; conflicting in-flight advice rejects and creates no scouting receipt.
Both paths preserve the full financial snapshot across database reopening. 224 local
tests pass. Cross-team fix CI 38479859663/38479859594 and chronological fixture
38479792769/38479792749 were confirmed in progress. No actual game execution occurred.

## October 13, 2026 — AI pick requires current canonical personalities

AI pick commit now revalidates every compared candidate's personality against local
and globally established actors inside the final transaction. Replay applies the
same check using actor events preceding the pick. Historical advice remains readable,
but a later contradictory actor assignment requires refreshed advice before an AI
pick. Manual picks retain explicit manual authority. Regression verifies stale advice
cannot create rights/reservations and preserves both teams' financial state.
225 local tests pass; guest draft execution remains unverified.

## October 13, 2026 — Refreshed personality advice completes durable pick

Extended the stale-personality pick acceptance scenario through recovery: fresh
canonical scouting advice permits the ordered AI pick and funding reservation;
reopening and retrying returns identical posting without another revision. Historical
and fresh advice coexist and room reflects one reservation. 225 local tests pass.
AI pick source CI 38479996558/38479996594 and cross-team fixtures were confirmed in
progress. This is a synthetic draft engine scenario, not guest-game execution.

## October 13, 2026 — Money audit scope refresh

Current audit verified 5,050 exact bonus-conservation cases and durable restart,
exclusive ownership and zero-room cap enforcement. Corrected stale output that
called all cash/guarantee and roster-phase work unimplemented: output now explicitly
names implemented components and distinguishes incomplete settlement/vesting, full
Team Salary/phase transitions and authoritative releases. Release/trade/restructure,
year rollover/options and real guest import remain unresolved. This output change
adds no financial authority. Cross-team fix f6bd2ec passed Franchise AI run
38479859663 and Build check 38479859594; later source checks remain pending.

## October 13, 2026 — Draft AI shutdown and manual recovery acceptance

Added a recorded-advice scenario where remote access denies inside the final AI pick
transaction. Reopening confirms both teams' financial snapshots remain identical,
with no pick/right/funding posting. An over-cap explicit manual pick still rejects;
a legal explicit manual pick then commits at the original order and revision with
one reservation. 226 local tests pass. The fixture uses a synthetic shutdown guard,
not live cloud credentials or actual game UI. Latest source CI remained in progress.

## October 13, 2026 — Companion registered-player discovery

Added authenticated GET /api/players backed by one validated database snapshot.
Lists stable registered IDs, veteran/drafted/undrafted classification and saved-actor
initialization, with revision and explicit unverified guest-membership scope. No
ratings/names/roles are inferred, no actors generated and no AI requests made.
HTTP regression verifies authentication, exact store correspondence and unchanged
revision. 226 local tests pass. This supplies a browser discovery read; no dashboard
or game roster import is claimed.

## October 13, 2026 — Player discovery preserves legacy state

Verified legacy HTTP player-list/detail reads keep actors absent with AI unconfigured
and leave finances unchanged. Added mixed veteran/drafted/undrafted registration
fixture confirming exact classifications and identical discovery after database
reopening, with no actor creation. The first fixture run failed on missing UDFA reservation
provenance and was accidentally pushed as 3202eed before verifying the result.
The follow-up adds explicit synthetic provenance and reruns validation. Money audit 2f8f6b8 passed
Franchise AI run 38480116739 and Build check 38480116772; discovery/shutdown source
CI remained in progress. No browser dashboard or guest roster verification exists.

The sourced discovery fixture repair passed all 227 local tests before publication.
No accounting code was changed by the fixture repair.

## October 13, 2026 — Companion origin source refresh

Confirmed the prior project origin live on localhost:8786 and deliberately restarted
it to load current validated API source (new session 41021), retaining trusted TLS,
private file-loaded bearer and --ai disabled. No database was invented/configured.
Public HTTPS health returns ready, unauthenticated /api/players returns 401, and
trusted authenticated localhost /api/players returns 503 franchise_not_configured.
Auto-review rejected sending the bearer through the public tunnel; no bypass/retry
occurred. Public authenticated response was not verified. Corrected fixture CI
38480372499/38480372500 remained in progress at inspection. UI product question is
pending; no browser dashboard or playable game exists.

## October 13, 2026 — Saved negotiation stories in player context

Player context now includes authoritative chronological negotiation_history from the
same validated database read as personality/promises/revision. Shared internal history
read preserves signed charges and recorded dialogue without model regeneration.
Native clients validate optional history containers and reject other-player offers.
Reopened signed-story correspondence and native foreign-player rejection are verified;
227 Python tests and portable CTest pass. Corrected fixture 2591b5b passed Franchise
AI run 38480372499 and Build check 38480372500; earlier 3202eed Franchise AI run
38480331814 failed as documented. This new source has not been deployed to origin.
Long-history pagination and actual browser/game story presentation remain unfinished.

## October 13, 2026 — Explicit recent negotiation history coverage

Player context now returns the latest ten stories with total count and has-more flag,
retaining complete durable history. Native clients validate optional coverage metadata.
A 13-story reopen fixture confirms chronology, recent selection, full retention and
unchanged charges. 228 local tests and portable CTest pass. Event-count limiting does
not guarantee byte-sized frames; oversized evidence/promises and full browser history
pagination remain unfinished. Source is not yet reloaded into the public origin.

## October 13, 2026 — Stable saved-story pagination

Added validated store and authenticated HTTP history pages with stable event-ID
cursor, latest-first retrieval/chronological page display and explicit next cursor.
Player filtering occurs before SQL page limit; manual signings without stories are
excluded. New append does not shift older pages. Tests traverse old signed/rejected
stories after append/reopen, reject invalid cursors/query fields, verify auth/unknown
players and preserve charges. 229 local tests pass. Per-story byte bounds, browser
rendering and actual game story presentation remain unfinished. New API is not yet
reloaded into the public origin.

## October 13, 2026 — History cursor bounds and mixed-event isolation

Found cursor values exceeding SQLite signed event IDs reached sqlite binding overflow;
now reject before querying with ValueError/HTTP 400. Added mixed-player and manual
signing fixture proving filtering happens before the page limit, nonstory signings
are excluded and older pages neither skip nor repeat the player's stories. 230 local
tests pass. Saved-story be39a27 passed Franchise AI run 38480679681 and Build check
38480679677; pagination/newer source CI remains pending. No live game data was used.

## October 13, 2026 — Oversized native player-context read recovery

Native player-context responses now check serialized UTF-8 frame size before returning
large saved content. Oversized read returns context_too_large/null result rather than
breaking the pipe parser. Regression uses a large legacy actor and verifies bounded
error, subsequent preview, no inference and unchanged revision. 231 local tests pass.
The guard is read-only and does not claim all-operation frame limits or automatic
truncation of saved records. Game UI handling and real integration remain unfinished.

## October 13, 2026 — Release lifecycle primary-rule review underway

Read-only independent financial review identified a substantive first transaction:
explicit healthy preseason veteran release before declared first regular-season game,
with source-backed absence of injury/termination/additional bonus liabilities,
allocated cash, settled past years and no earned/paid current base. Retain original
unamortized signing bonus and remaining protected base; preserve unpaid bonus and
guaranteed base cash and cancel only verified unearned unprotected base. Rookies,
waiver transfer, offsets/voids/designations and same-team re-sign remain unsupported
until their obligation/cohort/generation semantics exist. Review reports primary CBA
Article 13.6(b)(ii), 13.6(d)(iv) and Article 30 checked; full source report is pending
and no release implementation/authority has been added. Must handle over-cap
acceleration and subsequent signing restrictions without dropping liabilities.
History cursor 36493ce Build check 38480930953 passed; Franchise AI run 38480931002
was confirmed in progress. The financial review agent remains active.

## October 13, 2026 — Supported pure preseason release calculation

Parallel implementation added releases.py and six independent tests. Primary review
caught earned-versus-paid ambiguity; scope now requires explicit healthy status and
zero earned base, with omission/boolean misuse regressions. Calculation retains
original bonus layers and covered-base PV separately, preserving nominal paid/unpaid
cash and cancelling only sourced unearned unprotected bases. Independent pre/post
June example yields 39 versus (33,6), with paid9/unpaid30 cash; exact fractional,
elapsed-year, final2030 and unknown-payment guards pass. Full suite237 passes locally.
No durable mutation/ownership/game authority exists yet. Added source/scope docs and
next transaction prerequisites; nearest-$1000 posting/rates/real guest facts remain.

## October 13, 2026 — Durable supported veteran release transaction

Parallel ledger and primary store integration now recompute supported release under
write lock, archive originals, replace active cap with retained bonus/base debt,
retain paid/unpaid cash, remove active/exclusive ownership and record before/after
postings. Replay validates original and resulting cash/financial state; exact retries
retain receipt while stale/conflicting requests reject. Cancelled salary payments
reject; protected payments leave cap unchanged. Release-induced overage is preserved
and subsequent unaffordable signings reject. Unsupported same-team re-sign rejects;
new club ownership can sign while old retained liability survives. Tests cover
pre/postJune charges, other retained obligations, scope failures, retry, restart,
access rollback, tampered cash and SQL failure after ownership delete. 246 local tests
pass. No real game controls/runtime or complete waiver/offset/injury/calendar remedies
exist; exact NFL posting rounding and source rate verification remain unresolved.

## October 13, 2026 — Independent durable release review and identity fix

Independent read-only reviewer confirmed cash ceilings and rollback, and reproduced
retained-record ID collision with original obligations. Release now checks generated
bonus/base identities against original retained/adjustment records and prior releases
before mutation. Added collision/no-mutation regression plus durable old-signing
retry after release; original receipt returns without restoring ownership, cap or
nominal cash. 248 local tests pass. Pure calculation d56373a passed Franchise AI run
38481364854 and Build check38481365063; durable release d108266 CI38481644411/
38481644391 remained in progress at inspection. No guest-game integration is claimed.

## October 13, 2026 — Executable supported-release money audit

Extended tools.audit_money with independently expected durable pre/postJune release
scenarios: cap(39,0,0)/room-9 versus(33,6,0)/room-3; nominal39, paid9, unpaid30,
cancelled unearned30. Audit asserts removed ownership, identical restart receipt and
unaffordable signing rejection without mutation. Synthetic zero-rate/prototype scope
is explicit. Audit succeeds alongside5,050 bonus-conservation checks. Durable release
d108266 passed Franchise AI38481644411 and Build check38481644391; reviewed identity
fix9b94fee CI remained in progress. Actual game import/execution remains unverified.

## October 13, 2026 — Primary CBA rounding scope clarified

Independent primary-source research confirms Article2§5 nearest-$1000 for Team Salary,
but no verified component/aggregate order or halfway tie convention. Signing-bonus
proration, guarantee PV and rookie compensation provisions do not independently
specify a posting stage; compensatory rookie allotment expressly uses nearest dollar.
Added exact article/printed/PDF references and no-tie counterexample demonstrating
material order ambiguity. Exact engine accounting remains experimental internal
limiting, not a claim of official rounded NFL postings. Authoritative reconciliation
and sourced policy remain necessary; no guessed rounding or money mutation added.
Reviewed-release9b94fee and audit42781f3 CI were confirmed in progress earlier.

## October 13, 2026 — Explicit manual release through local bridge

Added strict protocol1 manual_release with explicit manual mode, sourced typed scope,
discount/payment offsets, revision, timeout and final local connection guard. Provider
and remote AI grant are not called; shutdown leaves manual financial authority intact.
Native result validation checks revision, absence of released player ownership,
original archive player identity, exact charges and retained cash arithmetic. Tests
verify AI-off release/retry, disconnect rollback, invalid scope/mode/stale request and
malformed native responses. 250 distinct Python tests and portable CTest pass; initial
test-module import duplicated six cases and was corrected before publication.
No guest release hook or browser control is connected; complete CBA posting policy
and real runtime validation remain unverified.

## October 13, 2026 — Windows native release acceptance fixture

Extended Win32 smoke client with explicit --release mode and strict protocol request
for a sourced synthetic release. Python verifier creates original allocated obligations,
executes C++ pipe release/readback twice across service restart, compares entire
financial/cash receipt with authoritative replay, and requires exact retained39,
room-9, unpaid30, removed ownership and revision2. Existing native signing/parent-death
fixtures remain. Python syntax, diff checks and portable CTest pass locally; Windows
execution is pending CI and no actual game runtime is claimed.

## October 13, 2026 — Native release fact and valuation integrity

Native release result validation now requires archived scope, discount profile and
payment timing to match the submitted facts. Exclusion ordering normalizes before
comparison; source/rate/offset changes reject. Added portable regressions for valid
reordered exclusions and altered source, rate or offsets. CTest passes locally.
Windows release fixture run38482311333 was confirmed in progress; actual guest writes
remain unavailable and no runtime claim is made.

## October 13, 2026 — Canonical release dates before commit

Native fact comparison exposed a format mismatch: Python date parsing accepted ISO
basic compact strings then archived extended dates, causing a valid native request
echo mismatch after transaction. Bridge now requires canonical YYYY-MM-DD for both
release and first-game dates before any mutation. Added compact-date rollback cases;
250 local tests pass. Native release fixture a4c83a0 Build check38482311350 passed;
Franchise AI38482311333 was still in progress at inspection. No Win32 release
execution success is claimed until its actual step completes.

## October 13, 2026 — Windows native release execution verified

Native fixture a4c83a0 passed Franchise AI38482311333 and Build check38482311350.
Completed logs explicitly confirm Windows supported release, retained debt/cash and
restart retry;250 tests passed Windows and Linux. Later native-fact/canonical-date
changes still require their own CI. This is synthetic C++/Python transport evidence,
not playable Remade guest execution or save/load verification.

## October 13, 2026 — Preseason trade primary-rule review

Independent review verifies CBAArticle13§6(b)(ii) bonus acceleration applies to trades,
AppendixA paragraph17 contract assignment requires assignee performance, and release
PV rule13§6(d)(iv) does not establish seller guarantee-PV charges for ordinary trades.
Unpaid signing-bonus responsibility is not inferred from retained cap debt; initial
supported trade must require fully paid bonus pending actual contractual assignment
terms. Synthetic expectation: original10,20,30/bonus9/protected0,20,10 gives seller
preJune9 or postJune(3,6), buyerbase(10,20,30), sellerpaid9/buyerunpaid60. Guarantees
remain with assigned active salary, not guessed seller PV. Full review/design pending;
no trade authority implemented yet. Next work requires atomic paired team events,
ownership reassignment, original archives and cash/cap reconciliation on both sides.

## October 13, 2026 — Pure supported trade assignment and replay design review

Parallel implementation adds trades.py/five independent tests: seller original bonus
cap/paidcash retained, remaining bases/guarantees assigned intact to buyer with no
bonus or releasePV duplication. Mandatory sourced scope and complete payments reject
unpaid bonus/unknown or contradictory coverage. Exact global cash/remaining cap
conservation passes, including elapsed/finalyear/fractional cases;255 fulltests pass.
Independent replay design review requires independently validating participant actual
pre-trade histories, not merely equal paired payloads, and nonrecursive final ownership
validation. Added source/scope/prerequisite docs. No durable trade/guest authority exists
until paired transaction and replay implementation are validated.

## October 13, 2026 — Atomic paired preseason veteran assignments

Parallel cap and primary store integration recompute seller/recipient plans and enforce
both revisions, original allocated payments, recipient floors/room and unique records.
One transaction reassigns exclusive ownership and inserts linked role events with
both actual before/after cash/financial snapshots. Replay checks pair count/roles,
source terms and independently replays all teams nonrecursively when trades exist,
preventing consistently forged paired JSON from masquerading as source history.
Seller keeps original paid history/bonus debt; buyer gets remaining bases/guarantees
without bonus or releasePV duplication. Unsupported prior-contract returns reject;
old-club promises/personality/history remain separate.265 local tests pass, covering
cash conservation, stale/affordability/access rejection, partial-SQL rollback,
competing buyers, three-club chain, missing/forged links and seller cap overage.
No trade consideration, guest assets/hooks, UI controls or official posting policy
are implemented. League replay performance requires actual runtime measurement.

## October 13, 2026 — Reviewed trade/payment/release lifecycle composition

Independent read-only review found no blocking defect and executed compound lifecycle
checks. Added permanent buyer-only cash payment, seller-payment rejection and buyer
release scenarios; original seller bonus9 remains once, buyer protected release30
and later unpaid25 reconcile. Original trade receipt retry after payment/release or
three-club chain changes no current cash/cap/ownership state.267 local tests pass.
Atomic trade efc262f runs38483265439/38483265491 remained in progress at inspection;
pure trade2ac6a53 passed38482850540/38482850516. Real guest transaction/gameplay and
official posting precision remain unverified.

## October 13, 2026 — Manual paired assignment through client bridge

Strict protocol1 manual_trade accepts both participant revisions and mandatory
canonical sourced scope, without provider/remote AI calls. Final connection/deadline
failure rolls back both participants. Native result checks both revisions/owners,
exact charges/cash arithmetic and unchanged paired archives/facts. Tests cover AI-off
commit/retry, source/mode/stale/date rejection, disconnect rollback and malformed
native replies. Found bool==int retry equality gap; store release/trade methods now
reject noninteger revisions before prior-receipt comparison.269 local tests and
portable CTest pass. Actual Win32 assignment transport and game controls remain
unverified; trade consideration and official posting precision remain unsupported.

## October 13, 2026 — Windows paired-assignment transport fixture

Added native --trade mode for explicit manual assignment and recipient context read.
Windows verifier creates two sourced books, executes the C++ pipe path twice across
service restart, compares both complete cash/financial receipts to independent replay,
and checks revisions2, sellerbonus9, buyerbases10/20/30, one buyer owner, inherited
protected bases0/20/10 and total nominalcash69. Python syntax, diff checks and portable
CTest pass locally. Actual Win32 execution awaits CI; no game trade UI/hooks or retail
assets were used. Existing release/signing/parent-death fixtures remain intact.

## October 13, 2026 — Executable paired-assignment money audit

Audit now asserts durable pre/postJune sellerbonus(9,0,0)/(3,6,0), unchanged buyer
bases(10,20,30)/protected(0,20,10), sellerpaid9/buyerunpaid60 and combinednominal69.
Exclusive buyer ownership, participantrevision2 and identical restart receipt are
verified. Complete audit succeeds with5,050 bonus-conservation cases and existing
release/signing scenarios. Consideration/game/runtime scope is explicitly unverified.
Windows paired fixture38483786386/38483786465 remained in progress; prior manual
bridge Build check38483689271 passed while engine38483689268 was still running.

## October 13, 2026 — Dated financial chronology and Windows assignment proof

Release/outgoing/incoming assignment now checks source salary/rookie profile year
and prior dated financial operation before mutation. Backward dates or crossing into
another year require an unsupported explicit year transition and reject. Chronology
is derived during event replay without changing prior posting shape; it is not a
complete franchise calendar. Regression rejects pre-assignment or next-year recipient
release and preserves all team state.270 local tests pass. Windows fixture56ba13f
Franchise AI38483786386 completed successfully; logs explicitly confirm paired
assignment/inherited guarantees/conserved cash/restart and269 tests on both OSes.
No actual guest-game execution/save evidence exists.

## October 13, 2026 — Measured local all-team replay baseline

Added bounded temporary benchmark with supported paired assignment and verified
history retention.32-team640 short dialogues measured median8.31/max8.96ms;3,200
measured median32.39/max33.07ms over5 fresh validated reads on this Mac. No persistent
cache introduced; fixture excludes actual model evidence/guest payload complexity.
Source syntax/diff and both executable runs passed. No correctness timing threshold,
Windows/Deck latency or game-thread responsiveness claim is made. Money audit1d3a095
passed CI38483895093/38483895310; chronology60b54e6 CI was in progress at inspection.

## October 13, 2026 — Recorded negotiation evidence replay measurement

Extended bounded benchmark with real Negotiation/StoredLedger recording, scripted
reject provider, typed synthetic performance/unknown targets+pressures, actors,
proposed goals and prior-history references. No inference/cloud/retail data.32-team
640 evidence events measured median22.55/max22.94ms;3,200 measured111.76/113.79ms.
Both runs verified exact history retention and paired assignment charges. Documented
short-dialogue workload underestimation and cumulative read cost; no speculative cache
or Windows/game responsiveness claim added. Chronology60b54e6 passed Franchise AI
38484083446 and Build check38484083550; prior benchmark CI remained in progress.

## October 13, 2026 — Single validated league pass for paired assignment

Measured workload motivated removing a concrete duplicate replay: _load_teams now
rebuilds requested participants and validates every other team once in the same
transaction. No persistent cache, skipped participant history or freshness relaxation.
Added corrupt unrequested-team retry regression;271 fulltests pass. Benchmark now
verifies/times paired retries;32-team640 recorded evidence measured readmedian22.21ms
and paired-retry22.48ms on this Mac. Syntax/diff and executable benchmark pass.
Windows/game/Deck performance and actual guest integration remain unverified.

## October 13, 2026 — Preserve bonus layers in pure restructure calculation

Parallel primary-rule research and cash-boundary review produced an immutable bonus
layer representation and sourced healthy preseason guaranteed-base conversion.
Independent elapsed-year arithmetic preserves old proration, exact total compensation
and paid history; new bonus remains unpaid. Legacy empty-layer serialization stays
unchanged. Ledger/rookie imports and release/trade operations reject layers until
durable cash, amendment replay and lifecycle integration support them. No game write,
model call or actual cap import occurred.278 tests pass; synthetic money audit and
syntax/diff checks pass. Prior1eaa58f passed Windows Franchise AI38484953683 and
Build check38484953749. Durable restructuring and real runtime gates remain open.

## October 13, 2026 — Carry restructure layers through pure release/assignment

Nominal compensation components now identify each conversion bonus separately.
Pure release preserves unpaid bonus cash and accelerates all original/new layers;
pure assignment requires every bonus paid, retains seller debt and assigns remaining
base/guarantees. Independent elapsed-year expectations verify release36 split
128/5+52/5 and assignment seller14 split18/5+52/5; cash60/30 release and38+142=180
assignment reconcile. Contract snapshots and assignment reconstruction retain typed
layers while legacy empty-layer shape stays unchanged.281 full tests, extended
synthetic money audit, syntax and diff checks pass. Durable layered imports stay
closed pending amendment/cash/replay support; no actual game execution established.
Foundationab2d986 Franchise AI38485612032 passed; Build38485612146 remained running.

## October 13, 2026 — Durable preseason restructure and cash/lifecycle replay

Ledger amendments use stored annual floors, chronology, exclusive active veteran
state and distinct layer IDs. Atomic store events preserve original contract/cash
and exact before/after postings; both revisions advance, nominal/paid cash and
ownership do not. Conversion payments have individual ceilings; total unpaid
bonus reporting includes layers. Tests cover restart, exact/conflicting retry,
stale/final-access rollback, partial payment/overpayment, release then original
retry, fully paid assignment, and tampered source/postings. Parallel review found
serialized exclusions could normalize a liability dictionary away; all three
lifecycle replay adapters now require canonical unique string lists. SQL event-insert
failure also rolls back every amendment field.295 full
tests pass. Actual game/native/UI restructuring and source import remain unverified.

## October 13, 2026 — Close test SQLite handles on Windows

Durable restructure3e8a3f2 Windows CI38486094688 failed three cleanup cases because
new direct sqlite3 test context managers committed transactions but did not close
connections. Tests now use contextlib.closing plus explicit transaction contexts;
eight targeted cases pass locally. Financial behavior assertions had passed; Windows
cleanup fix awaits fresh CI. Native restructure protocol work is separately underway.

## October 13, 2026 — Manual restructure pipe and native response boundary

Protocol1 manual_restructure validates complete sourced scope, strict money,
revision and canonical dates; initial/final connection/deadline checks surround
durable commit. Explicit manual operation works AI-disabled without model/grant
calls. Native validator checks unchanged original term/bonus, conversion/guarantee
delta, new layer identity/allocation, minimums, retained ownership and conserved
cash/payment history.31 portable corruption scenarios and CTest pass;299 full
Python tests pass. Added Windows --restructure pipe/restart fixture and validated
its exact request against the durable engine locally; actual Win32 fixture run
awaits CI. Earlier3e8a3f2 Windows cleanup failure fixed in4f551ca, fresh workflows
38486232604/38486232593 were still running at inspection. Actual guest/UI write
and playable game/save evidence remain absent.

## October 13, 2026 — Saved player contract accounting inspection

Player context now exposes only the selected player's saved active/released/assigned
contract, bonus layers, explicitly scoped charges, cash obligation and guarantees
from one validated snapshot. Unknown contract/cash coverage remains null; actor
initialization and engine accounting are distinct from actual game roster facts.
Authenticated HTTP inspection shares the read-only view without revision writes.
304 full Python tests pass. Native optional-context validation covers shape,
identity, lifecycle, bonus allocation, exact amounts and cash/guarantee arithmetic;
20 malformed accounting scenarios and valid lifecycle fixtures pass portable CTest.
New SQL read tests explicitly close handles for Windows cleanup.3b78231 passed Franchise AI
38486364011 and Build38486364039; direct Windows logs confirm299 tests and native
restructure schedules/unpaid cash/restart fixture. This proves synthetic pipe
execution, not actual gameplay or save/load integration.

## October 13, 2026 — Historical signing retry after an amendment

Added durable restart regression starting from a newly signed guaranteed contract,
recorded original-bonus payment and sourced restructure. Retrying the original
signing receipt returns its historical receipt while leaving amended terms, all
bonus layers, finances and cash unchanged.305 full tests and executable synthetic
money audit pass. Player-inspection26ead88 CI38486762451 had Linux success and
Windows still running at inspection; Build38486762354 also pending. No new game
execution/save evidence or external gate resolution is claimed.

## October 13, 2026 — Controlled raw-save transaction comparison

Extended read-only save_diff with optional --control-after from the same restored
baseline. Full transaction/control spans and hashes are preserved; transaction
changes partition into offsets unchanged in control versus control-overlap, with
all three raw byte values retained. No overlap is erased or called a contract
field.309 full tests pass; independent review checked729 exhaustive two-byte
combinations for disjoint/complete partition and exact bytes, plus CLI read-only
behavior. Raw mismatch/ZIP/empty control reject. No actual save is present; B01/B02
field decoding and real round trips remain gated. Prior3cd6a5f passed Franchise AI
38486893108 and Build38486893119; player-accounting26ead88 also passed38486762451/
38486762354. No gameplay or save/load integration claim is made.

## October 13, 2026 — Sourced production efficiency in negotiation and draft

Added five exact same-window opportunity/yardage ratios retaining both counters,
sources and sample sizes. Missing/null/zero opportunities remain unavailable;
zero observed production and signed yardage stay valid. Negotiation and draft
contexts use derived views without changing historical raw observation shape.
Canonical wire reconstruction and durable derivation checks reject altered
ratios/samples/provenance/window/boolean substitutions, including draft attempts
to replace unavailable targets with zero rates. Legacy records remain compatible.
323 full tests, syntax/diff and executable money audit pass. No paid inference,
actual guest counters or live weighting verification occurred.1ad48e8 passed
Franchise AI38487147877 and Build38487147775. Actual game integration remains gated.

## October 13, 2026 — Preserve historical evidence retries after efficiency rollout

Audit found old draft receipts lacked the new derived view and could reject an
unchanged retry. Comparison now reconstructs it only from strict original
counters, while returning the unchanged historical receipt without provider
calls/history writes. Canonical JSON comparison avoids bool/int equivalence.
Also preserved freeform legacy performance using an observations label; typed
identity/window/mode/coverage claims still require complete canonical evidence.
324 full tests, diff and synthetic money audit pass.50f37c8 Build38490369723
passed; Franchise AI38490369770 remained running. No real game/save evidence
was added; full delivery goal remains active.

## October 13, 2026 — Bounded read-local efficiency derivation reuse

Expanded evidence benchmark measured32-team640-record readmedian69.90ms and
paired70.82ms. Reusing only the last successfully checked identical source
derivation within each team replay reduced follow-up medians to59.11/60.74ms
on this Mac. Cache key includes canonical full raw evidence and freshly parsed
offer identity; every actual derived result/common evidence/financial event is
still checked. Fresh reads and writes recompute; one entry prevents history-sized
cache growth.328 full tests cover later corrupted results, changed source/identity/
boolean/offer claims, new-read freshness and bounded retention. Independent review
found no skipped financial authority. No game/Windows/Deck latency claim or paid
inference.50f37c8 passed CI38490369770/38490369723; b4e0d77 CI remained running.

## October 13, 2026 — Portable package archive-layout validation

Packaging audit reproduced accepted file/directory casefold collisions, reserved
receipt descendants and mixed directory casing that split one Windows logical
folder in ZIP layout. These now reject before output creation; existing archives
remain unchanged. Primary Microsoft naming rules also confirm six superscript
COM/LPT device variants, now excluded with extensions/in directories. Positive
nested runtime fixture preserves exact archive paths and hashed bytes.330 full
tests and diff checks pass. No retail assets, game runtime, release ZIP or
Proton execution supplied; this improves candidate tooling without claiming
playable delivery. b4e0d77 CI passed38490590450/38490590375; latest999f884 CI
38490946024/38490945988 remained running at inspection.

## October 13, 2026 — Current ownership versus lifetime negotiation history

Audit reproduced a released player's former-club dialogue blocked forever by an
old signed story. Removed lifetime terminal flags; fresh negotiation input now
reads current ownership (league-wide in durable store) in the same snapshot. Old
receipt retries return historical results without closing later dialogues; active
owned players reject new free-agent inference even without a recorded signed story.
Return-signing generation guards remain to protect prior debt/cash.332 full tests
and corrected benchmark fixture pass; the fixture now negotiates an actually
unowned player separately from its assigned contract. Parallel generation audit
documented ordered immutable identity/cash/archive/migration prerequisites and
acceptance cases. No actual game/save or generation migration claimed.999f884
passed CI38490946024/38490945988; current packaging CI remained running.

## October 13, 2026 — Legacy contract identity inventory for migration

Added read-only stable per-team/player legacy identities independent of mutable
terms/payments/status. One validated snapshot preserves effective contract/cash
and supported retained records; unknown cash remains null. Parallel review caught
unmatched cash omitted from the first draft; final view preserves it explicitly
alongside opening debt/credits, prior cohort records and unsigned tenders without
guessed links. Authenticated /api/contracts uses the configured team and makes
no actor/financial/schema writes.339 full tests and diff checks pass. No format
migration, new-generation signing or game field mapping claimed. Packagingcf5d6a7
passed CI38491252585/38491252588; 06ba848 Build38491823246 passed and Franchise
AI38491823297 remained running. Full goal remains active.

## October 13, 2026 — Private generation migration preflight

Added an explicit existing-format3 preparation command. It reserves the source
snapshot, creates a private exclusive consistent backup, hashes actual backup
bytes, then validates all team replay, integrity/foreign keys, creation metadata
and unused draft-order source identities. Failed validation preserves the backup;
failed copying cleans only the new partial backup. Source bytes/history/format
remain unchanged. Inventory now shares its ledger projection with preflight.

All 350 Python tests pass locally, including backup failures, competing writers,
orphan rows, malformed unused orders, source preservation and the CLI. Exact
prior head 6fdeacd passed both GitHub workflows. New change remote checks remain
pending until push. No actual generation migration, return signing, guest save
roundtrip or playable game demonstrated.

User clarified that franchise management does not need a web surface. Removed
the browser dashboard from the worklist; in-game management remains required.
Existing HTTPS/API infrastructure remains available for service connectivity.

## October 13, 2026 — Agreement identity on the native pipe

Player contract context now carries the same deterministic agreement identity
as the league migration inventory. A shared identity function prevents divergent
derivation. Tests cover persistence after amendment/payment/restart, stability
through release, and distinct seller/buyer identities. Native decoding preserves
legacy responses and rejects invalid identity types, length and hex encoding.
All 350 Python tests and the portable C++ protocol check pass. No game UI or
multiple-generation contract support claimed. Migration must also replace the
legacy cash-ID assumptions in release, assignment and restructure calculators
before return signing can safely create new obligations.

## October 13, 2026 — Consumed immutable accounting identities

Durable ledger replay now binds the team and reconstructs immutable agreement,
player and cash identities with a separate active pointer. Signing and incoming
assignment register identities; release/outgoing assignment close the active
pointer and retain historical identity. Payments, guarantees, lifecycle math,
cash creation, source reconciliation and inspection consume the cash resolver.
Team rebinding and inconsistent mappings reject without repair. Calculator
inputs require an explicit matching expected cash identity; assignment can
identify destination cash separately. Old IDs and serialization remain unchanged.

All 361 Python tests pass. Seven identity tests cover immutable binding, closure,
corruption, atomic invalid-input rejection, incoming cash mismatch and durable
restart. Four calculator/cash tests cover strict identity checks, distinct records
and conservation. An independent isolated HEAD/current comparison found exact
equality of financial/cash snapshots and stored config/event JSON through
sign/release/payments/trade chains/restructure/restart. The synthetic money audit
also passed 5,050 bonus-conservation cases. Both GitHub workflows passed exact
prior heads 850ea16 and 1e59328; this change's remote CI awaits push.

This remains the legacy identity foundation. Database format3, player-keyed
archives and former-club return guards remain; actual multiple agreements need
versioned archives/migration. No guest writes or playable build demonstrated.

## October 13, 2026 — Agreement archives and native contract inspection

Typed immutable agreement versions now retain birth/effective terms and supported
release, assignment and restructure plans by generation. Bound active-contract,
terms and guarantee reads use these archives; cash remains live under the exact
agreement cash identity. Payment validation iterates all generation archives and
applies per-agreement lifecycle ceilings. Inventory and player context share
archive projections. Missing/mismatched archive coverage and typed source plans
reject; original format3 postings remain unchanged.

Added team-scoped read-only native contract_context by generation ID, available
with AI disabled. Unknown/foreign-team IDs reject; deadlines, disconnect checks
and the 64KiB frame limit apply. C++ validates requested identities and accounting.
Four integration tests cover real stored agreement reads, release/payment/restart,
request rejection/disconnection and oversized response recovery. Four archive
tests cover immutable birth terms, effective/closed debt, live payments, invalid
records and agreement-specific guarantee lookup.

All 369 Python tests pass; portable C++ build/CTest pass. Independent isolated
HEAD/current comparison found financial/cash snapshots, guarantees and persisted
config/event JSON identical across sign/release/payment/trade chains/restructure
and restart. Synthetic money audit passed 5,050 bonus-conservation cases. Exact
prior f71e5fd passed both remote workflows; new head CI pending push.

No new database format or former-club return signing enabled yet. Superseded
agreement lookup, versioned posting migration and atomic return signing remain
required. Actual guest hooks/screens, legal assets/save evidence and playability
remain unverified.

## October 13, 2026 — Backed-up format4 generation checkpoint migration

Implemented explicit format3→4 migration under the same write reservation used
for private consistent backup and whole-league preflight. A singleton checkpoint
anchors exact historical config/metadata/draft-order/event rows and captures
financial/cash state plus generation identities, birth/effective terms and
retained records. Old events/config JSON are unchanged. Every connection validates
source-prefix hashes and strict boundary replay before reads/writes/constructors.
New valid events/teams remain supported; constructor preserves4 rather than
downgrading it. Install failure rolls back to3, retaining its private backup.

Added opt-in --migrate to tools.prepare_generation_migration; default remains
preflight-only. CLI tests verify the backup hash/version and exact old events,
reopening4 and repeated-migration refusal. Migration regressions cover corrupt
prefix/manifest types/duplicate keys, failed-install rollback, bootstrap write
bypass prevention, missing-checkpoint refusal, later release/payments and signing
by a newly added team. All 377 Python tests pass. Independent review also verified
integer/bool/float distinctions and subsequent signing/restart. Exact prior
d0395c4 passed both remote workflows; this change remote CI awaits push.

Extended the synthetic replay benchmark with --generation-checkpoint. On this
Mac, 32 teams/640 recorded evidence stories: format3 median read60.68ms and paired
retry62.71ms; format4 read131.81ms/max135.49ms, retry130.81ms. Checkpoint validation
adds historical replay cost; no persistent state cache or timing-test threshold
introduced. These measurements are not Windows/Deck/game acceptance evidence.

Format4 continues legacy event posting semantics. Versioned new-generation events,
superseded agreement lookup and return signing remain unfinished. Actual game
hooks, legal assets and save/load/runtime evidence remain external gates.

## October 13, 2026 — Durable same-year veteran return agreements

Implemented sourced healthy same-year preseason veteran return signing after
format4 migration. Each new agreement gets deterministic team/player/request
generation identity and matching cash ID. New cap charges add to old retained
debt. Prior birth/effective terms, unpaid cash, lifecycle sources and original
payment IDs remain archived. Old agreement lookup is independent of the current
player pointer. No implicit year transition or guarantee offsets.

Durable return/release/payment records validate versioned full generation postings
while preserving historical financial views. Second release retains both debts;
third agreement remains separate. Final access failure and a SQLite trigger
failing journal insertion after ownership acquisition roll back all state. Mixed
normal/return receipt reuse rejects cleanly; old signing/release retries preserve
the later active agreement. Native accounting inspection accepts contract-gen IDs
and requires their matching cash obligations.

All 392 Python tests and portable C++ build/CTest pass. Independent review verified
rollback, three agreements, old-debt payments/ceilings and first-return retry after
a third agreement. Ten+ focused source/durable cases cover cap/floor/chronology/
unknown cash/source/revision rejection, version downgrade/corruption, two former
clubs competing for ownership and cancelled salary payment rollback. Exact prior
8b43e6d passed both remote workflows; new head CI pending push.

Return signing is currently an explicit engine API. Normal AI negotiation and
native pipe entry still need scope/preview/decision wiring; returned-player trades
and restructures reject. Game hooks/screens, real saves/assets and playability
remain unverified. See docs/preseason-return.md.

## October 13, 2026 — Native return negotiation, stories and promises

Existing pipe preview/negotiate/manual_sign requests now accept optional sourced
return_scope. Read-only preview validates return eligibility and existing debt;
AI decisions use existing observed performance, personality, relationships and
lifetime history. Scope is frozen in provider context/evidence/receipts. Accepted
stories and promises commit with the new agreement. Rejected/counter dialogue
persists and cannot switch scope or normal/return mode on retry. Story/history
readers now include negotiated returns while safely skipping older manual
agreements without narration.

Final remote access, connection/deadline, revision/ownership and cap checks remain
enforced after provider response. Tests cover accept+promise restart/retry, reject,
counter, readonly preview, kill-after-provider, stale-budget race, disconnect,
manual AI-off and changed scope/mode rejection. All 397 Python tests pass; portable
C++ protocol build/CTest pass. C++ rejects changed return scope, numeric type
substitution and unexpected return mode.

Added asset-free Windows native fixture: return preview/manual agreement/player
context and process restart retry, verifying oldcash/debt39 remains while new
nominalcash18 and addedcharges6/6/6 commit. Exact raw requests and fixture bootstrap
passed in-process against Python with AI disabled; actual Windows execution
awaits CI. Fixed its exact Fraction(0) discount input before push. Exact prior
1a81217 passed both remote workflows. No paid model inference performed.

Actual game hook/screens and guest save/load remain unverified. Returned-player
trade/restructure and season progression remain unsupported.

## October 13, 2026 — Returned-agreement first restructure

The supported first fully-guaranteed-base conversion now applies to returned
agreement generations. New generation_restructure records contain exact agreement
identity and complete before/after generation postings; legacy receipts/events
retain their original view. The old closed agreement's cash, birth terms and cap
debt are untouched. Bonus-layer collision checks include every archived agreement.
Canonical dates/types, floors, chronology and final access checks remain binding.

Native manual_restructure requires an explicit generation_id on returned
agreements, resolved inside the transaction after historical receipt lookup. The
response echoes that ID and C++ validates matching original/amended cash records.
Legacy retries remain valid after a later return. Review found present-null IDs
could commit legacy operations before native rejection; field-presence validation
now rejects null/boolean/empty inputs without changing state.

All 403 Python tests and portable C++ build/CTest pass. Exact example: old retained
charge39 plus new5/5/5 base+bonus3, after paying the newbonus3 and converting4,
team charges become127/3,22/3,22/3. Oldcash39paid9 and newnominal18paid3 remain.
Tests and independent audit verify partial convertedbonus payment/release, source
corruption, duplicate oldlayerID rejection, rollback, restart and old retries.
Raw Windows fixture requests/bootstrap pass in-process with AI disabled; native
Windows execution for this new amendment fixture awaits CI. Synthetic money
audit passes 5,050 bonus-conservation cases; its scope labels no longer call all
durable restructures unimplemented.

Prior 80f73ab passed both workflows. Franchise CI38495870335 logs confirm397tests
on Windows/Ubuntu and actual asset-free native Windows return preview/agreement/
old debt/restart fixture success. This is pipe/runtime evidence, not game evidence.
Actual guest hooks/assets/save/load, returned-player trades, other amendments and
season progression remain unfinished.

## October 13, 2026 — General generation-aware assignments

Supported sourced preseason trades now move returned/assigned agreements and
receive players back at a former club. Each versioned receiver gets an assignment
identity from a distinct tagged four-element hash input, with immutable source
club/agreement ancestry. Both clubs keep prior cash, terms and retained debt.
New assignment origins support subsequent first restructure/release/payment and
canonical historical lookup. Custom source transfers require explicit destination
cash identity before mutation. Legacy snapshots and requests stay compatible.

Paired generation_trade_out/in records validate full before/after generation
postings and source/current/previous receiving identities. Two journals and
ownership commit atomically; affordability, final access and second-insert
failures preserve both books. Native manual_trade binds explicit source/previous
IDs, echoes the new receiver ID, and C++ checks matching cash, paired plans and
nominal conservation. Review caught explicit legacy→virgin IDs committing a
legacy receipt; explicit identity mode now creates a versioned receipt and retries
identically. Null source and malformed parent IDs reject before money changes.

All 415 Python tests and portable C++ build/CTest pass. A release39→return18→B→A
sequence conserves57 combined nominal cash, retains oldcash39 and settledreturn3,
and adds receivingbase15; final A charges47,5,5. Subsequent conversion/release
retains both older debts. Independent audit verifies paired source tampering,
atomic rollback/ancestry and historical retry nonmutation.

New Windows fixture trades the paid/converted return agreement: oldcash39paid9
remains, paid sourcebonus7 stays with seller, receiverbase11 is unpaid, and total
nominalcash remains57. Exact raw bootstrap/requests pass in-process with AI off
and retry; actual native Windows execution for this trade fixture awaits CI.
Fixed a C++ synthetic payment-array initializer before delivery. Prior11a36be
passed both workflows; CI38496520586 confirms403tests on Windows/Ubuntu and
actual native returned-restructure/olddebt/restart fixture execution.

Actual game hooks/assets/save/load, consideration and unsupported trade/contract
protections, season progression and final playable delivery remain unfinished.

### Generation assignment audit and Windows verification (2026-10-13)

Commit 60c54b4 passed Build check 38497901990 and Franchise AI checks
38497901974. Windows ran all 415 tests and executed the native generation
assignment fixture with separate receiver agreement, retained debt and restart
retry. Ubuntu also passed all 415 tests. These are synthetic pipe/service
checks, not execution of the retail game.

The repeatable money audit now independently constructs release, return,
assignment and assignment back to the former club. Expected former-club cap
is 47/5/5; original retained cash 39 plus returned bonus 3 plus receiving
base 15 preserves combined nominal cash 57 and paid cash 12. Three distinct
agreements survive; retrying the earlier trade leaves current ownership and
all agreement snapshots unchanged. The audit passes, including 5050 bonus
conservation cases. Real game import, posting and save/load remain gated.

### Native lifecycle receipt capacity (2026-10-13)

Measured a real source-level transport failure using synthetic 53-player books:
30 released agreements produced a 70,171-byte receipt against the native
65,536-byte limit. Previously these operations could commit before the native
client rejected the reply. Release, paired trade and restructure now run an
optional exact receipt validator inside the Store transaction, before final
connection/deadline checks and ownership/event writes. The native Bridge checks
the full JSON reply including envelope, escaping and newline and reports
response_too_large without mutation. Historical retries validate their original
receipt and never restore historical ownership. Direct engine receipt shapes
and existing event serialization remain unchanged.

Six new tests cover all three Bridge operations, exact frame boundary, realistic
53-contract overflow, byte-identical rollback, identity-bearing trade receipts,
historical retries and serialization before final access. All 421 Python tests,
portable native C++ protocol checks and the repeatable money audit pass. Compact
transaction receipts/paged reconciliation remain necessary for long franchises;
the guard prevents unreadable commits but does not expand protocol capacity.
No game execution or save/load evidence is implied.

### Windows capacity rejection fixture (2026-10-13)

Added an asset-free native smoke mode for an oversized lifecycle receipt. The
Windows fixture builds a sourced cash record larger than the pipe capacity and
runs the release request through two independent native client/sidecar processes.
It requires a bounded response_too_large reply, stable request identity, identical
repeated error, byte-identical SQLite file, retained ownership and unchanged
financial/cash totals. The exact raw C++ request was exercised locally through
Bridge twice with unchanged database bytes; portable protocol checks pass.
The new Windows process execution awaits CI and is not yet claimed verified.

### Compact native lifecycle receipts (2026-10-13)

Added opt-in receipt_format target_v1 to manual release, paired trade and first
restructure. Financial receipts retain all annual team cap charges, revision
and full ownership list, with only the target lifecycle archive. Cash retains
the allocated target record, team totals and a counted aggregate for every other
obligation. Python verifies projection against full source cash; C++ binds target
cash to the archive and uses checked arithmetic to reconcile target plus others.
Exact mode echoes, strict shape checks and corrupted totals/type/identity/mode
cases prevent accepting partial summaries as full receipts. Full event payloads,
checkpoint replay and historical transaction identities remain unchanged.

All 427 Python tests, portable native protocol checks and money audit pass.
Six Python tests cover all three operations, invalid projections/modes, a
53-player long franchise, generation-aware trades back to former clubs and
historical retry without ownership restoration, plus returned restructures.
The exact new Windows fixture after 30 prior releases produces a 2915-byte
Python reply (full team receipt exceeds 64 KiB), preserves cap 429m/88m/88m
and cash 605m nominal/477m paid. A temporary native C++ harness accepted that
actual Python reply. New Windows process execution remains pending CI.

The previous 01dcf17 Windows CI 38498584782 succeeded: 421 tests and the actual
native oversized lifecycle rejection/restart fixture passed. No retail game
execution, guest write or save/load evidence is implied by either fixture.

### Compact cash identity and settled history (2026-10-13)

Audit found that matching target/archive cash records alone did not bind a
compact release to its original cash identity. Python and native release checks
now require the original allocated cash record, canonical legacy or generation
identity, matching settled identity/player, unchanged paid amounts and payment
components, and nominal liability no greater than the original. Compact legacy
trade checks bind all original/seller/buyer cash records to contract:player,
conserve nominal cash exactly and preserve seller payment history. The same
trade helper also checks versioned assignments without changing receipt shape.

All 429 Python tests and portable native checks pass. Added 16 native corruption
cases that alter both wire and archive records, plus a valid returned release.
Python cases cover original identity/player/payment/component/amount corruption
and a returned release preserving old cash39 plus new cash8 and team cap47.
The rebuilt C++ harness still accepts the actual 2915-byte Python receipt.
The earlier compact Windows run 38498978074 was still live when checked; no
restart or new Windows execution is claimed here. Retail runtime/save gates
remain unresolved.

### Bounded release-history replay measurement (2026-10-13)

Added tools.benchmark_replay --release-history for a fixed 53-contract,
30-release fixture. It independently verifies cap422m/92m/92m and cash606m
nominal/477m paid/129m unpaid, then measures five reads and five compact
historical retries. Full receipt71346bytes vs compact3043bytes; retries must
preserve both canonical generation snapshots and exact database bytes. Fixture
construction is timed separately. --generation-checkpoint measures format4
without weakening reconciliation; the prior dialogue benchmark remains usable.

Local Mac sample: format3 median read56.46ms/max72.42ms and retry56.83ms;
format4 median read132.61ms/max138.96ms and retry122.31ms. Build743.58ms
and844.04ms respectively; checkpoint migration153.84ms. These measurements
show compact transport does not remove replay cost. They are synthetic local
figures, not Windows/Deck or game-frame acceptance. Both modes and the prior
2-team/zero-story mode executed successfully with internal financial assertions.

Windows CI38498978074 for5f0b472 completed successfully:427tests on Ubuntu
and Windows; native compact long-franchise cash reconciliation/restart fixture
executed on Windows. Later cash-binding CI38499239068 was still live when
checked. No retail gameplay or guest save/load evidence is implied.

### Profiled cash serialization cost (2026-10-13)

Profiled the fixed release-history format4 benchmark:215668 calls to
CashObligation.to_dict consumed2.319seconds cumulatively through recursive
dataclasses.asdict. Cash records contain immutable strings/integers and optional
immutable component tuples. Direct field serialization now preserves the exact
legacy dictionary/key order and omission rules, creates fresh component lists,
and avoids redundant recursive copying. No reconciliation/checkpoint validation
is skipped; no persistent cache is introduced.

Same profiled workload retained215668 serialization calls but their cumulative
time fell to0.066seconds; complete profiled workload6.893s to3.871s including
fixture construction. Unprofiled sampleformat4 medianread105.30ms and retry
105.20ms; format3 medianread60.26ms/retry52.68ms illustrates timing noise and
remaining replay costs. Full/compact receipts remain71346/3043bytes. Eighteen
independent comparisons against the old dataclass serializer produced identical
JSON and verified output component mutation cannot alter immutable records.
All429 Python tests and money audit pass. These are local synthetic measurements
with profiler overhead, not game-frame, Windows or Deck acceptance.

### Reuse validated agreement identities in component checks (2026-10-13)

Profiling showed _check_cash_components called generation_agreements, which
validates complete archive-map coverage and canonical identities, then revalidated
each same identity through generation_cash before the same cash-record lookup.
Component checks now use the already-validated immutable agreement cash ID.
Each Store call operates on a fresh local replay/write ledger; no cross-read
cache, shared mutable ledger or skipped component ceiling check is introduced.
Missing cash still rejects, and checkpoint/source replay remains unchanged.

Independent read-only review and37 focused corruption/archive/cash tests passed.
All429 tests and money audit pass. Fixed profiled workload retains1364 component
checks while canonical identity checks drop147108 to74816; component cumulative
time1.625s to0.925s and total profiled workload3.871s to3.330s. Unprofiled
format4 readmedian96.81ms/max110.51ms and compactretrymedian110.57ms; replies
still71346/3043bytes and exact database state is preserved. Timing is local
synthetic evidence, not game-frame/Windows/Deck acceptance.

Cash-binding commit fbe9e80 passed Windows/Ubuntu429tests and native compact
long-franchise reconciliation/restart fixture in CI38499239068. Later source
changes still need their own CI; actual game/save gates remain unresolved.

### Sourced promise circumstances for later negotiation (2026-10-13)

Added frozen PromiseCircumstances with player/team/window/mode, nullable total/
available/injury-unavailable/coaching-DNP counts, source/coverage/completeness
and an explicit reason for unknown counts. Bounds preserve availability/injury
disjointness and coaching-DNP subset membership without classifying missing
causes or converting unknown values to zero. Optional format1 promise-score
events persist context alongside unchanged raw achievement, with exact field/
type replay checks and stable retries. Legacy event/result shapes remain intact.
Typed performance recording checks player/team/window/mode before committing;
replay validates declared sources, not an independently saved raw collector
snapshot. That boundary is documented in docs/promise-circumstances.md.

Recorded promise_history already feeds later Negotiation model context. Prompt
guidance now uses sourced circumstances with saved priorities, retaining unknown
coverage and avoiding inferred fault, altered targets or automatic trust/money
effects. An actual scripted provider test sees injury4/availability12 alongside
unchanged achievement1/2 and trust0.6 after persisted score, release, format4
migration and return negotiation. Context-aware consequence policy, real game
capture and in-game display remain unfinished.

All437 Python tests, portable native protocol checks and money audit pass.
Eight new tests cover bounds, unknowns, foreign/duplicate windows, mode mapping,
strict replay tampering, stable retries/legacy shapes and provider delivery.
Independent read-only review passed24 focused cases with no concrete regression.
Replay optimization13031b5 also passed CI38499740729. New context Windows
execution remains pending CI; no retail game/save/load evidence is claimed.

### Native promise circumstance validation and restart fixture (2026-10-13)

Native player_context now validates optional circumstance history records: exact
12-field schema, requested/history player and requested team binding, scored
windows, unique nonempty context windows, declared mode, strict nullable counts,
source/coverage/reason/completeness and overflow-safe disjoint/subset bounds.
Legacy histories remain compatible. Added valid known/unknown native fixtures
and18 corruption cases including bool counts, duplicates, foreign identities,
missing team, unexpected fields and INT64_MAX count overflow.

The new Windows smoke mode and source fixture persist interim unknown eligibility/
coaching counts followed by final known availability/injury context. Two native
processes must read identical context, rawfinalscore1/2, unchangedtrust0.6,
cap20 and byte-identical database state. Exact fixture construction/request
passed locally through Bridge; a rebuilt portable C++ harness accepted its actual
Python reply. All437 Python tests and portable native protocol checks pass.
The new actual Windows process execution awaits CI. Prior promise-source CI
38500341337 was still live when checked; no retail game/save evidence is claimed.

### Bound model context before inference (2026-10-13)

VertexProvider now requires finite object context and checks the exact serialized
escaped UTF-8 JSON against a default1MiB context limit before calling the SDK.
An explicit positive integer constructor option can change that limit. Oversized
contexts reject without inference or silent removal of story history; existing
output/deadline/retry controls remain intact. The limit is context bytes, not
an estimate of token cost, total SDK request size or inference frequency.

Two new tests verify exact escaped-byte boundary, bool/invalid limits, oversized/
NaN/nonobject/unserializable input with zero SDK calls, unchanged finances when
negotiation fails and successful manual cap-enforced signing afterward. All439
Python tests pass. Tests use fake SDK calls; no paid cloud request or new
authorization was used. Story memory reduction and cost telemetry remain open.
Promise-context commit2a27925 passed CI38500341337; new native context
fixture and latest provider changes still need their own Windows execution.
Retail game and actual save/load gates remain unresolved.

### Safe provider usage metadata diagnostics (2026-10-13)

Verified official Google GenerateContentResponse UsageMetadata and installed
google-genai fields before implementing a bounded last-completed-call snapshot.
It captures model/contextbytes/SDKattempt/fixedoutcome and six optional token
counts, with unknown invalid/missing values preserved as null and no inferred
cost. Blocked/incomplete replies retain reported usage; SDK/preflight failures
clear stale counts. Per-call local state publishes once in finally, preventing
interleaved counters; callers receive a deep copy. No prompt/player/modeltext/
credential/errorbody is retained, no extra model call or retry introduced.

Three new tests cover known/unknown/invalid usage, blocked replies, failures and
copy isolation plus overlapping SDK calls with controlled completion order.
InstalledSDK typed metadata also passed an offline fake-response check. All442
Python tests pass; independent review found no concrete defects and reran10
provider tests. This is diagnostic capture, not durable billing or per-decision
attribution; costs, frequency/spend controls and pricing remain unfinished.
Context-preflight commitc2cc1f1 passed CI38500823733. New diagnostics need
their own CI; no paid inference or retail game/save validation occurred.

Completed CI38500823733 logs also verify the native Windows sourced promise
circumstances/unknown counts/raw score/restart fixture, with439tests passing
on both Windows and Ubuntu. This remains synthetic service/client execution.

### Offline seeded-personality continuity scenario (2026-10-13)

Added examples.personality_continuity and included it in the existing Windows/
Ubuntu offline examples CI step. A bounded16-ID authored fixture selects two
seeded players before create_franchise. Both receive the same observed50
receptions/700yards, unknown targets/pressures and identical offers. The scripted
provider explicitly checks saved priorities and observed inputs: first-round
counters20/30 differ, and the second identical20 offer produces one signing and
one rejection through remembered counter history. Synthetic cap100 retains
charge20/room80. Money units and choice rules are authored fixtures, not NFL
rules or a live-model decision mechanism.

The same explicitly authored +0.05 trust consequence is sourced to each saved
first-round counter. Restart preserves priorities, stories and trust0.55. A
second restart recalls all four replies with a provider that fails if called;
exact generation state, ownership and database bytes remain unchanged. Four
scripted provider calls, zero live calls, zero calls during recall. The scenario
executed successfully locally. Narrative round labels do not advance an actual
game week; live-model variation and guest calendar/save validation remain open.
Usage-diagnostic commitf7afca8 passed CI38501237122. New example execution on
Windows still awaits its own CI; no retail gameplay or paid inference claimed.

### Root game integration audit and C host adapter (2026-10-13)

Audited actual root config/game.cmake and src/main.c: no franchise-client
linkage/lifecycle/guest transaction calls exist yet. Build check configures
NFL2K5_BUILD_GAME OFF. Generated guest code is present (38tracked files);
retailXBE/rawsaves/Windowsdeps/build-generated function ranges are distinct
missing inputs. Updated stale nested-remade references in integration guidance
and added explicit unfinished actual-host linkage work. No financial offsets or
calling conventions were guessed from unrelated roster/overall patches.

Added a single-owner opaque C ABI around existing PipeClient, Windows static
library and plain-C fixture. Staticstatuses contain exceptions; boundedsubmit,
nonblockingready and cachedsize-query/short-buffer take preserve responses.
Successfulhello is required before AInegotiate; disabled/failedhello/transport
failure clears the grant. Serverstillrechecksaccess; manual/read calls remain
independent. No actual main/config game hook or guest memory write is added.

CheaderC11 strictsyntax and existing portable protocol build/CTest pass. Exact
Cfixture JSON requests passed locally through Bridge twice with stalepreview
rejection and identical manualsign/context, charge10/revision1. CI will build
and execute the plain-C client against that synthetic DB; Windows execution
is pending. Independent review found no concrete CABI defect. Existing blocking
transport write precedes its response timeout; shutdown is not yet an
unconditional bound against a nonreading peer. Actual game-host lifecycle,
franchise hooks, save/readback and gameplay remain unverified.

### Native stalled-peer shutdown (2026-10-13)

C host adapter Windows validation completed successfully in run 38503080961.
Changed PipeClient destruction to close its kill-on-close job before joining
the worker, while retaining parent pipe handles until the worker finishes.
This addresses a nonreading sidecar blocking synchronous WriteFile before
the response deadline. Explicit 4096-byte pipe buffers and a Windows CTest
fixture fill stdin, submit another frame, destroy the client and verify child
exit. CTest has a 20-second timeout to catch a hanging destructor. Portable
protocol checks pass; the new Windows regression is pending CI. No guest
transaction, gameplay, or save/load validation is implied.

### Host lifecycle work in progress (2026-10-13)

Run 38503588940 passed Windows/Ubuntu checks for c16ce25, including the first
stalled-peer shutdown fixture. A stronger fixture at 04cfe1f proves write
stall beyond the read deadline; CI remains pending. Review identified inherited
pipe-handle leakage between concurrent child launches: the constructor must
restrict inheritance with HANDLE_LIST alongside JOB_LIST before claiming robust
shutdown ownership. This is the next transport fix.

Uncommitted root host lifecycle wiring is drafted behind an OFF-by-default
CMake option and explicit vertex/Python/database environment configuration.
The shared C startup source is included in the asset-free Windows C fixture,
with disabled/invalid-provider/missing-path cases and idempotent cleanup.
Strict portable C syntax checks and protocol CTest pass; Windows compilation
and root game execution remain pending. No guest hooks or automatic AI grant.

### Restricted child inheritance and opt-in root lifecycle (2026-10-13)

Added HANDLE_LIST alongside JOB_LIST, with explicitly duplicated inheritable
stderr or NUL fallback. Temporary child handles close on setup/launch failures
and success. Stalled-peer fixture now checks an unrelated inheritable event
was excluded before exercising the blocked-write cleanup. Windows CI pending.

Reviewed and linked root host lifecycle behind NFL2K5_FRANCHISE_CLIENT=OFF
by default. Explicit vertex-only runtime paths launch immediately before guest
entry; normal return, crash and atexit clean up. No automatic handshake or
model call, fixture fallback, guessed guest addresses or guest writes. Same C
source compiles in asset-free native fixture with off/invalid/missing-config
cases. Portable strict C syntax and protocol CTest pass. Independent review
found no concrete lifecycle defect. Actual root build/runtime remains gated.

### Strengthened shutdown validation (2026-10-13)

Windows and Ubuntu run 38503835760 passed for 04cfe1f. The Windows
fixture establishes an actual blocked write by retaining a pending request
beyond the five-second response deadline, then verifies owned child exit.
This validates shutdown ordering; it does not yet validate the later
HANDLE_LIST sentinel or lifecycle source introduced in fb11725. That exact
revision is running in 38504026771; keep polling the same job.

### Host source and handle isolation verified on Windows (2026-10-13)

Exact revision fb11725 passed run 38504026771 on Windows and Ubuntu.
Windows compiled the actual shared lifecycle C source, passed both native
CTest cases (including inherited-event exclusion and blocked-write shutdown),
and completed the plain-C adapter/configuration checks and durable synthetic
restart fixtures. Marked transport shutdown complete; root lifecycle integration
remains open until an actual game build/execution is verified. No game assets,
guest save transactions or paid inference were involved.

### Positive host lifecycle regression (2026-10-13)

Added a Windows CTest using the actual game-host startup/cleanup C source
and an inert owned executable in place of Python. Explicit vertex-mode
configuration starts the child, a second start refuses replacement, repeated
stop is safe, and a later start/stop succeeds. This performs no handshake,
model request, game memory access or paid inference. Portable protocol checks
pass; the new Windows lifecycle execution is pending CI.

### Money audit report freshness (2026-10-13)

Re-ran tools.audit_money successfully. Updated the main money report's lead
with current supported durable cap/cash/ownership/lifecycle evidence and explicit
remaining season/guarantee/posting/game gaps. Preserved early findings under
historical headings so obsolete persistence/cash/assignment descriptions cannot
be mistaken for current coverage. No financial behavior changed.

### Local inference-rate admission (2026-10-13)

VertexProvider now defaults to 20 attempted SDK calls per rolling 60 seconds,
with positive integer constructor configuration, monotonic expiry and locked
concurrent admission. Failed/blocked attempts consume slots; malformed/oversized
contexts and rate denials submit nothing. Denials retain existing preflight
usage semantics, and introduce no waiting, retries or automatic AI re-enable.
Boundary tests cover failed-attempt retention, rejection at 59.999 seconds,
expiry at exactly 60 and invalid configuration. All 444 offline tests pass.
This remains process/provider-local, not durable spend/account enforcement;
restarts and separate draft providers have separate windows.

### Concurrent rate admission and host restart evidence (2026-10-13)

Run 38504383690 passed the positive Windows host lifecycle CTest for
2ed242a: actual shared C startup source can start an inert peer, refuse live
replacement, stop twice and restart without any model request. Root game
execution remains unverified.

Added meaningful rate regression checks: an in-flight SDK call reserves the
only slot across threads; rejected admission reaches no second SDK call,
leaves negotiation finances unchanged and preserves legal manual signing.
All 14 focused provider tests and all 446 offline tests pass.

### Durable rollover source review (2026-10-13)

Reviewed current replay, chronology, ActiveContract, GenerationAgreement and
cohort assumptions with a parallel agent. Recorded concrete blockers and ordered
implementation in docs/season-rollover.md. Budget replacement alone cannot
advance the year; original payment indices and prior transaction plans must
remain immutable. Calendar/projection anchors and an atomic common league event
are required before changing financial state. Rollover remains unimplemented;
no new season, game transaction or future cap value is claimed.

### Initial league calendar anchor in progress (2026-10-13)

Implemented common all-team calendar_anchor events with complete coverage,
expected revisions, source/year agreement, immutable membership and idempotent
retry. Replay checks peer records and binds dated transaction/projection checks
to the declared year. Cap/cash untouched; revisions advance once. Six focused calendar tests pass, including format4 migration in both orders,
exact posting types and sourced-year rollback. Independent review found boolean
posting forgery through Python equality; canonical JSON hashes now reject it. Actual rollover/projection/expiry remain unfinished.

All 452 offline tests pass for the reviewed calendar-anchor implementation.

### Calendar-backed agreement projections in progress (2026-10-13)

Added actual-store calendar_projection using validated league replay and immutable
generation schedules. Forward views preserve original payment indices, closed
payment ceilings and nominal cash; scheduled term completion does not imply
settlement or expired ownership. Tests verify persisted state bytes unchanged,
future charges, unpaid cash past scheduled term, and released layered obligations
without resurrecting cancelled bases. Focused tests pass; full suite/review pending.
No season transition or actual guest state change occurs.

Projection review found no concrete defect. Added next-year post-June release
debt and paired assignment coverage: seller bonus debt remains separate from
buyer base schedules, with cash and payment rights unchanged. Independent
layered/elapsed-year examples also passed. All 455 offline tests pass.

### Owner-funded normal payroll policy (2026-10-13)

Recorded user direction in docs/payroll-funding-policy.md: normal payroll uses
owner funding, requiring no revenue tuning or artificial bank-balance gate.
Owed/paid cash remains accurate compensation history, separate from cap/rookie
legality. Exceptional severe-mismanagement distress is explicit optional scope,
never inferred from losses/missing revenue. Updated negotiation/draft prompts
and the worklist to preserve this policy through settlement and rollover.
Current cash ledger has no revenue/bank-balance gate. Provider tests and money
audit pass; financial transaction code and compensation amounts are unchanged.

### Calendar Windows validation and rollover payroll boundary (2026-10-13)

Windows/Ubuntu run 38505171414 passed calendar anchoring at c8d09f3.
Subsequent projection/payroll revisions remain in existing live CI runs; no
restart was requested. Recorded owner-funded normal payroll in rollover closing
requirements: there is no revenue gate, but funding cannot silently become
allocated paid salary. Unpaid cash must survive source reconciliation.
Parallel implementation is preparing typed current contract views around
immutable agreement schedules; authoritative expiry/rollover remain open.

### Typed agreement calendar views and closing inspection (2026-10-13)

Parallel implementation added a frozen calendar view separating immutable
agreement economics from a derived active contract cursor. Schedule completion
alone is not authoritative expiry; explicit eligible sourced full allocated cash
settlement is required even for a validation view. Root calendar_projection now
consumes the typed view, preserving its legacy output. Added closing inspection
for recorded outgoing-year bases/unpaid cash with no revenue gate, invented
payment or ownership grant. All 462 offline tests pass.
Stabilized parallel source includes component-by-component expiry settlement
checks and six focused immutable-view tests. Additional stored closing coverage
keeps unknown allocations unknown and fully paid scheduled expiry unapproved.
Actual atomic season advancement remains unimplemented.

### First atomic veteran-only league-year transition (2026-10-13)

Implemented real Store year_transition events spanning every anchored team under
one write transaction, with exact shared inputs and before/after cap/cash/calendar
replay. Ledger calendar views preserve immutable agreements and allocated cash,
age surviving obligations and archive explicitly eligible fully settled expiry.
Inputs require sourced next budgets/minimums and explicit closing exclusions;
rookie/draft unresolved state rejects. Normal payroll has no revenue gate.

Independent review found stale legacy context after rollover; format2 calendar
context now separates current views from archives, and unsupported legacy reads
reject. Four durable Store tests pass across two teams/two transitions, explicit
intervening payroll, retained debt, expiry, unchanged cash, restart/retry, rollback
and tamper. All 471 offline tests pass. Postroll contract mutations/native calendar
context remain guarded unfinished work; no guest gameplay/save proof is claimed.

Upstream master has three new commits (d76949a,790d064,e3262f4) touching
main host/recompiler/CI. Preserve this validated source before merging them and
reapply opt-in host ownership to the refactored entry/cleanup paths.

### Merge three upstream cross-platform commits (2026-10-13)

Fetched and merged upstream master d76949a/790d064/e3262f4 while preserving
fork ancestry. Resolved the rewritten main.c conflict using upstream's host and
reapplying our opt-in startup/normal-return/crash cleanup calls. Preserved all
reviewed franchise work before merging. Recompiler gitlink c0ba4e7 is checked
out; corrected stale revision-file pin 13175b7 to match it.

Guarded Windows-only root tool targets for the new Linux runtime CI and made
NFL2K5_BUILD_GAME=OFF explicit with accurate runtime/tool job labels. The Win32
franchise pipe option fails clearly on native POSIX builds; Proton Windows route
remains the intended Deck delivery. Actual game compilation/playability and
Linux runtime CI remain unverified. Runtime symbol check reports33 referenced
functions resolved; portable protocol CTest and all471 offline tests pass.

### Merged CI dependency failures and calendar wire context (2026-10-13)

Build run 38506837822 failed: Windows lacked SDL3Config.cmake and Linux
Ubuntu24.04 could not find libsdl3-dev. Published c9e5d54 to build official
SDL3 3.2.20 at exact source96292a5b464258a2b926e0a3d72f8b98c2a81aa6
for both jobs; retained exact source license/attribution. Verification pending.

Added explicit calendar_v1 contract context routing, matching Store anchor year
and native format2 validation. Parallel validator checks layered surviving,
expired and released golden contexts plus23 corruption cases. Real Python
Bridge replies for current/expired agreements validated through portable C++.
AI-off wire test preserves DBbytes and rejects unknown/legacy advanced-calendar
formats. All472 offline tests and portable CTest pass. Added Windows pipe
fixture for two agreement contexts across two process restarts; execution pending.
Actual game UI/save integration and postroll contract mutation remain unfinished.

### SDL3 provisioning succeeded; recompiler compile repairs (2026-10-13)

Run38507040131 now builds/installs SDL3 on both platforms. Runtime compilation
then exposed Windows kernel SDL3 include propagation and Linux GNU register,
Windows include and mapping-registry prototype errors. Created an attributed
GitHub fork cosmokay1/xboxrecomp and preserved all upstream notices/ancestry.
Published c2bd146 on codex/platform-build-fixes with narrow source/CMake fixes,
including removal of an include-only renderer from standalone translation units.
Updated root submodule URL/branch and revision pin consistently. Actual platform
compile verification is pending CI; no game build or render behavior is claimed.

### Quarterback-hit investigation scope (2026-10-13)

Added quarterback hits alongside pressures by user direction. Investigate actual
contact, pass-release timing, defender/QB attribution, sack overlap, multiple
defenders, penalties/nullified plays and episode deduplication. Hits remain a
distinct observed counter, not inferred from pressures or sacks. Played/CPU/fast
sim coverage must be verified separately; unavailable counters remain unknown.
No game counter capture or new metric implementation is claimed.

### Windows verification and never-held postroll veteran signing (2026-10-13)

Windows run 38507267705 passed native calendar_v1 current/expired contexts
across process restart. Build run 38507497961 passed the Windows runtime/tools
build with pinned SDL3 and recompiler repairs; Linux still fails on GGL Windows
include/dependencies. Actual game execution remains unverified.

Implemented current-year signing for never-held registered veterans while
preserving historical re-signing guards. New agreement calendar anchors follow
actual signing year, and later close/aging uses per-agreement anchors. Durable
store tests verify actual2027birth→2028year1 beside older2026birth→year2,
explicit payments, retained charges/cash, retry/restart, cap/floor rejection and
typed calendar tamper. Earlier unmarked postroll cash history remains compatible
with exact monetary replay. Independent review found no defect.

Linux GGL header/TLS/diagnostic portability edits are local in the dependency
fork; its actual SRW condition-variable wait remains to implement. Preserve real
lock behavior and avoid synchronization stubs or disabling the guest lock.

All 478 offline tests pass for postroll signing and payment compatibility.

### POSIX guest-lock condition waits (2026-10-13)

Published dependency fork revision 830df0a with real pthread condition waits for
shared/exclusive SRW locks, atomic release/wait coordination, original-mode
reacquisition and Windows timeout errors. Guest-lock source now uses portable
thread-local/platform includes and guards Windows-only diagnostics. Local source
syntax and the standalone regression passed: 500 immediate wake cycles, eight
concurrent shared waiters, broadcast, timeout and invalid-flag lock retention.
SwitchToThread performs sched_yield and conservatively returns false because
POSIX does not report an actual thread handoff. Linux CI now runs this regression
before the full runtime build. New pinned-revision CI remains pending; these checks
do not establish game execution, Windows/Deck playability or franchise save/load.

### Pressure and quarterback-hit source triage (2026-10-13)

Inspected the broadcast boundary, copied player totals and native-popup forwarding.
The current sack presentation event carries no play/defender/QB identity or final
penalty disposition; it is insufficient for franchise attribution. No pressure
or hit field exists in that boundary, which does not establish engine absence.
Added docs/pressure-investigation.md with concrete contact, overlap, nullification,
mode-coverage and save/load capture requirements. No counters or offsets invented.

### Linux regression link repair (2026-10-13)

Build run 38508724986 stopped while linking the POSIX condition regression:
feclearexcept required libm. Dependency 11c7dea propagates libm from the platform
target; local configure/build/CTest passes. Full Linux runtime was not reached.
Separate local pushbuffer inspection found a Windows-only include, missing barrier
and three SEH guards; its experimental include/atomic publication changes remain
uncommitted pending a genuine POSIX fault-handling solution and full validation.

### Pushbuffer fault-boundary review (2026-10-13)

Independent review identified three SEH guards in nv2a_pb_exec.c: rendering
(vertex/texture reads, output writes and GPU calls), attribute carryover reads,
and guest texture-header diagnostics interleaved with fprintf. Broad signal/jump
replacement could abandon renderer/CRT locks; main.c already owns SIGSEGV for
APU MMIO and chains its prior handler. Do not substitute no-op SEH macros.
The compatibility VirtualQuery mapping registry does not establish actual page
protection. A Linux solution needs bounded guest-memory leaf access and audited
render writes/staged inputs, preserving Windows SEH; it is not a syntax-only fix.
Experimental portable include and atomic environment-cache publication remain
uncommitted. The actual extracted cache function, linked against the real platform
library, passed eight threads with 100,000 present/absent lookups each. Full source
syntax still fails on the SEH guards and an inconsistent volatile extern. This
limited check does not validate rendering. Build 38509009926 and franchise38509009927
were confirmed live on 0dd21e9; no jobs restarted on an observation timeout.

### Confirmed Linux lock regression and bridge compilation (2026-10-13)

Completed Linux job115672968433 on run 38509009926 passed the real POSIX lock
regression after libm linkage. Full runtime then failed in nv2a_pb_exec.c's
Windows include, xbox_memory_layout.c's AC97 Windows exception context, and
kernel_bridge.c's Windows timer constant. Published dependency215f8f8 keeps
Windows high-resolution creation intact and uses the existing real POSIX timer
on other hosts, without claiming equivalent wake accuracy. Portable explicit
ASCII .uh suffix matching removes a Windows CRT comparison dependency.
The complete bridge source now passes local Clang syntax with official pinned
SDL headers. Remaining runtime faults are not masked or disabled. Windows job
was still live at observation; franchise checks were also still live.

### Windows inheritance sentinel identity correction (2026-10-13)

Runtime build38509009926 Windows job passed (runtime/tools only). Franchise
run 38509009927 failed stalled_peer_shutdown immediately with Sidecar disconnected;
protocol and host-lifecycle checks passed. Review found the fixture rejected any
valid child handle with the parent's numeric value, which can be reused by child
startup and does not establish inherited object identity. The fixture now attempts
SetEvent on that candidate and the parent retains its original nonsignaled event
through acknowledgement/stall establishment, rejecting actual signaling of that
object. Scoped RAII closes the sentinel on success or failure. Production handle
allow-list and owned-job shutdown behavior are unchanged. Local portable protocol
CTest passes; Windows-only fixture compilation/execution needs new-revision CI.
No game/runtime playability claim follows from these source checks.

### Inheritance regression positive control (2026-10-13)

Added a real unrestricted-inheritance fixture launch before the PipeClient test.
It must signal the original parent event and exit successfully; the parent resets
that event before exercising the production allow-list and blocked-write shutdown.
This proves the revised signal-based check detects genuine inheritance instead of
merely suppressing a numeric-handle false positive. Control-process observation,
termination on timeout and handle cleanup are bounded. Independent read-only
review found no concrete API/lifecycle defect. Local portable protocol CTest
passes; this Windows-only control still requires exact-revision CI execution.

### Versioned calendar player snapshot store support (2026-10-13)

Store.player_context now accepts explicit calendar_v1 and returns the existing
format2 calendar contract envelope from the same loaded ledger as personality,
relationships and histories. Legacy contract_accounting remains null in this
format; archived economics and current elapsed/charges/ownership stay distinct.
Legacy callers remain unchanged and still reject stale post-roll accounting.
Expired latest generations retain sourced expiry; classified never-held players
receive null contract context. A shared single-snapshot helper also serves the
existing calendar contract endpoint. Focused two-team rollover tests and all479
offline tests pass. Bridge request handling and strict native validation are not
yet wired for this player format; actual game UI/save capture remain pending.

### Calendar player bridge/native boundary (2026-10-13)

Explicit player_context context_format calendar_v1 now selects the store's single
snapshot, remains readable with AI disabled and never invokes inference. Unknown,
null/bool format markers reject; legacy callers retain prior behavior and the
64KiB response gate remains. Native validation reuses the full calendar contract
validator and binds nested team/player/revision to the outer request/snapshot;
legacy requests reject unrequested calendar markers. Corrupt format, identity,
revision, ownership, missing nested context and invalid years reject in portable
C++ fixtures. Actual Python-generated survivor, expired and never-held snapshots
also passed the C++ validator. All480 offline tests and portable native CTest pass.
Windows pipe execution of this format and actual game UI/save integration remain
unverified. Delivery estimate remains approximately25–30percent by scope judgment,
not completed-test counts; verified playable-game acceptance remains unproven.

### Windows sentinel validation and calendar-player pipe coverage (2026-10-13)

Franchise run 38509566991 at7c7f4cd completed successfully on Windows and Ubuntu,
including genuine inheritance positive control and stalled-write child shutdown.
Prior corrected fixture run 38509483351 also succeeded. These validate synthetic
native ownership/shutdown behavior, not guest execution. Extended the existing
Windows calendar pipe scenario with active/expired player_context calendar_v1
requests and saved personality. Both process launches compare replies to exact
store snapshots and retain identical database bytes. Tool syntax and portable
native CTest pass locally; this new pipe scenario awaits exact-revision Windows
execution. No live cloud inference or game assets are used.

### Calendar release dependency audit and documentation refresh (2026-10-13)

Read-only audit confirms the release calculator should consume the advanced
contract cursor with original full salary/bonus/cash indices. Retained dead-charge
schedule must start at the actual release year rather than double-age from its old
anchor. Exact generation/year and financial/cash/generation/calendar postings are
needed for atomic replay. Existing restructure/assignment archive invariants need
explicit calendar-release representation; do not globally unlock dated mutations
or discard supported layers to simplify tests. This remains implementation work.
Verified historical run 38507267705 success live and corrected stale integration
text saying first calendar contract Windows execution was pending. Documented
new player-context format and its pending extended pipe verification separately.

### Linux build failure repair in progress (2026-10-13)

User reported Linux failure. Verified completed build38509871318: Windows runtime
and tools passed; Linux failed on nv2a_pb_exec.c windows.h and AC97 exception
structures in xbox_memory_layout.c. Prior timer constant failure is gone.
Coordinated implementation is in progress: Linux AC97 needs SIGSEGV write faults
and SIGTRAP single-step handling installed before MemoryLayoutInit, with existing
APU MMIO and prior-handler chaining retained. Root dispatcher edits and dependency
hook/test edits remain uncommitted pending isolated real-fault validation.
Pushbuffer audit found unguarded guest accesses beyond the three SEH blocks:
attributes, textures/palettes/DXT, framebuffer reads/writes, SDL presentation and
memory diagnostics. Safe Linux rendering needs exact checked kernel-copy leaves
and batch/row staging, not broad signal jumps, no-op SEH or per-pixel syscalls.
Implementation of checked-copy prerequisites is delegated; renderer integration
and positive textured/framebuffer evidence remain. No passing Linux runtime or
playability claim is made from partial repairs.

### Published Linux fault/copy prerequisites for CI (2026-10-13)

Dependency3b30798 adds real Linux x86-64 AC97 write-fault/single-step hooks,
registration-before-protection checks, unrelated/debugger trap rejection and trap
cleanup. Root main installs both SIGSEGV/SIGTRAP dispatchers before guest memory
initialization and chains the existing APU/prior handlers. Checked guest-memory
copy leaves use exact process_vm_readv/writev results on Linux and leaf-only SEH
on Windows, with guest/host interval checks; failed partial copies are not atomic.
CI now executes AC97 real-fault/reset cycles and protected-page copy boundaries
before the full Linux runtime. These Linux tests cannot run on the local macOS
host and await CI; local existing POSIX lock CTest still passes. Renderer access
staging is unfinished and its experimental changes remain uncommitted. This pin
is prerequisite source validation, not a passing full Linux build or game proof.

### Calendar player pipe verified; vertex conversion underway (2026-10-13)

Run38509950333 completed successfully at11cac7d, including Windows actual native
pipe checks for calendar player snapshots/personality and byte-identical database
restarts. This is synthetic engine transport evidence, not game integration.
Pending pushbuffer edits now use checked Linux attribute copies before decoding
and bound full inline float/short payloads rather than only four bytes. A temporary
fixture compiled the actual fetch_attr source and passed complete float4 decoding,
truncated float4/short4 rejection and maximal offset/index bounds on macOS. Linux
copy-path execution, texture/palette/framebuffer staging and full source compilation
remain unfinished; no renderer patch published yet. Runtime prerequisite CI
38510676691 was confirmed live building SDL at the latest observation.

### Linux prerequisite execution and renderer staging integration (2026-10-13)

Run38510676691 at12ddc36: Windows runtime/tools passed; Linux job115678212845
passed POSIX condition waits, actual AC97 fault/reset/single-step cycles and checked
memory-copy protected-page tests. Full runtime then failed only on the still
published Windows include in nv2a_pb_exec.c. Unpublished renderer work now stages
four texture layouts/palettes, preserves original pitch/swizzle/DXT offsets, uses
host framebuffer rows with dirty-span flush, and stages SDL presentation input.
Checked vertex reads and full inline attribute bounds are retained. Rendering
rejects an unreadable enabled texture batch instead of silently claiming textured
output. Windows SEH remains; Linux draw scopes use the checked leaves/staging.
Diagnostic raw-memory conversions and positive CPU rendering fixtures are still
in progress. This source is not yet committed or claimed compiled/render-tested.

### Linux renderer port published for x86-64 CI (2026-10-13)

Dependency889cbbb replaces Linux raw guest accesses with checked attribute copies,
four texture/palette snapshots, framebuffer staging/dirty row flush, staged SDL
presentation rows and bounded diagnostic copies. Windows SEH/direct-render paths
remain. Failed enabled texture copies skip that batch; partial output failures are
reported without claiming atomicity. Fixed the Linux DWORD/%lu diagnostic parse
mismatch found by review. Actual production CPU renderer fixture passed repeatedly
in an existing offline Linux ARM64 node20 container with read-only mounts, including
textured alpha blending, stage restoration, DXT1, indexed palette, protected/missing
pages, read-only outputs, deferred flush and inline/stride bounds. This validates
CPU staging on that host, not x86-64 SDL GPU presentation or game execution.
Independent review found no remaining Linux raw guest reads in the converted path.
CI now runs the renderer fixture against the pinned official SDL SDK before full
runtime compilation; exact-revision Windows/Linux x86-64 results remain pending.
Framebuffer staging currently has an explicit64MiB host allocation policy, not a
claimed NV2A hardware limit; real game workload/performance remains unmeasured.

### Linux renderer x86-64 passed; decoder include fix and release representation (2026-10-13)

Build 38511707664 at84b9768: Windows runtime/tools passed. Linux condition, AC97,
checked-copy and actual renderer fixture steps passed on x86-64; fullruntime
advanced to nv2a_mmio_hook.c GNU REG_RAX/... definitions missing because the feature
macro came after system headers. Dependency26d96ce moves it before all includes;
local Linux ARM64 syntax passes but that does not exercise the x86 register branch.
Next exact x86 CI remains required.

Added optional release_calendar_year to GenerationAgreement as a prerequisite for
post-roll releases. It preserves economic original/amended contracts and exact
restructure/incoming-assignment archives while separately validating the release
cursor; retained views must anchor at the actual release year. Closed payment
ceilings use that cursor so prior earned nonguaranteed salary is not cancelled.
Absent markers leave legacy snapshots unchanged. Layered, restructured and
incoming-assignment cases plus malformed markers/cursors pass; all483 offline
tests pass. Independent review found no concrete representation defect. Ledger,
Store and native transaction guards remain: exact authoritative cursor binding,
versioned atomic replay and native receipts are still required before enablement.

### Linux framebuffer type include and calendar-release Ledger transaction (2026-10-13)

User reported newest Linux failure. Verified run 38512107234 at889b940: Windows
runtime/tools passed; Linux renderer/fault prerequisite step passed, decoder REG
errors disappeared, full runtime then failed in video/fb_present.c missing ptrdiff_t.
Dependency1b0f3d6 adds explicit stddef.h. Actual offline Linux ARM64 source syntax
passes with one existing unrelated implicit framebuffer-dump declaration warning;
new exact x86-64 full-runtime CI is still needed.

Ledger.apply_calendar_preseason_release now requires the exact current owned
generation and authoritative current contract/year. It computes the full existing
healthy veteran release plan, cash/charge replacements, immutable calendar archive
and reanchored view before mutation. Prior-year transaction dates remain valid
chronological history; wrong current year still rejects. Legacy release API still
rejects advanced-calendar mutation. Tests preserve earned base indices, nominal
cash, archived terms and one-time dead-charge aging across a subsequent rollover,
plus reject malformed/stale/foreign inputs without changing snapshots. Independent
review found no concrete Ledger defect; all485 offline tests pass. Store atomic
calendar-release events/replay and native receipt formats remain unimplemented;
this method is not yet exposed through the game/service transaction path.

### Runtime CI green and durable calendar-release Store support (2026-10-13)

Run38512445923 at5b5ade2 completed successfully for both Windows and Linux runtime/
tools, including Linux condition, AC97, checked-copy and CPU-renderer fixtures.
This resolves observed source compilation failures; NFL2K5_BUILD_GAME remains OFF,
so it does not establish game linking/execution, SDL GPU presentation or save/load.

Store.release_calendar_preseason_veteran now commits a distinct versioned event
with exact current generation and canonical before/after financial, cash,
generation and calendar snapshots. Strict payload fields, integer formats,
canonical dates/rates and exact hashes reject tampering/downgrades. Ownership
removal, final access check and receipt check are in the existing atomic write
transaction; failure preserves the database. Historical retries remain stable after
another rollover. Retained cash/charges replay without double aging. Calendar-release
archive context fails closed until versioned native accounting is implemented;
no service/game transaction route was opened. Independent review found no concrete
Store defect; all488 offline tests pass, including rollback and six tamper cases.

Calendar-release inspection now uses explicit calendar_v2 / format3 for contract
and player context. The preserved economic terms, sourced release-year cursor and
current retained-charge slice stay separate. Native checks reconcile nominal
cash against already-earned prior base, retained guarantees and bonus layers,
including allocated payment ceilings and unpaid guarantees. Review found and
fixed a marker-null downgrade: all v2 released archives reconcile cash even when
using the legacy archive cursor. Legacy v1 still rejects new calendar releases.
Actual Python released/expired contract and player replies passed C++ validation.
All489 offline tests passed, including inspection after another rollover without
archive changes. Windows pipe fixtures now query released/expired generations
and saved personalities twice with identical database bytes; CI execution remains
pending. No calendar-release service write route or real guest hook is claimed.

Added explicit manual_release calendar_format=calendar_v1 plus generation_id.
The Bridge chooses the calendar-aware Store path only for this exact request;
legacy postroll calls remain rejected. Full and compact receipts preserve format2,
generation and league-year metadata. Native checks bind requested identity/year,
revision, original allocated cash, retained nominal compensation, prior earned
salary settlement and complete cash coverage. Encoded frame capacity and final
connection/deadline checks remain before the atomic commit. Manual releases
continue to work with AI disabled without calling a model. All491 offline tests
pass, including disconnect/capacity rollback and stable retry. Portable CTest
passes malformed write receipt cases. Exact Windows smoke request facts matched
its actual Python fixture database; full/compact Python receipts passed C++.
Windows fixture now executes/retries the release before reading contexts and
saved personality; that execution awaits CI. Actual guest release hooks remain
open. Prior revision ee92067 Windows/Linux Build 38513985206 passed; its Windows
Franchise AI 38513985171 was still active at last inspection.

Added whole-Store calendar release history tests rather than only constructing
agreement representations. One chain converts guaranteed base into a separately
indexed bonus, explicitly pays the conversion and earned base, anchors/migrates,
rolls, releases, reopens and rolls again. Original amendment/contract archives,
exact Fraction bonus charges and nominal paid history survive unchanged. Another
chain assigns a contract between teams, pays earned buyer base, rolls and releases
while seller bonus debt stays separate. It distinguishes accelerated guarantee
cap charges from nominal future cash: after explicit current-year payment and
another rollover, cap charges age to zero while the remaining $1 million future guarantee
is still unpaid. Actual Python layered/assigned release receipts and later-year
calendar_v2 contexts passed C++ validation. All 493 offline tests passed.
Prior ee92067 Franchise AI 38513985171 passed Windows native released/expired
contract/player inspection and restart with saved personality (verified log).
dcea1b2 Build 38514505332 passed both platform runtime builds; its native transaction
Franchise AI 38514505285 remains active at last inspection. None of this establishes
actual guest save/game execution.

Verified terminal success for dcea1b2 Franchise AI 38514505285. Its Windows log
explicitly confirms the native calendar-release transaction, archive/player reads
and owned sidecar restart fixture executed successfully; Windows and Ubuntu each
passed 491 offline tests. Both platform runtime builds also passed run 38514505332.
This proves synthetic native transaction transport and durable replay, not guest
save writes or gameplay. Revision e93283e adds the 493-test history coverage and
remains a separate CI revision.

Extended the synthetic Windows pipe check to reuse the complete layered and
assigned economic histories, replacing their release boundary with the actual
C++ client. Fixture requests arrive on the smoke executable's own stdin; its
owned sidecar still receives one request at a time and validates every reply.
Each history executes full and compact calendar release requests and contract/
player reads across two sidecar launches, preserves saved personality and exact
retry/database bytes, then runs the existing subsequent payment/rollover/reopen
assertions. Python fixture orchestration passed locally and the tool compiles;
actual Windows execution of this new history transport fixture awaits CI. This
is asset-free transport validation and cannot establish actual guest gameplay.

Calendar-aware seller assignment now binds an exact current generation and its
advanced contract before calculation. GenerationAgreement carries an optional
sourced outgoing_trade_calendar_year; the original economic contract, amendment
and incoming assignment remain immutable, while only the trade plan uses the
advanced elapsed-year cursor. Closed seller payment ceilings retain earned prior
base and zero transferred future base. Retained bonus charges anchor at the trade
year and age once; optional snapshot metadata leaves legacy shapes unchanged.
All archive/view/charge validations complete before ownership/cash/revision
mutation. The dated guard permits the current calendar trade while preserving
legacy guards and chronological ordering. Store/native inspection rejects these
new archives until explicit versioned accounting is wired. All 497 offline tests
passed, including layered compensation conservation, later-year debt, stale/
foreign identity no-mutation and preserved original amendment records. Independent
review found no concrete defect and passed 31 focused checks. This is seller Ledger
accounting only: receiving Ledger, atomic paired Store replay/rollback, versioned
native requests/receipts and actual guest trades remain required. No paired trade
service route was enabled. Prior 642d533 platform Build 38515051821 passed; expanded
Windows history Franchise AI 38515051781 remained active at last inspection.

Verified terminal success for 642d533 Franchise AI 38515051781. Its Windows log
confirms the layered/assigned calendar releases, full/compact receipts, personality
and next rollover fixture executed, rather than only compiled. Ubuntu and Windows
each passed 493 offline tests. Both platform runtime builds passed run 38515051821.
These are synthetic histories and owned transport/restart evidence, not actual
guest execution. Revision 665757d adds seller calendar assignment accounting with
497 locally passed offline tests; its new CI is separate and not yet verified.

Receiving Ledger calendar assignments now require explicit canonical source and
destination identities, advanced buyer calendar and typed source plan. Recalculated
plan, current-year/date/classification/floor/cap checks and new immutable agreement/
view construction finish before mutation. The buyer agreement anchors at actual
trade year and uses its independent transferred base indices. Returning acquisitions
preserve prior released/assigned generations and their cash/debt. Proven expired
prior agreements also qualify only through existing authoritative expiry facts,
no active ownership and known fully settled allocated cash; scheduled exhaustion
alone grants no eligibility. Legacy postroll assignment/signing paths remain guarded.
All 501 offline tests passed, including current-year acquisition then later rollover,
closed prior-generation preservation, settled expired prior history, and stale/
foreign identity, cap and floor rejection without mutations. Independent review
found no concrete defect in the buyer path or incremental expiry guard. Atomic
paired Store calendar events/replay/rollback, native accounting/receipts and actual
guest trades remain required; no postroll service transaction was opened.

Atomic Store calendar assignments now commit both books and exclusive ownership
under one BEGIN IMMEDIATE. Explicit current seller/prior-buyer identities, both
migrated calendars and source year are required. Separate calendar_trade_out/in
events and calendar-trade request namespace carry exact shared before/after
financial, cash, generation and calendar snapshots. Replay validates canonical
formats/revisions, exact participant maps and peer payloads, authoritative source
obligations and resulting state. Receipt/final connection checks precede ownership
and both event writes; failure of the second event rolls everything back. Stable
historical retries after payment/another rollover return the original format2
receipt. Original seller economics, earned cash, buyer-year anchor, retained debt,
saved personality and existing per-club relationships persist. Source calendar
assignment inspection still fails closed pending an explicit native format.
All 505 offline tests passed; focused tests also reject ten tamper/missing-peer/
downgrade cases and verify access/receipt/second-insert rollback byte-for-byte.
Independent review found no concrete defect. No Bridge/native trade route or guest
writes were opened. Both Build 38515825166 and FranchiseAI 38515825234 passed at
prior receiving-ledger revision 97553c1; the new paired Store change is separate.

Explicit calendar_v3 / format4 contract and player inspection now includes a
sourced outgoing trade year/cursor, with economic archives unchanged. Native
validation reconciles assigned cash as settled bonuses plus earned prior base,
zero transferred future bases/guarantees, exact payment component ceilings and
full settlement. Null-marker fallback uses the economic cursor to prevent a
later-trade cash downgrade. Release metadata stays independent; conflicting
lifecycle markers reject. Legacy v1/v2 Store inspection remains guarded for new
calendar assignments. AI-off reads invoke no inference and preserve DB bytes.
All 506 offline tests passed. Portable CTest passes valid and corrupt v3 contract/
player responses; eight actual Python seller/buyer replies in two calendar years
passed C++. Windows fixture source and local Python orchestration pass; actual
Windows pipe execution of v3 remains pending. Native write receipts and actual
guest trades remain open. Both atomic Store revision 78fcff1 Build 38516329482 and
FranchiseAI 38516329469 passed; this inspection extension is a separate revision.

Explicit calendar-format manual_trade requests now route to the paired Store
transaction only with complete canonical source/prior-buyer identities. Full and
compact receipts preserve typed format2/year/calendar echoes. Native checks bind
both participants, revision/ownership, allocated original/retained/transferred cash
and inventory totals, plus exact transferred remaining salaries/guarantees and
buyer cursor/bonus rules. Seller earned prior base and original bonus layers are
fully settled and future base transfers remain independent. Full cash posting
shape now includes actual coverage source and typed cash revision; validation
against real Python replies caught/corrected an initial schema mismatch. Receipt
capacity and final connection checks remain before atomic commit. All 508 offline
tests passed, including AI-off/no-model operation, stable full/compact retry and
capacity/disconnect rollback. Portable CTest and actual Python full/compact trade
and release receipts passed C++ validation. Windows fixture now executes the trade
across processes before inspecting both parties in two years; local Python fixture
orchestration passes, new native Windows execution remains pending. Prior 481027c
FranchiseAI 38516814959 log confirms actual v3 seller/buyer inspection, personality
and rollover restart; both runtime platform builds passed run 38516814955. No actual
guest trade/write or playable game claim is made.

Verified terminal success for 8ea3682 Franchise AI 38517734890. The Windows log
confirms actual calendar trade transaction, full/compact receipts, v3 inspection
and rollover restart execution. Both Windows and Ubuntu passed 508 offline tests;
both runtime platform builds passed run 38517734886. This remains synthetic native
transport, not actual guest game/save evidence.

Added complete Store histories for return to a former club and transferred
unconditional base guarantees. The return preserves older seller/buyer economic
and incoming-assignment archives, original bonus debt and allocated cash, creates
a separate receiving generation and keeps both historical receipts stable after
another rollover. Personality and per-club relationship records stay unchanged.
Transferred guarantees remain buyer liabilities through later release, explicit
payment and rollover; after accelerated cap charges age out, unpaid future
nominal cash remains recorded. All 510 offline tests passed. Six actual Python
full/compact return and guaranteed trade receipts passed C++ validation. These
new histories are durable synthetic financial evidence, not guest capture.

First calendar-aware Ledger guaranteed-base amendments now require exact current
owned generation/view and sourced current date/floors. GenerationAgreement carries
optional restructure_calendar_year; immutable original terms remain unchanged,
while plan input may differ only by the advanced elapsed cursor. The amended
schedule anchors at amendment year, and later closed release/trade markers take
their own effective anchors without erasing the prior amendment. All updated
agreements, views and charges validate before cash/contract/revision mutation.
Legacy and repeated layered paths remain guarded. Payment component indices and
nominal obligation stay unchanged; new bonus layer uses the original year start
and remaining-term allocation. All 513 offline tests passed, including payment,
second rollover and subsequent release with both bonus schedules retained, stale/
foreign/no-op rejection and invalid marker/source checks. Independent review found
no concrete defect and passed 33 focused checks. Store persistence/replay and
native calendar amendment routing remain open. Prior 8f7e080 Build 38518353558 and
FranchiseAI 38518353684 both passed; this Ledger change is a separate revision.
No actual game/guest save execution is claimed.


## October 13, 2026 — Calendar amendment persistence in progress

Published Ledger/model commit 8eb076b after all 513 offline tests passed.
Build check 38519382382 and Franchise AI checks 38519382379 were confirmed
in progress for that exact commit; neither is reported as passed yet.
Parallel implementation is extending Store event/replay and native receipt
validation. The local sidecar route now selects an explicit calendar_v1 amendment
with exact generation identity, and a new bridge test covers final-disconnect
rollback and historical retry. Those new changes remain unvalidated and uncommitted
until the Store implementation and native checks complete. No game integration
or playable execution is claimed.


## October 13, 2026 — Persistent calendar amendments and client receipts

Added distinct format4 calendar_restructure event and explicit generation-aware
Store API. Replay checks exact fields and original obligations, financial/cash
and generation/calendar before/after postings. Stable historical retries return
original format2 receipts after payment and another rollover. Final receipt and
connection checks run inside the write transaction before persistence.
The sidecar supports explicit calendar_v1 manual amendments, and compact receipts
retain the agreement/year markers. Native validation covers full/compact receipts,
opening agreement identity, conversion namespace and monetary preservation.
All 517 offline tests passed; rebuilt portable protocol CTest passed. A portable
native harness accepted six real Python-generated receipt/context cases across
2027 and 2028. Added an actual Windows owned-pipe smoke for the same lifecycle;
that execution remains pending CI. Prior 8eb076b Build 38519382382 passed;
Franchise AI 38519382379 was last confirmed running. Repeated conversions remain
unsupported. Actual game/save integration and playable verification remain open.


## October 13, 2026 — Amended release and assignment lifecycle regression

Added permanent Store amendment/payment/rollover/release/restart/rollover checks:
original and converted bonus debt total $1.05 million at final-year release;
$7 million settled nominal cash and original salary-payment indices survive
cancellation of $2 million unprotected salary. Both historical receipts remain
unchanged after another rollover, when current cap debt ages to zero.
Added an independent two-team amendment/bonus-payment/trade/buyer-payment/rollover/
release chain with full/compact sidecar receipts. Seller retains immutable birth
and amendment archives, both bonus schedules and $5.1 million paid cash; buyer
gets separate $3.9 million salary cash without inherited bonus layers. Historical
trade receipts survive release/restart without database writes. No source defect
was found. All 519 offline tests passed. Worklist stale amendment-routing and
post-rollover mutation descriptions were corrected in place.
Prior 8eb076b Build 38519382382 and Franchise AI 38519382379 passed.
Current 2f5ffda Build 38519720719 and Franchise AI 38519720705 were last confirmed
running; actual new Windows amendment pipe execution remains pending.
No guest execution, actual save integration or playable delivery is claimed.


## October 13, 2026 — Verified Windows amendments; repeated-conversion reconciliation

2f5ffda Build 38519720719 and Franchise AI 38519720705 passed. Windows log
explicitly confirms actual owned-pipe calendar amendment full/compact receipts,
current contract/player contexts and later-roll restart. These are synthetic
sidecar/client fixtures; no guest gameplay or real save integration is proven.
Added a separate pure layered conversion calculator using exact original nominal
cash/component ceilings, fully settled prior bonuses and base salaries, unique
new layer identity and unchanged old bonus schedules. Existing durable first-
conversion callers remain guarded. Independent expected second-conversion charges
and payment/nominal preservation pass, with unpaid bonus/identity/floor failures.
All 520 offline tests passed. Immutable multi-amendment history and a separately
versioned durable event/receipt are the next implementation boundary.


## October 13, 2026 — Immutable repeated-amendment model and Ledger

GenerationAgreement now retains an immutable prior_restructures tuple while the
existing restructure remains latest. Nonempty history revalidates every pure plan,
immutable birth economics, exact sourced year/elapsed deltas, old bonus layers,
nominal cash identity/source continuity and monotonic paid components. History
closure checks bind release/assignment year deltas to exact economic cursors.
A separately versioned detached model history snapshot preserves every plan;
legacy model outputs stay unchanged when prior history is empty.
Added explicit Ledger apply_calendar_layered_preseason_restructure for a strictly
later sourced calendar year/current agreement. It constructs the history-bearing
agreement and reanchored view before mutable posting, preserving original bonus
indices and cash payments. Existing first-conversion API still rejects layers.
Format1 generation_snapshot fails closed if history is present so persistence
cannot silently omit prior amendments. All 528 offline tests passed, including
8 new focused model/Ledger checks. Versioned Store persistence/replay and native
repeated-conversion routing remain next; no durable repeated-write support or
actual game integration is claimed.


## October 13, 2026 — Explicit history-bearing generation snapshots

Ledger.generation_snapshot now accepts exact integer history_format=2, returning
root format2 and every agreement's detached amendment_history (None without prior
amendments). Immutable birth/current contracts, all previous/latest plans, current
ownership, financial and cash fields remain available. Default format1 retains
its original shape and rejects any history-bearing state. Invalid or boolean
format values reject. All 531 offline tests passed, including three new snapshot
checks for explicit first/second-conversion state, mutation isolation and strict
format selection. Store persistence is in progress: repeated mutation plus later
payment and season wrappers must bind history-bearing before/after snapshots.
Native repeated-amendment routing remains outstanding. No guest gameplay or
actual save/load integration is claimed.


## October 13, 2026 — Repeated amendment persistence awaiting native validation

Local Store implementation now records distinct calendar_layered_restructure
format2 events with history-bearing generation snapshots before/after, returning
format3 history receipts. Later cash payments require history snapshots even for
legacy opening agreement IDs. Only history-bearing teams gain explicit versioned
before/after generation fields in league rollover wrappers; other teams retain
legacy shapes. Replay rejects deleted, retyped or unsourced history markers.
Local explicit calendar_v2 manual sidecar requests select repeated amendments;
full/compact receipts preserve bound latest/prior plans. All 540 offline tests
passed including payroll, mixed-team rollover, settled expiry, historical retries,
strict replay corruption and receipt/access/SQL rollback. Added Windows owned-pipe
smoke source for the full/compact repeated receipt across restart and later expiry;
Python compilation passed. Native validation is still being implemented and this
combined source remains uncommitted until portable native checks pass. No actual
Windows repeated-amendment execution or guest gameplay is claimed.


## October 13, 2026 — Native repeated-history review in progress

Published snapshot commit 1e163c9 passed Build 38520773506 and Franchise AI
38520773515. The local native validator now has explicit repeated-amendment
history-plan/chain code under review; portable fixtures/build validation are still
pending, so the combined Store/sidecar/native change remains unpublished.
Compact receipts additionally reject incomplete prior plan dictionaries; four
focused receipt/Bridge tests pass after that tightening. Generated four actual
full/compact Python sidecar replies across repeated conversion and later expiry
for independent native acceptance checking. Actual Windows execution of this new
repeated path is still pending; the earlier single calendar amendment was verified.


## October 13, 2026 — Repeated amendments ready for Windows CI

The combined repeated-amendment Store/sidecar/native path is validated locally.
Native calendar_v2 receipt validation checks complete versioned prior/latest
history, old layer prefix plus one new layer, exact source-year/cursor progression,
nominal and paid cash continuity, current floors/guarantees, and binding to actual
request terms and the posted financial archive. Full/compact cash validation
reconciles typed records and totals. Legacy and first calendar request branches
retain their existing behavior. Fresh portable build and CTest passed, including
31 corruption cases. Six actual Python/sidecar receipt cases were accepted by the
portable native validator. Final full Python suite: 540 tests passed.
The actual Windows pipe smoke source now executes repeated full/compact mutation,
restart retries, recorded payroll and later settled expiry/history preservation.
That Windows execution awaits this commit's CI. Post-repeat Store release/trade
support, explicit full-history inspection and actual game/save integration remain
open. No playable build is claimed.


## October 13, 2026 — Windows repeated-fixture array correction

4edd386 Build 38521743315 passed; Franchise AI 38521743303 failed Windows
protocol_boundary with "Invalid repeated amendment cash totals" before the native
pipe fixture executed. Ubuntu passed. The repeated fixture used a one-element
brace assignment for JSON obligations. Replaced both full/compact assignments
with explicit nlohmann::json::array construction to remove compiler-dependent
initializer selection. An isolated portable build against the exact published
4edd386 header and corrected fixture passed; current portable rebuild/CTest also
passed. Windows confirmation still awaits the fix commit's CI; repeated Windows
pipe execution has not yet been verified.
Separately, history-aware release Store and compact receipt work is local and
uncommitted; its native validation/fixtures are still in progress.


## October 13, 2026 — History-aware releases validated; Windows repeats confirmed

048a8e6 Build 38522299429 and Franchise AI 38522299444 passed. The Windows log
explicitly confirms repeated calendar amendment full/compact history, payroll,
expiry and restart execution, verifying the explicit JSON-array fixture correction.
Added history-aware calendar_layered_release format2 Store events, before/after
history snapshots and format3 receipts. Immutable amendment chains, retained bonus
and guaranteed-base liabilities, ownership removal, replay, historical retries
and final callbacks remain atomic. Tests preserve $2 million unpaid cash after cap
debt ages out, then settle it through explicit payroll without changing history.
A four-year fixture verifies June-1 treatment with nonzero future bonus allocation.
Manual release calendar_v2 now selects this explicit path; full/compact receipts
preserve bound amendment history. Native checks share history validation and bind
release timing to exact original cursors, cash/payment continuity, retained IDs,
all bonus ceilings and cancelled salary. Existing v1 behavior remains unchanged.
All 550 offline tests passed. Rebuilt portable CTest passed with 25 new corruption
cases; four actual sidecar full/compact fresh/historical receipts validate.
Added an actual Windows owned-pipe release smoke with restarts, later rollover and
retained payroll. Its execution awaits this commit's CI. History-aware assignments,
full-history inspection and actual guest/save integration remain open. No playable
game delivery is claimed.


## October 13, 2026 — History-aware paired assignments ready for Windows CI

f7d9ad9 Build 38522825831 and Franchise AI 38522825921 passed. The Windows log
confirms layered release full/compact history, retained payroll and rollover
restart execution. New calendar_layered_trade_out/in Store events bind both
clubs' format2 generation histories, exact paired postings/roles, identity,
ownership and rollback. Seller retains immutable amendment history and bonus
debt; buyer receives remaining salary/guarantees with fresh cash indices and no
inherited bonus layers. A return assignment through 2030 preserves the buyer's
older layered archives alongside the fresh agreement. Old routes remain guarded.
Explicit manual_trade calendar_v2 now returns bound format3 full/compact seller
history receipts. Native checks validate exact year/cursor and source/cash/payment
continuity, complete settled bonuses, retained record identity, actual chronology,
separate buyer compensation and paired financial/cash postings. All 558 offline
tests passed. Rebuilt portable protocol checks passed with 26 new corruption
cases, and four actual sidecar full/compact fresh/historical replies validate.
Golden JSON chunks are limited to 4096 characters for MSVC portability.
Added actual Windows owned-pipe layered assignment smoke across restart, buyer
payroll, rollover and buyer release. That execution awaits this commit's CI.
Full-history inspection and actual game/save integration remain outstanding;
no playable delivery is claimed.


## October 13, 2026 — Worklist reconciled with current evidence

Updated the primary worklist entries and added a current verified-state section;
removed obsolete appended checkpoints that described already-implemented history
support as pending. 212b037 Build 38523844512 and Franchise AI 38523844441 passed,
with actual Windows layered assignment full/compact history, separate buyer
payroll/release and rollover restart confirmed by the log. Calendar-v4 inspection
is local/unpublished: all 565 offline tests passed, seven new Store/Bridge tests
cover scoped history reads, and native validation accepted 18 actual responses.
Publication and actual Windows v4 pipe coverage remain the immediate work.
Game/save integration and playable acceptance remain unverified.


## October 13, 2026 — Full-history client inspection ready for Windows CI

Added explicit calendar_v4 contract context format5: immutable original contract,
complete first/prior/latest amendment history, archived economic terms and separate
current calendar accounting. Never-amended agreements use null history; first
amendments retain a latest plan with empty prior list. Earlier context formats
keep their original response shapes. Scoped player reads preserve personalities,
relationships and goal history without exposing another team's actor or agreement.
Store tests cover active/released/assigned/expired contracts, current cash, immutable
terms, detached response data, restart and unchanged database bytes. Native checks
bind full history to the immutable original economics and effective archive,
exact later source-year/cursor continuity, current anchor, identities and cash
ceilings; first amendment birth year is not invented when absent from the source.
All 565 offline tests passed. Rebuilt portable CTest passed with 14 history and
8 no-history corruption cases; all 18 actual contract/player sidecar responses
validated. Added actual Windows owned-pipe reads across active/expired state,
scoped player contexts and restart, requiring unchanged DB bytes. Python smoke
compilation passed; its Windows execution awaits this commit's CI. Actual game
save/load and playable Windows/Steam Deck delivery remain unverified.


## Persistent inference request ceilings and usage records

Added InferenceBudget with explicit immutable scope/request policy, atomic
BEGIN IMMEDIATE reservations, FULL SQLite durability and no automatic refund or
reset after failure/restart. Pending/crashed calls retain their request slot.
Completion is idempotent only for identical outcome/nullable token metadata;
missing usage stays unknown. Persisted malformed policy/completion/token records
fail closed before another SDK attempt. A seven-process fixture admits exactly
three calls under a three-request ceiling. No prompts, responses or cloud errors
are written to this usage database, and no dollar guarantee is inferred.
VertexProvider accepts an explicit typed request_budget, reserves immediately
before the SDK invocation and completes using each call's own diagnostic snapshot.
Context/rate preflight rejection makes no durable SDK reservation. Failed/blocked
SDK attempts remain charged; a completion-persistence error prevents a response
from reaching financial commit while the reservation remains spent.
All 575 offline tests passed. The milestone provides explicit configured request
limits; mandatory sidecar/HTTPS runtime wiring, actual season attribution,
input/output token and dollar ceilings, compact/batched prompts and measured game
costs remain next. No paid inference was performed in these fixtures.


## October 14, 2026 — Mandatory live-runtime request budgets

Live Vertex sidecar and HTTPS runtime modes now require explicit separate usage
DB, persistent scope and immutable request ceiling. Budget validation runs before
credential/SDK initialization; missing/invalid policy disables AI setup while
manual franchise operations continue. Both transports share attempts when given
the same usage file/scope/limit. Path/symlink/hard-link aliases of the financial DB
and in-memory usage storage reject. Offline modes do not create/require budgets.
Actual runtime-factory tests verify these bindings, restart/policy integrity and
manual signing recovery without paid calls or network requests. All 580 offline
tests passed. Published 00b65f2 Build38526105080 and FranchiseAI38526104386 passed;
3d3534c Build38524980783 and FranchiseAI38524980828 also passed.
Token/dollar admission, authoritative game-season attribution, native launcher
options and measured gameplay spending remain next. No spending guarantee or
actual game integration is claimed.


## October 14, 2026 — Native persistent-budget launch wiring

Added explicit franchise_host_create_with_budget while preserving the old C ABI.
Shared portable command construction validates mode, nonblank strings and positive
INT64-bounded request limits before Win32 handles/process creation, safely quotes
all arguments and forwards the actual runtime --ai-request-limit option.
The existing host startup hook reads explicit budget database/scope/limit fields;
partial policy, non-decimal, zero and overflowing limits refuse launch. No defaults,
new periods or AI grants are manufactured. Old unconfigured launch remains manual-
capable with AI unavailable under the Python mandatory-budget policy.
Rebuilt portable protocol CTest passed with new launch/quoting/invalid-policy
cases. Python Windows-smoke source compiles. Added actual Windows host lifecycle
checks and plain-C budget launch/read/restart smoke; the latter forces nonexistent
ADC and verifies the exact SQLite policy/scope with zero inference attempts.
Windows execution awaits this commit's CI. Prior a39ff30 Build38527218113 and
FranchiseAI38527218123 passed all580 offline tests. Token/spending admission and
actual game/season integration remain open; no paid inference was performed.


## October 14, 2026 — Full-request token-count preflight

Live sidecar and private HTTPS runtime now enable a16384 input-token preflight.
VertexProvider counts the exact serialized contents, instructions and response
schema/generation settings before reserving a paid generation attempt. Invalid,
missing or excessive counts and sanitized counting errors reject without
generation; byte/rate controls still precede counting. Explicit positive integer
output limits replace the internal literal, retaining4096 for runtime behavior.
Legacy controlled callers can omit counting; demonstration scripts remain outside
the production policy. No cumulative token/dollar ceiling is claimed.

Seven new synthetic SDK tests cover complete request identity, exact boundary,
unknown/invalid/oversize counts, sanitized errors and constructor validation.
Negotiation and draft calls supply a request-local access callback, rechecking
deadline/control/disconnection after counting and before paid reservation. A
real negotiation fixture disabled during count leaves finances unchanged and
manual signing available. A second check after potentially blocking SQLite
admission refuses expired generation while retaining the failed reservation.
All587 offline regression tests passed; no paid calls or cloud counting occurred.
Prior fbc7da4 Build38528423772 and FranchiseAI38528423925 both passed. The actual
Windows log confirms plain-C explicit budget launch preserves the configured
scope across restart and manual reads work with zero paid inference. These remain
asset-free fixtures, not game execution/save verification. Cumulative token
reservation and spending admission remain the next budget milestone.


## October 14, 2026 — Durable cumulative token reservations

InferenceBudget now accepts an explicit optional immutable token_limit. Additive
SQLite token-policy/reservation tables keep existing request-only policies valid.
Token admission and generation-attempt reservation commit atomically under
BEGIN IMMEDIATE; input+maximum-output allowances remain spent after response,
failure, crash or missing usage. Changed/removed policies, legacy attempted-scope
upgrades, orphan/missing/malformed reservations and reported usage overruns deny
future admission. Actual overrun metadata remains persisted before denying a
decision; unknown usage is never treated as zero or returned credit.

Vertex requires full-request counting when a token policy is active and reserves
reported input+configured generated ceiling. Both Python live launchers accept
explicit --ai-token-limit and share the exact configured policy. This option is
not mandatory yet: native ABI/environment forwarding remains next, alongside
dollar admission and authoritative game-season attribution. No paid calls or
counting requests were made; no billing or gameplay guarantee is claimed.

All603 offline tests passed. New tests verify seven-process contention admits
exactly three of seven token reservations, restart/no-refund behavior, immutable
policy/type/tamper checks, retained reported overruns, provider failures/missing
usage, post-reservation shutdown and unchanged negotiation finances. Both live
factory tests verify the same token ceiling across transports. Prior49366e5
Build38529452500 and FranchiseAI38529452501 passed. Real asset/save/runtime gates
remain unchanged.


## October 14, 2026 — Native cumulative token-policy launch

Added compatible franchise_host_create_with_token_budget with explicit
INT64-bounded request/token limits. Optional BudgetLaunch.token_limit forwards
only explicitly supplied --ai-token-limit; request-only and original ABIs retain
their shapes. Native startup accepts NFL2K5_FRANCHISE_AI_TOKEN_LIMIT only with
complete existing budget configuration. Shared decimal parsing rejects zero,
signs, overflow, whitespace and Unicode numerals. No defaults/grants/credits are
added; mandatory cumulative policy remains subsequent work.

Rebuilt portable protocol CTest passed exact forwarding, missing option and
invalid/maximum token-limit checks. Plain-C header syntax and a portable fixture
against the actual startup parser passed; those stub-factory checks do not prove
Win32 transport execution. Windows lifecycle cases now cover token policy and
shutdown. Added actual plain-C token-budget launch/manual-read/restart fixture
that checks persisted request/token rows before inspection could create them,
with missing ADC and zero paid inference. Its Python driver compiles; actual
Windows execution awaits this commit's CI. Prior f5e7965 Build38530074049 passed;
FranchiseAI38530074067 is still running. Previous49366e5 checks passed. No paid
requests, real game execution or save/load verification occurred this milestone.


## October 14, 2026 — Mandatory cumulative token policy for live AI

Both production runtime factories now require an explicit positive INT64-bounded
--ai-token-limit before creating usage storage, loading credentials or creating
the Vertex client. Missing/invalid cumulative policy leaves AI unavailable while
manual/read operations remain usable. Core request-only budget inspection and
legacy native transport APIs remain compatible; attempted old scopes cannot gain
fresh token capacity through an implicit upgrade. No defaults, paid calls or
period resets are introduced. Dollar policy and actual season attribution remain.

Updated both live-factory fixtures to cover missing/zero/negative/overflow token
limits, no credential/SDK/file creation and manual recovery; valid shared policy
fixtures reserve actual token allowances. The Windows driver now verifies legacy
request-only transport starts manual-capable with no usage file, while explicit
token launch verifies persisted policy. All603 offline tests passed; Python
Windows driver source compiles and diffcheck passes. Native actual execution
awaits current CI:75dbf4a Build38530565397 and FranchiseAI38530565261 are running.
Prior f5e7965 Build38530074049 and FranchiseAI38530074067 passed. No actual game
execution/save-load evidence is implied by these asset-free checks.


## October 14, 2026 — Return focus to playable integration

User feedback identified the cost-control work as a complicated distraction.
The existing mandatory request/token limits and remote killswitch are sufficient
for this stage. The unpublished declared-price spending experiment was shelved
recoverably in a named local Git stash; it was not pushed or added to delivered
requirements. No further dollar-policy expansion should precede meaningful game
integration progress. The worklist now prioritizes one actual franchise signing
path, in-game negotiation and contract save/reload over standalone infrastructure.

Current delivered source cb278b9 passed Build38530887689 and
FranchiseAI38530887732, with603 tests and actual synthetic Windows request-only
AI refusal/manual reads plus token-policy restart. Source inspection confirms the
root host only owns service startup/stop: no verified guest signing callback or
financial write exists. Legal Xbox assets, controlled saves and Windows gameplay
access remain B01/B02/B03; source/fixture checks cannot substitute for them.


## October14,2026 — Existing menu probe for first franchise integration

Source audit distinguished pregame card/roster identity and simulation-entry
selection from unknown franchise signing/financial behavior. Recorded exact
candidates and the controlled roster->player->contract trace in
docs/franchise-integration.md; no speculative financial interception was added.
The existing root FSM callback was a no-op despite address-anchored push/pop
patches already present. It now provides explicit NFL2K5_TRACE_FRANCHISE=1
read-only event logging capped at256 events per process, silent otherwise.
No guest memory access, hidden-rating input, AI inference or contract mutation
is introduced. The real source function body compiled under C11 with
-Wall/-Wextra/-Werror and a portable driver verified disabled modes silent,
exact object/descriptor output and the256-event bound. This proves the logger,
not real franchise descriptors or game execution.

original/ still contains onlyREADME; legal assets/saves/runtime gates persist.
User received the local original/disc intake path. Analysis accepts its XBE
through explicit -Xbe; its historical default original/default.xbe remains.
Next actual experiment is franchise navigation and selected-player readback,
then controlled signing/save/load. Cost-policy expansion stays deferred.


## October14,2026 — Menu-trace source checks complete; runtime input gate

38fcc2d Build38532242341 passed Windows/Linux, and
FranchiseAI38532242330 completed successfully on both platforms after observing
its actual running Windows compile/pipe fixture job. These are asset-free checks
and exclude the actual game target; they do not prove a franchise screen or
signing callback. Working tree was clean before this evidence update.

Checked original/ with ignored files included: onlyREADME is present. No raw
franchise saves or available wine/wine64/PowerShell/QEMU runtime were found in
the task's intake/tool locations. The next selected integration experiment needs
legal Xbox assets, controlled franchise saves and Windows gameplay access.
Source audit and the bounded existing FSM probe are ready. No guessed contract
write or additional quota/infrastructure work will substitute for that evidence.
User has the local intake instructions; no repeated asset request is needed.


## October14,2026 — Assets received, Sign Contract path identified, Deck connected

Observed the actual browser partial file through its final rename to the user
7zarchive; archive extraction completed. The Xbox extractor's initial option
placement caused a default output directory; verified all19listed file sizes
and moved the completed disc into ignored original/disc. Existing XBE parser
verified retail header title53450030 and input SHA256. Private analysis produced
31081detected entries/278523crossrefs plus UTF16candidate-to-reference mapping;
no generated code or guest financial memory was modified.

Verified the actual Sign Contract descriptor557B2C, message11 callback3478A0
and shared interactive/automated routine323D80. Corrected a critical identity
distinction: CB8C34 holds negotiation context, [context] points to the player,
and [context+4] is a separate object. Recorded static display-field candidates
with units/durable-ID/save semantics explicitly unverified. These are meaningful
source anchors for the first runtime experiment, not integration acceptance.

User supplied SteamDeck host and enabledsshd. Initial key rejection resolved via
a project-private key authorized by the user; SSHuname confirms x86_64SteamOS.
Read-only inventory found Proton8/9/11/Experimental and about77GBfree, without
nativecompiler/CMake. Existing rootlessPodman works. Private open-source
Wine/CMake/Ninja/MSI tooling image built under the Deck user's container storage;
Microsoft installer metadata fetched only. Compiler/SDK download still requires
explicit license acceptance. No proprietary toolchain or game asset was published,
no paid inference/cloud infrastructure was used, and no game was executed yet.


## October 14, 2026 — Private Deck Windows compiler verified

User explicitly accepted the Microsoft Visual Studio Build Tools 2022 license
and authorized the private compiler/SDK installation. Installation completed
with MSVC 19.44.35229 x64 and Windows SDK 10.0.26100.0 inside the existing
rootless build environment. No SteamOS system packages or Steam/Proton prefixes
were changed. Microsoft binaries remain private; none are committed or published.

The initial Wine prefix was incomplete and compilation failed with D8037.
Initializing a fresh project-private prefix with wineboot and waiting for
wineserver shutdown resolved that failure. The compiler built a Windows C probe,
and Wine executed it successfully on the Deck. A separate C++17 probe including
winrt/Windows.Foundation.h compiled successfully; its first include-path check
was corrected to follow the SDK directory symlink. These are compiler/runtime
checks only, not game execution.

The fork and pinned xboxrecomp submodule were cloned privately onto the Deck.
SDL 3.2.20 source matches the CI pin
96292a5b464258a2b926e0a3d72f8b98c2a81aa6; its Windows build and installation
completed successfully. WebView2 SDK 1.0.3124.44 retains its package license and
notices, and the miniz source/license are pinned to xemu commit
36334d95b86f9c3c6ae34efb9af06785273f8e1a. The full Windows game configured
successfully with the franchise transport enabled and completed all 120 build
steps, including the final NFL2K5.exe link. Executable SHA256:
9ba7e45c5bd1a1f7806f3e739a81a54d26ca3b115f7acc96afd6cd595cb9fa48.
Actual PE imports include SDL3, the MSVC runtime and Windows graphics/media
components; the static WebView2 loader introduces no loader-DLL dependency.
The supplied executable/data are being staged privately for an isolated Proton
run. Boot, franchise signing and save/reload remain unverified.
Financial guest-memory hooks remain disabled.


## October 14, 2026 — Real Proton validation and first game execution

All 17 required supplied executable/data files were transferred privately to the
Deck and verified against local sizes and SHA256 hashes. The actual full game
initially crashed during memory initialization: its POSIX slice-reservation
strategy used nonzero-size MEM_RELEASE, which Windows does not support.
Dependency commit 61ad649 restricts that strategy to the POSIX shim, retaining
Windows fixed-base views, and rejects a missing contiguous window before the
tiled-alias probe can dereference it.

A second observed failure occurred after validation shutdown: the untracked
kernel timer thread continued reading guest memory after it had been unmapped.
The same commit retains the thread handle, signals it to stop and joins before
memory release. It releases the caller's guest lock and rechecks stop after the
timer acquires that lock. Four complete real-asset Proton --validate runs then
returned zero. This verifies executable intake, initialization, the existing
memmove validation and this shutdown path; it does not verify gameplay or saves.
An already-running guest ISR/DPC may still delay shutdown; broader runtime
reinitialization/resource cleanup has not been validated.

Corrected executable SHA256:
97dd413c936060c8828fb13b25808c35f39ff1b84d6e05de97e5b154a808d29b.
Private controlled --run execution opened the actual ESPN NFL 2K5 window and
submitted audio, but the captured screen was black. Proton's built-in HLSL
compiler rejected the renderer shader. An app-local x64 d3dcompiler_47.dll from
the user-authorized Windows SDK, with a process-only native override, removed
that error: Direct3D11 now reports ready at feature level B000. A second captured
screen remains black; frontend rendering/progression needs further investigation.
The log also reports an unavailable tiled aperture, which remains unresolved.
No real franchise transaction, game completion or save/reload is claimed.
All assets, Microsoft binaries, screenshots and raw analysis remain private and
ignored; no binary release, paid inference or new cloud infrastructure was used.


## October 14, 2026 — Build parity investigation

Commit 3a256fd Build check 38544464324 and Franchise AI checks 38544464378
both completed successfully. These CI checks remain asset-free; they do not
replace the real Proton results above.

Read-only comparison identified a material runtime-build discrepancy: the
initial private direct-CMake build used optimization OFF and left the four
compatibility options OFF. Standard tools/build.ps1 builds enable optimization,
AUDIO_LOCK, 33660_DRAIN, NETPOLL and STATE9_READY. The observed state-9 give-up
branch is consistent with STATE9_READY being disabled. These are inherited
bypasses, not proof that hardware/resource-readiness defects have been fixed.

apply-gen-patches.py --check confirmed the required existing hooks were already
present. The private Deck recipe now runs that preparation step before the
register-locals conversion and uses exactly the standard five compile options.
The optimized full-game rebuild is actively compiling generated code in
2k5-parity-build; log is under the Deck's private 2k5-franchise-build directory.
Its eventual boot/frontend outcome is not yet known. Do not restart this build
solely because a status observation times out; inspect the container/log first.


## October 14, 2026 — Rendered franchise baseline and Steam Deck controls

The existing optimized standard build completed without restart and passed
Proton --validate. Executable SHA256:
c1855b735ad382393866aba33a3ad94612a5ee9936c7f685527a48499426d5c1.
With the inherited standard compatibility flags and app-local Microsoft shader
compiler, a private screenshot now shows the actual Franchise Options screen.
Renderer logs record successful draws/texture uploads. Failed tiled mapping
remains a known limitation; visible UI does not prove every rendering path.

The user attempted a negotiation and reported immediate acceptance. The same
private runtime log records Sign Contract FSM push descriptor 00557B2C,
sequence 28. This verifies the menu boundary, not player identity, contract
units, transaction mutation or AI behavior. The vanilla handler remains active;
no personality/performance negotiation hook has been connected to this screen.
That limitation was explicitly explained to the user.

The first controlled runs ended via their deliberate 120-second timeout, rather
than an observed new crash. A later 600-second test also ended with status 124.
User reported Deck desktop-mode trigger mapping. Staged a dedicated untimed
launcher preserving SteamAppId/SteamGameId, installed a desktop entry and used
Valve's installed steamos-add-to-steam helper. Steam persisted appid 3759717425
with name "2K5 Remade (Test Build)" and the expected script path. Its controller
log records XInput configuration activation. The user confirms launch from
Gaming Mode and that both LT/RT now work correctly. Only the private game's
controls.ini was adjusted (Xbox prompts and mouse-as-controller off); no global
desktop control layout was edited. Current Steam-launched session is untimed.

Current save intake contains only VIP1/USR payloads (20720 bytes), no franchise
save yet. Requested a user-created AI-BASELINE franchise save for verification.
Next work is narrow read-only signing readback and save-based field validation,
then actual negotiation interception; no guessed financial writes are authorized
by these baseline observations. Proprietary files and screenshots stay private.


## October 14, 2026 — AIBASELIN intake and compiled signing observer

User saved the actual franchise as AIBASELIN. Captured five companion/payload
files in private ignored original/saves/AIBASELIN-baseline after checking that
source sizes/mtimes did not change during copy. TYPE is FXG; logical franchise
payload matches UDATA container 8323F40E9258. SAVEGAME.DAT is 720044 bytes,
SHA256 2f82cfd9c608411c40b006db10f1e6dc6dfe46b187dd50c1ae94dd6341fd3dd2.
This resolves the missing baseline input; contract decoding and controlled
transaction pairs are still required. No franchise load/round-trip is claimed.

Added a narrow read-only observer to the existing optional FSM probe for the
observed 00557B2C signing screen. It follows the statically identified CB8C34
context candidate, validates complete reads against this run's ordinary guest
RAM, and uses the existing fault-safe copy leaf. It logs raw context bytes and
player salary/profile/term candidates with units and identity explicitly
unverified. The existing opt-in and 256-event limit remain; no guest writes or
AI requests were added. Extracted actual-function checks passed disabled/pop
behavior, valid capture, failing reads and boundary rejection. Full standard
Windows target compiled/linked with the observer. Current user game remains on
the earlier executable; observer runtime verification waits for a safe restart.

Steam launch remains confirmed by the user in Gaming Mode, with both triggers
working. The untimed launcher preserves Steam's game identity. User baseline
contract acceptance remains original game behavior until the negotiation engine
is actually connected; do not present this build as completed Franchise AI.


## October 14, 2026 — Verified baseline roster reader

Read-only structural analysis confirms the captured FXG signature companion
matches the runtime's zero-key HMAC implementation. The payload has directly
readable UTF16 names; no whole-file compression header was identified. Reviewed
pinned BAD-AL source format facts and independently implemented a small strict
reader. Actual AIBASELIN resolves all 32 team memberships, 1937 unique player
slots and 241 free agents; known names match roster membership. Source slots
remain snapshot locators and no financial interpretation or hidden ratings are
exposed. No upstream converter source/binary or user save was committed.

Five synthetic adversarial/read-only reader tests pass. The full 608-test offline
suite passed outside the sandbox, after four existing localhost-server fixtures
were blocked by sandbox socket permissions. This is synthetic engine/tool
validation plus actual read-only save parsing, not transaction/save round-trip
acceptance. Observer commit84faad4 Build38550360931 and
FranchiseAI38550360928 both completed successfully. The compiled observer is
staged privately as NFL2K5.next.exe (SHA256
512b193b2376bffd0056b77be3f0d8db338103434ac4302234eff63d6bf18bcc),
without replacing the user's running game. Actual observer readback and a
controlled contract/save pair are the next runtime steps.


## October 14, 2026 — Signing transaction audit and exact baseline name

User confirmed the baseline name is AIBASELIN. Parallel read-only audits were
cross-checked against the private executable disassembly: shared signing preserves
roster/cap gates, interactive offer judgment, contract mutations and subsequent
roster/team/history updates. The candidate allocation write is the high nibble
of player+0x26, correcting the earlier low-nibble note; raw observer bytes remain
valid. Runtime relocation walks84-byte records and preserves the candidate
financial bytes. Actual bank capacity2479 differs from the inspector's restricted
2317-slot scope. Units, persistent identity and live transaction/save reload remain
unverified; no guest/save writes or Deck actions were performed for this audit.

CI for4c7da04 completed successfully: Build38552289387 and Franchise AI38552289343.
Updated the worklist's stale source/test/input summary to this evidence. Keep the
user's current game undisturbed; staged observer activation and controlled save
pairs remain the next runtime steps.


## October 14, 2026 — Bounded signing player-bank observation

Implemented opt-in read-only bank-slot/name observation using the actual retail
slot getter's count/base/84-byte layout. Full-bank arithmetic uses64-bit bounds;
unknown pointers or malformed names never become asserted identities. Names use
bounded relocated UTF16 pointers and BMP-to-UTF8 encoding, with unsupported
surrogates and unsafe log characters rejected. No durable identity, financial
units, guest writes or AI signing integration are inferred.

An authored RAM harness compiles the actual src/main.c observer body with C11
Wall/Wextra/Werror and checks bank alignment, bounds/overflow, malformed names,
Unicode, default-off behavior and unchanged RAM during observation. Full609-test
offline suite passed. The private full Windows game target compiled and linked
under the authorized Deck build toolchain. Staged runtime/NFL2K5.next.exe SHA256
df1c0158a4325710bcddcb8740feda6501462581b9e30174b0a3956cd68ee07d.
The live executable remains c1855b735ad382393866aba33a3ad94612a5ee9936c7f685527a48499426d5c1
and PID65155 remains active; no restart or executable replacement occurred.
User was asked to exit normally when finished so the staged observer can be
applied safely. Actual selected-player readback and controlled contract/save
pairs remain pending.


## October 14, 2026 — Original judgment and cap-adjustment dependencies

Parallel read-only audits identified the pre-write old-contract adjustment: guard
0x0013EC30, calculation0x0013ED00, uint16 accumulator at team+0x19C+2*index and
write0x0013ED56. Signing passes index0. Cross-checked that cap accessor0x0013ECA0
subtracts this accumulator and later0x000C3F00 separately refreshes team+0x124.
Documented truncating storage without claiming an observed overflow/cap bug.

The interactive judgment0x00323A60 uses an output score from0x003232A0, with
refusal/decline/accept thresholds70/80 and a messaging threshold110. Default
demand depends on hidden durability/leadership and weighted position evaluation,
plus slot/experience heuristics and conditional shared RNG. This identifies what
the performance/personality AI must replace while retaining cap/roster/history
transaction effects. No interception or financial write was made.

CI for80279d9 was observed live: Build38553654953 and Franchise AI38553655040
were in progress. Do not report them as passing until completed. The currently
open Deck game still requires normal exit before staged observer activation.


## October 14, 2026 — Windows observer-harness portability repair

Observer source80279d9 Build38553654953 passed, but Franchise AI38553655040
failed only its new Windows harness: implicit declarations for POSIX unsetenv
and setenv under cc/Werror. Replaced those harness-only calls with an authored
getenv fixture and an explicit .exe output path; the production observer and
private compiled game are unchanged. The actual extracted observer's focused
C11/Werror test passes locally after repair. Windows CI must verify the fix.

Read-only Deck state still reports game PID65155 active, so staged observer
activation remains pending normal exit. No restart, live replacement or input
was performed.


The repaired authored observer harness also compiled with the authorized private
MSVC toolchain (/std:c11 /W4 /WX) and executed as a Windows PE console program
in the isolated build Wine prefix, exiting0. It reported bank_slot1/Test Player
for the valid fixture and identity unknown for the misaligned record. This is
Windows compilation/execution of the fixture, not a real guest signing. Private
log: observer-check-windows.log. Replacement checks0ba8cfe Build38554154874 and
Franchise AI38554155010 were confirmed in progress; watching the latter exact run.


## October 14, 2026 — Observer CI verified; actual-runtime integration gate

Replacement source0ba8cfe completed both workflows successfully:
Build38554154874 and Franchise AI38554155010. The Windows test suite, protocol
boundaries and native pipe restart fixture passed. Updated the worklist from
stale4c7da04/pending-harness status to this exact evidence.

The same actual-game gate persisted across consecutive goal turns: the user's
PID65155 remains active on the old executable. Staged observer activation needs
a normal exit; the user has already been asked to report closed. Independent
work completed the bounded bank/name observer, full private Windows compile,
Windows fixture execution, CI portability repair and signing/accounting audit.
The next required evidence is actual selected-player readback and UI/unit agreement
with controlled signing/save/reload pairs. Do not invent financial mappings or
replace the original transaction while that evidence is missing. Goal remains
unachieved: no AI/game transaction, durable story/save integration, supported
modern accounting in the game or live required-control acceptance is verified.
Further standalone layers do not resolve this runtime gate. No force-close,
restart, guest/save writes or live executable replacement occurred.


## October 14, 2026 — Observer installed after user-confirmed exit

User reported the game closed; read-only pgrep confirmed no NFL2K5.exe process.
Verified staged SHA256df1c0158a4325710bcddcb8740feda6501462581b9e30174b0a3956cd68ee07d,
backed up the previous executable and launch log privately, then checked exit
again before atomically replacing runtime/NFL2K5.exe. Installed hash matches.
AIBASELIN SAVEGAME.DAT still hashes
2f82cfd9c608411c40b006db10f1e6dc6dfe46b187dd50c1ae94dd6341fd3dd2.
No save writes, control changes or game launch were performed.

Next runtime action: launch the existing Steam Gaming Mode entry, load AIBASELIN,
open a player's Sign Contract screen without submitting an offer, and compare
actual observer bank/name readback with that visible player. Selected identity,
contract units and controlled transaction/save reload still remain unverified.


## October 14, 2026 — Deck access unavailable during scheduled checks

Scheduled checks at12:12,13:13 and14:15UTC could not resolve steamdeck.local.
The first check retried once with the same result. This is a runtime-access
blocker, not evidence that the game exited, crashed, or produced an observation.
The user was already notified to wake/connect the Deck; do not repeat unchanged
notifications. Repository remains clean apart from this evidence update. Installed
observer and preserved AIBASELIN were last verified during installation; no later
remote file or process state is claimed. No game/save writes, model requests,
cloud changes or binary publication were performed. Resume with a read-only
connection/log check when Deck access returns, then verify selected-player/UI
readback before any negotiation interception or financial mapping.


## October 14, 2026 — Actual Trotter-screen physical pointers

Deck access restored and user confirmed Jeremiah Trotter on Sign Contract.
Actual game stderr is redirected into the private Proton prefix's local
NFL2K5-PC/logs/session.log; the launcher log alone lacked all FSM traces.
The session log captured descriptor557B2C at sequences18/20 and rejected
player pointers811FCCE8/811FF3A0 with team811D3054 because the observer initially
allowed only low RAM. Thus no player identity was verified by that observation.
Read-only baseline inspection locates Jeremiah Trotter in free agents at slot1910;
that is an independent save locator, not yet a verified runtime association.

Confirmed runtime source maps the80000000 contiguous window to separate storage.
Repaired observer ranges to admit bounded original physical addresses without
masking them into low RAM; full bank ranges and overflow guards are checked.
Authored fixtures exercise both separate regions, wrong alignment, crossing the
physical-window end and oversized reads, plus unchanged low/physical memory.
Full609-test offline suite passed. Full private Windows game rebuilt successfully.
User closed normally; pgrep verified absence, prior executable/session log were
backed up, and an intermediate build installed with AIBASELIN hash unchanged.
Completing the same update's full raw offer word/packed flags before the next
launch; its focused high-byte readback fixture passes. Final installed hash and
actual selected-player/UI verification follow below when available. No offer
was submitted by the agent and no game save was written.

Final full Windows game rebuild linked successfully. Installed observer SHA256
1f1aa6150ba5d2046c4dc4c2067c008db2aab04232ef0bc664aaa1b5d33ab1b3
after rechecking no game process before atomic replacement. AIBASELIN remains
2f82cfd9c608411c40b006db10f1e6dc6dfe46b187dd50c1ae94dd6341fd3dd2.
The complete-offer-word fixture passed after the small logging addition; no
production acceptance or financial write behavior changed. Actual readback of
Trotter, financial units and controlled save/reload remain pending.


## October 14, 2026 — Actual Trotter player-bank readback verified

Corrected game process68889 reached signing descriptor557B2C at sequence19.
Per-user session log reports bank_slot1910, first_name Jeremiah, last_name
Trotter at pointer811FF3A0; this matches the user's selected player and baseline
free-agent slot1910. Captured trace privately in
analysis/AIBASELIN/trotter-live-observer.txt. This establishes a current-bank
record/name association, not a durable identity across saves or roster rebuilds.

Observed raw context+8 dword4D060004, context+0x0A byte06 and context+0x0C
word1949. Existing player salary word+0x0A, profile byte+0x26 and term byte+0x27
are zero. Currency units, offer years and packed flag meanings await displayed
UI comparison. No AI decision, accepted signing, guest write or save/reload is
proved by this readback. Both corrected-source258c223 workflows completed
successfully: Build38589604849 and Franchise AI38589604925. Updated worklist
from pending readback to this limited actual runtime evidence.


## October 14, 2026 — Team getter audit and failed UI capture

Read-only audit confirms team-pointer identity is table association through
0x000C4CA0, with0x000C4D50 subsequently indexing0x00E5775C. The bank-backed
count/base fields are+0x18/+0x1C, stride0x1F4; independent baseline reads show
52 team records and base44A8. This does not verify the observed offer's club.

Attempted one game-only screenshot to reduce manual UI readback: fresh display1
window3000001 had exact ESPN NFL2K5 title, PID68889 and matching X input focus.
ffmpeg's window-specific X11 capture emitted an image-data BadMatch and produced
black pixels. No UI amounts can be inferred; this is not evidence of a black
game screen. Screenshot remains private/ignored, and no controller input, game
restart, guest write or save change was made. Displayed years/salary and live team
association remain pending user-visible confirmation. Existing Trotter trace is
unchanged; no additional speculative fields or financial interception were added.


## October 14, 2026 — Gildon offer display calibration

User first reported Trotter$19.9M/Balanced/40%/6years, which does not precisely
match earlier word1949; clarification was requested without inventing a unit
conversion. User then reported current$8.29M/Descending/40%/2years. Actual
current trace identifies Jason Gildon slot1792 with context word829, byte0x0A=2,
low byte+8=4 and packed style bits29..31=1 (dword2D020004). The current screen
thus gives exact user-visible offer calibration for Gildon. Preserved trace
privately in analysis/AIBASELIN/gildon-live-observer.txt.

Cross-checked display word-to-value helper0x000E5FF0 multiplies by10 and
0x0031E580 formats integer thousands/millions. This verifies the observed
Gildon total-offer path's$10000 raw-word scale, not general annual cap/bonus
posting or save persistence. AIBASELIN hash is still
2f82cfd9c608411c40b006db10f1e6dc6dfe46b187dd50c1ae94dd6341fd3dd2.
The next required input is a separate unchanged AICNTRL save before a documented
vanilla signing/result AIGILDON save and reload. No offer submission, guest write,
model request or save mutation was performed by the agent.


## October 14, 2026 — Actual unchanged-save control captured

User saved AICNTRL without signing. Stable payload size/mtime check passed during
private snapshot, and logical save, snapshot and UDATA container11270FC6861F
payloads share SHA256
be60a034c3bb0ecbf273ae4891a2aeecca613f5f074672ff049a358ba5bc8ec3.
Captured all companions privately in original/saves/AICNTRL-control and wrote
intake.json. TYPE is FXG, SaveMeta.xbx is BOM-prefixed UTF16 Name=AICNTRL with
CRLF, and EXTRA matches the runtime's zero16-byte-key HMACSHA1. An initial
analysis assertion incorrectly expected a bare SaveMeta name; corrected the
read-only check to its actual metadata format. No save bytes were edited.

The control has the same year2004 and1937 player memberships as AIBASELIN;
roster list order changed, so comparison uses memberships as sets. Neither
salary word+0x0A nor candidate packed contract bits (mask0x0FFF000F at+0x24)
changed across all2479 bank records. This verifies only candidate fields, not
all financial state. Payload differs in14405bytes across1724spans; preserved
all changes in private analysis/AIBASELIN/control-diff.json instead of assuming
all differences are harmless bookkeeping. AIBASELIN itself still hashes
2f82cfd9c608411c40b006db10f1e6dc6dfe46b187dd50c1ae94dd6341fd3dd2.

Next controlled transaction: reload AIBASELIN, document Gildon's visible
$8.29M/2year/Descending/40% offer and cap room, perform one original-game signing,
save separately as AIGILDON if accepted, and verify reload/terms/cap readback.
If rejected, capture the result rather than silently changing terms. AI signing
remains unconnected; the experiment establishes actual save/financial mapping.


## October 14, 2026 — Actual Gildon signing/save and cap reconciliation

User completed the instructed signing/save/reload sequence as AIGILDON. Captured
stable private payload and all companions; logical save, snapshot and UDATA
container10A484FEF273 agree on SHA256
ac16245c5fcd743f3cc9e6aa37d76de72424238782de353765c758d242c6bc7d.
TYPE/Name metadata and runtime-key HMACSHA1 validate. AIBASELIN stays unchanged.
Actual result moves only Gildon slot1792 from free agents to Giants. Candidate
salary word changes0→829; packed contract word00100BA0→02410BA2 preserves
2/2 term nibbles, allocation4 and shape1. Original-game cap total changes
72272→77038; accumulator+0x19C stays0. Control-aware diff preserves14405 overlapping
bytes and identifies22 transaction-only bytes; only Gildon's candidate financial
fields change. Private reports are in analysis/AIBASELIN.

User supplied before/after UI: cap80.50M both; team72.27M→77.03M; room8.22M→3.46M.
These match exact stored totals72.272M→77.038M and remaining8.228M→3.462M, with
first-year delta4.766M. UI truncation must not become ledger rounding. A bounded
read-only /proc/68889/mem check was refused by OS permissions; no debugger attach,
sudo, elevation or bypass was attempted. Direct live cap-global read is not claimed.
User explicitly confirmed post-reload Descending annual rows: 2004 salary$3.10M
and bonus$1.65M; 2005 salary$1.86M and bonus$1.65M. This completes this
original-game contract UI reload check. Displayed rounded/truncated amounts
are not exact annual ledger values; modern accounting remains unverified.

Implemented small read-only tools.inspect_player_contract for supported observed
styles and active records, with named-membership validation and no cap/guarantee
inference or ratings exposure. Three authored tests cover calibrated values,
malformed/unknown contracts and slots, and CLI byte preservation. Full612-test
offline suite passed. Actual AIGILDON readback matches the documented deal.
No AI/game financial write integration is present, and modern lifecycle/posting
correctness remains open.


## October 14, 2026 — Signing-screen control handshake callback

Published16d3c966 passed Build38597224057 and Franchise AI38597224100.
Added the required-control hello request to the existing observed Sign Contract
FSM callback (descriptor0x00557B2C), independent of opt-in diagnostic tracing.
The callback submits/polls without waiting and only on the transport owner
thread. An outstanding hello is not duplicated; transport/take failures block
further submissions until explicit host shutdown/restart. Receipt is not
authorization: the native client still validates grants before any AI operation,
and the service checks remote control again per request. No control renewal,
model requests, guest writes or automatic fallback is added. Default provider
configuration remains disabled.

An authored Windows transport test covers default-disabled behavior, unrelated
FSM events, foreign-thread rejection, pending/consumed hello, oversized replies
and explicit stop/restart. Release assertions remain enabled. The private
licensed MSVC build passed /W4 /WX and the test executed under Wine. Full
private Windows NFL2K5 target compiled and linked; all612 offline tests passed.
The actual game has not executed this configured callback yet, so owner-thread
association and remote hello in the live game remain unverified. Contract
judgment and financial mutations still use original game logic.

The actual native pipe client and revised lifecycle test also compiled and
executed against the inert stalled peer under Wine (exit0). Its callback submit
and immediate poll completed within the1000ms guard. The initial manual
compile omitted the target's existing NOMINMAX definition; corrected the manual
command to match CMake, with no source change needed. Staged private next game
SHA256e6c10393d53b1cc355e981d612779fed96fbeeadd9ef8f7e067014a8a262b9aa.
Installed executable remains SHA256
1f1aa6150ba5d2046c4dc4c2067c008db2aab04232ef0bc664aaa1b5d33ab1b3
and game PID68889 remains active; no game restart or input was sent.
