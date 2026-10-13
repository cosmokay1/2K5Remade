# NFL 2K5 franchise AI delivery worklist

## Delivery target

Tested Windows and Steam Deck (Proton) packages of the independent Remade fork in which actual franchise
negotiations and draft decisions use persistent personalities, performance, relationships, and
history; all financial transactions obey the supported modern NFL cap/rookie
rules; saves preserve contracts and stories; and remote shutdown stops AI
decisions without corrupting the franchise.

**Immersion rule:** observable stats, performance, opportunities and history drive
franchise evaluation. Hidden overall/skill/potential ratings must not enter
negotiation prompts, contract valuation, scouting comparisons, or player-facing
explanations. Ratings used internally by the original on-field simulation are
outside this decision-system change; replacing gameplay physics is not required.

**A Python demo, a passing toolchain check, a synthetic bridge, or a compiled EXE
alone does not meet this target. Actual game execution and save/load verification
are required.** No completion date is promised before the runtime inputs exist.

Repository: https://github.com/cosmokay1/2K5Remade
Branch: `codex/franchise-negotiation`. Progress evidence: [WORK_PROGRESS.md](docs/WORK_PROGRESS.md).
Resume from the earliest unblocked unchecked item, respecting dependencies.

## Current blockers

| ID | Missing input | What it blocks | Independent work that continues |
|---|---|---|---|
| B01 | Legally obtained Xbox `default.xbe` and extracted game assets | Verified guest addresses, financial field mapping, real gameplay | Financial engine, persistence, negotiation, diagnostics, bridge protocol, synthetic integration |
| B02 | Raw franchise saves and companion metadata; controlled transaction pairs | Contract decoding, reconciliation and save round trips | Synthetic import fixtures, read-only diff tooling, state schema |
| B03 | Windows runtime and Steam Deck capable of running the user's legal game | Runtime reproduction, UI/gameplay validation, delivery acceptance | Portable engine tests and asset-free Windows compilation checks |
| B04 | Written upstream/third-party permission or suitable licenses | Redistribution of modified binaries and affected bundled components | Original source development, attribution, permission-request drafts |
| B05 | Explicit approval for scoped runtime impersonation delegation | Live runtime-identity read/inference verification | Offline/native recovery and financial implementation |

The user currently has no game binary/save. Never download retail assets to
resolve that blocker. Do not repeatedly ask for the same missing input. Report
the required inputs once when an otherwise ready milestone reaches that gate.

## M0 — Provenance and repeatable development

- [x] Create GitHub-recognized fork; preserve upstream ancestry/notices.
- [x] Identify our original additions and document unresolved permission scope.
- [x] Commit/push development work without publishing installers.
- [x] Add automated portable financial/negotiation tests to fork CI.
      Published at `589a2bd`; run `38457090392` passed on Linux and Windows.
- [x] Add asset-free Windows checks for our bridge/runtime additions; clearly
      distinguish these from a full game build/test. Native pipe compile/execution
      verified at `dd1ed9e`, run `38464795249`; no guest assets or game exercised.
- [ ] Keep public configuration free of credentials and retail assets.

Done when a fresh checkout can run the engine tests and CI reports their results.

## M1 — Authoritative and durable money state

- [x] Reject unknown/unclassified players and under-floor veteran offers.
- [x] Bound signing-bonus allocation and invalidate offers after budget changes.
- [x] Resolve F04 with exact rational internal bonus allocations and consistent
      cap/rookie-pool checks; display/game posting conventions still need verification.
- [x] Derive new durable opening balances from original contract terms, elapsed
      years, tenders, retained obligations and source adjustments. Existing
      roster contracts and verified sources still require game import under M5.
- [x] Add durable team IDs and exclusive player ownership for supported signings
      through `FranchiseStore`; complete imported league/rules data remains pending.
- [x] Add atomic commits, durable signing receipts, restart/rollback recovery and
      recovery from an abrupt process exit before database commit.
- [x] Store committed signing and associated story together; recalled agreements
      do not regenerate the model decision after restart.
- [x] Replace a declared rookie tender when its contract commits (F08); actual
      tender extraction remains dependent on verified game mapping.
