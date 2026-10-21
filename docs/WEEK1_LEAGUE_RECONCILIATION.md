# Week 1 league reconciliation

The target is all 32 teams and one shared, historically accurate free-agent pool.
Giants work is an investigation case, not a delivery shortcut. Every club needs
verified membership, annual contracts, reserve/practice-squad obligations,
retained/dead charges and club cap adjustments before the league is certified.
A complete set of roster schedules alone does not establish a full cap book.

## Modeled opening charges — October 20, 2026

The user authorized educated positional salary estimates where real salary data
cannot be defined. This supersedes the earlier requirement to wait for every
rookie historical source before modeling opening charges. It does not convert
estimates into historical facts, authorize guessed free-agent availability, or
permit adjusting prices to make a team fit under the cap.

The supplied weekly snapshot now has a charge for every one of its 2,526 club
entries: 1,930 archived annual figures preserved, 307 published matching-contract
estimates, 134 rookie projections and 155 positional estimates. Of the 150
historical rookie exceptions, 148 have modeled charges on club lists; two lack
club ownership. Four archived rookies in total need separate FA/rights review:
Hank Beatty, Mani Powell, Quentin Moore and Marcus Allen. Do not add them to a
team or erase their prior obligations merely to close the count.

Rookie projections preserve a known signed nominal total. Four-year draft deals
use the four nearest available draft slots; other rookie/replacement terms use
matching contract types. Exact rational weights and deterministic whole-dollar
allocation preserve the total. These are annual cap projections, not verified
base salaries, paid bonuses or guarantees.

Other gaps use position, experience and active/reserve/practice role. An
unambiguous own APY is preferred, using peer annual-cap/APY ratios; otherwise use
the comparable positional median. Thin specialist PS groups use the practice
experience tier. Sparse reserve groups use a full-salary positional projection
without inventing a split discount. Active-player floors use the adopted
simulation-experience rule. Known charges remain unchanged; neither ratings nor
team budget affects the prices. Insufficient peers and duplicate ownership still
fail explicitly. A GSIS ID is not proof of a native player binding.

| Club | Archived | Published estimate | Rookie model | Positional model | Missing charges |
| --- | ---: | ---: | ---: | ---: | ---: |
| ARI | 63 | 8 | 4 | 3 | 0 |
| ATL | 57 | 10 | 5 | 8 | 0 |
| BAL | 55 | 11 | 5 | 6 | 0 |
| BUF | 63 | 9 | 2 | 1 | 0 |
| CAR | 62 | 11 | 1 | 7 | 0 |
| CHI | 64 | 11 | 2 | 6 | 0 |
| CIN | 61 | 7 | 3 | 0 | 0 |
| CLE | 61 | 13 | 4 | 5 | 0 |
| DAL | 61 | 7 | 6 | 4 | 0 |
| DEN | 63 | 8 | 3 | 4 | 0 |
| DET | 62 | 8 | 2 | 5 | 0 |
| GB | 63 | 9 | 4 | 6 | 0 |
| HOU | 64 | 9 | 5 | 6 | 0 |
| IND | 56 | 13 | 6 | 1 | 0 |
| JAX | 59 | 9 | 8 | 1 | 0 |
| KC | 54 | 13 | 6 | 6 | 0 |
| LA | 59 | 8 | 5 | 5 | 0 |
| LAC | 56 | 12 | 3 | 7 | 0 |
| LV | 58 | 11 | 5 | 11 | 0 |
| MIA | 57 | 8 | 8 | 4 | 0 |
| MIN | 54 | 13 | 3 | 10 | 0 |
| NE | 59 | 12 | 4 | 4 | 0 |
| NO | 65 | 9 | 5 | 6 | 0 |
| NYG | 62 | 10 | 2 | 4 | 0 |
| NYJ | 60 | 6 | 6 | 8 | 0 |
| PHI | 62 | 10 | 3 | 0 | 0 |
| PIT | 62 | 10 | 2 | 2 | 0 |
| SEA | 63 | 8 | 2 | 6 | 0 |
| SF | 67 | 10 | 5 | 2 | 0 |
| TB | 54 | 11 | 5 | 5 | 0 |
| TEN | 61 | 8 | 3 | 7 | 0 |
| WAS | 63 | 5 | 7 | 5 | 0 |

This is coverage of the supplied snapshot, not a corrected opening roster or a
balanced final cap ledger. Known stale membership remains, including Slayton's
September7 release. Retained charges, adjustments, eligibility, native identity
bindings and the historical global FA pool remain separate. The estimator
therefore returns no certified cap room and keeps signing/import readiness off.

