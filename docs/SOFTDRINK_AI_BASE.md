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
No v0.6 game execution was performed in this investigation.

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
