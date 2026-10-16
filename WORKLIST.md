# NFL 2K5 franchise AI delivery worklist

## Delivery target

Tested Windows and Steam Deck packages using **SOFTDRINK 2K28 on Remade as the preferred game base**, subject to compatibility verification, in which actual franchise
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

## Current priority — core franchise negotiation

The user deferred additional statistics investigation on October14. Prioritize
native offer submission, player response, legal financial commit and save recovery.
Use one addon/application pipeline for vanilla Remade and compatible mod packs;
do not branch negotiation/accounting/story policy on a mod name or executable
whitelist. Supply verified calendar, money units and roster/contract context to
the same rules. Compatibility checks must describe supported layouts and engine
capabilities; differing roster content is data, not a separate application path.
Reject unsupported layouts explicitly rather than infer support from a pack name. New v2 registries now persist explicit calendar/units/cap context without image
whitelists. Copy-only v1 conversion preserves player IDs, personalities and
contract schedules. The service now checks an explicitly configured expected
load-image digest at hello, echoes the configured registry/snapshot identity and
holds AI/journal writes until that connection matches. An explicit persisted
registry/database association now audits seed, actor origins/coverage and initial
ownership, and normalizes v1/v2 identity without rewriting journal intents.
Runtime verifies its namespace/bootstrap fingerprint. Actual MyNFL1 read-only
handshake/context consumption is verified. Full active guest-franchise lifetime,
broader live migration and AI-enabled signing authority remain open.

Windows + Proton is the Deck delivery priority. Defer further native Linux port
work unless a concrete Proton limitation requires it; retain existing fixes.

- [x] Remove repeated actor-origin/financial snapshot work during replay while
      retaining every recorded integrity check. Real MyNFL1 Windows Giants replay
      improved1.552s→0.366s, all32-club replay takes4.130s, and isolated read-only
      service execution improved6.755s→4.029s with exact replies unchanged.
      Actual game callback delivery and full transaction deadlines remain unverified.

- [x] Verify actual read-only source/namespace connection with AI disabled.
      On installed5698281, the user left Will Hernandez's MyNFL1 offer open;
      the game consumed bind_runtime and the preserved Giants/player context
      without navigating away. Native file identity and all720044 decoded bytes
      match the configured UDATA source. Model attempts remain0, credentials are
      unavailable, and source/registry/database hashes are unchanged. AI/write
      flags are false; offer preview refuses unresolved contract classification.
      This does not verify full lifecycle invalidation or signing/save-reload.

- [x] Revoke the saved load checkpoint at shared load-router entry, before
      allocation/read failures can leave the prior origin usable. Generated and
      interpreted paths emit the same invalidation without guest table access;
      old in-flight read work cannot repopulate the revoked epoch. All884 Python
      tests and nine local native checks pass. Atde1a31c both Windows/Linux Build
      38836811528 and Franchise38836811596 pass. Actual game execution remains
      pending; this closes an early-failure gap, not the full
      active-franchise lifetime requirement or application authority.

