# Inference usage diagnostics

VertexProvider.last_usage returns a copied diagnostic for the last completed
call, or None before any call completes. It records model, serialized context
bytes, sdk_invoked, a fixed outcome label and six optional token counts:
prompt_token_count, candidates_token_count, total_token_count,
cached_content_token_count, thoughts_token_count and tool_use_prompt_token_count.

The fields follow [Google response usage metadata](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/rest/v1/GenerateContentResponse#usagemetadata)
and were checked against the installed google-genai types with offline responses.
Missing or invalid counts remain None; an observed zero remains zero. Counts are
not summed: prompt tokens can already include cached tokens, and total usage can
include reasoning and tool-input tokens. Raw prompts, player identities, model
text, credentials and provider error bodies are excluded from this diagnostic.

Accepted and rejected responses retain reported usage. SDK failures and preflight
rejections replace prior counts with unknown values. sdk_invoked proves only that
this adapter called the SDK, not that Google accepted or billed a request. The
snapshot is published once on completion; overlapping calls cannot mix counters.
Reading or changing the returned copy cannot modify the provider's record.

estimated_cost remains None. This snapshot is not a billing ledger, durable
per-decision attribution, weekly budget, or pricing estimate. It disappears on
process restart, and another completed call replaces it. Durable usage recording,
verified pricing, spending limits and cross-process frequency controls remain work.
No telemetry callback or extra request/retry is introduced.

## Local request-rate enforcement

Each VertexProvider allows at most 20 attempted SDK calls in a rolling 60-second
window by default. Construction may set a positive integer
max_requests_per_minute. A monotonic clock and lock protect admission across
concurrent calls. Invalid/oversized contexts consume no slot; failed or blocked
SDK attempts do consume one. At exactly 60 seconds the old attempt leaves the
window. Excess calls reject before the SDK, publish preflight_rejected usage
and do not wait or retry automatically. Existing bridge commit checks remain
responsible for preserving finances.

This is a per-provider, per-process limit. Restart clears it; separate negotiation
and draft providers have separate windows. It is neither an account-wide quota
nor a durable spending budget. The remote kill switch remains required.
