> Connection core extracted to [Engine Sidecar](../addons/engine-sidecar/README.md).
> The franchise wrapper retains launch policy, grants and contract/result validation.
> Historical pending notes below must be read with WORK_PROGRESS.md runtime evidence.

# Franchise sidecar protocol 1

`franchise.bridge.Bridge` is the injectable request handler.
`python -m franchise.sidecar --database PATH --provider vertex` runs it over
stdin/stdout JSON lines using Application Default Credentials and the required
remote switch. `--provider offline-fixture` is an explicit synthetic rejection
fixture with no cloud calls. The database must already exist. Native integration
remains under development. Never send cloud
owner credentials through this protocol or expose it as a public server.

Every request has `protocol: 1`, nonempty `request_id`, and `operation`.
`hello` has only those fields and verifies remote AI access. `preview` additionally
requires `team_id`, `offer`, `expected_revision`, and `timeout_ms`. `negotiate`
requires those fields plus `personality`, `performance`, and `relationships`.
An offer contains exactly `player_id`, integer-list `salaries`, and integer
`signing_bonus`. Timeout is 1–60000ms. State must already exist in the durable
store; clients cannot bootstrap balances through the handler.

Responses contain `protocol`, `request_id`, `result`, `error`, and `detail`.
Errors include `protocol_mismatch`, `ai_disabled`, `timeout`, `state_rejected`,
`invalid_request`, `response_too_large`, and `service_failure`. No automatic retries or inference on
failure. Retry the same recorded request/terms for the same committed result.
An unrecorded failed request requires fresh state/history before resubmission.

Preview consumes no money and remains available with AI disabled. It grants no
reservation or permission to bypass final cap enforcement. An expired inference
cannot commit after returning; this does not cancel provider network work already
in progress. The process transport runs one inference worker and has no waiting queue: additional
negotiations receive `busy`. Preview requests remain independent of that worker.
Frames are limited to 65536 characters; oversized input closes the channel.
EOF/broken output marks the client disconnected and denies subsequent commits.
Provider network work may finish before process exit. Clients must keep input open
until receiving their response. Stdout contains only protocol responses.
A native pipe client and actual game-thread integration are still pending.


## Game-facing proposal path

`negotiate_proposal` accepts the same fields and optional promise goals as
`negotiate`, except return signing is currently unsupported. It requires the
remote AI grant and uses the same bounded worker, request/token budget and
connection/deadline checks. The native host denies it before a successful hello.

Accepting eligible terms returns `outcome: "accepted_proposal"`,
`decision_mode: "proposal"` and `proposal_preview`. It records dialogue/evidence,
without changing cap charges, ownership, cash, financial revision or contractual
promises. It returns no signing `charges`. Counter/reject/accounting rejection
also carry proposal mode. Durable preview replay must match its historical
financial state; recording acceptance rechecks cap/minimums and global ownership
inside the write transaction. Accepted retries revalidate current affordability,
ownership and revision without calling the model again. Changing terms or
reusing the request in the committing mode rejects.

A proposal is neither a reservation nor permission to write guest memory. No
proposal-to-guest-commit operation exists yet. Actual integration must verify the
active save/player/calendar and terms, recheck remote control/state at commitment,
confirm guest effects and reconcile/save/reload before recording a signing.
Do not use the existing auto-committing `negotiate` operation at the guest judgment
boundary: it is an independent-engine operation and can commit before the game.
The native validator rejects signed/charge-bearing proposal replies and checks
the proposal mode. An optional `contract_format: "original_fxg_v1"` is supported
only for `negotiate_proposal`. It requires submitted salaries/bonus to encode
exactly in the observed game format before inference. Replies retain canonical
mapped `guest_offer` words and `guest_counter` words (or null). An unrepresentable
counter remains the player's original demand with ineligible validation; it is
never rounded into different terms. Financial checks still apply to encodable
counters. The format and encodings persist in dialogue and are checked on replay;
the same request ID cannot switch formats. Native validation reconstructs the
exact salaries and annual charges. These mapped words do not authorize guest
writes or preserve unrelated bits in a live offer context.

The native validator also checks
acceptance preview/evidence revisions. Guest commit/recovery remains unfinished.

