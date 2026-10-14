# Franchise money audit — October 13, 2026

**Current verdict:** the durable engine enforces its supported sourced acquisition,
release, assignment and first-restructure rules, with exact cap obligations,
separate nominal cash/payments, persistent stories and exclusive ownership.
It is still not a complete modern NFL franchise money system. The October14
static original-game audit below identifies signing/accounting boundaries, but
actual financial units, guest transaction readback and save/load remain unverified.

Re-ran `python -m tools.audit_money` against the current source on October 13.
F01/F02/F03/F07 reject the original invalid inputs; F04 now charges the same
exact 5/4 to cap and rookie pool; F08 replaces the tender once. Durable F05
retries preserve the receipt and revision; durable F06 prevents competing
ownership without changing finances. The recreated standalone-ledger examples
remain historical demonstrations of why production must use FranchiseStore.

Current supported lifecycle includes retained bonus/guarantee debt on sourced
healthy preseason releases, paired preseason assignments, separate returning
agreement generations and the first sourced guaranteed-base conversion. Cash
records preserve nominal owed/paid amounts and payment-component allocations;
cap present-value calculations do not erase nominal unpaid cash. Read-only
Top-51/regular-season projections do not change signing authority or advance
calendar state.

Remaining requirements include full guarantee protections/vesting and cash
settlement, broader releases/trades, extensions/repeated restructures, complete
Team Salary and phase transitions, incentive settlement, carryover/year rollover,
rookie options/escalators and verified official posting/import. Exact internal
arithmetic does not resolve NFL posting conventions; see
[posting policy](cap-posting-policy.md). Unsupported liabilities must reject,
not disappear from the ledger.

The original findings and early repair notes below are retained as historical
evidence. Their line references and descriptions reflect the earlier prototype.
The executable audit and [worklist](../WORKLIST.md) describe current coverage.

## October 14 — Original-game signing accounting, static evidence only

The legally supplied executable and AIBASELIN save now permit direct analysis.
This evidence supplements the earlier asset-free engine audit; it does not prove
modern NFL rules or an original-game cap defect.

- Interactive signing routine0x00323D80 checks roster/cap preconditions before
  calling offer judgment0x00323A60. That judgment uses score output from
  0x003232A0: below70 refuses further negotiation,70..79 declines,80..109 accepts,
  and110+ uses the generous-offer acceptance message. These are original-game
  score thresholds, not probabilities or new AI behavior.
- After acceptance and before new player contract fields are written, a conditional
  0x0013ED30 updates uint16[team+0x19C+2*index]; signing passes index0. Its guard
  consults0x0013EC30. It adds0x0013ED00's result computed from the old contract and
  stores only the low16bits. The effect of overflow on actual franchises is untested.
- 0x0013ED00 uses salary word+0x0A, packed allocation bits20..23 and term-like
  bits24..27 via0x000E6020, multiplying the result by packed bits0..3.
- Cap accessor0x0013ECA0 conditionally subtracts that accumulator from global
  0x00E3C278. It is separate from the roster salary total at team+0x124.
- Later roster refresh0x000C3F00 walks players whose record+0x24 low nibble is
  nonzero, sums0x000E6380 and0x000E6020 plus0x00246F20, and writes team+0x124.

Preserve the old-contract adjustment, player mutations, roster updates and total
refresh around the future AI offer judgment. A whole-function boolean replacement
would lose required accounting and history effects. No original-game financial
writes or AI interception have been added. Required observations remain selected
player binding, UI amount/unit agreement, salary-only and term-only controlled
saves, unchanged-save control and reload verification. The16-bit accumulator's
UI meaning, persistence and overflow intent remain unresolved.

## October 14 — Controlled Gildon signing and UI cap reconciliation

AIBASELIN, unchanged AICNTRL and signed AIGILDON now establish one actual original
game transaction. Jason Gildon moves from free agents to Giants; saved salary
word829 and packed word0x02410BA2 retain the observed$8.29M/2year/Descending/40%
terms. Both signature companions match the runtime implementation and the signed
payload matches its UDATA mirror. User reported completion of the instructed
save/reload sequence and explicitly confirmed Descending annual rows:
2004 salary$3.10M/bonus$1.65M; 2005 salary$1.86M/bonus$1.65M. No AI interception or modern financial posting occurred.

The control changes14405 bytes but no candidate contract fields across2479
records or1937 memberships. The signed result adds22 transaction-only bytes.
Giants salary total+0x124 goes72272→77038, an increase of$4.766M under the
verified thousand-dollar scale. User's$80.50M cap and displayed team/room values
match exact saved totals$72.272M→$77.038M and room$8.228M→$3.462M. Display
truncation explains why subtracting displayed cap and team numbers differs by
$10000 from displayed room. Use underlying monetary quantities for accounting.

