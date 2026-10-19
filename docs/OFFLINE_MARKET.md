# Offline franchise pricing

The local-rules negotiation backend now has a price-book generator. It runs
without a model, SDK construction, credential refresh or network access. Market
prices are independent of the offer submitted and the club's available room.
The ledger still decides affordability, earned salary, retained bonuses, minimums,
rookie rules and whether an agreed deal can actually be signed.

## Price inputs

`franchise/market_pricing.py` accepts dated, sourced annual contract values and a
reference cap, explicit player positions/classifications and annual salary floors.
It rejects rating fields, fitted cap-charge fields, duplicate players and foreign
performance identities. Prices scale by current cap / reference cap, rather than
applying SOFTDRINK's four-to-one encoding scale a second time.

With missing/incomplete performance, a player's own sourced APY remains the
anchor. Without an own source, at least three other veteran positional comparables
are needed for a median prior. This is an authored simulator prior, not a claim
that every unsigned player deserves starter compensation. Sparse cohorts stay
unpriced. Rookie contracts do not depress the veteran distribution.

Complete same-window, same-mode production with at least eight games can rank a
player into the observed positional annual-value distribution. Current supported
production measures are passing/receiving/rushing yards per game and sacks per
game. They are limited valuation signals, not a complete measure of football
quality. Positions without supported production retain their sourced anchor.
Missing statistics never become zero; partial seasons and different observation
modes are not mixed. Role, injury and age valuation remain future work.

The generator finds the least balanced native contract satisfying both the asking
annual value and every annual base-salary minimum. Bonus percentage and term are
explicit authored asking preferences, not reconstructions of source guarantees.
It refuses unrepresentable demands instead of shaving money to fit the cap.
Quote provenance is compact enough for native IPC; detailed inputs/reports remain
in the export, linked by a canonical content hash in the negotiation journal.

## Pinned opening-roster adapter

`python3 -m tools.export_local_market SAVE BINDINGS AUDIT --team Giants`
previews a policy and report without changing saves or databases. `--output NEW`
creates a policy exclusively, with signing disabled. Explicitly selecting that
file through the local-rules provider is a separate launch decision.

The adapter reuses existing identity/ownership/contract-source reconciliation and
the adopted completed-game-season minimum policy. It reads position byte 0x35
using the pinned BAD-AL format definition, never ratings. The September 2026 audit
contains actual `headline_dollars.apy` separately from fitted remaining cap
schedules. Unambiguous observed UFA/SFA/extension contracts enter the veteran
market. Acquisition labels such as Franchise are retained by the source on
negotiated multi-year deals (Burns, for example); matching multi-year term
evidence admits these while one-year tags/tenders remain excluded. Drafted/UDFA
contracts, special tenders, modeled schedules, changed source terms and unresolved identities are excluded explicitly. Supported registered
free agents can use the positional prior even without an own historical APY.
This adapter supports that pinned 2026 opening; future source refresh/aging is
not inferred. The pricing core itself is independent of the mod and money scale.

`python3 -m tools.build_local_pricebook INPUT --output NEW` accepts the generic
server-owned input schema. Keep the input/report with the generated policy so
its content hash can be audited. Neither command activates a service or signing.

## Evidence and remaining delivery

The cached opening snapshot produces 816 veteran comparables and 393 Giants/free-
agent quotes. All quotes pass the existing local runtime's configuration checks
and exact native encode/decode. No source save, ledger or live launch was changed.
The largest compact source record is 310 bytes; the generated-price bridge test
fits within the native 4 KiB response limit even with verbose source inputs.

Sixteen new checks cover star pricing, insufficient/mixed observations, rookie
exclusion, source APY vs fitted charges, cap scaling, native rounding/minimums,
server-owned prices, refusal of hidden ratings and the actual local proposal path.
Existing local bargaining/auction checks also pass. In the cap-pressure fixture,
a $300M cap is unchanged: existing $200M contracts plus a $20M roster reserve
permit four $20M signings and reject the next without changing the books. This
is a behavioral constraint check, not a calibrated league-wide cap distribution.

The full Python run attempted 1,063 tests: 1,062 passed and one new fixture had a
setup error. That fixture was corrected; its entire pricing group and the later
adapter/bridge checks pass in targeted reruns. No earlier failed full run is
reported as green. Portable native protocol validation passes, including an actual generated-price
reply and a tampered-price negative case through the strict native validator. The combined Windows game/addon compiled. Six headless Windows checks pass,
including explicit local-mode startup, protocol, held signing, one-use issuance,
cap enforcement and stage-aware signing. Matching EXE/addon game validation
passes in the isolated profile; no live binary replacement occurred.
Actual offline negotiation/signing, cap reconciliation and save/reload on the Deck
remain unverified. Offseason auctions have no verified native clock/bid binding;
see LOCAL_AUCTIONS.md. No live playability claim follows from these fixtures.

Keep the scheduled task off. No AI controls, IAM grant, credentials or inference
budget were renewed. Develop against snapshots; no repeated Deck/menu prompts.

Price generation does not certify the opening cap room. The existing dated
contract-source reconciliation explicitly lacks a complete retained/dead-money
opening book. Those obligations must be reconciled before claiming accurate
whole-franchise cap room; new asking prices must not conceal missing liabilities.

## Cap difficulty acceptance

The user wants regular, consequential cap decisions. Do not manufacture these
by reducing the league cap, erasing earned pay, discounting player demands to
club room or inventing opening liabilities. Accurate opening obligations and
independent market demands must create the pressure. Rookie savings and rebuilding
room are legitimate; a strong roster should face choices about whom to retain.

Before calling the economics calibrated, compare all 32 clubs over multiple
seasons: available room after roster reserves, attempted signings refused by the
cap, starters lost/replaced, rookie savings and future bonus/dead-money charges.
An over-cap refusal fixture proves enforcement, not realistic difficulty.

The private combined patch is staged under the Deck build directory at
`offline-franchise-v1/package`. It contains matching validated EXE/addon,
committed Python sources, NBC native definition, signing-disabled policy preview
and checksums. It excludes retail assets, saves, databases and credentials.
It is not installed or activated; its preview must be rebound to the disposable
franchise registry before any negotiation test.

## Retained opening debt through amendment signing

The read-only signing checkpoint and owned-player preflight now distinguish
native roster payroll from separately declared retained opening obligations.
The ledger must equal the exact saved contract schedules plus those retained
records. Unknown credits, source-cap adjustments, altered contracts and unmatched
native accumulators remain outside this adapter. This does not establish that
the imported list is complete or invent missing MyNFL1 dead money.

The existing native amendment projection includes these obligations and roster
reserve in enforced payroll, keeps the league ceiling fixed, and rounds only
the aggregate liability upward to native units. The free-agent native signing
path still refuses supplemental debt because it lacks this payroll adapter.

Six authored checks exercise the actual saved-amendment journal: retained debt
survives one-use issuance, settlement, store reopen and idempotent retry; debt
can make an otherwise affordable native-roster offer illegal; fractional debt
rounds conservatively; unverified credits and a reduced saved payroll fail
without committing finances. The full Python regression passes: 1,074 tests. Native runtime bytes are
unchanged in this batch.
These are offline fixtures, not observed Deck gameplay or a complete opening
cap reconciliation. Follow-on saved checkpoints are now handled by the combined candidate described
in PRESEASON_OPENING.md; real Deck and preseason opening-book verification remain pending.