`negotiate_proposal` also accepts a captured-screen request with only protocol,
request_id, operation, observation, guest_offer, expected_revision, timeout_ms,
and optional promise_goals. The observation and raw offer have the same shapes
as signing_context. The server requires fresh remote access, reconciles the
pinned legacy checkpoint, derives persisted personality/relationships and saved
performance, and requires an eligible exact-format financial preview before
inference. Clients cannot add or override actor, performance, team or offer data.
The service then uses the existing proposal-only path with original_fxg_v1.

Successful replies add signing_checkpoint; native validation checks that read
checkpoint and the proposal's matching source evidence and exact offer. Dialogue
persists through the ordinary proposal path. On replay the checkpoint is freshly
read and may include updated dialogue history, while the recorded proposal is
reused without new inference. A reply exceeding the pipe frame reports
context_too_large; dialogue may already be recorded, but no contract is committed.
This variant does not resolve active-save selection or authorize guest writes.

## Native candidate

`native/franchise_bridge` builds a standalone Windows C++17 transport check.
`PipeClient.submit/ready/take` runs pipe I/O asynchronously; one request at a time.
The smoke check explicitly selects the offline fixture. Build and execute through the
Windows CI steps or `tools.check_native_bridge`. This is transport evidence only.
Guest hooks, JSON result validation, production launch/authentication, lifecycle
placement and reconciliation with actual saves remain required.

## Explicit manual path

`manual_sign` uses the preview fields plus `decision_mode: "manual"`. It commits
through the authoritative signing validator with a clearly labeled manual story.
It requires neither inference nor an enabled AI grant, but still rejects cap,
rookie, ownership, stale-state, expired-request and disconnected-client failures.
Clients must deliberately select this operation; AI errors never trigger it
automatically. This engine path is not yet connected to an actual game UI.

The native transport compiled and executed on Windows at `dd1ed9e`, CI run
38464795249. That revision verifies handshake/preview/dialogue/restart and launch
failure exits. The expanded manual-signing/cap-rejection native fixture requires
its own subsequent passing Windows run. Neither fixture exercises the actual game.

