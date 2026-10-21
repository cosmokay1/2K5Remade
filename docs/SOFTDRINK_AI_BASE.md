# SOFTDRINK franchise AI compatibility gates

On October 14, 2026 the user chose SOFTDRINK if usable. Prefer the Xbox Remade
pack path and defer NFL 2K27/PCSX2 migration. This is a direction, not compatibility proof.

## v0.6.1 integration candidate — October 21, 2026

Official [v0.6.1](https://github.com/cruuz/softdrink-2k28/releases/tag/v0.6.1)
is pinned at `8de98db980c4dbe88e1ec1614e322df5ef35d636`. Its patch is
1,021,040,707 bytes, SHA256
`bf9c1ebc210a0ca832a586b884c0db714960f4434b227d21f644f464f964eac6`.
The release requires Studio beta-77.1/RC112. Its format-3, reader-4,
source-copy-v1 patch reconstructs with the existing pack importer: retail source
hashes and every changed output verify. The private overlay is about716MiB;
no full ISO was generated. A later worker compatibility repair required one
native EXE rebuild, described below. Reconstructed default.xbe:
`9465382bfd617b6d1aeadc5653fefef256678c12a65a5f828705495291e40610`.

Static comparison finds unchanged shared signing/judgment/offer access routines,
interactive-dispatch span, payroll/roster helpers, offer descriptor and salary
clock descriptor range. The XBE section layout changes (28 to29 sections), so
these comparisons do **not** establish interpreter, hook or runtime compatibility.

Preserve the user's Week1 hybrid rather than replacing it with the pack's
October14 roster. The new stock roster roundtrips losslessly using the official
RC112 core modules pinned at `a292dbfe0e3d72b8a338670e26415b706675baf4`.
All1985 native-origin hybrid identities uniquely match name/date-of-birth in the
new stock roster, with zero portrait-ID changes. Retain the hybrid's other79
approved profiles and existing portrait cache. This is identity evidence, not
proof that portraits render in the new runtime. Do not automatically apply the
Studio franchise-upgrade command to the custom hybrid.

A separate candidate namespace was prepared from the original game-created
PLAYW1 opening save, without changing deployed saves, DBs or pending journals.
It contains32 opening books and2064 actors; its cap-bound save matches the prior
opening payload byte-for-byte. The Giants retain modeled room$8,079,279.
Rebuilt local pricing has793 sourced comparables and397 quotes; signing defaults
OFF, with zero inference requests. These remain the approved simulation books,
not certified historical Week1 financial statements. This candidate is a fresh
compatibility test, not a migration of existing negotiation history.

Private receipts: `.local-runtime/softdrink-v0.6.1/` contains release/download,
reconstruction, boundary/roster audits and `franchise-candidate/` receipts.
Eleven importer-contract, opening-preparation and market-export tests pass.
No assets or save payloads are committed.

Deck staging now verifies all17 transferred overlay files, preserves434 protected
save/context files, and passes the Windows handshake and all32 cap-restoration
checks. Reuse the existing addon7ee654d8… and shared runtime dependencies. New
profile: `native-05ac4e9/softdrink-v0.6.1-test/profile`; signing/submission OFF,
preview-only. Normal Steam routing is restored after the one-time launch.
The initial preview/hold/submit flag combination was invalid and was corrected
without changing policy or binaries.

Actual startup then exposed a replaced I/O worker at guest0004D810: v0.6.1 uses
a different state machine and removes the old0004D8C0 jump table. The manual
native worker still read it and aborted at state11/target90909090. Because the
routine is absent from the generated dirty-function map, route it through the
existing interpreter whenever pack interpretation is active, before any native
frame/table access. Retail retains the native path. The portable worker ABI/
routing fixture and existing interpreter-hook fixture pass. Deployed source
plus only this repair rebuilt in52.06s, generated-local freshness check passed,
and paired game validation exited0 in3.47s. Candidate EXE:
`a53550db1dae565fee099aa0588f6ed59b68d9ebc3143231b4146ff8f92f586a`.
The build-output hardlink was broken before linking; existing profile EXEs and
all434 protected files remain unchanged. Unrelated dirty native edits were not
included in the build.

The repaired process runs and the addon reports the exact9465382b… loaded image;
this clears the observed worker abort, not full boot acceptance. A later watchdog
reports a10s guest-lock stall (last guest call00035983, owner PC in native
sub_0014EC70). User-visible menu state is requested and not yet confirmed.
Usable boot, post-play transitions, franchise load/context, signing/cap receipts
and save/reload remain required. Do not promote this profile or replace the
established pack yet. Keep the scheduled task off; no controls/IAM/budgets renewed.

## Inspected evidence

[SOFTDRINK v0.6](https://github.com/cruuz/softdrink-2k28/releases/tag/v0.6)
requires a user's unmodified USA Xbox disc and beta-77/RC111 Mod Studio to install
its patch. The release describes playbook/CPU changes, experience corrections,
grades and honors; it explicitly retains numeric ratings in calculations.
Its documented execution uses xemu at 128 MiB, with important gameplay checks
still pending. Installer reconstruction/offline selectors are not live proof.

Our src/main.c reads active-pack.ini, selects a pack default.xbe, loads retail
base data, enables 128 MB guest memory and initializes nfl2k5_interp_setup.
src/nfl2k5_mod_packs.c keeps packs on the installed main executable rather than
requiring a separate native executable per pack. README reports v0.4/v0.5 support;
older HANDOFF-MODS.md separate-build failures describe a historical route.
Private v0.6 execution now reaches the field on Deck after the interpreter shared-
epilogue fix (4e3d3d5). Initial match-start failure and recovery are recorded in
WORK_PROGRESS.md. The manager Off/On restart and actual DLL mapping alongside the
active pack are verified. Fresh-franchise, post-play, signing and save/load gates
remain open; this does not establish full compatibility.

The [v0.6 notes](https://github.com/cruuz/softdrink-2k28/releases/tag/v0.6)
document corrected rookie-equals-1 experience and aligned career seasons, current-
team history rows, overall letter grades and player honors. Numeric ratings still
drive sorting/calculations; attributes remain numeric. New roster/history data
needs a fresh franchise. These are additional inputs to revalidate rather than
proof of our performance-driven decisions or modern financial accounting.

## Acceptance before AI integration

Pin patch, reconstructed executable/assets and runtime hashes. Preserve retail
and previous saves. Test boot, attract demo, exhibition post-play transitions,
fresh franchise and vanilla signing/save/reload on the actual Deck runtime.
Reconcile identities, contract encoding, payroll/cap, history, experience and
calendar from controlled pack saves; retail addresses and old UUID bindings are
not automatically valid. Inspect pack modifications for overlap with the signing
boundary and history fields before any write.

Retain independent accounting, personality/performance, promises, draft, provider
and shutdown modules. Validate pack money scale before applying modern minimums
and rookie amounts. Fresh franchise initialization must use pack identities.
Then hold original signing while obtaining a proposal, recheck control/state,
commit supported terms and prove guest/ledger/save agreement and recovery.

Preserve BeyondTomrrow/Remade and SOFTDRINK/cruuz/contributor notices. Do not infer
endorsement or rights to redistribute game assets. Do not renew disabled controls,
make paid inference or replace the running game during compatibility inspection.

## Verified money-scale correction

MyNFL1's Giants audit confirms the installed pack already includes the experimental
2026 economy, including four-to-one real-dollar display. The saved league cap is
$75.3M internal = $301.2M displayed, not an outdated $75.3M league ceiling. The
Giants'53 saved charges total $52.996M internal = $211.984M displayed, leaving
$89.216M room. All32 roster totals reconcile. Raising the ceiling or multiplying
values a second time would be wrong. See [Mynfl1 audit](MYNFL1_CAP_AUDIT.md).

The pack's encoded contract total represents fitted remaining cap liability, not
necessarily original headline value, cash or guarantees. Existing real-world
released-player debt/reserve obligations and exact schedules remain to reconcile.
The strict reader now supports the declared expanded bank and variable settings.
An explicit hash-pinned opening binding supplies logical2026 and4:1 legacy export.
Complete obligations and actual guest/ledger commit verification remain open.

## Creator-source scope inventory (October 15)

The requested parallel audit inspected the installed v0.6 pack/patch recipe and
creator beta-77 source at commit
[e193841](https://github.com/cruuz/2k-football-mod-tools/tree/e19384123c23a3601949dda67c9a3ab754d65fd6).
These identify intended/enabled behavior; they do not establish complete Deck
execution, financial correctness or multi-season/save compatibility.

| Area | Installed/configured or documented scope | Evidence |
|---|---|---|
| Accelerated clock | Enabled with20 seconds as the minimum play clock after huddled calls. Only the actual reduction runs off a running game clock; no-huddle and the final two minutes of halves/OT bypass it. User observed it working. | [Clock report](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/ASTRA_B65_CLOCK_REPORT.md) |
| Decided-game clock | Separately enabled: at a dead-ball/huddle in Q4, a possessing leader up17+ with60 seconds or less ends the remaining clock. Excludes live plays, trailing possession and OT. | [Implementation](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/mod_editor/core/nfl2k5_decided_clock.py) |
| Gameplay/CPU | Modern fourth-down/two-point/OT decisions, scrambling, contact/momentum, abilities, coverage/screens, holders, kickoff behavior and all32 modern offense/defense playbooks. These playbooks are not financial books. | [v0.6 gameplay notes](https://github.com/cruuz/softdrink-2k28/releases/tag/v0.6) |
| Franchise | Selected Experimental preset includes2026/calendar support, progression, player editing, autosave, practice and depth-lock changes; overrides include remembered weekly/CPU preparation. Autosave needs its in-game switch and an existing manual-save destination. | [Preset source](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/mod_editor/core/mod_build.py) |
| Economy | Creator explicitly intends2026,301.2M real cap and4 real dollars per internal dollar. Demand, renewal, offer, cap and rookie-economy paths change; annual schedules remain fitted approximations and do not encode exact cash/guarantees. | [Economy implementation](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/mod_editor/core/nfl2k5_franchise_economy.py) |
| Draft/free agents | CPU selection combines relative class quality, needs, positional values and randomness; free-agent preferences and prospect ranking change. It still consumes numeric ratings. | [Draft-AI implementation](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/mod_editor/core/nfl2k5_draft_ai.py) |
| Naming/cards/history | MyNFL is the Franchise label replacement, not a distinct engine. MyCareer is a separate documented mode. Experience/history fixes, letter grades and honors do not eliminate numerical ratings. Some historical honors are seeded; a full records system is absent. | [Naming/history changelog](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/docs/mod_editor/2k5_mod_studio_changelog.md) |
| Content/presentation |2026 roster snapshot, coaches/likenesses, uniforms, stadiums, ESPN presentation, music/intro and historic/moment content. New embedded roster/history data requires a fresh franchise. Creator documents approximations and incomplete live testing. | [Creator overview](https://github.com/cruuz/softdrink-2k28#softdrink-2k28), [release](https://github.com/cruuz/softdrink-2k28/releases/tag/v0.6) |

Full modern53/47/48, elevations and IR runtime enforcement is explicitly not a
finished feature; Senior Bowl is not a delivered playable event. The installed
recipe disables read-option runtime, extra created teams and16 reserves. Practice
Squad screen flags conflict with the earlier release note about removing its
incomplete screen, so actual screen coverage remains unverified. See the
[2026 runtime report](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/ASTRA_FRANCHISE_2026_RUNTIME_REPORT.md).

The retail executable already contains the Thrown To/TT label; it is not evidence
of a new SOFTDRINK counter. Counter semantics and extraction remain unverified,
as recorded in [pressure investigation](pressure-investigation.md). Do not
restart that deferred investigation merely because the label is visible.

Keep credit boundaries clear: Remade supplies native PC/runtime, controller/video,
mod-pack/save management and broadcast-package infrastructure; SOFTDRINK supplies
the pack changes above. Our addon must coordinate with existing draft/free-agent,
progression and preparation hooks, rather than letting two decision systems run.
Retain the verified4:1 opening scale, replace rating-based decision inputs with
our performance/personality model, and keep complete financial obligations and
real signing/save recovery as separate acceptance gates.
