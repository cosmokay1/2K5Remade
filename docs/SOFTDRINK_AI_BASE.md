# SOFTDRINK franchise AI compatibility gates

On October 14, 2026 the user chose SOFTDRINK if usable. Prefer the Xbox Remade
pack path and defer NFL 2K27/PCSX2 migration. This is a direction, not compatibility proof.

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
The retail-only strict reader currently rejects valid changed settings/expanded
record counts; fix that schema support before automated pack import.