- [ ] Finish held native submission through accepted proposal, guest/ledger commit
      and recovery. An opt-in source path now defers retail judgment/precommit,
      queues one captured proposal (including a bounded cross-thread submit handoff)
      and presents the response. Atomic engine settlement of recorded acceptance
      now preserves exact terms, promises and cash with restart/replay checks.
      Read-only saved-signing confirmation now checks pinned identities, exact
      contract terms, unchanged bank contracts/calendar and all32 payrolls.
      Saved confirmation also checks a shared exact native target image, including
      preserved packed status bits and byte8 flags across the whole bank. An
      isolated actual-generated signing probe matches pending-before/final images;
      this does not prove live application or save/reload.
      A durable engine journal now preserves before/after saves, freezes competing
      store writes and commits confirmed effects with the ledger atomically.
      Explicit opt-in service operations now prepare/confirm against server-owned
      current save reads and expose bounded recovery status without AI access.
      Windows restarted save-reader compatibility is repaired and CI-verified
      at f876edb (Franchise38680339623, Build38680339592).
      Explicit native preparation now binds the consumed captured acceptance to
      its exact terms/hash/revision; queued preparation holds further offers
      across screen changes and uncertain replies. No guest write is granted.
      Verified at2abc9a6: Franchise38682855612 and Build38682855623 passed
      Windows/Ubuntu and native fixtures.
      Final pending-offer freshness fix1a9654f passed Franchise38686150816
      and Build38686150717; changed terms still invalidate the held display.
      Native pending journals now read the configured save status and can confirm
      only a verified candidate after-save against captured identity/charges/
      revision. No inference or guest write grant; signing remains held after
      settlement because native application/reload verification is unfinished.
      Source8e68e91 passed Franchise38701244992 and Build38701245086 on
      Windows/Ubuntu, including actual native-client saved settlement and a
      fresh AI-disabled recovery process with authored save files.
      Native application and save/reload remain unconnected.
      Held interactive returns now preserve rejection attempts and leave the
      offer screen open, using a single-use thread-local context match in both
      compiled and interpreter hooks. Local actual-shim and generated-caller
      checks pass; game execution of this opt-in fix remains unverified.
      CPU automatic negotiation has a direct-write route via00323B30 outside
      shared signing. Its hold now runs before the whole00324060 dispatch pass,
      covering both routes before offer/free-agent/contract changes. Compiled
      and interpreter hooks use the original epilogue, and known old generated
      cache patches are relocated with strict custom-edit/CRLF checks.
      Authored route tests and actual generated-caller probes pass locally;
      actual game CPU settlement/save verification remains open.
      Judgment and precommit now use distinct addon events, so bypass/precommit
      callers hold without creating interactive negotiation intents. Existing
      generated v1 hooks have an explicit upgrade check; the native judgment-result replacement now has a separate two-stage
      application-event branch, exercised with authored grants through actual
      generated signing code. Current production DLL grants nothing; remote/
      durable permits, uninterrupted application and game verification remain open.
      Source48c3c55 passes Windows/Ubuntu Franchise38774595042 and
      Build38774595079. Its private full Windows game --validate and actual
      signing/addon fixture children also pass under Deck Proton. This remains
      isolated validation; no new native build is installed, no production
      application grants exist and actual signing/save/reload is unverified.
      The original success epilogue now also provides a same-context one-use
      completion notification after roster/payroll/history, in generated and
      interpreter paths. Production consumption, exact live-target comparison
      and actual saved/reloaded confirmation remain to connect.
      Completion source7c45a76 passes Windows/Ubuntu Franchise38776861697
      and Build38776861856, plus actual private Windows/Proton completion/addon
      fixture children and isolated game --validate. No new native pair installed.
      Read-only journal status can now compare reported completed finance/identity
      projections against its exact accepted target without treating a live match
      as a saved signing. Native completion now samples/copies the projections on
      the owner and requires their comparison before automatic saved confirmation.
      Wrong-thread/unreadable/unbound results and mismatches keep recovery held;
      this flow has no application issuer and actual game execution remains open.
      Application attempts now also hold when the selected player has pending
      native trades/offers or the queue sample is unreadable/changing. Clear
      queues still grant nothing. The known cleanup/popup path has a verified
      queue prerequisite; full exclusive-application proof remains open.
      Both application checks now require one unchanged nonzero guest-lock
      acquisition serial, including across each addon callback. Missing ownership
      or release/reacquisition holds and consumes the attempt. This pins the checks,
      not the subsequent original-game writes; production still grants nothing.
      Ownership source1bf1013 passes six local CTests, the actual guest-lock checks,
      Python regressions and a private MSVC/Proton ownership fixture. Full Windows/
      Ubuntu Franchise38783097191 and Build38783098207 now pass.
      A full43-function static comparison finds seven SOFTDRINK-modified ranges,
      including five entry detours and a redirected signing helper. A private actual
      Windows interpreter/production-hook/runtime-lock probe now passes acceptance
      and both refusal cases on pinned pack bytes. Accepted finance/identity match
      exactly; refusals preserve pending-before images. The same guest-lock serial
      spans each tested call and the competing thread acquires after leave. This
      covers one authored deal/roster, not a live MyNFL1 signing or all pack paths.
      Source61c1c81 passes Windows/Ubuntu Franchise38783661071 and Build38783661101.
      A shared loader-supplied XBE identity event/snapshot now carries the actual
      load-input digest to any addon, without a version whitelist. Registration
      of franchise interpreter hooks is independent of the image name/hash.
      The runtime now provides an optional synchronous file-read observer, and
      the root loader forwards engine.file-read.v1 with borrowed native handle,
      status and delivered bytes. Runtime CI38800594758 covers actual Windows and Linux reads. The private
      Windows kernel-to-DLL/native-file-identity fixture and rebuilt game
      --validate pass on Deck at source8909ede/runtime ea4a0ee. Actual MyNFL1
      read delivery is verified below; selected-container/load binding remains open. This is read evidence, not active-save/load proof or an
      application grant. The existing POSIX sentinel-handle crash exposed by this
      test has a separate small upstream PR#2.
      The franchise addon now records a full supported save-read candidate's
      delivered-byte hash and owned native file identity, with no guest access or
      retained handle/buffer. Windows production-DLL fixtures pass on Deck. Source2bab3a4 is privately
      installed read-only with all205 save files unchanged; actual game delivery of MyNFL1's720044-byte hash is now verified, and the
      user confirms it open. Duplicate-container selection and causal load
      completion remain unverified.
      A staged v2 event now adds bounded guest destination locators without
      memory authority, preserving v1 delivery. All15 actual Windows standalone
      tests and the rebuilt game --validate pass under Proton; not installed.
      Load-boundary observation now correlates the delivered read, exact input
      hash and decoded byte count on the same owner/frame/destination. Generated
      and interpreted paths share the checkpoints across compatible packs.
      All17 Windows standalone tests and isolated game --validate pass; the
      combined source09fcc07 is privately installed after normal exit, with all205
      save files unchanged and AI off. Actual MyNFL1 read/destination and decoded
      checkpoint delivery are verified, but the initial checkpoint rejected the
      count because EBX excludes the final section length returned in EAX.
      Corrected total-count observation passes all17 Windows checks and isolated
      game validation. Sourcef08390c is now installed after normal exit, preserving
      all205 save files; Windows/Ubuntu CI also passes. Actual MyNFL1 read/input/
      decoded correlation now passes on the running build: phase3, all720044 bytes
      and the expected source hash/destination. The physical UDATA container is
      now identified by actual native file identity. Active-load lifetime still
      needs verification before namespace binding.
      A grouped source-origin gate is now validated privately: native file
      identity/version/content must match the configured save, its delivered hash
      must match the consumed sidecar runtime handshake, and pending replies are
      pinned to the same load epoch. Duplicate-file and stale-acceptance tests,
      both actual Windows client/journal fixtures and game validation pass.
      Source23946c9 is now privately installed after normal exit, with all205
      save hashes unchanged; the existing Steam entry is running. Actual file
      identity selects UDATA's MyNFL1 and its payload matches the existing2070-player,
      32-team registry/database association in a copied preflight. The live
      read-only connection is verified below; full lifecycle invalidation and
      production financial authority remain open.
      A new read-only bind_runtime handshake now verifies/echoes the same
      namespace while explicitly denying AI and journal grants. Native observation
      mode uses it; AI negotiation still requires hello and fresh remote access.
      All871 Python tests, nine local native checks,17 Windows addon checks and
      both native client/service fixtures pass. An isolated Windows preflight on
      the actual UDATA source returns the preserved player context with zero model
      attempts and unchanged source/database hashes. Source5698281 and its
      read-only configuration are installed with all205 saves unchanged. The
      first boot emitted the expected loaded-image digest but then crashed with
      integer divide-by-zero; the single retry also exited at the same address.
      Exact executable disassembly maps the fault to sub_003CAD50's division
      by MEM32(ecx+0x48), matching the pre-existing startup issue in the
      October9 worklog. Both traces are preserved; the underlying zero-input
      cause is unresolved. Source5698281 Build38817632722 and
      Franchise38817632849 pass Windows/Ubuntu. After the Deck returned, an
      unchanged installed-game launch through Steam progressed to movie/music/
      vblank execution; the intermittent crash is not fixed. Isolated GDB runs
      did not capture a reliable divide fault. Actual MyNFL1 read-only handshake
      and preserved Will Hernandez/Giants context consumption now pass with the
      offer held open. Source, registry and copied database remain unchanged;
      persisted model attempts0. Full active-franchise lifetime/write authority
      remain open; the offer still rejects missing contract classification.
      The actual Windows game/DLL build now passes isolated --validate and the
      game-built DLL identity/reload fixture under Proton. Real game-boot delivery
      and read-only context consumption are verified. Service handshake consumption validates
      explicit expected load-image data without a version whitelist; native
      validation requires the exact echo. A session match grants no application
      permit or full active guest-franchise lifetime proof. Enabled AI handshake
      and actual financial signing/save-reload remain open.
      Guard source7a39913 passes Windows/Ubuntu Franchise38781544199 and
      Build38781544176, actual private Windows/Proton queue/DLL checks and
      isolated full-game --validate. Those queue checks grant no production writes.
      Source7b536c2 passes actual Windows/Proton protocol, owner-host, adapter
      and client/sidecar live-before-save/completion/settlement/restart fixtures
      with authored data, plus isolated full-game --validate. Build38779416490
      and full Windows/Ubuntu Franchise38779416527 pass.
      An explicitly requested controlled-signing mode now also holds when the
      addon is unavailable, rather than silently falling through to retail.
      This now includes builds with sidecar support compiled out: both judgment
      and precommit gates preserve the requested hold and single-use held marker;
      a dedicated no-client native fixture covers the fallback.
      Stage/guard sourcec388051 passed Franchise38715022063 and
      Build38715022192 on Windows/Ubuntu, including real DLL boundary checks.
      Game-facing acceptance remains held until native application, save/reload
      and recovery are connected and verified. Actual game execution remains
      required. Do not enable this unfinished mode in the installed user runtime.
      The addon now exposes a read-only whole-league financial snapshot with
      an independent saved-state comparison, including free agents and unrostered
      bank contracts. Local actual-addon comparisons and sanitizer checks pass;
      d354faf passed Windows/Ubuntu Franchise38725532744 and Build38725532721.
      Live comparison remains to verify. This grants no permit and
      does not establish guest quiescence, full identity or current authority.
      See docs/NATIVE_FINANCE_STATE.md for the boundary and remaining conditions.
      Native preparation now supplies a fresh financial projection SHA256; the
      service requires it to match the server-owned before-save before reserving
      a journal. Missing/changed captures stay held. This is a consistency guard,
      not quiescence or permission to apply. Source6df0c0f passed Windows/Ubuntu
      Franchise38730370139 (including CNG mismatch/replay/prepare/settlement) and
      Build38730370102. Actual game application/save/reload remains unverified.
      Preparation now also compares all bound roster/free-agent biography fields
      through a separate sampled identity SHA256; no raw names or ratings are
      sent to the model. Source2fbc3cf passed Windows/Ubuntu
      Franchise38738527171 and Build38738527281, including native identity
      mismatch/replay/preparation/settlement. Active franchise/runtime and
      quiescence remain open; no application permit has been granted.
      The host now restricts memory reads to one guest-lock ownership span per
      addon invocation; release/reacquire and unowned calls fail closed. Local
      actual-runtime tests pass. Source2cd98d4 passed Windows/Ubuntu
      Franchise38748479653 and Build38748479778, including actual DLL read-scope
      execution. This
      does not pin the original commit or grant application authority.
      An opt-in single-file capture at the existing offer-screen event now makes
      live financial/identity comparison possible without starting AI or signing.
      Source6291411 passed Windows/Ubuntu Franchise38754170960 and
      Build38754170971. Actual Deck Windows/Python/Proton checks also pass31
      financial/capture and25 identity cases. The matching host/DLL pair is now
      installed in the existing private Steam entry with backups and all save
      hashes preserved. AI and controlled signing remain off. The user has been
      asked to load MyNFL1's offer screen for actual live/save comparison.
      Actual installed addon mapping and continued guest execution are verified;
      the user reports one startup failure followed by a successful retry.
      The first failure remains unexplained; no live capture has arrived yet.
      The user confirms an offer screen is open. The pinned pack detours FSM
      push through the interpreter, bypassing the generated observer. Source
      268e8d8 adds interpreter observation independently of negotiation mode;
      its actual private Windows game build, child validation and DLL checks
      pass. After normal game exit, the validated pair is installed with all16
      save hashes and the launcher preserved. The user was asked to reopen a
      MyNFL1 offer screen for actual capture; AI and controlled signing remain off.
      Actual capture now verifies matching cap/calendar/all32 club financial rows
      and all2619 contracts. The selected free agent is temporarily unlisted while
      its offer is open; the other2069 live member identities exactly match.
      An explicit pending-offer projection now handles precisely the accepted
      bound player's omission during journal preparation, preserving all other
      comparisons. Actual AI signing/application/save recovery remains unfinished.
