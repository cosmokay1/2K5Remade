# Supported preseason release calculation

`franchise.releases.calculate_preseason_release` calculates a pure plan from original
ActiveContract, allocated original CashObligation, mandatory PreseasonReleaseScope,
explicit DiscountProfile and sourced whole-year payment offsets. It does not mutate
ledger, ownership, cash or game state. A durable adapter must verify veteran status,
recompute under its transaction, archive original terms and preserve liabilities.

Scope requires actual release and first club regular-season game dates in the declared
CBA year, healthy status, verified zero earned current-year base, unconditional covered
guarantees and sourced absence of injury/grievance/extra termination pay, additional
compensation, offsets/voids, designation and waiver-transfer liabilities. Omitting a
fact rejects. The date does not prove health or earned-salary coverage.

Payment history must allocate the original nominal contract cash. Prior bases must be
fully paid, and current/future bases unpaid. Original bonus proration is retained with
actual June-1 timing; protected base is separately valued using supplied exact rate
and whole-year offsets. Nominal cash retains paid history, unpaid bonus and protected
base. Only verified unearned unprotected base is cancelled. Discounting cap liability
never discounts the nominal cash owed. Synthetic rates in tests are not published rates.

Primary rules reviewed: [executed NFL–NFLPA CBA](https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf),
Article 13 sections 6(b)(ii) and 6(d)(iv), Article 30 and Article 45. Exact nearest-$1000
posting interpretation, real payment timing/rate provenance and guest facts remain
unresolved. This component grants no full release authorization.

The store now exposes `release_preseason_veteran` as an explicit sourced transaction.
It recomputes the plan under the write lock, archives originals, replaces cap charges,
retains nominal cash, removes exclusive ownership and records replayable before/after
postings. Stale/conflicting requests reject; exact retries return the original receipt.
Final access failure or database failure rolls back all changes. Retained cash payments
cannot allocate money to cancelled base salary. No guest, native menu or browser
release control is connected. Releases may accelerate a club over its limit;
retain the liability and prevent subsequent unaffordable signing. Same-team re-sign,
rookie/cohort releases and unsupported protections require separate lifecycle work.
