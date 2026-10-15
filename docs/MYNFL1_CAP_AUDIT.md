# MyNFL1 Giants cap audit — October 14, 2026

The roughly $89M available room agrees with the contracts in this save. It is
not evidence that the complete real-world 2026 Giants cap position was imported.
The league ceiling is already modern; raising it would create additional room.

## Inputs and year

User identifies the Giants and the saved franchise MyNFL1. Read-only local copy:
720044 bytes, SHA256
4c8c31b4f400e25175223163a948e126cb83d10aa4bb98979a564ef287761ec3.
SOFTDRINK v0.6 XBE SHA256
f67e6fc1cb76c9ea1f1ad504e4a6491ff126483d66a9da8ddb92950bbaf740ba.
Source hash was rechecked after analysis and still matches; TYPE is FXG and its
runtime zero-key HMAC-SHA1 signature verifies. No save, contract, cap, control or
running game was modified for this audit.

The scheduled-game year byte is26. The original scheduler index is0 (first season),
which the retail calendar reader labels2004; that label is not an authoritative
MyNFL year. The installed pack's authored 2026 economy and roster establish the
intended opening season. The [NFL's 2026 league ceiling is $301.2M](https://operations.nfl.com/calendar-events/nfl-free-agency/nfl-salary-cap).

## Money scale and reconciliation

The pinned authoring source at e19384123c23a3601949dda67c9a3ab754d65fd6 explicitly
uses four real dollars per game dollar. Its six replacement economy code windows
match the actual installed pack XBE byte-for-byte, including the money formatter.
The executable also initializes the saved cap to75300 game thousands. This is
verified code and data, not a multiplier inferred only from a coincidental total.

Sources: [economy implementation](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/mod_editor/core/nfl2k5_franchise_economy.py),
[generated replacement code](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/mod_editor/core/nfl2k5_franchise_economy_code.py).

| Measure | Internal game dollars | Real-dollar display scale |
|---|---:|---:|
| League cap | $75,300,000 | $301,200,000 |
| Giants roster charges | $52,996,000 | $211,984,000 |
| Available room | $22,304,000 | $89,216,000 |

All53 Giants contracts reconstruct the stored roster payroll exactly: $0 difference.
All32 teams' reconstructed roster payrolls also match. The Giants' first-year
adjustment flag is1, with a zero accumulator, so that branch adds no first-year
charge. Display truncation can show approximately $89.21M for $89.216M.

The save declares2619 player records. The former reader's fixed2317-slot bound
and required first settings word4 rejected this valid save. The strict reader
now checks the serialized ROST headers, section size, declared player count,
base and adjoining-table boundary instead. It reads2070 memberships including377
free agents (highest free-agent slot2463), checks every referenced record/name,
and reproduces all32 payroll totals using the supported schedule math for codes0..7.
Authored expanded-bank and corrupt-boundary regressions pass. No header was changed
in the audited payload. An explicit hash-pinned opening profile now binds the intended2026 season
and4:1 export scale; the retail2004 observation is preserved. Future calendar
migration, active franchise selection and complete obligations import remain open.

## Accuracy beyond arithmetic

SOFTDRINK fits annual cap schedules into the game's limited contract fields.
The [author's fitter](https://github.com/cruuz/2k-football-mod-tools/blob/e19384123c23a3601949dda67c9a3ab754d65fd6/tools/franchise_economy/contracts.py)
explicitly distinguishes encoded remaining cap liability from original headline
contract value, actual cash and guarantees. Our integration must preserve that
distinction and the four-to-one scale. `LegacyContract` now preserves an explicit
`game_dollar_scale=4` alongside the raw fitted fields and scales reconstructed
charges after guest truncation. Default retail records serialize identically,
preserving existing checkpoint hashes. This does not infer cash or guarantees,
choose a pack profile automatically, or authorize calendar/lifecycle conversion.
Read-only validation against MyNFL1 reproduces all1693 active schedules across32
clubs at display scale; Giants total211984000. No ledger was created from the save.

Selected opening-year comparisons:

| Player | MyNFL1 charge, display scale | Published 2026 charge |
|---|---:|---:|
| Brian Burns | $21,400,000 | $21,383,333 |
| Andrew Thomas | $13,048,000 | $13,031,956 |
| Kayvon Thibodeaux | $14,760,000 | $14,751,000 |
| Arvell Reese | $8,324,000 | $8,696,557 |
| Chauncey Golston | $6,920,000 | $5,201,103 |
| J.J. McCarthy | $5,956,000 | $895,833 |

All53 saved players matched the [current 2026 Giants reference](https://overthecap.com/salary-cap/new-york-giants);
45 charges are within $20,000. The reference includes different roster/status
and dated contract circumstances, so a difference is not automatically a fitter
bug. Josh Tupou, for example, is on its practice squad.

| Reference reconciliation | Dollars |
|---|---:|
| Charges for the same53 identities | $204,251,252 |
| Additional27 active/reserve/practice-squad identities | $42,392,016 |
| Released-player dead money | $43,691,218 |
| Total published cap liabilities | $290,334,486 |
| Implied adjusted cap, from published liabilities plus room | $300,195,334 |
| Published available room | $9,860,848 |

The components sum exactly. This is a comparison with today's reference, not a
proposal to overwrite the frozen roster. Do not add the whole IR total: Burns,
Golston and Dart are already charged in-game. The implied cap adjustment needs
its own provenance before import.

Conclusion: the base cap and saved roster arithmetic reconcile. Full real-world
2026 cap accuracy is not established. The schema-checked modded save reader is verified. Next work is a dated,
lossless obligations import covering active/reserve players,
released-player debt, adjustments and supported contract details. Preserve
existing fitted deals until an explicit reconciled conversion is ready.
