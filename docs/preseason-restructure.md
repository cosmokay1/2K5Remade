# Preseason base-to-bonus restructure calculation

Supported engine amendments now commit and replay durably. Actual game amendments
remain unverified; no HTTP or native restructure command is exposed yet.
The first supported calculation converts positive unpaid, unearned, fully guaranteed
current veteran base to an unconditional signing bonus, keeping the term unchanged.
Explicit health, consent, eligibility, actual preseason dates, annual minimums and provenance
are required. Original signing bonus must be paid, past base settled and remaining
base unpaid. Existing additional layers and unsupported compensation/protections are
rejected. Annual floors are supplied source assertions, not inferred player facts.

## Preserve original bonus schedules

An immutable BonusLayer records an identified amount, original-year start index,
allocation years and source. ActiveContract adds each layer to the original schedule;
original Offer.signing_bonus is never reset. Empty layers preserve legacy serialized
shape. Nonempty layers round-trip through typed opening books, but Ledger and rookie
opening imports reject them to require historical amendment events instead of importing unexplained layered balances.
Pure release and trade calculators preserve every layer. Opening imports remain closed; supported durable amendments use explicit events.

Synthetic arithmetic example: original seven-year contract with bonus10 spread over
five years and two elapsed years has remaining bonus charges(2,2,2,0,0). Remaining
bases(10,20,30,40,50), conversion8 and a five-year new layer produce exact charges
(28/5,118/5,168/5,208/5,258/5). Reallocating old remaining6 plus new8 together would
incorrectly move old debt into later years. Small amounts illustrate arithmetic;
they do not satisfy actual NFL minimum salaries.

Nominal compensation and paid history remain unchanged. Creating the new bonus does
not record its payment. Deferred new-bonus payment terms are explicitly excluded. The plan preserves the original contract/cash and amended
terms; component payment ceilings, protected bonus reporting, revision checks, idempotent
receipts, replay and subsequent supported release/trade commits preserve every layer.
Exact internal fractions follow the unresolved rounding policy in cap-posting-policy.md.

## Primary rules and limits

[Executed 2020 CBA](https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf):
Article13 section6(b)(i), printed109–110, straight-line signing bonus allocation capped
at five years; section6(b)(iii), printed111, bonus/modification consideration;
section8, printed125–127, renegotiation restrictions; Article26 section1, printed171,
annual minimum salaries; Article4 section9, printed12, earned base protection.
These support the modeled components, not automatic verification of supplied facts.
The calculation rejects terms extending past2030 to avoid unsupported final-CBA-year
rules. Extensions, repeated amendments, rookies, voids, offsets, benefits, contingent
compensation and actual game synchronization remain unsupported.

## Subsequent pure lifecycle calculations

For the elapsed synthetic example above, release after June1 retains cap charges
(128/5,52/5): protected remaining base22 plus all remaining bonus14. Nominal cash
retained60 includes paid history30 and unpaid30 (base22 plus conversion bonus8).
Paying some conversion bonus changes unpaid cash, never cap acceleration.

Assignment after June1 requires all bonus components paid. Seller retained bonus
charges(18/5,52/5) total14; buyer bases(2,20,30,40,50) total142. Seller cash38 plus
buyer cash142 preserves original180. Original typed layer archives survive snapshot
and reconstruction. Pure and durable fixtures verify these relationships, including partial payment,
release/assignment and restart. Actual game lifecycle and payment import remain unverified.

## Durable authority

FranchiseStore.restructure_preseason_veteran verifies exclusive ownership and stored
annual floors under a write transaction, records original contract/cash plus both
before/after snapshots, and checks final access before publication. Financial and
cash revisions each advance once; ownership and nominal/paid cash stay intact.
Exact retries return the original receipt, including after a later release.
Replay recomputes from actual prior state and rejects original/posting corruption.
Reused layer identities, stale revisions, unsupported terms and repeated layered
conversions reject before mutation. Liability exclusions must be canonical unique
serialized lists; dictionary values are never discarded during reconstruction.
