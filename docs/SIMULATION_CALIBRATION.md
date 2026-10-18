# SOFTDRINK simulated-season calibration

User authorized disposable copies of MyNFL1; the main save must stay untouched.
The scheduled task stays off. No model requests, credentials or franchise ledger
are needed for this experiment. No screenshots without an explicit user request.

## Prepared October 17

Deck profile: `/home/deck/.local/share/2k5-franchise-build/simulation-calibration-v1`.
Its only franchise is named **SIMTEST**. The copied SAVEGAME.DAT is byte-identical
to MyNFL1 (`4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3`).
Only the test copy's display metadata/name changed. Separate writable saves,
caches, portable configuration, input queue and logs; existing content assets
are shared. No addon or service/ledger/credential configuration was copied.
All 66 original loose-save files matched the pre-copy manifest. The ordinary
Steam entry was temporarily routed for one launch, then restored byte-for-byte. The known game EXE/Proton runtime is reused.

Direct launch attempts produced an invisible game process. The test-only
process was stopped and the game dispatched through the existing Steam entry,
with normal routing restored immediately afterward. The user confirmed the NFL2K5 main menu is visible. Asked them to load SIMTEST
and open its schedule. They instead reported damaged-save entries. All copied
DAT bytes and PC HMAC signatures still verify; load acceptance FAILED.
Do not simulate or recommend settings. After normal exit, exact original container names/metadata were restored in the
isolated profile (display MyNFL1, still separate from the real save); the failed
import was retained. Steam relaunch dispatched and normal routing restored.
Awaiting actual load confirmation. No claim that renaming is the proven cause. No season has been simulated and no settings recommendation has
been established by this experiment.

## Tool reuse

- `tools/game_test_control.py`: existing bounded button batches and log status.
  A consumed input queue does not prove menu state. Ask for the visible screen
  before navigating; stop on an unexpected screen or confirmation dialog.
- Existing roster/calendar and player-history readers validate supported saves.
- `tools/inspect_simulation_totals.py`: read-only team yards/turnovers report,
  adapting the documented team-stat field map from cruuz's pinned save reader.
  Field names still need corroboration against the game's completed-season table.
  Missing/zero games produce unmeasured rates, not a fictitious successful result.
  Raw retail calendar year is distinct from the SOFTDRINK logical 2026 binding.
- `tools/prepare_simulation_trial.py` creates signed copies, never in-place edits.
  Source tracing now identifies played minutes at settings+0x8C (getter149170,
  E6000C) and simulated minutes at+0x90 (menu descriptor52BD74 names Sim. Quarter
  Length; getter2C6F60 reads E60010; arrows2C6F00/30 bound3..15). The creator's
  serializer map places the settings prefix at E5FF80. Valid PC-runtime HMAC
  signatures are required; the signing implementation follows Remade's existing
  public zero-runtime-key path. Actual baseline is8played/5simulated. Three
  signed variants5/6/7 were prepared; only the simulation word and signature
  differ, while source remains identical. In-game load/display confirmation is
  still required. Do not assign names to unknown statistic codes.

## Experiment

1. Confirm SIMTEST loads and capture a saved baseline plus its settings. Record
   the pack, game hashes and actual schedule/game count; do not assume 17 games.
2. Test simulated quarters at 5, 6 and 7 minutes, restoring the **disposable**
   baseline between trials. Hold roster, difficulty, preparation and sliders
   constant. Confirm each setting survives save/load before its trial.
3. Save checkpoints immediately after preseason and at regular-season completion,
   before postseason or offseason resets. Establish whether team counters reset
   at the regular-season boundary; exclude preseason/postseason from comparisons.
4. Corroborate exported yardage/turnover/game counts against the game table.
   Measure scoring, pass/rush attempts, sacks and individual distributions only
   where named readers or observed game tables support them. Offensive plays
   are pass attempts + rush attempts + sacks taken, not a yardage estimate.
5. Compare league totals divided by actual team-games against one explicitly
   selected completed NFL season, alongside completion %, yards per carry/pass
   attempt, sack/interception rates and concentration among starters. Preserve
   team variation; do not tune to one star or demand identical team outputs.
6. Run additional fresh trials at the best candidate to check random variation.
   Change one setting group at a time. Gameplay slider effects on quick simulation
   are unproven until measured; do not assume an effect.
7. Rehash the normal profile against `main-save-manifest.json` after each trial.
   Preserve raw checkpoints/results. Recommend a setting only after real season
   runs; do not apply it to MyNFL1 as part of this experiment.

Played-game calibration is separate. Twelve-minute played quarters remain an
untested starting point with the installed accelerated clock, not a conclusion
from fast-simulation results.
