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
