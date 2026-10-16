# Real-roster historical statistics

External history is a fallback only while no complete in-game season is available.
An existing complete seeded game season also takes priority over an external fetch.
A complete season means a completed league season with supported coverage, not a
requirement that an injured or reserve player appeared in every game.
After a complete simulated season, game results supply the performance view and
model evidence; missing values do not reactivate external supplementation. Do not
fetch or display a metric unless the game can produce and display it after a full
season for that player/position. Public availability alone is not permission to
add a metric. In particular, external snap counts and starts are excluded until
matching game-season support is verified. Keep imported and simulated evidence
separate, and never add both sources' totals for the same season.

Fetch a requested historical season when needed; do not preload every year or
make a web request per simulated play/week. A2026 opening franchise may use2025
real history only under that fallback rule. Later real-world downloads must never
replace the franchise's simulated2026 results.

`franchise.nflverse.SeasonCache` is the tested download/cache foundation. Its
constructor performs no disk/network work. `poll(dataset, year, completed_game_seasons=0)` schedules only
that dataset/year on a background worker, returns `None` while pending and reuses
one request across callers. Ready data carries its source URL and content hash.
Atomic disk entries are reused after restart and never silently refreshed.
A server-owned completed-season count is required on every request; nonzero or
unknown counts refuse the fetch. Failures stay explicit; they never produce zero
statistics. Only documented
nflverse source URLs and pre-opening seasons are accepted. This helper is not yet
connected to the running sidecar, player identity mapping or game UI refresh.

The documented nflverse endpoints return season CSV datasets, not individual
player JSON responses. Fetch that year's roster only for identity matching,
player statistics for supported production metrics. Snap-count fetching is
excluded from the application cache. Cache bytes locally and select a verified individual record afterward.
No new cloud service, API key or model request is needed for these public sources.

Match real players using both supported saved biography and source identifiers;
never fuzzy-match a name or attach a real player's history to a fictional rookie.
Preserve unmatched players as unknown. Imported evidence must retain the source
season, regular/postseason distinction, external ID, source URL/hash and coverage.
Keep separate seasons separate and avoid adding game-imported and external totals
for the same season. Starts, pressures and other unavailable fields remain unknown.
Snap-count game rows do not establish starts.

The private read-only2025 audit matched1753 of2070 MyNFL1 identities uniquely by
name and DOB components;317 were unmatched. It did not attach records to actors.
Hernandez, Dart and Nabers each have a unique match. The sampled Hernandez snap
source has participation evidence, but it will not be imported or displayed under
the game-parity rule. These read-only audits did not alter franchise records.

The existing native saved-history reader now additionally maps receptions,
receiving yards and receiving touchdowns. The original REC/YDS/TD field selectors
at509A80 use2E/4F/3E; descriptorA8A510+field*1C+0C maps these to12/13/14. The pinned
retail and SOFTDRINK v0.6 images agree. Actual MyNFL1 Nabers readback retains
109/1204/7 and18/271/2 as separate career periods. Dart already has nine supported
passing/rushing/game records. Hernandez has no saved history pointer. No missing
history is synthesized from ratings.

Sources and credits:

- [nflverse player statistics](https://nflreadr.nflverse.com/reference/load_player_stats.html)
- [nflverse rosters](https://nflreadr.nflverse.com/reference/load_rosters.html)
- [Pro Football Reference snap counts via nflverse](https://nflreadr.nflverse.com/reference/load_snap_counts.html)
- [Dataset CC BY4.0 license](https://github.com/nflverse/nflverse-data/blob/main/LICENSE.md)
- [Pinned mod editor record-layout reference](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/mod_editor/core/nfl2k5_roster_records.py)

Downloaded datasets and third-party reference source stay private and are not
vendored into this repository. The cache records attribution and the dataset
license URL. The addon transport remains independent of these franchise rules.
