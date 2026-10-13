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

The signing API now requires `veteran_minimums`: a registry mapping known veteran
IDs to positive annual salary floors. Drafted rookies remain explicitly registered
with `RookieScale`. Unknown players reject; no missing classification falls back
to the veteran path. Every offered veteran year requires a supplied floor and
must meet it. Example floors are synthetic, not an official annual salary table.
Modern bonus allocation limits cannot exceed five years. `cap`, `roster_reserve`,
and `max_bonus_years` are read-only properties. Use `update_budget` with the latest
revision to change cap/reserve; a material change invalidates outstanding offers.

`franchise/minimums.py` supplies the published 2020 CBA Article 26 tables for
2020-2030, with source URL and rule version. It distinguishes active/inactive
compensation from the separate non-active/inactive table, converts source
thousands to dollars, and requires explicit credited-season/category inputs.
Practice squad and years beyond the published range reject. Annual schedules
do not assume a player earns a credited season. This is a rule-data component;
binding real game roster status, credited-season evidence and annual rule profiles
to the authoritative import is still required. Draft-slot allotments remain inputs.

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
idempotent. League-wide pool accounting is still unimplemented. Offers use integer
dollars; internal cap and rookie bonus allocations use the same exact fractions.
JSON represents fractional dollars as strings such as `"5/4"`, never floats.
Display rounding must not change ledger values or create cap room. This policy
does not establish the original game's fractional-dollar posting convention.

Explicit `rookie_tenders` identify amounts already included in bootstrap team
charges. Each must match that rookie's supplied first-year minimum, and declared
tenders cannot exceed existing charges. Signing replaces its tender rather than
adding both obligations. Rejected offers and repeated receipts leave it intact
or already replaced, respectively. Unknown aggregate balances still cannot reveal
undeclared tenders; an authoritative importer remains required.

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
not a personality simulation. The basic `Ledger` remains in memory.
`FranchiseStore` adds a local SQLite event store; `StoredLedger` connects it to
negotiation commits. It preserves bootstrap data, supported signing/budget events,
ownership, receipts, and committed negotiation stories. Exact retries recall the
recorded agreement without another model call, including after reopening the file.
Run `python3 -m examples.persistent_negotiation` for the offline restart demo.

Store writes use database transactions; a signing, its ownership and associated
story commit together. Independent connections cannot allocate the same player
to two teams. Replay is deterministic accounting and does not invoke the model
or remote handshake; new AI decisions still require access. Invalid schema
versions and invalid history stop reconstruction. Initial aggregate charges are
still supplied externally. All teams must use the same store for shared ownership
enforcement; standalone `Ledger` objects do not coordinate across teams.

Database format 3 records each contract's actual charges and the complete financial
result of each event. Replay compares those results and reconciles ownership; a
disagreement blocks further financial writes. New teams require `OpeningBooks`
and `Ledger.from_opening`: original active contract terms plus elapsed years,
declared rookie tenders, retained charges and adjustments with provenance. Totals
and ownership derive from those records and are reconciled on reload. Ordinary
in-memory unit fixtures can still use aggregate totals, but durable creation
rejects aggregate-only books.

Format-2 migration requires explicit matching source books for every team:
`FranchiseStore.migrate_v2(path, books_by_team)`. It first takes a consistent
SQLite backup, checks opening totals/ownership/tenders and every historical
posting, then commits the source records and format change atomically. Failure
leaves original state/version intact. Format-1 data lacks posting evidence and
is still preserved but unsupported by this migration. No format is silently
reinterpreted or overwritten. Supplied provenance is metadata; it does not prove
that source contract values were correctly extracted from a real game save.

Active/counter/rejected negotiation histories, personality changes, real franchise
imports, releases/trades, migrations and cloud replication are not yet durable
through this store. It is an engine database, not a compatible Remade save file.

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
supplied aggregate existing charges. Exact internal allocations are implemented;
game/display posting conventions and a compatible save writer remain unverified.

See [the source audit and game integration experiment](franchise-integration.md).

Offer preview: `ledger.preview_offer(offer, expected_revision)` validates the same
financial rules as signing and returns exact annual charges, resulting cap room,
replaced tender and rookie pools. `StoredLedger` also checks other teams' ownership.
It does not reserve room or promise future acceptance. Commit must still recheck
current state. `contract_cash` is total nominal compensation, not guarantees or a
cash-payment calendar. No AI access is required for read-only financial previews.

For published veteran floors, construct `VeteranMinimumProfile(start_year, players)`
with immutable `(player_id, annual_credited_seasons, annual_roster_categories)`
records. Pass both `veteran_minimums=profile.floors()` and
`veteran_minimum_profile=profile` to the ledger. Durable reload reconciles them.
Supported years are 2020-2030; no historical-year conversion or automatic credited
season accrual is applied. This profile establishes veteran salary floors only.

Negotiation accepts `PerformanceEvidence` with explicit window/mode/coverage and
`Observation` records. Use `value=None` plus an unavailable reason when targets,
pressures or another counter are not exposed; use zero only when it was observed.
Records require provenance and reject incompatible opportunity/outcome counts.
They do not authenticate a source or implement game instrumentation. The shared
model prompt preserves that uncertainty. Hidden rating keys are rejected in all
actor context fields, including personality and relationships.

