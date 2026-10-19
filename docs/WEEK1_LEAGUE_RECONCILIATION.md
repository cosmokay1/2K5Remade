# Week 1 league reconciliation

The target is all 32 teams and one shared, historically accurate free-agent pool.
Giants work is an investigation case, not a delivery shortcut. Every club needs
verified membership, annual contracts, reserve/practice-squad obligations,
retained/dead charges and club cap adjustments before the league is certified.
A complete set of roster schedules alone does not establish a full cap book.

## Verified source coverage — October 18, 2026

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
