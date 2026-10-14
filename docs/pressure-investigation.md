# Pressure and quarterback-hit investigation

Status: source inspection only, October 13, 2026. No verified guest counter,
contact capture, saved statistic or played/fast-sim coverage yet.

## Existing source boundaries

`src/nfl2k5_broadcast.h` exposes a sack event and player tackle/sack totals.
It contains no pressure, quarterback-hit or intended-receiver target field.
The event API takes only an event kind and team, without a play identifier,
defender, quarterback, contact time or final penalty disposition.

`src/nfl2k5_presentation.cpp:nfl2k5_presentation_popup` recognizes text containing
SACK and queues a presentation event with an empty player string. Its team value
comes from possession or a home-team fallback. `src/main.c` forwards the native
popup title to this function. This path is a presentation cue, not sufficient
evidence of defensive attribution or an official counted sack, pressure or hit.
It must not feed franchise counters directly.

The same presentation source copies supplied player totals in
`copy_player_stat`; that copying does not prove where the totals originated or
whether the game maintains additional counters. A source search found no caller
of `nfl2k5_broadcast_player_stat` outside its implementation and header within
`src`. Generated guest code and legally obtained executable/save evidence remain
to be inspected before concluding that a statistic is absent from the engine.

## Next capture work

1. Locate a stable game/play identity, offensive quarterback and defensive player
   identities. Confirm identity continuity through substitutions and save/load.
2. Capture pass release, contact start/end, sack resolution and final play status
   from guest state or events. Proximity alone does not establish contact or
   disruption. Popup text and repeated rendered frames are not play identities.
3. Compare controlled plays: clean release; contact before and after release;
   sack; scramble; two defenders contacting one QB; repeat contact; accepted and
   declined penalties; nullified plays; replay presentation; pause/save/reload.
   Resolve the intended counting rules against sourced evidence before producing
   totals. A hit and a sack may overlap; neither implies a pressure count by itself.
4. Compare before/after guest counters and raw save bytes for those plays. If a
   counter exists, prove its units, ownership, reset boundary and persistence.
   Otherwise instrument verified events and deduplicate contact episodes within
   the stable play identity, including replay/reload behavior.
5. Repeat coverage checks separately for user-played, CPU-played and fast-sim
   games. Unsupported coverage stays unknown; an explicit observed zero requires
   a complete observation window. Do not manufacture hits from sacks, pressures,
   tackles or hidden ratings.

Evidence required before franchise use: reproducible capture fixtures with game
mode, play IDs, player IDs, timestamps, final play disposition and source version;
independently checked expected attribution/counts; and a save/load round trip
showing no duplicates or loss. Legally obtained game assets and runtime access
are required for that evidence. This document introduces no guessed memory
offsets or synthetic production counters.
