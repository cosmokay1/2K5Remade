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

## Latest verified state — October 14, 2026

- Latest published verified source: `743deb6`. Build `38634852382` and Franchise AI
  `38634852421` passed. CI checks asset-free runtime and bridge components;
  the actual game target is excluded. The privately compiled standard game renders
  Franchise Options in Deck Gaming Mode, and the user confirms LT/RT work.
  Signing still uses the original game logic; the AI transaction hook is pending.
- Latest verified published CI suite: **686 tests passed on Windows and Ubuntu**. Actual AIBASELIN parsing
  resolves 1937 roster/free-agent members. This does not prove contract/save
  round-trip integration. The read-only signing observer includes bounded bank-slot/name reads and is compiled and installed after confirmed exit;
  actual readback identifies Jeremiah Trotter at bank slot1910, matching AIBASELIN.
  Gildon offer amount/term/style/bonus readback is calibrated against the UI;
  Gildon signing moves him to the Giants with persisted terms and a$4.766M
  first-year charge matching displayed cap balances. The read-only decoder now
  calculates original Descending/Balanced annual rows with guest rounding;
  those rows do not establish modern-rule compliance or season aging. User confirms post-reload
  Descending annual rows: 2004 salary$3.10M/bonus$1.65M and 2005
  salary$1.86M/bonus$1.65M. AI/modern accounting
  integration and broader lifecycle/save verification remain pending. The Windows harness portability
  repair passed replacement CI and private MSVC/Wine fixture execution.
- Request/token ceilings and remote shutdown are sufficient for current work.
  Additional dollar-policy machinery is deferred at the user's direction.
- Xbox asset intake and Steam Deck SSH are now verified. Static analysis located
  the actual Sign Contract FSM descriptor0x00557B2C and message11 callback,
  and that descriptor has now been observed during a user signing attempt. Current
  bank/name readback is verified for Trotter; Gildon terms, saved ownership and first-year cap readback are verified; durable
  pinned same-year UUID bindings now preserve1937 IDs/initial profiles across baseline/control/signing snapshots. Actual Trotter slot/name/biography guard now matches the pinned candidate UUID in the running game test; automatic bridge binding/calendar/financial reconciliation remain pending; identity across rebuilds and AI/modern transaction integration remain unverified.
- Actual root-game transport startup and signing-screen hello reply consumption
  now execute on the Deck using the packaged Windows service. This diagnostic
  keeps AI disabled with explicit missing ADC and uses a private cloned ledger;
  zero model attempts were recorded. Guest transaction integration remains pending.
- The live Trotter biography/team/calendar observation now passes a reusable
  read-only signing checkpoint against AIGILDON and the pinned legacy ledger,
  resolving the persisted UUID/personality at revision0. Changed identity, raw
  cap/calendar inputs, contract provenance and revisions reject. This checkpoint
  does not authorize AI or writes. A configured service signing_context operation
  and native reply validation now expose that read. Automatic root-game capture
  and scheduling are authored and pass portable/actual Windows checks;
  the private build is installed after verified game/service exit. Actual game
  request/reply now resolves Trotter's persisted context automatically; all32
  ledger financial snapshots remain unchanged and model attempts remain zero.
  Owner-thread input polling is now authored, privately compiled and installed
  after verified normal game/service exit. Actual same-screen execution remains
  pending. It does not enable AI or contract writes.
- Actual AI/game/save integration, telemetry capture and final playable
  Windows/Steam Deck acceptance remain unverified. External gates are listed below.

## Current priority — a usable franchise negotiation in the game

Approved import policy: preserve existing deals as legacy schedules, use modern
rules for new deals, and retain2004 dollars with proportional modern amounts.
Legacy guarantees/cash/termination obligations must remain explicit or reject
unsupported operations; do not impose new bonus horizons on opening contracts.
Typed preserved legacy exports now match all32 current payroll totals across
the three private saves (1696/1696/1697 contracts). Durable books now preserve
legacy cap/ownership and permit cap-constrained new modern deals; the private
32-team restart check retains1697 IDs/actors/exact current charges. Free-agent
floors, cash/rookie sources, calendar conversion and actual guest writes remain. A
three-game historical credit policy versus conservative floors/exact source
records is now awaiting user selection; no new credit counts were assigned.
Observed FA identity initialization now covers all1937 players in the private
32-team import, including240 FAs. Missing salary classification stays explicit
and rejects before inference/signing; it is not replaced with a zero-credit floor.