- [ ] Reconcile the required opening obligations/rules before permitting financial
      writes, then prove signing and save/reload on the pinned pack.
      Optional explicit legacy-unknown cash scopes now preserve null total cash
      and track new contracts exactly; no automatic live import or inferred
      legacy cash/guarantees. Actual opening cap/non-roster/rookie data and
      native application/save/reload remain to verify.
      Source4a74436 passed Windows/Ubuntu CI38692925601. A separate pinned
      MyNFL1 preflight replayed32 clubs/1693 legacy schedules with unknown cash;
      it is a roster-only projection and grants no live signing authority.
- [x] Add a durable salary-classification import for the existing franchise.
      User selected completed game seasons as the explicit salary-credit
      simulation policy. Atomic imports preserve bootstrap, actors/history and
      balances; stale/partial/conflicting imports and prepared guest work reject.
      MyNFL1 copy imports1806 veterans across32 clubs, retaining264 zero-season
      players for separate rookie rules. Hernandez's captured offer changes from
      missing-classification rejection to an eligible preview with9.704M/7.172M
      charges and79.512M roster-based first-year room. Below-floor and over-cap
      previews reject. No live database or source save is changed.
      All883 offline Python tests pass. Private scripted-proposal/journal restart/
      settlement/retry checks pass on constructed after-save data, not native
      application. A single144-file Windows service/fixture batch is prepared;
      initial Windows CI exposed unclosed SQLite preview/test handles. Explicit
      closure and a portable failure-path regression now pass884 local tests.
      The corrected144-file package now passes all13 targeted Windows tests,
      actual UDATA floor/cap/AI-disabled checks and both native C-client journal
      fixtures under isolated Proton. Revision2 context preserves the original
      personality/source/database with zero model attempts. After confirmed
      normal exit, the launcher configuration is installed with all205 current
      save hashes unchanged; the executable/addon and disabled AI mode are
      preserved. Actual revision2 in-game context is now consumed while the
      Hernandez offer stays open: eligible preview, unchanged personality and
      source/bindings/database hashes, zero model attempts. Native signing and
      save/reload remain unverified; this read-only milestone grants no writes.
