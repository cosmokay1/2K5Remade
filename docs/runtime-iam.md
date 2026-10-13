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
