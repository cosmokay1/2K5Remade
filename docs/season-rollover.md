# Durable season transition — implementation worklist

Current source supports a scoped, atomic veteran-only league-year transition
and calendar-aware release accounting. Rookie cohorts, options, incentives,
carryover and actual guest year advancement remain incomplete. The ordered list
below describes the full boundary; later sections record implemented portions.

The transition must run league-wide under one BEGIN IMMEDIATE transaction,
with a stable request identity, exact team coverage and expected revisions.
Old team configuration and historical events remain immutable. Every team
must replay the same common transition identity and source year; partial
transitions, disagreement and retries with changed terms must reject.

## Source constraints found in the current implementation

- Ledger._check_transaction_date derives year from the opening minimum/pool
  profiles and last transaction. A cap update does not advance these anchors.
- ActiveContract requires a remaining year. Expiry needs an explicit archived
  state, rather than constructing an invalid contract or deleting its history.
- GenerationAgreement validates current contract against immutable restructure,
  release and assignment plans. Aging those plan inputs would corrupt replay.
  A separate current projection cursor is needed while original economics stay
  intact. New agreements must record their year anchor.
- Cap charge schedules are relative tuples. Opening retained/adjustment rows
  and later retained debt need explicit year anchors for projection. Additional
  bonus layers keep their original start index and allocation length.
- Cash payment component indices refer to original contract years. Never
  reindex them, reset paid cash, discard expired unpaid amounts, or apply cap
  present-value discounts to nominal cash.
- Rookie pools, tenders, ordered draft rights and funding reserves belong to a
  cohort/year. Historical pick ownership cannot establish new-year eligibility.

## Ordered implementation

1. Add replayable league calendar and agreement/charge projection anchors,
   preserving existing event prefixes and explicit backed-up migration gates.
2. Require sourced next-year cap/reserve, minimum profile and applicable rookie
   inputs, plus explicit settlement of incentives/adjustments/carryover. Do not
   derive future cap figures or imply missing liabilities are zero.
3. Reconcile closing cap/cash/generation state. Persist one common league
   transition and per-team before/after postings atomically. Keep nominal cash
   and original bonus/contract histories unchanged.
4. Advance surviving obligations, retain multi-year debt and archive expired
   agreements with explicit ownership/rights transitions. Unknown settlement,
   option or protection status must reject.
5. Advance rookie cohorts, rights, option/escalator decisions, annual rules and
   draft funding with sourced inputs. Never auto-exercise a fifth year.
6. Verify at least two synthetic seasons including returned/assigned and
   restructured generations, retained debt, expired unpaid cash, changed annual
   cap and retry/restart/tamper/partial-team failure cases.
7. Connect verified actual game year advancement, reconcile displayed terms
   and guest state, and prove save/load round trips.

The first supported transition may exclude unresolved rookie/option/rights
state explicitly while these cases are implemented. That milestone does not
complete the franchise lifecycle or replace the full delivery target.

## Initial calendar anchor implementation

FranchiseStore.anchor_calendar binds a declared sourced 2020–2030 initial year
to all existing teams atomically with exact expected revisions. Each team gets
a common calendar_anchor event and revision increment; cap and cash remain
unchanged. Prior sourced minimum/pool profiles and dated transaction history
must agree. Team membership cannot change after binding. Replay validates
all participating records, and later dated financial operations/roster projections
must match the anchored year. league_calendar validates and returns this origin.

This establishes an initial year only. It does not advance contracts, expire
agreement generations, settle liabilities or authorize a next-year cap. Source
labels are caller declarations, not proof of a decoded game calendar.

## Calendar-backed schedule projections

FranchiseStore.calendar_projection requires an anchored year and validates full
league replay before returning original agreement schedules at a current/future
CBA year. It reports recorded status separately from scheduled term completion,
keeps original year indices, unchanged nominal cash and closed payment ceilings,
and provides no future cap, ownership change or settlement grant. Historical
agreement economics and lifecycle plans remain unchanged. This is the projection
view needed for rollover work, not an executable season transition. New-year
agreement anchors and authoritative expiry/ownership transitions remain work.

## Payroll funding during closing and rollover

Normal payroll follows docs/payroll-funding-policy.md: no revenue or bank-balance
threshold is required. Closing-year settlement still requires recorded allocated
payments or explicit sourced settlement facts. Owner funding is not a payment
record; unpaid nominal obligations must survive. This keeps liquidity gameplay
separate from cap legality and compensation-history reconciliation.

## Typed calendar views and closing inspection