The user identified cost-control expansion as a distraction. Stop adding spending
policies, quota layers or supporting infrastructure. Keep the existing request/
token bounds and remote killswitch; defer the unpublished dollar-policy experiment.
Prioritize the first real franchise path: identify an existing guest signing
boundary, establish player/contract readback, present negotiation in the game,
commit supported legal terms, and verify save/reload. Use source inspection where
it can advance this path; do not create speculative hooks or claim verified
addresses without the controlled runtime/save evidence. B01/B02/B03 remain real
gates for execution. Independent work must directly reduce those integration
steps, rather than expand the already substantial standalone engine.


## Current blockers

| ID | Input / status | What it blocks | Independent work that continues |
|---|---|---|---|
| B01 | User-supplied Xbox executable/disc now extracted; title/hash checked | Static intake resolved; runtime field/call verification remains | Private executable analysis and native build |
| B02 | AIBASELIN baseline, AICNTRL control and AIGILDON signing captured; original-game Gildon contract/roster/cap readback verified; broader pairs and lifecycle reload pending | Contract decoding, reconciliation and save round trips | Synthetic import fixtures, read-only diff tooling, state schema |
| B03 | Deck access restored; corrected observer identifies Trotter at bank slot1910. AIGILDON persists observed Gildon terms and Giants ownership; saved salary totals match user-reported cap UI. AI transaction integration remains pending. Standard Windows build renders franchise UI in Deck Gaming Mode; actual transaction/save accounting pending | Actual franchise execution, save/reload and delivery acceptance | Private local build environment and read-only signing-path analysis |
| B04 | Written upstream/third-party permission or suitable licenses | Redistribution of modified binaries and affected bundled components | Original source development, attribution, permission-request drafts |
| B05 | Approved temporary delegation applied, expiring2026-10-15T19:10:27Z; explicit CLI and actual Deck Windows control reads verified, with short-lived token cleanup/expiry denial. Persistent sidecar local ADC unavailable | Runtime sidecar/Deck authentication and live inference verification | Offline/native recovery and financial implementation |

User-supplied Xbox assets and the AIBASELIN franchise baseline are present
locally; controlled transaction and unchanged-save pairs remain pending. The Steam Deck is reachable over project-key SSH with Proton installed.
Keep game assets and raw disassembly private; do not download additional retail
assets or publish binaries without resolved rights. Do not repeatedly ask for
the same missing input.

## M0 — Provenance and repeatable development

- [x] Create GitHub-recognized fork; preserve upstream ancestry/notices.
- [x] Identify our original additions and document unresolved permission scope.
- [x] Commit/push development work without publishing installers.
- [x] Add automated portable financial/negotiation tests to fork CI.
      Published at `589a2bd`; run `38457090392` passed on Linux and Windows.
- [x] Add asset-free Windows checks for our bridge/runtime additions; clearly
      distinguish these from a full game build/test. Native pipe compile/execution
      verified at `dd1ed9e`, run `38464795249`; no guest assets or game exercised.
      Windows and Linux runtime/tool compilation plus Linux fault/copy/CPU-renderer
      fixtures passed at `5b5ade2`, run `38512445923`; the game executable is excluded.
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

- [x] Add immutable contract generations, backed-up format migration and separate
      retained cash/debt histories before enabling former-club return signings.
      Read-only legacy identities and explicit unmatched obligations now support
      reconciliation inspection through authenticated /api/contracts.
      Backup/replay preflight now checks whole-league integrity before migration;
      tools.prepare_generation_migration defaults to preflight; --migrate explicitly
      commits the backed-up format4 checkpoint.
      Accounting now consumes immutable legacy identities and a cash resolver;
      typed generation archives now drive payment ceilings and native inspection;
      backed-up format4 checkpoint migration is implemented. Versioned new-generation
      events and superseded lookup now support explicit healthy same-year veteran
      return signing and subsequent release/payment. Native service preview, AI
      negotiation and manual signing accept explicit return_scope with stories
      and promises. Returned first restructures use exact agreement IDs and versioned
      postings. Generation-aware assignments preserve both clubs' older cash/debt,
      including trade back to a former club. Actual guest entry and season rollover
      remain pending.
      See docs/contract-generations.md; current ownership now controls free-agent
      negotiation availability without deleting historical receipts.

- [ ] Define verified league-year rules; explicitly choose economic treatment
      (user chose2004 dollars/$80.5M cap; exact proportional scaling uses sourced2026 cap301.2M with minima up/ceilings down to1000-dollar units. Salary-profile provenance now persists/replays and rollover rejects an implicit economy change. Actual import/calendar and rookie-source integration remain required.)
      for historical start years rather than silently combining incompatible eras.
