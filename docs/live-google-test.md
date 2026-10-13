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
