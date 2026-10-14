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
