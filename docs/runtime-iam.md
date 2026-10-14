# Google runtime identity and control separation

On October 13, 2026, created keyless service identity
`franchise-runtime@llm-2k5.iam.gserviceaccount.com` in project `llm-2k5`.
No user-managed service-account key was generated or distributed. No deployment,
paid inference request, control renewal or switch re-enabling was performed.

Direct grants:

- Project custom role `franchiseInference`: `aiplatform.endpoints.predict` and
  `serviceusage.services.use`; no resource administration.
- Bucket custom role `franchiseControlReader`: `storage.objects.get`, restricted
  by IAM condition to `projects/_/buckets/llm-2k5-control-326898036708/objects/ai-control.json`.
  No listing, writing, deletion or IAM management.

Run `python -m tools.audit_runtime_iam` with an authorized administrative login
for a read-only direct-policy/key audit. It prints no tokens and calls no model.
The audit verified these exact grants and zero user-managed keys. It does not
inspect inherited organization/folder policies or prove effective model access.

Live authentication under this identity still needs verification. The sidecar
supports explicit `--impersonate-runtime` in Vertex mode, using authorized source
ADC to acquire 15-minute credentials for the configured runtime account. Separate
credential objects are used for switch reads and inference. Ordinary ADC mode does
not automatically impersonate this account. No owner-CLI fallback is permitted
when runtime credentials are selected.
Do not distribute owner credentials or service-account keys. Local administrative
`gcloud` demo access remains distinct from the future runtime authentication path.
The service identity's existence does not authorize arbitrary end users to
impersonate it; token-creator/federation grants were not added.

Primary references:
[Vertex AI access control](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/access-control)
and [Cloud Storage IAM roles](https://docs.cloud.google.com/storage/docs/access-control/iam-roles).

Control refresh HTTP calls use a 15-second timeout and reject expired credentials
even after refresh. Reusing a valid token never reuses the remote enabled grant:
each handshake fetches the switch again. Offline tests cover disable/unavailability
with cached tokens and failed refresh without owner ADC fallback. Effective live
identity access remains unverified.

## Live source-permission gate

October 13, 2026: a read-only GCS request using the runtime identity failed before
object access because the current administrative source login lacks
`iam.serviceAccounts.getAccessToken` on the target. No token was printed, model
called or control object changed. Automatic approval review rejected a scoped
Token Creator grant as a persistent IAM delegation requiring explicit human
approval. The grant was not applied; approval is pending in the chat.

Do not work around this gate with owner fallback, distributed keys or another
identity. Offline tests confirm denied runtime impersonation leaves AI disabled
while explicit manual transactions retain the same cap validator.


## Required persistent request budget

Live sidecar `--provider vertex` and HTTPS origin `--ai vertex-runtime` both
require `--ai-budget-database`, `--ai-budget-scope`, and `--ai-request-limit`.
The usage database must be separate from the franchise database (path aliases,
symlinks and hard links to the same file are rejected). Share the same usage file,
scope and limit between transports to share the ceiling. A missing/invalid budget
keeps live AI unavailable before credentials/SDK initialization; manual operations
remain available. Offline fixture/disabled modes require no budget.

Example arguments appended to an existing authorized runtime launch:

```text
--ai-budget-database .local-runtime/ai-usage.sqlite --ai-budget-scope franchise-a:2026 --ai-request-limit 250
```

The scope is an explicit operator-selected period identity, not the wall clock.
Restarting retains spent/pending attempts; changing a recorded limit rejects.
Neither runtime automatically creates a new period to restore capacity, refunds
failed calls, or re-enables the remote switch. This is a request ceiling, not a
$5 spending guarantee. Token/dollar admission limits, authoritative game-season
attribution and native launcher configuration remain subsequent work. Explicit
paid demonstration scripts are outside these production runtime launch paths.


## Native host launch options

The original `franchise_host_create` ABI is preserved. The explicit
`franchise_host_create_with_budget` entry point additionally receives the separate
usage database, persistent scope, and positive request limit (at most INT64_MAX).
Budget options are accepted only for Vertex runtime mode. Arguments are validated
before handles/process creation and quoted individually for Windows.

The existing host startup hook accepts these explicit environment variables:

- `NFL2K5_FRANCHISE_AI_BUDGET_DATABASE`
- `NFL2K5_FRANCHISE_AI_BUDGET_SCOPE`
- `NFL2K5_FRANCHISE_AI_REQUEST_LIMIT`

If any value is supplied, all are required; the limit must contain decimal digits
and represent a positive value within INT64_MAX. Missing budget configuration
retains the previous launch ABI, but the Python runtime keeps AI unavailable while
manual operations remain usable. No native launch automatically grants AI access,
selects a new period, or restores budget capacity. Actual Windows budget-launch
pipe validation passed CI38528423925; no guest/gameplay integration is established.


## Per-request token preflight

Both live runtime factories enable a 16384 input-token preflight and retain the
4096 maximum generated-token setting. VertexProvider also accepts explicit
max_input_tokens and max_output_tokens for controlled callers. Counting submits
the same serialized contents, system instructions and response schema/config
used for generation. Count errors, missing/noninteger/negative counts or counts
above the input limit refuse generation before reserving a durable attempt.
Negotiation and scouting recheck their request-specific access guard after
counting, before reservation/generation; a deadline or disabled/disconnected client
therefore cannot start a new generation following that wait. The guard also runs
after potentially blocking SQLite reservation; denial retains the spent attempt.
These count requests consume the rolling API admission slot but are not recorded
as paid generation attempts. No retry or prompt truncation is introduced.

This is a provider-reported preflight bound, not exact billing or a cumulative
season dollar guarantee. A production failure to count disables that negotiation;
manual operations remain available. Cumulative token/spend reservations and real
gameplay calibration remain outstanding. No live counting/inference was used
for validation.

References: [CountTokens](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/reference/rest/v1/projects.locations.publishers.models/countTokens),
[schema token accounting](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output),
[generated and thinking token limit](https://ai.google.dev/gemini-api/docs/generate-content/thinking).


## Cumulative token admission

Live Python launchers accept optional `--ai-token-limit POSITIVE_INTEGER` with
the existing explicit budget database/scope/request limit. The token policy is
immutable and shares the same SQLite admission transaction as request capacity.
Every generation reserves the preflight-reported input count plus the configured
maximum generated tokens; completion never refunds this conservative allowance.
Failures, pending calls, missing metadata and crashes retain the allowance.
Status exposes `token_limit`, `reserved_tokens` and `remaining_tokens` separately
from partial measured usage. No prompt or credentials are saved.

An attempted legacy scope cannot acquire a token policy retroactively; a policy
cannot be removed or changed to restore capacity. Existing request-only scopes
remain supported. No automatic new scope or season is selected. Native launch
forwarding and making cumulative token policy mandatory remain subsequent work.

Known input/output/total usage above its reserved allowance is persisted, rejects
the returned decision and blocks subsequent admission. Unknown components stay
unknown; they do not earn refunds. Counts are provider-reported preflight estimates,
so this is an admission ceiling, not an exact billing guarantee. Dollar pricing
and spending policy are still unimplemented.
