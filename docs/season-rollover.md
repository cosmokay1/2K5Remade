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
path validates before mutation and preserves legacy postroll guards. Paired Store
commit/replay is now implemented below; native versioned accounting/receipts and
guest wiring remain open.
Legacy calendar inspection rejects these outgoing archives; explicit calendar_v3
inspection reports their sourced trade cursor separately from archived terms.

The receiving Ledger explicitly recalculates the original plan, binds canonical
source and destination generation identities, and enforces current cap and salary
floors before mutation. Its new agreement anchors at the actual trade year, with
independent buyer base indices; later rollover ages it once. Prior released or
assigned agreements remain separate. An expired prior agreement is eligible only
through the saved view's authoritative exhausted-term/fully allocated settlement
facts, never merely because its schedule ended. Prior debt/cash is preserved.
Legacy assignment paths still reject after rollover.

`trade_calendar_preseason_veteran` commits exact seller/buyer generations,
ownership and both financial/cash/generation/calendar postings in one write
transaction. Separate calendar trade events and request namespace preserve
historical retry after another rollover. Replay requires exact shared peer facts,
both participants' before/after snapshots, canonical types and current-year plans;
missing peers, downgraded event types and inconsistent postings reject. Receipt
and final connection gates precede ownership/event writes; failure of the second
event rolls the entire transaction back. Legacy routes remain guarded, and this
Store method is not yet a native or actual guest transaction.

Store history checks now cover a return assignment to a former club, preserving
both earlier generations and the seller's retained bonus debt while the new
receiving agreement ages independently. Original and return receipts remain stable
through later payroll/rollover. A transferred-guarantee chain also covers buyer
release, explicit payment and future unpaid cash after cap acceleration ages out.
No archived liability or cash payment is erased because ownership changes.

## First calendar-aware guaranteed-base amendment

The Ledger has an explicit exact-generation path for the first supported
postroll guaranteed-base conversion. The immutable original contract remains
unchanged; the amendment's input differs only by the derived elapsed cursor.
New bonus allocation uses original salary-year indices and the remaining term,
with unchanged nominal cash and allocated paid history. Current-year/floor/source
checks and complete updated agreement/view validation precede mutation. The active
amended schedule anchors at its actual year; later release/assignment schedules
use their own years while preserving amendment history. Repeated layered
conversions remain unsupported and reject before mutation. This is Ledger
accounting only; durable Store replay and native/game routing remain open.


The first calendar-aware amendment now has a distinct format4 Store event and
an explicit manual_restructure request using calendar_format=calendar_v1 and the
current generation_id. Its format2 receipt identifies the original league year
and agreement; retries preserve that historical receipt after later rollover.
Full and compact native receipts are supported. This remains synthetic sidecar
integration, with actual game mutation and save/load verification outstanding.


Repeated-conversion implementation boundary: the explicit pure
calculate_layered_preseason_restructure reconciles existing bonus components and
requires every old bonus fully paid, settled prior salaries, unpaid current/future
salaries, a fresh layer identity and current unconditional guarantee/floor facts.
It appends the new layer without resetting old allocation indices and preserves
nominal cash and paid allocations. The existing first-conversion API still rejects
layered contracts; no durable repeated-conversion route is enabled yet.
Next implement immutable prior amendment plans plus a separately versioned second
amendment event/receipt; replay must validate birth terms through every prior plan
and current cursor, retaining all sources and payment indices before write support.


Immutable repeated-conversion history is now available on GenerationAgreement:
prior_restructures holds prior plans, restructure is latest, and the detached
amendment_history_snapshot has its own format marker. Source-year increments
must equal original contract elapsed-index increments; terms and old layers
remain identical across each boundary, and paid components cannot disappear.
The explicit Ledger layered calendar API validates this history before mutation.
The legacy format1 generation snapshot refuses history-bearing state. A versioned
Store event and snapshot plus native routing must be added before durable repeated
conversions can be enabled.


Explicit Ledger generation_snapshot(history_format=2) now carries a detached
amendment_history on every agreement and root format2. Default format1 continues
to reject history-bearing state. The next Store event must use explicit format2
before and after snapshots even when its opening agreement has only one amendment.
Subsequent payment and rollover wrappers must also preserve and validate this
history; old format1 events remain replayable before repeated conversion.


Repeated later-year conversions now use the distinct format2 Store event
calendar_layered_restructure, with explicit history snapshots before/after.
Subsequent cash payments and affected team rollover wrappers validate complete
history; mixed-team transitions keep unaffected teams' original wrapper shapes.
The sidecar manual_restructure operation selects this path only with
calendar_format=calendar_v2 and exact current generation_id. Format3 full/compact
receipts carry the complete prior/latest amendment history, which the native
client validates against terms, cash, bonus layers and original-year progression.
Actual Windows repeated-path pipe execution remains pending CI. Store release and
assignment paths for history-bearing agreements remain guarded until their own
history-aware event/receipt support is added.