GenerationCalendarView keeps immutable agreement terms/plans separate from the
current contract cursor. Unfinished active terms expose a derived ActiveContract;
term completion alone grants no ownership expiry. Explicit expiry facts require
eligibility, sourced matching fully paid component-allocated cash and scheduled
completion. That view is validation only; the durable transition must establish
the facts and publish ownership changes atomically. Existing public schedule
projections retain their exact shape.

FranchiseStore.calendar_closing_state reports recorded outgoing/past active base
settlement and outstanding nominal cash. Unknown allocation stays unknown; owner
funding creates neither a revenue gate nor a paid record. The inspection never
authorizes expiry or advances a season.

## Initial durable transition scope

FranchiseStore.advance_league_year now commits a supported veteran-only
transition across all anchored teams under one BEGIN IMMEDIATE. It requires
format4 migration, consecutive explicit years, exact expected revisions, sourced
next cap/reserve/minimum inputs, explicit eligible expiry IDs and declared absence
of unresolved incentives, cap adjustments, carryover and other calendar liabilities.
Draft cohorts/rights, rookie obligations and other unresolved state reject.

Replay validates the common per-team event, exact closing/after financial, cash
and calendar postings, and full peer coverage. Surviving contract cursors and
retained schedules advance; original economics/payment indices remain immutable.
Eligible fully settled terms lose ownership but retain their archives/cash.
Normal owner funding introduces no revenue gate and no automatic payment.

Two-team/two-transition tests cover restart, historical transition retry, explicit
intervening payroll, retained debt, expiry, stale/partial closing rollback and
posting-type/missing-peer tamper. Calendar contract context format2 separates
current state from the economic archive; legacy contexts/inventory reject after
advancement rather than showing stale current contracts. Native format2 inspection
passed synthetic Windows pipe checks. Never-held veteran signing and explicit
calendar-aware Store releases now have supported paths; other post-transition
signing/trade/restructure paths remain guarded. Payments, reads and
further supported transitions work. This does not complete playable franchise
season advancement, rookie lifecycle, official posting or actual guest save hooks.

## Never-held veteran signings after rollover

Current sourced cap/floors now permit ordinary signing of a registered veteran
with no historical contract on that team, subject to exclusive league ownership.
The new agreement's calendar anchor is its actual signing year, and subsequent
transitions age it relative to that anchor. Older agreements retain their own
anchors. Historical re-signing/renewals and dated postroll lifecycle mutations
remain guarded.

Postroll sign events persist exact calendar, financial and cash postings. New
payment events also record calendar views; earlier supported unmarked payment
events remain compatible with strict canonical monetary replay because payments
cannot age agreements. No owner funding is silently recorded as payment.

## Calendar-aware releases

`release_calendar_preseason_veteran` binds the exact current generation and
release year, preserving economic archives and original salary/payment indices.
Retained charges anchor at the release year and age once on later transitions.
Ownership removal, cash/cap postings, receipt checks and final connection checks
commit together; historical retries return their original receipt. The supported
healthy preseason scope still excludes unresolved liabilities.

Explicit `calendar_v2` inspection reports the release cursor separately, checks
retained allocated cash, and preserves the archived contract. Legacy inspection
rejects these releases. Explicit manual native requests require calendar_format
and exact generation identity; full/compact receipts bind year, allocated cash
and revision. Receipt capacity and final connection checks run before commit.
Actual guest transactions remain pending.

Whole-Store history tests cover actual guaranteed-base conversion and incoming
assignment before anchoring/rollover/release/restart/another rollover. Conversion
bonus indices and original amendment plans remain immutable. Seller bonus debt
and buyer base guarantees stay separate. Accelerated guarantee cap charges may
age out while unpaid nominal future guarantee cash remains recorded; cap timing
must never erase cash liability. These are synthetic histories, not decoded saves.

## Calendar-aware assignment prerequisites

The seller Ledger has an explicit exact-generation calendar assignment path.
Its immutable economic contract and prior amendment/incoming plans remain intact;
the outgoing plan records the advanced original salary-year cursor and sourced
trade year. Earned prior base remains in seller cash ceilings, transferred future
base does not, and retained bonus charges start at the actual trade year. This
path validates before mutation and preserves legacy postroll guards. It is not
an atomic paired Store trade: paired replay and rollback, native versioned
accounting/receipts and guest wiring remain open.
Store inspection rejects these outgoing archives until that protocol exists.

The receiving Ledger explicitly recalculates the original plan, binds canonical
source and destination generation identities, and enforces current cap and salary
floors before mutation. Its new agreement anchors at the actual trade year, with
independent buyer base indices; later rollover ages it once. Prior released or
assigned agreements remain separate. An expired prior agreement is eligible only
through the saved view's authoritative exhausted-term/fully allocated settlement
facts, never merely because its schedule ended. Prior debt/cash is preserved.
Legacy assignment paths still reject after rollover.