- [ ] Load annual minimums and draft allotments with recorded source/version.
- [ ] Separate cash owed/paid, cap charges, guarantees, and management reserves.
      Nominal cash/payment ledger and full base-guarantee terms are implemented;
      explicit base/bonus payment allocation and settlement are implemented; conditional
      guarantee protections, offsets and richer lifecycle rules remain. Normal payroll assumes owner funding, not a revenue-dependent cash gate; exceptional severe-mismanagement scenarios are optional future scope. See docs/payroll-funding-policy.md.
- [ ] Model guarantee protections/vesting and supported bonus components.
- [ ] Implement releases/retirement and retained obligations/dead charges.
      Supported sourced healthy preseason veteran releases now commit/replay with
      original archives, retained bonus/guarantee debt, nominal cash and ownership
      removal. Other releases, retirement, offsets, waivers and calendar remedies remain.
      Calendar-aware Ledger and atomic Store release commit/replay now bind the
      current generation/year, retain original cash/base indices and bonus layers,
      and start dead-charge aging at the release year. Immutable restructuring and
      assignment archives remain. Explicit calendar_v2 native inspection now
      separates release-year cursor from archived terms and validates allocated
      retained cash. Explicit manual calendar-format requests now route to the
      atomic Store release with bound full/compact native receipts; Windows pipe
      transaction/restart execution passed run 38514505285 at dcea1b2. Actual game wiring remains open and legacy
      post-roll APIs remain guarded. History-aware releases now retain all amendment
      plans and unpaid cash through rollover and later payroll; Windows execution
      passed run 38522825921 at f7d9ad9.
- [ ] Implement atomic trades with both teams' obligations and ownership.
      Calendar-aware seller Ledger assignments now preserve economic archives,
      earned prior base and actual-year retained charges. Receiving Ledger now
      enforces current cap/floors and preserves prior closed/settled expired debt,
      with a new trade-year-anchored agreement. Atomic paired Store calendar
      commits/replay now persist both books and ownership with strict before/after
      calendar checks and rollback. Explicit calendar_v3 native inspection now
      separates the outgoing trade cursor and retained cash from archived terms;
      Windows inspection passed run 38516814959. Explicit manual calendar trade
      requests now route to the paired Store with bound full/compact native receipts;
      Windows transaction/restart execution passed run 38517734890 at 8ea3682.
      Return-to-former-club and transferred-guarantee histories now preserve old
      generations, debt and unpaid cash through another rollover. Repeated-amendment
      assignments now persist complete histories on both books, including return to
      a buyer with older layered archives. Windows pipe execution passed run 38523844441
      at 212b037. Actual game wiring remains open.
      Supported sourced preseason veteran contract assignments now commit paired
      cash/cap/ownership events with independent league replay. Consideration, rookies,
      unpaid bonus and other trade protections remain; supported assignments now use
      separate receiving generations when returning to a former club.
- [ ] Implement extensions/restructures without erasing existing bonus layers.
      First calendar-aware Ledger conversions now preserve immutable original
      terms and paid indices, reanchor the amended schedule and retain both bonus
      schedules through later rollover/release. Store replay, explicit sidecar routing
      and native full/compact calendar amendment receipts are implemented at 2f5ffda;
      Windows pipe verification passed run 38519720705 at 2f5ffda.
      Pure sourced preseason guaranteed-base conversion and immutable bonus layers now
      preserve exact old/new schedules. Supported amendment cash, replay and subsequent release/trade commits now retain
      all layers. Strict local protocol/native validation is implemented. Extensions,
      game/UI controls and actual guest transactions remain. Repeated later-year
      guaranteed-base conversions now have immutable history, format2 Store replay,
      history-aware payment/rollover wrappers and explicit calendar_v2 native
      full/compact receipts. Windows repeated-path execution passed run 38522299444.
      History-aware releases and paired assignments preserve full amendment histories
      and separate buyer obligations; Windows pipe execution passed runs 38522825921
      and 38523844441 respectively. Extensions and richer terms remain open.
