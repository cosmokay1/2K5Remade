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


## October 14, 2026 — Original annual rounding reconciled

Extended the read-only contract decoder with supported original Descending
and Balanced annual rows. Static E6020/E6040 evidence establishes integer bonus
allocation, float32 store/conversion boundaries and final salary truncation;
private image jump-table and constants confirm code1/code2 dispatch. No original
code bytes or disassembly are published. Gildon reconstructs salary3108K/1865K
and allocated bonus1658K each year. Year0 charge4766K equals the controlled
saved team delta. Both rows match user-confirmed UI after reload. Summed original
postings8289K differ from offered8290K; the decoder exposes rather than repairs
that residual. Modern engine bonus conservation remains unchanged.

Five focused tests passed, including actual-observed terms, unchanged payload,
rounding residuals, Balanced truncation, one-year/zero/full-bonus endpoints and
unsupported inputs. Actual AIGILDON private readback was regenerated without
editing the save; payload hash remainsac16245c5fcd743f3cc9e6aa37d76de72424238782de353765c758d242c6bc7d.
Later-year exact postings remain static reconstruction until season advancement
evidence exists. No AI judgment or guest financial write was added.


## October 14, 2026 — Full original roster payroll reconciled

Extended the original static annual calculator to raw codes0..7 without adding
unverified UI names. E6380 selects the year index from original minus remaining
terms; C3F00 skips zero remaining terms and sums salary/allocated bonus. Added
tools.reconcile_franchise_payroll to read all32 clubs, reject unsupported active
fields and return exit3 on any stored/reconstructed difference. This is read-only
original payroll evidence, not a modern ledger import or cap authorization.
Additional246F20 mode-specific obligations remain undecoded; differences are
reported rather than guessed away.

The actual AIBASELIN, unchanged AICNTRL and signed AIGILDON each match all32
stored team+0x124 totals exactly. Active contract counts1696/1696/1697 and Giants
72272K/72272K/77038K agree with independent stored quantities. All prior payload
hashes remain unchanged; complete private reports retained in analysis/AIBASELIN.
Eleven focused tests passed across contract/payroll readers: all schedule
directions/midpoints, one-year endpoints, known signing, term-index selection,
inactive records, malformed active fields, mismatch exit and byte preservation.
No ratings, guest writes, paid calls or modern accounting changes were added.

Handshake revisiond61427b passed both workflows: Build38600646883 and Franchise
AI38600646884, including Windows native callback and lifecycle checks. Annual
revision283b0e9 Build38601087383 passed; Franchise AI38601087366 was still in
progress at inspection. Actual configured hello execution and AI signing remain
unverified.


## October14,2026 — Actual packed history bank extracted

Mapped player+2C to14E8A0/14E800 traversal and14EE40 signed low-word values.
Static filters establish statistic bits16..22, period23..27, deleted28, mode29
and terminal31; bit30 is retained as unknown. Added a small read-only selected
player history inspector with roster validation, aligned declared bank bounds
and mandatory terminator. It retains deleted/mode records and terminal values;
missing pointers remain unknown instead of zero. No metric labels, calendar
years or units are guessed, and no history is yet submitted to the model.

Actual AIBASELIN header360/364 declares36866 four-byte entries at41D54..65D5C.
All1937 supported members inspected:1325 present lists,612 null pointers,36866
entries, zero deleted entries and zero parse failures. Independently scanning
terminal flags and comparing segment starts to all player pointers verifies
exact bank partition with no gaps or overlap. Payload SHA256 remains
2f82cfd9c608411c40b006db10f1e6dc6dfe46b187dd50c1ae94dd6341fd3dd2.
Summary and Gildon/Trotter raw histories retained privately in analysis/AIBASELIN.

Four authored tests passed for signed values, mode/deleted/unknown flags,
terminal-value retention, missing-history semantics, malformed/unaligned/outside
bank pointers, missing terminator and unsupported slots. No retail fixtures,
ratings, save edits, game inputs or model requests were added. Targets, pressures
and QB-hit names/coverage remain unresolved; this bank is a source to investigate,
not permission to invent those counters. Prior839b986 passed Build38601670012
and Franchise AI38601670196;283b0e9 also completed both workflows successfully.


## October14,2026 — Five passing-history counters mapped

Read original A8A510 descriptor table (stride1C, offset0C history code).
Named live-QB fields04/23/4C/40/16 map to saved7/6/8/9/10. History reader
now labels pass attempts, completions, passing yards, passing touchdowns and
interceptions thrown, retaining raw code/period/mode/deleted/end fields.
Sparse missing metrics are not synthesized as zero, and no raw mode is
converted to played/CPU/fast-sim. No PerformanceEvidence or model submission
is created before coverage and identity binding are resolved.