- [x] Refuse replay/writes when recorded postings, contract charges or ownership
      disagree. Real-game import reconciliation remains pending under M5.

Done when restart, retries, competing teams, and interrupted commits preserve
exact obligations, ownership, cap balances, rookie pools, and story history.

## M2 — Modern contract and season lifecycle

- [ ] Define verified league-year rules; explicitly choose economic treatment
      for historical start years rather than silently combining incompatible eras.
- [ ] Load annual minimums and draft allotments with recorded source/version.
- [ ] Separate cash owed/paid, cap charges, guarantees, and management reserves.
      Nominal cash/payment ledger and full base-guarantee terms are implemented;
      paid guarantee allocation, settlement and management cash budgets remain.
- [ ] Model guarantee protections/vesting and supported bonus components.
- [ ] Implement releases/retirement and retained obligations/dead charges.
      Supported sourced healthy preseason veteran releases now commit/replay with
      original archives, retained bonus/guarantee debt, nominal cash and ownership
      removal. Other releases, retirement, offsets, waivers and calendar remedies remain.
- [ ] Implement atomic trades with both teams' obligations and ownership.
      Supported sourced preseason veteran contract assignments now commit paired
      cash/cap/ownership events with independent league replay. Consideration, rookies,
      unpaid bonus, return-contract generations and other trade protections remain.
- [ ] Implement extensions/restructures without erasing existing bonus layers.
      Pure sourced preseason guaranteed-base conversion and immutable bonus layers now
      preserve exact old/new schedules. Pure subsequent release/trade calculations now retain all layers. Durable cash,
      amendment replay, lifecycle commits and actual guest transactions remain.
- [ ] Implement offseason/regular-season accounting and roster-status costs.
- [ ] Implement dated June-1 treatment, supported tenders/tags and salary benefits.
- [ ] Implement incentive settlement, cap adjustments, carryover and year rollover.
- [ ] Complete drafted/undrafted rookie rules, pool accounting, option exercise,
      and performance escalators; never auto-exercise a fifth year.
- [ ] Re-audit money using independent expected examples from primary rule sources.

Done when supported operations reconcile across at least two synthetic seasons.
Explicitly reject unimplemented terms; do not silently drop liabilities. Do not
invent future published NFL values: separate verified inputs from simulation policy.

## M3 — Negotiation and story simulation

- [x] Add structured Gemini/Vertex AI decisions and a mandatory final cap gate.
- [x] Verify a real model acceptance cannot force an over-cap contract.
- [x] Add offer previews using the same financial validation as final commits.
      Durable previews also check league ownership; previews do not reserve room.
- [ ] Add player/agent and team/GM priorities with persistence and bounded updates. Source-backed immutable GM profiles now persist with original team configuration and feed private draft context; player priorities and bounded relationship updates already persist. GM evolution and actual CPU team strategy remain.
- [ ] Feed actual statistics, roles and relationship history; label missing evidence.
- [ ] Evaluate production with opportunities/context: targets/snaps, efficiency,
      drops, opponents/scheme, health, recency and sample size where available.
- [ ] Verify whether intended-receiver targets exist in guest state or saved
      counters; otherwise instrument pass release/outcome events. Handle throws
      away, interceptions, spikes and nullified plays without inferring targets
      from receptions. Persist source/provenance for each counter.
- [ ] Investigate QB pressures as observed play events: identify dropbacks,
      rushers, timing and disruption; define/test attribution and avoid counting
      each frame as a new pressure. Do not substitute proximity or sacks silently.
- [ ] Establish equivalent evidence for played, CPU-played and fast-sim games.
      If fast simulation exposes no targets/pressures, report them unavailable
      rather than zero or manufacture them from hidden ratings.
- [ ] Exclude hidden skill/overall/potential ratings from franchise evaluations;
      do not turn a generated composite grade into a new visible OVR.
- [ ] Give scouts/agents/teams imperfect observations and uncertainty; rookies
      require prospect evidence, not invented NFL statistics.
- [ ] Test similar observed histories with different hidden ratings: franchise
      decisions must not reveal or depend on the hidden ratings.
