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