- [ ] Implement offseason/regular-season accounting and roster-status costs.
- [ ] Implement dated June-1 treatment, supported tenders/tags and salary benefits.
- [ ] Implement incentive settlement, cap adjustments, carryover and year rollover. Atomic initial calendar anchoring now validates all teams, revisions, source years and exact postings across restart/migration; typed current contract views and closing settlement inspection preserve original plans/cash without a revenue gate. A scoped veteran-only atomic league transition now advances sourced schedules and eligible settled expiry with exact all-team replay; supported postroll veteran sign/release/trade and first/repeated-amendment mutations, history-aware payroll and native calendar context are implemented; rookie/cohort rules and actual game advancement remain open. Source/schema review identified generation projection, expiry and cohort dependencies; follow docs/season-rollover.md for the durable league-wide transition work.
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
- [ ] Feed actual statistics, roles and relationship history; label missing evidence. Actual AIBASELIN history bank now has bounded raw-code extraction: 1325 player lists partition36866 entries without gaps/overlaps;612 members have no history pointer and remain unknown. Games/rushing codes0..3 and passing codes6..10 now have descriptor-backed names/count-or-yard units corroborated by NFL McNabb history; Saved history19 now has a corroborated half-sack mapping with raw units and an explicit historical inference scope; it does not establish live telemetry. A pinned saved-performance export now passes those named counters into actual Negotiation context in offline tests, with missing metrics, excluded flags and candidate years explicit. Other metric names/units, period calendars, observation modes, active game binding and live model consumption remain pending.
- [ ] Evaluate production with opportunities/context: targets/snaps, efficiency,
      drops, opponents/scheme, health, recency and sample size where available.
      Five exact sourced opportunity/yardage ratios now feed negotiation and draft
      contexts with sample counts, unknown coverage and durable recomputation.
      Actual capture, broader context and live-model weighting remain unverified.
- [ ] Verify whether intended-receiver targets exist in guest state or saved
      counters; otherwise instrument pass release/outcome events. Handle throws
      away, interceptions, spikes and nullified plays without inferring targets
      from receptions. Persist source/provenance for each counter.
- [ ] Investigate QB pressures and quarterback hits as distinct observed play events: identify dropbacks,
      Source triage and capture requirements: [pressure investigation](docs/pressure-investigation.md).
      rushers, timing and disruption; define/test attribution and avoid counting
      each frame as a new pressure. Do not substitute proximity or sacks silently.
      For hits, verify actual contact and timing relative to pass release; attribute
      the defender and quarterback, and establish sourced handling of sack overlap,
      multiple defenders, penalties and nullified plays. Deduplicate each contact
      episode. Verify saved counters or instrument events; never infer hits from pressures.
- [ ] Establish equivalent evidence for played, CPU-played and fast-sim games.
      If fast simulation exposes no targets/pressures/quarterback hits, report them unavailable
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
- [ ] Bound inference frequency; cache recorded decisions; add usage/cost telemetry. Provider context is byte-bounded and safe last-completed-call token diagnostics are captured; a thread-safe rolling per-provider request limit now rejects excess calls before the SDK. A persistent SQLite request budget now reserves each actual SDK attempt before
      submission, shares its ceiling across processes/restarts, keeps failed or
      unfinished attempts counted and records nullable token usage without prompt
      content. Vertex accepts this explicit budget. Live sidecar/HTTPS runtime budget configuration is now mandatory before SDK
      initialization; missing or invalid policy leaves manual operations available.
      Immutable cumulative token reservations now share the same atomic
      admission transaction, retaining allowances after errors/crashes and stopping
      on reported usage overruns. Live CLI accepts explicit --ai-token-limit;
      native token-policy forwarding is now implemented through explicit ABI and
      environment options; Windows execution awaits CI. Live runtime token policy
      is mandatory before credentials/SDK initialization. Further dollar-policy
      infrastructure is deferred; automatic attribution to actual seasons,
      compact prompts/batching and measured gameplay costs remain.
- [ ] Test different personalities on the same situation and validate multiweek continuity. examples.personality_continuity now verifies seeded priorities, equal observed inputs, different scripted offers/outcomes and two-round restart history without regeneration; live-model variation and actual game-week advancement remain unverified.

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
- [ ] Ship a cooperative client handshake without distributing owner credentials. A pinned private Windows CPython runtime is installed with license/checksum and isolated application path; synthetic native pipe checks pass with it under Wine. Retrieved Deck Proton artifacts verify no-console import and C-host handshake, cap preview, manual signing, player context and restart retry. These are synthetic tests, not actual game transactions. Pinned SDK execution and a read-only Windows GoogleControl check with one approved temporary runtime token now pass; token expiry denies without owner fallback and both temporary copies were removed. Actual root-game startup and signing-screen hello reply consumption now pass with deliberately unavailable credentials and zero model attempts. Persistent runtime credentials, authenticated game authorization and real-franchise bridge import remain pending.
- [ ] Validate bounded native lifecycle receipts in the integrated game before long-franchise runtime validation; opt-in target_v1 receipts now retain target archives and reconcile team cash totals. Precommit capacity checks reject oversized replies without mutation; actual guest reconciliation remains unverified.
- [ ] Ensure AI shutdown preserves financial enforcement and provides a clearly
      labeled manual/deterministic decision path; no silent native cap bypass.