- [ ] Complete draft, persistent stories/promises, shutdown and final delivery checks
      below. Defer broader stat mapping while the core signing flow is incomplete.

## Connection addon foundation

The user requested extracting connection tooling into its own addon, then consuming
it from the franchise application. Keep domain rules out of the reusable core.

- [x] Extract original Windows process/pipe ownership, launch quoting and JSON envelope validation into addons/engine-sidecar.
- [x] Make the franchise pipe client a consumer retaining application validators, budgets and control policy.
- [x] Add standalone asset-free protocol/echo checks and independent CI.
- [x] Verify Windows transport and franchise regression CI after extraction: consumer ba8a4f5 run 38655649598 passed Windows/Ubuntu.
- [x] Publish private standalone source with provenance: https://github.com/cosmokay1/engine-sidecar (export bdaa2df). Standalone Windows/Linux CI 38655732233 passed.
- [ ] Select a public reuse license before public distribution.
- [x] Build and validate separately loadable franchise addon and thin shim: 6f75219 Windows DLL ABI/load/forward/unload/reload fixture passed in CI38656804337; authored RAM observation remained read-only. Actual game execution remains below.
- [x] Remove franchise types from the public DLL ABI: ABI2 exposes lifecycle,
      named events and snapshots; private franchise payloads stay in its adapter.
      Actual Windows/Proton fixture loads a separate counter addon using only
      the generic header; unknown messages, size checks and ABI1 refusal pass.
      The private Deck entry now has the ABI2 host05ac4e9 and addon6291411 pair;
      actual module mapping and continued guest execution are verified. The new
      read-only live capture remains to verify.
