# Cap posting precision: verified rule and unresolved implementation

The [executed NFL–NFLPA CBA](https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf)
Article 2 section 5, printed pages 6–7 (PDF pages 22–23), expressly applies nearest
$1,000 rounding to Team Salary. Article 13 section 5, printed pages 107–108,
defines applicable obligations in daily Team Salary. This confirms exact internal
fractions alone do not establish an official posted NFL Team Salary.

The reviewed source does not specify component-before-sum versus aggregate-after-sum
posting order or exactly halfway tie handling. Two synthetic components of $600
illustrate material ambiguity without a tie: independently rounding yields $2,000;
summing then rounding yields $1,000. Do not silently choose either as authoritative.

Other reviewed provisions:

- Article 13 section 6(b)(i), printed pages 109–110: straight-line signing bonus
  allocation, maximum five years. No separate rounding/residual allocation stage found.
- Article 13 section 6(d)(iv), printed page 122: covered unpaid guaranteed salary
  enters current Team Salary at present value upon release. No posting sequence found.
- Article 7 sections 1 and 3(f)–(g), printed pages 22–23 and 31–33: rookie compensation
  and equal bonus allocation. No independent per-contract nearest-$1,000 rule found.
- Article 7 section 1(g)(iii)(B), printed page 24: compensatory formula allotment
  explicitly rounds to the nearest dollar; do not replace this with thousand rounding.

Current engine keeps exact source obligations and applies its experimental exact cap
limit consistently. It does not yet implement verified official rounded postings.
Rookie allocations/allotments and nominal contract cash remain distinct quantities.
A production posting policy requires an authoritative worked reconciliation establishing
order and tie behavior, with a sourced/versioned policy and independent boundary tests.
Do not rewrite existing exact obligations or erase release debt to satisfy rounding.