- [ ] Implement team accept/reject/counter strategy within legal financial limits.
- [ ] Make guarantees and supported nonfinancial promises meaningful negotiated terms.
- [ ] Trigger stories from committed events and actual consequences, not invented facts.
- [ ] Add negotiation deadlines, withdrawal, holdout/request state, and resolution.
- [ ] Bound inference frequency; cache recorded decisions; add usage/cost telemetry.
- [ ] Test different personalities on the same situation and validate multiweek continuity.

Done when an offline league scenario and a bounded live scenario produce distinct,
coherent negotiations and persistent consequences without violating financial rules.

## M4 — Remote control and client bridge

- [x] Verify private remote switch denies disabled/expired/unavailable handshakes.
- [x] Verify shutdown during inference and before commit leaves finances unchanged.
- [ ] Separate admin switch-write access from client read/inference permissions.
- [x] Design a versioned local bridge with request IDs, state revision, protocol
      compatibility, timeouts and explicit error handling. Native offline transaction
      verified at `d2d9e0b`, run `38465198052`; game integration remains under M5.
- [ ] Keep game thread responsive while inference runs; reject obsolete responses.
- [ ] Ship a cooperative client handshake without distributing owner credentials.
- [ ] Ensure AI shutdown preserves financial enforcement and provides a clearly
      labeled manual/deterministic decision path; no silent native cap bypass.
- [ ] Test disconnects, expired credentials, protocol mismatch and service restart.

Done when the synthetic native client completes a transaction and all failures
leave game/engine state consistent. Remote control is not tamper-proof DRM.

## M5 — Verified Remade integration (B01/B02 gate)

- [ ] Establish a baseline game build and franchise behavior with the legal game.
- [ ] Map contract records, cap/tender fields, player identity, statistics and save data.
- [ ] Trace signing, extension, release, trade, draft and year-transition functions.
- [ ] Trace CPU-controlled paths as well as user menu paths; avoid double decisions.
- [ ] Intercept a single verified free-agent signing through existing patch conventions.
- [ ] Commit legal terms to the actual game and verify readback/save/reload.
- [ ] Integrate all supported roster transactions and season advancement.
- [ ] Reconcile the external ledger and guest state before every financial write.
- [ ] Add real franchise negotiation UI with cap/cash/guarantee effects and reasons.
- [ ] Integrate persistent stories/relationships into the actual franchise experience.
- [ ] Add opt-in configuration, backups, recovery and explicit migration handling.

Done only when real guest state, engine state, displayed terms and reloaded saves
agree. Never patch guessed addresses or fabricate unknown contract fields.

## M6 — Playable Windows acceptance (B01/B02/B03 gate)

- [ ] Launch into franchise and finish an actual game or simulation week.
- [ ] Complete a veteran and drafted-rookie negotiation in the game UI.
- [ ] Show an unaffordable deal rejected in game with no roster/save mutation.
- [ ] Exercise player/CPU release, trade and renewal paths with correct accounting.
- [ ] Save, exit, restart and verify identical finances/history/ownership.
- [ ] Advance through draft/offseason into the next year without lost obligations.
- [ ] Disable remote AI during an in-flight request and verify safe manual recovery.
- [ ] Verify cloud failure does not freeze the game or corrupt its saves.
- [ ] Capture build revision, Windows environment, scenario, logs and screenshots
      or video demonstrating each acceptance case.

Done when all cases pass on the real game. Label test failures and unsupported
areas clearly; do not equate queued CI with a passing result.

## M7 — Lawful delivery (B04 gate)

- [ ] Resolve release rights and preserve evidence of granted permissions.
- [ ] Verify inherited and optional component notices in the actual artifact.
- [ ] Package an opt-in installer/source build requiring the user's own game.
- [ ] Ship setup, authentication, shutdown, backup and recovery instructions.
- [ ] Publish/attach only permitted artifacts with verified checksums and version.
- [ ] Mark the work complete only after M6 and all release requirements pass.

## Autonomous work rules

Continue useful work while external gates are blocked. Do not spend turns only
rewriting plans or rerunning passing tests without new evidence. Prefer completing
one meaningful milestone per continuation. Inspect dirty state; preserve user
changes. Update this file and the progress log with actual evidence. Commit and
push validated source changes to the fork; do not force-push upstream history.

