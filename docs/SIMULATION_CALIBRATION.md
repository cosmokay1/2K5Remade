# SOFTDRINK simulated-season calibration

User authorized disposable copies of MyNFL1; the main save must stay untouched.
The scheduled task stays off. No model requests, credentials or franchise ledger
are needed for this experiment. No screenshots without an explicit user request.

## Prepared October 17

Deck profile: `/home/deck/.local/share/2k5-franchise-build/simulation-calibration-v1`.
The first named SIMTEST copy had unchanged DAT bytes but showed damaged-save
entries. After a normal exit, exact original container names/metadata were copied
into a fresh test save tree; the failed import was retained. The user confirmed
that copied **MyNFL1** now loads. This is still the separate test runtime, never
the normal MyNFL1. The precise initial load-failure cause is not yet proven.

The starting DAT matches MyNFL1
(`4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3`).
All66 original loose-save files matched after test startup. Writable saves,
cache/configuration/input/logs are separate; content assets are shared. No addon,
service, ledger or credentials were copied. Normal Steam routing is restored
immediately after each test launch. Direct launches were invisible; the working
route is the existing Steam entry temporarily dispatched to the test script.

The first 5-minute season is complete and saved as **MyNFL2**: 272 games,
17 per team. The user confirmed Dart's exported passing line against the game.
Detailed results and mapping limitations follow below. The user is now running
the 6-minute comparison; no agent reset or input should interrupt them. No best
setting has been established from comparative or repeated trials yet.

## Tool reuse

- `tools/game_test_control.py`: existing bounded button batches and log status.
  A consumed input queue does not prove menu state. Ask for the visible screen
  before navigating; stop on an unexpected screen or confirmation dialog.
- Existing roster/calendar and player-history readers validate supported saves.
- `tools/inspect_simulation_totals.py`: read-only team yards/turnovers and regular-season combined score report,
  adapting the documented team-stat field map from cruuz's pinned save reader.
  Field names still need corroboration against the game's completed-season table.
  Missing/zero games produce unmeasured rates, not a fictitious successful result.
  Regular-season scoring excludes preseason/playoff rows and flags mismatched
  team-game counts. Raw retail calendar year is distinct from the SOFTDRINK logical 2026 binding.
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

1. Confirm the isolated MyNFL1 copy loads and capture a saved baseline plus its settings. Record
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

## Reference

2025 is the selected completed NFL reference season. Computed from all32 teams
in the official [passing](https://www.nfl.com/stats/team-stats/offense/passing/2025/reg/all)
and [rushing](https://www.nfl.com/stats/team-stats/offense/rushing/2025/reg/all)
tables, per544team-games:61.26offensive plays,209.70net passing yards and116.94
rushing yards per team/game. Raw passing yardage must be confirmed as net/gross
before comparing; gross reference is225.02yards/team/game. These are calibration
references, not data injected into players or claims about the simulated output.

## First completed trial — 5-minute simulation

User saved the disposable result as **MyNFL2**. Physical result SHA256:
`9077c8f654209196de568d7699c37acd40c3ad1c306fc89aca9558a96c85b734`.
Saved setting remains8played/5simulated minutes. All272regular-season games are
marked played;32teams each have17recorded games (544team-games), matching the
regular grid. All66normal-profile files still match the original manifest.
User corroborated Dart's3562passing yards/25TD/7INT against the game.

| Per team/game | 5-minute trial | Official2025 reference |
|---|---:|---:|
| Offensive plays, from player attempts + defensive sack credits |63.53|61.26|
| Pass attempts |30.09|32.06|
| Rush attempts, from player histories |30.96|26.84|
| Gross passing yards |236.72|225.02|
| Rushing yards |125.02|116.94|
| Completion percentage |63.72%|64.32%|
| Gross yards/pass attempt |7.87|7.02|
| Yards/rush |4.04|4.36|

Combined score over the272-game regular grid is12544points,23.06/team/game.
This is one trial, not a demonstrated optimum. Passing and rushing player-yard
sums match their team fields exactly. Defensive half-sack credits sum1352events,
matching raw QB history11. Player rush attempts sum16841 versus16858in the team
candidate counter (17difference), and completions exceed recorded receptions by8.
Keep these discrepancies explicit; do not silently normalize game records.

The reused source label at team+1D2 is **disproved as total offense**: Giants427
there, versus3562passing+2161rushing. It is now excluded from named metrics.
A regression covers this observed mismatch using authored synthetic bytes.
Passing is gross here: team and QB history yardage sums match. The report names
combined yardage passing_plus_rushing_yards; never compare it with NFL net offense.
Do not propagate the unverified source label into negotiation/performance data.

Player distributions also need attention:

| Season threshold | Simulated players | NFL2025 players |
|---|---:|---:|
|4000passing yards |18|6|
|1000rushing yards |31|17|
|1500rushing yards |14|3|
|1000receiving yards |21|20|

References: official NFL2025 [passing](https://www.nfl.com/stats/player-stats/category/passing/2025/reg/all/passingyards/desc),
[rushing](https://www.nfl.com/stats/player-stats/category/rushing/2025/reg/all/rushingyards/desc)
and [receiving](https://www.nfl.com/stats/player-stats/category/receiving/2025/reg/all/receivingyards/desc)
leaderboards. Each fetched table extends below the relevant threshold; no count
is extrapolated beyond its first25rows. Current-period/mode0history only; prior
seeded years are excluded. All32passers with200+attempts recorded17games.
Saved Injury slider stays20/40; both Fatigue sliders stay4/40. That does not prove
injury enablement, rotation or quick-simulation injury behavior. Quarter duration
alone may not correct starter workload concentration and run/pass balance.

After initially requesting no reset, the user chose to run the6-minute trial
personally. No agent reset or game input was sent. Asked them to reload the
unchanged MyNFL1 copy in the isolated runtime, set6minutes, simulate the same year
and save as MyNFL3. Awaiting that result. Do not assume a paired trial until its
season, setting and baseline lineage are checked. Twenty-three targeted tool
checks pass; no new native binaries or cloud inference are involved.