- [ ] Generalize the manager's explicit single-addon selection before proposing
      general addon support upstream; verify a matching host/DLL pair in-game.


## Native Steam Deck port — user requested

Upstream review October15: repack master86198cf includes our attributed POSIX
prerequisites; its runtime pin0baca1a trails the game runtime's three new Linux
filesystem commits. Imported those commits with attribution into runtimec867ad3,
preserving our actual POSIX guest lock and read serial. Authored offline Linux
checks pass for case resolution, team/save paths, partition persistence and
settings migration. Source05ac4e9 passed Windows/Ubuntu Franchise38750534000
and Build38750533958. An isolated private Windows game/addon build and actual
Proton DLL-boundary/read-scope fixture also pass; game validation could not start
after the Deck connection timed out. Installed game/saves remain unchanged.
Linux mod-pack disc overlays remain explicitly unimplemented upstream; native
SOFTDRINK boot/rendering/signing/save/reload remain unverified.

Preserve the current broadcast styles while replacing WebView2; the user did not
request a simplified scoreboard. Keep the working Windows/Proton installation
until a native full-game build is verified.

- [x] Add and execute native Linux engine-sidecar process transport checks on the
      Deck without Proton: protocol, echo and process ownership checks passed.
      This does not port the franchise adapter or the game.
- [x] Verify Windows/Linux standalone CI and consumer regressions:8503615 consumer
      Franchise38677356141 and Build38677356207 passed. Standalone export2a2110d
      Windows/Ubuntu CI38677485314 passed.
- [x] Make WebView optional for native JSON styles; compile the real retained
      renderer with/without HTML support and verify identical settled FOX/CBS BGRA
      pixels and HUD placement. Full Windows game configuration accepts a missing
      WebView SDK when disabled. This is not an NBC replacement or Linux renderer.
- [ ] Replace HTML/WebView presentation rendering while retaining package layout,
      colors, logos, typography and animations; compare rendered output. Existing
      FOX/CBS JSON packages already use the native Windows renderer. The NBC HTML
      package needs a supported native equivalent, not a plain scoreboard.
- [ ] Port the Windows game/addon loader, remaining UI/files/audio dependencies
      and presentation renderer; prove full native Linux boot, match transitions,
      franchise signing and save/reload. SDL3 input alone does not provide this.

## Mod-manager extension — current scope

The user clarified that this fork updates the existing mod manager to support
addons, then applies the sidecar addon alongside SOFTDRINK. Retain one manager.
A repack converter must target verified compatible hosts; universal binary
conversion is not claimed.

- [x] Validate independent addon selection, disabled default, restart status and
      missing-addon handling through existing manager callbacks and real Windows DLL:
      d3ca4aa CI38658080834 passed. User now confirms the installed manager
      displays Franchise Sidecar Off; subsequent On/restart/module loading is verified below.
- [ ] Verify addon installation/upgrade for pinned repacks; preserve user saves
      and reject unsupported native executable versions. The guarded DLL installer
      now passes install/reinstall with copied actual private binaries and rejects
      the previous host; synthetic upgrade/backup/failed-replace checks pass.
      Cross-version live upgrade acceptance remains open.
- [x] Verify installed manager Off/On selection survives normal restart and loads
      the DLL alongside the selected SOFTDRINK pack: user confirmation plus
      process102235 mapping, enabled=1, unchanged active-pack and zero runtime errors.
