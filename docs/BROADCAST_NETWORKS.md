# Schedule-based broadcast assignments

The coverage policy uses saved matchup dates, the game's 12-hour kickoff field,
home/away conference and season phase. It makes no random draw and does not use
ratings, simulation results, AI calls or changing standings. Reopening the same
schedule gives the same assignments. It never reschedules a game.

- Sunday afternoon: CBS for AFC visitors, FOX for NFC visitors.
- Sunday evening: NBC; Monday: ESPN; Thursday: Prime, with the early-September
  opener and Thanksgiving evening on NBC.
- Thanksgiving early/late: CBS/FOX. Saturday regular season and Sunday 9:30:
  NFL Network. Preseason uses regional coverage by the home team's conference.
- Postseason preserves the evening windows and otherwise uses conference
  coverage. This is an editable simulation policy, not verified TV rights.

The source schedule has no AM/PM field. Sunday 9:30 is treated as morning;
other 7–11 kickoffs are treated as evening. Those are explicit conventions.
The policy preserves the actual schedule's dates; it does not infer a calendar
year from a roster's name or the franchise UI's displayed year.

Presentation Studio → **Franchise networks** reads a selected saved franchise,
lists the matchup and reason, and allows a network override for each game.
Automatic clears an override. Network-to-package mappings and the enable switch
live in `mods/broadcast-networks.json`, outside saves. Equivalent copies of the
same season schedule share overrides. A new schedule/season has a different
identity, so stale overrides do not attach to unrelated matchups. This identity
is a non-security FNV checksum, not a franchise ownership credential.

Start the Python editor with `--saves /path/to/runtime/saves/franchise`, or pass
that path as the second argument to `launch.sh`. Only the selected save is read;
no franchise file is written. Refresh after saving changed/new playoff matchups.

The native adapter reads a bounded schedule copy and matches the current game to
the current franchise phase/week and team pair. Unsupported calendars, ambiguous
matches and non-franchise modes preserve manual presentation selection. It applies
the chosen package at a match boundary, restores the manual preference afterward,
and allows an explicit native menu/F2 selection for the remainder of that match.
Settings changes apply to the next loaded matchup, avoiding mid-play switches.
Missing network graphics use original ESPN, with an explicit log message.

Defaults map CBS/FOX to their native JSON packages, NBC to `NBC_SNF`, ESPN to
`ESPN_MNF` and Prime to `Prime_TNF`. NFL Network requires an installed mapping.
MNF/TNF are custom variations of the NFL2K5-PC NBC package, sharing its original
art, data and animations with different branding and accents. Their manifests
retain the base author's credit. They require the sibling NBC_SNF package.

## Restoring the original NBC media

The source archive deliberately excludes local reference artwork. The official
[v0.6.0-nbc-snf installer](https://github.com/BeyondTomrrow/2K5Remade/releases/tag/v0.6.0-nbc-snf)
contains the original PNG plates, masks, peacock and team logos. Its
published SHA256 is
`fa585e0e602de51dd5f397f0007a33dd6145728f2629fa5b94e8591b019d95a4`.
That checksum was verified before unpacking. The installer was not executed.
The current portable Inno Unpacker supports its 7.0 format; the Linux
innoextract 1.9 release does not. Duplicate-file filters failed to recover all
paths; full temporary extraction recovered the media, then the unrelated files
and 216 MB installer were removed. Only 43 missing NBC media files, 24,331,805 bytes,
were installed. No existing edits were overwritten. Media remains private under
the repository's existing asset ignores; this is not a redistribution license.
The NBC package's optional broadcast font is not included in that release.

NBC now declares its mandatory background assets. The native loader rejects
an incomplete package rather than offering broken text-only graphics. Studio's
**Run preview clocks** animates sample clocks; it does not control game clocks.

## Verification and remaining acceptance

Seven Python policy tests include 5,490 Python/C++ calendar comparisons. Seven
HTTP tests exercise persistent overrides, package editing and unchanged save
bytes, including traversal and cross-origin rejection. The original NBC script
suite passes 107 checks. The two saved 272-game trials produce identical network
assignments despite different football results. The native Windows game compiled
and linked using the existing compiler. The final MNF/TNF routing defaults
still need an incremental relink; no binary has been installed for this feature. Native match selection, actual graphics and override persistence
still require a real Deck matchup and relaunch. Do not call these stages verified
from the compile or source fixtures alone.

Pending scope: expose supported runtime gameplay and SOFTDRINK controls together
with broadcast settings, and provide access to the broader Mod Studio tools.
Fourth-down tuning waits for the active-image/dispatch audit in
[CPU_FOURTH_DOWN_AUDIT.md](CPU_FOURTH_DOWN_AUDIT.md). Scheduled task stays off.
