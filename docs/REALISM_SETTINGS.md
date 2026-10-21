# rspencer86 settings on stock SOFTDRINK

The user selected rspencer86's published gameplay set on October21.
Source: [author's post and clock discussion](https://forums.operationsports.com/forums/forum/football/nfl-2k/espn-nfl-2k5-football/espn-nfl-2k5-sliders/121121-rspencer86-s-realism-sliders-gameplan-settings).
Author's original platform: PS2/default rosters. SOFTDRINK results still need testing.

`data/settings/rspencer86.json` records all21 sliders, maxed penalties, Normal
speed, Performance EQ off and Multiple Hot Routes off. The author's coaching
gameplan changes are deliberately excluded: preserve SOFTDRINK's profiles.
Played quarters begin at10minutes; simulated quarters stay5minutes throughout
played-clock tuning. SOFTDRINK's20-second accelerated-clock minimum is unchanged.

`python3 -m tools.prepare_rspencer_settings SOURCE OUTPUT --played-minutes 10`
prepares a fresh signed PC-runtime Settings1 directory; it never edits SOURCE.
Only identified slider words and their gameplay mirrors, penalties, speed/EQ/
hot-route options and quarter lengths change. No roster/franchise/coach writes.
Native option evidence: speed getter1490E0 readsE5FFA8; formatter14C480 selects
Slow/Normal/Fast from4ED944. EQ1493E0 readsE60034 and hot routes1494E0 readE60040;
their formatters use Off/On at4ED994. Penalty-enable149B70 readsE6008C; float
getters149C50..14A3A0 coverE60090..E600B8 excluding unusedE600A8. Slider layout
credits Mod Studio RC112's save_writer. PC signatures use the existing runtime
zero-key format, not a cloud credential.

Installed after confirmed normal exit in stock profile Settings1, container
83C3760943CB, both physical UDATA and organized settings directory. No prior
Settings1 existed there. Old profile Settings1 was used only as a signed template;
105 bytes changed, scope checked, all21 authored numbers and both mirrors read
back correctly, signature verified. New settings SHA256:
fc382432f7a65cec01ed9c29579e73ee7d1b842d62ce9d2659f453a99ff3c49a.
Old template unchanged;28 preexisting other stock save files unchanged.
Game EXE and active roster pack unchanged, no addon, scheduled task OFF.
Private installer/receipt: Deck native-05ac4e9/rspencer-settings-v1.

## Played-clock acceptance

1. Load Settings1 in-game before starting a match. Confirm Normal and10/5.
2. Play a complete regulation exhibition using normal playcalling/replay habits.
3. For BOTH teams record pass attempts, rush attempts and sacks allowed. Their
   sum is the estimated combined offensive play count; exclude kickoffs/punts/
   field goals. Record overtime separately rather than treating it as regulation.
4. Aim near126 combined plays, accepting a useful initial band of120–135.
   NFL2025's32 published team scrimmage-play totals sum to34417, or126.533 per
   game over272 games: [NFL reference](https://amp.nfl.com/stats/team-stats/offense/downs/2025/reg/all).
5. If volume is outside the band, estimate next played minutes as
   current_minutes*126.533/observed_plays, round to a supported integer1..15,
   then verify another game. Keep every slider, simulated quarter and accelerated
   clock rule fixed. One matchup is a first adjustment, not robust calibration.

Game load, a completed trial and clock calibration remain UNVERIFIED. An earlier
post-play access-violation crash is still unresolved; this settings import does not repair that defect. Preserve any next crash evidence.