Native sidecar ownership uses a Windows job assigned at process creation, with
termination on final job-handle close. Windows 10/Server 2016+ required. See
[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
and [UpdateProcThreadAttribute](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute).
The abrupt-parent-exit fixture requires Windows runtime evidence before this
implementation can be treated as verified.

Offers may optionally include `guaranteed_salaries`: annual integer base amounts
fully protected for skill/injury/cap termination at signing, bounded by annual
salaries. Preview reports their base total. Manual and negotiated transactions
preserve them. Conditional guarantee clauses and release settlement remain pending.

Vertex sidecar mode accepts `--impersonate-runtime` for the configured keyless
runtime account using authorized source ADC and short-lived credentials. No
service-account key or owner-CLI fallback is used. Local credential/schema tests
do not establish live impersonation permission; IAM Credentials API, authorized
source identity and target-account impersonation grants still need verification.

The native client now validates response envelopes before returning them: exact
fields, protocol, matching request identity and consistent success/error shape.
Duplicate JSON fields and excessive nesting reject. Malformed replies terminate
the transport. The parser uses checksum-pinned nlohmann/json v3.12.0 with its MIT
license retained. Operation-specific result/financial-field validation remains
required before any game-memory write can be enabled.

Native result validation checks handshake shape, preview revision and charge term,
submitted offer/guarantee identity, decision outcome/action and manual mode. Money
must be integer or canonical reduced rational charges; floating-point money rejects.
This does not independently calculate cap usage or authorize guest writes. Real
state reconciliation and save/readback remain required.

Native `PipeClient` requires explicit `ServiceMode::OfflineFixture` or
`ServiceMode::VertexRuntime`. Runtime mode launches Vertex with runtime
impersonation; no owner or scripted fallback. AI startup failure leaves the
sidecar's financial/manual service available with `ai_disabled` for AI requests
and a generic stderr diagnostic. Manual signing remains a deliberate operation.
Live runtime authentication and game integration remain unverified.

### Nonfinancial promise proposals

Protocol-1 negotiate requests optionally include `promise_goals`, an array of exact
objects with `goal_id`, `metric`, positive integer `target`, integer `importance`
(1-100), `window` and `source`. Supported metrics: touches (carries plus receptions),
starts, receiving/rushing/passing yards and team wins. Omission means no proposed
goals. These terms create no salary, bonus or cap charge.

Accepted/rejected model responses use null promise_goals and preserve the proposal.
Counter responses specify a complete array, including [] for explicit withdrawal.
Responses cannot silently discard a nonempty proposal. Recorded events retain
`promise_goals` and optional `counter_promises`; signed events commit goals with the
financial transaction. Retry request IDs must match both money and promise terms.
The native/game/browser interfaces do not yet present promise controls, and actual
game-counter instrumentation and automatic story consequences remain unfinished.
Source-backed promise scoring and explicit bounded relationship updates are available
in the engine; they do not prove real-game observations.


### Saved player context

A protocol-1 `player_context` request includes `request_id`, `team_id`, `player_id`
and `timeout_ms` (1–60000). It requires a classified player and a live local
connection, but no remote AI grant. The result contains `player_id`,
`financial_revision`, `initialized`, `personality`, `relationships`,
`agreed_promises` and `promise_history`. Uninitialized legacy actors return null
personality/relationships; reads never create or rebind them. Initialized actors
return the saved objects. Signed agreements contain an agreement request identity
and typed goal array. Native validation checks identity, revision types, actor
containers and saved goal definitions.

Native negotiation validation also compares the submitted promise array with the
recorded echo and validates complete counter arrays, including explicit withdrawal.
These checks protect client response interpretation; guest-state writes still
require reconciliation and real save/readback verification.

The asset-free Windows pipe fixture at fb62cfd fetched this context after signing,
compared it to the authoritative database and required the same result after
client/sidecar restart. Workflow 38479010675 logs confirm execution. This synthetic
fixture does not establish a game menu, game hook or playable Windows build.

Player context includes the latest ten chronological `negotiation_history` events,
`negotiation_history_total` and `negotiation_history_has_more`. Older stories remain
stored and available to the full history store read; the companion must label the
recent view rather than imply it is the entire history. Native validation checks
coverage metadata when present. This bounds event count, not complete response byte
size: individual evidence/promise payload bounds and browser pagination remain work.

Native player-context reads serialize-check the complete response against the 64 KiB
pipe frame limit. Oversized context returns `context_too_large` with null result;
records are retained, no inference/financial mutation occurs and later requests
remain usable. History pages can retrieve stories separately through authenticated
HTTP, but large actor/promise payloads still require explicit UI handling. This read
check does not claim byte-size guarantees for every operation or request identity.

### Explicit supported manual release

Protocol-1 `manual_release` requires request_id, team_id, player_id, expected_revision,
timeout_ms, decision_mode=`manual`, complete scope and discount objects plus a
payment_year_offsets array. Scope is the sourced PreseasonReleaseScope schema with
ISO dates and unique explicit exclusions; discount includes declared league_year,
exact annual_rate and rate_source. Unsupported/missing facts reject. It requires local
connection/deadline validity inside the transaction and calls no model/remote AI grant.
Result contains decision_mode, player_id and release {financial,cash} original receipt.
Native validation checks revision progression, player removal/archive identity, exact
charges and nominal/paid/unpaid totals. This does not independently calculate CBA
posting rules or grant guest-memory write authority. No game/browser release UI exists.

### Explicit supported manual assignment

`manual_trade` requires protocol1, request_id, seller, buyer, player_id,
seller_revision, buyer_revision, timeout_ms, decision_mode=`manual` and complete
PreseasonTradeScope JSON. Dates must be canonical YYYY-MM-DD and exclusions a unique
array. It calls no model and needs local connection/deadline validity at final paired
commit. Result contains manual mode, identities and `trade` receipts keyed by each
team, each {financial,cash}. Native validation checks both revisions, one recipient
owner/no seller owner, exact charges/cash totals, unchanged scope and identical shared
assignment archives. These are response integrity checks, not independent NFL/game
reconciliation. No native/game/browser assignment controls are implemented.

## Explicit manual preseason restructure

Protocol1 `manual_restructure` requires request_id, team_id, player_id,
expected_revision, timeout_ms, decision_mode=`manual`, converted_base (positive
integer money), and complete scope. Scope fields are league_year, amended_on,
first_regular_season_game, current_year_earned_base, healthy, consent,
renegotiation_eligible, exclusions, minimum_source and source. Dates must be
canonical YYYY-MM-DD; exclusions must be unique strings naming the supported
calculator's exact excluded terms. No input is inferred from ratings or dates.

The operation uses stored annual floors and durable amendment validation. Local
connection/deadline checks run initially and inside the final write transaction.
AI shutdown does not prevent explicit manual financial operations; these make no
model requests and never obtain an AI grant. Replies contain decision_mode,
team_id, player_id and restructure `{financial,cash}`. A retry returns the saved
receipt rather than restoring old state. Unsupported repeated conversions reject.

The native response validator checks identity/revision, retained ownership,
source scope, unchanged term/original bonus, converted base and guarantee delta,
new layer allocation, annual floors, unchanged nominal/paid history and cash
posting totals. The asset-free Windows `--restructure` fixture also compares
receipts across restart with durable engine state. These checks are not actual
guest synchronization or an independent complete NFL cap implementation.

## Saved player contract inspection

`player_context` also returns this player's `contract_accounting`, separately from
personality and initialization. Null means no saved contract for this team; it does
not mean zero salary, a free agent, or an observed game roster status. When present,
the view identifies active, released or assigned engine history, saved terms and
bonus layers, explicitly scoped annual charges, and this player's known cash and
guarantees. Unknown cash coverage remains null. Other players' obligations and
whole-team cash records are excluded.

The authenticated `/api/player?player_id=...` endpoint shares this read-only view.
It reads one freshly validated engine snapshot and does not initialize actors or
change financial revisions. Source accounting still requires real game import
and reconciliation; browser display and actual guest roster verification remain
separate delivery requirements.


Manual release, trade and restructure receipts are checked against the 65,536-byte
native frame capacity, including the complete reply envelope, JSON escaping and
newline, inside the held database transaction. An oversized reply returns
`response_too_large` with null result before ownership or event writes. Historical
retries validate the original receipt without restoring old ownership or changing
current finances. Direct engine calls retain their existing unbounded receipt
shape; this check is imposed by the native Bridge boundary.

Full lifecycle receipts still include team cash and financial snapshots. A
synthetic 53-player roster with 30 released agreements produces a 70,171-byte
release receipt, so the current native protocol cannot support that state through
these operations. Clients can opt into the compact receipt format described below. Full-format
receipts retain this capacity limitation; the guard prevents unreadable commits.


Release, trade and restructure requests may include `receipt_format: "target_v1"`.
The successful result echoes that exact format. Each participant contains team
financial revision, all annual cap charges, the complete signed-player list and
only the affected player's lifecycle archive. Cash contains its revision and
complete team nominal/paid/unpaid totals, the affected obligation and an
`other_obligations` summary with count and nominal/paid/unpaid totals. The native
validator binds the target cash to its lifecycle archive and checks target plus
other cash against all team totals. Counts and money use nonnegative integers;
partial, substituted or unexpected compact formats are rejected.

Projection uses the exact fresh or historical stored receipt, and the complete
projected reply must fit before commit. Full database receipts and event replay
are unchanged. The compact request can retry a full-format original transaction,
or vice versa, because receipt format is a transport choice, not new financial
terms. A large affected archive or ownership list can still exceed capacity and
reject safely. This is a bounded transaction receipt, not a complete league
reconciliation or proof of guest-game posting.

Compact release cash must retain the original obligation ID, player and settled
payment history; release cannot increase its nominal cash liability. Compact
legacy trades bind original, seller and buyer records to `contract:<player>` and
conserve nominal cash while preserving the seller's allocated payment history.
Generation assignments retain their explicit source and destination identities.
Matching wire/archive copies alone do not satisfy these provenance checks.


## Saved historical performance input

For a pinned snapshot, `tools.export_player_performance.saved_player_performance`
returns the player's stable ID and named saved history for the performance field.
It validates biography/calendar bindings first. Records retain source entry,
raw mode and candidate calendar year; it does not aggregate periods or claim
played/CPU/fast-sim coverage. Deleted records, unknown bit30, unmapped codes and
negative counts are excluded with counts; signed yards remain valid. Missing
history/metrics remain unknown. Historical sacks retain raw half-unit counts and exact half-sack values, with
the descriptor/NFL corroboration identified as a historical inference. This does
not establish live sack telemetry. Tackles, targets, pressures and QB hits are
still unmapped and are not manufactured.

Negotiation rejects a supplied performance player_id belonging to another player.
Provider instructions exclude these historical records from salary-credit and
promise scoring. Export is not proof of the active game/save or authority to
negotiate/sign; the real guest bridge still needs verified snapshot selection,
calendar/revision reconciliation and sourced financial classification.


## Native held-offer integration (staged, not delivered)

`NFL2K5_FRANCHISE_NEGOTIATION=1` is an explicit experimental native switch. It
requires the pinned save/bindings/revision plus saved-performance and guest-offer
inspection configuration. It does not enable remote AI, supply credentials, renew
a control grant or bypass native/service budgets. The installed runtime remains
unchanged with this mode off. The incomplete commit path prevents enabling it as
a playable delivery.

When enabled, the optional franchise DLL defers the shared native signing routine
before retail judgment, and also before the bypass path can commit. The thin host
shim only forwards a private named event. The original routine uses its existing
failure cleanup, preserving its caller frame. In SOFTDRINK v0.6 the shared routine
has a redirected roster-limit call and is interpreted, so the same two boundaries
are registered through the existing interpreter hook API only for that pinned
XBE hash. Policy stays in the optional DLL; the reusable process/pipe core has no
franchise policy or new guest-write capability.

A fresh matching signing-screen observation queues a captured negotiate_proposal
request on the transport owner. It waits for an already-pending read reply without
blocking the game thread. Duplicate submissions for unchanged terms do not queue
another proposal; changed terms clear that per-screen state. Session-qualified
request IDs avoid request-number collisions across process restarts. Foreign
callbacks copy one bounded submit intent under a lock; they never operate the
single-owner transport. The adapter captures the selected player, exact terms,
calendar and financial fields and rechecks the selected-context pointer after
sampling. A screen-generation token rejects callbacks spanning exit/reopen or
service restart. Only a fresh matching owner observation consumes the intent;
changed terms/player/financial state, invalid samples and screen exit discard it.
An invalid sample also cancels an already-consumed intent waiting behind a context
reply. Unmatched/unsupported paths
remain held and never grant a commit.

Validated replies present the player's response and reason. A counter displays
its term and total; acceptance explicitly says the signing remains held. Stale
observations/screens discard the reply. This records a proposal, never an actual
signing: accepted-deal settlement, current control/revision checks, guest contract
application, ledger confirmation and crash/save recovery remain required.


### Engine settlement foundation (not a bridge operation)

`FranchiseStore.commit_accepted_proposal(team_id, proposal_request_id,
request_id, expected_revision, access_check=...)` consumes a recorded acceptance
without inference. It requires a distinct settlement ID and a callable current
access check. In one SQLite write transaction it verifies the latest negotiation
for that player, unchanged accepted preview/revision, current ownership and
salary/draft constraints, then records the exact accepted offer, cash obligation,
promises and signed story. The source proposal remains unchanged. A final access
check after inserts can roll back all effects before SQL commit.

The signing event carries `proposal_request_id`; replay reconstructs its story
from the earlier accepted dialogue and verifies its exact preview, terms,
evidence and history. The same settlement ID retries its original receipt;
another ID cannot consume the proposal again. Historical retries preserve later
transactions. Superseding dialogue, changed finances, foreign ownership, or a
nonaccepted proposal reject. Ordinary signing cannot relabel a story as settlement.

This method updates the independent engine only. It is deliberately absent from
the bridge operations and never grants guest memory writes or confirms a save.
A durable guest application/reconciliation coordinator is still required before
native accepted offers can use it. Do not substitute it for that coordinator or
call it at the native judgment boundary before game effects are verified.


### Saved-effect confirmation foundation

`tools.confirm_saved_signing.confirm_saved_signing` compares immutable before/after
FXG payloads against a pinned before hash, existing player bindings, typed accepted
offer, captured guest offer and target team. It checks one bound free agent moved
to that team, exact new contract fields (including initial remaining term), no
other bank contract or bound membership changes, unchanged calendar/cap/adjustment
fields, reconstructed payroll for all32 teams, and the exact target payroll delta.
The validated binding profile determines the dollar scale. Unrelated nonfinancial
settings bytes may change; this does not assert complete byte equality of saves.

The result fingerprints both payloads and bindings and explicitly grants no
write authority. It confirms saved roster/contract/payroll effects only. It does
not prove complete modern books, paid cash, live memory, fresh remote access,
durable intent or coordinated save/ledger settlement. The native addon remains
held until those pieces are connected. An old real signing pair is confirmation
regression evidence, not an AI signing or current SOFTDRINK runtime acceptance.


### Durable saved-signing journal (engine API and opt-in service)

`franchise.guest_signing.prepare` binds a source acceptance, exact captured terms,
franchise bindings, original save/hash and revision in the franchise SQLite DB.
Preparation requires all32 supported team books, known cash obligations and exact
saved roster/contract/annual-charge agreement. Retained-charge projections that
cannot match the guest payroll and unresolved first-year adjustments reject;
legacy cash is still unavailable until a verified import exists. New preparations
check current access twice and returns `write_authorized: false`.

One prepared journal freezes other cooperative store writes across processes,
including other clubs, actor updates, direct settlement and migrations. Reopening
the store and read-only recovery remain available. Older writers that do not
implement this guard are unsupported; do not share a pending DB with them.

`settle` confirms the candidate saved payload and records the confirmed bytes,
proof, consumed acceptance and financial signing within the same SQLite
transaction. Current access is required again, including the signing's final
precommit check. Failure/abrupt exit rolls back journal resolution and all ledger
effects together. Same-ID/same-payload retries return the original signing;
changed payloads reject. No inference or control renewal occurs.

`inspect` returns verified original/confirmed payload backups and identifies
`before`, `candidate_after`, `confirmed_after` or `unrecognized` saved state.
Candidate detection is read-only and works with AI disabled. A settled journal
paired with the original save reports `before`; it never silently undoes money.
`cancel` releases only uncommitted work against the exact original saved bytes
with a caller-supplied stopped-game check before and after the update. It never
restores game files or re-enables AI. Changed saved effects must be resolved
explicitly with the game quiescent, rather than discarded as unapplied.

The service can expose preparation, confirmation and bounded status through the
explicit opt-in described below. The native application/save/reload coordinator
and actual quiescence checks still need implementation and game verification.
This journal alone grants no guest writes, proves no active-save selection, and
does not complete live delivery.


### Opt-in saved-signing service coordination

`--guest-signing --guest-save PATH --guest-bindings PATH` enables three bridge
operations. It defaults off and is not enabled in the installed game. Both paths
are fixed at service startup; input frames cannot supply paths, bindings, save
bytes, outcomes or write authority. Initial save/bindings validation is still
required at startup. The service reads the current regular save file with a
bounded read and file-identity/size/time checks, rather than confirming against
its frozen startup snapshot. All operations require a 1–60000ms `timeout_ms`.

- `guest_signing_prepare`: protocol/request_id/operation/timeout_ms plus
  `team_id`, `proposal_request_id`, `guest_offer`, `expected_before_sha256` and
  `expected_revision`. SHA256 is canonical lowercase hex. The request ID becomes
  the journal ID. Preparation verifies the existing accepted proposal and complete
  supported books, retains original bytes and freezes competing writes; its
  response remains `write_authorized: false`. Response capacity is checked before
  reserving anything. Same-ID unchanged preparation can be retried.
- `guest_signing_confirm`: protocol/request_id/operation/timeout_ms plus
  `journal_request_id` and `expected_after_sha256`. Current saved effects must
  match the journal's exact accepted terms. The service atomically resolves the
  journal and commits ledger effects, returning the journal ID, `state: settled`,
  player ID, financial revision, exact annual charges, after-save hash and
  `write_authorized: false`. This confirms saved effects/ledger settlement; it
  does not assert live guest memory or verified game reload. Same journal/hash
  retries return the original financial result without another inference.
- `guest_signing_status`: protocol/request_id/operation/timeout_ms plus
  `journal_request_id`. Returns journal state, save position, current/before/after
  hashes and `write_authorized: false`. Backups remain in SQLite rather than
  overflowing pipe frames. Status is read-only and requires no AI grant.

Preparation and confirmation require current remote authorization, connection and
deadline checks inside the journal transaction. Each check also rereads the
server-selected file and rejects a changed payload. Confirmation checks response
capacity inside that transaction and rechecks authority afterward; any refusal
rolls back proof, journal resolution, cap, ownership, cash and stories together.
Neither operation requests inference or renews control. They share the existing
single worker/no-queue policy with negotiations. Keep stdin open until the reply;
the reader must detect EOF while a write request is in progress, so a disconnected
client cannot commit after the last gate. Competing worker requests receive busy.

There is no cancellation RPC: it still requires a real stopped-game check supplied
to the engine API. No game-file restore, guest write, native acceptance release or
automatic shutdown renewal is introduced. Startup recovery from an unreadable or
invalid-layout save still needs a dedicated recovery launcher; it is not silently
accepted as a valid opening snapshot. Actual native application/save/reload,
legacy cash import and real-game acceptance remain open.

### Native held acceptance preparation

`NFL2K5_FRANCHISE_GUEST_SIGNING=1` explicitly enables the same service journal
mode and native coordination. Only `0` or `1` are accepted; absence defaults off.
The game additionally requires its existing pinned context, saved-performance,
guest-offer and held-negotiation configuration. This unfinished mode must remain
off in the installed runtime until application and recovery are connected.

After consuming a validated captured acceptance, the native client can prepare
only that exact proposal, using its checkpoint team, revision, save hash and
captured raw terms. The journal ID is the proposal ID with `-guest` appended.
There are no caller-supplied overrides. A successful hello AI grant and advertised
journal capability are required; the server still checks current remote control.
Rejections, counters, errors, uncaptured proposals and obsolete screen/offer
responses do not trigger native preparation. Preparation requests no inference.

Once queued, the owner-thread host blocks further offer requests and keeps retail
signing held across changed terms and screen transitions. It consumes the pending
receipt even after leaving the screen. Error, lost or malformed replies never
unlock signing: the journal may already have committed. The receipt is strictly
matched to the journal ID and before-save hash and cannot grant guest writes.
Logs retain the receipt for recovery; no guest application, file restore, automatic
cancellation or recovery completion is implied. A restart does not clear a
durable journal; the service's pending-work guard continues to reject competing
writes. Recovery must inspect the saved journal before any later application.

Explicit engine cash initialization may now declare preserved legacy cash unknown
rather than inventing values. Partial snapshots retain null franchise-wide cash
totals and separately name known totals and unknown legacy players; no such
scope is selected automatically. Saved-signing prepare still requires initialized
cash coverage on every club, but that coverage may explicitly mark preserved
legacy cash unknown. New contract cash is fully enumerated. The negotiation cash
summary includes only the count of unknown legacy contracts, not their IDs.
Lifecycle bridge receipts currently require complete cash coverage and refuse a
partial scope before release/trade/restructure writes. See the explicit-scope
contract in docs/franchise-integration.md; guest application remains unconnected.

### Native saved-state confirmation loop

The opt-in native journal coordinator now checks the service's startup-pinned
save path every two seconds while a prepared journal is pending. This is an
asynchronous local read, not an inference, directory discovery or game-file hook.
An unchanged before-save queues no financial write. Only a validated
`prepared/candidate_after` status and the existing hello grant can queue
confirmation with that exact after-save hash. The service still checks current
remote control, connection, deadline, bytes and journal proof inside settlement.
The native client additionally matches the confirmation's player, exact charges
and next financial revision to the consumed captured acceptance.

A confirmation is followed by a status read. `settled/confirmed_after` or cancelled
journals stop automatic checks. Errors force another status read; AI-disabled
responses clear the grant and leave read-only status available, without another
hello, renewal or inference. Unknown states/hashes, substituted journals and
contradictory confirmations are rejected. Unchanged replies are not repeatedly
logged. Navigation does not stop pending receipt collection, and stale offer
panels remain hidden.

The host never releases retail signing here, even after successful settlement.
The configured path must eventually be verified as the actual active game's
save; this loop does not prove that selection, guest application or game reload.
A new process does not guess its old journal: explicit-ID recovery remains
available through `guest_signing_status`, including with failed AI initialization.
Unreadable-startup recovery and safe guest application remain unfinished.
