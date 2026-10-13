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

Authentication under this identity still needs implementation and verification.
The current sidecar uses ADC and does not automatically impersonate this account.
Do not distribute owner credentials or service-account keys. Local administrative
`gcloud` demo access remains distinct from the future runtime authentication path.
The service identity's existence does not authorize arbitrary end users to
impersonate it; token-creator/federation grants were not added.

Primary references:
[Vertex AI access control](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/access-control)
and [Cloud Storage IAM roles](https://docs.cloud.google.com/storage/docs/access-control/iam-roles).