Durable negotiations now retain counteroffers, rejections and accounting failures.
A new session restores that player's history with the team; retries return recorded
responses rather than generating new ones. Dialogue consumes no cap or ownership,
and records the unchanged financial posting for replay verification. Signed
contract/story writes remain atomic. Histories currently span the player's entire
conversation with a team; deadlines and distinct negotiation campaigns are pending.

The durable store registers initial player personality and team relationships when
a negotiation session is created. Later sessions reuse them; changing constructor
defaults does not reset the player. Personality follows the player across clubs,
while relationships are team-specific. Performance evidence can refresh each
session. Explicit bounded relationship/personality evolution is pending.

Model-backed writes verify the conversation request sequence as well as financial
state. A concurrent response invalidates an in-flight acceptance/counter, even if
cap revision did not change. The caller should submit a new request after refreshing
history; an obsolete response is not committed or silently regenerated.

`signing_bonus_acceleration` models only the retained signing-bonus component of
a termination using original contract terms, elapsed years and actual removal
date. Its source is executed CBA Article 13 section 6(b)(ii). It does not release
a player or compute total dead charges: guarantees, earned salaries, termination
pay, injury protections and roster effects remain separate pending work.

Model-backed events retain their frozen personality, relationship and performance
evidence plus the observed financial revision. This provides the facts behind
remembered dialogue; it does not make generated narration a verified fact.
Historic/manual events do not acquire invented evidence during migration/reload.

Cash accounting is explicit and independent of cap proration. Initialize a durable
team with `store.initialize_cash(team_id, tuple_of_CashObligation, source=...)`.
Every active original contract must have `contract:PLAYER_ID` with nominal total
equal to original base salaries plus signing bonus; paid amounts require source
evidence. Additional retained cash obligations can be declared separately. Missing
initialization returns unavailable cash (`None`), never an assumed zero.

Subsequent signings add nominal obligations atomically with contract/story records.
`record_payment` requires a request ID, known obligation, positive integer amount,
source, external `payment_reference` and expected cash revision; overpayments/stale/conflicting retries reject.
Cash changes advance franchise revision while leaving cap charges unchanged.
Replay checks cash postings and financial postings. This is nominal owed/paid
compensation only: no payment-date calendar, guarantee vesting, offsets, incentive
settlement, owner cash budget or trust-funding rules yet. No paid cash is inferred
from elapsed cap proration. Older code rejects the new event kinds rather than
silently skipping them; use the current branch for databases with cash events.

Payment references are unique within the team and evidence source, independently
of request IDs. A second request cannot credit the same source receipt again.
Historic cash events without references remain readable but require an audited
migration before retrying them with external references; no reference is invented.

Offers support optional `guaranteed_salaries`, one integer protected base amount
per contract year. These are full skill/injury/cap guarantees at signing, limited
to that year's salary. They neither increase nominal total nor reduce cap charges.
Counter responses may negotiate them; accept/reject leaves them unchanged.
`Offer.from_dict/to_dict` preserves legacy three-field fixture terms and new
guarantees. `ledger.contract_terms(player_id)` exposes original saved terms.

[Definition source](https://operations.nfl.com/calendar-events/nfl-free-agency/contract-language).
Conditional guarantees, vesting, offsets, forfeiture and release settlement are
not implemented. No guarantee is inferred from missing original-game data.

`store.update_relationship` applies one explicit bounded change to an existing
relationship score, requiring a recorded negotiation source request and current
franchise revision. Scores stay in 0–1; step limit 0.1 is simulation policy.
One event/relationship may affect the score once. Live/restarted sessions observe
updated relationships through an atomic actor/accounting read. No automatic trust
changes are inferred from free-form model narration. Personality and agent/GM
evolution remain pending.

`guaranteed_base_liability` calculates a separate present-value cap component from
explicit unpaid protected bases and payment-year offsets. Its nominal unpaid cash
remains unchanged. `DiscountProfile` requires an exact annual rate, league year
and provenance; no real rate is bundled or inferred. Only whole annual periods
are supported. Source: executed CBA Article 13 section 6(d)(iv) and Article 1.
Covered termination, payment/offset/void facts and complete settlement must still
be verified before a release transaction can be enabled.

Cash records may include immutable `paid_components`: `(component, amount)` pairs
where components are `signing_bonus` or `base:N` in original contract year indices.
Allocations must reconcile total paid and original amounts. New tracked contracts
require payment `component`; historical unknown allocations remain unavailable.
`ledger.guarantee_cash(player_id)` reports unpaid protected bases and bonus when
known, or `None` otherwise. It does not infer payment dates, covered termination
rights, offsets or guarantee voiding. Existing legacy records are not silently
converted to known zero allocations.

`store.termination_components` uses stored original active terms, elapsed years
and known component payments. Supply removal date, DiscountProfile and explicit
payment-year offsets. It reports separate bonus/base cap components and nominal
unpaid amounts without changing ownership or finances. Missing allocations or
unsettled prior-year protected bases reject. `release_authorized` remains false:
covered-release facts, offsets/voids, earned/termination/injury liabilities and
phase/roster costs still require complete settlement handling.