- [ ] Test disconnects, expired credentials, protocol mismatch and service restart.

Done when the synthetic native client completes a transaction and all failures
leave game/engine state consistent. Remote control is not tamper-proof DRM.

## M5 — Verified Remade integration (B01/B02 gate)

- [x] Fix native client shutdown ordering so a sidecar that stops reading cannot leave destruction waiting on a blocked pipe write; add a Windows stalled-peer regression. Shutdown now stops the owned sidecar before joining its worker; the strengthened stalled-write CTest passed Windows run 38503835760. Inherited-handle isolation and stalled-write cleanup passed Windows run 38504026771.
- [x] Link the reusable C-compatible franchise client into the actual root game host with explicit opt-in lifecycle ownership; validate host transport separately from guest transactions. OFF-by-default root linkage and explicit vertex-only startup/cleanup are implemented. Actual privately compiled game starts the packaged Windows service, consumes hello and automatically requests/receives the pinned Trotter personality/context on the Deck, with AI disabled and zero model attempts. Normal game exit verifies owned child cleanup. This completes transport/lifecycle validation; authenticated AI authorization and guest transactions remain separate open requirements.
- [x] Establish a baseline game build and franchise behavior with the supplied game. Standard optimized build passes Proton validation and renders Franchise Options; user tested the vanilla Sign Contract path. This is baseline behavior only, not AI integration or full gameplay acceptance.
- [ ] Map contract records, cap/tender fields, player identity, statistics and save data. Read-only current roster payroll reconstruction now matches all32 saved team totals in AIBASELIN, AICNTRL and AIGILDON (1696/1696/1697 active contracts). The installed bounded probe now matches actual Trotter signing team15/mode2, payroll77038 and league cap80500 to AIGILDON/prior UI evidence. The read-only calendar/cap-adjustment observer is now installed after confirmed normal exit; actual season index and week/phase remain unverified. This covers original contract schedules only; An exact new-deal format adapter now decodes raw offer fields and checks annual modern charges without rounding changes; actual saved Gildon terms round-trip with the same $4.766M/$3.523M charges. It rejects unsupported guest bonus allocation and base guarantees; broader modern obligation storage, tenders, durable identity and statistics remain open.
- [ ] Trace signing, extension, release, trade, draft and year-transition functions.
- [ ] Trace CPU-controlled paths as well as user menu paths; avoid double decisions. Existing FSM push/pop probes have an opt-in 256-event trace; actual Sign Contract descriptor 00557B2C was observed during the user test. Authored read-only shared transaction entry, interactive judgment-return and precommit checkpoints now preserve the original decisions/writes; bounded portable memory checks and private MSVC game compilation pass. All three compiled callsites verified; the combined observer is installed after a fresh no-game guard. Runtime execution, CPU paths and callback/transaction readback remain pending.
- [ ] Intercept a single verified free-agent signing through existing patch conventions.
- [ ] Commit legal terms to the actual game and verify readback/save/reload.
      Original-game controlled Gildon signing now has saved contract/ownership
      and first-year cap readback; AI/modern terms are not yet committed to the game.
- [ ] Integrate all supported roster transactions and season advancement.
- [ ] Reconcile the external ledger and guest state before every financial write. The bridge now has a remote-gated proposal-only negotiation path that records accepted dialogue without cap/ownership mutation; exact preview persistence and retry checks pass. Actual guest commit confirmation, recovery and save reconciliation remain pending.
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
- [ ] Build a verified integrated Windows runtime with portable sidecar dependencies. Private CPython and25 hash-pinned Google SDK wheels now pass an actual Proton offline import/client-construction check with retained notices. Revised SDK check exits0 through Proton's Wine executable; the original launch-shim wait is isolated from Python execution. Explicit sidecar-owned SDK cleanup is tested on EOF/transport failure. Runtime authentication, real-franchise import and game AI integration remain pending.
- [ ] Validate Proton pipes, controller UI, gameplay, suspend/resume and save/load on Deck.
- [ ] Package the verified runtime and record tested Proton version and file hashes.
- [ ] Implement draft choices from observed prospect production, role, personality and evidence uncertainty; exclude hidden ratings. Read-only comparison context and strict model scouting advice now validate sourced evidence, per-candidate cap/pool estimates, shutdown and stale revisions; scouting history now also persists/replays with exact eligible preview checks; durable pick commitments and actual game draft choices remain.
- [ ] Constrain draft commitments by source-backed rookie allocations and team cap; persist decisions and scouting history. Source-backed management funding earmarks now protect cap/pool availability and replay with explicit withdrawal/signing replacement; source-declared pick order and exclusive rights now commit atomically with funding; actual source import, lifecycle and guest transactions remain.
- [ ] Validate actual in-game draft hooks and save round trips.

