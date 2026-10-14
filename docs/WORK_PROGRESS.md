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
