# Franchise money audit — October 13, 2026

**Verdict: the prototype protects a supplied current-year cap balance during a
simple signing. It is not yet an authoritative franchise money system.**

Eight reproducible findings and multiple missing lifecycle rules prevent a
claim of modern NFL financial correctness. This audit does not prove a cap bug
in the original NFL 2K5 game or change its behavior.

**Repair update, October 13, 2026:** F01, F02, F03, and F07 now have regression
coverage and are addressed at the prototype boundary. Veteran identities and
positive annual floors are mandatory; unknown/unclassified IDs reject; bonus
allocation is capped at five years; budget changes advance revision. Floors and
classification still need authoritative imported data. F04, F05, F06, and F08
remain open, along with the missing lifecycle rules below. Original audit
evidence and findings are preserved as the baseline at commit `02a10ac`.
See [current checks](money-audit-after-repairs.json). The suite now has 46 tests.

## Scope and evidence

Reviewed all implementation files in `franchise/`, examples, tests, configuration,
and existing integration notes. Rechecked public Remade revision
`579c72b58153c37ceb9cf20502f9ac81a3de6f4e` and save-converter revision
`e3afeece61896380a95e506ab43ae1abda0ae8a5`.

Ran 38 existing tests successfully and a separate synthetic audit reproducer.
The reproducer also checks compensation conservation across 10,100 combinations
of bonus amount, contract length, and allocation limit.

- Reproducer: `python3 -m tools.audit_money`
- Captured results: [money-audit-evidence.json](money-audit-evidence.json)
- Existing live model evidence: [live-google-test.md](live-google-test.md)

No game binary or franchise save is available. Generated guest-code money
functions have not been identified, executed, or traced. Therefore the original
game's salary calculations, CPU transactions, contract storage, and save/load
behavior remain unverified. No paid model calls, cloud changes, or implementation
fixes were made during this audit.

## How money actually flows in this implementation

1. A caller supplies `cap`, aggregate `existing_charges`, an optional reserve,
   bonus allocation limit, signed player IDs, and optional rookie registry/pools.
   None is derived from a franchise save or authoritative player contract table.
2. An offer contains only a player ID, annual base salaries, and a signing bonus.
   Amounts must be nonnegative integer dollars. Zero is allowed.
3. The model receives those terms plus actor context/history and returns accept,
   reject, or counter. Counters are recorded without financial validation or a
   team-side acceptance policy. Accept cannot silently change the original terms.
4. A registered rookie undergoes the four-year/salary/allotment/raise checks.
   Everyone else follows the veteran path.
5. Bonus charges are allocated across the smaller of contract length and supplied
   allocation limit. Extra whole dollars go to earlier years.
6. Spendable room is `cap - current aggregate charges - roster reserve`.
   If the new current charge exceeds that number, the transaction is rejected.
7. Otherwise charges are added to every affected year, player membership is
   recorded, a request receipt is cached, and applicable rookie pools are reduced.
8. These records exist only in memory. There is no cash payment ledger, year
   rollover, durable transaction log, or Remade save commit.

Remote control checks surround live inference and precede the final ledger
operation. They stop access; they do not make an incomplete money model correct.

## Reproduced findings

Priorities describe impact on the intended franchise product, not a deployed
production incident. P1 blocks credible financial enforcement; P2 affects
consistency or operating reliability. All examples use synthetic amounts.