- [ ] Verify broader controller/gameplay behavior with addon plus SOFTDRINK.
      Private Windows candidate built and installed on Deck; DLL/manager fixture
      passed under Proton. SOFTDRINK reached team selection, then crashed when
      starting a match. Shared-epilogue interpreter regression reproduced and fixed;
      user reports the fixed match-start retry is working; independent on-field
      screenshot and zero interpreter/crash errors corroborate it. Broader gameplay/controller acceptance remains open.

## Active base decision — October 14, 2026

The user selected SOFTDRINK if compatible. Prioritize the Xbox Remade pack path;
NFL 2K27/PCSX2 migration is deferred. Preserve prior PS2 research as reference.
The existing AI engine is reusable; no pack/game AI signing is verified yet.
Do not deploy superseded staged diagnostics blindly or overwrite existing saves.

- [ ] Pin SOFTDRINK v0.6 patch/checksum, retail input and Remade runtime; verify
      installation/reconstruction and applicable attribution/distribution terms.
- [ ] Verify the interpreter pack path on Windows/Deck: boot, fresh franchise,
      played/simulated transitions and clean shutdown, including known freeze cases.
- [x] Audit MyNFL1 Giants opening cap scale and roster payroll read-only: all53
      contracts and all32 team totals reconcile; verified pack economy displays
      four real dollars per game dollar. $89.216M room follows $301.2M cap less
      $211.984M roster charges. Matched all53 names to the2026 reference, isolated
      $42.392M of additional current-reference roster/reserve/PS charges and
      $43.691M dead money; dated obligations import remains unverified. See
      [Mynfl1 audit](docs/MYNFL1_CAP_AUDIT.md).
- [x] Support declared modded player-bank bounds/settings in the strict save reader:
      MyNFL1 reads2619 records/2070 memberships including377 free agents; all32
      payrolls reconcile unchanged. Synthetic corrupt-boundary checks and710
      regressions pass. This does not authorize modern ledger import.
- [ ] Reconcile dated inherited cap obligations and fitted contracts at franchise
      creation, preserving the verified4:1 scale, with explicit pack calendar
      policy and no double-counted reserve players or retained debt. Preserved
      legacy schedules now support explicit4:1 cap scaling after guest rounding,
      with durable cap enforcement; actual import/future-calendar/non-roster mapping
      remains open. Dated source adapter now proposes exact adjustment records
      for1406 matched schedules;287 remain unresolved. Giants42 matched deals
      show +$57.104M next-year source liability versus fitted curves, making
      future-year source reconciliation a required acceptance gate.
- [x] Add explicit hash-pinned SOFTDRINK opening snapshot bindings: logical2026,
      preserved4:1 legacy export and scaled read-only checkpoint. MyNFL1 resolves
      2070 stable IDs/profiles and1693 active schedules; no active-game import.
- [x] Carry verified pack offer scale through raw preview, exact counter encoding,
      persisted dialogue replay and native response checks.726 Python regressions
      and5767 host native/Python codec cases pass; no runtime deployment or signing.
- [ ] Capture controlled pack signing/save/reload evidence; verify player identity,
      history, experience, calendar, salaries/payroll/cap and effective money scale.
- [ ] Revalidate existing Xbox observer and bridge against pack code and saves;
      implement held negotiation, proposal presentation and legal commit/recovery.
- [ ] Verify modern accounting, rookie/draft rules, promises, remote shutdown and
      final Windows/Deck acceptance against the pinned pack.

See [SOFTDRINK_AI_BASE.md](docs/SOFTDRINK_AI_BASE.md). Old native/PS2 evidence does
not establish v0.6 compatibility or a new completion percentage.

## Latest verified state — October 14, 2026

- Latest verified implementation: `2b35f3e`; Build `38665445078` and Franchise AI
  `38665445103` passed. Windows/Ubuntu passed707 regressions and native checks,
  including the generic example addon, ABI1 refusal and interpreter regression.
  The installed Deck runtime remains the verified ABI1 pair; ABI2 is staged only. Private Windows game built
  and match-start recovery verified on Deck. Manager selection and DLL component checks passed. Windows DLL addon fixture and707 tests on Windows/Ubuntu passed; the private candidate now runs with the addon enabled after normal restart.
  DLL mapping and unchanged SOFTDRINK selection are independently confirmed.
  Initial SOFTDRINK match start crashed; its specific recovery is now verified.
  Broader gameplay and franchise compatibility remain unverified. A synthetic regression confirms an interpreter shared-epilogue bug;
  its fix passes under Proton, and the user reports the match retry is working.
  Broader gameplay and franchise acceptance remain open. CI checks asset-free runtime and bridge components;
  the actual game target is excluded. The privately compiled standard game renders
  Franchise Options in Deck Gaming Mode, and the user confirms LT/RT work.
  Signing still uses the original game logic; the AI transaction hook is pending.