Actual McNabb slot1146 period5/mode0 independently corroborates all five mapped
values against [NFL's career statistics](https://www.nfl.com/players/donovan-mcnabb/stats/career):
478/275/3216/16/11 for the2003 passing row. Private named readback retained in
analysis/AIBASELIN/mcnabb-passing-history.json; unchanged baseline SHA256.
General calendar assignment and simulated/played history remain unverified;
defensive candidates cannot be named from plausible values alone. Five focused
history tests passed, adding metric mapping with raw-key retention and missing
metric behavior. No hidden ratings, paid calls or game/save writes occurred.


## October14,2026 — Private Deck build installed; games/rushing history mapped

User explicitly closed normally. SSH pgrep verified no NFL2K5.exe process
before installation. Preserved the previous private executable as
runtime/NFL2K5.pre-handshake.exe (SHA256
1f1aa6150ba5d2046c4dc4c2067c008db2aab04232ef0bc664aaa1b5d33ab1b3),
then atomically installed the previously compiled staged binary SHA256
e6c10393d53b1cc355e981d612779fed96fbeeadd9ef8f7e067014a8a262b9aa.
This includes the d61427b host handshake changes; no new game execution or
configured remote hello is claimed. Steam launcher and controls are unchanged.
Actual Vertex sidecar/runtime identity and game financial imports remain gates
for AI decisions. The installed build still uses original signing judgment.

History descriptor fields63/03/50/3F map to codes0/1/2/3. Added named games,
rush attempts, rushing yards and rushing touchdowns, corroborated by McNabb's
baseline history and [NFL's published historical table](https://www.nfl.com/players/donovan-mcnabb/stats/career).
Private named readback retained without save edits. Six focused tests passed,
including signed rushing yards, separate passing/rushing TDs and no invented
target/pressure/QB-hit values. No model request, runtime control renewal or
guest financial mutation occurred.


## October14,2026 — Issued real-roster IDs and stable initialization seed

Added tools.franchise_snapshot_bindings with explicit create-once companion
files. UUIDs belong to a new local franchise namespace; slots and name/raw
biography guards constrain lookup. Exclusive create refuses overwrite; malformed
or missing bindings fail validation. Guard changes, duplicate IDs/slots, roster
intake/removal and calendar advancement reject automatic remapping. Financial
changes and supported same-year transfers do not regenerate identities.

Initial profile previews reuse existing initial_actor with persisted seed/UUIDs.
They are bootstrap input, not a mutable parallel actor store. Future financial
bootstrap must use the same IDs/seed before actual game negotiation consumes them.
No engine ledger is fabricated from incomplete modern contract sources.

Private actual baseline companion contains1937 IDs. Baseline, unchanged control
and Gildon signing all validate with1937 members and identical profile digest
631e23605125af89e211e7f4072f3a140ea5da68bebfd8d361d90043d172df02.
Gildon's ID persists from FA to Giants. Profile styles span all five authored
styles; these are fictional preferences, not assertions about actual people.
All three save hashes remain unchanged. Companion and evidence retained in
analysis/AIBASELIN.

Five focused tests passed for signing/financial change plus JSON restart,
biography/slot reuse rejection, membership/year migration gates, malformed
bindings and explicit create refusing overwrite. Cross-franchise selection,
bank rebuilds, drafting/year advancement and live guest binding remain unverified.
Published bd180f8 passed Build38603293266 and Franchise AI38603293274.
697c587 Build38604337494 passed; Franchise AI38604337319 was still in progress.

Successful bd180f8 job logs independently confirm625 full-suite tests passed
on both Ubuntu and Windows. New binding tests are focused local validation;
the new revision's full CI is not yet claimed.


## October14,2026 — Signing biography candidate boundary

Extended the existing bounded observer to emit raw04..07/19..1B bytes after
validated bank-slot/name readback. Uses the already read player prefix and
keeps trace opt-in/event limits; no guest writes or hidden ratings reads.
Factored the same canonical guard digest into file and observation matching.
New resolve_signing_candidate requires all typed fields and returns a candidate
UUID only; active franchise, calendar and financial state remain unconfirmed.
No live bridge operation or model request is added.

Actual observer C compiled with -Wall/-Wextra/-Werror against authored low-RAM
and separately backed physical-memory fixtures and passed byte-preservation
checks. Six binding tests passed, including altered/missing guard rejection,
wrong player slot and explicit non-authorizing candidate scope. Existing private
1937-member companion still resolves unchanged after the guard refactor.

The first private-build SSH attempt failed DNS resolution (exit255) while
source transfer session95526 was pending. The user restored Deck reachability;
that transfer completed successfully without restart. Local/remote main.c hashes
matchce717c2763d6a5bf9b54a2873d0d7926fae8201a02d01e15c04e726581384411.
The existing incremental private Windows build then compiled main.c and linked
NFL2K5.exe successfully. Process check confirmed the game stopped; retained
the prior executable as runtime/NFL2K5.pre-guard.exe and atomically installed
new SHA256a4648f45882f48ac12a322f7f7221585710a783fd89ddb91585262d9a0e4d67c.
Requested a read-only AIGILDON/Trotter offer-screen observation without submitting
an offer. Until its new trace is inspected, live guard matching remains unverified.
Published712582b passed Build38605154365 and Franchise AI38605154405.


## October14,2026 — Actual Trotter biography candidate matched

User confirmed the requested Trotter offer screen is open after the AIGILDON
load instruction. Actual session.log from active PID71410 reports slot1910,
Jeremiah/Trotter, pbp_photo_raw19051905 and dob_region_raw16b449. Installed
executable hashes to a4648f45882f48ac12a322f7f7221585710a783fd89ddb91585262d9a0e4d67c.
The authored resolver matches those live guard fields against the private pinned
companion and AIGILDON payload, yielding the existing Trotter candidate UUID.
Private evidence retained in analysis/AIBASELIN/trotter-live-guard-match.json.
No offer submission, guest write, model call or profile reroll was performed.

This verifies actual guard observation and offline candidate matching in this
controlled screen. The game bridge does not call the resolver yet; automatic
franchise selection, runtime calendar and whole-book financial reconciliation
remain required before a signing operation can use the candidate. Do not report
this read-only match as AI negotiation integration or financial authorization.


## October14,2026 — Private Windows Python service runtime

Added tools.install_embedded_python for explicit private CPython3.13.16 amd64
packaging. Official archiveSHA256
97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297
verified before extraction. LICENSE.txt and provenance retained; isolated ._pth
includes only bundled library, interpreter directory and explicit relative
authored application root. Existing destinations and bad hashes reject without
overwrite. Actual official-archive manual checks passed for notice/path/refusal
behavior. No pip, SDK, credentials, cloud infrastructure or control enablement
was added.

Installed privately in Deck dependencies/python-3.13.16; source-relative path
is ..\..\source. Wine9 execution reportsPython3.13.16/SQLite3.50.4 and imports
franchise.sidecar. Actual native bridge and C-host fixtures compiled and complete
tools.check_native_bridge suite exited0 with synthetic financial/lifecycle,
personality, restart and budget-policy checks. Log: python-pipe-check.log.
No model requests or retail data were used in these fixture databases.

Proton isolated-prefix check first failed because the prefix parent directory
was missing, then stalled its console host under headless SSH. Inspected the
known test processes/command/display state; stopped only its Python/conhost
processes after diagnosing the console wait. Switched the authored check to
pythonw. Import result verifiesPython3.13.16/SQLite3.50.4 and actual sidecar
source under Proton11.0-100. A second authored check launches the native C host
with CREATE_NO_WINDOW and exits0 after two synthetic handshake/preview/manual
sign/context/restart runs. Its charge10/room90 assertions are synthetic.
Result-artifact retrieval initially hit a transient SSH port22 timeout. After
the user woke the Deck, dependencies/python-proton-pipe-result.json was read
back successfully: packaged Python3.13.16 reports handshake, cap preview,
manual signing, player context and restart retry passing, with charge10/room90.
These are authored synthetic C-host checks under Proton, not game transactions
or paid inference. Actual game PID71410 remained running and was not interrupted.
Separate test prefix and private fixture DBs preserve the game prefix/saves.

Optional Google SDK vendoring, authorized scoped runtime identity, actual remote
hello and real-franchise import remain required. Game provider remains unset
and original signing judgment still runs. Publisheda4e89c1 passed
Build38606568296 and Franchise AI38606568593;0eb0135 also completed both workflows.
Published589bea2 Build38611029790 passed; Franchise AI38611029693 is still
in progress at this check and is not yet claimed successful.

## October14,2026 — Bounded signing team/cap probe installed

Audited original team getter mode at0x00E576A0 and both jump tables in the
privately supplied executable. Mode0 selects bank+18/+1C with stride1F4;
mode1/2 selects countE576AC and pointersE5786C. Added opt-in read-only
association with a52-record bound, validated bank geometry and unknown-mode
rejection. Matched records expose raw team+124 payroll and globalE3C278 cap.
They remain current-table locators and original unreconciled accounting;
no active-franchise identity, adjusted cap room or modern authority is inferred.

Actual observation source compiled with -Wall/-Wextra/-Werror and passed
authored bank/pointer-table, unsupported-mode/count, malformed-address and
separate physical-memory tests with byte-preservation assertions. Incremental
private Windows build compiled main.c and linked NFL2K5.exe successfully.
User confirmed game closed. The first installation guard matched its own shell
command filenames and safely refused without mutation; an exact process/launch
check confirmed no game process and installation then completed. Retained
runtime/NFL2K5.pre-team-probe.exe as rollback. Installed SHA256
0783c6e91751e8989d1b6c33720db27df5b6cf93cb72f999c39abcebf1053760.
Requested the same AIGILDON/Trotter screen without offer submission. Actual
team/cap readback remains pending; original signing logic is unchanged.

## October14,2026 — Actual signing team and raw cap matched

User opened Trotter after loading the requested AIGILDON. Installed SHA256
0783c6e91751e8989d1b6c33720db27df5b6cf93cb72f999c39abcebf1053760
and actual process73738 were checked. The new trace identifies Trotter slot1910
with the same biography guard, plus team mode2/table index15, payroll77038
and league cap80500. Index15 is Giants in the supported saved roster ordering;
the exact payroll matches AIGILDON and the cap matches prior user display.
Private bounded trace retained in analysis/AIBASELIN/trotter-live-team-cap.txt.
No game input, offer submission, financial write or control enablement performed.
This closes the specific live team/raw total association; it does not authorize
modern accounting or prove full franchise/calendar reconciliation.

Independent calendar audit identifies season-index getterC4EB0/globalE576B8,
display247AC0 adding2004, and scheduler serialization/load at record+6.
No new field is installed or inferred from another process's memory; actual
season-index and week/phase validation remain pending. The saved game-year byte
used by roster inspection is not accepted as independent runtime calendar proof.
Published589bea2 and ebb12a1 both passed Build and Franchise AI workflows;
5c83166 workflows38612170134/38612170392 remain in progress at this check.

## October14,2026 — Saved season boundary and binding guard

Traced original save/load composition: E2E00 prefix2E0, A5460 size0,
C1F90 roster header allocation+20, BFE50/16A0F0 span allocation+40 rounded
even, C5300 scheduler83DC, and 2D0780 franchise tail165B0. The new independent
tools.inspect_franchise_calendar derives the scheduler boundary from the declared
ROST span and requires exact section exhaustion, both tags and mode2/32-team
header. It exposes season-index/display-year from the independently audited
serializer/getter/display chain, leaving phase/step/counter meanings raw.

All three private baseline/control/signing saves locate the scheduler at91320
and yield season index0/display year2004; payloads were only read. V1 snapshot
creation/resolution now additionally require this saved season to match their
existing year constraint. An actual season change can no longer pass just
because a scheduled game's year byte remained unchanged. Unsupported divergent
calendar creation/migration rejects; existing companion IDs/profiles are not
rewritten. All1937 pinned members still resolve in each private save.

Nine focused calendar/binding/observer tests passed, including authored divergent
game/season years, malformed section lengths/modes and season-advance rejection.
No live calendar read, modern calendar import, automatic companion selection or
guest write is claimed. The currently installed Deck observer is untouched.

## October14,2026 — Private Windows Google SDK packaging checked

Resolved requirements-google.txt into25 PyPI Windows amd64/CPython3.13 wheels
and recorded exact versions/SHA256 in requirements-google-windows.lock.
Offline pip staging with --require-hashes/--no-index succeeded; each wheel
has included license/notice files retained. Private SDK PROVENANCE.json records
source index, lock hash and wheel hashes/notice paths. No binaries or credentials
are committed. A separate private python-3.13.16-google interpreter uses an
explicit sibling SDK path; the installed game runtime/configuration is unchanged.

tools.check_google_runtime uses explicit anonymous fixture credentials and never
discovers ADC or submits inference. Actual Deck Proton result artifact verifies
Python3.13.16, google-genai1.75.0, google-auth2.62.0, pydantic2.14.1/core2.50.1,
cryptography50.0.2. Compiled SHA256, response schema, actual Vertex client
construction/close, Requests transport and credential-free control rejection
passed. Artifact: dependencies/google-proton-result.json in the private build.
No cloud request, paid model, control enablement or game transaction occurred.

The extraction emitted macOS extended-header warnings; files still extracted
and imports/checks completed. Test wrapper PID73974/Steam stub73975 remain
live in do_wait/ntsync after the result was written; launch exit is not yet
verified. The same session67313 is retained for lifecycle inspection rather
than restarted. Actual game73738 remains running in its separate prefix.
Scoped runtime authentication/B05, live control/model checks and real-franchise
import remain required; SDK packaging alone does not satisfy them.

## October14,2026 — Explicit SDK cleanup and clean Windows check exit

Inspection of the same SDK test handle confirmed only Steam shim73975 and
test-prefix Wine services/explorers remain; no Python worker. Prefix matching
accounts for Proton's trailing slash. This is a launch-shim wait, not evidence
of a stuck SDK call. No process was restarted on observation timeout.

Added VertexProvider.close for the SDK client created by that provider; injected
clients remain caller-owned. Sidecar releases that owned provider on EOF or
transport failure, including initialized-client cleanup if later setup fails.
Cleanup errors produce only a generic stderr message and cannot replace a
transport error or leak SDK details into protocol responses. The offline SDK
check uses the same explicit close method.

Twenty focused provider/sidecar tests passed, covering owned/external clients,
repeated close, EOF, broken transport and cleanup failure. Staged only authored
source updates privately. The revised actual Windows SDK check through Proton's
own Wine executable exited0 and its google-direct-wine-result.json repeats all
five offline packaging passes. The separate original Proton Steam shim was
identified for targeted cleanup; game73738 and game prefix remain untouched.
No cloud call, credentials, grant or real-franchise transaction is involved.

## October14,2026 — Saved cap accessor branches reconciled

Added tools.inspect_franchise_cap using the validated scheduler/section layout,
original franchise-tail league cap and serialized team flags. Audited13EC30's
C4D50 delegation and13ECA0's conditional first-year accumulator subtraction;
reports both adjustment branches, never guesses which runtime caller requests it.
Requires all32 original roster payroll totals to reconcile before reporting.

Nine focused cap/payroll/calendar tests passed, including nonzero authored
accumulator with flag on/off, signed-cap rejection and mismatched payroll.
Actual baseline/control/signing reads confirm cap80500000, Giants flag1,
zero first-year accumulators across32 teams, room8228000 before/3462000 after.
No modern liability, cash settlement, guarantee or guest mutation is inferred.

User explicitly selected the2004 dollar economy: retain80.5M cap and scale modern
minimums/rookie amounts proportionally. Source reference year/cap and precise
posting still need implementation before a legal import. Existing contracts
must not be inflated or revenue changed merely to make signings affordable.

The prior SDK test shim cleanup completed: only verified test PID73975 was
sentSIGTERM; original wrapper returned241 after deliberate cleanup. The revised
direct Proton-Wine SDK check independently exited0; the old wrapper is not
claimed to have exited naturally. Published409a3ce and3aeb93f passed both CI
workflows;03dda17 workflows were in progress at this check.

## October14,2026 — Approved historical economy conversion

Verified NFL's official2026 cap publication at301.2M; retained its URL with the
conversion policy. HistoricalEconomy uses verified target cap and exact ratio,
ceil minimums/floor ceilings to1000-dollar units, and maps game2004 to published
2026 CBA minima. Later game years advance the published minimum table with a
fixed reference ratio, rejecting beyond2030 rather than inventing future rules.
It never rewrites existing contracts or the league cap and does not alter revenue.

With80.5M target the ratio is805/3012, zero-credit active floor237000 and7+credit
floor348000. Drafted/undrafted four/three-year minima use237000/249000/261000/
273000 as applicable. Drafted allotments require supplied typed source inputs
with reference-year minima; no actual pick/club allocations are guessed.

Thirteen focused conversion/minimum/rookie tests passed. Actual Ledger preview
rejects347000 against the scaled348000 veteran floor, accepts348000, preserves
80.5M cap and zero fixture charges. Rookie fixtures reject underpayment and
insufficient scaled pool; allocation fixtures are authored, not official pick
values. Actual guest encoding, original obligation/guarantee conversion and
persisted source policy remain unintegrated. No new Deck build or model request.

## October14,2026 — Historical salary policy survives engine restart

VeteranMinimumProfile accepts an optional typed HistoricalEconomy. Published
rule years remain2026 onward; converted floors use the stored exact policy.
Serialization retains target/reference caps, year/source/version and posting;
strict deserialization refuses altered source/reference/posting metadata.
Unscaled profiles preserve their existing JSON shape. Negotiation context
now includes adaptation provenance alongside the original CBA floor source.

Actual SQLite fixture restart preserves scaled348000 floor and rejects347000;
durable Store signing at348000 replays identically on another load. Changing
the target conversion cap without matching the stored floor rejects replay.
Year transition checks the same adaptation before mutating any finances;
authored removal/replacement attempts leave financial/cash/generation snapshots
unchanged, while a transition retaining policy advances sourced floors.

Initial full suite ran643 tests with four HTTP/TLS loopback-bind permission
errors in the sandbox; no financial regression failure. After the rollover guard
and its boundary test, full offline suite outside sandbox passed644 tests in
21.422s. No cloud/model request or game/save write was performed. This validates
durable engine policy, not guest calendar/contract import or AI signing.

## October14,2026 — Legacy opening policy and live calendar probe

Read-only AIGILDON audit counts1697 active contracts;195 bonus-bearing contracts
have original term above5 years across31 clubs. User explicitly approved keeping
existing deals as legacy schedules while modern rules govern new agreements.
Recorded preservation/unknown-liability boundaries in the money audit. No
retroactive five-year proration or original term/cap rewrite was performed.

Extended opt-in signing observer, only for verified mode2 club indices below32,
to read serialized-calendar globalsE576A4..E576BC, team flagE5775C[index] and
uint16team+19C accumulator. It displays2004+bounded season index and leaves all
phase/step/counter/adjustment meanings raw. Unsupported index values/read faults
remain unverified; no signing authority or guess about the caller's adjustment
argument is produced. Uses the same fault-safe original-pointer reads.

Five focused observer/calendar/cap tests passed. Actual observer source compiles
with-Wall/-Wextra/-Werror and preserves low/high memory bytes, including authored
mode2/nonzero accumulator and invalid-season checks. Source staged for a private
Windows build; installation and actual live calendar read remain pending.
The currently running game is not interrupted.

Incremental private Windows build completed compilation/linking successfully.
Staged executableSHA256dd2a51bfa1022e9a723b227117d335985957f3bf2c968cdcc2ee48d4563e9df4.
Installed observer remains0783c6e91751e8989d1b6c33720db27df5b6cf93cb72f999c39abcebf1053760;
game73738 is still running. Requested normal exit before installation; no running
executable/prefix/save was replaced. Published4e57db8 passed both workflows
38615267863/38615265206;02aa02f CI is still in progress at this check.

## October14,2026 — Typed preserved legacy schedules from actual saves

Moved the existing original annual calculator into franchise.legacy_contracts;
the inspector retains its public function import and unchanged arithmetic.
Added immutable LegacyContract with original raw terms, stable player ID and
source; serialization preserves the original8-year fixture and Gildon's1000
rounding loss without manufacturing nominal paid cash or guarantees. This type
is deliberately distinct from modern ActiveContract; no five-year rewriting.

The export helper requires pinned identity/calendar validation and independently
reconciled saved cap/payroll, then validates each team's sum of legacy current
charges. Inactive or unsupported roster contracts fail instead of becoming zero
obligations. Actual baseline/control/signing produce1696/1696/1697 records;
all32 team totals match, Giants72272000/72272000/77038000. Existing IDs retained.

Fourteen focused legacy/contract/payroll tests passed, including serialization,
immutable terms, long bonus horizon, rounding loss, source identity, malformed
records and payroll mismatch. No database/game/save writes or model requests.
Opening-book ownership/generation integration, unknown legacy liability handling
and actual lifecycle/season validation remain required. Staged calendar observer
installation still awaits normal game exit; this source work does not replace it.

## October14,2026 — Durable legacy cap obligations and exclusive ownership

OpeningBooks now stores legacy schedules separately from modern contracts,
rejecting duplicate players across both kinds/tenders. Ledger derives preserved
charges and signed ownership from those records; generation identities cover
modern agreements only, avoiding fictional legacy cash generations. Strict source
balance/ownership checks include legacy records. Financial checkpoints retain a
canonical schedule digest/count without expanding every receipt with raw terms.

Legacy IDs are registered for initialization/read context, without invented modern
minimums. Existing unadapted books/contexts retain prior shapes. Inventory/player
context explicitly expose preserved records and unknown liability scope. Cash
initialization, calendar migration/aging and roster-status projection reject
unsupported legacy conversion; no missing payment/guarantee is guessed zero.

New fixture tests verify restart ownership/personality, cross-team theft rejection,
cap rejection after legacy charges, legal new signing/replay, unchanged legacy
schedule digest and no mutation on unknown cash/calendar attempts. Full offline
suite outside sandbox passed650 tests in33.681s.

Created only private analysis/AIBASELIN/legacy-cap-import-check.sqlite from actual
AIGILDON typed exports and pinned seed/IDs. All32 teams reopened with1697 owned
legacy players/actors, exact matching current charges and original seeded traits.
Cap80500000 is sourced; reserve0 is provisional. This private validation has no
registered free-agent floor inputs, cash/rookie/calendar import or live game
configuration and is not signing authority. Game/save/control remain untouched.
Publishedb6cf85f passed Build38616885315 and AI38616885613; logs confirm647 tests
on Windows and Ubuntu.334268e also passed both workflows.

## October14,2026 — Native legacy player-context validation

Reviewed manual-sign/preview responses against legacy-backed books: they remain
bounded offer receipts and do not copy full financial snapshots. Found that
native player-context validation ignored newly added legacy fields. Added paired
record/scope validation, exact seven fields, matching player identity/nonblank
source, integer original term/amount/bonus/style bounds and rejection of modern
accounting/calendar conflicts. No legacy field grants AI or financial permission.

Portable CMake native protocol check compiled with AppleClang21 and passed
CTest protocol_boundary, including a valid8-year record and ten corrupted
identity/bounds/extra-cash/scope cases. Actual private Gildon player context from
the AIGILDON-derived ledger passed Bridge with explicitly denied AI access, then
the compiled native decode_response/validate_result path. No model or signing
was requested. Private context/checker artifacts are ignored, not published.

Deck process73738 still runs the installed observer, so staged calendar probe
installation remains pending normal exit. No game inputs, executable replacement,
save writes or remote-control changes. This validates a real saved-context/native
serialization path, not the live root hook or Windows pipe/game transaction.

## October14,2026 — All observed free agents initialized with unknown floors

Added immutable observed identity registry/source to Ledger bootstrap/replay.
Declared identities join initialization and read context but do not qualify as
classified modern owners or acquire a fabricated minimum. Pending context is
explicit and source-labeled; native validation rejects missing/contradictory
pending metadata. New owned modern books still require a real classification.

The boundary test exposed Negotiation invoking a provider for a declared player
with unknown salary rules before eventual signing validation. Added pending
classification rejection before inference. Test verifies provider never called,
manual rejection and unchanged financial snapshot/personality across restart.
Full offline suite outside sandbox passed652 tests in46.035s. Portable native
protocol compiled/passed with valid pending context and four invalid variants.

Private complete-personality-import-check.sqlite was created from actual AIGILDON
legacy exports and240 pinned FA IDs, preserving the original seed. All32 clubs
reopened; all1937 unique players have exact expected fictional initial traits,
and current legacy payroll matches each saved total. Trotter1910 now has a
persisted readable personality with classification pending. Its actual private
Bridge read, with AI denied, passed the compiled C++ response validator.
The checker's fixed success label says legacy context; this run's input is the
pending Trotter record, not a legacy owned contract.

No inferred credited seasons, missing floors, cash or rookie inputs were supplied.
Reserve0 remains provisional; the private database has no guest signing authority
or runtime configuration. Active calendar/live-save binding, sourced FA minimums
and actual root signing integration remain required. No game/control change.

## October14,2026 — Career-relative history calendar corroboration

Investigated Trotter salary classification without age/ratings. Actual record
current-period bits are7 for Trotter,6 for McNabb,11 for Gildon. Trotter history
periods1..6 match NFL career1998..2003 games; McNabb periods1..5 align1999..2003
with counter6. Raw period5 therefore cannot represent one calendar year across
all players. Added the raw current-period field and explicitly scoped
calendar_candidates, preserving unknown periods/bit30, modes, deletion and
missing evidence rather than fabricating dates.

Nine focused history/calendar tests passed. Private actual Trotter/McNabb
candidates produced the expected sequences from saved year2004. This supports
candidate alignment, not universal season-mode or paid-status verification.

Read official CBA Article26 section2 directly: salary-credit definition differs
from NFLPA's general benefits FAQ, including IR exclusion. Recorded source/section
and refused to substitute retirement-credit rules or assume missing pay/list
eligibility. No credit count/minimum was assigned; Trotter remains pending.
No database/game writes, model calls or control changes.

## October14,2026 — Runtime IAM gate revalidated and scoped proposal prepared

Read service-account policy using current administrative CLI login: no direct
delegation bindings. Existing audit_runtime_iam independently confirms exact
runtime prediction/service-use grants, object-get restricted to ai-control.json,
no direct switch-write grant and zero user-managed keys. No inherited-permission
or effective model-access claim. No owner control-read/inference fallback,
impersonation token request, IAM mutation, paid model or killswitch change.

CLI initially selected unsupported systemPython3.9. Selecting already installed
Python3.12 through command-local CLOUDSDK_PYTHON resolved it; no install or global
environment change. Private runtime-delegation-proposal.json names the existing
administrator, exact target/role and fixed request-time condition ending
2026-10-15T19:10:27Z. No administrator identity is published in source docs.

Requested explicit approval for this time-limited service-account-only binding.
Explained the earlier automatic review rejection of persistent IAM delegation;
approval remains pending. Built-in Token Creator includes token creation/signing,
not just reading control. No automatic renewal or expiry extension is proposed.
Independent game/book work remains available; the overall goal is not blocked
or complete solely because live scoped-runtime verification awaits this input.


## October14,2026 — Approved temporary runtime delegation verified

Applied the explicitly approved Token Creator binding only on the configured
runtime service account for the existing administrator. Independent policy read
verified the exact role/member, one direct conditional binding and unchanged
fixed expiry2026-10-15T19:10:27Z (October15,12:10:27PM PDT). No renewal is authorized.

Explicit CLI impersonation successfully read ai-control.json under the runtime
identity. Safe parsed evidence: protocol1, enabled=true, existing control expiry
2026-10-20T19:20:26.943409+00:00; library validate_control allowed it. No token was
printed, control changed or model/count request made. This resolves the direct
IAM permission gate for that CLI read; it does not prove inference or game access.

Actual sidecar runtime_credentials/GoogleControl verification refused before
object access. Follow-up identified DefaultCredentialsError: local application-
default credentials are unavailable. CLI authentication is a different source.
No owner fallback, credential copy, key creation or login mutation. B05 now tracks
runtime authentication instead of pending delegation approval. Game signing and
Deck integration remain unchanged and unverified.


## October14,2026 — Calendar observer installed; signing checkpoints authored

User confirmed normal game exit. SSH independently found no game process, checked
both executable hashes and installed the staged334268e calendar/cap observer by
rename after preserving NFL2K5.pre-calendar-probe.exe. Installed SHA256
`dd2a51bfa1022e9a723b227117d335985957f3bf2c968cdcc2ee48d4563e9df4`;
backup `0783c6e91751e8989d1b6c33720db27df5b6cf93cb72f999c39abcebf1053760`.
Requested the same AIGILDON/Trotter offer screen without submission once; awaiting
that runtime observation. No automatic launch, signing or save modification.

Authored three reproducible apply-gen-patches checkpoints in shared323D80:
entry323D80 (ecx/context, edx/output, safely read caller), interactive judgment
return323F13 (esi/context, ebp/output, eax/return), and precommit323F17.
The latter can also be reached by the original judgment-bypass path and is not
proof of commit. Bounded observer uses existing guest-memory helpers, raw offer
fields and pinned-biography guard inputs; no skill ratings or AI requests.
All branches remain original; it neither replaces acceptance nor alters terms.

Actual extracted C observer harness passes C11/Wall/Wextra/Werror with authored
low/high RAM, disabled/no-read behavior, invalid context/output/caller pointers,
unchanged guest memory and a separate256-event limit. Full offline suite passes
653 tests in24.957s. Latest completed source1548831 has Build38621703475 and
AI38621703539 success; logs verify653 tests on Windows and Ubuntu. ca73789 AI
run38622309030 was still in progress when inspected, not claimed passing.

Private patch application matched all three actual generated labels. Initial
incremental build compiled the observer but used the pre-existing optimized
build/gen-locals copy, so it did not establish linked callsites. Applied the same
three patches to that actual compile input and started the required rebuild.
The installed calendar observer remains unchanged during this independent build.
No generated guest code/assets or private binaries are included in the commit.
Actual checkpoint execution and AI/modern signing/save integration remain pending.


The required rebuild completed successfully with MSVC: optimized recomp_0022.c
compiled and the game linked. COFF relocation inspection shows exactly three
nfl2k5_diag_signing callsites in that compiled object. Staged EXE SHA256
`1bbad443ce59a46eb8e963634952fa11177e4a0f4cb0413c8c700d132d0cf985`.
The user had not relaunched; a fresh process guard confirmed the game still
closed. Installed the combined calendar/transaction observer by rename, retaining
NFL2K5.pre-transaction-probe.exe with the calendar-only hash above, so another
exit cycle is unnecessary. Installed hash verified exact. No signing, game launch
or save write. The already requested AIGILDON/Trotter screen remains the next live
check; old session.log has no new calendar/checkpoint evidence and is not reused
as proof of this build's execution.


## October14,2026 — Exact new-contract guest format boundary

Implemented GuestContractTerms and guest_terms_for_offer using the calibrated
original annual-row calculator. Context extraction follows323D80's actual field
copies (bonus low nibble, term bits16..19, schedule bits29..31). New terms retain
nominal signing bonus; they do not invent a smaller bonus to hide truncated guest
allocation. Modern charges must equal every original annual charge exactly.
Bonus-bearing terms over5 years refuse; existing legacy schedules are unaffected.
Exact encoding checks all annual salaries/bonus, whole-thousand posting and term
bounds. Positive bonus yields at most10 amount candidates; zero-bonus shapes use
bounded binary search. Unrepresentable annual vectors and positive guaranteed
base refuse without changing terms. This is a compatibility boundary for a first
supported guest path, not a restriction on the independent engine's broader modern
contract rules. Arbitrary modern schedules/guarantees need authoritative override
storage and guest lifecycle hooks before they can be used in the game.

Seven focused tests cover all8 shapes/15 zero-bonus terms, exact positive bonus
allocation over1..5 years, malformed raw fields, impossible vectors/protection,
calibrated Descending rounding and cap/minimum rejection with unchanged ledgers.
Full offline suite passed660 tests in22.351s. Private read-only report from actual
AIGILDON saved slot1792 decodes829/4/1/2, returns the exact $4.766M/$3.523M charges,
and encodes an identical economic offer. No save/legacy migration or guest write.
Report remains private in .local-runtime/guest-contract-compatibility.json.

Fresh Deck check still found no game process and only old session.log evidence;
no new-build runtime claim. The requested Trotter offer screen remains pending
without another prompt. Published ca73789 Build38622308971/AI38622309030 completed
successfully. Checkpoint57a7c1f Build38623459291 passed; AI38623459396 was in progress
at inspection, not claimed passing. No cloud/model/control or installed-game change.


## October14,2026 — Noncommitting game-facing negotiation proposals

Audited bridge ordering: existing negotiate commits the independent ledger on
model acceptance, before any possible guest confirmation. Added explicit
negotiate_proposal through the actual Bridge/Negotiation/sidecar/native boundary.
It retains the same required remote handshake and provider budget. Eligible
acceptance records accepted_proposal dialogue plus a financial preview; it never
changes cap charges, ownership, cash, revision or contractual promises and returns
no signing charges. Other outcomes preserve proposal mode. Existing committing
engine operation remains compatible but must not be used at the guest judgment
boundary. This is a required integration step, not an implemented guest transaction.

Durable accepted preview is recomputed inside recording's SQLite transaction and
on financial replay. Recording checks global ownership/draft rights/current
revision and control again before insertion. Accepted retry rechecks current
state without another inference. Request reuse across commit modes/terms refuses;
ordinary signing cannot reuse the dialogue ID. No operation to promote a proposal
or commit to the guest exists yet; commit readback/recovery/save/load remain open.

Sidecar audit found its worker selection matched only negotiate. Updated both
AI operations to share the one-worker/busy admission and disconnect behavior;
proposal inference cannot block stdin dispatch. Native host blocks proposal
submission without hello, and response validator rejects claimed signing/charges,
wrong mode, inexact preview and mismatched evidence/preview revision.

Eight proposal tests cover unchanged finances/restart, no repeated inference,
mode/term promotion denial, stale state/foreign ownership, over-cap acceptance,
counter/rejection persistence, disable during inference and tampered durable
preview. Added real sidecar proposal/restart and mixed-operation busy/EOF tests.
Full final offline suite passed670 tests in24.759s. Portable native protocol
compiled and CTest passed with accepted proposal and7 corrupt variants.
Actual synthetic Bridge acceptance JSON passed a freshly compiled native decoder;
its private reused checker prints a fixed legacy-context label, which is not a
real-save/legacy execution claim. Added Windows C ABI before-hello refusal and
post-hello synthetic proposal rejection/restart assertions; published Windows
execution of those new assertions is pending CI. No actual game/provider auth,
paid inference, installed executable, control object or save was changed.
Fresh Deck check still found no game process and only old log evidence; the
requested installed-observer Trotter screen remains pending without re-prompting.


## October14,2026 — Windows proposal fixture connection cleanup repaired

Published482c364 Build38625232889 passed, but AI38625232792 failed in Windows
Python cleanup of test_tampered_durable_preview_is_rejected_by_financial_replay.
The new test used sqlite3.Connection as a transaction context manager, which does
not close the connection; Windows WinError32 prevented temporary database removal.
Changed the fixture to explicit contextlib.closing plus the transaction context.
The assertions and production proposal behavior are unchanged; no ignored cleanup
errors or weakened test. Eight focused proposal tests pass locally.

Ran all eight repaired proposal tests using actual Windows CPython3.13.16 AMD64
under the existing Deck Proton Wine runtime in the separate python fixture prefix.
The process exited0; retrieved JSON confirms sys.platform=win32,8 tests and success,
including cleanup after tampered-preview refusal. No game prefix, save, executable,
cloud credentials or paid inference was used. Only authored Python files/fixture
were copied to the private source check tree. Published Windows/native checks
still need a successful replacement CI run; this focused proof is not gameplay.


## October14,2026 — Pinned saved performance reaches negotiation context

Added saved_player_performance: validate same-year UUID/biography bindings, then
export only descriptor-backed named history counters under that stable player ID.
No ratings, aggregate sums or invented current-week/played/CPU/fast-sim coverage.
Each record retains its source entry, raw mode and candidate calendar year.
Deleted/unknown-bit30/unmapped/negative-count records are excluded with explicit
counts; signed yards remain valid. Missing history/metrics stay unknown. Tackles,
targets, pressures and QB hits remain unmapped. Export does not establish salary
credit, promise coverage, the active game snapshot or signing authority.

Negotiation now rejects an explicit foreign performance player_id before actor
binding/provider context. Shared model instructions explain historical/raw-mode
and candidate-year limitations. Six authored tests cover source binding/biography
refusal, actual Negotiation provider-context consumption, null history, deleted/
unknown/unmapped/negative counts, signed yards, raw mode and foreign-player denial.
Final full offline suite passes676 tests in25.155s.

Private actual AIGILDON exports retain Trotter's6 named game-count records,
McNabb's44 named records across all9 supported metric names, and Gildon's10 game
records. Trotter/Gildon have42/58 unmapped records respectively; those are not
called tackles or sacks by guessing. Kept reports private in
.local-runtime/performance-context-readback.json; no save/game/control/model call.
This export is usable as the bridge performance input but the real root game
snapshot resolver/live consumption and salary classification remain pending.
Latest completed published33db7a3 Build38624020793/AI38624020917 are successful;
logs verify660 tests on both Windows/Ubuntu.482c364's failed Windows fixture is
addressed separately by42d02fb; replacement CI has not yet run for these local
commits. No claim of actual AI signing, new-build execution or save/load delivery.


## October14,2026 — Deck Windows runtime control read verified

Used the approved conditional runtime delegation to mint one900-second service-
account token with explicit impersonation. Local metadata conservatively expires
890seconds after mint start, within the existing fixed grant expiry. Owner ADC,
refresh credentials and service-account keys were not copied. No paid generation
or token-count request. SSH transferred the token into a700 test directory with
mode600, and the Mac copy was removed after transfer.

Actual Windows CPython3.13.16/Proton called production GoogleControl with explicit
nonrefreshable credentials. Authenticated control object read/validation succeeded.
Forced credential expiry then denied before another object request; no owner/ADC
fallback. Production control.py SHA256 matched on both hosts:
4565c16030075eec76cc8aec591ae4d7bccb367f9dbaa66b6bc8eb30f02ea10d.
The checker deleted the Deck token in finally. Independently verified absence of
both temporary files. Safe win32 result reports handshake=true, expiry denial=true,
model_called=false,control_changed=false. This was one isolated component check,
not a game hello, persistent auth setup, token renewal or control/IAM extension.
B05 remains persistent authentication/game execution, not inability to perform
any delegated Windows control read.

## October14,2026 — Native fixture context-index failure repaired

Replacement684168e Build38626325409 passed. AI38626325397 reached/passed Python,
audit/examples, Windows native compilation and protocol checks, then failed at
check_native_bridge.py755: an unchanged replies[3] assertion compared the manual
signing receipt to player_context after adding the proposal at index2. Corrected
that one assertion to replies[4]; no production behavior or expected state changed.

Privately compiled the current C host/client/protocol fixtures with MSVC, then
executed the actual C ABI/Windows sidecar with packaged CPython under isolated
Proton. Both runs verify5 replies, hello, preview, explicit proposal rejection,
manual signing, full player_context comparison and durable restart. Process exited0;
retrieved win32 artifact confirms charge10 and room90. No game EXE installed or
asset/save/model/control mutation. The broader hosted replacement run remains
required; the previous run's native failure is not reported as success.

## October14,2026 — Defensive history unit investigation

Read descriptor field0x32→history18/current getterC9C40 at+184, and field0x2F→
history19/current getterC9C80 at+17C. Named presentation API fields alone do not
prove these guest labels. Raw18 totals differ from modern NFL tackle totals;
no tackles mapping was guessed or normalized. Gildon's ten pre-2004 raw19 values,
divided by2, match [NFL's sacks column](https://www.nfl.com/players/jason-gildon/stats/career).
Trotter's final candidate differs from [NFL's table](https://www.nfl.com/players/jeremiah-trotter/stats/career).
This supports a half-unit sack candidate, not universal live/coverage verification.
No defensive code was added to named exports yet. Raw histories remain private,
with no ratings or invented targets/pressures/QB hits introduced.


## October14,2026 — Corroborated historical half-sack units exported

Mapped saved history19 to sacks in half-unit storage, retaining raw signed values,
exact scaled halves and an explicit inference scope. Descriptor field2F and the
previous ten-season Gildon/NFL comparison support this historical interpretation;
no live-update or coverage proof is claimed. Game values remain authoritative for
this export: Trotter's final saved value is not rewritten to match a different
modern NFL table. Deleted/unknown-bit30/negative counts remain excluded. Missing
sack entries are unknown, not synthesized zero or pressure/QB-hit estimates.

Private actual export retains Gildon's ten sack entries and Trotter's four sparse
entries. Kept raw/converted readback in .local-runtime/half-sack-history-readback.json;
no save, game or model changed. Added exact half-unit history/export tests and
negative-half-counter exclusion; existing raw metadata/missing-metric tests updated
for the new supported metric. Focused15 tests pass; full offline678 tests passed
in17.096s. No new minimum classification or credit count supplied.

Asked once for the missing minimum-salary policy: saved historical3+game simulation
credits, conservative highest-tier floors, or exact credit records. Original game
pay/list history does not supply the full modern credit inputs. This policy input
and the already requested actual Trotter screen remain pending; neither silence
nor a preselected option authorizes assigning new financial classifications.

Replacement1dc42a4 Build38628432683 and AI38628432855 completed successfully.
Hosted logs verify676 tests on Windows/Ubuntu and repaired native plain-C
host/context/restart execution. That validates the earlier checker repair;
new half-sack source678 suite still requires its subsequent published CI.
Persistent runtime auth, actual guest signing and save/load integration remain open.

## October14,2026 — Root transport diagnostic built and privately installed

Deck access restored; freshly verified no game process and unchanged installed
game/launcher hashes before installation. Added bounded diagnostic logging of the
startup transport owner and the first foreign-thread signing callback. A foreign
callback still performs no IPC and never assumes ownership. Default provider-unset
behavior and all signing/accounting behavior remain unchanged.

Actual private MSVC compilation passed for NFL2K5 and the existing owner-thread
handshake fixture. Restored the current native CMake manifest in the private build
to expose that fixture; its first attempted combined build rejected the previously
missing target. The rebuilt Windows fixture executed under isolated Proton and
passed owner submissions, foreign-thread rejection and transport failure handling.
Local strict C11 syntax and git diff checks also passed.

Staged a private cloned ledger with all32 financial snapshots matching the source,
retaining Trotter's pending minimum classification. Packaged Windows CPython ran
the actual sidecar hello with an explicit nonexistent ADC path: ai_disabled,
zero SDK attempts, unchanged Giants financial snapshot. No model/control/IAM
request, credentials distribution or salary-credit assignment. Evidence is private
runtime/root-transport-diagnostic/windows-preflight.json; this proves the Windows
service preflight, not a root game callback or actual signing integration.

Installed root EXE SHA256
efa3958a00b035ab5f70f905a5033639f1ed138bcb9b4147080180e5a0a31cc5
and launcher SHA256
5a0b046c2df7efa6e3b8b69b46c03f11f27307e822c61cda1abf91664c511afb.
Preserved prior files as NFL2K5.pre-root-transport.exe and
launch-2k5.pre-root-transport.sh, with their previously verified hashes unchanged.
The diagnostic launcher explicitly denies AI through the absent ADC path and uses
the clone; no actual guest write/modern contract hook is enabled. Requested normal
Steam launch and Trotter offer screen without submission; actual game execution
of this newly installed diagnostic remains pending.

Published3c97f06 Build38629769797 and AI38629769570 passed. Retrieved logs verify
678 tests on both Windows and Ubuntu. This updates the earlier published676
baseline; it does not validate the newly authored logging change's hosted CI.

## October14,2026 — Actual game/Windows-sidecar handshake round trip

User launched the same Gaming Mode entry, loaded AIGILDON and opened Trotter's
offer without submitting. The actual session log records transport owner320,
Sign Contract descriptor557B2C, Trotter slot1910 and matching biography guard,
Giants15/mode2 payroll77038/cap80500, and calendar index0/display2004. The real
pythonw.exe child command uses the cloned ledger, explicit vertex impersonation
and diagnostic budget scope. After the user backed out/reopened, the actual game
logged Control handshake reply consumed. No foreign-thread rejection was logged.
This establishes root-game transport execution and reply consumption; the reply's
authorization fields were not separately logged and no authenticated AI grant is
claimed. Explicit missing ADC still denies AI. Read-only budget query reports
zero model attempts.

Retrieved the private session log and cloned ledger readback. All32 financial
snapshots match the pre-game clone. Retained safe scoped result in
.local-runtime/root-transport-diagnostic/game-transport-result.json. No offer
submission, guest write, source credential distribution or remote control/IAM
change. Game remains running for the user; actual child cleanup after normal
game exit, authenticated game authorization, AI decisions, guest commit/recovery
and save/reload remain pending. Logging source committed/pushed as9537d80;
its published CI is not yet asserted successful.

## October14,2026 — Saved/live signing checkpoint reconciled

Added tools/reconcile_signing_context.py to bind a complete live biography, team
and raw calendar observation to the existing pinned snapshot and saved legacy
book. It checks exact original cap/payroll/adjustment inputs, all saved legacy
contract records including source, full annual ledger charge vector, current
ownership and explicit revision, then returns the persisted player context.
Changed identity, calendar, cap inputs, source schedules or revision reject.
Inspection neither assigns a salary floor nor invokes a model/financial write;
the result explicitly denies AI/write authority. Active franchise selection,
cash/rookie obligations, modern ledger mutations, concurrent write authorization
and automatic game/bridge submission require subsequent integration.

Actual captured Trotter fields from the root-game session reconcile against
original/saves/AIGILDON-signing/SAVEGAME.DAT and the diagnostic ledger: UUID
a564eb821c3742929f408fac07929cc5, Giants, revision0, persisted personality and
classification_pending. Retained private observation/result JSON under
.local-runtime/root-transport-diagnostic. This is a local reconciliation of actual
game observations, not a new native game request or a guest transaction.

Four focused tests pass, including same IDs/cap totals but different preserved
contract source rejection. Full offline682 tests pass in24.778s; diff check passes.
Prior9537d80 Build38633164511 and AI38633164597 now completed successfully;
72443cd Build38633607007 passed while AI38633606823 remains in progress.
No game installation, model request or control/IAM change in this milestone.

## October14,2026 — Signing checkpoint exposed through service boundary

Added signing_context to Bridge and explicit paired source configuration to the
sidecar. Service-owned save/bindings are validated once before startup; missing,
malformed or incomplete configuration cannot generate replacement identities.
Requests carry complete observations, revision and bounded timeout, never file
paths. Read-only reconciliation works despite disabled AI, checks connection
before/after inspection and bounds response framing. Successful hello advertises
the operation only when configured. It neither bypasses remote AI control nor
calls the provider.

Native response validation checks canonical UUID/hash, observed team table/slot,
requested revision, initialized nested player context and explicitly false AI
and write flags. Authored protocol cases reject authority escalation, mismatched
identity/team/slot/revision, uninitialized context and extra financial fields.
Portable protocol compilation/execution passes. Four new service tests include
an actual subprocess with pinned authored source and missing ADC; full offline
686 tests pass in29.143s. Diff check passes.

Actual captured Trotter observation also passes through a local sidecar process
against AIGILDON and the diagnostic ledger; persisted UUID/personality matched,
pending minimum classification retained and Giants financial snapshot unchanged.
Private request/reply evidence is service-signing-context.json under the existing
diagnostic directory. This is local service-process evidence, not a new Windows
root-game request or signing. No live game source/runtime was overwritten.
Automatic root-game submission remains the next integration step.

Prior72443cd Build38633607007 and AI38633606823 passed. a124246 Build38634283242
passed while AI38634283048 remains in progress. New source CI remains required.

## October14,2026 — Automatic game signing-context capture built and staged

Added an opt-in root-game read-only inspector using the already bounded live
bank/name/team/calendar readers. It operates independently of diagnostic trace
logging, sends fresh observations through signing_context after hello collection,
and never blocks a callback, moves transport ownership or touches guest memory.
Explicit paired source paths and nonnegative ledger revision are required; partial
source/revision configuration rejects startup. With the inspector disabled,
the prior per-screen hello behavior remains. Pending reads prevent duplicate
submissions; later FSM events collect validated replies with a16-reply log bound.
Receipt consumption does not authorize a model request or financial transaction.

Extended the portable actual-reader RAM harness to run this path with trace off,
verify captured fields and unchanged low/high guest memory, and reject an invalid
season. Extended Windows scheduling fixture covers partial source configuration,
invalid revision, pending hello/read, no redundant hello and malformed name
rejection. Full offline686 tests pass in23.832s; strict C11 syntax and diff checks
pass. Actual MSVC NFL2K5/handshake/protocol targets compile; Windows fixtures
execute successfully under isolated Proton. Private staged game SHA256
e18edc0db40e0b34df2c49a568daeef38d318dbe98c4b6a089337184ec9bd1c4.

Prepared isolated signing-context-stage with copied licensed embedded Python,
current authored service/tools, pinned private AIGILDON/bindings and cloned books.
The live game and existing service package were not replaced during staging.
Windows service preflight returns disabled hello followed by actual Trotter
context: UUID a564eb821c3742929f408fac07929cc5, initialized/pending classification,
zero model attempts, unchanged Giants financials, no AI/write authority. Evidence
is private signing-context-stage/windows-check-result.json. No credentials,
model/control/IAM request or financial classification was introduced.

Staged launcher and hash-guarded installer preserve both currently installed files
and refuse a running game. Process check found game78193 and owned sidecar78236,
so requested normal exit without submitting. User subsequently confirmed closed;
fresh cleanup check/installation are underway. Automatic root request/reply
execution remains pending normal user launch; the Windows component preflight
is not claimed as automatic game execution.

Fresh post-exit process check found neither game nor pythonw.exe child; this
verifies owned child cleanup after this normal root-game exit. Guarded installation
passed: root EXE hash e18edc0db40e0b34df2c49a568daeef38d318dbe98c4b6a089337184ec9bd1c4,
launcher hash 1f2771c2cdf51391b3e2a823922ebd3757e9c8e4d73e17a3646e43f44ff7acce.
Preserved prior game/launcher as .pre-signing-context files with their verified
efa3958a/5a0b046c hashes unchanged. Requested normal load/open/back/reopen/back
without submission to collect the new automatic context reply. No offer changed.

Published743deb6 Build38634852382 and AI38634852421 passed. Retrieved logs
verify686 tests on Windows/Ubuntu. Updated WORKLIST's latest source/test baseline
and lifecycle cleanup status; new capture source CI and actual game execution
remain separate pending evidence.

## October14,2026 — Actual automatic game player-context round trip verified

User backed out of reopened Trotter offer without submitting. Actual root log
line1138 contains game-sign-context-1, error=null, pinned UUID
a564eb821c3742929f408fac07929cc5, Giants/revision0/slot1910 and AIGILDON source
hashac16245c5fcd743f3cc9e6aa37d76de72424238782de353765c758d242c6bc7d.
The returned actor is initialized with persisted fictional personality and
relationships, classification_pending=true, AI/write authority=false. This
request was captured/serialized by the actual game and served by the packaged
Windows sidecar through the native validator, not injected by a local script.

Read-only remote budget query reports zero attempts. Retrieved private session
log and clone; all32 financial snapshots match the pre-game clone, and the full
returned player context exactly matches the existing persisted store context.
Private evidence is .local-runtime/automatic-context-proof/result.json. No offer
submission/guest contract write, salary-credit assignment, model/control/IAM
request or credentials distribution. Receipt is inspected on a later FSM event;
live same-screen polling/UI still requires integration.

Marked the specifically scoped root transport/lifecycle item complete: actual
startup, hello/context round trip and earlier normal-exit child cleanup all have
execution evidence. This does not complete AI negotiation, financial transaction,
modern calendar, game save/load or broader playable acceptance. Published
87450b3 Build38636188349 passed; AI38636188333 is still in progress.

## October14,2026 — Owner-thread input polling built and staged

Moved ready-reply collection into a reusable owner-only poll and invoked it from
the existing HLE XInputGetState callback through the actual bounded reader.
Hello can finish on the same screen; fresh context is captured when ready, once
per Sign Contract entry. Busy/foreign-thread callbacks cannot take or submit.
Leaving/changing the screen clears the active locator, rejecting stale observation
submission. Context replies still grant neither AI nor financial authority.
No network wait, model request or new guest patch/address was introduced.

Portable actual-reader harness now executes the polling wrapper with trace off,
validates captured fields, unchanged low/high RAM and invalid-season rejection.
Windows scheduling fixture validates same-screen hello/context collection,
foreign polling rejection, once-per-entry dispatch and closed-screen rejection.
Full offline686 tests passed in26.547s; updated portable fixture also passed;
strict C11 syntax/diff checks pass. Actual private MSVC game/fixture builds and
Windows fixture execution under isolated Proton pass. Staged root SHA256
a47435e9d0c5bf9a7fa652a853722484a84d9282a15f5f28c34be40934a7bd28.

Fresh process check found game79698 still running, so preserved its installed
executable/launcher and staged a hash-guarded installer with backup. Requested
normal exit without submitting. Actual installation and same-screen behavior
remain pending; fixture success is not reported as game execution. Existing
isolated service/database/auth denial remain unchanged. Earlier CI check timed
out in automatic approval review; one permitted read-only retry succeeded.
Published87450b3 Build38636188349 and AI38636188333 passed; 8167bde checks are
still in progress. Current polling source requires its subsequent hosted CI.

User confirmed closed. Fresh process check found no game or pythonw.exe child;
guarded installation passed with staged root SHA256 a47435e9...a7bd28, backup
e18edc0d...bd1c4 and unchanged launcher1f2771c2...7acce. Requested normal launch,
AIGILDON load and Trotter offer left open without submission. Actual same-screen
reply collection remains pending; source committed/pushed asfbde4cc.

## October14,2026 — Actual same-screen reply collection verified

User launched AIGILDON and left Trotter's offer open without submitting. Actual
root log shows Sign Contract push at line910, hello collected916 and successful
game-sign-context-1 reply920, with no intervening FSM push/pop. This verifies
the existing guest input callback executes the owner-thread poll and fresh context
capture while that screen remains open. Exactly one context reply appears;
it resolves the same UUID/Giants/revision0 and persisted fictional personality,
with classification still pending and AI/write authority=false.

Remote read-only budget query reports zero attempts. Retrieved private session
log and cloned ledger; all32 financial snapshots and full returned actor context
match the pre-game persisted store. Evidence is
.local-runtime/same-screen-context-proof/result.json. User remains in the offer
screen; no contract submitted, model/control/IAM request or salary credit assigned.
Polling build installation is recorded in a102d38; actual execution closes this
polling verification gap, not AI/financial/save integration or active-franchise
selection. Same-screen UI rendering and accepted/counteroffer transactions remain.

## October14,2026 — Saved performance added to signing-context format

Added optional performance_format=saved_history_v1 to signing_context. It uses
the existing pinned exporter, verifies the same player ID and retains raw history
filters, sparse observations, source indices, inferred half-sack units, candidate
years and explicit unknown metrics/coverage. Default requests retain their old
response shape. Native validation rejects foreign ID/source, ratings/unsupported
fields, invalid units/counts/calendar candidates, duplicate sources and missing/
present contradictions. Root env flag NFL2K5_FRANCHISE_SAVED_PERFORMANCE=1 is an
explicit opt-in; invalid flag/source configuration rejects startup.

Five focused bridge tests and full offline687 tests pass in23.045s. Portable
native protocol/strict C11 checks pass. Actual Trotter local service response has
six game entries/four sacks; that exact saved-performance response passes native
validation. Actual private MSVC game/host/protocol builds and Windows native
fixtures pass. Staged game SHA256
556016fa375d3e8b3f676cd6e3bbc3a879498c2d834709a28391ffec7fa1c537.

Prepared isolated saved-performance-stage source/licensed interpreter with no
overwrite of the running game's package. Windows actual service subprocess first
checked an explicit staged source bootstrap, then the staged interpreter's normal
-m franchise.sidecar launch. Both return the actual ten Trotter history entries,
zero attempts and unchanged Giants financial snapshot. Private Windows result is
saved-performance-stage/windows-result.json; local result is
.local-runtime/root-transport-diagnostic/service-signing-performance.json.
This is saved history, not live stats or new root-game execution. No ratings,
invented pressures/QB hits, model/control/IAM calls or salary credits introduced.

Prepared hash-guarded backup/install script and requested normal exit before
replacing game/launcher. Fresh process check found game80919 running. Actual
installation and game receipt of this new format remain pending user exit/launch;
the currently installed same-screen personality path remains intact.

## October14,2026 — Live offer format and financial precheck prepared

Added a raw guest_offer option to signing_context, after the existing pinned
identity/team/calendar/legacy-book checkpoint. Exact GuestContractTerms decoding
rejects incompatible new-deal bonus horizons/rounding before financial preview.
Successful decoding uses FranchiseStore.preview_offer, retaining global ownership,
draft-right, minimum/revision and cap enforcement. Outcomes distinguish format
rejection, accounting rejection and advisory eligibility; no reservation, model
request, signing, salary classification or guest write occurs. Legacy schedules
remain unchanged. Root flag NFL2K5_FRANCHISE_GUEST_OFFER=1 explicitly opts into
bounded context amount/flag capture; invalid source/flag config rejects startup.

Four new helper tests cover exact Gildon charges, incompatible horizons/rounding,
unknown minimum, overcap, stale revision, owned player and malformed raw words.
Bridge test keeps actor access while rejecting unsupported/missing-minimum offers.
Full offline692 tests pass in19.237s; portable native protocol and strict actual
reader/C11 checks pass. The captured actual Trotter raw1949/4D060004 offer returns
format_rejected/five-year allocation reason through a local actual sidecar, with
personality/history still readable. Recompiled an older ad hoc validator before
using it on the extended reply; that exact new reply then passes native validation.

Actual private MSVC game/host/protocol builds and Windows fixture execution pass.
New staged game hash e88e74d864f8f587263f9c0922d20f4b469cff82c200420fc452e0616298aa51.
No installed game/service was replaced: fresh check still found game80919 and
child80962. Preserved the earlier validated performance EXE separately at
saved-performance-stage/NFL2K5.validated.exe (556016fa...1c537), and rebound its
pending installer to that frozen file so later builds cannot change its artifact.
User exit request for that performance update remains pending, without repeating
it. Actual new offer-format request/reply, UI enforcement, AI decisions, commit
recovery and save/load remain unverified. No cloud/control/IAM change or asset
publication occurred.

## October14,2026 — Native exact salary schedule gap closed

Inspection found native offer_context validated ID/term/nominal bonus but could
accept altered salary vectors with those same raw words. Added bounded native
schedule reconstruction matching the observed original float32 stores, integer
division and final truncation. No arbitrary salary, altered annual charge or
false format-rejection receipt now passes. Incompatible modern bonus allocation
still rejects; existing preserved legacy schedules are unaffected.

Added an asset-free differential runner to the native protocol CLI/CI. Python
generates expected exact offers/rejections for all8 shapes, terms1..15, four bonus
codes, six word cases and malformed boundaries:2886 cases. Portable native and
actual MSVC/native+Windows CPython under isolated Proton both match all cases.
Windows result is private saved-performance-stage/native-corpus-windows-result.json.
Protocol cases also reject changed salaries, charges and a false rejection of
known-compatible Gildon terms. Full offline692 tests pass in20.013s; diff checks
and private Windows game/native compilation pass. New private build hash
1951119d7f0723e6eebf511c5bd068964432378f0dc154aa497569bbc33cf80b.

No game/runtime package installed, model/control/IAM request or financial state
changed. Frozen validated performance artifact556016fa...1c537 stays preserved
for its pending normal-exit deployment. Native decoding equivalence is not
actual game enforcement, AI negotiation or save/commit verification.

## October14,2026 — Obsolete signing-context receipt safeguard

Rechecked the actual running game log: Trotter's persisted personality receipt
appears at line920, after hello at916, without an intervening offer-screen
transition. This confirms the existing same-screen proof; it is not a new AI
negotiation or saved-performance deployment.

The host now samples before collecting replies and compares player, offer,
calendar and team observations plus the screen entry epoch. Changed, unreadable
or closed-screen receipts are discarded. Valid changed terms refresh after
300ms stability; unchanged samples do not send duplicate requests. Failed reads
invalidate freshness and allow retry when a valid observation returns. Inspection
remains read-only and never grants AI/signing authority.

Full offline692 tests pass in22.036s, strict C11 syntax and diff checks pass.
Private MSVC game/native compilation and actual Windows scheduling/protocol
fixtures pass. Scheduling execution logged three discarded receipts for edited,
unreadable and closed-screen observations, while unchanged/current receipts
remained accepted. New private executable SHA256
2dc415198ba8375c3985e7ba99a5aa9874d911dfe9b05b29a30fe98b560820bc.
Updated the worklist's published baseline to successful dd13542 CI runs
38643561542/38643561629. No running game/package was replaced, financial state
written, cloud setting changed or model request submitted. Actual execution of
this new safeguard and the frozen saved-performance install remain pending.

## October14,2026 — Exact game-format negotiation proposals

Added optional original_fxg_v1 contract format to the existing proposal-only
operation. Submitted terms must encode exactly before inference. Accepted offers
retain canonical mapped amount/flag words; counters that cannot encode preserve
the original demand and get ineligible status rather than silently changing
salary/bonus/guarantees. Encodable demands still pass the authoritative cap and
minimum preview. Format and encodings persist in dialogue, reject tampering on
load, and cannot change under a reused request ID. No signing is recorded.

Native validation independently reconstructs offers/counters and annual charges,
rejecting substituted mapped words, unrelated flag bits, altered charges and
unencoded counters advertised as eligible. Model context describes the format
restriction without adding ratings or fabricated player evidence.

Five focused tests cover accepted/restarted dialogue, mode/format replay,
unrepresentable input before inference, unchanged unusable demands, representable
and overcap counters, and corrupted encoding recovery. Full offline697 tests
pass in22.038s. Portable native fixtures and2886 decoder differential cases pass;
an actual asset-free Python Bridge proposal receipt passes the native validator.
Private MSVC game and native compilation plus actual Windows protocol fixture
execution pass. Private game hash
59cdf999829f79d411ce0e524dbdc7a817279e930831d1942a552dd05a8911d1.

The previous safeguard64ef086 now has successful CI38645309410/38645309320.
Game80919 remains running the earlier installed personality diagnostic; no live
package or launcher was replaced. No cloud/model/control/IAM request, salary
classification, guest write or financial transaction occurred. Actual root
proposal submission, UI presentation, precommit/guest recovery and save/load
remain required; this closes proposal representation only.

## October14,2026 — Captured signing checkpoint to proposal path

Added a captured-screen request variant to the existing negotiate_proposal
operation. It accepts the live observation/raw offer/revision and optional
promises, requires remote access, reconciles the pinned checkpoint, derives
persisted identity/team/personality/relationships and saved sparse performance,
and requires an eligible exact-format preview before inference. Client actor,
performance, team and decoded-offer overrides reject. The ordinary proposal-only
engine retains dialogue but never signs, with the remaining shared deadline.

Successful replies attach the read-only checkpoint. Native validation checks
checkpoint/offer/performance source and exact proposal encoding, rejecting changed
actor/evidence, false write permission and incompatible eligibility. Service replay
also refuses to relabel previously client-supplied evidence as captured evidence.
Repeated captured requests re-read the checkpoint and reuse recorded dialogue
without inference; checkpoint dialogue history can therefore change on replay.
An oversized combined reply reports context_too_large without a contract commit;
the dialogue may already have been recorded.

Five focused tests cover enabled authored acceptance/restart with unchanged
finances, missing classification, source/actor/revision/format overrides, shutdown
before dispatch and replay evidence substitution. Full offline702 tests pass
in19.564s. Portable native checks and an actual authored Python Bridge receipt
pass native validation. A real local sidecar subprocess accepts the read checkpoint
and returns ai_disabled for captured negotiation with missing ADC, retaining
revision0. Private MSVC game/native compilation and actual Windows protocol
execution pass; game hash
389e78140f0719f15ee8d31b0886cca319e80297c573ee1ccc176199010d2fd3.

Prior812f54e CI38646195809/38646195538 is successful. Fresh check still found
game80919; no running game or service package was replaced. No real player's
minimum/credit policy, cloud control/IAM, financial state or guest memory changed;
no paid inference was attempted. Actual root proposal submission/presentation,
active save selection, persistent runtime auth, classification policy, guest
commit/recovery and save/load remain unverified or blocked on their inputs.

## October14,2026 — Native read-only signing panel candidate

Connected the current signing context to the existing native Direct2D HUD
compositor through bounded owned display buffers. Renderer threads only copy an
SRW-locked snapshot; they do not parse JSON, use transport or read guest memory.
Owner publication requires the current screen epoch/observation. Changed terms,
closed screens, failed sampling, obsolete replies, transport failures and
shutdown invalidate the display. Successful sampling does not transiently hide
it; actual failed reads invalidate before collecting a pending reply.

The card shows player name, the two highest saved fictional contract priorities,
supported offer-preview status and history availability with season uncertainty.
It exposes no numerical personality weights, hidden ratings or invented current
performance. The footer explicitly says signing still uses the original game.
This candidate is informational; it does not add a negotiation action or write
guest terms, and source-format rejection is not game enforcement.

Portable protocol/display checks, strict C11 and full offline702 tests pass
in20.784s. Actual private MSVC game/native builds and Windows scheduler/owned-copy
fixture execution pass, including foreign-reader access, hidden failed samples,
restored matching observations and cleared changed offers. Final game hash
2ca0064219f10be5f01c5624f789f2f54db9610017064451dbad56423ba98318.

Built a private fixture by extracting the actual Direct2D renderer, using the
captured Trotter service reply. Initial headless execution returned3; reading only
the game's DISPLAY/XDG_RUNTIME_DIR values and running in that graphics session
produced actual Windows/Proton panels for1280x800 and1600x900. Private PNGs are in
.local-runtime/signing-card-proof. A bounded Impeccable component review returned
ship with no material findings; documentation records its limited scope. The
existing game screenshot is black and cannot prove placement or readability over
the actual offer screen. No screenshot or component verdict proves game delivery.

Priorcb41cbc CI38647049179/38647049334 is successful. Fresh game80919 remains
active, so no game/package installation occurred. Frozen performance artifact
556016fa...1c537 remains preserved. No paid inference, cloud/control/IAM update,
classification policy, ledger transaction or guest write occurred. Actual-game
panel placement/controller checks, proposal action, legal commit/recovery and
save/load remain unfinished.


## October 14, 2026 — SOFTDRINK preferred base

User selected SOFTDRINK if compatible, superseding PS2-first migration. Inspected
current v0.6 public release and local main/mod-pack interpreter startup; identified
newer shared-executable support versus historical separate-build notes. Worklist
now prioritizes pinned pack execution and controlled franchise save pairs before
AI writes. No v0.6 execution, paid inference, game deployment or save mutation
performed. Compatibility and playable AI remain unverified.


## October 14, 2026 — standalone connection addon extraction

Extracted original C++17 Windows owned-process pipe transport, launch quoting and
strict JSON envelope validator to addons/engine-sidecar. Core has no franchise
imports, AI provider, cloud control, game assets or guest-memory access. Franchise
PipeClient now consumes it and retains result/contract validation; launch arguments
retain explicit provider/budget policy. Standalone Python echo and independent
Windows/Linux CI are included. Portable addon and franchise native checks pass,
including 2,886 native/Python guest contract cases. Windows process execution and
regression CI remain pending. No game deployment or paid inference performed.
Standalone source starts private; original-code licensing has not been selected.

Standalone addon export bdaa2df is published privately at
https://github.com/cosmokay1/engine-sidecar. Independent CI 38655732233 passed on
Windows and Ubuntu, including actual Windows process/echo round trip. Consumer
source ba8a4f5 Build check 38655649764 passed; Franchise AI 38655649598 Ubuntu
passed and Windows was still running at this evidence update. Local 702 tests
passed. No Windows consumer result is inferred from the standalone echo check.


## October 14, 2026 — loadable application addon

Extraction consumer ba8a4f5 CI38655649598 now passed Windows/Ubuntu; standalone
bdaa2df CI38655732233 also passed. User clarified true addon delivery rather than
static module separation. The game-specific observer/diagnostics and host service
now build into franchise-addon.dll, loaded via versioned C API from a small shim.
Main retains checked read-only memory capabilities and existing lifecycle calls;
existing input/FSM/signing/render paths forward without new generated-code hooks.
No guest write API or gameplay hot reload is added. Missing default addon permits
vanilla execution; explicit bad paths, ABI and startup failures reject. Display
calls synchronize with unload. Asset-free Windows DLL lifecycle tests are authored;
portable observation checks pass. Full CI/game execution remain pending.

Local validation: 702 Python tests passed in20.836s, including the authored RAM
observer exercising the actual host read capability and DLL observation code.
Portable strict C syntax checks passed for addon adapter and disabled loader.
Native protocol checks passed. Windows DLL loading/ABI rejection/reload and game
execution are not inferred from these local results.

Loadable-addon implementation6f75219 is pushed. Build38656804259 and Franchise
AI38656804337 passed. Both platforms ran702 Python tests (Ubuntu17.803s,
Windows97.906s). Windows compiled the actual franchise-addon.dll and passed all
five native tests, including loadable_game_addon (ABI mismatch, absolute-path
loading, forwarding, disabled service, unload/reload), stalled-peer ownership,
handshake and lifecycle. Native/Python guest-term comparison and the durable
pipe/restart fixtures also passed. This is component execution, not game execution:
no new game build was deployed, no paid inference or guest write occurred, and
SOFTDRINK compatibility/legal signing/save-reload remain unverified.


## October 14, 2026 — existing mod manager gains addon selection

User clarified manager extension then SOFTDRINK application. Added separate
Franchise Sidecar row through existing manager callbacks. Persistent opt-in state
is independent of content packs, defaults off and applies on next launch. UI
status distinguishes missing module and pending restart; toggling never restarts
a running franchise. Existing native16-row limit reserves one addon row/15 packs.
DLL ABI/provider/control policy remains enforced, including explicit diagnostic
paths. Windows fixture now exercises manager selection alongside the real DLL
and confirms the active content-pack file remains unchanged. Verification pending;
no game deployment, cloud inference or save/contract writes occurred.

Local702 regressions passed in23.072s. The manager/selection/DLL Windows fixture
adds default-off and malformed-state denial, installed/missing status, delayed
selection, unchanged content-pack choice and real module lifecycle. Source UI
callbacks preserve the incumbent native menu; visual/controller verification is
still pending.

Manager implementationd3ca4aa CI38658080834 passed Windows/Ubuntu;
Build38658080837 also passed. Windows compiled actual manager/loader/DLL code
and ran loadable_game_addon, including default-off and malformed state,
selection persistence and pending-restart labels, unchanged content-pack choice,
missing DLL and ABI failure handling, and module unload/reload. Both platforms
passed702 regressions and native checks; durable transport/restart checks passed.
No screenshots/controller interaction, SOFTDRINK v0.6 runtime, repack conversion
or private-game deployment were performed. Those acceptance gates remain open.


## October 14, 2026 — private addon/manager build and SOFTDRINK match-start failure

Built the full Windows game and loadable franchise DLL on the awake Deck using
MSVC14.44/SDK10.0.26100 under the existing private build container. A fresh cloned
compiler prefix resolved MSVC D8037 temporary-file failure. The actual manager/DLL
fixture completed under Proton (exit0 and final fixture cleanup), including opt-in
selection, independent content pack, ABI failure, load/unload/reload and disabled
service checks. Initial headless fixture startup stalled; rerun with Gaming Mode
DISPLAY succeeded. No AI provider, credentials or paid inference were enabled.

Pinned official SOFTDRINK v0.6 patch SHA256
8f38472ec12d1c4d9745683d10e5df15d426b8b339ab9ff4a886bcfaf6caceb0.
The local installer checked all19 retail input file hashes and14 changed output
hashes. Reconstructed XBE SHA256
f67e6fc1cb76c9ea1f1ad504e4a6491ff126483d66a9da8ddb92950bbaf740ba.
This proves the file overlay, not a reconstructed ISO layout. No retail downloads
or asset publication. Existing upstream/SOFTDRINK attribution remains required.

Candidate manager-addon-5605345 has its own runtime, saves and cloned Proton
prefix. Existing Steam entry3759717425 and validated controller profile retained;
only its launcher was reversibly redirected. Original EXE and saves untouched;
launcher backup is launch-2k5.sh.pre-manager-addon-5605345. Initial candidate EXE
SHA2561d83fb8d29d5f4717c7c0b92bd5783bd1466be203b99c8b2eb659a7d832b3366;
DLL d4d1020eee8732aa3b60ba08a8a93237922619548344ab8c9540ff9f81750190.
These identify the failed first run, not the subsequent interpreter-fix build.

Actual Gaming Mode run reached team selection, captured through Gamescope.
User reports starting a match immediately before closure. Active overlay is
confirmed by session.log (14/19 disc files changed,1287/31081 converted functions
interpreted,128MiB guest memory). It failed with C0000005 at host1401903D2 after
invalid interpreted jumps. Addon was disabled throughout; AI signing was not run.
Preserved private failure-20261014-174625/session.log and steam-launch.log before
relaunch. No clean gameplay, fresh franchise, signing or save/reload acceptance.

First invalid jump follows guest4721A ->470DB, a shared cleanup entry which
removes16 bytes of locals before returning. Interpreter native-jump dispatch
instead cached the top local word as the return address (trace43E80000). Fix keeps
ordinary guest JMP targets interpreted so actual RET discovers the address after
cleanup; native CALL and explicit manual/kernel bridges remain native. This can
increase interpretation work on tail-jump paths; game performance remains to test.
Added asset-free native/interpreter fixture: nested call with16 local bytes and
shared epilogue, plus native CALL/manual/kernel bridge checks. The unchanged
interpreter fails it under Proton (exit1); fixed interpreter passes (exit0).
Windows compilation/link succeeded. Added Windows CI coverage. This reproduces a
concrete defect matching the trace; it does not yet prove the real crash resolved.

Installed the fixed private EXE after confirming no game process:
SHA2561742d8c261f661a46434d0345a05e4b59270676ab27e18fc4585672d441d6bcb.
Interpreter source SHA256ddfae28de4f256578b25ff4affbb1a77a8de52bb06247db516911182b4cc5d06.
Failed EXE retained privately as NFL2K5.pre-interpreter-fix.exe. Same Steam
launcher, addon disabled and AI unconfigured. User asked to repeat the same
matchup and opening snap; real-game retry remains pending.

User reports “Working” after the fixed-build matchup retry. Record this as
user-confirmed recovery of the match-start failure, not full gameplay/franchise
acceptance. Independent log check and native manager controller navigation are
still pending; asked user to inspect the Franchise Sidecar Off row after playing.

Independent retry check: game process101848 remains running; current session log
83013 bytes has zero [CRASH] markers and zero unknown-opcode reports. A private
Gamescope screenshot (retry-screen.png) visibly shows players on the field at
MetLife with the in-game pause menu, independently confirming entry into a match.
This verifies the specific match-start recovery, not a full quarter, game, franchise
or save/load round trip. Windows CI38662620516 is still running; Ubuntu passed.


## October 14, 2026 — manager disabled default observed; interpreter CI passed

User confirms the actual Deck Mod Packs screen shows Franchise Sidecar Off.
This verifies row visibility and disabled default only; asked user to toggle On,
observe On - restart, exit normally, relaunch the existing Steam entry and check
On without the restart marker. No provider/credentials/control changes are made.

Source4e3d3d5 CI38662620516 completed successfully on Windows2022 and Ubuntu.
The new Windows interpreted_shared_epilogue regression passed, alongside existing
native protocol/manager/DLL and franchise tests. This complements the actual Deck
on-field recovery evidence; save/reload and enabled-addon game execution remain
separate unchecked gates.


## October 14, 2026 — actual enabled-addon restart and guarded installer

User confirms Franchise Sidecar On after normal restart. Independent process102235
maps the installed runtime/addons/franchise/franchise-addon.dll. Selection is
enabled=1, active pack remains SOFTDRINK_2K28_v0.6-v0.6, current log contains zero
crash/unknown-opcode markers. No provider, control renewal or cloud calls. This
checks real manager selection/restart/module loading, not AI or save integration.

Added tools/install_sidecar_addon.py: trusted package manifest lists exact supported
host SHA256s and DLL checksum. It rejects unlisted hosts, corrupt/non-AMD64 DLL
headers and symlinked installation paths. Only the franchise DLL is replaced,
atomically; previous content-hashed DLL backup retained, identical reinstall is a
no-op. Selection, content pack, launcher, host, saves and AI configuration untouched.
It requires an already addon-capable host; no universal repack conversion or general
addon registry is claimed. Documentation includes package trust/licensing limits.

Five new synthetic tests cover initial install/default-off, upgrade/backup, exact
reinstall, host/payload rejection, failed replacement preserving installed state
and symlinked-directory refusal. All707 local regressions passed in20.586s. Initial
sandbox run blocked four localhost HTTP/TLS fixture listeners; unsandboxed retry
passed. No external services or paid inference were used by those fixtures.

On Deck, a separate installer-check directory with copies of the actual private
EXE/DLL passed initial install and no-op reinstall, retaining synthetic save and
selection/pack markers. Supported host1742d8c261f661a46434d0345a05e4b59270676ab27e18fc4585672d441d6bcb;
previous hosta47435e9d0c5bf9a7fa652a853722484a84d9282a15f5f28c34be40934a7bd28
was refused without host mutation. DLLd4d1020eee8732aa3b60ba08a8a93237922619548344ab8c9540ff9f81750190.
Private installer-check-receipt.json records this. Active game/runtime was never
modified by this check. Synthetic upgrade tests do not prove cross-version live
upgrade compatibility. Windows/Linux CI for the new installer remains pending.


## October 14, 2026 — public addon ABI separated from franchise payloads

Added native/game_addon/api.h ABI2: lifecycle, poll, named synchronous events
and snapshot reads plus the existing checked memory-read capability. No franchise,
AI, money or renderer types appear in the public interface. Existing include path
forwards to it. Private franchise_addon.h owns FSM/signing payloads and display
type; game_addon_adapter.c translates existing native call sites. Loader module
locking covers all callbacks versus unload; callbacks cannot reenter lifecycle.
No write capability, registry, queue or hot reload added.

A small counter DLL includes only the generic header and standard C headers.
Extended the real Windows fixture to load it through the same loader, exercise
event/poll/snapshot, reject unknown names, wrong capacities and null buffers, then
unload. Franchise dispatch and lifecycle remain covered. ABI1-only module refusal
and rejection of requests for ABI1 by ABI2 modules are explicit. No silent table
reinterpretation. The single manager slot/selection and existing guest hook/render
call sites remain application-specific; this is not a completed upstream PR.

All707 local regressions passed in20.493s. Full private Windows game, DLL and
fixtures compiled with MSVC. New fixture passed under Proton, exit0, in a separate
abi2-fixture-prefix; initial invocation failed because the prefix parent did not
exist, corrected by creating it before Proton startup. ABI2 fixture receipt is
private. Working Deck executable, DLL, selection, saves and running session were
not replaced. ABI2 requires a newly pinned matching host/DLL pair; the existing
ABI1 host hash must never be used to authorize installing ABI2. Cloud unchanged.


## October 14, 2026 — MyNFL1 Giants cap audit corrects legacy-cap assumption

User requested validation of approximately $89M room for Giants/current roster,
expected2026. Retrieved MyNFL1 read-only,720044 bytes, SHA256
4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3.
The strict retail reader correctly refused its first settings word1 and enlarged
player bank. Private structural audit validated declared2619 records against
base/stride/next-table boundary and all team pointers/names, then reconstructed
all32 payroll totals exactly. Giants53 charges sum52,996 game thousands; zero
first-year accumulator with flag1. Original scheduler index0, scheduled-game year26.
No save bytes were changed. Earlier assumption that reported89M was an outdated
league ceiling was wrong; user was reporting available room.

Pinned official authoring source e19384123c23a3601949dda67c9a3ab754d65fd6 defines
REAL_CAP_DOLLARS301200000, DOLLAR_SCALE4 and GAME_CAP75300. Safely parsed constant
replacement bytes (no external source module execution); all six economy windows
match the installed XBE exactly, including31E580's multiply-by-four formatter.
13EF17 initialization matches75300. Therefore displayed ceiling301.2M, roster
charge211.984M, room89.216M. Official NFL 2026 ceiling independently confirmed.

OTC current-year comparison shows the roster charges are approximations and
real-world non-roster liabilities are material. Do not substitute its9.86M room
or blindly add all IR charges: roster dates/memberships differ and some injured
players are already charged in the game. Full per-obligation conversion remains
unverified. Public audit docs/MYNFL1_CAP_AUDIT.md records sources, sample differences,
limitations and next steps. Proprietary payload, screenshots, detailed53-player
report and patch-byte verification receipt remain ignored/private.


MyNFL1 intake verified again after analysis: source hash unchanged, TYPE FXG,
runtime zero-key HMAC-SHA1 valid. Matched all53 Giants identities against the
current public2026 reference,45 within$20k of their current charge. Some larger
differences involve changed roster/status/date; McCarthy5.956M vs0.895833M,
Golston6.920M vs5.201103M and practice-squad Tupou1M vs0.275250M. Do not label
these all encoding bugs or silently change the frozen source.

Private same-player-comparison.json and reference-waterfall.json reconcile:
same53 current-reference charges204251252 +27 additional current active/IR/PS
identities42392016 +dead money43691218 =total liabilities290334486. Published
room9860848 implies adjusted cap300195334, or -1004666 from base301200000.
This adjustment is derived, not a sourced carryover classification. Some IR
players are already in the game roster, so blindly adding full IR would double
count them. The report distinguishes exact saved arithmetic from real-world
liability coverage and preserves raw payload/source records privately. No game
financial writes or model calls occurred. Next code work is schema-checked mod
save parsing and dated obligation mapping, preserving the already-correct scale.


ABI2 source2b35f3e validation completed: Build38665445078 and Franchise
AI38665445103 passed. Windows/Ubuntu707 Python regressions plus native fixtures
passed, including the generic counter addon through the shared loader, franchise
message/snapshot checks, legacy ABI refusal and interpreter shared epilogue.
Installer be9239a also passed Build38663889260 and Franchise38663889318.
Installed game remains the working ABI1 pair; no ABI2 runtime replacement occurred.


## MyNFL1 strict reader compatibility

Replaced the false first-settings-word format check and fixed2317-slot roster
limit with observed serialized ROST headers, fixed section size, declared player
count and exact base/adjoining-table boundaries. Bounds, alignment, duplicate
membership and UTF-16 guards remain. Calendar accepts variable saved settings
while retaining scheduler section/mode checks and its explicit retail-year scope.
No automatic2026 rebasing, money multiplication or ledger writes were added.

Read-only MyNFL1 SHA4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3
now parses2619 declared records,2070 memberships,377 free agents (maxslot2463),
Giants53. Public reconcile_payroll independently matches all32 stored totals;
Giants52996000 internal dollars. Input bytes remained unchanged. Retail calendar
index0 still yields2004, so existing identity guards correctly continue blocking
unverified modern import. Next integration work owns the explicit pack calendar,
4:1 money semantics and dated inherited/non-roster obligations reconciliation.

Validation:710 Python regressions passed in24.109s including three new tests
for expanded bank/settings compatibility and corrupt bank/header rejection.
No running game, cloud control, paid inference or save was modified.


## Preserved fitted liabilities at verified pack money scale

LegacyContract now stores optional game_dollar_scale4, retaining the raw amount,
bonus, shape and remaining/original term fields. Charge reconstruction applies
the scale after original guest truncation. It never treats encoded fitted cap
liability as headline cash, guarantees or modern bonus terms. Supported scales
are original1 and verified4 only; booleans/other scales reject. Retail wire
records omit the new default, preserving existing checkpoint hashes and replay.

A durable synthetic ledger test reopens the scaled inherited contract, rejects
a new deal exceeding remaining room by one dollar, accepts the exact boundary,
and continues rejecting unknown inherited cash initialization. Full712-test
suite passed22.713s. Read-only use of the typed scaled schedules on private
MyNFL1 reproduced all32 roster totals across1693 active contracts; Giants53
contracts total211984000 against301200000 base cap. No persistent slot IDs,
actual imported database, guest writes or runtime deployment were created.

Explicit pack calendar/identity bindings and dated non-roster obligation mapping
remain required before modern franchise import or signing authorization. This
is persisted schedule support, not completion of pack negotiation integration.


## Hash-pinned SOFTDRINK opening identity and scaled context

Snapshot creation accepts optional --game-xbe only with --create. Exact verified
v0.6 XBE SHAf67e6fc1cb76c9ea1f1ad504e4a6491ff126483d66a9da8ddb92950bbaf740ba
selects an explicit persisted opening profile. This requires index0, internal
cap75300000, reconciled team payrolls and scheduled-game year2026. Logical year
2026 is pack policy; native retail scheduler coordinates remain unchanged.
Unknown executable/profile, changed season/cap/payroll and biography drift reject.
No future-year migration, raw save edits or active-pack verification is implied.

Legacy export now carries the validated scale into typed preserved contracts and
compares scaled payrolls. Existing read-only signing checkpoint still compares
raw live observations to raw save fields, then checks scaled cap and liabilities
against durable ledger state. Synthetic restart/context regression confirms the
player is initialized with AI/write authorization false, rejecting a mistakenly
scaled native observation. Default retail registry shape/behavior remains intact.

Actual MyNFL1 read-only intake with actual pinned XBE created a private no-overwrite
registry at .local-runtime/softdrink-v0.6/mynfl1/bindings-softdrink-opening.json.
All2070 IDs/profiles resolve identically after JSON reload;1693 active contracts
export across32 teams; Giants53 charges211984000. Save bytes remain unchanged.
No actual franchise DB/game/cloud state was changed. Full717 Python regressions
passed22.818s. Source fixtures are authored and patch only the expected test hash;
no game/executable bytes are committed.

Remaining financial import work includes dated non-roster obligations, exact
contract source semantics, cash/guarantees and minimum/rookie classification.
Actual runtime selection/negotiation/legal commit/save-load remain unverified.


## Dated source liabilities versus fitted curves

Read the pinned public authoring audit fc/data/contract_audit.json at
e19384123c23a3601949dda67c9a3ab754d65fd6; SHA256
dc34704beaf7219119f377584a753ae03b74973d09625deee061e7780e98e466. It pins
September24,2026 source data. Full source stays ignored/private. It is roster
contract evidence, not a complete opening retained/reserve obligations inventory.

New offline tools.reconcile_pack_contract_source verifies the exact source hash,
profile, unique source/snapshot names, all five raw fitted fields, source club
allocation and observed-vs-modeled provenance. Verifies represented annual
charges against independent decoding, then proposes exact ChargeRecord opening
adjustments while retaining raw legacy deals and explicit unknown cash. No
estimated, ambiguous, changed-term or cross-club schedule is silently converted.
Original Washington game keyRedskins maps to sourceCommanders only; compound
source teams require allocation review.

Actual MyNFL1:1343 matched,350 unresolved (66 ownership,70 changed terms,206
modeled schedules,8 absent/ambiguous identities). Giants41 matched/12 unresolved.
Their corrections are -233097,+57104160,+18897840,+909250 for2026..2029. Burns
2027 alone requires11979333 above the fitted charge. This establishes that
correct opening cap scale does not establish future source liability accuracy.
Private dated-contract-source-reconciliation.json records per-player evidence.

Four authored tests cover exact signed corrections/book round-trip, corrected
cap enforcement at one-dollar boundary, missing/duplicate/changed/estimated/
transferred records, duplicate snapshot names, source mismatch and bad schedule
vectors. Full721 tests passed23.014s. No game, DB, save, cloud, AI request or
financial balance changed. Complete dated obligations and runtime enforcement
remain required; the report cannot certify complete opening books.


## Per-season source club allocation

Verified the nflreadr primary contracts dictionary: contract-level team may list
multiple clubs separated by slash; season_history.team and cap_number identify
the specific year/club liability. Source:
https://nflreadr.nflverse.com/articles/dictionary_contracts.html . Replaced the
overly conservative compound-header rejection with exact per-season validation
for every source year: exactly one annual row, current club (including verified
Washington label mapping) and exact Decimal million-to-dollar cap equality.
Still require identical fitted fields, unique identities and observed schedules.
No splitting totals, guessing former-team debt or transferring signing bonuses.

Actual MyNFL1 now matches1406 source schedules;287 remain unresolved:1 ownership
allocation (McCarthy),70 changed fitted terms,208 modeled schedules and8 absent/
ambiguous identities. This resolves63 additional records using dated annual
evidence. All previously1343 matched schedules pass the stronger annual check.
Giants now42 matched/11 unresolved; first-year subset correction -228097, later
years unchanged at +57104160,+18897840,+909250. The private report was refreshed;
no game/save/DB writes occurred.

Tests cover compound historical header with proven annual club, wrong annual
club, missing/duplicate year, dollar disagreement and unknown cap values.
Full722 Python regressions passed22.535s. Read-only SSH confirms existing game
PID102235 remains running through Proton; no installation or restart attempted.
Future raw contract edits, estimated rookies and full non-roster obligations
remain separate reconciliation requirements before live financial integration.


## Pack-scale captured new offers and counters

Added explicit softdrink_fxg_v1 proposal format alongside unchanged retail
original_fxg_v1. Exact decoding multiplies guest-rounded salary/nominal bonus
by4; reverse encoding respects4000 display-dollar units without altering raw
amount/flags or repairing bonus loss. Captured preview selects format from the
validated pinned binding, never a caller-supplied arbitrary multiplier.
Negotiation format constraints tell the provider the correct salary unit;
counters, persisted story events and replay retain/revalidate exact encoding.
Base guarantees, unsupported bonus terms and unknown formats still reject.

Updated native response validation for scaled legacy records, new-offer preview,
proposal/counter encoding and captured nested checkpoint normalization. Native
fixtures exercise both formats, eligible counter handling, false scale labels,
unknown legacy scales and captured proposal substitution. The native/Python
codec corpus now covers both scales over5767 accepted/rejected cases.

Validation:726 Python regressions passed43.019s. Host clang C++ protocol fixture
passed; native/Python5767-case codec parity passed. Used pinned nlohmann/json
v3.12.0 header SHAaaf127c04cb31c406e5b04a63f1ae89369fccde6d8fa7cdda1ed4f32dfc5de63.
New scaled preview correctly rejects a19.064M charge against10M cap; durable
scaled counter replay does not invoke the provider again or sign a contract,
and relabeling the persisted format as retail rejects.

No Windows/game execution, deployment, guest commit, paid inference or remote
control renewal occurred. Current installed ABI1 pair remains unchanged. Complete
opening obligations, supported rules/classification and actual save/reload still
gate live financial use.


## Core reprioritization: held native offers and response presentation

User deferred further statistics investigation. Added the opt-in native
NFL2K5_FRANCHISE_NEGOTIATION mode: the private franchise addon holds the shared
signing routine before retail judgment and before bypass-path contract writes,
using the original failure epilogue. The public generic addon API is unchanged;
a thin private event adapter forwards submission intent. Policy remains in DLL.

A matching fresh owner-thread observation queues one captured negotiate_proposal
request. It waits for pending context without blocking; repeat submits for the
same terms do not queue another request. Changed terms clear per-screen state;
session-qualified IDs avoid process-restart counter collisions. Foreign callbacks
remain held without accessing the transport. This is not a financial commit grant.
Response projection presents accept/reject/counter, counter term/total and a
bounded reason; acceptance explicitly remains held. It cannot silently sign.

Static comparison showed the pack redirects the shared323D80 routine's247AF0
roster-limit call to295320 (three changed call-displacement bytes), so generated
hooks alone are skipped. Registered the same two deferrals through the existing
interpreter hook API for the pinned v0.6 XBE only, and only when the experimental
mode is explicitly enabled. Default-off execution adds no interpreter-hook span.
No new generic interception framework or guest-write capability was introduced.

Validation:726 Python regressions passed21.585s. Host clang protocol checks pass.
Final private MSVC game/DLL build passed with staged EXE
c3c22716b3a5897e96b211bfe940a87caa1c426476eb8d1fb6cfadb75d0b8e81
and DLL850c2ff196aae5adf32d838934507021569c230fcad610c549bb8021dd96fb27.
Native Windows/Proton held-host, handshake, protocol, interpreter and addon
fixtures all executed successfully in a separate prefix. Each child success is
proved by a fresh Windows CMD completion file, not merely Proton launcher exit.
Held-host also writes its own completion receipt after all assertions. The
interpreter fixture proves skip-write deferral preserves stack/register cleanup;
protocol fixture checks response text never claims a proposal was signed.

The private compiler needed its already-installed SDK cppwinrt include supplied
through CL. An attempted standalone-interpreter target in the game build was
corrected to a separate native/interpreter CMake build. Refreshed archive input
timestamps and regenerated register-local copies to prevent stale Ninja objects;
final builds include the actual generated hooks and interpreter registration.
Build helper .local-runtime/manager-addon-5605345/build-held.sh records commands.

Installed EXE1742d8c261f661a46434d0345a05e4b59270676ab27e18fc4585672d441d6bcb
and DLLd4d1020eee8732aa3b60ba08a8a93237922619548344ab8c9540ff9f81750190
remain unchanged. Prior game PID102235 was no longer present at the final check;
no install, launch, game/save write, cloud change, control renewal or paid inference
occurred. New game execution/playability is not claimed. Accepted-deal settlement,
complete required books/rules, live owner/UI flow, guest/ledger agreement and
crash/save recovery remain core requirements before this mode can be delivered.

Prior sourcec4e073d CI was verified green: Build38668052493 and Franchise AI
38668052451. New held-source CI remains to verify after push.

## Core negotiation: submit intent across game threads

Fixed a functional gap in the held proposal path: a foreign-thread signing
callback previously deferred retail signing but could not request a proposal.
The private adapter now captures the selected player's complete normalized
observation and exact offer, with selected-context checks before/after sampling.
A lock-protected single-slot intent copies that observation without touching the
single-owner transport. A generation token invalidates callbacks crossing screen
exit/reopen or service restart. Only a fresh matching owner observation consumes
an intent; player/offer/calendar/payroll changes or unreadable samples discard it.
Duplicate unchanged submissions remain suppressed. Also cancel consumed intent
waiting behind a read reply when a later observation fails. The public addon ABI
and control policy are unchanged; this adds no guest write or settlement permission.

Validation: final private MSVC Windows game/DLL build passed. Staged EXE SHA256
4ae10a05769657487c874b3ef83473353566e0b767a0d9a26ada9aaa7dc4ffdb;
staged DLL3ca08d35bc3dd9e4409e0ef65fbaa22bd872bdd9e5894ae3085df69d7290ce9e.
Actual Windows held-host, handshake and addon fixtures passed in the separate
Proton prefix. The host fixture asserts transport owner identity for submit,
ready and take, and checks foreign submission delivery, duplicate suppression,
changed-term rejection, invalid observations before/after intent consumption,
screen-generation rejection, malformed bounded strings and default-off behavior.
Each fixture has a fresh CMD success marker and expected child output; the host
also writes its own final completion receipt. The initial private runner command
failed before child output; isolated echo probes identified quoting/redirection
as the issue. The corrected invocation executed all three fixtures successfully.
Receipt: .local-runtime/manager-addon-5605345/handoff-fixtures-receipt.json.

Verified installed hashes unchanged: EXE1742d8c261f661a46434d0345a05e4b59270676ab27e18fc4585672d441d6bcb,
DLLd4d1020eee8732aa3b60ba08a8a93237922619548344ab8c9540ff9f81750190.
No user game launch/install/save write, cloud change, control renewal or paid
inference occurred. Actual owner/UI interaction, accepted-deal guest/ledger
settlement, complete required opening books/rules and save/load recovery remain
unfinished. The installed runtime does not enable this experimental mode.

Prior held-source65f913a is confirmed green in fork CI: Build38671991468 and
Franchise AI38671991412. This handoff change's CI remains to verify after push.

## Core signing: atomic settlement of a recorded acceptance

Added engine-only FranchiseStore.commit_accepted_proposal, reusing the existing
signing transaction rather than creating another financial store. It derives
terms, promises, personality/performance evidence and attributed reason from the
persisted accepted proposal; callers cannot supply replacement terms or story.
Requires distinct proposal/settlement IDs and a callable current access check.
Revalidates latest player dialogue, financial revision/preview, global ownership
and supported salary/draft rules. Ownership, annual cap, cash, promises and the
signed story commit together, with a final access check after inserts. The
acceptance dialogue remains an immutable separate event, linked from settlement.

Replay reconstructs the expected settled story from its earlier proposal and
checks exact terms/preview/history. Same-ID retries return the original receipt
without inference or another financial change, including after later unrelated
transactions. Different IDs cannot consume an acceptance twice; ordinary signing
cannot forge the settlement label. Concurrent same-ID and competing-ID requests
are covered. No bridge operation or native commit permission was added: guest
application, guest confirmation, durable cross-save journal/recovery, complete
required books/rules and actual game/save testing still gate delivery.

Validation: all12 targeted settlement tests passed0.744s. They cover persisted
cash/promises/story, original and4x SOFTDRINK encodings, historical retry,
superseded/rejected/missing acceptance, revision/foreign ownership, rollback on
shutdown after SQL inserts, tampered replay, and competing transactions. An actual
child process exits73 after inserts/before commit; restart observes no phantom
contract or cash and then settles once with no repeated inference. Final full738-test
suite passed22.683s. The initial sandboxed suite had
four loopback bind PermissionErrors; the authorized socket-enabled rerun passed.
Money audit passed, including5050 bonus conservation cases. No game asset,
installed runtime/save, cloud control or paid provider was changed or invoked.

Prior native handoff05fc86d is verified green in fork CI: Build38673028105 and
Franchise AI38673028333. Settlement-source CI remains to verify after push.

## Core signing: exact saved-effect confirmation

Added tools.confirm_saved_signing.confirm_saved_signing for the guest coordinator's
confirmation boundary. It checks immutable before/after payloads against a pinned
before hash, existing durable player bindings, typed accepted offer, captured raw
terms and target team. Requires exactly the bound free agent to join that team,
exact initial contract amount/bonus/shape/terms, unchanged contract fields across
the entire declared player bank (including unbound records), unchanged other
memberships/calendar/cap/first-year adjustments, reconciled all32 payrolls and an
exact first-year target charge delta. The validated profile determines1x/4x scale;
no arbitrary caller multiplier. Returns JSON-safe source fingerprints and exact
charges with write_authorized=false. It permits unrelated settings-byte changes
and does not claim complete byte equality or financial coverage beyond scope.

Real private AIBASELIN -> AIGILDON regression passed: bound slot1792 Jason Gildon
moves free_agents -> Giants,829/4/1/2 saved terms, charges4766000/3523000, payroll
72272000 ->77038000. Before SHA256
2f82cfd9c608411c40b006db10f1e6dc6dfe46b187dd50c1ae94dd6341fd3dd2;
afterac16245c5fcd743f3cc9e6aa37d76de72424238782de353765c758d242c6bc7d.
Receipt .local-runtime/saved-signing-confirmation-gildon.json. These are the earlier
user signing saves, not AI effects or a new pack/game execution. No retail assets
or bindings are added to Git. Existing attribution remains in the independent
FXG reader modules used here.

Validation:10 authored confirmation tests passed0.114s, covering original/4x
charges, wrong actor/team/terms, noninitial elapsed term, other bound/unbound
contracts/memberships, calendar/cap/flags/accumulator changes, payroll mismatch,
bank/biography changes, wrong hash and unchanged payload. Full748-test suite
passed23.216s with authorized loopback access. The first targeted invocation used
module loading without the fixture directory on sys.path; the repository's
standard unittest discover invocation passed. Initial real receipt serialization
exposed Fraction values; projection now uses the existing exact json_amount codec.

This remains a read-only component. Live guest application, durable intent and
cross-save recovery, current control rechecks, complete modern opening obligations
and actual integrated signing/save/load are still required before releasing held
native offers. Nothing was installed, launched or changed in game saves, cloud
control or paid inference.

## Core signing: durable prepare/confirm/settle journal

Added franchise.guest_signing with one league-wide pending SQLite journal. It
retains exact accepted-proposal/input fingerprints, pinned bindings and original
save bytes. Preparation requires all32 supported team books, known cash inventory,
exact saved/ledger ownership and annual charges, preserved legacy terms or exactly
supported active terms, current accepted preview/revision and current access
before/after insertion. Unresolved first-year adjustments or guest payroll
projections reject; legacy cash import remains unavailable. No revenue adjustment,
zero-cash assumption or new guest-write permission is introduced.

Prepared work blocks other cooperative FranchiseStore writes across processes,
including other clubs, actors, direct settlement and migrations. Constructor
schema initialization/reopening and reads remain available. Older writers that
lack this guard are unsupported. The journal has a versioned intent and a unique
pending-row index; it is separate from immutable generation checkpoint tables.

The existing signing helper can now use the coordinator's SQLite transaction.
Saved proof/after bytes, resolved journal, cap, cash, ownership, promises and story
commit together. A failure after inserts rolls all of them back. Same journal and
payload retry returns the original receipt; changed saved payloads reject. Reads
verify source proposal/backup/proof fingerprints and identify before,
candidate_after, confirmed_after or unrecognized state even with AI disabled.
A settled journal with the old original save is detected without silently
reversing finances. Cancellation requires the exact original bytes and successful
stopped-game checks before/after updating state. It never restores files or
renews/re-enables controls. Native apply/save/reload and actual quiescence checks
are still absent; these APIs deliberately have no bridge operation or write grant.

Validation:12 authored full-league journal tests passed2.364s. They cover restart,
known-cash/league gates, same-ID and concurrent settlement retries, changed
preparation, competing operations/club writes, shutdown after prepare or financial
inserts, original-save cancellation, game restart during cancellation, disabled
control recovery, invalid saves and corrupt backup/proof rejection. An actual
child exits73 after journal/financial updates but before SQL commit; restart
retains the original backup and prepared state with unchanged finances, then
settles once without inference. Imported fixture class initially duplicated its
10 tests; module-qualified fixture import corrected collection. Final full760
regressions passed29.765s. Money audit passed5050 conservation cases. No game,
installed runtime/save, cloud authorization or paid inference changed.

Prior167eee8 CI is confirmed green: Build38674199746 and Franchise AI38674199935.
Prior3b2b6c9 settlement CI is also green: Build38673709294 and Franchise AI38673709155.
Journal-source CI remains to verify after push.

## Requested upstream Steam Deck contribution: initial scope inspection

User asks whether the original repack creator can receive deployment support.
Current mod base is SOFTDRINK 2K28 v0.6 (cruuz/softdrink-2k28); repack upstream is
BeyondTomrrow/2K5Remade. Keep a contribution focused on deployment rather than this
AI branch. Verified Gaming Mode registration/controls came from a private untimed
launcher preserving Steam identity, Valve's steamos-add-to-steam helper and local
Xbox-prompt/mouse-controller defaults; user confirmed both triggers. A portable
public launcher still needs extraction from those private installation scripts.

Current public tools/package_steamdeck.py is a manifest ZIP packager, not an
installer or Steam library registration tool; its README's blanket untested-Proton
statement is stale relative to later private evidence. Candidate runtime fix
61ad649 in cosmokay1/xboxrecomp joins the kernel timer before RAM teardown and
corrects Windows mapping paths; parent3a256fd updates that dependency. It must be
compared with fresh upstream code and separated from prerequisite platform
changes before a dependency PR. No whole AI-branch PR, maintainer message or
binary publication was made. User was told a focused Steam Deck PR is feasible;
upstream publication has not been represented as completed.

## Native Linux sidecar transport, separate from the full-game port

User requested removing Proton, then clarified that presentation replacement must
retain the nice scoreboard styles, replacing WebView rather than simplifying the
scoreboard. FOX/CBS presentation.json already uses native Direct2D; NBC_SNF uses
HTML/CSS/JS and WebView2. No feature removal or simplified-scoreboard change was
made. Native renderer/style parity and full-game Linux deployment remain open.

Added a Linux PipeClient behind the existing platform header: exact absolute
execve argv, bounded JSON framing/envelope validation, nonblocking socketpair I/O
with a five-second write-and-reply deadline, one pending request and bounded abort.
Unrelated descriptors are closed at exec; MSG_NOSIGNAL preserves the host's
SIGPIPE handling. Default SIGCHLD ownership is required. Normal teardown kills the
owned process group before reaping its leader; Linux parent-death signalling kills
the direct peer after abrupt parent exit. This is not a cgroup sandbox or Windows
job equivalence: arbitrary descendants need cooperative cleanup after abrupt
parent death and must not escape their owned group during normal teardown. The
Windows implementation is retained behind its existing platform guard.

Deck build initially could not find a native C++ compiler. Added g++ only to a
local derived Ubuntu24.04 build container (247MB;42GB host free), leaving SteamOS
and the installed game untouched. Native GCC13.3 Release build completed. CTest
protocol/echo/linux_process all passed in7.60s, including exact argv, repeated
requests, concurrent-submit refusal, malformed/mismatched/oversized replies, dead
peer, stalled timeout/abort, descriptor inheritance, process-group descendant
cleanup and abrupt-parent death with child reaping. The same three ELF x86-64
binaries then ran directly on SteamOS glibc2.41, outside containers and without
Wine/Proton; all passed. This is component evidence only. No game boot, contract
write, save modification, paid inference or remote-control renewal occurred.

Previous journal commit3bd6525 CI is confirmed successful: Franchise38675583760
and Build38675583704. New transport consumer/standalone CI remains to verify.

Consumer validation: all760 Python regressions passed22.348s outside the sandbox.
The initial sandbox run failed only four loopback-server binds with EPERM; those
passed when rerun with local networking allowed.

### Presentation reference: Timkay Nicotine

User suggested https://github.com/timkay/nicotine. GitHub API inspection of main
81f0dbe88f7ff730f8dba1adff5011b9e1ae4962 found a QuickJS native-call host with
app-owned drawing adapters (Cairo on Linux, GDI+ on Windows, Core Graphics on
macOS). README and docs/DECISIONS.md make the separation useful as an architectural
reference: readable scripted behavior and native drawing need no browser. It is
not a DOM/CSS engine or a drop-in NBC_SNF page renderer. Existing HTML/CSS geometry,
fonts, assets, clipping and animation need deliberate translation and visual
comparison. The game needs an off-screen alpha surface rather than a separate
GUI window. README describes its Windows drawing adapter as unexecuted; GitHub
reports no recognized repository license. No Nicotine code/dependency was copied
or integrated; source reuse terms and embedding validation remain unresolved.

## Optional WebView build and actual native style parity

Added NFL2K5_HTML_PRESENTATIONS (defaultON) to omit webview2_host.cpp, its SDK
requirement and loader when disabled. The retained native JSON renderer, package
geometry, assets, fonts and animation definitions remain. Disabled builds log
and exclude unsupported HTML packages, so they cannot select an empty browser
presentation. DefaultON protects NBC_SNF until its native equivalent is visually
verified; this does not fulfill that replacement or the native Linux game port.
No installed game, selected presentation or save was changed.

Added native/presentation, an asset-free fixture compiling the actual presentation
and portrait source twice with HTML support on/off. The enabled fixture's browser
factory fails if called; neither variant links WebView. Authored match state goes
through the real HUD callback and returns BGRA/geometry, not a mock drawing. The
fixture waits for unchanged frames after initialization/fade and retains bytes.
Both Windows executables compiled under private MSVC19.44 and executed in the
isolated Deck Proton fixture prefix, with fresh child completion markers and
stdout. This is Windows component execution, not a native Linux renderer or
actual game execution. Logos absent from source remain absent in both variants;
asset-complete style and animation review is still required. Windows CI now runs
this actual renderer comparison without retail assets.

The initial FOX comparison failed while CBS matched. A fixed800ms capture could
finish during initialization/fade; waiting for stable frames still reproduced
the mismatch. Inspection identified a real existing cache issue: eased opacity
was rounded to three decimals in the render signature before the entrance
transform reached its final geometry. The key now includes lifecycle state and
progress, forcing the final settled frame to redraw. With that correction the
actual on/off variants match exactly in both pixels and placement:
- FOX1040x185, stride4160, HUD120,507;17432 colored pixels; BGRA SHA256
  395234650fb39a91adf5eafa2cedd44bfd5dcc7f9ec67d13f69f3352cebaf718.
- CBS1186x428, stride4744, HUD47,268;79600 colored pixels; BGRA SHA256
  62566bfbf1d408ec666e53e5a6051a2c136289ea96232c817d3666aa17633bbd.
Private receipt/images retained under .local-runtime/presentation-verified.

A separate cloned-source Windows game configuration also passed with
NFL2K5_WEBVIEW2_SDK=/task/deliberately-missing-webview-sdk and HTML disabled;
build.ninja contains the disabled source define and neither WebView host nor
loader. The first configure lacked the existing SDL3 dependency mount; retry
with dependencies mounted read-only passed. This was configuration verification,
not a full game compilation or boot. Python compare source compiles; diff checks
pass. New presentation-source CI remains to verify after push.

The independent native Linux transport milestone is now CI-verified: consumer
8503615 Franchise38677356141 passed Windows/Ubuntu, Build38677356207 passed;
standalone fast-forward export2a2110d CI38677485314 passed Windows/Ubuntu.

## Core signing: opt-in service journal coordination

Connected the existing engine journal to explicit guest_signing_prepare,
guest_signing_confirm and guest_signing_status bridge operations, enabled only
with --guest-signing and startup-pinned save/bindings. Clients cannot provide
paths, bindings, save bytes, outcomes or write grants. Current save reads are
bounded regular-file reads with identity/size/time checks, not the original
startup snapshot. Preparation retains the all32 supported books/known-cash gates
and accepted proposal/terms/revision checks. No actual opening liabilities were
invented, imported or relaxed. Preparation/confirmation still grant no guest writes.

Writes require current remote access, connection and deadline checks inside the
journal transaction, including rereading the same current save bytes on each
check. Preparation preflights reply capacity before inserting. Confirmation checks
capacity inside the existing transaction after financial work and rechecks access
afterward; failure rolls back journal, saved proof and every financial/story
effect. It reuses the accepted proposal without another provider request. Status
returns bounded hashes/state/save-position instead of raw backups and remains
readable with AI disabled. Cancellation stays engine-only until a genuine
stopped-game verifier exists. CLI startup still requires a valid snapshot;
corrupt/unreadable-startup recovery needs a dedicated launcher, as documented.

Preparation/confirmation share the existing single asynchronous worker so the
stdin reader can detect EOF during a write. Competing requests receive busy.
Disconnect after preparation or financial SQL inserts prevents commit. Explicit
false authority/connection callbacks now reject through transport wrappers. No
new inference, remote control renewal, automatic guest application or file
restore was added. The installed runtime and its configuration/saves are unchanged.

Validation:15 new authored tests passed2.530s; final full775 regressions passed
24.680s. They cover disabled/default capability, strict fields and hashes, stale
saves, file change after inserts, shutdown before/after financial updates and
after reply validation, timeout, oversized replies, replay/restart, busy/EOF
rollback and disabled read-only recovery. An actual sidecar child prepared against
a server-selected authored file, exited, then a fresh child read the authored
after-save and settled exactly once; another child with unavailable Vertex/ADC
returned recovery status without inference. Callback-only tests do not stand in
for game execution. Money audit passed5050 conservation cases. Python compile/help
and diff checks passed. New source CI remains to verify after push.

Prior2468fb1 presentation source is now CI-verified: Build38678553596 passed
Windows (including the actual native FOX/CBS pixel comparison) and Linux runtime;
Franchise38678553423 passed Windows/Ubuntu. Full Linux game rendering, NBC native
style parity, real financial opening import, native apply/save/reload and delivery
acceptance remain open.

## Windows saved-signing reader compatibility repair

013854d CI38679439266 passed Ubuntu but failed Windows at the restarted
confirmation child's startup, before any reply. Build38679439375 passed. The
reader compared path stat and descriptor fstat ctime directly. CPython documents
an open Windows inconsistency where these expose creation and change time
respectively (https://github.com/python/cpython/issues/157671). Retain cross-API
device/inode/size/mtime checks, but compare ctime within each API separately.
This preserves detection of path and descriptor mutations without assuming the
two timestamp sources have identical semantics. Child test failures now include
exit code and stderr instead of hiding startup diagnostics.

Four focused regressions accept differing stable ctimes and reject path ctime,
descriptor ctime, identity, size and mtime changes. Existing private Windows
Python3.13.16 under isolated Proton did not reproduce the mismatch: both APIs
returned equal timestamps after a rewrite. This does not establish real Windows
behavior; fresh hosted Windows CI is required to validate the repair. No installed
game, save, remote control or paid inference was changed.

Local validation after repair:779 regressions passed29.355s with localhost
fixtures permitted; the initial sandbox run had four socket-bind permission
errors, not assertion failures. Targeted15 signing bridge tests passed5.403s.
Money audit retained5050 bonus conservation cases. Hosted Windows validation is
pending the repair push; native apply/save/reload remains unfinished.

Repair f876edb is now CI-verified: Franchise38680339623 passed Ubuntu and
Windows2022, including all779 regressions, money audit, native protocol,
interpreter and actual Windows pipe/restart checks. Build38680339592 passed
Windows/native presentation and Linux runtime checks. The previously failing
Windows saved-signing process restart/confirmation test now passes. Separately,
Windows Python3.13.16 under the isolated Deck Proton prefix passed all19 targeted
reader/journal bridge tests in15.693s, including actual child prepare/restart/
confirm and disabled recovery. The fresh log is guest-journal-windows/probe.log
in the private build stage. These are component fixtures, not game signing or
save/reload acceptance. Next core work remains native journal coordination and
verified opening obligations, followed by controlled apply/save/reload/recovery.

## Native held acceptance to saved-signing preparation

Added an explicit NFL2K5_FRANCHISE_GUEST_SIGNING=1 mode shared by the native
host and service; absence defaults off and other values reject. Native startup
requires the existing pinned-context/performance/guest-offer/held-negotiation
configuration. The installed runtime remains unchanged and this unfinished mode
must not be enabled there. A consumed validated captured acceptance is converted
into a journal request using its exact source proposal ID, raw terms, team,
revision and before-save hash; there are no caller overrides or new inference.
The deterministic journal ID appends -guest to the proposal ID. Nonaccepted,
uncaptured and error responses produce no preparation. Altered source evidence
rejects through existing native validators. The C client requires a successful
hello grant and all three advertised journal operations for journal writes.

The actual owner-thread C host queues preparation only while the captured offer
and screen remain current. Once queued it keeps retail judgment held and blocks
further offer requests, retaining pending receipt collection across navigation.
Errors, malformed/lost receipts and transport failures never unlock an uncertain
signing. A preparation receipt must match ID/hash/state and deny write authority.
Native display continues to describe a held signing rather than a completed
contract. Durable pending-work guards survive restart; no automatic cancellation,
guest application, file restore or remote renewal is introduced. Actual opening
legacy obligations and apply/save/reload/recovery remain unfinished.

Validation: all779 local regressions passed27.609s, including actual sidecar
children with explicit environment opt-in, CLI replay and invalid-value refusal.
Money audit passed5050 conservation cases. Native protocol checks passed0.25s,
including source substitution, rejection/error handling and corrupt receipt
refusal. Authored C-host fixtures now cover opt-in gating, owner-thread prepare,
queued/failed preparation remaining held across changed offers/screens, and stale
acceptance suppression; these fixtures use transport stubs, not game memory.

Actual private MSVC compilation passed for the final host/client/DLL and plain-C
smoke executable. Real Windows/Proton protocol, held-host, handshake and loadable
addon fixtures passed under the isolated ABI2 fixture prefix, each with fresh
child completion receipts and expected stdout. Private handoff-fixtures-receipt.json
records staged DLL04128fbee37218606271247d03ee9bfab6bd45a2bfa9d4c37d9fae1cdf2c5cd7.
Installed EXE1742d8c and DLLd4d1020 hashes remain unchanged. These authored
component checks do not establish accepted live game application or save/reload.
Hosted Windows/Linux CI and plain-C service lifecycle assertions remain to verify
after push. No game execution, installation or paid request was performed.

2abc9a6 hosted validation completed successfully: Franchise38682855612 passed
Windows2022/Ubuntu, including the new actual plain-C client cached-reply and
nonacceptance API checks against offline sidecar children. Build38682855623 also
passed Windows/native presentation and Linux runtime checks. This is native
Windows addon preparation, not a native Linux full-game port. The extra private
Deck client/service runner initially could not find its unbuilt C++ smoke EXE;
that fixture is being built separately, not treated as a product failure or a
passed run. Installed user binaries/saves remain unchanged.

Review follow-up: keep sampling offer freshness while preparation blocks further
requests. Changed terms clear the displayed proposal without queuing another
request, and obsolete preparation receipts stay hidden. The host fixture now
checks this before navigating away with preparation still pending. The private
rebuild compiled/linked the updated C host/DLL, but its SSH connection stalled;
independent Deck process inspection found no remaining private build/fixture
process, and no fresh completion receipt was produced. Closed only the stale
local SSH client. That run is unverified, not passed; the installed game process
was left running and untouched. Hosted Windows must verify the final follow-up.

Final freshness follow-up1a9654f passed Franchise38686150816 Windows2022/Ubuntu
and Build38686150717 Windows/Linux. The hosted actual held-host fixture proves
changed terms clear the pending display without another request, and navigation
before reply does not release signing. Separately, a focused current-version
plain-C client/service fixture passed under isolated Deck Windows Python/Proton:
cache/consumption gates, uncaptured rejection and durable restart checks succeeded
with a fresh native-smoke.passed child receipt. Its private output is
guest-journal-windows/native-smoke.log. The earlier broad private checker used an
obsolete expected reply count (four rather than current five), so its assertion
failure is not claimed as a passed run. Hosted CI covers the complete current
checker. No installed binaries, user saves, game session or remote control was
changed. The full native Linux game port, verified opening legacy import and
actual application/save/reload/recovery remain open.

## Explicit legacy-unknown cash scope for new contract accounting

Identified a structural opening gate: legacy schedules were supported for cap,
but cash initialization always rejected any legacy team, while journal prepare
required a cash book on all32 clubs. Packed cap liability cannot establish old
nominal cash, paid cash or guarantees. Added an optional explicit inventory of
unknown legacy player IDs rather than assigning fabricated zero obligations.
Default initialization remains strict, and no live franchise policy or data has
been changed while the user's cash-scope preference is pending.

Cash initialization must enumerate exactly the preserved legacy players; modern
opening obligations still require matching known cash records. Unknown IDs cannot
also have known/fabricated-zero records or be replaced through add_contract.
The durable initialization event and replay validate scope, identity coverage,
canonical ordering and matching cash postings. Existing full-coverage snapshots
retain their original format. Partial snapshots publish null nominal/paid/unpaid
franchise totals, separate known_totals and explicit unknown_legacy_players.
New contracts and their allocated payments remain exact and idempotent.

The journal can prepare/confirm a new accepted contract with this explicit scope,
retaining all32 saved-cap/identity/contract/revision checks and atomic story,
financial and saved-proof settlement. Legacy cap schedules remain unchanged;
legacy conversion/termination and calendar aging remain unsupported. Native
lifecycle receipt formats do not represent partial totals, so release/trade/
restructure bridge routes refuse that mode before writing. This does not add a
cash spending ceiling, synthetic revenue, automatic migration or guest writes.

Eight authored tests cover null totals vs known subsets, unchanged legacy cap,
known modern opening coverage, invalid/duplicate/missing/zero cash declarations,
new payment/retry/restart, replay tampering, lifecycle bridge refusal and a full32
saved-signing prepare/confirm/replay with one fixture provider call and exact new
cash. Targeted checks passed0.550s. Initial full784 tests passed26.079s before
three added cases. The final787 run caught one existing diagnostic-substring
assertion after an error-message update; corrected the wording and reran. Final
suite evidence and hosted Windows/Linux CI remain to record after completion.

Final787 regressions passed25.401s after bounding the prompt cash summary to an
unknown-contract count; full player IDs remain only in the ledger inventory.
Money audit retained5050 bonus conservation cases. Compile and diff checks passed.
No live database was initialized, cash history guessed, control enabled or paid
request made. Next verification is hosted Windows/Linux CI, followed by explicit
opening scope/source selection and native guest application/recovery work.

dbce8ad CI38691414837 passed Ubuntu but Windows failed only during temporary
SQLite fixture cleanup: test_replay_rejects_scope_and_null_total_tampering left
sqlite3 connections open (the transaction context manager does not close them).
Windows ran787 tests146.249s with this single cleanup error. Changed the fixture
to explicit contextlib.closing plus transaction contexts for its edits; production
store connection ownership is unchanged. The targeted eight-test suite is rerun
before push; fresh hosted Windows verification remains required. The additional
private Windows Python check could not stage because steamdeck.local did not
resolve, so it was not run or claimed as passed.

Cash-scope repair4a74436 now passed Franchise38692925601 Windows2022/Ubuntu,
including all787 regressions, money audit and actual native pipe/restart checks.
Targeted eight cases passed0.611s after explicit fixture connection closing.

A separate private preflight used the existing legally provided pinned MyNFL1
snapshot, without changing the save, bindings or any live DB. A new disposable
read-only projection replayed all32 clubs,2070 bound player identities and1693
preserved legacy contracts with explicit unknown cash. Every current roster cap
charge and legacy schedule hash matched; all franchise-wide cash totals remained
null and known subsets were empty (no new contracts were inserted). Giants
roster payroll remained211.984M at301.2M cap, with89.216M roster-only room.
Modern free-agent classification was deliberately left pending and a new offer
was refused; no salary floors, retained debt, rookie reserves or guarantees were
invented. A zero reserve is labeled only as a projection convention, not verified
complete Team Salary or authority for writes. No model/game execution occurred.

Private evidence: .local-runtime/softdrink-v0.6/mynfl1/
cash-scope-preflight-830u4h3t/receipt.json and read-only-projection.sqlite.
Source payload SHA2564c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3;
bindings9955880d3fb6a02eaebc4c1662cfac075afb59443a1191e709bf2dd51c9ee442.
These are existing local snapshot inputs, not proof of the current Deck session
or a financial migration. Live opening/source selection, supported legacy aging,
partial lifecycle native receipt support and actual apply/save/reload remain open.

Companion Build38692925575 also completed successfully on Windows/Linux. The
extra private Windows/Proton cash-scope suite remains unrun because the Deck's
hostname did not resolve during staging; hosted Windows results are authoritative
for that component scope, not proof of game playability.

## Native pending-save status and confirmation

Connected the native addon-owned journal to asynchronous checks of the service's
startup-pinned save path. While pending, the owner thread queues one check every
two seconds; unchanged before-saves never queue financial writes. A validated
prepared/candidate_after status plus the existing hello grant can queue confirm
with that exact after-save hash. The service still checks current remote control,
connection, deadline and file bytes inside atomic journal settlement. No new
model request, directory discovery, game-kernel file hook, control renewal or
native guest write permission is introduced.

The native client retains accepted identity, exact charges, revision and journal
binding independently of temporary reply buffers. It validates recovery states/
hashes and matches confirmation to that acceptance; contradictions abort the
owned transport. Confirmation is followed by a status read; confirmed-after and
cancelled states stop polling. Errors force fresh reads. AI-disabled confirmation
clears the local grant, leaving read-only recovery without another hello. The
owner thread continues collecting after navigation, hides stale panels and logs
only changed journal responses. It never unlocks retail signing, including after
settlement: game application/reload and continued-session rebinding remain open.

Added actual Windows C-client/service fixture target and CI invocation. Authored
full32 legacy/explicit-unknown-cash inputs contain one recorded captured proposal;
its provider is a Mock called once during fixture setup. The real native test
replays it with the offline service, prepares, reads before-state, copies an
authored candidate save, confirms, rereads settled status and opens a new client
whose Vertex hello is disabled by absent runtime policy/credentials. Explicit-ID
recovery must still read confirmed-after. The driver verifies one financial
revision, one new exact cash obligation and two history events. No retail/game
file is used, and copying a test save is not native game application evidence.
A local fixture check initially compared the original checkpoint with replay;
checkpoint history legitimately gains the recorded proposal. Corrected that
fixture comparison to preserve source evidence and use the warmed replay.

Validation:788 local regressions passed28.196s; portable native protocol checks
passed0.59s, including AI-off reads, no confirmation before a verified candidate,
foreign IDs, hashes, charges/revision substitution, invalid state combinations,
refusal recovery and terminal stop. Actual fixture frames also passed the native
C++ validators via a temporary local executable. Money audit retained5050 bonus
conservation cases. Windows compilation/process execution for the new fixture is
pending CI; the Deck was unavailable in the prior turn, so none is assumed here.
Installed runtime, saves and remote controls are unchanged.

8e68e91 hosted verification completed successfully: Franchise38701244992 passed
Windows2022/Ubuntu and Build38701245086 passed Windows/Linux. Windows compiled
and executed the new actual franchise_saved_signing_check through the Python
driver: captured proposal replay, explicit prepare, before/candidate-after reads,
one financial confirmation, confirmed-after stop and fresh AI-disabled client
recovery all passed with authored files. The full788 regressions, existing native
C-client/cache/handshake/interpreter fixtures and money audit also passed.
This closes native saved-state coordination for the active journal, not real
in-game guest application, active-save discovery, session rebinding or reload.
No installation, retail file mutation, paid inference or control change occurred.

## Separate judgment and precommit addon boundaries

Static inspection confirmed that the existing single boolean hook conflates the
interactive judgment return and the bypass/shared precommit path. Added the
application-private franchise.sign-gate.v2 payload (stage/context) without
changing public ABI2. Judgment retains existing captured-offer submission.
Precommit calls only the held-mode check with NULL/zero intent, without guest
sampling or treating a bypass/CPU call as a new interactive negotiation. The
thin host preserves v1 fallback for older addons; nonboolean nonzero results and
unknown stages remain held. No code issues an application permit or bypasses
retail judgment. The interpreter keeps the same cleanup target and splits its
callbacks by stage. The generated patches now pass the same stage labels.

Existing generator markers previously caused cached code to skip updated patch
bodies indefinitely. The patcher now upgrades exactly the recognized old one-line
signing hook, rejects old hooks under --check, refuses edited bodies and preserves
CRLF. It does not replace arbitrary contributor edits or generalize patch upgrades.
Fresh, old, edited, repeated and CRLF authored-cache cases are covered.

Validation:792 local Python regressions passed26.327s. Three portable native
checks passed0.47s: protocol, actual thin shim (including old-addon hold fallback)
and actual DLL adapter with inert host callbacks. Precommit sampled no memory or
epoch and created no observation intent; judgment retained its normal sampling
path. Disabled behavior and invalid message sizes/stages were checked. Windows
DLL forwarding fixtures now exercise the new stages while service is disabled.
A full local generated-tree --check is running to verify its existing cached
hooks are detected; Windows compilation/execution and new source CI remain to
verify. The installed game, controls and saves are unchanged. Safe application
still requires a verified live-state/control permit and replacement judgment
result semantics, followed by actual game save/reload evidence.

Full generated-tree --check reported exactly the two recognized old signing
bodies; every other patch was already present. Applied only those two upgrades
to the existing local cache and the scoped stage check then passed. The tracked
generated diff contains only the two owned hook call/prototype changes; no new
retail data or executable is added. Static inspection also showed that the retail
judgment routine supplies an output score through the transaction's out-parameter.
A future authorized bypass must preserve verified result semantics as well as
current-state guards; blindly jumping to precommit is not a completed solution.
No permit or result-score substitution was implemented in this hold-only change.

33ea4ec stage source passed Franchise38711085426 Windows2022/Ubuntu and
Build38711085469 Windows/Linux, including actual DLL/shim/adapter stage checks.
Review then found a fail-open edge in the pre-existing host shim: if explicit
controlled negotiation was requested but addon event dispatch returned zero
(missing/disabled/failed module), the original retail transaction could continue.
The shim now retains the hold whenever NFL2K5_FRANCHISE_NEGOTIATION=1, for v1
and stage-aware paths. Unset/0 retains vanilla behavior when no addon holds.
This source-only guard does not enable AI, change launch settings or grant writes.
Portable actual-shim tests verify missing-handler responses under both launch
settings, and the Windows loader fixture exercises the hold after module stop.
The fixture uses CRT environment setters to match the shim's getenv semantics.
All three local native checks passed0.65s. Fresh Windows CI is required for this
follow-up; the installed runtime remains untouched.

Final stage/guard follow-upc388051 passed Franchise38715022063 on Windows2022
and Ubuntu, including all792 regressions, the actual portable shim/adapter stage
checks, Windows DLL stop/unavailable-addon guard, native pipe/interpreter checks
and saved-signing confirmation/recovery process fixture. Build38715022192 also
passed Windows/Linux. This verifies stage discrimination and held-mode fallback;
it does not verify a full new game build, live judgment replacement, an apply
permit or game execution/save/reload. Those remain required before enabling the
unfinished negotiation mode in the installed runtime. No private assets were
published, user save changed, control renewed or paid model request made.

## Whole-league native financial comparison before application

The next application prerequisite is a financial comparison of live memory with
the prepared saved world. A selected player's biography/offer and the original
save alone do not exclude unsaved changes elsewhere. Added the application-private
franchise.finance-state.v1 snapshot on the existing addon ABI2. It is read-only,
explicitly requested and contains raw cap/calendar, all32 payroll/flag/accumulator
triples and every bank slot's packed contract/flags plus normalized ownership.
Names, ratings, pointer values and roster order are excluded. No public ABI,
generic sidecar policy or native signing decision changed.

Static inspection of324060 and2425C0 resolved the live free-agent vector as
bank+38, DWORD count and relocated list pointer+4. It is not a Team record.
The capture bounds the observed expanded bank and all32 clubs, rejects duplicate
or malformed membership and rechecks selection/bank/calendar/table/cap metadata.
It cannot lock guest mutations and is explicitly not an atomic snapshot, identity
proof or application permit. A future coordinator still needs quiescence, bound
identities/runtime, current remote authority and one-use application semantics.
No live permit, retail output-score replacement or guest commit is implemented.

Added an independent saved projection through the existing roster/calendar and
payroll-reconciled cap readers, plus an explicit-file comparison CLI. The actual
addon callback (with inert service callbacks) matches independently authored
saved semantics across relocated banks and reordered free-agent lists.28 cases
cover unrelated/unrostered contract changes, all32 adjustment coverage, payroll,
ownership, calendar/cap changes, duplicates, overflow, invalid modes/counts and
truncated memory. The same28 pass AddressSanitizer/UndefinedBehaviorSanitizer.
All796 Python tests pass25.352s; the three existing native CTests pass0.96s.
Windows/Ubuntu CI now includes the cross-language comparison; new CI is pending.

Read-only projection of the existing pinned MyNFL1 save succeeds: before hash
4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3,
29241 projection bytes, SHA256
eeeb2175d84fff5b411c9189d6f6c07b45adc5bf8b954f6e1d9f4af5f9f10de5.
The source save remained byte-identical. This is saved-only evidence, not a live
comparison or complete opening-book proof. The installed Deck build/settings,
user saves and remote controls are unchanged; no paid inference was made.

Source d354faf passed Franchise38725532744 on Windows2022 and Ubuntu: all796
regressions, both actual-addon28-case financial comparisons, standalone process
checks and existing native/interpreter/saved-signing fixtures. Build38725532721
also passed Windows/Linux runtime/tool and native presentation checks. These
are component/build results, not a full newly integrated game. A read-only SSH
retry failed DNS resolution for steamdeck.local, so no live financial snapshot,
private installation or runtime/save verification was possible in this turn.

## Bind native journal preparation to the sampled live financial world

Connected the whole-league capture to the actual native owner's accepted-proposal
preparation path inside the franchise addon. The C wrapper now requires the used
image bytes, checks its version/shape/bounds and hashes them with Windows CNG
before queuing the captured preparation. The service requires a canonical
live_finance_sha256 and compares it with the independently payroll-reconciled
server-owned before-save projection before reserving any journal. Existing
control, save, connection, deadline, league-book and accepted-terms checks remain.
No caller override of captured terms/revision/identity was added. Capture failure
keeps signing held; no retail judgment or precommit permission was implemented.

This comparison describes the sampled cooperative client state. It does not lock
guest mutations, prove all identities/runtime or authorize later application.
The actual transaction still requires those checks and a fresh one-use grant.
The C wrapper signature and service prepare schema must be deployed together;
older digest-free preparation requests are refused. Persisted journal formats,
status/confirmation recovery and independent engine APIs are unchanged. No extra
inference or cloud infrastructure is needed for the comparison or proposal replay.

New service tests reject absent/noncanonical/different projections before journal
creation and check changed-capture retries leave prepared work unchanged. The
Windows native saved-signing fixture now hashes authored image bytes, rejects
missing/truncated images locally and submits an unrelated unrostered contract
change that must be refused by the service before replaying the same accepted
proposal and preparing the correct state. Windows execution is pending CI.
The first full regression run found the extracted observation harness needed
the new financial header; the repaired actual-source observer test passes.

Final local validation: all799 regressions pass26.027s, the three portable native
CTests pass1.06s, the actual addon28-case financial comparison passes and the
5050-case money conservation audit passes. The installed runtime and user saves
are unchanged; this source is not a new playable delivery. Windows SHA256/client
execution and new CI remain to verify after push.

Source6df0c0f passed Franchise38730370139 on Windows2022/Ubuntu, including all799
regressions and the Windows CNG/native-client fixture's changed unrostered
contract rejection, captured proposal replay, matching financial preparation,
saved-candidate confirmation, exactly-once settlement and AI-disabled restart
status. Both actual-addon28-case comparisons and native boundary/interpreter
checks passed. Build38730370102 also passed Windows/Linux runtime/tool and native
presentation checks. No game binary was installed, guest write permitted or
actual application/save/reload verified; those final requirements remain open.

## Check every bound live roster identity before journal preparation

Financially identical player banks can still contain different identities, while
the existing observed biography protects only the selected candidate. Added an
application-private identity snapshot covering all rostered/free-agent bank
slots, their raw PBP/photo and DOB-region fields, and bounded UTF-16 first/last
names in slot order. Native relocated pointers and roster ordering are excluded.
The reader supports valid surrogate pairs and rejects malformed/unbounded names,
rechecks each record's identity/pointers and the bank header, and allocates the
expanded-bank buffer on the heap. Unrostered biographies have no bound actor;
their contracts remain covered by the existing financial image.

The actual addon owner now supplies both sampled images to preparation. The
C client hashes both through the existing Windows CNG API, and the service
requires both to match server-owned before-save projections before reserving
the journal. Only the hashes cross this protocol; no names, hidden ratings or
new inference are added to model requests. Terms/revision/bindings/book/control
checks and persisted journals/recovery remain unchanged. Older preparation
requests missing either digest are refused. Generic addon ABI2 and engine-sidecar
process transport are unchanged; this is franchise application code.

These comparisons do not prove active franchise namespace, runtime image or
guest quiescence, and cannot authorize a later transaction. No apply permit,
retail output-score replacement, installation or guest write was added. Identity
migration and complete opening obligations remain required where unsupported.

Validation: all805 Python regressions passed27.549s; three portable CTests
passed0.95s. The actual addon callback passes25 identity comparison cases across
relocated pointers, expanded5198-slot banks, reordered membership, unselected
biography/name changes, valid Unicode, truncation and malformed names/pointers.
The same25 pass AddressSanitizer/UndefinedBehaviorSanitizer; all28 existing native
financial cases still pass. Service tests prove identity mismatch is rejected
despite identical finances, missing/malformed fields cannot prepare work and
bad retries preserve existing prepared state. Windows CNG/client execution,
including unselected-identity rejection before matching preparation, is pending.

The pinned MyNFL1 save still has SHA256
4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3.
Read-only identity projection covers2619 bank slots/2070 bound members with436782
bytes and SHA256 a0dd8621024e0dffdc13282c27adddf085769ea308004a369b387eb8dbcc0386.
The source save remained unchanged. This is saved-only evidence, not a live
comparison, complete opening-book import or game application/save/reload result.

Source2fbc3cf passed Franchise38738527171 on Windows2022/Ubuntu, including all805
regressions, both25-case actual native identity comparisons, both28-case financial
comparisons, native boundaries and interpreter checks. The Windows CNG/native
client/service fixture refused an unselected player's changed identity, replayed
the captured proposal and prepared/settled matching authored saved effects with
AI-disabled restart recovery. Build38738527281 also passed Windows/Linux runtime,
tool and presentation checks. The CI watchers temporarily lost GitHub connectivity;
direct reinspection of the same runs confirmed both completed successfully.
A fresh read-only Deck SSH attempt still failed steamdeck.local DNS resolution.
No installation, private game execution, guest application, save/reload proof,
paid inference or remote-control renewal occurred. The goal remains incomplete.

## Restrict addon reads to an uninterrupted guest CPU ownership span

Source audit found that GGL serializes translated guest execution, but neither
the addon API nor its old host read capability established current ownership.
Added a nonblocking runtime query returning a non-reused acquisition serial only
to the enabled lock's current owner. Recursion preserves it; a full release or
blocking yield invalidates it, including immediate reacquisition by the same
thread. Serial exhaustion returns unavailable rather than reusing an identity.
The query neither initializes, acquires nor pins the lock.

The loader brackets start/stop/poll/event/snapshot callbacks with a thread-local
read scope. The host memory-read capability refuses calls outside that scope or
after its serial changes. Nested calls cannot revive an unowned/stale outer
scope; range queries remain read-free and unchanged. ABI2 and the callback table
are preserved. Actual franchise preparation captures both financial and identity
images in the same poll scope. A compatible rebuilt host is required; older
hosts do not gain this behavior from a DLL-only update.

This is guest-CPU read consistency, not global DMA/host-writer exclusion, runtime
authentication, a lock pin or an application permit. Kernel and blocking
boundaries can release GGL; entry ownership alone cannot establish an atomic
original signing commit. No transaction was released or guest write added.

The new authored fixture compiles the real runtime GGL and platform primitives.
Enabled/disabled CTests pass locally, including recursive ownership, a competing
thread that cannot inherit ownership, release/reacquire and blocking-yield
invalidation (0.34s). All805 Python regressions pass25.857s, including the actual
observer/read function with an unavailable-scope sentinel check. A Windows DLL
fixture now checks owned/unowned invocation reads and a changed serial between
two reads; Windows execution is pending. CI fetches the pinned runtime explicitly
for the new portable lock tests. No installed game, save, remote control or paid
model request changed. Live execution/application/save/reload remain unverified.

The runtime query is committed/pushed as4359426 to cosmokay1/xboxrecomp on
codex/platform-build-fixes, and the consumer pins that exact dependency. The
serial is unique within the process, not a cross-process identity. Full source
Windows/Linux CI and actual DLL read-scope execution were pending after push.

## Guest-read ownership CI verified and newest upstream filesystem integration

Source2cd98d4 passed Franchise38748479653 on Windows2022 and Ubuntu, including
the actual runtime lock tests, DLL-owned/unowned/stale-scope reads, financial and
identity capture and the saved-signing fixture. Build38748479778 also passed
Windows/Linux runtime/tool and native presentation checks. This verifies component
execution; no guest application permit or actual game signing/save/reload follows.

At the user's request, fetched repack master86198cf, builds991cd02 and main9a46626,
plus the runtime's game-specific branch8fcec41. Master's latest merge explicitly
imports and attributes our Linux/POSIX prerequisites; its Windows/Linux build
checks38677062168 pass with NFL2K5_BUILD_GAME=OFF. Latest public repack release
remains v0.6.1-hotfix (portable mod packs). The game runtime has three newer
filesystem commits not pinned by master: aa0e8b3,9603907,8fcec41.

Imported those three commits with cherry-pick attribution into our runtime branch
as96842da,d02d271,8e127f3. Resolved the GGL conflict by retaining our real portable
lock and ownership-serial implementation; upstream's POSIX no-op stub is not
adopted. The existing game-thread global already exists in our implementation.
Follow-upc867ad3 guards the upstream strings.h include from Windows builds. No
other runtime default-branch changes or generic compiler releases were imported.
The consumer submodule and revision manifest now pin c867ad3 exactly.

The new tests/runtime_paths_posix fixture compiles the actual kernel_path.c and
uses authored files on a case-sensitive Linux container filesystem. Case lookup,
missing final filename preservation, all three added-team path forms, user-save
translation, partition table magic, cache image geometry and persistence across
reinitialization, one-time settings migration without overwrite, nested profile
directories and portable paths pass. Symbolic-link table lookup and logging are
explicit fixture stubs; the fixture does not claim their kernel integration.
The existing offline node:20 image ran with networking disabled and source
read-only; no assets, packages or cloud services were downloaded. Actual GGL
enabled/disabled checks also pass on Linux and macOS after the import. Hosted
Windows/Linux runtime verification is pending and is required before deployment.

The imported POSIX overlay loader explicitly returns0: mod-pack disc overlays
remain unimplemented. These filesystem changes address native Linux prerequisites,
not a verified Proton-free SOFTDRINK build. No installed executable, user save,
AI control or paid inference changed. Core native signing/application, complete
opening obligations, actual game execution and save/reload remain open.

## Imported-runtime CI and isolated Windows game build verified

Source05ac4e9 passed Build38750533958 on Windows/Linux and
Franchise38750534000 on Windows2022/Ubuntu. Linux's new runtime filesystem
CTest passed in the hosted build. These suites exclude full-game execution.

The Deck became reachable and no NFL2K5/service process was present. Prepared
private stage native-05ac4e9 from a copy of the existing private source/build
snapshot, then verified all1227 transferred tracked-source hashes (110 source
files changed). Runtimec867ad3 preserves our real guest-lock implementation.
The already accepted private MSVC toolchain built the actual Windows NFL2K5.exe
and franchise-addon.dll successfully, with retained original build options.
The persistent SSH build handle completed with exit0. Nothing was installed over
the user's game. The build's existing renderer warnings remain; compilation alone
does not establish rendering or runtime correctness.

Executed the newly built Windows addon boundary fixture under actual Deck Proton.
Launcher exit0 plus child completion addon-passed and the expected success output
verify ABI/refusal/forwarding/reload and the owned/unowned/stale read-scope checks.
The intentional missing-DLL case logs load error126; the fixture completed.
New DLL SHA2565b3248d5c4955a4df198dd2db94a09b0cb6b05e114eab3847b4ba171244d6708.
Private receipt: native-05ac4e9/addon-boundary-receipt.json. Isolated copies of the
runtime and Proton profile finished, but the subsequent SSH connection timed out
before game validation could start. A separate read-only check also timed out;
this is an external connection gate, not evidence of a game crash. Do not install
or relaunch blindly; recheck the Deck and process state first.

Further bounded signing-source inspection found that the optional post-contract
warning call at0x00323FC7 routes via0x0014E520/0x0014E440/0x0014E070 into UI
callbacks with indirect dispatch. Checking guest-lock ownership at precommit
cannot by itself prove that the original routine will remain uninterrupted.
The direct helper closures excluding this UI branch are small, but generated
retail source inspection is not proof of the active SOFTDRINK interpreter path.
No application permit, guest write, AI grant or paid inference was introduced.

User asked specifically about Deck packaging. The current explicit-manifest ZIP
tool and previously working Gaming Mode shortcut are component evidence, not a
verified reusable installation/update package. Launcher bundling, removal of
private build-folder assumptions and fresh package/save-preservation validation
remain part of final delivery. Windows/Proton remains the current delivery path;
the incomplete native Linux port does not replace it.

## Deck packaging scope correction: no custom launcher

The user explicitly rejected a custom launcher as overkill. No launcher code was
added. Retain the simple explicit-manifest ZIP and normal Steam non-Steam EXE
shortcut with a selected Proton compatibility tool. The earlier launcher-bundling
plan is superseded. Ship the matching game/addon/dependencies and concise setup
instructions with relative runtime paths; verify fresh extraction, Gaming Mode
controls and save preservation through that normal Steam flow. A custom launcher
or automated Steam-library editor is not a delivery requirement.

## Read-only live reconciliation capture and confirmed private validation

Windows + Proton remains the Deck delivery priority after the user questioned
the value of the native port. Further native Linux port work is deferred; retain
the already validated portability fixes. No custom launcher is being built.

Added opt-in NFL2K5_FRANCHISE_CAPTURE to the franchise addon, using the existing
offer-screen event and existing financial/identity readers. It performs no reads
or output by default. With an absolute new filename, it captures both projections
inside the host invocation and exclusively creates one bounded diagnostic file.
Existing files survive, malformed memory produces no capture, and no provider,
inference or transaction is involved. The standalone comparison tool derives
expected projections from the save and rejects truncated/oversized/inconsistent
images. This is not an active-franchise identity or application authorization.

Actual adapter/fixture execution passes31 financial/capture and25 identity cases
on macOS and offline Linux. All807 Python regressions pass60.356s. The initial
sandbox run exposed an observer-fixture environment assertion, now updated to
explicitly leave capture disabled, and four existing loopback socket permission
errors; the full rerun outside the sandbox passes. Standalone native CMake's
unconditional JSON download was unavailable in the sandbox, so these C boundary
fixtures were compiled directly from the same actual source files. Hosted
Windows/Ubuntu execution of the new capture remains pending.

The user opened the installed game, which was confirmed running through the
existing Gaming Mode Steam entry, then closed it. No executable was replaced.
Once closed, isolated source05ac4e9 Windows validation ran against the legal pinned
SOFTDRINK XBE f67e6fc1cb76c9ea1f1ad504e4a6491ff126483d66a9da8ddb92950bbaf740ba.
The first runner's launcher-only exit lacked child evidence; its corrected
Windows cmd invocation supplies both a child completion marker and actual
[TEST] Validation passed output, exit0 and memory-layout shutdown. Logs show
128MB guest RAM,186/186 bridged thunks, the selected portable SOFTDRINK pack and
recompiled entry readiness. This validation mode does not execute gameplay.
It reports two failed RAM mirrors and a failed tiled aperture with a rendering
fault warning, so rendering must be checked before installing this pair.

Private source05ac4e9 EXE SHA256
222d0b123b064111a62c47d95157ba3e54b065bc1bfd8618133b2ea0e5fe42a7;
DLL5b3248d5c4955a4df198dd2db94a09b0cb6b05e114eab3847b4ba171244d6708.
Receipt: native-05ac4e9/validate-receipt.json on the Deck. The new capture feature
is not in that staged pair and has not been installed. Actual capture, contract
application, full opening accounting and signing/save/reload remain open. No AI
control was renewed or enabled, and no paid inference occurred.

### Isolated SOFTDRINK guest execution after validation

The source05ac4e9 pair also entered actual recompiled guest execution under Deck
Proton in its isolated runtime/profile. The boot log reports D3D11 readiness,
1200 GPU frames/1197 draws, ongoing vblank,1478 audio submissions with zero
reported dropped/underrun submissions, and later60FPS samples. These are runtime
activity counters, not a visual, frame-pacing or gameplay acceptance test.
The tiled-aperture warning remains and must not be dismissed from these counters.

Spectacle screenshot capture timed out, so the unattended boot runner did not
reach its automatic cleanup. A subsequent window-close request targeted the owned
test game PID136118; process inspection confirmed no remaining game or screenshot
process. No clean-exit marker was recorded, so orderly game shutdown is not
proven. The private runner now handles screenshot timeout before cleanup for a
future run. No franchise was opened or saved, no installed files were replaced,
and no image/screenshot or playable-delivery claim follows.

Private boot.log, validate-receipt.json and addon-boundary-receipt.json are copied
to .local-runtime/native-05ac4e9 for continuity. New capture source6291411 passed
Build38754170971 on Windows/Linux and its Ubuntu Franchise38754170960 job.
The same run's Windows job remains active in Python regressions; native Windows
capture execution is not yet verified. Do not deploy the new capture DLL based
on the older source05ac4e9 component/game evidence.

## One focused upstream fix PR and installed read-only capture pair

The user explicitly authorized sending genuine original-runtime fixes upstream
as small PRs without overwhelming the maintainer. Checked both upstream repos:
no open overlapping PRs. Runtime nfl2k5-port8fcec41 still included POSIX strings.h
unconditionally. In an isolated branch based on that exact upstream revision,
cherry-picked only the existing two-line !_WIN32 include guard with attribution.
Actual private MSVC19.44/SDK10.0.26100 compilation reproduced baseline fatal
C1083 for strings.h; the same file compiled successfully with the guard. Opened
https://github.com/BeyondTomrrow/xboxrecomp/pull/1 targeting nfl2k5-port, one file,
two additions, no deletions. Attached the PR to this task. No other PR, maintainer
message, AI/franchise code or assets were submitted. Keep future genuine fixes
similarly focused; check merged work and avoid overlapping submissions.

Source6291411 passed hosted Windows/Ubuntu Franchise38754170960 and
Build38754170971. The private Deck Windows toolchain rebuilt the actual capture
DLL and financial C fixture from verified source overlayd1ce378. Windows Python
3.13.16 under Proton executed31 financial/capture and25 identity cases, including
exclusive creation/no overwrite and malformed-memory refusal, with exit0 plus
the explicit child capture-passed marker. No model/provider was configured.
DLL SHA2561c3d51ecb8eeb7a1fbef281effa9d647654c4ef1b6115be981abf045008445f9.

Confirmed the game was stopped, then backed up the installed EXE/DLL/private
launch entry before replacing only that pair and adding the temporary read-only
capture environment setting to the existing private test entry. No new launcher
was introduced; final packaging remains normal Steam EXE/Proton. Installed host
source05ac4e9 SHA256222d0b123b064111a62c47d95157ba3e54b065bc1bfd8618133b2ea0e5fe42a7,
and addon source6291411 uses the DLL hash above. Installed entry SHA256
09e60e9eeea2d1a527031e067ea96e9044a2b9e68d790f81c7f1154022bd47b1.
All16 SAVEGAME.DAT hashes are unchanged, including MyNFL1 and its UDATA copy:
4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3.
Rollback files are under native-05ac4e9/installed-backup-6291411; private receipts
are installed-capture-receipt.json and capture-windows-receipt.json, copied locally.

The existing Steam test entry is configured to capture once to the new absolute
private path native-05ac4e9/live-mynfl1.dat. The user was asked to load MyNFL1 and
open any player's offer without submitting, reporting any picture problem.
Actual installed module loading, visual correctness and live/save equality are
pending. Once captured, remove only the owned temporary capture setting from the
private entry; do not overwrite unrelated edits or renew AI controls. Negotiation
mode/provider remain off. Actual legal signing, full opening obligations and
save/reload integration remain unfinished.

### Installed game retry and actual module loading

The user reported a startup crash after installation, then explicitly reported
that the second launch worked. Read-only inspection confirms running game
PID137707 through the original Steam test entry and the new franchise-addon.dll
mapped from the installed addon folder. The capture environment contains the
intended new private filename; the AI provider is absent. Current session logs
show ongoing D3D11 rendering, controller input, franchise/player-table activity,
60FPS samples and zero reported audio drops/underruns. This proves actual module
mapping and continued guest execution, not complete rendering/gameplay acceptance.

The current Wine/Steam launcher log has no exception record explaining the first
failure. The per-user session log belongs to the successful retry; the earlier
failure remains unresolved and is not dismissed because retry worked. No rollback
or further runtime changes were made after the user's successful-retry report.
The live capture is still absent; the user was asked to load MyNFL1 and open an
offer without submitting. Do not infer successful capture from merely loading a
franchise/player table. Preserve the running game and wait for the actual file or
the user's screen confirmation before diagnosing missing offer-screen capture.


### Pending offers preserve retail negotiation attempts

Found a concrete caller-level integration bug: our shared signing hold returns
EAX0 through the original refusal epilogue, but interactive caller003478A0 treats
that as rejection, increments context+9 (capped at7), and can pop the offer screen.
The host shim now records a thread-local held context for that synchronous return.
The compiled caller patch and interpreter return hook consume it once and jump to
003478F0, preserving the original UI dirty flag and stack/callee-save cleanup
without changing attempts or closing the screen. Entry resets stale state in
both paths. Wrong-context consumption clears it; ordinary refusal/acceptance and
missing-addon controlled holds retain their existing policy. No addon ABI change,
financial writes, application permit or AI activation was introduced.

Validation: actual host shim checks repeated holds, consumed/wrong-context tokens,
entry reset, later retail decisions, legacy fallback, explicit controlled mode
with no event handler and shutdown reset. Five focused Python patch tests pass,
including compiling/executing the production patch plus actual shim against an
authored caller:12 waits preserve attempts, real refusals increment/clamp and
acceptance resets. A private local probe executes the actual generated003478A0
body with the new production patch and authored shared-signing/UI callees:
12 holds preserve attempts and screen, two original refusals increment attempts,
and acceptance retains the original callbacks; every return preserves ESI/ESP
and sets the UI dirty flag. The probe uses authored memory, runs on macOS, and
is not actual game execution. Its generated code stays private/untracked.
Windows CI and actual opt-in game execution remain to verify. The running Deck
was not interrupted or replaced; the initial startup failure remains unexplained.


### CPU settlement holds before free-agent removal

Inspection of the actual retail CPU caller00324060 shows that00324088 removes
the selected free agent (via002425C0) before invoking shared signing00323D80.
An EAX0 return then changes the offer status and clears its pending record.
Holding only in shared signing therefore was too late for this caller. The new
compiled patch and interpreter hook use the existing PRECOMMIT policy at00324088
and skip to the next offer at00324169 when held, before either change. They clear
the synchronous interactive hold marker since this path does not return to the
interactive caller. No interactive intent, model request or acceptance is created.
The original path remains intact when controlled policy does not hold.

The private pinned SOFTDRINK v0.6 executable disassembles00324088 as the expected
player lookup followed by the original removal call;00324169 is its original
loop continuation and stack cleanup. This checks the hook addresses against the
actual pack, without distributing executable bytes or changing installed files.
The same check confirms both interactive return/cleanup addresses from1fdf388.

Validation: six focused patch tests pass, including the actual host shim plus
production CPU patch over1200 authored pending records and ordinary no-hold
fallback. All68 signing-focused Python tests pass locally. A private probe runs
the actual generated00324060 body with authored bank/offer data and aborting
stubs for list removal/shared signing:12 complete100-record passes preserve the
pending offer, EBX/ESI/EDI/EBP and ESP, never reach those mutation callees, and
leave no interactive hold token. This is isolated generated-code execution on
macOS, not actual game/CPU/save acceptance; generated code stays untracked.

The earlier1fdf388 Ubuntu engine job passed; Windows Franchise38760686708 failed
one new test because its child environment omitted PATH, causing the MinGW-built
fixture to fail loader startup with0xC0000135. The test now preserves the inherited
environment and only overrides negotiation mode; local regression checks pass.
Windows/Ubuntu rerun remains required. The Deck currently does not resolve over
SSH, so no runtime installation, capture or save change was attempted.


### Windows fixture loader repaired; isolate an existing deadline-sensitive check

Atbb339a8 the new CPU/interactive compiled fixtures both pass on the actual
Windows runner, confirming the inherited-environment fix. Ubuntu's full engine
job passed. Windows Franchise38761382737 reached809 tests with808 passing;
its one failure was an existing unrepresentable-offer test returning timeout
instead of invalid_request after its one-second real-clock budget expired.
That test now fixes monotonic time while testing format rejection; separate
bridge deadline tests retain an advancing clock. Production timeouts are
unchanged. Local proposal, bridge and signing-patch regressions pass. Full
Windows native checks still require a successful rerun; no green claim is made.

The user reported the Deck ready; SSH now connects and confirms the same running
PID137707. Its capture path remains configured and the capture file is absent.
The user was asked to confirm a MyNFL1 offer screen without submitting. No game,
addon, save or launcher replacement was made while the session was running.


### SOFTDRINK interpreted FSM observation gap

The user confirms a MyNFL1 offer screen is open, while the configured live
capture is absent. Comparing legally supplied retail and pinned SOFTDRINK v0.6
images shows that FSM push0006E390 is detoured in the pack, so the generated
DIAG_FSMPUSH callback never executes. The offer descriptor00557B2C and original
push checkpoint0006E3E6 are unchanged. The pack detour rejoins the original
routine at0006E39A; its descriptor mapper only substitutes two other screen
identifiers, preserving the contract-offer descriptor. FSM pop is unchanged.

Added interpreter observation callbacks at the same push/pop checkpoints, before
the negotiation-mode check, because read-only context/capture must work with AI
off. The existing main call installs them only for the pinned v0.6 pack hash.
Transaction gates remain opt-in. An asset-free test compiles the actual owned
hook block and verifies disabled negotiation installs just the observation hooks,
with exact object/descriptor/push values, unchanged registers and no guest jump;
enabled mode adds the existing signing gates. Local test passes. Actual Windows
build and new installed menu event/capture remain to verify; the running game
has not been interrupted or changed.


### Interpreter menu fix: private Windows build and preflight passed

Source268e8d8 compiled the actual Windows game, updated generated signing callers
and franchise DLL using the existing licensed MSVC offline container. The source
stage retains baseline05ac4e9 plus prior6291411 capture overlay and the exact new
source manifest; no retail/mod assets are published. New EXE SHA256
eefe906af888deab73270b056accc050bea50061f2f7fbfd85c2800a52f3f5c9;
DLL SHA2568b9bfb63052ae8294a746f807be4ad9d5cdb8570db65dacc1fada07ef6e2b32a.

Actual isolated Proton game --validate exited0, wrote its child completion marker
and logged[TEST] Validation passed. The separate actual Windows addon boundary
fixture exited0 with addon-passed and ABI/forwarding/disabled-service/reload
checks passed, including ownership read-scope checks. Receipts are private local
and Deck native-05ac4e9/validate-menu-hooks-receipt.json and
addon-boundary-menu-hooks-receipt.json. These are preflights, not actual restored
menu/capture/signing/save verification. Sourcea969b53 passed both complete CI
workflows38762188708/38762188772, including the corrected Windows format test;
268e8d8 Build38762515073 passed, Franchise38762514947 is still running.

The user was asked to exit normally without submitting so the staged pair can be
installed safely. A guarded private installer preserves saves/launcher, validates
source/binary receipt hashes, requires the old installed hashes and no running
game, and saves rollback files. It has not run; no installed files have changed.
AI/provider and controlled signing remain off; no controls have been renewed.


### Interpreter menu fix installed after normal exit

The user reports Closed; the guarded installer independently verified no running
NFL2K5.exe and matched the expected previous installed hashes before replacing
only EXE/DLL. It verified the staged source manifest and both Windows receipts.
Installed hashes are eefe906af888deab73270b056accc050bea50061f2f7fbfd85c2800a52f3f5c9
and8b9bfb63052ae8294a746f807be4ad9d5cdb8570db65dacc1fada07ef6e2b32a.
All16 save hashes are unchanged, as is the existing private launch entry
09e60e9eeea2d1a527031e067ea96e9044a2b9e68d790f81c7f1154022bd47b1.
Rollback pair is under native-05ac4e9/installed-backup-268e8d8; receipt
installed-menu-hooks-receipt.json is copied locally. AI and controlled signing
remain off. The user was asked to launch the same Steam entry, load MyNFL1 and
open a contract offer without submitting. Actual post-install callback/capture,
visual behavior and game/save comparison remain unverified.


Source268e8d8 now passed the full Windows/Ubuntu Franchise38762514947 suite and
Build38762515073. This includes the new compiled actual-hook registration test,
CPU/interactive pending-return fixtures, native DLL/pipe/restart/financial
checks and existing interpreter fixtures. These checks do not establish actual
post-install menu behavior. The latest read-only Deck check finds no running
NFL2K5.exe and no live capture yet; launch/offer confirmation is still pending.


### Actual SOFTDRINK offer capture and transient free-agent reconciliation

The user says Look now; the new game session PID139951 maps the installed
franchise addon and logs live_capture=written. Installed EXE/DLL hashes remain
eefe906a...f5c9 /8b9bfb63...b32a as recorded above; provider and controlled-signing
environment settings are absent. The465828-byte private capture SHA256 is
8e6e09ad1d5918737cbd4446afcf24222cd4897a503d352367dfe43cace99d9b.
Both current MyNFL1/UDATA save hashes still equal
4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3.

Strict full projections differ, and inspection identifies the entire difference:
slot2371 (saved free agent Will Hernandez) has become unlisted in the live pool
while the offer is open. Identity membership2070->2069 omits exactly that slot;
all remaining biographies match. All2619 contract/flag records, all32 club
financial rows and the entire cap/calendar header match byte-for-byte. This
explains the private shared-signing probe's earlier apparent duplicate/absent
free-agent issue: caller/menu membership must be accounted for separately from
the shared routine. It is not proof of a full applied/saved transaction.

Added an explicit read-only pending-offer expected projection, retaining strict
comparison by default. The actual capture matches both projections exactly for
that scope: finance172254b69b1405e45b9aa60ce36001bd93eea653ec53d7c88da0e16f36870352,
identity1bd8efb558a7301e8519ee7177c8ac312b53e6e9fd238747e8b43378e553e491.
The excluded selected biography still needs its current native observation and
future commit validation; this member-only capture does not establish it.

Journal preparation now checks the live pair inside its transaction after
resolving the durable accepted player. It accepts exact full or exact selected
pending-free-agent pairs only, derives the candidate from accepted player/pinned
bindings, and rechecks retries. Clients cannot specify an omitted-player slot.
Every other contract, owner, identity, calendar and money field remains compared;
complete opening books, control and financial checks still apply. No native
application, inference, remote renewal or write permission is added. All814
offline Python regressions pass locally in30.797s, including new pending prepare/
restart, cross-pair rejection, other financial/identity mismatch and no-mutation
cases. Windows/Ubuntu CI still needs to run for this source change.

Using the pinned4x profile, actual observed Giants roster-only figures reconcile
as301.2M cap -211.984M payroll =89.216M room. This does not establish complete
modern obligations or service/rookie classification. The user may back out
without submitting; further actual game signing remains blocked on integration.
Private actual-comparison evidence is native-05ac4e9/live-mynfl1-receipt.json;
no capture/save data is committed.

A separate CPU audit found a second automatic offer route from00324060 to
00323B30 that directly removes a free agent and writes ownership/contracts,
bypassing shared00323D80. Moving the existing CPU hold before the loop's dispatch
is still required; no such fix is claimed in this reconciliation change.

After verified collection, removed only the owned two-line temporary capture
setting using an atomic launcher replacement (the executing shell retains its
old inode). No game binary or save was changed; all16 save hashes remain the
same. The launch entry returns to its original SHA256
94f7dccc0a2e74fb693782fe925f6435d22928fcd02040e6d854339769c1c718.
The capture remains intact, and future launches do not try another capture.
Private capture-cleanup-receipt.json records the before/after hashes and backup;
no provider/control settings were enabled or renewed.


### CPU hold covers automatic direct signing as well as shared signing

Moved the existing CPU hold from accepted-record branch00324088 to00324072,
after the dispatcher prologue and before any record lookup/route selection.
A held pass uses the original00324173 epilogue. This prevents the other branch
from reaching automatic judgment and direct contract writer00323B30, while
preserving offers, free agents, contracts and history. No game-facing acceptance
or write permission is granted; controlled mode remains unfinished/off on Deck.
The existing per-record marker has a recognized old-body/location migration;
--check rejects stale caches, application relocates that exact patch only, and
custom bodies, moved current patches or missing anchors fail without overwrites.
CRLF caches retain their line endings. Interpreter registration/continuation use
the same early boundary and the current ABI/event policy.

Ten focused local tests pass: compiled production patch/actual host shim skips
both authored routes while held and preserves normal dispatch when unheld;
the actual owned interpreter callback has the expected stage/context/target,
clears its marker once and leaves the unheld path alone; old cache relocation,
idempotence, failure preservation and CRLF behavior pass. A private probe also
executes the actual generated00324060 body with authored memory:12 held passes
perform no record lookup, while an unheld pass visits100 inactive records. All
passes preserve EBX/ESI/EDI/EBP and exact ESP; mutation callees abort if reached
unexpectedly. Generated game code stays private/untracked. This is isolated
macOS generated-code execution, not actual game/CPU/save verification. Windows
CI and a private full Windows build remain to verify for the new source.


The CPU-pass source160c53d also compiled the actual private Windows game in the
existing offline licensed toolchain. Its isolated Proton --validate child exited0
with the validated marker and[TEST] Validation passed. Private receipt is
native-05ac4e9/validate-cpu-pass-receipt.json. This is staged validation only; the
installed game remains268e8d8, with AI/controlled signing off. Full source160c53d
CI remains in progress (Ubuntu engine and Build checks passed at observation).
The previous transient-free-agent reconciliation sourcefd5758c passed both
complete Windows/Ubuntu workflows38765718208 and38765718212.

The user's requested parallel SOFTDRINK scope audit is complete. The agent
inspected installed recipe flags and pinned creator source; it made no file or
Deck changes. Added the attributed feature inventory and primary links to
docs/SOFTDRINK_AI_BASE.md. Creator source independently confirms logical2026,
4:1 money and301.2M cap; draft/FA decisions still consume ratings. Accelerated
clock and decided-game cutoff are separate enabled features. MyNFL is a naming
change; functional changes are broader gameplay/franchise patches. Full modern
roster/IR enforcement is not delivered. The inventory separates intended source/
recipe features from actual runtime evidence and preserves Remade attribution.

### October 15 — Publish initialized personalities and explicit cash scope together

The creation command now accepts an optional all-team cash import beside its
existing source-backed opening ledgers. Each team explicitly supplies records,
source and unavailable legacy cash identities. Existing store reconciliation
checks every known original agreement and the complete preserved legacy unknown
inventory. All cash initialization happens in the unpublished temporary DB;
a later team's reconciliation failure discards the entire artifact, including
earlier imports and generated personalities. Omitted cash retains prior behavior.
The receipt now counts registered legacy/observed players as well as classified
modern players, and reports the number of initialized cash books.

Eight creation tests pass, including mixed modern/legacy/observed identities,
reopened paid/unpaid/unknown cash, deterministic personalities, invalid team
coverage and failure after one successful cash import. All820 Python regressions
pass in30.462s with localhost fixture binding allowed; the sandbox-only attempt
failed four existing HTTP/TLS tests because socket binding was prohibited.
The money audit passes5050 bonus-conservation cases. Prior source160c53d full
Windows/Ubuntu Franchise38766311581 is now verified successful (Build38766311589
also succeeded); the new bootstrap source still requires its own CI.

A private full MyNFL1 bootstrap exercised this exact command, then reopened every
team independently:32 teams,2070 unique bound identities,66240 saved player/team
personality records,1693 preserved legacy deals. Every actor matches its saved
seed-derived fictional initialization across teams/restart; all32 roster payrolls
reconcile at the pinned4:1 scale. Cash totals remain null for the explicit legacy
unknown inventory. Unclassified free-agent offers still reject rather than
inventing minimums. Input publication took97.718s; final independent verification
completed in131.425s. Private receipt:
softdrink-v0.6/mynfl1/personality-bootstrap-7n67xew_/receipt.json.
Original save SHA4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3
and bindings SHA9955880d3fb6a02eaebc4c1662cfac075afb59443a1191e709bf2dd51c9ee442
remain unchanged. Source input and DB remain private/untracked.

This is a known-roster offline projection, not complete modern Team Salary:
zero reserve is explicitly a projection convention, missing obligations and
classification remain unresolved. No live DB, installed game, controls, inference
or saves changed. Native creation hookup, positive contract application and
actual game save/reload are still open; no signing authority is claimed.

### October 15 — Honor controlled signing in builds without the client

Tracing the native application boundary found a real fallback inconsistency:
`nfl2k5_franchise_hold_signing` honored an explicit negotiation mode even without
compiled client support, but `hold_signing_at` returned0 in that configuration.
The judgment/precommit patches use the latter, so this could silently execute
retail signing when controlled mode was requested. The no-client branch now
uses the same existing hold function, preserving the single-use context marker.
Normal mode still allows retail behavior. No permit, acceptance, memory write
capability or remote control activation was added.

A new CTest executable compiles the actual adapter without the client define or
addon stubs. It verifies both valid stages, CPU context0, exact single-use token
consumption, mismatched contexts, new-call invalidation, disabled/noncanonical
mode strings and invalid stages. Both this actual no-client fixture and the
existing with-client signing-stage fixture pass locally; the10 focused compiled/
interpreter/patch-cache tests also pass. Windows/Ubuntu CI for this new source is
pending. The installed Deck runtime and its settings remain untouched. Native
positive application and actual signing/save/reload are still incomplete.

### October 15 — Exact native post-signing comparison target

Added a reusable expected final financial/identity image for one bound free-agent
signing. It uses the validated money profile and exact captured/accepted terms,
updates only the native mapped fields and selected owner/payroll, preserves other
packed status bits and clears byte8 bit3. The full identity membership includes
the selected player again. No save or guest memory is written. Saved confirmation
now consumes this target after its existing detailed checks, closing omissions
for raw byte8 and non-economic packed flags across every bank record. Existing
receipts/journal formats are unchanged; no protocol permit is added.

Four additional confirmation tests cover independent authored transitions to two
teams, both money scales, selected/other/unbound flag changes, preserved status
bits, the exact cleared signing flag, wrong candidates/ownership and terms. All14
confirmation tests pass. All824 Python regressions pass in32.125s; final narrowed
candidate test additions also pass. No further money formulas changed.

A private actual-generated-routine probe validates the same target independently
of authored after-save construction. It runs original shared signing323D80 and
its generated callees using authored relocated memory and user-provided local
constants, bypassing retail judgment; unexpected UI/judgment paths abort. Starting
with exactly the selected free agent reserved, the actual production addon reader
captures matching pending-before and final images, including deliberately set
preserved status bits and byte8 bit3 clearing. Guest result1, final finance SHA
94bb53a3311849c97e330dd66ef2159e70bf1c7bcbc0668681deefe8eef8ffce and identity SHA
b675304ccbfa5171a8ed670c328da5118f7f9837df5fbf2030ba532bcdf98ad1.
Private receipt native-commit-probe/target-receipt.json and generated probe/assets
stay untracked. This is isolated generated execution, not live gameplay, modern
opening-book verification, a permit or game save/reload. The installed game,
saves and controls remain unchanged. Positive live application remains open.

### October 15 — Real SOFTDRINK personality context passes Windows service boundary

Prepared a separate read-only MyNFL1 context DB through the atomic creation
command, this time using exactly the personality seed from the pinned bindings
rather than an offline test seed. It contains32 teams,2070 stable IDs and the
explicit unknown cash inventory. This is not a reroll of an active franchise:
no earlier preflight database was connected to this game. Modern opening books
remain incomplete; this known-roster projection cannot authorize signing.

The real saved Will Hernandez checkpoint (slot2371, Giants) passes the service
boundary with expected revision1. Local process preflight completed in5.396s.
The same owned Python source and DB passed actual Windows Python under Proton
on Deck in11.609s total process/check time; the context request itself met its
10000ms service deadline. Required child marker context-passed, not merely Proton
launcher success, was verified. Hello reports ai_disabled, context returns the
persisted personality matching the bindings' seed, offer preview rejects missing
classification, and durable model-attempt count remains0. Deliberately unavailable
ADC prevents provider initialization; no control was renewed or enabled. DB,
save and bindings SHA256s remain exact across the Windows check:
- DB b08a836f26ce65d4d5429d99134cb6610d1f53509b950b14bf5798684a279662
- Save4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3
- Bindings9955880d3fb6a02eaebc4c1662cfac075afb59443a1191e709bf2dd51c9ee442

Private Deck stage: mynfl-context-0639549 under the existing build root. Local
receipts/checks are softdrink-v0.6/mynfl1/context-stage-0639549. The staged launch
configuration points the existing game/addon at this read-only service with
negotiation/journal disabled, no credential source and a bounded unused budget.
It does not replace any executable. Staged wrapper SHA
bd97cbeecfdedb09e332366c0a60c88d27fef492043434ea91091017eb27b07c;
current wrapper remains94f7dccc0a2e74fb693782fe925f6435d22928fcd02040e6d854339769c1c718.
Installer checks clean game/service exit, input/binary/config hashes and all save
hashes before atomic wrapper replacement, retaining an exact rollback copy.
The user was asked to save/exit normally; installation and automatic game-context
verification are pending. Game PID139951 was running at observation and was not
interrupted. Original game signing remains available while negotiation mode is0;
the planned verification must leave offers unsubmitted. No claim of integrated
AI signing, cap correction, game save/reload or native creation is made.

Full CI is now verified successful for de62233 (Franchise38768823911,
Build38768823319),2cc8b55 (Franchise38769190714,Build38769190659) and0639549
(Franchise38769967998,Build38769967912), including Windows and Ubuntu.

### October 15 — Reduce real signing-context replay cost without caching

The saved signing checkpoint now reconstructs its team once instead of four
times, deriving inventory, financial posting and actor/history from one SQLite
read snapshot. Extracted the existing player-context derivation for reuse; its
public API and context formats retain their behavior. No persistent cache or
replay-validation shortcut was introduced. After releasing the read snapshot,
SQLite data_version on the same connection plus the main database file identity/
metadata detect concurrent commits or replacement before returning the context.
This retains freshness rejection rather than returning a coherent but obsolete
snapshot after an intervening write. It still grants no later application lock.

Four new tests verify exactly one validated replay with an identical context and
unchanged database bytes; concurrent WAL budget commits; existing actor edits
without additional events; and replacement by another valid database during the
read. The replacement test runs where the platform permits replacing an open
SQLite file; platforms that prevent it report that case skipped. Existing actor
corruption still fails replay on subsequent inspection. All828 local Python
regressions pass in29.393s, including8 checkpoint tests. Native source was unchanged.

The same real MyNFL1/2070-player read-only service preflight improved from5.396s
to2.324s on Mac. Actual Windows Python under the existing isolated Proton fixture
prefix improved from11.609s to5.853s, with the final file-replacement guard passing
again in5.822s. These measure full process/check time, not an in-game UI latency
benchmark. Both final platform checks return the same stable player/personality,
revision1 and deliberate accounting rejection for missing classification. Source
DB/save/bindings retain their recorded hashes, model attempts remain0, and the
required Windows child marker is context-passed.

Private evidence is softdrink-v0.6/mynfl1/context-stage-0639549 locally and
mynfl-context-0639549 on Deck, including windows-fileguard-driver-receipt.json and
context-receipt-windows-before-fileguard.json. The staged installer now also binds
exact owned service Python/config hashes and refuses if either actual MyNFL1 save
mirror differs from the pinned snapshot. No executable, launcher, active game,
save, control or inference setting was changed. Its pending normal-exit request
is unchanged; do not run old preparation scripts over the updated source manifest.
Actual automatic menu context, native application and game save/reload remain open.
Windows/Ubuntu CI must run for this new source.

### October 15 — Native accepted-judgment branch with separate commit authorization

Implemented the missing judgment replacement at the existing compiled and
interpreter hooks. The domain-specific application event uses the existing addon
transport; no generic ABI, arbitrary memory-write API or new infrastructure was
introduced. Explicit negotiation plus saved-signing modes and exact application
reply2 can select the original judged-result continuation with EAX1. Precommit
requires a second same-context reply2 and consumes the thread-local context
before invoking addon code. Bypass/CPU, stale/mismatched/repeated/invalid grants,
new-call/lifecycle/legacy-hold resets and mode changes cannot reuse it. Existing
v2 replies remain hold-only. Known old judgment caches upgrade; moved or custom
gates fail, preserving user edits and CRLF behavior.

Production DLL deliberately has no application-event handler and still grants
nothing. It needs a verified remote/durable permit issuer, current complete
books and identities, active runtime/franchise binding and an uninterrupted
mutation plan. In particular the previously documented post-contract UI path
is unresolved; this patch does not pin or suppress it. No live application mode
was enabled or deployed. The pending read-only launch configuration remains for
the already installed game, independently of this new native source.

All831 Python regressions pass in34.015s. Focused checks execute actual owned
interpreter callbacks and production generated patches with the actual host
shim; accepted authored judgments skip retail scoring but retain the commit/
history branch, missing commit grants hold, and disabled mode preserves retail
accept/reject behavior. Actual no-client, legacy-stage and new two-stage native
fixtures pass locally. Added the two-stage fixture to Windows/Ubuntu CTest and a
current-production-DLL refusal check; new Windows CI/build execution is pending.

Private native-application-probe/target-receipt.json executes43 actual generated
functions plus the actual shim, with authored two-stage addon grants and original
interactive bypass argument0. Retail judgment and unexpected UI paths abort if
reached. The original signing returns1 with expected stack/output, exactly one
judgment/commit grant, and the same target finance SHA
94bb53a3311849c97e330dd66ef2159e70bf1c7bcbc0668681deefe8eef8ffce and identity SHA
b675304ccbfa5171a8ed670c328da5118f7f9837df5fbf2030ba532bcdf98ad1. The pending-before
image and preserved status/cleared flag agree as well. Generated source, local
constants and memory images stay private; temporary edits to tracked generated
cache files were removed after the probe, retaining only owned patch tooling.
This is not actual game execution, control authorization, saved signing, modern
book completion or final delivery. No user save, installed binary or control
changed. Next: production authorization/coordinator and actual application/save
verification after the required accounting/runtime conditions are established.

### October 15 — Windows/Proton validation of the native application boundary

Source48c3c55 now passes full Windows/Ubuntu Franchise CI38774595042 and
Build38774595079. This includes the new authored two-stage signing fixture,
production DLL refusal, native pipe/restart and saved-signing recovery checks.
The earlier780e717 Franchise run38772466954 failed downloading the pinned public
JSON header (HTTP error22), before native compilation; its Build38772466790
passed. The superseding48c3c55 full run passed that dependency step and all
checks, including the unchanged one-snapshot context regressions.

The Deck is reachable again. An initial detached compiler launch exited before
creating a container or writing build output; process/container checks confirmed
that state before starting an attached build. The existing offline licensed
compiler container then completed the full Windows game and fixture build at
parallel2. An exact nine-file owned-source hash manifest binds the48c3c55 overlay
over the existing private05ac4e9/menu/CPU stage; the runtime pin remainsc867ad3.
No retail generated source or assets were committed or distributed.

Actual Windows fixture children under the separate Proton fixture profile pass:
application judgments/commits with authored grants, and production addon ABI/
forwarding/disabled-service/refusal/reload checks. Both require launcher exit0
and child marker addon-passed. The full isolated game --validate child also
returns0, writes validated and logs [TEST] Validation passed with the pinned
SOFTDRINK v0.6 executable. Game EXE SHA256
d8adeac4afb1c32b4ca7d872d1c0d4ff78528b587de223c68ab5ad93372eb63a; DLL
aef85952323ef1989a185a712db2519c701d392042a8704e24a544873f5262a0.
Private receipts: native-05ac4e9/validate-application-receipt.json,
addon-boundary-application-receipt.json and signing-application-receipt.json.

This validation initializes the pack/runtime; it does not execute gameplay,
signing or save/reload. It retains the earlier isolated-validation mirror/tiled-
aperture mapping warnings and does not prove rendering. The installed Steam
runtime was not replaced; its existing game process was observed still running.
The read-only context launch configuration remains staged, awaiting normal exit
before its guarded installation. No application grants, control renewal or paid
inference were enabled. Native application policy, complete opening obligations,
actual automatic menu context and legal signing/save/recovery remain unfinished.

### October 15 — Notify the addon after original signing completes

Added the missing success-side callback at0032404E, after the original contract,
roster/payroll and history operations and before its register-restoring epilogue.
The generated patch and interpreter hook share the thin shim. An authorized
precommit arms a same-context thread-local notification, consumed before addon
invocation. Duplicate, reentrant, mismatched, failed and retail commits do not
produce another completion. Call/judgment/hold/lifecycle resets discard stale
state. Disabling control after the committed writes still permits reporting
completion for recovery; ignored callback replies cannot authorize further work.
No generic addon ABI change, new toggle, guest-write API or cloud work was added.

The private event franchise.sign-completed.v1 currently has no production
consumer; the production addon still grants no applications. Its future consumer
must compare live final state to the prepared target and separately verify
save/reload before ledger settlement. The optional post-contract UI yielding
path is still unresolved. Reporting original success does not prove an
uninterrupted transaction, financial legality or saved signing.

Focused authored generated-code tests execute the actual patches/shim, require
completion after history and reject moved/customized completion markers without
overwriting them. Actual interpreter callback tests preserve registers and the
original continuation. The native boundary fixture covers single-use/reentrant
reporting, failed/wrong/stale grants, lifecycle reset and disable-after-write.
No-client fallback remains held. The pinned legal local v0.6 XBE has exactly the
expected15-byte success epilogue at0032404E.

The isolated actual-generated43-function probe also emits exactly one completion
with authored judgment/precommit grants, returns1 and retains the exact expected
finance/identity target hashes94bb53a3...8ffce and b675304c...ad1. Retail
judgment/UI abort stubs remain unreached. Private evidence stays in
native-application-probe/target-receipt.json; temporary tracked generated-cache
edits were restored byte-for-byte. This is not actual game/save execution.
All831 final local regressions pass in62.227s; four loopback tests required
running outside the network-restricted sandbox. New Windows CI and full private
Windows game validation remain to run. No installed game, user save, launch configuration or remote control was changed.

The same7c45a76 source now has a full private offline Windows game build and
actual isolated Proton child validation. The success boundary fixture, production
addon ABI/forwarding/refusal/reload fixture, and game --validate all return0 with
required child markers addon-passed/addon-passed/validated; game output contains
[TEST] Validation passed. Exact owned source hashes are checked before the game
check. EXE SHA256d6098f50f8914773274e9ece2b92669006383dff085aba0ba5c064581a013f8b;
DLL3a74be2363e391b3ce1246b1a0b25daacfdffd8931895c627cfcb41e1dfc56e0.
Private receipts are native-05ac4e9/validate-completion-receipt.json,
addon-boundary-completion-receipt.json and signing-completion-receipt.json,
separately retained from the48c3c55 receipts. The existing isolated validation
mirror/tiled-aperture warnings remain; this is not rendering/gameplay proof.
Installed EXE/DLL/launcher still match eefe906a...f5c9/8b9bfb63...2b32a/
94f7dccc...c718. They were not replaced. The read-only service configuration
still awaits normal confirmed game exit; no AI, control or save changed.

Full Windows/Ubuntu Franchise CI38776861697 and Build38776861856 now pass for
7c45a76, including the native completion boundary, pipe/restart and saved-signing
coordination checks. This supersedes the pending CI statement above. Actual
production application authority, complete opening accounting, uninterrupted
mutation, automatic in-game context and signing/save/reload remain unverified.

### October 15 — Compare completion projections against the durable journal

Extended existing read-only saved-signing status with an optional complete pair
of live financial/identity SHA256s. The service reconstructs the exact expected
native target from the persisted journal's original save, bindings and accepted
terms, returning a boolean live_application_matches independently of save state.
Canonical pair validation and cancellation refusal precede comparison. No new
operation, database schema, application authority, financial mutation or provider
call was introduced. Existing status responses retain their shape when hashes
are absent. Native response validation covers both permitted shapes and rejects
missing/malformed/unsolicited live-match fields and invalid input hashes.

Five added bridge cases cover true live results with an unchanged original save
and AI disabled, independent financial/identity mismatches, incomplete/noncanonical
pairs, cancelled journals and read-only inspection after saved settlement. They
assert unchanged database bytes, financial history and zero provider calls. The
actual separate-process fixture now checks this comparison before saving and
after settlement in a restarted credential-unavailable/AI-disabled service.

All836 local regressions pass in41.723s; focused bridge checks and the actual
compiled native protocol/response fixture pass. Windows/Ubuntu CI is pending for
this source. The game completion callback is not yet wired to submit these
hashes, and reported hashes do not prove fresh guest sampling or uninterrupted
application. No installed runtime, save, configuration, credentials or control
changed. Next is the native completion handoff and comparison consumption,
retaining required saved proof and all unresolved accounting/authority gates.

### October 15 — Native completion handoff and comparison sequencing

Connected the completion event to the franchise owner and existing native saved
journal. Owner callbacks sample both existing read-only projections within the
addon read scope, validate framing and copy immutable hashes without transport
waits. The journal accepts completion only after validated preparation/status.
Repeating identical hashes is harmless; changed data rejects. An older pending
status reply cannot bypass comparison. Live mismatch pauses automatic progress;
a match still needs the saved candidate plus current settlement authorization.
Captured comparison/status remains available after AI disable.

Foreign, unreadable or unbound completion sets an atomic failure observed by the
owner, preserving durable prepared work for explicit recovery. Start/stop reset
it; this is not cancellation of a previously submitted service operation. No
application issuer, guest-write API or new generic addon ABI was introduced.
The future permit issuer still must require the transport owner and uninterrupted
mutation. Production grants remain unavailable; no installed game changed.

The actual native protocol fixture covers immutable/repeated completion, pending
pre-completion status, mandatory comparison, AI-off reads, saved-candidate gating
and mismatched completion stop. Adapter forwarding validates context/size; the
Windows held-host fixture now covers immediate owner sampling, unreadable capture
and foreign-thread refusal. The real Windows client/sidecar fixture is extended
to hash authored final snapshots while an older read is pending, compare before
saving, then independently confirm saved effects and recover disabled. Windows
execution of these updated cases remains pending.

All836 local Python regressions pass in34.678s; the actual compiled native
protocol and adapter boundary pass. Full Windows CI/private execution is next.
Actual application permission, complete books, uninterrupted mutation and real
game signing/save/reload remain unverified. No user save, runtime, launch
configuration, credentials or control was changed.

Source7b536c2 now builds the full Windows game, DLL and updated handoff/client
fixtures with the existing private offline compiler. Actual Windows protocol,
adapter, owner-host/foreign refusal, and C-client/sidecar fixtures pass under the
isolated Proton profile. The client hashes authored completion images while an
older status is pending, obtains a true live comparison with the original save
still present, then separately confirms the saved target, updates the ledger
exactly once and reads recovery after disabled restart. This uses authored files
and offline responses only; it is not game signing. Launcher exit0 plus child
marker handoff-passed and handoff-windows-fixtures-passed are required. Receipt:
native-05ac4e9/handoff-windows-receipt.json;314 owned source hashes are pinned
by handoff-source-manifest.json (SHA256
e4bda8b283befe697df6806a66bdfcbfe972d40d70e2a8ddfa9fe1659dc43263).

The isolated full game --validate also passes with child marker validated and
[TEST] Validation passed, recorded in validate-handoff-receipt.json. EXE SHA256
d1db3a5197dedd32d93606da6fccb8bf29b23066328f7c6558fe4a77b25d2e4b; DLL
a0a560ddd839850acef4581e8e8c7f1c50d37fc7e1dde55d579eaef3de0e8909.
Existing isolated-validation mirror/tiled-aperture warnings remain; this does
not verify rendering or gameplay. The installed Steam runtime was not replaced.

Preceding source6f0e327 passes full Windows/Ubuntu Franchise38778655643 and
Build38778655706. Current7b536c2 Build38779416490 and Ubuntu Franchise pass;
Windows Franchise38779416527 is still running its Python regression step at
observation, not failed. Follow that existing job rather than restarting it.
Live application permits, complete opening books, runtime/franchise binding,
uninterrupted mutation and actual signing/save/reload are still open.

### October 15 — Hold native applications with competing pending work

The original shared signing routine runs pending trade/offer cleanup after
contract writes; when it finds matching work, the later warning popup can enter
a blocking UI loop before roster/payroll/history finish. Added a private read-only
guard at the production application event before either stage can proceed. It
validates the context's selected bank slot, checks all15 active trade rows/six
participant fields and100 inline offer records/status bits, and holds matching,
unreadable or changing data. Context/bank/queues are reread before a clear result.
The guard never grants application, queues a proposal or writes guest memory.
Clear queues still fall through to existing held negotiation; original UI code
is retained. No generic ABI or new environment switch was introduced.

A new CTest executes the actual guard and addon dispatcher with authored memory,
covering every trade participant/row, all offer rows and active states, unrelated/
inactive records, read failures, context/bank/queue changes, relocation and invalid
bank locators. Positive results explicitly grant nothing and submit no inference.
The actual DLL fixture now expects unreadable application state to hold. All six
local native CTests pass; all836 Python regressions pass in59.120s.

Private queue-probe.c executes the actual generated2BAAE0/323060 lookups and
callees against the same guard, agreeing in771 authored cases. No generated
retail source is committed. Local legal retail versus pinned v0.6 comparison
confirms byte-identical code ranges2BAAE0(64),322840(13),322BA0(16),323060(48),
2BB6E0(128); hashes are in native-application-probe/pending-queue-code-receipt.json.
This supports the queue prerequisite of the known warning path; it is not a
full no-yield/mutation-ownership proof or actual game execution. Runtime/pack
binding, complete books, durable current-control permits and actual signing/
save/reload remain open. No installed runtime, save, control or credentials changed.

The preceding7b536c2 source is now fully green in Windows/Ubuntu
Franchise38779416527 and Build38779416490. This supersedes its earlier pending
status. New Windows CI and actual private Windows guard execution remain next.

Source7a39913 now also builds the actual Windows pending-work fixture, matching
DLL/host boundary fixture and full game using the private offline compiler. Under
the isolated Proton fixture profile, actual child output verifies pending queue
refusal, no grant on clear queues, and separate DLL load/forward/refusal/reload
checks. Launcher exit0 and marker addon-passed are required; receipt:
native-05ac4e9/pending-boundary-receipt.json. The isolated game --validate also
returns0 with child marker validated and [TEST] Validation passed, recorded in
validate-pending-receipt.json. All318 effective owned source hashes match the
current committed source; layered manifest is pending-effective-source-manifest.json.
EXE SHA256ec6d59595c7e7ef2bd82764c6e90051e2151a5df3ee0758760fb6ec1a58edb83;
DLLf591e83c8c1c8a7e081a9eb88da6271f025223d20b2e10081fdad4d2a750f660.
Existing isolated-validation mirror/tiled-aperture warnings remain. This is not
rendering, live signing, save/reload or permit evidence. Installed EXE/DLL/launcher
still match their previous eefe906a...f5c9/8b9bfb63...2b32a/94f7dccc...c718 hashes.
No installed pair, launch configuration, user save or remote control changed.

Build38781544176 and full Windows/Ubuntu Franchise38781544199 now pass.
The terminal GitHub result supersedes the earlier pending observation.


### October 15 — Pin the two signing checks to guest-lock ownership

The private application shim previously bound judgment/precommit to a thread-local
context pointer without checking whether guest-lock ownership had been released
between callbacks. It now captures the runtime's nonzero acquisition serial and
requires the same serial before/after judgment, before precommit and after its
addon callback. Missing ownership or release/reacquisition holds the attempt;
the captured context is consumed before callbacks and a retry needs a fresh
judgment. Disabled/retail paths and the public addon ABI remain unchanged.

The actual shim fixture covers no owner, changed ownership inside judgment,
release/reacquisition between stages, changed ownership inside precommit,
consumed retries and a fresh successful authored attempt. Six protocol/native
CTests, two actual guest-lock CTests and24 signing patch regressions pass. The
full836-test Python run passed832 with four loopback-binding sandbox errors;
all five web tests then passed outside that restriction. There are no remaining
local test failures. The private actual-generated signing probe still matches
finance94bb53a3311849c97e330dd66ef2159e70bf1c7bcbc0668681deefe8eef8ffce
and identityb675304ccbfa5171a8ed670c328da5118f7f9837df5fbf2030ba532bcdf98ad1,
with one completion; its lock ownership and grants are authored fixtures.

This pins the two permission checks only: it does not retain ownership through
the original-game writes after precommit, issue a durable permit or prove live
game signing/save/reload. Production grants remain unavailable. The Deck game
was still running at observation; no installed binaries/configuration, saves,
AI control or credentials changed. Windows CI for this source is pending.


Static follow-up compared all43 full generated extents used by the private signing
probe to both legally local XBE files. Thirty-six are identical; seven differ,
including five entry detours, a mask change and a redirected helper call in shared
signing. The private callgraph-code/instruction-changes receipts identify them;
no retail generated source or executable bytes are committed. This changes the
next integration check: the existing authored generated-body result cannot prove
SOFTDRINK's interpreted detours. Those routes must run with the production hooks
and match the expected targets before relying on them for a live permit.


Source1bf1013 also passes an actual offline MSVC19.44 Windows build and Proton
execution of the authored ownership fixture. The child marker is ownership-passed,
launcher exit0, and all six transferred source hashes match the committed inputs.
Receipt: ownership-1bf1013/windows-receipt.json. Fixture EXE SHA256
 aa7291ce47601e9800d801c425a17e693fe85977d9d4af4e73e64de8e0ced6a9.
No game runtime/profile or user save was replaced. Ubuntu Franchise38783097191
passes; Windows remains live in its Python regression step. Build38783098207 has
passed Linux with Windows still running. Follow those existing handles; neither
full workflow is yet counted as green.


### October 15 — Execute SOFTDRINK's interpreted signing path

Completed the next pack-path validation with private Windows/MSVC19.44 probes,
without changing the installed game. The probe links the actual interpreter,
production signing shim and exact source callbacks copied from recomp_manual.c,
with the seven modified function entries marked dirty. It executes pinned v0.6
bytes from the authored memory fixture, dispatching unchanged generated bodies
natively. Unexpected kernel dispatch and retail judgment/UI abort rather than
silently succeeding. The initial build lacked the interpreter's FPU include;
adding that existing source dependency fixed the private harness build.

The accepted two-year descending40percent bonus offer returns success with
judgment/precommit/completion counts1/1/1. Its finance image29,241bytes is exactly
94bb53a3311849c97e330dd66ef2159e70bf1c7bcbc0668681deefe8eef8ffce and identity645bytes
b675304ccbfa5171a8ed670c328da5118f7f9837df5fbf2030ba532bcdf98ad1, matching the
expected accepted target with zero differing bytes. Denied judgment returns
0 with counts1/0/0; denied precommit returns0 with1/1/0. Both preserve pending-before
finance d19bfc6170c2739c144b2156d319b92ffebb6162f99654d05272bc0c5220ee9f and identity
ba900627476da9ed7d01a21d1f6c97c4c9a48481f8fc13284b510842af3e5798. Both refusal
full-memory outputs also match each other.

Replaced the initial authored lock serial with the actual pinned runtime
c867ad30cccd3eec50c6ff82d468f48067fc2b8b guest lock and a competing native thread.
All three cases still pass, with one unchanged nonzero acquisition serial spanning
the original call, no competing acquisition before leave and successful acquisition
after leave. Each actual Windows child marks interpreted-signing-passed with launcher
exit0; twelve transferred source files match their manifest. Probe SHA256
 d79c9f0846d93f4951e2ebc90b044cbcf4d6938ef1870881ee0b49cf71be871c;
EXE b4bc05911bca6ea3ffd70397bee08a8c47a1052a076303097578c5090c4c8aa7.
Private evidence: pack-signing-61c1c81/guest-lock-matrix-comparison.json,
source-manifest.json and each guest-lock-*/windows-receipt.json.

An independent comparison verifies all43 complete generated function extents and
six512-byte detour/helper target entry ranges in the actual input and accepted/
refused outputs against XBE f67e6fc1cb76c9ea1f1ad504e4a6491ff126483d66a9da8ddb92950bbaf740ba.
Receipt: pack-code-comparison.json. This guards against accidentally testing
retail bytes, but is not whole-image attestation or coverage of every function.
No retail generated source, memory image or game executable is committed.

These tests use authored grants, roster/calendar and money data; they do not
verify live MyNFL1 signing, all contract shapes/rosters or modern opening books.
Runtime/franchise binding, durable current-control permits and actual signing/
save/reload remain open. The installed game, user saves and remote control were
not modified. Production application grants remain unavailable.

The earlier ownership source1bf1013 is now fully green in Windows/Ubuntu
Franchise38783097191 and Build38783098207. Current61c1c81 also passes full
Windows/Ubuntu Franchise38783661071 and Build38783661101; these terminal results
supersede the preceding pending observations.


### October 15 — One addon path for vanilla and modded runtimes

The user requires vanilla Remade and compatible mod packs to share one addon,
without named-mod or executable-whitelist branches in application policy.
Removed the uncommitted version-specific signing-code whitelist. The replacement
is optional generic engine.loaded-image.v1 metadata over the existing ABI2 event/
snapshot mechanism. The host supplies its actual validated XBE load-input digest
after built-in file patches, and publishes it just after addon startup. No new
public ABI, game bytes, network calls or financial authority were introduced.

The loader accepts any canonical SHA256 through the same path, refuses a different
binding while loaded, clears stale unbound metadata on invalid input and reserves
the startup event against ordinary forwarded injection. Both the franchise addon
and generic counter example own an immutable snapshot; stop/reload resets their
copies. Actual Windows DLL fixtures exercise two authored identities, idempotent
binding, attempted retarget/injection, invalid binding and reload. The same path
handles both identities without game/mod detection. Metadata is trusted local
load-input identity, not attestation of subsequent guest writes, the native build,
active franchise or code compatibility. Durable service binding remains open.

Franchise interpreter hook registration now runs independently of an executable
hash. The dispatcher workaround follows interpreter activity rather than a
SOFTDRINK name/hash. Built-in file-patch rehash failure now stops before publishing
an uncertain digest. Existing named financial bootstrap profiles still need
conversion to explicit verified calendar/units/data context while preserving
saved bindings and actor identities; this change does not claim that migration.

All836 offline Python regressions pass in45.940s, and all six local native CTests
pass. The actual offline MSVC Windows build and Proton DLL/adapter/application/
pending-work fixtures pass with marker identity-passed, launcher exit0 and all339
source hashes verified. Receipt: shared-image-fa2673a/identity-receipt.json.
DLL SHA256 d1c112183b386c335eac2b30bb9f067b6d85bc8bf89701f26e68a0dcc4bfe049;
example DLL960a84bbbbc5d04e478630eccddeaf56eb81d5df9c2e9f7708683f88c799ac4b.
The fixture's intentional bad-DLL load failure126 remains an expected passing case.

The actual full Windows game build is still running after effective339-file source
verification and generated-patch checks. Follow that existing build; startup
validation and actual boot delivery of metadata are not yet proven. Installed
runtime/configuration, user saves and remote AI control were not changed. No live
signing/application permit or save/reload acceptance is claimed.


The full-game compile caught a missing declaration for g_interp_active. Including
the interpreter's public header in main.c fixes that actual compiler error.
The first resume lacked the existing SDL SDK mount; restoring the private build
configuration allowed the same build to finish without repeating generation.
The actual Windows game and matching DLLs now link successfully. Isolated
--validate returns launcher0, child validated and [TEST] Validation passed.
Receipt: shared-image-fa2673a/validate-game-receipt.json. The existing isolated
mirror/tiled-aperture warning remains; rendering/gameplay is not verified.

The game-built host/DLL fixture also passes the shared identity/load/reload tests
under Proton, marker identity-passed and launcher0, with all339 effective source
hashes matching the checkout. The private runner initially expected a differently
named marker; matching its assertion to the actual emitted marker resolves that
verification-driver failure. Receipt: game-pair-identity-receipt.json.
EXE SHA256 ba915e6564b65e0204ba18a4ac9c90e35a897d0c3dcad76b0e2fa0a18d847d72;
game-built DLL9a1f7843a6b251a268186eb8b627b2cf0ccf619fa2cf4304623943e14cf3434c.
The validation branch does not start the addon, so real game-boot delivery of this
metadata still needs verification. No installed game/configuration, user save or
remote control changed. Service binding, bootstrap generalization and live
signing/save/reload remain incomplete.

## October 15, 2026 — Shared explicit franchise context

New snapshot creation now emits original-save-bindings-v2 with explicit logical
season, raw scheduler index, liability unit factor and raw league cap. Source
executable bytes optionally record provenance; no image name/hash chooses rules.
The supported factors1 and4 use the same biography, contract and accounting path.
Raw scheduler/cap drift and malformed/mixed version schemas reject. Financial
exports separately reconcile payroll; an identity match grants no authority.

Existing v1 registries remain readable, including historical named-profile data,
so existing journals keep their recovery semantics. A copy-only --migrate-context
command normalizes that previously recorded data without rerolling UUIDs or
personalities. It refuses output overwrite and does not replace configured live
registries or migrate DB/journal hashes automatically.

All843 offline Python regressions pass in43.129s. Seven explicit-context tests
also pass in actual Windows CPython under the isolated Deck Proton profile,
followed by the native captured-acceptance/saved-candidate/ledger-confirmation/
AI-disabled restart-recovery driver against authored files. Launcher0, child
context-passed and explicit-context-windows-passed are verified. Receipt:
explicit-context-v2/windows-receipt.json; source manifest SHA256
8ff81448808dd0c0d596fe7b2827966f3224659cfd6a59cd1b6efc2c92c2e1d9.
Native checker SHA256 a43e6bb54f491095aacc911649b53529712b5f60d35389933d1a9a8386256242.
No paid inference was made.

Actual MyNFL1 copy conversion preserves2070 identities/personalities and1693
legacy schedules across32 clubs, with the original save and registry unchanged.
Save SHA256 4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3;
converted registry2e3b8d6b3cdf499dfdff10094d7edf34ab29d162477f7bdb92949c3aac4e5e86.
Receipt: softdrink-v0.6/mynfl1/explicit-context-validation/receipt.json.
The context records2026/index0/factor4/rawcap75300 as data. This does not reconcile
omitted non-roster liabilities or establish complete modern Team Salary.

Installed game/configuration, user saves, live DB and remote control were not
changed. Live service binding, store/journal migration and actual permitted
signing/accounting/save-reload acceptance remain open. Passing authored fixtures
and copy conversion do not establish game integration or playability.

## October 15, 2026 — Loaded-image handshake reaches the Windows service

The game adapter now exposes its immutable loader-provided image digest to the
franchise host. Hello forwards that digest on the owner thread without guest
reads. Negotiation-enabled callbacks fail closed if metadata is missing or
malformed. Neither an image name nor a predefined hash selects application rules.

An optional explicit loaded_image_sha256 in the v2 game context pins the expected
post-file-patch load input separately from source_image_sha256. The service
requires an exact match before inference or saved-journal preparation/confirmation.
Successful hello echoes that image, configured franchise namespace, canonical
registry SHA256 and service-start snapshot SHA256. Native response validation
requires the exact image echo and typed identities; unrequested binding replies
reject. Restart and every failed re-handshake clear the session match. Read-only
checkpoint/recovery and independent manual engine operations remain available.

A new failing test exposed explicit False control returns being ignored by the
two negotiation entry points. Both now deny before inference/recording. Raised
shutdown denials retain their behavior; matching runtime identity never overrides
remote control. No control object or credentials were renewed or enabled.

All850 offline Python tests pass in46.750s. All six local native CTests pass.
The actual offline MSVC Windows build succeeds, including the production addon
DLL, host client and saved-signing checker. Under isolated Deck Proton, protocol
identity validation, actual C-host forwarding of two arbitrary digests, malformed/
missing metadata holds, held-offer state, addon/DLL reload and14 Windows Python
context/handshake tests pass. Both the ordinary14-reply and runtime-bound17-reply
native client/sidecar authored saved-signing flows pass, including exact accepted
terms, preparation, live comparison, candidate save, ledger confirmation, failed
re-handshake revocation and AI-disabled restarted recovery. No paid inference.

The first private Windows runner failed before executing a child because its
inline grouped command was not accepted. Replacing it with an explicit .cmd file
resolved the runner failure; launcher0, child runtime-passed and emitted
runtime-handshake-windows-passed are all verified. Receipt:
runtime-handshake-c226e36/windows-receipt.json. All342 manifested source files
match the checkout; manifest SHA256
342d0fd94a77f24eb86b42017040839853dd364f5fc3c5d921ea3671c9c6dfe7.
DLL SHA256 df5a6d3fc936077e681c81b415e3e8f03419dfa8de6a04811808881259beaa53;
native saved-signing checker71d89d2964063d88c7392ff01cd6728a5ca75719f4dea655449bac5f401892ab.
Prior shared-context sourcec226e36 passes Franchise38790707525 and Build38790707466.

This matches a connection to its configured snapshot; it does not establish that
snapshot is the active guest franchise, verify arbitrary executable compatibility,
reconcile complete modern opening books, or issue a one-use guest application
permit. Installed game/configuration, real saves and live DB were untouched.
Actual game-boot handshake, application permits, legal live signing and durable
save/reload reconciliation remain open. No integrated-playability claim is made.

## October 15, 2026 — Persisted registry/database namespace association

Loaded-image-bound hello now also requires an explicitly registered association
between the configured snapshot registry and initialized database. The new
franchise.snapshot_origin module and tools.bind_franchise_snapshot command use
the existing transactional metadata table and pending-journal write guard.
Registration requires the original personality seed, all32 supported clubs,
complete bound actor coverage with correct generated origins, and matching
initial ownership. It adds one namespace record; no personalities, financial
records, save files or original journal intents are rewritten.

The association normalizes v1/v2 representations and reordered binding rows.
Its fingerprint includes the namespace, initial source/biography identities,
calendar/money context and immutable team bootstraps. Source/load-image digests
remain separate provenance rather than namespace/rule selectors. Conflicting
registries, altered seed/players/bootstraps, corrupted actor origins, concurrent
namespace claims and pending-work registration reject. Existing matching origins
are idempotent. Recovery reads retain the namespace while saved guest ownership
and pending ledger ownership temporarily differ; the old v1 journal's serialized
intent/hash remains byte-for-byte unchanged through verified settlement.

Initial full-club replay was too expensive on the actual private MyNFL1 database,
which contains66240 actor records for2070 distinct players. Registration instead
audits the immutable actor origins directly, reusing each generated identity
within that read transaction. Runtime verification reads the persisted association,
seed and bootstrap fingerprint. Financial/current actor-history validation stays
in its existing checkpoint/transaction paths; this is not an accounting shortcut
or a claim that every stored financial posting was verified at registration.

All862 offline regressions pass in74.928s. Actual Windows CPython under the private
Deck Proton profile passes19 namespace/handshake tests, followed by both ordinary
14-reply and runtime-bound17-reply native saved-signing/disabled-restart recovery
flows with authored files. The first Windows test run exposed SQLite fixture
connections whose transaction context managers did not close their handles;
explicit closing fixes the cleanup failures without changing product behavior.
Launcher0, child origin-passed and snapshot-origin-windows-passed are verified.
Receipt: snapshot-origin-24eeed1/windows-receipt.json; source manifest SHA256
34664e0c98cbc7b74371e3384b803810c92cd99a926ac3c5eeae682ef1881913.
The already compiled native checker71d89d2964063d88c7392ff01cd6728a5ca75719f4dea655449bac5f401892ab
is unchanged; this milestone changes Python application code only.
Prior source24eeed1 passes Franchise38792322978 and Build38792323233.

Actual MyNFL1 copies pass on both Mac and Windows. Logical SQL dump hashing proves
all pre-existing rows remain unchanged; only the explicit association was added.
The original DB b08a836f26ce65d4d5429d99134cb6610d1f53509b950b14bf5798684a279662,
registry9955880d3fb6a02eaebc4c1662cfac075afb59443a1191e709bf2dd51c9ee442 and
save4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3
remain unchanged. Existing logical rows SHA256
7db7c9fd87907c220a2754345273851512feed5fec92afea9941db2fe899a087.
The final Windows copy is ce06504319f4eb2e4a3c41cc835184a2750720c99b492ab74853e2e2bcd10cb5;
one-time registration3.598s, runtime namespace verification0.0745s. Receipt:
snapshot-origin-24eeed1/mynfl-windows-receipt.json. The actual copy paths are
isolated from installed runtime/configuration, original save and live DB.

No paid inference or remote-control change. This proves the configured registry/
database relationship, not the identity of the save active in guest memory,
complete modern opening obligations or a one-use guest application permit.
Actual game-boot handshake, legal signing/accounting/save-reload, supported rookie
integration and final playable-build acceptance remain open.

## October 15, 2026 — Faster actor replay with all integrity comparisons retained

The actual MyNFL1 DB has2070 actor registrations per club (66240 total). Each
registration previously built a complete negotiation context and rebuilt an
unchanged financial snapshot, including serialized legacy-contract hashes.
Store replay now checks registered membership directly, computes the unchanged
classification/posting once per contiguous actor block, and compares every saved
posting against it. Any other event invalidates the block values before replay.
A single _load_teams read shares immutable expected origins keyed by seed/player;
actual mutable actors remain separately decoded records. Nothing is cached across
read transactions, stored financial history is not skipped, and no data migration
or new application authority is introduced.

All866 offline Python tests pass in41.715s. New regression cases reject late-block
posting corruption, stale postings after an interleaved financial event, corrupt
origins after another read and unknown actor identities. A sourced relationship
update on one club cannot mutate the expected origin or another club's actor.
Actual Windows CPython passes32 actor/initialization/namespace/handshake tests,
then both14-reply and runtime-bound17-reply native saved-signing/disabled-restart
recovery flows using the existing compiled checker. Launcher0, child replay-passed
and replay-windows-passed are verified. Receipt: replay-ab02a28/windows-receipt.json;
source manifest SHA256 9238488dbbcab83ce3532172761d06aeefa71e718b0f8eba669a108e1dd8a8a3.
The unchanged native checker is71d89d2964063d88c7392ff01cd6728a5ca75719f4dea655449bac5f401892ab.

Measured actual MyNFL1 copy on Mac: Giants1.749s→0.572s, all32 clubs3.901s.
Windows: Giants1.552s→0.366s, all32 clubs4.130s. Old/new financial, cash and
full actor fingerprints match exactly; final league postings also match their
recorded source events. The Windows DB ce06504319f4eb2e4a3c41cc835184a2750720c99b492ab74853e2e2bcd10cb5
is unchanged. Receipt: replay-ab02a28/windows-benchmark-receipt.json. These are
isolated replay timings, not proof that a whole guest transaction meets a deadline.

A separate actual Windows sidecar process check uses the pinned MyNFL1 signing
context request, deliberately unavailable credentials and read-only operations.
Old/new protocol replies match exactly, with AI disabled, classification-pending
modern offers still rejected and all inputs unchanged. Process timing including
launch improved6.755s→4.029s. The first private timing harness hung reading a
pipe under Wine and was stopped by its exact PID; file-backed input
and explicit child markers then passed. Receipt:
replay-ab02a28/windows-service-receipt.json. No installed game/configuration,
original save, live DB or remote control was changed; no paid inference.

Static tracing for active-save binding found common load interiors around
16E70B/16E7AE (input selection/prefix),16E7E0 (roster relocation),16E7FD
(scheduler) and16E815/16E81A (tail/size). C2040 rewrites pointers in the serialized
buffer, so hashing only after deserialization cannot identify its original bytes.
Several generated exports share these interiors. A future source observation
must cover the actual pre-relocation input span and selected container, and must
not treat reaching one interior as complete successful load proof. No new load
hook, active-franchise claim, application permit or playable-game delivery was
introduced. Actual load selection, native signing/accounting/save-reload and final
acceptance remain open.

## October 15, 2026 — File-read observer source; Windows integration gate remains

Active-save tracing needs the native file handle and bytes actually delivered,
not a configured path or a roster-only match. Runtime fork branch
codex/file-read-observer adds an optional synchronous xbox_NtReadFile observer.
It reports the original native handle, status, requested/completed lengths and
borrowed bytes; failed/empty/out-of-bounds deliveries expose no bytes. Nested
reads execute normally without recursively notifying. Success completion events
are signaled after observation, before returning to completion waiters. Setup
requires quiescent I/O, normally before guest startup; no result can be overridden.
The Windows and POSIX read paths share that behavior without game/mod policy.

Root source registers a forwarding callback before guest execution and sends
optional ABI2 engine.file-read.v1 through the existing loader. The domain-neutral
example counts observed bytes. A new authored kernel-to-host-to-DLL delivery
fixture also checks the source handle's native file identity. The read-scope DLL
fixture checks that file notification does not grant unrelated guest-memory
access. No franchise handler consumes the new channel yet; raw pointers/handles
must never cross the process wire or outlive their synchronous callback.
The observer does not establish offsets, stable file contents, deserialization
success, selected franchise identity or permission to apply a transaction.

A real Linux I/O regression exposed an existing POSIX bug: w32_handle_fd/path
would dereference INVALID_HANDLE_VALUE or pseudo handles. The independently
isolated guard fix reproduces the segfault before the change and passes afterward
on macOS, including untouched failed-read buffers and valid reads/writes.
It is submitted separately as https://github.com/BeyondTomrrow/xboxrecomp/pull/2,
only39 added lines across three files against upstream main. The earlier Windows
string-header PR#1 is now merged into upstream nfl2k5-port. No other maintainer
message was sent. Attribution/licenses are preserved; no assets/binaries published.

Runtime source393fe75 initially passed Windows dispatch but failed real Linux I/O
because of that pre-existing handle crash. Source4bf498c3d94c1faf6b1956fba9f77f58f52bac5f
includes the guard and passes both jobs in runtime CI38799506013. Default observer
dispatch also passes locally. All866 root Python regressions pass in36.703s and
all six local native CTests pass. These checks do not substitute for the Windows
kernel/DLL delivery fixture or actual game boot.

The private Linux setup first lacked host CMake; using the existing offline Linux
compiler image resolved that setup issue. The initial focused harness then lacked
POSIX temporary-file/event helpers; the corrected version links in CI and exposes
the real invalid-handle bug above. A private Windows standalone observer/bridge
build returned0 before the final read-scope test additions. The private full-game
build returned1; its log has not been inspected because the Deck went offline.
Do not restart that job or overwrite its source blindly: inspect its existing
container/build log after reconnection. Source overlay367 files was guarded by
previous full-game/runtime hashes and backed up before modification; only private
build-source/artifact directories changed. No installed runtime or user save changed.

The Deck is unreachable over SSH; an awake/same-Wi-Fi request is pending. The final
POSIX harness fixes and runtime guard have not yet been copied into that private
full-game build source. After reconnection, inspect the old build, compare hashes,
apply only the declared final source delta and resume the existing build. Validate
actual Windows read/EOF/error/completion order, kernel-to-loader-to-DLL identity/
byte delivery and full-game --validate before any installation. Live load/container
binding, one-use application permits and actual signing/accounting/save-reload
remain open. AI/control remains disabled; no paid inference or control renewal.

## October 15, 2026 — Shared observer Windows I/O validation

Runtime ea4a0eecb78bff79225768d7c167d9feb12f9447 passes both Windows and
Linux actual file-I/O checks in CI38800594758. The focused Windows target links
the real path, I/O and guest-lock dependencies; only logging is stubbed. Root
checks now enable actual reads on both platforms and add a Windows
kernel-to-loader-to-example-DLL delivery check without requiring game assets.
Its root Windows result remains pending until the updated source runs in CI.

The shared compatibility contract applies to original Remade and compatible packs:
layout/capability checks guard the same application path, while verified calendar,
money units and roster/contract content are explicit data. Historical named
registry decoding is retained solely for durable recovery; it does not select
new-franchise policy. Unsupported layouts must reject explicitly. No new mod-name
branch, application grant, live installation or save modification was introduced.
The Deck connection and actual full-game/save-load verification remain pending.

## October 15, 2026 — Deck reconnected; rebuilt Windows observer pair validated

The user restored Deck connectivity. Inspection confirmed the previous build was
terminal: its full-runtime test harness linked unrelated title dispatcher/video
references and failed with28 unresolved symbols. No live container or game was
running. A declared369-file source delta for root8909ede/runtime ea4a0ee was
verified against the prior effective manifest, backed up and applied only inside
the private build source. The validation-only top-level CMake suffix was retained
and separately hashed. The corrected build uses the focused real-kernel delivery
target instead of the unrelated full-runtime harness; the game still links its
normal complete runtime. The offline MSVC game build and subsequent addon/observer
build both returned0. No source changes were needed beyond8909ede.

Actual Windows binaries under Proton passed dispatch, native read/short-read/EOF/
invalid-handle/missing-status checks, nonrecursive notification, completion-event
ordering, source-handle native-file identity through the loader/example DLL, and
ABI/disabled-service/reload checks. Logging alone is stubbed in the focused I/O
harness; the real kernel path/I/O/guest-lock sources are linked. Child marker
passed and launcher0 are recorded in
.local-runtime/file-observer-56ed62d/final-checks-receipt.json. The expected missing-
DLL refusal in the ABI fixture is exercised successfully. No file event grants
guest-memory authority.

The rebuilt game and production DLL also pass isolated --validate under Proton:
launcher0, child marker validated and [TEST] Validation passed.
EXE SHA256 daab780e0058ba9553ef12fa0c9eead1161d3d53c6ccf26aa65265f8a088ad3d;
DLL SHA256 cf0dce7f252bd21098913dcfff8fafdd8bad1f229b8f943d74df136a882951a1.
Receipts and effective manifest are copied locally alongside the source manifest.
This invocation does not execute game-boot metadata or prove a loaded franchise.
Only the isolated native-05ac4e9 validation runtime was updated; the installed
Steam game, wrapper, user saves and controls were not changed. No AI inference,
cloud changes or control renewal occurred.

Root8909ede Build38801025861 passes; Franchise38801026470 has passed Ubuntu
and is still running Windows financial tests at this checkpoint. Previous
root4aefd29 Build38799924278 and Franchise38799924192 both pass. Standalone
engine-sidecar CI38677485314 at2a2110d also passes. Seven local explicit-context
regressions pass, including arbitrary image provenance with either supported unit
factor and copy-only legacy recovery. Active-save binding, one-use application
permits, complete modern opening books, actual signing/accounting/save-reload and
final playable delivery remain open.

## October 15, 2026 — Franchise save-read candidate capture

The franchise DLL now consumes the generic file-read channel. A shared observed
FXG envelope filter accepts only full720044-byte deliveries with the declared
roster markers, length and bounded player-bank pointers. Windows captures the
delivered-byte SHA256 plus native volume/file index, size and write time while
the borrowed handle is valid, checking identity/size/write time again afterward.
It stores only owned scalars/digest under a lock. A snapshot exposes the most
recent candidate and restart clears it; no guest read or process/model/store call
occurs in the callback. Trace output is deferred to owner polling. No engine or
transport policy, pack-name branch, extra memory grant or application issuer was
added. Partial reads remain unsupported. Native metadata stability does not prove
immutable source bytes or successful deserialization; an overlay can affect bytes.
The record explicitly does not claim an active franchise.

Seven local native CTests pass. The866-test Python run had only four sandbox
loopback-bind permission errors; the complete five-test web module passes outside
the sandbox. Actual private MSVC production DLL/read fixture passes under Proton:
two distinct native files containing the same authored payload yield the expected
SHA256 and different file identities; short/failed/oversized/invalid-handle reads
do not replace the candidate; closing/freeing borrowed inputs preserves the owned
snapshot and restart clears it. Source overlay373 files is hash-verified and
backed up before application. The game/updated-DLL pair passes isolated --validate
with child marker validated and launcher0. EXE remains
daab780e0058ba9553ef12fa0c9eead1161d3d53c6ccf26aa65265f8a088ad3d; new DLL
983dcf429d56d0f658458357c83a2175c35ef2e4fded2df0ed4a1eeade7e253a.
Receipts are private under .local-runtime/save-read-b937df0.

Root8909ede CI38801026470 passed the new native observer/delivery checks but
later failed an existing C-host expected-player-rejection assertion without
printing the actual reply. An assertion diagnostic now preserves that reply.
Six direct actual Windows C-host runs on Deck (three databases, each restarted)
pass unchanged one-second request deadlines. The already-running documentation
checkpoint b937df0 CI38801913914 also passes Windows and Ubuntu on the same code;
its Build38801913988 passes. The original transient failure cause is unproven;
no timeout was relaxed and no assertion was bypassed.

At this checkpoint no installed game, wrapper, saves or AI controls changed.
Actual game read delivery, selected-container/load completion, current franchise
identity, full modern opening obligations and real signing/save-reload remain
open. This evidence does not establish playable integrated negotiations.

## October 15, 2026 — Read-only save observer privately installed

Source2bab3a4 and its authored checks are committed/pushed. With both the game
and sidecar absent, the guarded installer verified the expected old EXE, DLL and
wrapper, all373 declared source hashes, private Windows fixture completion and
the isolated game validation receipt. It backed up the previous pair/wrapper
under save-read-b937df0/installed-before-save-read and installed the validated
EXE daab780e...88ad3d and DLL983dcf42...7e253a in the existing Steam runtime.
The wrapper now enables trace and explicitly sets controlled negotiation and guest
application to0 while retaining its unset provider/Python/database policy.
Original retail signing is available; no AI or sidecar financial authority was
enabled and remote controls were not changed. New wrapper SHA256
946c98866fb1a9b2fe6ded31d4a967bb277c59a181f42e3deed6682682be2143.

All205 files currently under that runtime's saves directory have identical
before/after hashes; no registry/store or save migration was performed. The
installation receipt records those hashes and all installed hashes privately.
Actual game boot/load remains unverified. A request is pending for the user to
launch the same Steam entry, load MyNFL1 and leave its franchise menu open without
submitting. Inspect the new log for delivered-save candidates; do not equate one
with complete selected-container/load binding.

Exact source2bab3a4 CI is still running: Build38803210462 and Franchise38803210766.
Prior b937df0 Build38801913988 and Franchise38801913914 both pass. Keep the new
handles; do not restart them merely because a status observation times out.

## October 15, 2026 — Actual MyNFL1 save-byte delivery verified

The user launched the installed source2bab3a4 build and confirmed MyNFL1 open.
An actual running Windows game child (PID176538 at observation) produced
franchise save_read sequence1,720044 bytes, SHA256
4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3.
Both runtime saves/franchise/MyNFL1/SAVEGAME.DAT and its UDATA copy have that
exact hash. The selected pack logged SOFTDRINK2K28v0.6 with1287 interpreted
functions. Parent steam-launch.log contains mainly Gamescope output; the actual
pack-dispatched child redirects diagnostics to the prefix's per-user
AppData/Local/NFL2K5-PC/logs/session.log. A bounded copied log and process/artifact/
save-hash receipt are private under save-read-b937df0/actual-read-receipt.json.
Installed EXE/DLL/wrapper hashes still match the recorded installation.

This proves actual kernel-to-loader-to-production-DLL delivery of those save
bytes while the real game runs, beyond the authored fixtures. It does not prove
which duplicate file/container was selected, causal load completion, namespace
binding, transaction authority or signing/save-reload. The user session remains
running and was not interrupted. AI/provider/controlled application remain off.

## October 15, 2026 — Destination-aware read evidence; complete Windows suite

To correlate a native read with the actual load destination, the host now emits
optional engine.file-read.v2 alongside unchanged v1 delivery. A small bounded
translation uses the current guest mapping base and existing memory-range checks
to report guest_mapped/guest_address only for a complete successful delivered
span. It dereferences no bytes and grants no memory access. Null/zero/unmapped/
overflow/out-of-range spans remain unknown. This is generic engine metadata; no
pack/image name selects behavior. The franchise.save-read.v2 owned snapshot
consumes the richer event once per delivery and retains the locator alongside
the delivered hash/native file identity. Locators can be reused and still do not
prove a selected container, causal load completion or transaction authority.

Eight local native CTests pass. A separate offline MSVC build compiles the full
Windows game and every standalone bridge target, then all15 generated Windows
CTest commands execute successfully under the isolated Proton fixture prefix.
This includes actual kernel-to-DLL delivery, legacy v1 compatibility, a mapped
locator without guest-lock memory authority, malformed locator rejection, the
production save-read DLL, bounded host protocols, ownership/lifecycle and stalled
peer shutdown. All375 declared source hashes are verified; child marker passed
and launcher0 are recorded under read-location-a6b3263/checks-receipt.json.

The full game/new-DLL pair also passes isolated --validate, marker validated,
launcher0. EXE SHA256184f81fec072ac4b06ecd36c743e5243c1eca8284df6d644bdf9ec23b9c20883;
DLL SHA256354ae9bc7f9fdd14038e600065dd6deaacbce0b1828ba43d300f2748aac82868.
These staged artifacts are not installed; source2bab3a4 remains running with its
verified v1 MyNFL1 read. No user game interruption, save edits, inference, control
renewal or application grant occurred. Combine the next load-boundary integration
with this metadata before requesting another user restart.

Exact2bab3a4 CI38803210766 passes Ubuntu but failed Windows linking the standalone
signing-adapter-stage test, which also compiles the real adapter and lacked its
new bcrypt dependency. The production DLL/game and the initially selected private
targets compiled, but that target was omitted from the earlier private build.
The missing target-specific bcrypt link is now added. Building/executing the
complete standalone suite above verifies this correction without relaxing tests.
Build38803210462 passes. Current changed source still requires its own CI run.
The earlier transient C-host expected-rejection failure remains a separate issue
with reply diagnostics and six passing direct Windows reproductions; no deadline
was changed. Actual selected-load binding and financial signing/save-reload remain
open; these read observations grant nothing.

## October 15, 2026 — Correlated load checkpoints; Windows validation passed

The franchise addon now observes the existing load router before its native read,
on failure, before relocation and after franchise decoding. All five generated
copies and interpreted execution report the same four checkpoints without
changing game control flow. The patcher rejects altered checkpoint bodies or
locations. No pack name selects behavior. The existing guest-memory callback
supplies bounded table/input reads; native pointers are not retained.

An owned observation correlates one full delivered720044-byte read with its
mapped destination, owner/frame/table, exact input SHA256 and final consumed
byte count. Epochs prevent an older in-flight read attaching to a newer load.
Missing, duplicate, partial, changed, unreadable, mismatched or nested attempts
invalidate the observation. The historical snapshot is explicitly a load
checkpoint, not an active-session proof, selected-container namespace or permit.
Failures before the first checkpoint and subsequent lifecycle transitions still
need active-binding coverage before this can authorize anything.

All868 Python regressions and nine local native CTests pass. An offline MSVC
build verifies380 declared source files, compiles the full Windows game/DLL and
all standalone targets. All17 generated Windows CTest commands pass under the
isolated Proton fixture prefix, including the production-DLL read/input/decoded
fixture, duplicate/changed/unreadable rejection and restart. The full game/DLL
also passes isolated --validate, child marker validated, launcher0. Private
receipts are retained under load-read-8d4f3cd on the Mac and Deck.

EXE SHA256 b770243d64a211595848dd41a17773887c9bb797862ecae9dd77523b699bb518;
DLL SHA256 4af092de1a4a509d8efc12490997a5fcf94ac793218af91fcbc975b5c705bcc5.
These combine destination metadata with load checkpoints and are not installed.
The user game is not interrupted; actual MyNFL1 checkpoint delivery, complete
active namespace binding and financial signing/save-reload remain unverified.
AI controls remain off; no inference, save edits or application grant occurred.

Exact preceding commit8d4f3cd passes Build38805048068 and Windows/Ubuntu
Franchise38805048342, including the corrected bcrypt link. Those CI results
cover the preceding connection change, not the new uncommitted checkpoint code.

After the user confirmed normal exit, the guarded installer verified no game or
service process, the exact previous EXE/DLL/wrapper and the tested380-file source
overlay. Source09fcc07's combined EXE/DLL above are now installed, with the prior
pair backed up under load-read-8d4f3cd/installed-before-load-read. All205 save-file
hashes are unchanged. The wrapper is unchanged and retains AI/controlled signing
off. Installation receipt is retained on Deck; actual new game boot and MyNFL1
read/input/decoded checkpoint delivery are pending the requested normal launch.
Exact09fcc07 Build38807043193 and Franchise38807043294 were still running at
this installation check; do not describe them as passing yet.

## October 15, 2026 — Actual MyNFL1 checkpoints exposed a count-observation bug

The user launched the installed build and confirmed MyNFL1 open. Process188574
delivered the same720044-byte save SHA256
4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3
to mapped destination0x81d8f280. Load epoch1 reports kind9 and source sequence1,
then rejects the decoded checkpoint with consumed628476, phase4. The exact
installed EXE/DLL hashes still match the installation receipt. Private actual
trace/artifact evidence is retained under load-read-8d4f3cd/actual-load-receipt.json
and actual-load-session.log on Deck. This is actual callback/read correlation
evidence, not successful completed binding or an application permit.

Inspection of the router shows that at0x16E81A EBX excludes the final franchise
section: helper0x2D0780 returns its0x165B0 length in EAX, without adding it to EBX.
628476+91568=720044. The original checkpoint observed EBX alone. The correction
reports a checked EBX+EAX sum for this checkpoint in generated and interpreted
execution, rejecting overflow; it changes no game register, branch or save data.
The patcher upgrades only the exact previous owned body at the expected anchor.
Four targeted tests pass, including compilation/execution of all five generated
checkpoint bodies and interpreter callbacks with these observed prefix values,
register preservation, upgrade/check behavior and overflow rejection. Corrected
private Windows build is running under decoded-load-027e68b; actual new load
verification remains pending. User session is not interrupted; AI remains off.
Exact09fcc07 Build38807043193 has now passed; Franchise38807043294 was still
running at this check.

The corrected count build now passes all17 actual Windows standalone checks and
isolated full-game --validate, child marker validated and launcher0. All380
declared private build-source hashes were verified. One subsequent test-only
change skips C compilation when cc is unavailable after still checking patch
upgrades; all four targeted tests execute and pass locally with cc. Native build
inputs are unchanged by that portability adjustment. Receipts are under
decoded-load-027e68b. Corrected EXE SHA256
c23dee11e3df74d6d40d18af82652d9b876cc04c3f6202014d69e853bea853a3;
DLL is byte-identical to the installed
4af092de1a4a509d8efc12490997a5fcf94ac793218af91fcbc975b5c705bcc5.
The corrected executable is staged, not installed; normal exit is required.

### Resume gate — corrected count installation

Across three subsequent checks, the previous game process188574 remains running.
Do not replace or terminate it. The prepared guarded installer is
decoded-load-027e68b/install-readonly.py on the Deck, pinned to sourcef08390c;
it replaces only the EXE, checks the unchanged DLL/wrapper, backs up the old EXE
and verifies every save hash. After normal game exit, execute that installer,
then request one MyNFL1 load and inspect the actual session.log for epoch/phase,
720044 consumed bytes and the expected source hash/destination. Successful
checkpoint correlation still does not establish selected-container identity,
active-load lifetime, a production permit or financial signing/save-reload.

Exact09fcc07 Franchise38807043294 is now successful on Windows/Ubuntu.
Corrected sourcef08390c Build38808041932 and Ubuntu checks pass; Windows
Franchise38808041886 is still executing Financial, negotiation and shutdown tests.
An existing read-only gh watcher is exec session24462, with output retained in
.local-runtime/decoded-load-027e68b/ci-watch.log. Poll that run/handle for terminal
evidence; do not restart it or label it passing. Independent native build,
17-test Proton execution and isolated game validation are already complete.
The next runtime acceptance step requires the user's normal game exit and load;
no game interruption, save edits, inference or control renewal is authorized.

## October 15, 2026 — Corrected load count installed after normal exit

The user confirmed normal exit. The guarded installer verified no game/service
process, the exact installed EXE and unchanged DLL/wrapper, plus the tested
private source overlay. It installed only sourcef08390c's corrected EXE,
SHA256 c23dee11e3df74d6d40d18af82652d9b876cc04c3f6202014d69e853bea853a3,
with the prior executable backed up under
decoded-load-027e68b/installed-before-decoded-count. All205 save-file hashes are
unchanged; the installation receipt is retained on Deck. AI/controlled signing
remain off. The user has been asked to launch the same Steam entry and leave
MyNFL1's franchise menu open for actual corrected checkpoint verification.

Exactf08390c Franchise38808041886 has now passed both Windows and Ubuntu;
Build38808041932 also passed. The read-only CI watcher finished successfully.
These checks do not establish actual new-game load correlation, selected-container
binding or legal signing/save-reload; those gates remain open.

## October 15, 2026 — Actual corrected MyNFL1 load correlation passes

After verifying no game process, launched the existing 2K5 Remade (Test Build)
Steam shortcut16147863382609887232. The user confirmed MyNFL1 loaded. Actual
process194180 runs the installed corrected EXE c23dee11e3df74d6d40d18af82652d9b876cc04c3f6202014d69e853bea853a3
with unchanged DLL4af092de1a4a509d8efc12490997a5fcf94ac793218af91fcbc975b5c705bcc5.
The selected pack logs SOFTDRINK2K28v0.6. Its real trace now reports:

```
load_read epoch=1 phase=1 stage=1 buffer=0x81d8f280 size=720044 kind=9 consumed=0 source_sequence=0
save_read sequence=1 bytes=720044 payload_sha256=4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3 guest_mapped=1 guest_address=0x81d8f280
load_read epoch=1 phase=3 stage=4 buffer=0x81d8f280 size=720044 kind=9 consumed=720044 source_sequence=1
```

This verifies native delivery, exact pre-relocation input matching and decoded
checkpoint correlation on the actual running game, including the corrected
EBX+EAX count. Evidence and full copied session log are retained privately under
decoded-load-027e68b/actual-load-receipt.json and actual-load-session.log on Deck.
Both saves/franchise/MyNFL1/SAVEGAME.DAT and its UDATA copy still have this exact
hash. Their duplication means hash matching does not identify the selected
physical container. Selected-container/namespace binding, active-load lifetime,
production permits, financial signing and save/reload remain open. No game input
was injected and no saves were edited. AI/controlled signing remain off. The
optional bounded Spectacle observation produced no screenshot; no screen state
is inferred from it.

## October 15, 2026 — Batched physical-source and negotiation-origin guards

The user requested grouping changes before another game restart. This batch stays
in the franchise addon/bridge; no new native guest hooks or mod-specific policy
are added. The owned loaded-source snapshot reports a decoded origin and an
explicit configured-path match. Matching requires the same native volume/file
index, length, last-write version and exact delivered payload SHA256; identical
bytes in another physical container are rejected. Handles/buffers are temporary.
Load epoch/source/phase are checked again after the bounded file read.

The Windows C client retains the payload hash from its consumed, validated runtime
hello. A new hello immediately clears the old grant/hash; a denied handshake or
missing binding cannot match. On the owner, context/proposal submission, reply
presentation, accepted preparation, completion and automatic journal checks now
require the decoded source hash to match that handshake and the configured
physical save. Replies also require their original load epoch, so a later load
cannot consume an older acceptance even with identical observed offer terms.
Existing persistent namespace/origin verification remains in the service.

Per-frame context sampling copies only owned load scalars/hash. Full file
verification occurs at request/reply boundaries after debounce; held journal
checks retry on their existing two-second cadence. An authored host regression
checks that pending frame samples do not repeat file verification. Physical
source identity is included in the load trace for later actual-container audit.

All869 Python tests pass across the main run and the permitted loopback rerun:
the sandbox rejected four localhost bind attempts; all five web tests pass with
loopback permission. Nine local native CTests pass. The initial Windows build
and final refinement both compile. The final382-file source overlay passes all17
actual Windows standalone CTests under isolated Proton, including production-DLL
duplicate-container rejection and host unbound/payload-mismatch/stale-load cases.
Both actual Windows C-client/sidecar saved-settlement runs pass with authored
inputs, including runtime-bound payload match/mismatch and failed re-handshake
revocation. No paid inference or real save inputs are used by those fixtures.
The full game/DLL pair passes isolated --validate, marker validated, launcher0.

Final receipts are private under source-binding-763c714-final. EXE SHA256
f991f49c7aacd0625d264dced1686c6b25ccb1d007e3e1619e0507488189de45;
DLL SHA256005a0e1cb4e65b4288403556ffd6237a1b9c8a57ba25f8e42c5d6d62277a62da.
These are staged, not installed. Actual selected-container matching and current
franchise lifetime invalidation, complete opening books, production application
permits and actual signing/save-reload remain open. A decoded origin is historical
evidence, not a complete active-session proof or write grant. The running user
game, saves and AI controls are unchanged; AI remains off.

## October 15, 2026 — Combined source-binding batch installed

After the user confirmed normal exit, the guarded installer verified no game or
service process, exact installed artifacts/wrapper, the382-file tested source
overlay and all three fixture/validation receipts. It installed source23946c9's
EXE/DLL above, backed up the previous pair under
source-binding-763c714-final/installed-before-source-binding, and verified all205
save-file hashes unchanged. The launcher/wrapper and AI controls are unchanged.
The existing Steam shortcut was relaunched and process205319 is running. The
user was asked to load MyNFL1 for the combined build's actual container audit.

A private read-only Windows ctypes inspector reads metadata and content through
the same native handle, checking identity/version before and after hashing.
It confirms that the observed copies have equal720044-byte hashes but distinct
file identities on volume4061331925: saves/franchise/MyNFL1/SAVEGAME.DAT has
index00000000:00945223; saves/UDATA/53450030/12051C2F122B/SAVEGAME.DAT has
index00000000:00945220. Both retain payload SHA256
4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3.
This maps candidate files only; compare the actual game load trace before
identifying its source. Native inspection marker passed, launcher0, receipt
native-save-identities-receipt.json is private in the same stage. No save writes,
paid inference, control renewal or production application occurred.

Exact23946c9 Build38811766079 and Ubuntu Franchise checks pass; Windows
Franchise38811766065 was still running at this installation check.

## October 15, 2026 — Actual UDATA source identified; existing namespace preflight

The user confirmed MyNFL1 loaded on the combined build. Actual process205319
reports a decoded epoch1/phase3 checkpoint with720044 consumed bytes and source
sequence1. Its native volume4061331925/index00000000:00945220 uniquely matches
the Windows witness for saves/UDATA/53450030/12051C2F122B/SAVEGAME.DAT. The equal-byte
saves/franchise/MyNFL1 copy has a different index00945223 and is not this read's
source. Delivered/input/disk payload hashes all remain
4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3.
Installed EXE/DLL hashes match the deployment receipt. Actual trace, exact file
witness and artifacts are retained in actual-source-receipt.json and the copied
actual-load-session.log under source-binding-763c714-final on Deck; the receipt
is also retained on the Mac. This proves the physical file for this decoded read.

A SQLite backup from the prior registered snapshot-origin validation database
was verified against the existing v2 registry and the exact now-observed payload.
The association retains franchiseb8d2e88dbe2d4c96804a8c2dff050e19, its original
personality seed fingerprint and player IDs. All2070 players resolve across32
teams, logical2026, scale4:1, raw cap75300. Original database/registry/save hashes
are unchanged. The copied preflight and observed-source-namespace-receipt.json
are private in the local stage. No registry or personalities were recreated.

Exact23946c9 Franchise38811766065 now passes both Windows and Ubuntu, alongside
Build38811766079. Native physical origin and copied namespace preflight do not
prove a live configured source/namespace handshake, full active-franchise lifetime,
modern opening books, a production permit or actual signing/save-reload. Provider
and controlled signing remain off; no AI request or real-save write occurred.

## October 15, 2026 — Read-only namespace handshake without an AI grant

Previously native payload matching required the AI hello grant, preventing the
live namespace connection from being verified while AI stayed disabled. The new
bind_runtime operation verifies the explicit expected image and existing
registry/database association and returns exactly ai_enabled=false, the sole
signing_context capability and the existing four-field runtime binding. It does
not consult/refresh AI control or call a provider. It resets prior AI-handshake
state and never marks the service AI handshake verified. Wrong/missing expected
images or association data reject; no image whitelist or mod-name rules are added.

The native client accepts this narrow observation result, records its validated
payload hash, and retains AI/journal grants false. A new hello/bind attempt clears
old grants and hashes before submission; fatal transport failures clear the
binding. AI operations still require the separate hello grant and existing fresh
control checks. The game host selects bind_runtime only for configured observation
mode; enabled negotiation retains hello. Observation mode now requires actual
loaded-image metadata rather than falling back to an unbound legacy hello. A
once-per-start diagnostic records that metadata for actual callback auditing.

All871 Python regressions and nine local native CTests pass. The full offline
Windows build verifies382 source hashes; all17 standalone Windows checks and
both actual C-client/sidecar journal fixtures pass under isolated Proton. The
runtime-bound fixture first consumes an observation binding, verifies its payload
hash, and proves that a negotiation submission remains denied until an AI hello.
Native protocol tests reject observation replies claiming AI/extra capabilities.
The rebuilt game/DLL passes isolated --validate, child marker validated, launcher0.
Private receipts are under readonly-binding-0fda623. EXE SHA256
f07c38347db765b8c355e977fbc5647e558bbc7771c99184eb5e966ba007a74a;
DLL SHA25629ffb27c669dec8957fc7246fe2b5e6dd39934fd9ceb3c99580b6498966d7e92.

A separate immutable135-file service source bundle and copied existing database/
registry are staged. Expected imagef67e6fc1cb76c9ea1f1ad504e4a6491ff126483d66a9da8ddb92950bbaf740ba
is explicitly pinned from the active pack input and the current loader's digest
calculation; actual new callback echo remains to verify. Existing franchise/player
IDs, seed, calendar and4:1 units are preserved; no identities are regenerated.
The configured save is the now-verified physical UDATA path, not its equal-byte
franchise copy. Staged launcher keeps negotiation and guest signing0 and uses
forced missing ADC, with the existing explicit one-request/20000-token ceiling;
read-only binding never grants or spends that budget.

The isolated Windows service preflight uses that actual UDATA file, copied DB and
registry, bind_runtime, existing Giants/Will Hernandez context and a forbidden AI
request. It completes in2.322s, returns the preserved namespace/player personality
and financial revision1, reports no AI/write authority, rejects the AI operation
and records zero model attempts. Input save/registry/database hashes are unchanged.
The offer remains accounting_rejected for unresolved classification/opening scope.
AI initialization is deliberately unavailable through missing ADC; the read-only
path works without enabling it. context/context-receipt.json and driver-receipt.json
retain marker passed/launcher0 and135 verified service files on Deck.

No installed executable, launcher, database, save or controls have changed in this
milestone. Actual in-game source/namespace reply consumption, complete lifecycle
invalidation, modern opening books, permits and financial signing/save-reload still
need verification. This staged observation connection is not an application grant.

### Read-only batch installed after normal exit

After the user's normal-exit confirmation, the guarded installer replaced only
the executable, addon DLL and existing Steam wrapper with the validated5698281
batch. All205 save hashes remain unchanged. The previous three artifacts are
backed up in readonly-binding-0fda623/installed-before-readonly-binding, and the
installation receipt is preserved on Deck and locally. Existing namespace data
is used from the immutable copied context; identities were not recreated. Native
negotiation/guest signing remain0, credentials are deliberately unavailable, and
the read-only binding grants no AI or journal authority.

The first actual launch reached the addon and emitted the expected loaded-image
digestf67e6fc1cb76c9ea1f1ad504e4a6491ff126483d66a9da8ddb92950bbaf740ba,
then exited with exception0xC0000094 at host0x1423CD9CF. This is an integer
divide-by-zero; its cause is not established. The complete first-boot log is
preserved locally as first-installed-boot-crash.log before retry. A single retry
through the same Steam shortcut is running as PID212176 and emitted the same
digest with held negotiation mode0. No running user game was interrupted, and no
artifact was changed for the retry. Successful retry does not resolve the crash.

The user was asked to load MyNFL1 and leave a player offer open without submitting
for actual read-only source/namespace reply consumption. This remains unverified;
startup metadata alone does not establish a live franchise binding or gameplay
acceptance. Build38817632722 passed at5698281. Franchise38817632849's Ubuntu job
passed; its Windows job remains in progress at the native handshake fixture.

### Repeated boot failure blocks live namespace verification

The single retry also exited before franchise loading with exception0xC0000094
at the identical host0x1423CD9CF and matching logged guest registers. No game
process remained on inspection. Its complete trace is preserved on Deck and
locally as second-installed-boot-crash.log; no further launch was attempted.
Disassembly of the exact privately built executable shows the faulting host
instruction is div rcx after loading the guest divisor at object+0x48. The
nearby pushed return address0x003CAD6A and surrounding instructions match
generated sub_003CAD50 in src/recomp/gen/recomp_0026.c. This is the same guest
routine and failure class already documented as a SOFTDRINK startup issue in
docs/WORKLOG-2026-10-09.md. This establishes the failing code, not the reason
its divisor became zero or proof that current configuration cannot affect it.
No fabricated divisor, exception suppression, save edit or rollback was applied.

Exact source5698281 Franchise38817632849 has now completed successfully on
Windows and Ubuntu, alongside Build38817632722. Those CI/isolated checks do not
exercise this full asset-bearing startup path. The actual game has emitted the
configured image digest, but no loaded-franchise binding/context consumption was
reached in either launch. The pending request to open an offer is superseded by
this startup blocker; a user offer-screen test is not currently required. The
installed batch and205 unchanged-save installation receipt remain preserved.
AI/control/application grants remain off, and no inference or guest financial
write was performed. Resolve or capture the zero-divisor initialization path
before repeating the live namespace/signing acceptance test.

### Deck returned; isolated debugger limits and post-reboot Steam execution

The Deck reconnected with no game running. GDB is installed, but ptrace_scope1
and unavailable passwordless privilege prevent a sibling attachment. A private
startup-zero-divisor diagnostic directory copies the executable/addon/config and
saves and uses the existing isolated validation prefix. Retail/pack asset paths
are shared by symlink for loading; no asset mutation is part of the diagnostic.
The installed Steam wrapper is unchanged.
AI/provider configuration is absent from these diagnostic executions.

The first debugger run followed Wine's32-bit start.exe rather than the64-bit
game. Direct64-bit loader attempts encounter Wine trap handling: one capture
stopped on a trace trap rather than division and is invalid; passing the initial
loader trap terminates the loader. A final trap-aware run progressed into
guest execution but stalled with last kernel return0x00420A77 instead of yielding
a verified divide-fault capture. No object dump from a non-divide stop is accepted
as evidence. The diagnostic-only child was stopped by its exact private runtime
path; no running user game was interrupted. Logs are preserved locally/on Deck.
This approach has not identified or fixed the zero-divisor initialization cause.

Integrity checks confirm all three installed artifacts retain their5698281 batch
hashes. All203 non-partition save/library files still match the installation
receipt, including the configured MyNFL1 UDATA payload. Partition0.img and
Partition5.img differ from the preboot installation hashes; their original
modification times are October15 at22:48:19 and22:48:12 UTC, before this diagnostic
session. Preserve those images; do not roll them back or claim all205 files remain
unchanged after game execution. Exact differences/hashes are retained privately
in save-change-inspection.json. No diagnostic copy replaces a user save.

One subsequent launch of the unchanged installed game through the existing Steam
entry is running as PID214192. Actual session output progresses beyond startup
into STATE9/movie/music, vblank600 and rendered-frame timing; no crash was present
in that observed interval. This is resumed guest execution after reboot, not a
crash fix, complete playability or franchise connection proof. The user was asked
to load MyNFL1 and leave an offer open without submitting for the still-pending
read-only namespace/context check. AI/control/application remain off.

### Actual MyNFL1 read-only binding and player context consumed

The user confirmed MyNFL1's player offer open. On the actual installed5698281
game, the live trace records the expectedf67e6fc1 load-image digest, all720044
MyNFL1 bytes with payload4c8c31b4, and decoded phase3/stage4 at epoch1. Native
volume4061331925/index00000000:00945220 selects the configured UDATA container.
Will Hernandez is observed at slot2371, with Giants table index15. Without any
navigation away, the game logs Franchise handshake reply consumed followed by
the complete read-only signing-context reply. This exercises the production
native consumed-binding/source-path gates, not an authored C-client fixture.

The reply identifies existing player2dd58d0c9bd54e758ae5d9907056d726, Giants and
financial revision1. Its personality and initial relationships match the existing
registry seed's initial_actor output exactly. The configured namespace is
b8d2e88dbe2d4c96804a8c2dff050e19; native consumption validates the four-field
runtime binding rather than logging the raw wire echo. The response reports
ai_authorized=false and write_authorized=false. Observed calendar values remain
raw2004/season0; the registry's logical2026 mapping is explicit configuration,
not proven by the raw display year. History is absent for this player; missing
targets/pressures/QB hits are not treated as zero or used to satisfy promises.

The captured offer decodes to salaries6328000/3796000 and signing bonus6752000,
but preview returns accounting_rejected because contract classification is
missing. Do not weaken that refusal to enable inference/signing. Full opening
liabilities, modern salary/rookie classification and production application remain
unfinished, as do complete active-franchise lifecycle and actual signing/reload.

A read-only query of the configured usage database confirms zero model attempts;
forced-missing credentials remain absent. Actual source hash is unchanged and
registry/database file hashes match the local staged copies exactly. Private
actual-readonly-context-session.log, actual-readonly-context-receipt.json and
actual-readonly-safety-receipt.json preserve the trace, validated assertions and
zero-inference evidence. This completes the live read-only connection milestone;
it does not establish AI-enabled negotiation or financial write authority.

## October15,2026 — Grouped salary classification and accounting checks

The user requested the remaining core work as one batch and selected completed
in-game seasons for minimum-salary tiers. Added explicit game-completed-seasons-v1
export: completed seasons equal the saved one-based career-period counter minus
one; a zero counter stays unknown, and zero-completed-season players stay outside the
veteran import. Annual future floors project one additional completed franchise
season per year, without claiming those seasons have occurred. Modern minimum
tables and the previously approved historical-dollar conversion remain unchanged.
No hidden ratings or performance counters enter salary-floor classification.
docs/simulation-salary-policy.md records the distinction from real NFL credits.

Ledger/store initialization imports declared veteran salary inputs atomically
across the existing league. Immutable bootstrap/actor/history/ownership/cash and
contract balances are preserved. Each team advances one financial revision.
Existing annual credit inputs cannot be replaced even if they produce the same
floor. Duplicate imports are idempotent; concurrent identical requests commit
one group. Partial group deletion/header tampering, unknown/rookie identities,
stale revisions, mismatched chronology/economy and changed membership reject.
An actual authored prepared guest journal blocks the import without mutation.
Recorded classification provenance joins server negotiation accounting; the CBA
table source is not presented as proof of real NFL service eligibility.

The import CLI defaults to an SQLite-backup preview with committed WAL state,
without running schema initialization on the original database. Applying requires
explicit --apply. The exporter refuses to overwrite its output and records the
actual supplied payload hash rather than mislabeling later data as the baseline.

All883 offline Python tests pass in43.952s outside the sandbox for the four
existing local-loopback checks. The earlier sandbox run's four errors were local
socket permission failures; they are not recorded as passing. New coverage checks
restart/idempotency/atomic failure, actor/financial preservation, prepared-work
freeze, minimum enforcement, original-calendar conversion, unknown seasons and
rating-independent salary inputs. No native source or generic sidecar code changed.

Private .local-runtime/salary-chunk/classified.sqlite copies the existing MyNFL1
namespace and imports1806 veterans across32 clubs.264 zero-season players remain
for separate rookie rules. Original database hashb9b6803d remains unchanged;
snapshot-origin verification preserves the existing bootstrap association and
personality seed. All32 club financial snapshots are identical apart from
revision1 to2. The captured Will Hernandez amount422/flags755105796 now returns
eligible_preview, salaries6328000/3796000 and signing bonus6752000. Exact cap
charges are9704000/7172000; Giants first-year roster-based room is79512000.
The context takes0.979s locally. Separate below-floor and over-cap read-only
requests reject before any provider/control call. Full modern opening scope is
not inferred from these roster-based results.

A second private copy tests an offline scripted acceptance, stale-proposal
rejection before the scripted provider, durable preparation, restart inspection,
constructed after-save comparison, settlement and identical retry. It settles
once at revision3, first-year charges221688000, with one scripted provider call.
The constructed after-save is comparison/test data only: no actual game memory
or user save was edited, and this is not native application/save-reload proof.
Private classification-receipt.json, floor-and-cap-rejections.json and
private-recovery-receipt.json preserve the evidence.

A single pinned144-file source/fixture package is prepared for isolated Windows
tests, actual UDATA read-only context including floor/cap refusals, and both
existing native C-client journal fixtures. It preserves the old unused inference
budget/scope and forced missing credentials; it enables no AI, application grant
or remote control renewal. steamdeck.local stopped resolving before transfer, so
Windows validation and installation remain pending. The user was asked to keep
the Deck awake; the running installed game/launcher/database were not replaced.

### Windows CI exposed SQLite handle ownership

At157f3c9 Build38832249074 passed, but Franchise38832249078 failed on Windows:
six cleanup errors reported WinError32 for open SQLite files. A connection's
transaction context does not close its handle. The import preview and several
new test queries incorrectly relied on that context for ownership. Ubuntu/local
success did not establish Windows compatibility; the pending package is superseded.

The preview now explicitly closes both backup handles, including backup-error and
validation-error paths. New test connections likewise commit writes separately
from handle closure. A portable tracked-connection test verifies closure after a
successful preview, stale-input rejection and an injected backup failure, without
depending on garbage collection or Windows cleanup retries. All884 offline tests
pass in45.788s. Salary calculations and imported inputs are unchanged.

The user restored Deck connectivity. PID214192 remains running and is preserved.
The144-file package was rebuilt with the fix and regression; a separate staged
namespace/Windows environment is being prepared at low priority. No installed
game, launcher, live database, user save or AI controls have been changed.

The corrected package now passes its full isolated Windows batch: seven import/
replay tests, six simulation/preview/resource-ownership tests, actual UDATA
read-only context, below-minimum and over-cap refusals, forbidden AI operation,
and both legacy/runtime-bound actual native C-client journal fixtures. Windows
launcher exit0 and child marker passed are recorded in windows-receipt.json.
All144 source hashes match the package manifest. The native checker hash is
ff2118ad850e6fcb0b6ed3399f2d88e9a1558c70f20e4c62bb0970c38fe7e9df.
The separate namespace replays all32 clubs/1806 classified veterans with unchanged
contract balances and original database/identities. Its database hash is
8f64df7947ce77ef10a873b60d92a8536bd6f16f6bb4c697e278760fa79820e1.

The actual-source Windows context returns revision2 and the eligible Hernandez
preview, rejects both illegal offers, preserves personality/source/registry/DB
hashes and records zero model attempts. Credentials remain forced unavailable;
the existing unused budget/scope is copied rather than credited or reset. These
are isolated Windows checks, not updated callbacks in the running game. A guarded
installer is staged to back up and atomically replace only the launcher after
normal exit, preserving all current save hashes and the executable/addon. The
current game remains running; no live package replacement has occurred.

### Salary classification package installed after normal exit

The user confirmed normal exit. The guarded installer completed successfully:
only the launcher configuration changed, selecting the separately validated
revision2 context. All205 current save hashes matched before/after installation;
the executable and addon hashes are unchanged. The previous launcher is backed
up under salary-classification-v1/installed-before-salary-classification.
Private installation-receipt.json preserves the complete save manifest. AI and
guest application remain disabled, credentials remain unavailable, and the
existing unused inference budget/scope is preserved.

At03391e7899cb278349470dbc622e9767f7c1205e both final CI workflows completed
successfully: Build38835081734 and Franchise38835081779, including Windows and
Ubuntu. This supersedes the failed Windows handle-cleanup run. Actual revision2
game callback consumption and native signing/save-load proof remain pending.

The existing Steam entry then starts game PID215039 and the new staged sidecar
PID215081. The log confirms the expected SOFTDRINK image f67e6fc1cb76c9ea and
the same720044-byte MyNFL1 payload4c8c31b4f400e251, read fully at epoch1 from
volume4061331925/index00945220. Held negotiation mode remains0 and guest commits
are unavailable. This launch reached the franchise load checkpoint without the
previous startup divide fault; that intermittent fault is not declared fixed.
The user was asked to leave Hernandez's offer open for revision2 context proof.

### Actual revision2 offer context consumed in the game

The user opened Hernandez's offer. The running game consumed its handshake and
read-only signing-context response game-sign-context-320-88618836-1 while the
screen remained open. It identifies Giants/player2dd58d0c9bd54e758ae5d9907056d726,
slot2371, financial revision2, and returns eligible_preview for raw amount422 /
flags755105796. Cap charges are9704000/7172000, first-year team charges221688000
and roster-based room79512000. The accounting and initialized player context
exactly match the isolated Windows preflight. The game additionally requested
performance context; its saved-history source matches the same payload/slot,
and absent history remains explicitly absent rather than zero performance.

Read-only verification confirms unchanged source payload4c8c31b4f400e251,
bindings98087909746c5743 and database8f64df7947ce77ef hashes. Personality and
relationships are preserved, inference attempts remain0, credentials remain
absent, and both AI/write authorization are false. Private
actual-revision2-context-session.log, actual-revision2-context-reply.json and
actual-revision2-context-receipt.json preserve this actual game evidence.

This completes the salary-classification read-only integration batch. The
matching-checkpoint scope still does not establish full active-franchise
lifetime or complete opening/non-roster/rookie obligations. Native controlled
signing, financial reconciliation and save/reload remain required before AI
application; no user offer was submitted by this verification.

### Early load-attempt invalidation before AI application

The shared load router can exit on allocation/selection failures before reaching
the existing read BEGIN checkpoint. Previously the addon retained an earlier
decoded origin on those paths. A new observation at the existing router entry
0016E540 clears that origin and advances its epoch before any guest table/read
access. It is present in all five generated copies and the interpreter hook,
with identical behavior independent of pack names. It changes no game registers,
return values, offers or save bytes. The generic addon transport is unchanged.

The addon accepts the new application-specific attempt event even when guest
memory is unreadable. It clears the old owned source; late hash completions and
decoded callbacks cannot revive it. A later complete read/input/decode can
establish a new checkpoint. Epoch exhaustion remains invalid. Native state and
production-DLL fixtures cover those cases; interpreter checks verify the callback
works with negotiation disabled and preserves registers. All25 generated load
patches pass idempotency/location checks. The actual local generated cache also
accepts all five new entry observations. All884 Python tests pass in44.050s;
all nine local native CTests pass. Windows/Linux CI is pending.

No new build was installed or tested in the running game. This addresses the
known before-BEGIN failure gap; it does not prove new-franchise creation, every
exit/post-decode failure path, full active-session authority, or production
application permits. Those remain required before actual AI-controlled signing.

### Negotiation behavior and player/agent voice requirements

The user clarified that native offseason free-agency waiting/competition should
remain, along with the normal in-season flow. Low offers must affect opinion;
rapid repeated approaches must consume player-specific patience rather than
permit a free lowball-and-increment search. Early extension discussions and
sourced contract-year/underpayment frustration are core behavior, with actual
holdout participation/resolution needed before claiming gameplay effects. These
requirements are now explicit unchecked worklist items. Existing owned-contract
extensions remain unsupported; no negotiation clock or holdout enforcement is
claimed from the current read-only integration.

Accept/reject/counter already requires a nonempty structured reason. The shared
provider instructions now require one to three short natural sentences in the
player's or agent's consistent voice, explaining the actual concern/change or
agreement. Accepted terms must not be narrated as already signed/saved. The model
must not invent rival bids, stats, promises or applied frustration/cooldown/
holdout consequences. This uses the same decision response, with no extra model
call. All26 negotiation and34 Vertex-provider offline tests pass. Actual generated
voice quality and in-game AI presentation remain unverified; no paid requests or
new runtime deployment were made.

The load-attempt source de1a31c918dfaae2aa5137fc9c8fc3f8d5e71ad1 now passes both
full Windows/Linux workflows: Build38836811528 and Franchise38836811596. This
includes the production Windows DLL invalidation/unreadable-memory fixture and
native bridge checks; the guard remains uninstalled in the actual game.
The later voice-instruction source84a74f0 has60 targeted local tests passing;
its full CI remains pending at this checkpoint. Presentation inspection finds
the existing native preview truncates reasons at140 bytes into a160-byte history
field and clips its small display area. Complete dialogue presentation is now
explicitly tracked rather than claimed from a prompt change.

### Durable offer reactions for negotiation

The user asked to continue toward negotiation. Application still lacks verified
active-franchise lifecycle and a production issuer, so no native writes were
enabled. This batch implements a concrete negotiation behavior: a typed offended
reaction on a rejection/counter now records a bounded team-specific respect loss
alongside the natural-language decision. The engine, not the model, derives the
0.05/clamped/six-decimal offer-reaction-v1 effect. It is an authored simulation
policy, not a real NFL rule. Ordinary bargaining is neutral; accepted offers
cannot be offended, and better later terms do not automatically repair respect.

The dialogue and an explicit offer_reaction marker commit in one SQLite write
transaction. Replay derives the actor effect and requires the matching adjacent
marker. Missing/orphaned/altered effects reject; old readers encounter the unknown
event kind and fail instead of silently dropping the new behavior. Prepared guest
work retains its existing write freeze. Remote shutdown and an injected failure
between the two inserts leave neither dialogue nor an opinion change. Request
retries/restart apply nothing twice, and the generic relationship API cannot
reapply the same respect consequence. Personality, cash, cap, contracts and
financial revision remain unchanged; same-player history IDs guard concurrent
negotiations. In-memory examples now retain and validate their bound actors too.

Captured negative replay required a compatibility fix: the decision's original
relationship evidence may precede its own persisted reaction, while a fresh
checkpoint correctly returns the changed opinion. Such non-authorizing replies
retain historical evidence; identity, personality, performance and financial
revision still match. Acceptances retain complete current-actor matching and
superseded proposals cannot settle. Native validation checks the bounded effect
and refuses malformed claims; opinion metadata grants no application authority.

Private opinion-rehearsal.sqlite copies the classified MyNFL1 namespace without
rewriting its source. An offline scripted first rejection changes Hernandez's
respect0.50 to0.45. The next larger offer receives0.45; its neutral reaction does
not restore it. A restarted captured-request retry preserves the original decision
with the current0.45 checkpoint and no additional scripted call. Original
personality, financial snapshot, source DB, bindings and game save hashes are
unchanged. Two scripted provider calls, zero paid requests; this is not actual
game AI execution. Private opinion-rehearsal-receipt.json preserves the evidence.

All895 Python regressions pass in46.652s before the last injected-write-failure
case; all10 focused reaction tests now pass, along with13 captured-context tests
and nine local native CTests. Final full-suite/Windows CI evidence follows.
Native application, game dialogue rendering, approach limits/verified game-time
cooldowns, extension talks and holdout participation remain unfinished. The
running Deck/game, installed package and disabled AI/control state are unchanged.

Final frozen-source validation passes all896 Python tests in43.017s, including
the injected second-insert rollback and captured historical-reply regressions.
All nine local native CTests pass. Cross-platform CI and actual Windows/game
execution of this reaction feature remain pending; no live inference was used.


## Replacement negotiation screen — complete addon view boundary

The user wants a full replacement negotiation screen. docs/NEGOTIATION_SCREEN.md
now defines the integrated terms/performance/promises/agent-response flow and the
required input ownership. Drawing over the old screen alone is explicitly not a
completed takeover. No new WebView, launcher or generic transport API is needed.

franchise.negotiation-view.v1 now supplies an owned complete context/proposal
frame and the current compact status through the existing named snapshot API.
The retained compact-display ABI remains unchanged. No agent reason, exact annual
schedule, existing promise/counter or sourced performance data is reduced to the
old short display strings. Journal progress preserves its matching context;
submitting again clears the old reply. Existing player/terms/source/screen
invalidation hides or clears it. Renderer calls do not perform I/O or inference;
this data is never an application grant. Missing/older addons and unsuccessful
snapshots clear the entire destination, including partial output from an addon.

The portable signing-shim test now verifies complete owned copies and failed
snapshot clearing; all nine rebuilt local native CTests pass. Windows fixtures
add a maximum-size 65,535-byte UTF-8 response, consumer mutation isolation,
foreign-thread reads, pending submission and stale/new-source visibility checks.
Windows CI is required before claiming those fixtures passed. Previous e8c2240
Build and Franchise AI checks are now both fully successful, including Windows.
No model request, game deployment, UI rendering or contract write occurred in this
chunk. Actual replacement controls/layout, financial completion and real-game
signing/save/reload remain open. The Deck settings and disabled AI are unchanged.


## Read-only replacement negotiation view and controller ownership

The screen renderer and navigation now live in franchise-addon.dll. The game adds
only optional named UI draw/input hooks: gathered packets before guest delivery,
and a caller-owned BGRA buffer before ordinary HUD rendering. No franchise rules
enter the generic host hook or independent engine-sidecar process transport.
The opaque view uses the retained dark palette/Bahnschrift and Contract,
Performance and Agent sections. It displays exact schedules/charges, separate raw
saved period/mode records, explicit missing evidence, full agent reasons, counters
and proposed promises. No hidden metric is permitted. D-pad scrolls full content;
LT/RT change sections; one native B pulse exits. Entry-release handling and held
input quarantine prevent controller carry-through after dismissal/addon failure.

Preview mode defaults off, needs an explicit controller port, rejects simultaneous
AI-negotiation/application startup and holds original signing even without the
addon. It cannot submit a model request or apply a contract. Cached owned pixels
avoid per-frame GDI redraw; no borrowed DLL surface survives module unloading.
Eleven rebuilt portable native CTests pass, including new host filter and content/
navigation checks. Windows fixtures render both1280x800 and1280x720, capture full/
scrolled/missing-data states, and check cache/Back behavior. Their execution and
actual game takeover remain pending; no deployment or save change is claimed.

01afe88 CI passes Linux; Windows caught a real display-ordering issue: a late
read-only context could republish after a waiting proposal intent was consumed.
The signing hold did not release. The host now preserves waiting display state
until the proposal reply; the fixture already exposes this regression. Maximum
frame/UTF-8 ownership and other Windows checks passed in that run. New source
must pass the corrected Windows fixture before this issue is considered verified.

An isolated one-CPU private compiler attempt linked the renderer far enough to
identify its missing user32 dependency (now included), then the reused Wine
compiler prefix failed to create a temporary IL file. Disk has18GB free. This
fixture stage did not touch the running game. Windows CI now runs native checks
and uploads authored screen captures before the longer Python suite, providing a
separate validation route. No control/IAM grant, paid inference, installed game
replacement or financial write occurred. Editor/submit and real signing/reload
remain open.


Initial469406a Windows validation now compiles the production addon renderer and
passes all20 native CTests, including actual GDI frame rendering at1280x800 and
1280x720, one-use Back, ownership/caching, host lifecycle and the corrected late-
preview/held-signing fixture. Authored PNG artifacts were retrieved from run
38842645097. The batched initial inspection finds readable text and complete
response/counter access, but long lines, ungrouped money and a partially clipped
line at a scroll boundary need one correction batch. The source now groups exact
integer dollars, shows total compensation/term, retains fractions without rounding,
uses a shorter reading measure and aligns scrolling to text lines. Raw history
codes remain in the source rather than the player-facing text. UTF-8 speech and
other-controller/mixed-mode rejection checks join the final confirmation fixture.
Final Windows confirmation is pending. The extracted standalone sidecar CI
38677485314 remains successful;469406a Linux engine and Linux runtime checks pass.
No installed game, save, controller mapping or remote control was changed.


Final UI confirmation: fb743f6 passes all20 Windows native CTests, including the
real renderer and extra wrong-port, invalid-port, mixed-mode and UTF-8 checks.
Authored captures from38843271087 were downloaded privately and inspected at both
Deck sizes in the one allowed confirmation pass. Exact grouped amounts/total,
shorter reading measure and whole-line scrolling are readable; no further visual
polish is scheduled. Both Windows and Linux Build38843271009 pass. Linux's full
Franchise AI job passes; the broader Windows job is still running at this entry.
The earlier469406a full Franchise AI38842645097 and Build38842645059 both pass.
The optional host UI protocol is documented in native/game_addon/README.md.

This completes the authored read-only screen/layout/input-fixture milestone, not
actual game integration. The installed executable/DLL and205 save files were not
replaced; the user game remains running. A fresh private game build/package,
normal-exit installation and real Deck offer-screen/controller verification are
still required. The isolated compiler temporary-IL error remains an environment
issue for private packaging; use the established clean compiler setup rather than
assuming this failed stage is deliverable. Editor/submit, actual bounded model
response, complete finance coverage, native application and save/reload remain
open. Do not deploy a DLL alone to an older host that lacks the UI hooks.


## Compiler repair and redesigned contract presentation

The isolated probe Wine prefix has no Windows TEMP variable (`wine cmd /c set
TEMP` reports it undefined). The established compiler prefix reports
C:\users\root\Temp. An explicit Linux TMP/TEMP override did not repair the
probe prefix. The private fixture build now uses the existing initialized
/task/compiler-prefix-clean, mounted from native-05ac4e9, matching the established
private game build setup. Three Windows executables compile successfully there;
the renderer also compiles in two subsequent fresh containers. The previous
D8037 temporary-IL-file packaging blocker is resolved for this compiler setup.
No SDK/license change or game-file replacement was required. The private
negotiation-screen-preview/build.sh and build-screen.sh record the working setup.

The user rejected the plain text presentation. The addon now uses a navy/crimson
franchise layout with a strong player header, vertical section navigation,
right-aligned annual salary/protected-base/cap columns, a distinct cap-room band,
and a dedicated scrollable agent/evidence area. Colors are a generic game palette;
no unverified team identity or branding is invented. Unsupported/ineligible offers
and longer contracts retain the complete scrollable text path instead of clipping
rows or accounting reasons. Rendering remains cached and inside the addon. Input,
financial rules, missing-data semantics and preview-only signing holds are retained.

Current source hashes are checked before isolated Proton execution on the Deck.
Renderer, held-signing and host-handshake Windows children all pass. Proton's
launcher returned0 without forwarding child stdout on the first attempt, so the
runner now captures child logs and checks fresh per-child Windows completion
markers rather than treating that launcher exit as proof. All three child markers
and both existing success messages are verified.24 authored PNGs have correct
1280x800/1280x720 dimensions, including seven-year terms and accounting rejection.
A batched inspection of the actual Proton captures confirms readable tables,
full text/scroll access and the new layout. Private checks-receipt.json preserves
source hashes, results, zero model requests and no game installation. This is
execution of authored fixture programs on the Deck, not the running game.

The previous fb743f6 full Windows/Linux Franchise AI38843271087 and runtime
Build38843271009 now both pass. New redesign CI follows. Actual rebuilt game
packaging, normal-exit installation, live offer-screen takeover, editor/submit,
AI execution and signing/save-reload remain unfinished. Existing saves, installed
runtime/launcher, control grants and paid inference policy were not changed.


## Approved screen — real-game package validation

The user approved the redesigned native screen. At e45a634, Windows/Linux
Build38845005523 and full Franchise AI38845005585 both pass. The private builder
contained the known5698281 overlay on the earlier763c714 staging manifest; all11
differing files were matched byte-for-byte to repository history before a backup
and248-file source upgrade. Existing input/presentation/config sources were also
verified against5698281. The private-only CMake validation block was accidentally
appended twice during staging; configuration rejected duplicate targets before
compilation, and the block was restored to its previous known hash. No installed
runtime was affected.

The actual Windows game, new generic UI hooks and matching production addon now
compile in the established initialized compiler prefix, using one CPU. Isolated
Proton game --validate returns a fresh child completion marker and the explicit
validation success message. EXE SHA256
b1105267f99ac1d89491f610fa64dcfa9a8374ac7d0a7e5131e83716aa8f9506;
DLL5771c92c77b36c8fbda046c28de86bd9adfcf7f75d463377158f4513eb3fe624.
Private screen-package-e45a634 preserves source/backup manifests, build log and
validation receipt. This validates the executable, not actual franchise boot or
screen takeover. All20 matching Windows standalone package tests now execute successfully under
Deck Proton, with fresh child completion and per-test log evidence. Production
addon tests explicitly load the exact DLL paired with the validated game. All249
source files (including the known private validation-only CMake file) are hash
verified. A candidate wrapper adds only SCREEN_PREVIEW=1 and SCREEN_PORT=0,
retaining NEGOTIATION=0, GUEST_SIGNING=0 and unavailable credentials. The package
receipt verifies installed/candidate hashes; the closed-game-only installer
backs up all three replaced files, checks every save hash and rolls back on
failure. It has not been run. The user was asked to exit normally because the
installed game remains running. Actual boot/takeover/controller, editor/submit,
model response and signing/save-reload are still unverified. No installed game,
save, remote control or paid inference was changed.


## Approved preview installed after normal exit

The user reported closed. The installer independently verified the game and owned
service were absent, checked all249 source hashes, completed test/validation
receipts, old installed hashes and candidate hashes, then backed up the game,
addon and wrapper before replacing the matching set. All205 save-file hashes
remain unchanged. The installed EXE/DLL are the b1105267/5771c92c validated pair;
wrapperdf88996c adds preview on port0 while AI and guest application stay off.
Private screen-package-e45a634/installation-receipt.json records the hashes and
unchanged saves; installed-before-preview retains the original three files.
Actual live franchise screen takeover/controller behavior is still to verify.
No control renewal, inference request or financial write was made.


## Live preview feedback — loading and navigation correction

The installed e45a634 game/service started successfully after protected installation.
The user confirms the addon screen works in MyNFL1, but appears after a long wait
and maps horizontal input to the vertical section list while ignoring sticks.
Current logs confirm the pinned MyNFL1 payload and Hernandez context were consumed;
this is actual read-only integration evidence, not signing/AI/save-reload proof.

The correction now publishes a claim-free loading snapshot on offer FSM entry,
before the runtime binding/context response. The renderer retains the approved
layout and fills financial/player data only from the complete verified reply.
Invalid display data cannot leak into a loading snapshot; close/failure clears it.
Up/down on D-pad or left stick selects the vertical sections, LT/RT still select
sections, right-stick up/down scrolls, and horizontal D-pad no longer changes the
vertical list. Entry waits for neutral sticks;16000/8000 hysteresis prevents drift
and repeated held actions. The footer reflects these controls.

All11 portable native checks pass. Actual Windows navigation, loading-render,
host-handshake and held-signing fixture children pass under Deck Proton. The
loading snapshot is tested before any reply and after close; the real renderer
produces loading/context captures at both Deck sizes. Isolated game --validate
passes with a fresh child marker. EXE4d30c13c1b48a52ca9e9ed56962b88dfe9ea53d8d633a096fb1ad6e36d353c38;
DLL1f9fa29e08b63fd6ec2c739a95198bf3fa7eae8dbcac886f7dd43b40f415750d.
The private screen-controls-batch records source hashes/backups and child logs.

The cause of the complete live delay is not yet measured. Existing isolated
service execution was approximately4s; the native path also binds the runtime
before requesting context and collects replies in owner-thread input polling.
New context-roundtrip/largest-poll-gap and loading/context-first-paint diagnostics
will help distinguish collection gaps from request work; they do not claim to
measure pure service time. No AI, signing authority or control renewal was added.
Installation and live verification of this correction remain pending.


## Live timing, receiving records and lazy historical source foundation

The user exited through Steam. The combined6c79e74 controls/loading package
installed with all205 save hashes unchanged and unchanged preview-only wrapper.
The game and read-only service were relaunched through the existing Steam entry.
Windows/Linux Build38847528205 and Franchise38847528242 pass. User confirms Dart's
passing stats appear; Hernandez has no rows. Fresh actual logs show loading
first-paint15–29ms, context roundtrip1862–1949ms and largest owner-poll gaps18–37ms.
Thus these captures do not support animation-paused polling as the main remaining
delay; request work dominates. No pure-service timing claim is made.

Read-only MyNFL1 inspection finds1521 players with history pointers and549 without,
including Hernandez. Dart slot987 has nine supported records, including2272
passing yards/15TD/5INT. Nabers slot998 has two periods with saved receiving codes
previously excluded by the reader. Original REC/YDS/TD selectors and A8A510
descriptors map native fields2E/4F/3E to history12/13/14 in both pinned retail
73105b17 and SOFTDRINKf67e6fc1 images. New mappings/export/UI allowlisting preserve
Nabers'109/1204/7 and18/271/2 separately, signed yards and missing fields, with no
ratings or aggregation.29 focused Python checks and11 native checks pass; all897
Python regressions pass when localhost web/TLS tests run outside the sandbox.
The first broad run's four errors were sandbox port-binding denial, not assertions.
This new receiving mapping is source-only and not yet deployed to the live service.

The user requested real-player historical imports, then specified lazy year API
requests. Documented nflverse APIs supply season CSVs. A private bounded2025
roster/stat/snap audit retains URLs and SHA256s.1753 of2070 game identities have a
unique name-and-DOB-component match;317 remain unmatched. Hernandez has396
offensive snaps across seven regular-season source game rows and8 special-team
snaps; starts are not established. No imported data was attached to actors or saves.

A small franchise-owned SeasonCache now requests only the selected dataset/year
on a background worker, deduplicates requests and persists immutable source bytes
with hash/URL/attribution/license. Startup is inert; restarts reuse pinned cache.
Failure, corrupt cache, future year and arbitrary URL/dataset requests do not
become invented zero stats or unbounded retries. Four authored offline cache tests
pass. It is not yet wired into Bridge, player identity association or the UI;
external history remains separate from game records. docs/HISTORICAL_STATS.md and
the worklist identify the remaining integration. Engine-sidecar transport, cloud
controls, paid inference, personalities and financial records were unchanged.


## Game-parity fallback rule and context request performance

The user limited external imports to missing complete in-game seasons and metrics
the game itself can produce/display after a full season. Existing complete seeded
history also takes priority. Missing metrics after a full game season do not
reactivate external supplementation. The cache now requires a current server-owned
completed-game-season count on each poll and rejects nonzero/unknown counts; snap
counts are removed from its fetch allowlist. Five authored cache tests pass. No
external data is connected to the game or model yet; the eligibility/metric gating
and source association remain explicit integration requirements. Hernandez snap
audits are research only and will not become unsupported UI/model metrics.

Fifth-year options are explicitly in scope. RookieScale currently records only
first-round eligibility; exercise/decline, supported pricing/deadline/protections,
cap/cash effects and durable game save/reload remain unchecked. Nothing adds an
automatic fifth salary year or silently exercises an option.

An actual MyNFL1 cProfile identifies two ledger replays per context: one for
checkpoint/player context and another for guest cap preview. The new path computes
both in one fresh SQLite read snapshot, retaining ownership/draft-right checks,
contract inventory, revision, every actor/posting check and post-commit data-version/
file-version freshness. Salary classification is validated once per read snapshot
and reused across its replayed events; direct historical replay still validates it.
No persistent financial cache or public schema/index changes were added. An index
experiment touched only a disposable local profile database and was not shipped.

Regression tests compare the combined result to the original standalone preview,
require one replay and unchanged bytes, and retain rejection of null/incomplete
guest offers. All904 offline Python tests pass, including localhost web/TLS checks.
Eleven portable native tests passed for receiving support. The combined native
Windows screen/navigation, loading, handshake and held-signing fixture children
pass under Deck Proton.

On actual Deck Windows CPython with private MyNFL1 database copies, before samples
are1.827856/1.706341/1.837075s and after0.935895/0.811568/0.785956s: median improves
1.827856→0.811568s. Replies are exactly equal except the three added receiving
missing-metric names. Both source and private database hashes remain unchanged;
model/cloud calls are forbidden. Targeted Windows tests pass:15 context-bridge,
8 reconciliation (one platform skip),7 classification,8 performance-export and5
lazy-cache checks. Receipt/source hashes and child completion are retained in
private context-fast-batch. This is an isolated service measurement, not a new
installed-game performance claim. Rebuilt game validation/package installation
follow; AI and guest writes remain off.


The first isolated game-validation attempt printed [TEST] Validation passed but
did not produce a child completion marker before the120s timeout. It is not
counted as a completed validation. The exact isolated process exited; the user
game was not interrupted. One retry uses an explicit Windows batch file with
errorlevel checking, fresh completion marker and explicit batch exit. That retry
exits0 with marker validated and the validation success line. This establishes
completion for the retry, not a claimed general shutdown fix. Matching rebuilt
EXE95d0cc77abe82d876f727f2ae873cf18efe30cd591d6f26e9bb12390ec6130e2 and
DLL75ef2cb9875d9420e42f2bee83952df8617a28dce4b1ef6925c25179afa571e9
are pinned in the receipt.

The package uses a copied Windows Python runtime with the new service import
path, while retaining the original live financial database, registry, missing
credentials, budget and disabled AI/application modes. The historical cache is
not connected, so there is no runtime external-stat request or unsupported-stat
display. The receiving mapper and faster authoritative read path are packaged
together to avoid sending new metric names to an older UI allowlist. Normal-exit
installation and actual live speed/receiving-page verification remain pending.


### Combined faster-context / receiving package installed

After the user confirmed Steam showed Play, the protected installer verified the
closed runtime and installed the matching EXE/DLL above plus wrapper
2b3d723eba8a74d3dabdfd38c5e729823b420459bf544f07cd07419c9122f47b.
All205 save hashes remain unchanged. The private installation receipt is retained
in context-fast-batch. Its base source_commit e45a634 plus working_tree=true
identifies the packaging base, not a claim that e45a634 contains these changes;
the verified source manifests correspond to committed implementation2733c99.

The existing Steam entry launched successfully. Process inspection confirms the
Windows sidecar now runs from context-fast-batch/context/python/python.exe while
using the original salary-classification-v1/context/franchise.sqlite and usage
budget. Startup logging advances through the game boot. AI, guest signing and
external-history integration remain disabled. Actual offer-screen timing and
Nabers receiving rows await the user's MyNFL1 screen transition. Build CI
38849831676 completed successfully; Franchise AI CI38849831828 was still running
at this check. This installation does not establish signing/save-reload acceptance.


### Receiving protocol mismatch reproduced and corrected

The user reported being ejected from the negotiation preview after installation.
Live logs show the game continues running, hello is consumed, then the host marks
the transport unavailable and clears its display. The service process disappears
after that failure. The renderer allowlist was updated for receiving history, but
the independent native contract-response validator still supported only the old
ten history metrics. Every new service reply names receptions, receiving_yards
and receiving_touchdowns either as rows or missing coverage, so even Hernandez's
empty-history response is rejected. Host validation aborts its owned peer; this
is not evidence of a Python crash or model request.

A temporary C++ harness using the exact isolated Deck Windows service reply
reproduces `Invalid missing history metric` with the old committed validator,
then accepts the same bytes with the corrected units map. The new authored
protocol tests cover all13 missing metrics for empty history, present receiving
rows with signed yards, and wrong-unit rejection. All11 local native CTests
pass. The earlier Franchise AI CI38849831828 failed in the Windows native
saved-signing integration step; the Python-only checks had not exercised this
application validation boundary. Private Windows rebuilding and deployment are
pending; no running game files have been replaced during diagnosis.


The corrected private Windows build completes. All five Proton child checks pass
(protocol, navigation, loading-render, host-handshake, held-signing), launcher
exit0 plus fresh passed marker. Isolated game validation also completes exit0
with fresh validated marker and validation success line. Candidate EXE
de1b532c3a9301aaf34958702cfbbf1eb1c01df0f8868a9870b4412e82dcc2ab and
DLL8a0c3203e84597543753e6e7890a9c97b2f03e509a207db4b35595b7ce1e6a7e
are pinned in receiving-validator-fix receipts. The protected two-file installer
is staged, retaining the installed faster service, wrapper, database and controls.
Installation awaits normal exit; actual game receiving-page confirmation is open.
CI for56ce66e was dispatched as Build38850554580 / Franchise38850554573 and was
still running at this check.

### Installed validator fix and external Deck test control

The user confirmed the game was closed and requested tooling that can control it
for actual tests. The protected installer installed the56ce66e EXE/DLL pair;
all205 tracked save hashes were unchanged at installation. The existing launch
wrapper, faster service, database, registry and disabled AI/signing settings were
retained. Both native fix CI runs completed successfully: Build38850554580 and
Franchise38850554573, including the Windows native integration that failed
before the receiving validator correction.

Added tools/game_test_control.py and docs/GAME_TEST_CONTROL.md. This is a small
Linux/Proton runner, not another daemon or launcher. It identifies one actual
NFL2K5.exe by executable and configured runtime root, supports the existing
optional file-input hook, and provides an explicit existing-keyboard-mapping
backend. Cooperating drivers share a nonblocking input lock. Batches are bounded,
pending queues cannot be overwritten, keyboard keys are released in finally,
and queue consumption is not misrepresented as menu success. Log assertions use
an explicit pre-action byte offset and fail on restart, truncation or timeout.
Nine asset-free tests pass, covering stale evidence, pending input, malformed
batches, process identity, restart/truncation, key release and input serialization.
The Linux lock case is intentionally skipped on Windows.

The game was already running again when private queue enablement was attempted;
the guard refused to change its launch configuration. A normal X11 window-close
request did not stop it, and no process was force-killed. Rather than ask the user
for another restart, actual tests used the explicit keyboard backend. The launch
wrapper remains byte-identical and no file input queue was enabled. Ordinary X11
root screenshots returned black on this Gamescope session, so the driver instead
uses the installed gamescopectl screenshot command and requires a complete new
PNG. It captures on demand, not continuously, and adds no host/renderer code.

Actual process230141 was driven from Dart's Agent page to Performance, showing
14games,86 rush attempts,487 rushing yards,9 rushing TD,339 pass attempts,
216completions,2272passing yards,15passing TD and5interceptions. The live native
context log reports1.278s roundtrip and18ms largest owner poll gap. This is live
IPC/service/collection evidence, distinct from the earlier0.812s isolated median.
The driver backed out without submitting, used the observed position selector
and player list, selected Nabers, inspected his action menu, chose Re-negotiate
Contract, waited for a fresh context reply and selected Performance. A first
wait correctly timed out at the intermediate action menu; no following input
was blindly executed after that failure.

The actual Nabers screenshot shows separate saved records:109 receptions,
1204receiving yards and7receiving TD in one period, and18 receptions,271yards,
2receiving TD in another. These are not summed, assigned invented season labels,
or represented as imported/current-season totals. Dart and Nabers both render
through the corrected native validator; no model request or contract submission
was made. Private screenshots/receipts remain in .local-runtime/game-test-control
and the corresponding Deck directory; no retail assets are added to Git.

The user also clarified that signed players must be able to negotiate early
extensions, pay reductions instead of release, and supported cap restructures.
WORKLIST now explicitly includes these distinct proposals, player consent where
required, current-year relief/future commitments, and preservation of earned
money, guarantees and bonus layers. The current signed-player rejection is an
unimplemented feature, not product policy. This tooling milestone does not remove
that guard or claim extension/signing/save-reload completion.

Post-test read-only verification matches both installed binary hashes, the
unchanged launch wrapper and original franchise database hash. All203 nonpartition
files in the205-file save manifest are byte-identical, including both logical
MyNFL1 and its physical UDATA payload. Partition0.img and Partition5.img hashes
changed during the running session; they are preserved, not restored or claimed
unchanged. Their internal changes were not attributed, and this is not a
save/reload acceptance test. The live log has zero transport-unavailable events
and two valid context replies, with correct Dart slot987 and Nabers slot998,
AI/write authorization false. Nabers's actual roundtrip is1.146s with18ms maximum
owner poll gap. The game is left on Nabers's Performance screen, with no held keys
or background test driver.


### Football stat and annual contract tables

The user rejected the raw Record/unit/missing-field text wall and requested the
same tabular treatment for Contract. Both sections now use aligned native tables
inside the approved navy/crimson layout. Performance groups Receiving, Passing,
Rushing and the mapped Defense counters, with familiar abbreviations and separate
saved period/mode rows. It does not invent calendar years, aggregate duplicate
entries, fill unknowns with zero, or display speculative pressure/QB-hit columns.
Games-only observations remain visible. The user-facing missing-field inventory
and Record numbering are removed; one short source/unknown-value note remains.

Contract uses one annual row whenever decoded offer terms exist, including
rejected/active-player offers and longer terms. It shows base salary, guaranteed
base, supported bonus cap and cap hit, plus total/bonus and supported cap room.
Unavailable preview figures are dashes; no new financial authority, proration
policy or active-contract settlement is introduced. Existing liabilities are not
replaced. Long tables scroll; Agent prose and navigation stay intact. Exact
fractional cap amounts remain exact, with a compact fraction in the cell.

Eleven local native CTests pass. Tests cover distinct periods/modes, repeated
entries without summing, negative yards, known zero, unsupported metrics, and
annual terms with and without a cap preview. The first Windows/Proton round
passes protocol/navigation/render/handshake/held-signing child checks and renders
both1280x800 and1280x720. One combined visual review covers Contract, receiver
Performance, rejected Contract and mixed-category Performance. A single final
batch removes speculative Defense headers, retains games-only observations and
compact exact fractions, and corrects a synthetic yard-unit label. The source
uses existing design context because the Impeccable launcher lacked execution
permission; no missing product/design brief was invented. Final confirmation and
protected addon-only package preparation follow. The running game is unchanged.

The user's subsequent requests expand this batch to calendar-year labels and
physical/injury information. YEAR now uses the pinned franchise baseline year
plus the retained native calendar candidate offset; the raw game year stays in
the evidence. New optional franchise_season_year and player_profile fields are
strictly validated at the native reply boundary, with compatibility for old
responses. Actual saved readback resolves Dart to2025 and Nabers to2024/2025.
Their saved physical values decode to74in/225lb and72in/200lb respectively, both
age23 at September1 of the configured2026 season. Invalid/missing DOB or height
remains unknown. No real wall-clock aging is used. Record-layout field provenance
is the pinned mod-editor reference already credited in HISTORICAL_STATS.md;
no third-party source code was vendored.

The header shows saved height/weight/season-start age; the sidebar identifies
injury tendency as insufficient recorded history. Injury history/availability
capture is not yet connected, so an injury-prone/durable assessment is neither
invented nor derived from hidden injury ratings. The native profile validator
currently refuses nonnull injury assessments. All915 Python tests pass after
these read-only metadata additions. Local native tests passed before the final
additional profile-validator rejection case; synchronized Windows checks follow.

The worklist and screen design now require each remaining negotiation system to
ship its relevant sourced state, comparisons, usable controller actions,
explanations, pending/error handling and persistence verification in this screen.
That is a delivery criterion, not a commitment to add unsupported placeholder
controls now. Backend-only progress is not a finished player feature.

The final expanded Windows package passes all five protocol/navigation/render/
handshake/held-signing fixture children with a fresh passed marker and launcher0.
Isolated actual game validation exits0 with a fresh validated marker. Windows
CPython tests pass:15 signing-context,10 performance-export and5 snapshot checks.
Both native saved-signing integration variants (ordinary and runtime-bound) pass
against the updated service, using authored files/providers with zero paid model
requests. This specifically exercises the real native reply-validation boundary
for the new calendar/profile fields.915 Python regressions pass; no further
functional changes followed those checks.

The combined final visual confirmation checks Contract and receiver Performance
at1280x800 plus rejected Contract and mixed-category Performance at1280x720.
Calendar years, exact columns, missing-value dashes, physical profile and injury
unknown state render without overlapping navigation/footer. No more polish loop
is planned. New EXE06fb67cc03201073cc10dbc17504ff98c97a8ff412cffb680b1ab8487a32d74e
and DLL5e391494a3db2032f1e9c774ddac95e4e82f14d3d94f96fcb06a3ccd9f19ba11
are pinned in private football-profile validation receipts. The service has its
own verified copy of the289-file source set and Windows runtime, with the
original live ledger/usage database and disabled controls preserved. Installation
and actual in-game verification still require normal game exit; previews are
authored renderer fixtures, not a claimed installed-game screenshot.