| ID | Priority | Finding | Reproduction and consequence | Code |
|---|---|---|---|---|
| F01 | P1 | Veteran minimum salaries are unenforced | A one-year zero-salary, zero-bonus veteran deal commits and costs no cap room. The ledger lacks league-year and credited-season inputs needed for the floor. | `franchise/cap.py:17-36`, `:141-147` |
| F02 | P1 | Player classification fails open | An unknown player ID signs. Omit a draft pick from `rookies` and a one-year deal commits without spending either rookie pool. Correctness depends on callers supplying a complete registry. | `franchise/cap.py:75-91`, `:139-145` |
| F03 | P1 | Modern veteran bonus limit is configurable beyond its permitted ceiling | Setting `max_bonus_years=10` allocates a $10 bonus at $1 per year over ten years. With only $1 room, it commits; a five-year allocation needs $2 in year one. | `franchise/cap.py:38-45`, `:72-74` |
| F04 | P2 | Rookie cap and pool accounting use different rounding models | A four-year rookie deal with $1 annual salaries and $1 bonus charges $2 to current cap, but $1.25 to its year-one rookie pool. Total bonus conservation is correct; the yearly views disagree. | `franchise/cap.py:42-45`, `:159`, `franchise/rookie.py:49-50` |
| F05 | P1 | No durable money state or request receipts | Reconstruct an empty ledger after a signing and the same player/request signs again. There is no supported reload path to restore charges, membership, receipts, pools, and narrative together. This demonstrates missing persistence, not automatic double charging in a nonexistent importer. | `franchise/cap.py:75-77`, `:154-161`, `franchise/negotiation.py:57-59` |
| F06 | P1 | No league-wide player ownership transaction | Two independent team ledgers both sign the same player. Their local locks and membership sets cannot enforce exclusive ownership or trade rights across teams. | `franchise/cap.py:75`, `:78`, `:139-140`, `:156` |
| F07 | P2 | Cap inputs can change without changing revision | Change public `ledger.cap` from $10 to $100 after taking a snapshot; an offer using the old revision commits at $20. Revision protection covers signings, not configuration changes. | `franchise/cap.py:67-74`, `:137-138` |
| F08 | P1 | Signing cannot replace an existing draft tender | Bootstrap $1 of aggregate charges representing a rookie tender, then sign that player to a $1 current-year contract. Recorded total becomes $2 instead of $1. An aggregate balance cannot identify and remove the replaced obligation. | `franchise/cap.py:71`, `:149-152` |

F01 and F03 conflict with the modern minimum/proration requirements. F08 follows
from the draft-tender accounting lifecycle. These rule checks were grounded in
the [executed CBA, Articles 13 and 26](https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf).
F04 is a verified internal inconsistency; the league's exact fractional-dollar
posting convention was not established by this audit, so no replacement rounding
rule is asserted.

## Coverage of the complete money lifecycle

| Area | Current coverage | Required before authoritative franchise use |
|---|---|---|
| League year and rules | No year in ledger or offers | Season-versioned rules and effective dates; decide modern economics in a historical season versus a current-season league |
| Team cap | Supplied number | Verified league cap plus explicit club adjustments; separate policy reserve from legal cap room |
| Existing obligations | Supplied annual totals | Recalculate from player contracts, tenders, retained obligations, and adjustment records; reconcile imports |
| Base salary | Nonnegative integer only | Credited-season floors, roster status, earned/accrued salary when signing during a season |
| Signing bonus | Conserved total; configurable proration | Enforce rules and one defined precision model; retain original allocation and remaining unamortized balance |
| Guarantees | Not representable | Guarantee types, vesting dates, offsets, and retained obligations; do not confuse guaranteed cash with current cap charge |
| Other compensation | Not representable | Roster, reporting, workout, option bonuses, and supported deferred/advance terms |
| Incentives | Not representable | Classification, accounting, earned results, and subsequent adjustments |
| Rookie contracts | Drafted base salary/bonus subset | Authoritative slot/year data, draft rights, rookie tender replacement, guarantee restrictions, undrafted deals, and complete allocation bookkeeping |
| Rookie performance | Eligibility metadata only | Exercised option state and earned escalation state; no automatic fifth-year commitment |
| Free agency | Any unsigned string ID | Global player identity, rights, tender/offer status, expiration, and roster eligibility |
| Extensions/restructures | Rejected for already-signed IDs | Replace/amend the existing obligation while preserving earned salary, bonus layers, and consent/history |
| Releases/retirement | No operation | Retain applicable obligations and remove only amounts actually extinguished |
| Trades | No operation | Coordinate both teams, ownership, transferred obligations, and charges retained by the old team |
| June-1 treatment | No date or operation | Effective-date-aware release/trade accounting and designation tracking |
| Offseason versus season | No phase; every new charge simply added | Phase-aware contract ranking, relevant excluded salary components, and full season obligations |
| Roster costs | Arbitrary reserve only | Active/inactive/reserve/practice squad state and replacement costs |
| Salary benefits | Not modeled | Supported qualifying-contract cap treatment without altering actual cash paid |
| Cash spending | No separate cash ledger | Payment schedule and spending accounting distinct from cap allocation |
| Season advancement | No operation | Carry forward surviving obligations; expire completed ones; apply cap/adjustments and update rights |
| Multi-team concurrency | Process-local team lock | One atomic ownership/financial transaction across affected teams |
| Persistence/recovery | None | Durable financial state and idempotency; crash recovery; narrative tied to the same committed event |
| Remade synchronization | None | Verified mapping and interception of every relevant player/CPU transaction, plus save/load reconciliation |

