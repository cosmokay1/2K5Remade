# Story-driven NFL 2K5 franchise prototype

The intended product is personality/performance-driven negotiation constrained
by modern NFL contract and cap rules, including the rookie wage scale.

Current implementation is an accounting and negotiation prototype with optional
Gemini/Vertex AI and OpenAI adapters. It is not connected to Remade and does not
yet implement a complete modern NFL ruleset. No game binary is required for
examples/tests.

A [live Google Cloud smoke test](live-google-test.md) completed two Gemini
requests. The player accepted an offer exceeding current cap room; the engine
rejected it and preserved the ledger. This verifies the live adapter and final
cap gate, not full contract rules or personality realism.

```sh
python3 -m examples.negotiation
python3 -m examples.story_negotiation
python3 -m unittest discover -s tests -v
```

The demo rejects a $9M first-year charge against $8M available room, then accepts
an $8M counteroffer. It reports future obligations and protects current room,
including a configurable roster reserve. Request retries do not double-charge;
offers based on an old ledger revision cannot commit.

`franchise/rookie.py` validates drafted-rookie base-salary/signing-bonus proposals:
four-year terms, supplied annual salary floors and allotment bounds, total
compensation limits, the year-one-based 25% annual increase restriction, and
supplied remaining club allocations. First-round fifth-year eligibility is
metadata, not an automatically exercised option. Registered draft picks are
validated inside the same locked commit as team-cap and rookie-pool deductions;
they cannot bypass the rules through the veteran signing method.

Annual draft-slot values are inputs, not invented formulas or hardcoded 2026
numbers. All test amounts are synthetic. `Ledger` maintains remaining club
allocations, deducts them only for committed rookie signings, and makes retries
idempotent. League-wide pool accounting is still unimplemented. Whole-dollar
team cap allocation and exact fractional rookie-pool accounting have a documented
rounding difference for bonuses not divisible by the contract term.

## Negotiation

`Negotiation` supplies personality, performance, relationships, prior decisions,
the proposed terms, and current cap/rookie constraints to a model provider.
The response must be accept, reject, or counter with a reason. A counter is a
proposal, not a committed contract. Acceptances commit the exact offered terms
only after accounting validation. Invalid output, blocked/truncated responses,
and cloud failures leave the ledger untouched. A cap change while the model is
thinking rejects a stale acceptance. Repeating a completed request returns its
recorded reply without another model request or charge.

The default story example is explicitly scripted for local verification; it is
not a personality simulation. Histories, ledgers, and request receipts currently
exist in memory only. Restarting loses them; persistent franchise saves are a
required next step before meaningful multiweek play.

## Google Cloud / Gemini

The optional adapter uses the Google Gen AI SDK in Vertex AI mode with
Application Default Credentials. Choose a project with billing, enable the
Vertex AI API, and grant the calling identity appropriate Vertex AI access.
For local testing, authenticate using `gcloud auth application-default login`.
See [Google's setup guide](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/quickstart)
and [structured output documentation](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output).

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-google.txt
export GOOGLE_CLOUD_PROJECT='your-project-id'
export GOOGLE_CLOUD_LOCATION='your-supported-location'
export GEMINI_MODEL='your-available-model-id'
.venv/bin/python -m examples.story_negotiation --provider vertex
```

Live mode sends up to two paid requests containing synthetic demo data. Model
and region are explicit inputs because availability differs by account/region.
The supplied project is `llm-2k5` (number `326898036708`). Its billing is enabled
and the Vertex AI API was enabled on October 13, 2026. Checked-in defaults in
`config/google.json` use `global` and `gemini-3.5-flash`; environment values
override them. No server, database, or hosted game service has been deployed.
The adapter has a 45-second request timeout and one SDK attempt. It rejects
incomplete or blocked output rather than substituting a scripted acceptance.

For the short local demo, the existing gcloud login can be used without creating
an ADC file:

```sh
.venv/bin/python -m examples.story_negotiation --provider vertex --gcloud-auth
```

This flag captures a short-lived access token in memory and is intended for the
two-request demo. A long-running service must use refreshable ADC/workload
credentials. Tokens are never written to the configuration or printed.

An optional OpenAI adapter uses `OPENAI_API_KEY` and `OPENAI_MODEL` with
`--provider openai`, following the [Responses structured-output format](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

## Remote shutdown / mandatory handshake

Live clients must pass an authenticated handshake against the private control
object `gs://llm-2k5-control-326898036708/ai-control.json`. The switch is checked
at session creation, before each model request, after the response, and inside
the ledger lock before any accepted contract commits. Cached negotiation replies
also require access. There is no cached enabled grant or offline live fallback.

Disabled, expired, missing, unreadable, malformed, and incompatible controls deny
access. Initial grants expire seven days after an admin enables them. Updating
the object changes what clients see at their next check. The bucket uses uniform
access and public-access prevention. Future client identities must receive only
object-read permission; switch writes belong to administrators. The current
development demo uses the owner's existing login, not a distributed client identity.

From the workspace root, using the authorized admin gcloud login:

```sh
.venv/bin/python tools/ai_switch.py --disable
.venv/bin/python tools/ai_switch.py --enable
```

`--enable` also renews the seven-day expiration. Both commands publish to the
project in `config/google.json`. Failed uploads do not claim a state change.
The actual disabled-state handshake was verified against Google Cloud.

Shutdown prevents subsequent AI actions and commits; it cannot undo an already
committed contract or cancel/bill-refund an inference already sent to Gemini.
As with any remote check, a switch change immediately after the final successful
check can race that one commit. This is a cooperative client control, not
tamper-proof enforcement against a modified executable. Remade itself is still
unconnected and therefore cannot yet perform this handshake.

Source references: [executed NFL/NFLPA CBA, Article 7](https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf)
and [NFL Football Operations contract terminology](https://operations.nfl.com/calendar-events/nfl-free-agency/contract-language).
The CBA's rookie increase rule uses year-one rookie salary, including bonus
proration; it is not a compounded 25% increase in base salary.

Remaining work includes undrafted contracts, guarantee conditions, options,
performance escalators, league rookie pools, veteran minimums, dead money,
Top-51 offseason accounting, season transitions, persistence, live personality
behavior evaluation, and Remade transaction hooks. The cap prototype currently uses
supplied aggregate existing charges. Its integer-dollar bonus allocation assigns
remainders to earlier years; game/league rounding conventions remain unverified.

See [the source audit and game integration experiment](franchise-integration.md).