Read-only original payroll reconstruction now matches all32 teams in baseline,
unchanged control and signed saves, covering1696/1696/1697 active contracts.
Static raw schedule codes0..7 and original-minus-remaining term indices explain
the current stored totals without ratings. Mismatches and malformed active
contracts fail reconciliation; no unknown debt or tender is assumed zero.

This validates current original roster charges. Subsequent annual charges,
term aging, long-contract bonus limits, releases, retained debt, guarantees and
modern-rule/game posting consistency remain unverified. No completed modern
franchise money system is claimed.

## Saved first-year cap branches and economy decision

User chose to retain2004 dollar amounts and the original$80.5M league economy,
scaling modern minimums/rookie amounts proportionally to that cap. Modern rule
structure remains required. An explicit source reference cap/year and integer
posting policy must accompany that scaling; do not guess minimums or change
existing contract totals to finance a signing. No conversion is installed in the game yet.

`franchise.historical_economy.HistoricalEconomy` now implements this simulation
conversion using the [published2026 cap](https://www.nfl.com/news/nfl-announces-2026-salary-cap-set-at-301-2-million-per-team)
as a fixed301.2M reference. With the verified80.5M target, the exact ratio is
805/3012. Minimums round up and ceilings down to1000-dollar postings. This is
an authored adaptation policy, not a historical NFL minimum or NFL posting rule.
Game2004 maps to published2026 minimums; later game years advance the minimum
table year while retaining the fixed reference ratio, through its published2030
limit. No future reference cap is predicted or fetched automatically.

The helper supplies typed drafted/undrafted scale inputs to existing validators;
drafted allocations still require actual source amounts, and mismatched reference
minimums reject. It cannot invent pick allotments. Original offer-word encoding,
legacy guarantees/debt conversion, persistence of adaptation provenance and the
game calendar/import remain required before actual transactions use these inputs.

Adaptation provenance now persists within `VeteranMinimumProfile` and is exposed
in negotiation context. Replay rejects unsupported reference sources/posting or
converted-floor disagreement. A year transition rejects removing/changing the
adaptation before mutation. This covers durable engine rule inputs; it does not
prove real-game calendar mapping, legacy contract conversion or rookie allotment
provenance. Existing unscaled profile records retain their prior serialization.

## Existing contract preservation policy

User explicitly chose to preserve all existing deals as legacy schedules and
apply modern rules to new deals. AIGILDON has1697 active contracts;195 with
nonzero bonus codes have original terms over five years, spread across31 clubs.
Their original-term histogram is1:137,2:208,3:443,4:375,5:332,6:125,7:68,
8:6,10:3. Applying a five-year bonus horizon retroactively would change these
opening schedules and is outside the approved import policy.

Legacy import must preserve independently reconstructed charges and original
identity/terms, separately from new modern contracts. Unknown legacy guarantee
protections, unpaid cash and termination obligations require explicit supported
treatment; preservation is not permission to zero them or claim a full modern
conversion. Releases/trades/restructures must reject unsupported legacy cases
until their original obligations and transition are verified.

`franchise.legacy_contracts.LegacyContract` now preserves raw amount/bonus/style
and original/remaining term fields with stable player ID and snapshot source.
Its immutable records serialize without adding paid cash or guarantee defaults.
The existing static original calculator is shared with the read-only inspector;
long terms and original rounding loss are retained, rather than converted through
modern `Offer.charges()`.

`tools.export_legacy_contracts.legacy_contracts` requires pinned same-season
identity resolution, valid saved cap context and all-team payroll reconciliation.
It rejects inactive/unsupported roster contracts and returns typed active records
only after their current totals match each club. Private baseline/control/signing
exports contain1696/1696/1697 records and match all32 totals. These are opening
inputs; they are not yet loaded into FranchiseStore, nor is future season aging
or legacy cash/termination treatment authorized by this export.

`tools.inspect_franchise_cap` now derives the franchise tail from the validated
saved scheduler boundary and reads the league-cap field at tail+15D0. Original
save/load routines2D0790/2D0CE0 transfer this field to/from globalE3C278. Team
flagE5775C[index] serializes at scheduler+AC+4*index;13EC30 delegates toC4D50.
First-year accessor13ECA0 subtracts uint16team+19C only when that team flag and
the caller's adjustment argument are nonzero. The reader reports both branches
without choosing the runtime caller's branch or declaring modern liability.

All three private saves yield cap$80.5M, Giants flag1, zero first-year
accumulators across32 clubs and fully reconciled original roster totals.
Baseline/control Giants room is$8.228M and signed room$3.462M, agreeing with
prior UI evidence and the live signing probe. An original zero accumulator is
not proof that modern retained obligations, cash payments or guarantees are zero.
Unsupported layouts/nonpositive cap/payroll mismatch reject the report.

## Historical prototype snapshot

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

## Earlier durable-path reassessment — historical snapshot

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
