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