- Latest verified published CI suite: **707 tests passed on Windows and Ubuntu**. Actual AIBASELIN parsing
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
  pinned same-year UUID bindings now preserve1937 IDs/initial profiles across baseline/control/signing snapshots. Actual Trotter slot/name/biography guard matches the pinned candidate UUID; automatic context binding reconciles the pinned legacy checkpoint and retrieves persisted personality while the offer stays open. Active-franchise selection, identity across rebuilds and AI/modern transaction integration remain unverified.
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
  after verified normal game/service exit. Actual Trotter same-screen execution
  now verifies one context reply without an intervening FSM transition, unchanged
  finances and zero model attempts. It does not enable AI or contract writes.
- Saved historical performance is now an opt-in signing-context format with
  native identity/unit/source checks and explicit unknown coverage. Actual Trotter
  service checks return six game entries/four sack entries; Windows build/runtime
  checks pass. The new game/service package is staged for actual game validation,
  and is not yet installed. Targets, pressures and QB hits remain unmapped.
- Opt-in live offer capture/precheck is now authored and privately compiled.
  Exact guest-format compatibility and stored ownership/minimum/cap checks produce
  advisory rejection or preview, with no model call or financial mutation. The
  captured Trotter six-year bonus offer rejects incompatible modern allocation.
  Actual game execution/enforcement of this new check remains pending.
  Native validation now also reconstructs every guest salary and requires exact
  modern charges; 2,886 native/Python cases match on portable and actual Windows
  execution. This is decoding/preview validation, not a guest signing commit.
- Game-facing proposals now optionally require exact original-game encoding.
  Acceptance and representable counters retain mapped amount/flag words;
  unrepresentable demands stay unchanged and ineligible, with no rounding or
  signing. Durable replay checks format/encodings and native validation checks
  exact salaries/charges. Actual root negotiation requests, UI and commit remain.
- Captured-screen proposal requests now reconcile the pinned checkpoint and
  derive UUID/team, saved personality/relationships, sparse performance and exact
  offer inside the service. Missing classification, bad checkpoints and disabled
  control reject before inference. Native checks bind proposal evidence back to
  that checkpoint. Actual root submission/presentation is still pending.
- A native read-only signing panel is now authored using the existing HUD
  compositor. Owned display copies clear on stale/failed observations and show
  saved fictional priorities, offer eligibility and explicit vanilla-signing
  status. Actual extracted Direct2D rendering passed component review at Deck
  and desktop sizes; installation and actual-game overlap/readability remain.
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
- [ ] Map the original TT/Thrown To receiving stat to guest state and saved
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
      Preserve native offseason free-agency waiting/competition and the normal
      in-season signing flow. Bad offers must have durable opinion consequences;
      repeated lowball-and-increment attempts must not be a free search for the
      minimum price. Player-specific patience limits approaches in a short
      verified game-time window, survives restart and permits withdrawal.
      Early extension talks should provide more opportunity to reach agreement;
      current owned-contract extensions are explicitly unsupported and must be
      implemented. Sourced contract-year/underpayment frustration may progress
      toward a holdout, with actual participation effects and resolution required
      before claiming holdout gameplay. Do not use wall time or invented market
      value/hidden ratings to manufacture these states.
- [x] Persist a bounded opinion reaction to a bad offer in the same decision call.
      Structured offended rejection/counter responses now atomically reduce saved
      respect under an explicit authored policy; neutral bargaining and raising
      the offer do not erase it. Restart/retry, stale concurrent history, shutdown,
      failed inserts, missing markers and duplicate consequences are checked.
      Current and historical captured negative responses stay distinct; acceptance
      retains the current actor check. Private MyNFL1 scripted rehearsal passes
      with unchanged finances/source saves and no paid requests. Not installed;
      actual game AI behavior remains unverified. See docs/negotiation-reactions.md.
- [ ] Present each accept/reject/counter as concise natural speech from the player
      or agent, consistent with remembered treatment and supported consequences.
      The existing structured reason is required for every action and uses the
      same decision request; voice instructions are now explicit. Actual in-game
      AI response display and behavior remain unverified with AI disabled. The
      current reason preview truncates at140 bytes in a160-byte history field;
      complete natural explanations need a readable bounded display, without
      claiming that narration itself applied an opinion or holdout consequence.
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
- [ ] Map contract records, cap/tender fields, player identity, statistics and save data. Read-only current roster payroll reconstruction now matches all32 saved team totals in AIBASELIN, AICNTRL and AIGILDON (1696/1696/1697 active contracts). The installed bounded probe now matches actual Trotter signing team15/mode2, payroll77038 and league cap80500 to AIGILDON/prior UI evidence. Actual calendar readback now matches AIGILDON season index0/display2004 and raw phase7/step5; those raw codes are not modern NFL phase/week authority. This covers original contract schedules only; An exact new-deal format adapter now decodes raw offer fields and checks annual modern charges without rounding changes; actual saved Gildon terms round-trip with the same $4.766M/$3.523M charges. It rejects unsupported guest bonus allocation and base guarantees; broader modern obligation storage, tenders, durable identity and statistics remain open.
- [ ] Trace signing, extension, release, trade, draft and year-transition functions.
- [ ] Trace CPU-controlled paths as well as user menu paths; avoid double decisions. Existing FSM push/pop probes have an opt-in 256-event trace; actual Sign Contract descriptor 00557B2C was observed during the user test. Authored read-only shared transaction entry, interactive judgment-return and precommit checkpoints now preserve the original decisions/writes; bounded portable memory checks and private MSVC game compilation pass. All three compiled callsites verified; the combined observer is installed after a fresh no-game guard. Runtime execution, CPU paths and callback/transaction readback remain pending.
- [ ] Intercept a single verified free-agent signing through existing patch conventions.
- [ ] Commit legal terms to the actual game and verify readback/save/reload.
      Original-game controlled Gildon signing now has saved contract/ownership
      and first-year cap readback; AI/modern terms are not yet committed to the game.