The newly inspected [September4 cap texture](https://mrcaseb.com/posts/nfl_cap_texture.html)
contains rounded percentages, not exact retained-debt/club-adjustment rows. It
cannot replace those obligations or justify cap credits. No current-table values
were imported as dated liabilities.

Reproduce with `python3 -m tools.estimate_week1_salaries WEEKLY.json CONTRACTS.json
ROOKIES.json --season-year 2026 --league-cap 301200000 --output ESTIMATES.json`.
JSON inputs contain rows/rows/reports respectively; output cannot overwrite any
input. Private modeled-opening-charges.json stores the complete model and input
hash. No source archive, game save or runtime is mutated.40 focused tests pass.

## Rookie source pass — October 18, 2026

Audited all 459 current-year rookie contracts in the archived active subset,
including undrafted players and replacement contracts. Published schedules match
309 archived identities, owners, terms and nominal totals: 197 Drafted, 33 UDFA,
78 Practice and one SFA replacement. Of these, 307 supplement club-listed gaps.
These later published schedules are **comparisons, not verified Week 1 charges**;
the original 1,930 archived annual matches remain a separate evidence category.
No salary, paid bonus, retained debt or cap-room authority is inferred from them.
Five matching cap schedules have inconsistent published cash components; those
components remain flagged and are not imported as cash or salary.

150 rookie contracts remain unresolved: 61 unavailable pages, 43 annual-total
contradictions, 24 different current contract generations, nine archived-lineage
conflicts, nine truncated identity/history pages, three ownership/history
conflicts and one unsupported bonus allocation. Reserve/split-salary changes
explain some patterns but their effective dates and exact opening treatment are
not established. Do not restore a cut rookie's original deal over a later practice
contract, or erase original retained bonus debt when importing the replacement.

Across all club lists, 289 entries still lack even a matching annual comparison:
42 ACT, 75 RES, 171 DEV and one EXE. The separate retained/dead-money, club
adjustment and historical free-agent/rights gaps remain open. This is a concrete
source-data blocker to a reconciled hybrid, not a completed cap import. No new
Deck candidate was created; MyNFL1 is untouched and scheduling remains PAUSED.

| Club | Archived annual matches | Additional published comparisons | Still without a comparison |
| --- | ---: | ---: | ---: |
| Cardinals (ARI) | 63 | 8 | 7 |
| Falcons (ATL) | 57 | 10 | 13 |
| Ravens (BAL) | 55 | 11 | 11 |
| Bills (BUF) | 63 | 9 | 3 |
| Panthers (CAR) | 62 | 11 | 8 |
| Bears (CHI) | 64 | 11 | 8 |
| Bengals (CIN) | 61 | 7 | 3 |
| Browns (CLE) | 61 | 13 | 9 |
| Cowboys (DAL) | 61 | 7 | 10 |
| Broncos (DEN) | 63 | 8 | 7 |
| Lions (DET) | 62 | 8 | 7 |
| Packers (GB) | 63 | 9 | 10 |
| Texans (HOU) | 64 | 9 | 11 |
| Colts (IND) | 56 | 13 | 7 |
| Jaguars (JAX) | 59 | 9 | 9 |
| Chiefs (KC) | 54 | 13 | 12 |
| Rams (LA) | 59 | 8 | 10 |
| Chargers (LAC) | 56 | 12 | 10 |
| Raiders (LV) | 58 | 11 | 16 |
| Dolphins (MIA) | 57 | 8 | 12 |
| Vikings (MIN) | 54 | 13 | 13 |
| Patriots (NE) | 59 | 12 | 8 |
| Saints (NO) | 65 | 9 | 11 |
| Giants (NYG) | 62 | 10 | 6 |
| Jets (NYJ) | 60 | 6 | 14 |
| Eagles (PHI) | 62 | 10 | 3 |
| Steelers (PIT) | 62 | 10 | 4 |
| Seahawks (SEA) | 63 | 8 | 8 |
| 49ers (SF) | 67 | 10 | 7 |
| Buccaneers (TB) | 54 | 11 | 10 |
| Titans (TEN) | 61 | 8 | 10 |
| Commanders (WAS) | 63 | 5 | 12 |

Reproduce with `python3 -m tools.rookie_contract_sources CONTRACTS.json --sources
CAPTURE.txt ... --season-year 2026 --report REPORT.json`, optionally adding
`--updated-contracts COMPARISON.json`. Outputs cannot replace input files.
Private captures and `rookie-source-audit.json` retain individual source URLs and
hashes. `source-research/league-rookie-comparison.json` records the all-team
comparison, not historical payroll. Source captures with conflicting schedules
are rejected rather than selected by retrieval order.

Validation: 34 focused source/identity/portrait/transaction checks passed. No
runtime code, native build, saves, inference, credentials or controls changed.

## Original archived source coverage — October 18, 2026

The same `league_source_coverage` pipeline audits every club and refuses a missing
or unknown team. It uses the cached September 10 NFL weekly roster and contract
archive, preserving conflicting or absent amounts as unresolved. This covers
2,526 club-listed players: 1,930 matched annual cap figures and 596 unresolved.
All 32 opening books remain incomplete. These counts do not measure overall
project completion and the amounts below are not cap room or complete payroll.

The gaps include 255 drafted rookies from 2026. By roster list: 266 ACT, four INA,
78 RES, 247 DEV and one EXE entry lack matching annual figures. Fix these source
cohorts across the league rather than hand-tuning the Giants. Missing money is
not zero; retained debt can coexist with a later contract for the same player.
The global FA/rights audit is separate and remains incomplete.

| Team | Matched / club-listed | Unresolved | Known charge subtotal only |
| --- | ---: | ---: | ---: |
| Cardinals (ARI) | 63 / 78 | 15 | $211,627,054 |
| Falcons (ATL) | 57 / 80 | 23 | $223,376,654 |
| Ravens (BAL) | 55 / 77 | 22 | $271,726,090 |
| Bills (BUF) | 63 / 75 | 12 | $240,488,559 |
| Panthers (CAR) | 62 / 81 | 19 | $277,883,563 |
| Bears (CHI) | 64 / 83 | 19 | $263,961,122 |
| Bengals (CIN) | 61 / 71 | 10 | $284,915,683 |
| Browns (CLE) | 61 / 83 | 22 | $183,517,978 |
| Cowboys (DAL) | 61 / 78 | 17 | $244,143,280 |
| Broncos (DEN) | 63 / 78 | 15 | $264,604,840 |
| Lions (DET) | 62 / 77 | 15 | $272,460,211 |
| Packers (GB) | 63 / 82 | 19 | $239,024,352 |
| Texans (HOU) | 64 / 84 | 20 | $211,859,442 |
| Colts (IND) | 56 / 76 | 20 | $247,920,075 |
| Jaguars (JAX) | 59 / 77 | 18 | $232,486,543 |
| Chiefs (KC) | 54 / 79 | 25 | $257,590,057 |
| Rams (LA) | 59 / 77 | 18 | $289,166,020 |
| Chargers (LAC) | 56 / 78 | 22 | $250,678,498 |
| Raiders (LV) | 58 / 85 | 27 | $229,690,620 |
| Dolphins (MIA) | 57 / 77 | 20 | $96,090,409 |
| Vikings (MIN) | 54 / 80 | 26 | $238,260,810 |
| Patriots (NE) | 59 / 79 | 20 | $274,734,229 |
| Saints (NO) | 65 / 85 | 20 | $189,670,372 |
| Giants (NYG) | 62 / 78 | 16 | $233,045,649 |
| Jets (NYJ) | 60 / 80 | 20 | $169,236,801 |
| Eagles (PHI) | 62 / 75 | 13 | $216,704,807 |
| Steelers (PIT) | 62 / 76 | 14 | $273,297,101 |
| Seahawks (SEA) | 63 / 79 | 16 | $285,667,419 |
| 49ers (SF) | 67 / 84 | 17 | $226,690,047 |
| Buccaneers (TB) | 54 / 75 | 21 | $273,771,405 |
| Titans (TEN) | 61 / 79 | 18 | $254,856,741 |
| Commanders (WAS) | 63 / 80 | 17 | $260,900,388 |

No club has verified cutoff membership, complete retained/reserve liabilities and
adjustments, or certified cap room. No final hybrid or new Deck test package was
created by this audit. MyNFL1, game files and runtime controls are unchanged;
the scheduled task remains off. No inference or native rebuild was needed.

## Sources and reproducibility

[September 10 nflverse archive](https://github.com/nflverse/nflverse-data-archives/releases/tag/archive-2026-09-10):

- `roster_weekly_2026.rds`, SHA256
  `3aaaafdec8e3f407a08676cf1744a80f8cd0c3958e7f4ea136db319aa53744a4`.
- `historical_contracts.rds`, SHA256
  `80e8f98e8b43ea2f1e35e39e956f65d2cb3da628f1db54fc6070932df84635e3`.

The extracted active-contract subset also has a pinned hash in the private
`week1-roster-v1/source-research/league-contract-coverage.json` receipt. Inputs and
player-level results are private; no game assets or save data are published.
Source capture dates do not guarantee all included fields were current; the
Slayton roster/transaction disagreement remains an example requiring correction.
Detailed source limits and FA investigation: [PRESEASON_OPENING.md](PRESEASON_OPENING.md).

Validation: 24 focused league/contract/identity/portrait/transaction tests pass.
The preceding unchanged financial/runtime baseline passed 1,119 tests. This
source-only batch did not repeat the full runtime suite or claim game execution.
