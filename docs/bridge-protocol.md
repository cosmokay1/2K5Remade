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
It currently launches only the offline fixture. Build and execute through the
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
