# Live Vertex AI negotiation test

Verified October 13, 2026 against project `llm-2k5`, project number
`326898036708`, location `global`, model `gemini-3.5-flash`.

Billing was already enabled. Enabled `aiplatform.googleapis.com` successfully.
Used the existing gcloud login with a short-lived token held only in memory.
No ADC credential file, service account key, server, or database was created.

Command:

```sh
.venv/bin/python -m examples.story_negotiation --provider vertex --gcloud-auth
```

Two real model requests completed with valid structured decisions.

Synthetic state: $100M team cap, $90M existing current-year charges, $2M roster
reserve. Available room was $8M. Receiver performance was 1,100 receiving yards
and eight touchdowns; personality emphasized money.

1. Team offered three $7M annual base salaries and a $3M signing bonus.
2. Gemini countered with base salaries of $8M, $9M, and $10M, plus a $4M bonus.
   Its stated reason referenced the receiver's provided production.
3. The demo team submitted those exact terms back to the player. Gemini accepted.
4. Accounting rejected the transaction: current-year cap charge was $9,333,334,
   exceeding available room by $1,333,334 under the prototype's whole-dollar
   remainder allocation. No contract committed. Remaining room stayed $8M.

This proves authentication, model access, structured output parsing, the
two-turn negotiation interface, and mandatory cap enforcement on a live model
acceptance. It does not establish personality realism, full CBA compliance,
rookie behavior in live inference, persistence, or Remade integration.

The scripted demo explicitly chooses to submit a counter without a team-side
screen first, allowing the final cap gate to be exercised. A playable team
negotiator still needs offer previews and its own acceptance/rejection policy.

### Local context preflight

VertexProvider now bounds the serialized context before generate_content. The
default max_context_bytes is1048576 (1MiB), measured on the exact escaped UTF-8
JSON sent as contents. It can be explicitly configured by the engine caller with
a positive integer. The context must be an object with finite JSON values.
An over-limit or invalid context rejects before inference; history is not
truncated and no extra automatic retry is added. This bounds context bytes, not
token cost, total request size including instructions/schema, or weekly inference
frequency. Durable memory reduction and cost telemetry remain separate work.

Offline tests verify exact boundary/escaped Unicode, unsupported/non-finite
values, no SDK invocation on failure, unchanged contract finances and subsequent
manual signing with cap enforcement. No paid request was made for this change.