See packaging/steamdeck/README.md. Candidate packaging is not playable delivery.

## Cloudflare service delivery

- [x] Inspect cosmokay.com and existing tunnel/DNS resources using Cloudflare plugin.
- [x] Prepare authenticated loopback HTTP franchise inspection/preview origin.
- [x] Restore Cloudflare connector write access; dedicated tunnel creation succeeded after reconnect.
- [x] Create dedicated tunnel and route 2k5.cosmokay.com; verify HTTPS 200, origin certificate validation and scoped HTTP-to-HTTPS 308.
Browser franchise dashboard removed from scope by user direction. Franchise
management and promise displays belong in the game; retain HTTPS infrastructure
for service connectivity where needed.
- [ ] Extend live negotiation/draft API with persistent transactions and existing remote killswitch. HTTP negotiation now shares durable Bridge transactions and fresh access checks; actual restricted-runtime inference and draft transactions remain unverified/unimplemented.

See docs/cloudflare-tunnel.md. Dedicated tunnel/DNS/TLS route is live; in-game integration and remote service validation remain unfinished.

## Negotiated promises and achieved-goal scoring

- [x] Define sourced nonfinancial goals for touches, starts, position-specific yards and team wins, with an explicit time window and player importance.
- [x] Score observed achievement with unknown coverage and period closure; keep this separate from hidden player ability and salary incentives.
- [x] Wire promise proposals/accept/reject/counters through provider schemas and the Python pipe/HTTP protocol; native/game UI remains under integration milestones.
- [x] Commit agreed promises atomically with the contract and story; preserve them across restart.
- [ ] Derive actual touch/start/yard/win evidence from verified game counters; never infer unavailable targets or starts from other stats.
- [ ] Apply goal consequences to trust, satisfaction and future negotiation with context for injury, availability and coaching choices. Scores now persist and feed player context; only known final scores can source once-only bounded relationship changes. Structured sourced availability/injury/coaching circumstances now persist alongside unchanged scores and feed later negotiation context; actual capture, context-aware consequence policy and in-game story triggers remain.
- [ ] Display promised vs observed goals and fulfillment score in the game interface.

## Franchise creation and personality population

- [x] Atomically create engine teams/ownership and initialize every registered player with saved fictional personality traits and neutral relationships.
- [x] Save a versioned franchise seed; preserve stable identity across teams/restart and refuse rerolls or missing initial actors.
- [ ] Connect the native franchise-creation event to verified roster import and this initialization process. A strict JSON bootstrap command now creates/replays/publishes the initialized engine DB. The saved scheduler boundary/season display now has independent read-only decoding; pinned bindings reject a season advance concealed by unchanged scheduled-game year, while all1937 existing IDs still resolve across the three private saves. Actual live calendar/phase binding, export import and guest hook remain.
- [ ] Verify a real new franchise save/load retains all player and team identities.

See docs/franchise-creation.md and docs/promise-observations.md. Automatic promise
mapping now protects team scope and complete-window coverage; actual game counter
capture and multi-window aggregation remain unverified/unimplemented.

Native budget launch wiring is implemented through a compatible explicit C ABI
and validated host environment fields. Portable launch/quoting checks pass;
actual Windows configured-budget launch/restart smoke passed in CI38528423925.
Live runtimes now count the exact contents, instructions and structured response
schema before generation, rejecting missing/invalid/over-16384 input counts.
The provider output ceiling is explicitly configurable (runtime4096). Durable
cumulative token admission is implemented as an explicit optional
policy and live CLI/native launch options, now required for production AI.
Portable forwarding/parser checks
pass; actual Windows token launch/restart awaits CI.
Further spending-policy expansion is deferred. Prioritize the actual in-game
negotiation path and save/load evidence; authoritative season scope and measured
gameplay costs remain unverified.