Respect the user's shutdown command: never automatically renew or re-enable the
AI grant. Use offline fixtures by default; do not run recurring paid model tests
or provision ongoing cloud services without a concrete authorized need. Do not
send the unsent maintainer request without human authorization.

An hourly follow-up in this chat resumes this work. Keep notifications limited
to meaningful milestones, failures, new actionable blockers or verified delivery.
If every remaining item is externally blocked, record the exact gates and avoid
repeated unchanged blocker messages. Disable the follow-up when delivery is
verified or the user cancels it.

## Steam Deck and draft delivery additions

- [x] Prepare explicit-file local Proton candidate ZIP tooling and runtime requirements.
- [ ] Build a verified integrated Windows runtime with portable sidecar dependencies.
- [ ] Validate Proton pipes, controller UI, gameplay, suspend/resume and save/load on Deck.
- [ ] Package the verified runtime and record tested Proton version and file hashes.
- [ ] Implement draft choices from observed prospect production, role, personality and evidence uncertainty; exclude hidden ratings. Read-only comparison context and strict model scouting advice now validate sourced evidence, per-candidate cap/pool estimates, shutdown and stale revisions; scouting history now also persists/replays with exact eligible preview checks; durable pick commitments and actual game draft choices remain.
- [ ] Constrain draft commitments by source-backed rookie allocations and team cap; persist decisions and scouting history. Source-backed management funding earmarks now protect cap/pool availability and replay with explicit withdrawal/signing replacement; source-declared pick order and exclusive rights now commit atomically with funding; actual source import, lifecycle and guest transactions remain.
- [ ] Validate actual in-game draft hooks and save round trips.

See packaging/steamdeck/README.md. Candidate packaging is not playable delivery.

## Cloudflare web delivery

- [x] Inspect cosmokay.com and existing tunnel/DNS resources using Cloudflare plugin.
- [x] Prepare authenticated loopback HTTP franchise inspection/preview origin.
- [x] Restore Cloudflare connector write access; dedicated tunnel creation succeeded after reconnect.
- [x] Create dedicated tunnel and route 2k5.cosmokay.com; verify HTTPS 200, origin certificate validation and scoped HTTP-to-HTTPS 308.
- [ ] Add authenticated browser franchise UI and project/package section.
- [ ] Extend live negotiation/draft API with persistent transactions and existing remote killswitch. HTTP negotiation now shares durable Bridge transactions and fresh access checks; actual restricted-runtime inference and draft transactions remain unverified/unimplemented.

See docs/cloudflare-tunnel.md. Dedicated tunnel/DNS/TLS route is live; full browser franchise delivery remains unfinished.

## Negotiated promises and achieved-goal scoring

- [x] Define sourced nonfinancial goals for touches, starts, position-specific yards and team wins, with an explicit time window and player importance.
- [x] Score observed achievement with unknown coverage and period closure; keep this separate from hidden player ability and salary incentives.
- [x] Wire promise proposals/accept/reject/counters through provider schemas and the Python pipe/HTTP protocol; native/game UI remains under integration milestones.
- [x] Commit agreed promises atomically with the contract and story; preserve them across restart.
- [ ] Derive actual touch/start/yard/win evidence from verified game counters; never infer unavailable targets or starts from other stats.
- [ ] Apply goal consequences to trust, satisfaction and future negotiation with context for injury, availability and coaching choices. Scores now persist and feed player context; only known final scores can source once-only bounded relationship changes. Context-aware consequence policy and in-game story triggers remain.
- [ ] Display promised vs observed goals and fulfillment score in the game/browser interface.

## Franchise creation and personality population

- [x] Atomically create engine teams/ownership and initialize every registered player with saved fictional personality traits and neutral relationships.
- [x] Save a versioned franchise seed; preserve stable identity across teams/restart and refuse rerolls or missing initial actors.
- [ ] Connect the native franchise-creation event to verified roster import and this initialization process. A strict JSON bootstrap command now creates/replays/publishes the initialized engine DB; actual export decoding and guest hook remain.
- [ ] Verify a real new franchise save/load retains all player and team identities.

See docs/franchise-creation.md and docs/promise-observations.md. Automatic promise
mapping now protects team scope and complete-window coverage; actual game counter
capture and multi-window aggregation remain unverified/unimplemented.