The CBA provides phase-specific treatment of contract components, draft tenders,
cash-spending obligations, and cap carryover. Rookie terms include fixed lengths
and restrictions beyond salary amounts. See [Articles 7, 12, 13 and 26](https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf).

The [NFL contract guide](https://operations.nfl.com/calendar-events/nfl-free-agency/contract-language)
explains guarantee categories, bonus allocation, retained charges, release/trade
timing, incentive accounting, and qualifying contracts. Those components are
absent from the present offer schema. Their absence should restrict supported
transactions, not cause silent removal of money owed.

## Important interpretation points

**Current cap compliance and future planning are separate.** The code reports
future obligations but does not know future cap limits or advance a season.
Not rejecting all future commitments today is not itself a defect. Missing
rollover means it cannot enforce tomorrow's obligations when tomorrow arrives.

**The roster reserve is a management policy.** Calling the reduced number
"cap room" can confuse legal room with money a team has chosen to protect. Show
both balances, then let the team policy decide whether an otherwise valid offer
is affordable. Do not treat a caller-chosen reserve as an NFL rule.

**Cap cost is not cash cost.** The present code allocates a bonus for cap purposes
but does not track when it is paid. Owner cash limits and football payroll cap
limits cannot share one balance.

**Historical year and modern rules need an explicit choice.** The official NFL
table lists a 2004 cap of $80.6M and a 2026 cap of $301.2M. The example's $100M is
synthetic, not an imported game cap or a current NFL figure. Source:
[NFL salary-cap table](https://operations.nfl.com/calendar-events/nfl-free-agency/nfl-salary-cap).

**A model counter is not an affordable offer.** The live Google test produced a
counter that the player subsequently accepted but the engine rejected for cap
room. The final gate worked. A team-side preview should screen proposals before
spending another model call or narrating the offer as a feasible agreement.

**AI identity and rule data are caller-supplied.** A good prompt cannot guarantee
truthful draft status, complete contract history, or accurate existing charges.
These must come from the authoritative franchise state, not the model.

## What is verified correct within the supported subset

- Negative, boolean, fractional, and string money inputs are rejected.
- Bonus allocation preserves every supplied dollar in all 10,100 audited cases.
- The final check allows exactly available room and rejects a one-dollar excess.
- Registered drafted rookies receive four-year, floor, allotment, pool, and
  year-one-based annual increase checks for the represented compensation subset.
- An ordinary rejection leaves cap/pool balances and revision unchanged.
- Same-process identical retries reuse receipts; conflicting request IDs reject.
- Competing signing attempts cannot both consume the same team revision.
- An intervening signing makes an outstanding model acceptance stale.
- The model cannot change accepted terms by returning different salaries.
- Disabled/expired control checks stop the tested AI path before a commit.

These properties do not establish completeness. In particular, tests intentionally
use synthetic small salaries that would not be real NFL minimum contracts.

## Recommended repair order

1. Establish authoritative league/player identity, ownership, year/phase, contract
   records, and durable transactions. Keep aggregate charges as a derived view.
2. Enforce veteran minimums and bonus ceilings; require complete rookie
   classification; adopt one explicit money precision/posting convention.
3. Implement obligation replacement for tenders and amendments, then releases
   and trades with retained liabilities. Every transaction must reconcile the
   before/after cap and cash ledgers.
4. Finish phase accounting and season rollover; complete the supported rookie
   contract lifecycle with verified annual inputs.
5. Add an offer preview using the same validation logic as commit. Feed actual
   legal terms and strategy limits to the player and team negotiators.
6. Connect Remade only after mapping its fields and transaction functions. Keep
   unsupported transactions disabled until their round trips are verified.

Do not add a parallel table of manually maintained cap totals. That would repeat
the original weakness: a budget that can drift from the contracts producing it.

## Required Remade investigation

Public source inspection found no named money API; that does not mean the
generated game code lacks financial logic. With a legal game binary and paired
saves, trace signing, tender replacement, extension, release, trade, CPU roster
changes, draft advancement, and year advancement. Record displayed cap/terms,
memory changes, save payload changes, and reload results for each. Use separate
control saves to distinguish ordinary bookkeeping from financial changes.

Until those inputs are available, this report is a complete audit of the
available prototype and integration evidence, not a completed reverse-engineering
audit of NFL 2K5's original franchise finances.

## Current durable-path reassessment — October 13, 2026

The original findings above remain historical evidence. The supported bridge path
now uses `FranchiseStore`, not a freshly reconstructed in-memory Ledger.
`python -m tools.audit_money` separately reproduces the in-memory limitations and
verifies durable receipt/story recovery and exclusive league ownership. Current
captured results are in [money-audit-current.json](money-audit-current.json).

| Area | Current evidence | Remaining financial scope |
|---|---|---|
| Contract acquisition | Exact current cap, registered floors, bonus horizon and rookie limits | Full annual cap/draft profiles and imported real terms |
| Persistence | Identical restart receipts, atomic story/signing, source/posting reconciliation | Real game save/load and external ledger reconciliation |
| Ownership | Competing team cannot sign an owned player | Trades, waivers, release/retirement transitions |
| Rookie tenders | Own declared unsigned tender replaced once | Real tender mapping and full option/escalator lifecycle |
| Salary floors | Source-bound modern veteran profiles with explicit annual credited-season inputs | Complete roster-status rules and future-year policy |
| Termination bonuses | Exact June-1/final-CBA-year acceleration component | Full liabilities and executable release operation |
| Cash/guarantees | Nominal contract total only; no payment ledger | Owed/paid cash, protections, vesting and offsets |
| Season accounting | Future contract cap charges retained | Top-51, carryover, incentives, adjustments and year rollover |
| Shutdown | Disabled AI rejects inference; explicit manual sign still uses same cap gate | Real UI/manual path and native transaction hook |

No current result establishes an audit of the original game's finance code.
Missing retail binary/controlled saves still prevent that investigation. Passing
acquisition tests do not prove a complete modern franchise accounting system.
The next finance work must introduce explicit cash/guarantee obligations and
complete their lifecycle rather than assuming missing liabilities are zero.

### Newly verified rule dependencies

- Article 7 section 3(h): late rookie protections require preceding-year full
  protection; the drafted validator now enforces this supported subset.
- Article 7 sections 1(i), 2(d)-(e), 3(a): UDFA term/reservation and reserved share
  of club pools must be represented explicitly before full rookie accounting.
- Article 2 section 5 states rounding for computed/used agreement amounts,
  including Team Salary. Its interaction with exact internal proration, official
  posting and cap authorization needs explicit resolution. Current rational
  acquisition arithmetic must not be presented as complete NFL posting policy.

Source: executed 2020 CBA; retail-game rounding remains unverified.
