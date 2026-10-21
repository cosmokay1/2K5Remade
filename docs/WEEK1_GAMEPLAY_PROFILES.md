# Missing Week 1 gameplay profiles

These estimates fill missing native player records only. They do not enter
negotiation demands, contract pricing, personality or franchise decisions.
Preserve existing verified community profiles, including Jihad Ward's recovered
older record and Sedrick Van Pran's existing shortened-name record.

## Evidence and approximation policy

Use prior completed NFL production and snaps first. For an early-career player
without an NFL sample, use draft position as an uncertainty prior, not proof of
ability. Undrafted does not mean incapable; an established veteran's old draft
pick does not replace his recent performance. College production and role provide
context; college totals are not numerically equivalent to NFL totals.

The creator's pinned public tooling at commit
`e19384123c23a3601949dda67c9a3ab754d65fd6` documents two models:

- [M2](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/docs/nfl2k5_ratings_model.md)
  maps position-specific production percentiles to the original 2K5 attribute
  distributions. It can reuse our already captured 2025 NFL statistics/rosters/
  snap counts. Its limits include approximate blocking and missing measurables.
- [V2](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/tools/ratings_v2/model.py)
  improves shrinkage and position/tier modeling. Its draft priors are .75 for
  picks1–10, .65 through32, .55 through64, .45 through100, .38 through150,
  .30 through262 and .20 otherwise. These are percentiles, not overall ratings.

Our private compatibility trial uses M2 for available NFL samples. For absent
samples it applies V2's draft prior to the pinned M2 reference distribution;
older low-volume backups use the .20 position profile instead. This is our
explicit approximation, **not the creator's exact current V2 output**. The
receipt records model, source hashes, sample availability and fallback per player.
We do not rerate the existing SOFTDRINK population or use uniform 75 defaults.

A measured combine forty can set speed using the creator's original-scale fit.
For Horn, use the club-reported4.46 combine time; don't substitute the faster,
hand-timed pro-day range. Missing drills remain flagged profile estimates.

## Seven missing active records

| Player | Sourced evidence | Treatment |
| --- | --- | --- |
| Zach Wood | [Saints biography](https://www.neworleanssaints.com/team/players-roster/zach-wood/): snapped all17 games in2025, two special-teams tackles | Established long-snapper role; sparse tackle rows are not his games-played record |
| Thomas Odukoya | [Titans biography](https://www.tennesseetitans.com/team/players-roster/thomas-odukoya/splits/2022/reg/):2022 undrafted international-pathway TE;2021 college13 catches/130 yards/two TD | Limited receiving evidence; do not turn missing catches into zero blocking ability |
| Garrett Dellinger | [Ravens draft profile](https://www.baltimoreravens.com/draft/draft-tracker/2025/):2025 pick243;13 LG starts in2023 and seven in2024 | Early-career missing-sample prior; retain actual second-year status in2026 |
| Jimmy Horn Jr. | [Colorado](https://cubuffs.com/news/2025/4/26/football-jimmy-horn-jr-drafted-by-the-carolina-panthers):2025 pick208;2024 receiving37/441/one TD. [Panthers](https://www.panthers.com/news/jimmy-horn-jr-showing-off-some-speed-but-still-has-another-gear-panthers):4.46 combine forty | Prefer captured2025 NFL production; measured speed, not a generic late-round WR profile |
| Ricky Barber | [UCF](https://ucfknights.com/sports/football/roster/player/ricky-barber):2024 had34 tackles, six TFL,2.5 sacks. [Commanders](https://www.commanders.com/team/players-roster/ricky-barber/career):2025 five tackles/one sack in two games | NFL sample first, with its small size visible in the evidence |
| Johnathan Edwards | [Colts2025 statistics](https://www.colts.com/team/stats/2025/reg):26 tackles,19 solo. [Colts biography](https://www.colts.com/team/players-roster/johnathan-edwards/logs/2026/reg/):2025 UDFA;2024 Tulane24 tackles/one PD | Observed NFL performance takes precedence over undrafted status |
| Beau Gardner | [Georgia](https://georgiadogs.com/news/2025/12/13/football-gardner-wins-patrick-mannelly-award):2025 Patrick Mannelly Award winner | Specialist role; absence of normal offensive statistics is expected |

The native game represents LS as C. For the three missing specialist records
(Wood, Gardner and qualified free agent Jacob Bobenmoyer), use the median of six
independently bound SOFTDRINK LS profiles, not the generic center distribution.
This does not simulate measured snapping accuracy, and Gardner's award does not
justify inflating his general offensive-line blocking attributes.

## Actual offline result and limits

Private `missing-gameplay-estimates.json` contains19 complete estimates: the
seven active players above plus12 absent profiles in the qualified FA subset.
Private `assembled-roster-receipt.json` binds1753 players (1695 active/inactive,
58 evidence-qualified FAs):1685 native profiles,38 Week1 community profiles,
11 older community profiles and19 estimates. The593984-byte roster serializes
and reloads losslessly; all32 memberships, portrait IDs, estimated attributes and
sourced birthdays match. Unassigned/classic records remain byte-identical.
Two overlong community surnames use explicit display aliases: Easton
Mascarenas-A. and Brandon Crenshaw-D.; full GSIS identities remain unchanged.

The58 FA candidates are a qualified subset, not a certified exhaustive pool.
Native contracts remain legacy/display projections: the modeled modern cap book
has not been applied to a fresh franchise. No Deck load, on-field behavior,
signing, cap enforcement or save/reload has been verified for this hybrid.
MyNFL1 and the Deck were not modified; scheduling remains off.

Original codec/model provenance: MIT, Copyright2026 Noah and the 2K Football Mod
Tools contributors; record research credits Flying Finn/Glen Leskinen and BAD_AL.
Source assets, downloaded player data, headshots and retail binary data stay
private and are not included in this repository change.
