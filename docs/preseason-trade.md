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
No overwritten contract/cash/retained IDs; reject unsupported return-to-prior-club
contract generations. Preserve old-club personality/promises/history and do not score
old promises against new-club observations automatically. No trade authority exists yet.
