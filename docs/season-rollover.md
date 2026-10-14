# Durable season transition — implementation worklist

Current source has no executable year rollover. This document records the
required implementation boundary, not a completed rule or transaction.

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