- [ ] Integrate all supported roster transactions and season advancement.
- [ ] Reconcile the external ledger and guest state before every financial write. The bridge now has a remote-gated proposal-only negotiation path that records accepted dialogue without cap/ownership mutation; exact preview persistence and retry checks pass. Actual guest commit confirmation, recovery and save reconciliation remain pending.
- [ ] Add real franchise negotiation UI with cap/cash/guarantee effects and reasons.
      Target a full addon-owned replacement screen, preserving the game style and
      free-agency timing, rather than extending the compact diagnostic overlay.
      See docs/NEGOTIATION_SCREEN.md for the flow, input ownership and acceptance.
      The complete context/proposal snapshot is implemented separately from the
      unchanged compact-display ABI: exact offer/preview, saved evidence, missing
      data and full agent/counter/promise response, without another inference.
      A read-only addon renderer and controller filter are now authored with
      Contract/Performance/Agent sections, complete scrollable responses, one-use
      Back and held-button quarantine. The preview refuses AI/application mode;
      native signing remains held even if the addon fails. Eleven portable native
      checks pass, and all20 Windows native checks/render fixtures pass at both
      Deck resolutions. Actual Deck takeover remains unverified;
      editing/submission/application remain unfinished. Installed code is unchanged.
      The compiler TEMP blocker is repaired by using the initialized Wine prefix;
      repeated fresh-container builds and all three isolated Windows/Proton child
      checks pass. The user-requested redesign adds salary/cap columns, stronger
      navy/crimson hierarchy and a dedicated dialogue area;24 authored captures
      include long contracts/rejections. The approved e45a634 design passes full
      Windows/Linux CI. Its actual Windows game and matching addon now compile,
      and isolated Proton game --validate passes with a child completion marker.
      All20 matching Windows package tests pass under Deck Proton, loading the
      actual paired game addon DLL. A hash-pinned preview-only package and
      backup/rollback installer are ready. After the user's normal exit, the
      matching game/DLL/preview wrapper were installed with backups and all205
      saves verified unchanged. The user confirms the live screen appears, but reports delayed opening,
      horizontal controls driving vertical sections and no stick navigation.
      A combined fix adds pre-reply loading, vertical D-pad/left-stick selection,
      right-stick scrolling and timing logs. Eleven portable checks and four
      targeted Windows/Proton fixtures pass; the rebuilt game validates. Live
      verification of this correction is pending. Editing/submission and AI
      remain disabled.
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

Packaging status October15: tools/package_steamdeck.py builds an explicit-manifest
candidate ZIP with per-file hashes; it is not yet the final self-contained Deck
installation flow. Existing private Gaming Mode shortcut/controller evidence does
not verify a newly extracted package. User explicitly rejected a custom launcher:
use Steam's standard non-Steam EXE shortcut with a selected Proton compatibility
tool. Bundle installation instructions, eliminate private build-directory
assumptions, and verify a fresh
install/update with preserved saves before marking Deck delivery complete. Keep
Windows/Proton as the working delivery path while the native Linux port remains
unfinished. Current private source05ac4e9 game/DLL compilation and Proton boundary
fixture passed; no new installed game or playable-package claim follows.

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
- [ ] Connect the native franchise-creation event to verified roster import and this initialization process. A strict JSON bootstrap command now creates/replays/publishes the initialized engine DB. Optional complete per-team cash imports are reconciled before publication, with preserved legacy cash explicitly unknown; failures discard the entire unpublished artifact. Receipt counts include all registered legacy/observed identities. A real MyNFL1 context DB using the pinned binding seed passes the Windows/Proton service boundary with zero model attempts and unchanged input hashes; its read-only game launch configuration is staged pending normal exit and actual menu verification. The checkpoint now uses one validated ledger replay, retaining concurrent-commit/file-replacement rejection; the real Windows/Proton process preflight improved from11.61s to5.82s with zero model attempts. The saved scheduler boundary/season display now has independent read-only decoding; pinned bindings reject a season advance concealed by unchanged scheduled-game year, while all1937 existing IDs still resolve across the three private saves. Actual live calendar/phase binding, export import and guest hook remain.
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
