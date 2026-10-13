# Franchise negotiation and cap integration

## Source audit, October 13, 2026

Inspected Remade revision `579c72b58153c37ceb9cf20502f9ac81a3de6f4e`
and BAD-AL save converter revision `e3afeece61896380a95e506ab43ae1abda0ae8a5`.
The checkouts are in `remade/` and `save-tools/`.

Remade runs generated Xbox guest code with native runtime bridges. No named
salary-cap, contract, or negotiation API was found in the public source.
This does not establish that the original game uses decision tables or identify
a defect in its cap accounting. Neither has been measured yet.

Relevant integration points:

- `remade/tools/apply-gen-patches.py`: existing address-anchored guest patches,
  reapplied during builds. A transaction hook belongs here only after its guest
  address and calling convention are verified.
- `remade/src/nfl2k5_save_library.cpp` and `remade/docs/SAVE-LIBRARY.md`: Xbox
  working saves and readable mirrors synchronize every 2.5 seconds. Editing a
  live mirror is not an authoritative transaction interface.
- `save-tools/lib/gamesave_tool.dart` and `GAMESAVE_SECTIONS.md`: team membership,
  player records, and performance data are mapped. Salary, bonus, guarantees,
  cap totals, and contract durations are not exposed by this converter.
- `remade/tools/xbe_peek.py`: existing raw guest-image inspection utility.

No game binary or franchise save is present in these public checkouts. The
Windows runtime cannot be verified in this macOS workspace.

## First experiment: discover and verify accounting

Use copies of one franchise at one fixed date, with the game closed when copying
saves. Preserve SAVEGAME.DAT and its signing/metadata companions together.

1. Save a baseline and record the displayed cap, cap room, roster, and selected
   player's full contract terms.
2. Save again without a transaction. Compare this control pair to identify
   ordinary save bookkeeping changes.
3. Restore the baseline. Complete exactly one signing with recorded terms and
   save again. Do not advance a week or make another roster move.
4. Repeat independently for release, trade, and re-signing. Vary one contract
   term at a time where the UI permits it.
5. Compare raw payloads with:
   `python3 tools/save_diff.py before/SAVEGAME.DAT after/SAVEGAME.DAT`.
   Add `--control-after control/SAVEGAME.DAT` when the no-transaction control
   was saved from the same restored baseline. The JSON retains every transaction
   span and separately reports changes at offsets unchanged in that control and
   changes overlapping control bookkeeping. Both groups include exact bytes and
   hashes; overlap is never discarded. A single control does not establish that
   an offset is always stable or identify a contract field. Restore the exact
   baseline for each experiment; unrelated franchise dates/rosters are invalid
   comparisons even if raw lengths happen to match.
6. Trace candidate fields into generated guest functions, then verify against
   displayed accounting and a save/load round trip. Include CPU-controlled
   transactions and offseason advancement in the hook audit.

## Intended negotiation boundary

Personality, performance, relationships, and remembered promises inform LLM
offers, counteroffers, and willingness to accept. The LLM never supplies an
authoritative cap total or writes game memory directly.

A validated transaction must calculate the full team's cap usage from a
verified ledger, including existing obligations and any applicable release or
trade charges. Apply offers against the latest state; reject stale proposals
and duplicate commits. Commit the agreement and its narrative consequences
together. A rejected offer changes no contract or roster data.

Money uses integer units with verified conversion to the game's representation.
Cap equality must be allowed and a one-unit excess rejected. Tests must cover
bonus allocation, releases, trades, duplicate requests, competing offers, and
season advancement before game writes are enabled.

The user selected modern NFL-style contracts, including the rookie wage scale.
The ruleset therefore needs an authoritative external ledger if the native
contract representation cannot express those obligations. Modern guarantees,
bonus proration, cap growth, and post-June-1 treatment must not be assumed to
exist in the native game. Runtime enforcement must cover every roster transaction
and season transition; merely displaying external cap room cannot enforce it.

Future commitments should be visible in negotiations. Today's binding cap
limit and any policy reserving space for future rosters are separate checks;
do not silently prohibit a contract using invented future cap assumptions.

## Next required inputs

The user currently has no game binary or save. Offline engine development can
continue with synthetic data. Connecting it to the game still requires an
extracted Xbox `default.xbe`, a raw franchise save with its companion files, and
paired saves from the controlled experiment. These allow actual contract-field
mapping and cap bug reproduction. Until then, the implementation is an offline
prototype, not an installed franchise modification.
