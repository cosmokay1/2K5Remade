# Local free-agency auctions

The sidecar now supports pending veteran bids and deferred round resolution
without an LLM. This is implemented and tested at the service/ledger boundary.
**The game's native offseason clock, bid submission and competing-bid hooks are
not bound yet. Do not describe this as working offseason gameplay on the Deck.**
The existing native free-agency flow has not been replaced or deployed.

## Implemented flow

1. A server-owned window declares participating registered players, an opening
   simulation tick, a closing tick and its source. Clients cannot provide or
   override deadlines. Unknown native offseason phases still fail closed.
2. Submit an affordable offer. A player can reject a lowball, counter, or hold an
   eligible offer as **pending** until the round closes. A pending offer is not
   consent, a contract, a cap charge or guest write permission.
3. Pending offers earmark current-year cap room in the auction book. Submitting
   another offer counts the club's existing earmarks; replacing a bid replaces
   its earmark. Withdraw a pending bid before closing to release it. Normal
   spending outside the auction can change affordability, so resolution and final
   signing both revalidate finances.
4. At closing, resolve only actual recorded bids. Current cap/minimum/ownership
   checks run again. A player selects an acceptable offer by exact annual value,
   protected money and recorded security/loyalty/trust preferences. An exact tie
   goes to the first recorded bid, not a client-chosen request ID. Players are
   processed in stable identity order; this is a simple clearing policy, not a
   league-wide optimal matching algorithm. No competitor is invented.
5. Selection records an ordinary accepted proposal. Losing/invalid pending bids
   release their earmarks. A selected proposal remains earmarked until the ledger
   records actual ownership. There is no automatic game-memory or save write.
6. The existing signing authorization, guest journal, cap reconciliation and
   save/reload path must consume that proposal. Signing remains separately gated
   by the explicitly enabled local signing policy. Changed finances, ownership or
   negotiation history can invalidate consent; selection cannot bypass those
   checks. Cancellation/renegotiation of a selected agreement is not implemented.

Lowballs atomically apply the existing bounded respect consequence in the normal
negotiation ledger. Retrying the request applies it once. Restarting the service,
increasing the bid or entering an adjacent round cannot erase recent offense or
reset recent submission counts. Patience limits apply throughout a configured
round. A later window preserves accumulated respect changes. Proposed promise
goals survive pending offers and selection; this policy does not fabricate a
monetary value for them. Rookie auctions and active-contract auctions are excluded;
existing rookie accounting and active-player negotiation remain separate paths.

Auction records live in two tables in the existing franchise database, separate
from financial postings. Reaction/proposal events and auction updates share one
SQLite transaction. Deadline rollback, disabled access, disconnect, changed clock
and an oversized response abort writes. Pending bids never reserve actual NFL cap
charges or claim cash has been paid.

## Configuration and API

Add an optional `auction` object to an explicitly selected local-rules policy:

```json
{
  "id": "unique-franchise-round-id",
  "opens_at": 4,
  "closes_at": 7,
  "player_ids": ["registered-player-id"],
  "source": "Explicit source for this simulation window"
}
```

Those ticks illustrate the schema; they are **not** a discovered offseason
mapping. Every participant requires sourced asking terms in `quotes`. A window's
identity, deadlines and business policy cannot be changed by restarting it.
Overlapping windows for the same player are refused. Explicitly changing signing
permission and restarting does not reset the auction. Ordinary local negotiation
for configured auction participants is refused, preventing immediate-signing
bypass through that path. Operator-only manual financial operations remain explicit.

The hello operation advertises these additional operations only when an auction
is configured. All use protocol 1 and a stable request ID:

| Operation | Additional request fields | Result |
| --- | --- | --- |
| `auction_bid` | `team_id`, `offer`, `expected_revision`; optional `contract_format`, `promise_goals` | Pending, counteroffer or rejection; never signed |
| `auction_withdraw` | `team_id`, `player_id` | Withdrawal of a pending bid before closing |
| `auction_status` | `team_id` | Own bid states/earmarks and declared round outcomes |
| `auction_resolve` | None; time is server-owned | Recorded selections after the closing tick |

The public bridge restricts club submissions to the policy's team. The internal
`LocalAuction.bid` interface accepts trusted engine-sourced competing club bids;
there is no automatic CPU bidder and no extraction of native rival offers yet.
Resolve returns selected `proposal_request_id` values for the existing signing
journal. Every auction response explicitly has `write_authorized:false`. Mutating
auction requests use the existing single-worker sidecar queue and frame limits.

## Validation and next binding

22 authored checks cover waiting, competition, security/ties, combined cap
capacity, concurrent bids, withdrawal, offense/patience/restart, neighboring
rounds, changed cap, partial clearing, permission changes, response/transaction
rollback, clock changes and preserved promises. An authored 32-team guest-save
fixture takes a native-encoded winning bid through existing journal preparation,
$4.766M/$3.523M annual charges, settlement/retry and database reopen. This is not
real-game signing evidence. Run:

```sh
python3 -m unittest discover -s tests -p test_auction.py
```

Broader pass: 1,052 tests attempted. 1,039 passed immediately; 10 known socket
checks were explicitly skipped and one newly added socket check was blocked by
the same sandbox restriction. Two multiprocessing checks initially failed because
the temporary validation runner lacked a main guard; that runner was corrected
and both checks passed separately. No source test was weakened or removed.
Logs: `/tmp/2k5-auction-targeted.log`, `/tmp/2k5-auction-full-suite.log`,
`/tmp/2k5-auction-budget-recheck.log`.

Next required evidence: a disposable franchise at the native free-agency period,
its before/after advance saves and observed bid state. Pin the phase descriptor,
round progression, actual competing offers and acceptance/apply callbacks before
wiring the native menu to these operations. Never infer that raw phase codes or
calendar labels alone prove those semantics. Keep the scheduled task and live
Deck configuration unchanged until that combined integration test is prepared.

October 18: the local runtime and auction service checks also pass in the combined
pricing regression group. The combined Windows host compiled and passed local-
mode/protocol/signing-boundary fixtures. This still does not bind the native
auction calendar, competing bids or offseason menu; that acceptance remains open.
