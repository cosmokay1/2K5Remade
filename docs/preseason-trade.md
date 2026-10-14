# Supported preseason trade calculation

`calculate_preseason_trade` is a pure contract-assignment plan. It changes no ledger,
ownership or game state. Mandatory sourced scope establishes healthy preseason
eligibility before both clubs' first regular-season games, zero earned current base,
assignment consent and absence of unsupported compensation/restriction liabilities.
Payment history must be fully allocated: signing bonus paid in full, prior bases
settled and remaining bases unpaid. Unpaid/deferred bonus rejects because contractual
responsibility cannot be inferred solely from cap retention.

Seller retains original bonus acceleration, paid history and a paid-only nominal cash
record. Buyer receives remaining base salaries with unchanged guarantees, no original
signing-bonus proration, and matching unpaid nominal base cash. Original contract/cash
are archived in the plan. No guaranteed-base release PV is added to the seller.

Primary source: [executed NFL–NFLPA CBA](https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf),
Article 13 section 6(b)(ii), printed page110 (traded assignment bonus acceleration),
section6(d)(iv), printed page122 (covered release PV), and AppendixA paragraph17,
printed page341 (assignee performs contract). Exact official posting precision remains
unresolved as described in cap-posting-policy.md.

Independent synthetic example: base(10,20,30), paidbonus9, protectedbase(0,20,10).
Seller retains9 beforeJune2 or(3,6) afterward; buyer carries(10,20,30). Sellerpaid9
plusbuyerunpaid60 preserves nominal69. Protected future30 transfers and is not cancelled.

Next durable work must atomically rebuild both teams, verify both revisions and buyer
funding, archive source terms, update ownership and insert linked events. Each role
must compare its actual pre-event state/contract/cash against common source fields.
Matching two event payloads alone can conceal identical fictional-source corruption.
Use nonrecursive participant replay in one read transaction and final ownership checks.
No overwritten contract/cash/retained IDs. Format4 generation-aware assignments
now support return to a prior club while preserving that club's old debt. Preserve old-club personality/promises/history and do not score
old promises against new-club observations automatically. The store now exposes `trade_preseason_veteran` for explicit sourced contract assignment.
One write transaction checks both revisions, applies both financial/cash postings,
reassigns ownership and inserts paired records. Exact retries return the original
receipt; conflicting identities, missing links and inconsistent source state reject.
When assignments exist, nonrecursive replay validates every team independently in
one read transaction, including actual seller terms and both prior/result snapshots.
This prototype favors correctness; larger-history runtime cost remains to be measured.
Trade consideration, guest draft assets and actual game trade controls remain
unsupported. The native service supports explicit manual trades.

## Generation-aware assignments

Format4 supports returned/assigned source contracts and receipt by a former club.
A receiving agreement gets contract-gen: plus SHA-256 of compact UTF-8 JSON
["assignment",team_id,player_id,trade_request_id]. This identity is distinct from
free-agent return IDs. Its cash ID matches; immutable ancestry records identify
the source club and agreement. Closed prior contracts/cash/retained charges stay.

Versioned paired generation_trade_out/in records carry seller/buyer identities,
the receiving club's prior identity (null only when absent), and full before/after
generation postings for both books. Strict replay checks each side and its paired
source. Ownership and both journals commit atomically. Historical retries return
original receipts without restoring old ownership or changing later agreements.

Native manual_trade uses seller_generation_id and buyer_previous_generation_id
for this mode; explicit IDs select versioned assignment even for a legacy source
and a first-time receiver. Both fields must be provided together. The buyer ID
can be null when no previous agreement exists; the seller ID cannot. Source/parent
IDs must match under the transaction lock. The response echoes these and the new
buyer_generation_id. C++ checks cash identities, pair consistency and nominal
conservation. Existing legacy requests keep their original response shape.

A→B→A can therefore retain every prior agreement and then apply supported
restructure/release/payment rules to the latest one. This does not add trade
consideration, waived-player transfer, unpaid bonuses or implicit season rollover.
Actual guest roster/contract writes remain unverified.
