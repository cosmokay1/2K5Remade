# Local negotiation without an LLM

The explicit `local-rules` provider uses the existing contract editor, negotiation
journal, cap/minimum/rookie checks, earned-salary amendments, saved-signing
coordination and one-use native authorization path. It does not instantiate an AI
client, read Google credentials, initialize inference budgets or fall back after a
Vertex failure. Choosing local rules is a separate, explicit launch decision.

## Behavior and persistence

- Asking terms come from a sourced, server-owned policy file, never the submitted
  offer. Money, security, loyalty, patience, trust and respect affect bargaining.
- Offers below 65% of asking annual value offend the player. The ledger applies
  the existing bounded respect consequence exactly once. Increasing the next
  offer does not erase the offense.
- Two to four submissions are allowed per window, depending on patience. A new
  window requires two saved simulation steps. Service restarts, new request IDs,
  quote changes and switching providers cannot reset the current local window.
  Simulation time cannot move backward relative to recorded local negotiations.
- The clock reads the server-selected save. Supported observed preseason,
  regular-season and postseason horizons map to sequential steps; these are an
  authored simulation cooldown, not real NFL calendar days. Unsaved progress does
  not reopen talks. Unmapped native offseason phases still fail closed. The local auction backend
  now supports pending bids and timed resolution; see [LOCAL_AUCTIONS.md](LOCAL_AUCTIONS.md)
  for its implemented service flow and remaining native binding.
- Asking contract, source, policy hash, clock, window cursor and any performance
  inputs are recorded with the decision in the existing atomic SQLite journal.
  There is no separate bargaining database or client-controlled reset operation.
- Brief stable agent dialogue explains acceptance, counteroffers, lowballs and
  exhausted talks. Retrying a request replays its recorded response.
- Agreement does not mean signing succeeded. The existing financial and native
  gates still enforce exact salaries/bonus representation, old bonus obligations,
  earned base pay, minimums, rookie rules, cap room, identity, revision and save
  reconciliation. Counteroffers are not lowered to fit the club's cap room.
- Proposed promises are preserved on counters. This policy does not assign them
  invented dollar values or claim to evaluate winning, playing-time promises,
  market/media momentum or teammate relationships yet.

## Explicit launch and authorization

Set `NFL2K5_FRANCHISE_PROVIDER=local-rules` and
`NFL2K5_FRANCHISE_LOCAL_CONFIG` to a private policy file. Keep the existing Python,
verified database, guest-save/bindings/revision and editor/signing launch settings.
Remove AI budget launch arguments for local mode: mixed local/AI configuration is
rejected. The CLI equivalent is:

```sh
python -m franchise.sidecar --database /private/franchise.sqlite \
  --provider local-rules --local-config /private/local-rules.json \
  --guest-save /private/SAVEGAME.DAT --guest-bindings /private/bindings.json
```

The hello response explicitly reports `ai_enabled:false`,
`negotiation_enabled:true`, `decision_mode:local-rules`. The native client checks
that this matches its selected launch mode before granting submission capability.
Observation-only bindings do not acquire negotiation or signing permission.

Example policy shape (illustrative amounts, **not** a real player's valuation):

```json
{
  "format": 1,
  "enabled": true,
  "signing_enabled": false,
  "team_id": "Giants",
  "quotes": {
    "registered-player-id": {
      "offer": {
        "player_id": "registered-player-id",
        "salaries": [6000000, 6000000],
        "signing_bonus": 8000000,
        "guaranteed_salaries": [0, 0]
      },
      "source": "Explicit asking-price source in this franchise's dollar scale"
    }
  }
}
```

A missing quote refuses negotiation for that player. Asking terms must be in the
franchise's money scale and exactly representable when native counters are used.
The runtime does not manufacture a whole-roster price book from hidden ratings.

`signing_enabled:false` allows proposals but denies automatic direct signing and
saved-signing preparation/authorization/settlement. Enabling signing requires an
explicit policy edit and service restart. Removing, disabling or changing the
policy file revokes an existing service's access, including checks at financial
commit. A new service validates the complete policy before enabling access. This
local authorization file does not renew or change any cloud shutdown control,
IAM grant, credential or budget; it is not a replacement remote control service.

## Optional sourced performance pricing

A quote may include both `performance` (the canonical
`PerformanceEvidence.to_context()` schema, for that player, with
`complete_window:true`) and `adjustment`:

```json
{"counter":"receiving_yards","reference_per_game":80,"minimum_games":8}
```

This is an authored, deliberately bounded simulator policy: observed production
per game divided by the explicitly sourced reference changes the baseline asking
price within 75–125%. Missing production or insufficient observed games retain
the baseline, with factor 1 recorded. Supported pricing counters are passing,
receiving and rushing yards, and sacks. It never consumes the client-supplied
performance dictionary as a pricing source. Native adjustments operate on exact
amount/proration units and record the resulting asking contract; they do not
round cap charges to make a transaction fit.

The policy importer must supply verified complete-window evidence. The original
saved-history exporter deliberately does not assert complete seasons or map raw
modes to played/fast-sim coverage, so those records are **not automatically
relabeled** as canonical complete performance. Automatic real-roster market-price
sourcing and historical-stat normalization remain separate work.

## Evidence and delivery boundary

Offline integration tests exercise local acceptance/rejection/counters, durable
lowball/cooldown/patience/retry behavior, explicit authorization, policy revocation,
clock changes during a request, sourced pricing and native unit preservation.
An authored 32-team saved-signing fixture exercises proposal, journal preparation,
exact $4.766M/$3.523M annual charges, settlement retry and database reopen. An
active-contract fixture preserves already-earned salary and the original bonus
through local consent, settlement and reopen. These are not real-game evidence.

Run Python checks with `python3 -m unittest discover -s tests`. The portable native
protocol fixture covers local/AI handshake separation and cloud-free launch args.
Windows host/game compilation and a real Deck negotiation/signing/cap/save-reload
acceptance test are still required. No install or live configuration was changed
by this side conversation; it leaves the main thread's simulation profile and
scheduled-task state alone. Keep the new source batch together with the main
thread's pending transport fix when preparing a Windows candidate. Do not deploy
this source change by copying Python alone: the native handshake/launch changes
also require rebuilt owning binaries.

Validation of the preceding local-runtime batch: all 16 runtime integration checks and 12 local
decision/ledger checks passed. The full Python pass ran 1,022 tests: 1,012 passed,
and 10 unrelated web/presentation-server tests were blocked at loopback socket
binding by the sandbox (`PermissionError: Operation not permitted`). Do not label
that full pass green. The newly compiled portable protocol check passed. Logs:
`/tmp/2k5-local-runtime.log`, `/tmp/2k5-local-full-suite.log`, and
`/tmp/2k5-local-native.log`. Windows host compilation was not attempted here.

October 18 combined development: sourced market generation now supplies native-
exact asking quotes without hand-entering each contract (OFFLINE_MARKET.md).
The combined Windows game/addon compiled, six affected headless Windows checks
passed, and isolated paired game validation passed. This supersedes the earlier
"Windows compilation not attempted" boundary for that candidate only. No live
negotiation/signing or save/reload acceptance is claimed; no live install occurred.
