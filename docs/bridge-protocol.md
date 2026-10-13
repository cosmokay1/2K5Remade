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
`invalid_request`, and `service_failure`. No automatic retries or inference on
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
