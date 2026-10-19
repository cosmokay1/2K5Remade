# MyNFL1 preseason opening book

The user requires the roster and liabilities at the beginning of preseason.
Later cuts, trades, extensions and injured-reserve placements must not be
backdated into that book. The read-only audit currently uses August 6, 2026,
the league's first preseason game, as its explicit cutoff. This is an audit
boundary, not a claim that a dated opening roster has been recovered.

## Verified saved amounts

The cached MyNFL1 snapshot has a $301,200,000 league cap and $211,984,000 of
roster charges in the verified four-to-one scale. Its displayed $89,216,000 room
is therefore a roster-only figure. All saved first-year accumulators are zero;
that does not establish that modern retained/non-roster liabilities are zero.
The dated contract adapter matches 42 Giants contracts and leaves 11 unresolved.

MyNFL1 is not itself an opening-preseason roster: it contains J.J. McCarthy on
the Giants. The club announced that acquisition in late September. The available
September 24 contract audit and October 18 public cap snapshot cannot certify
an early-August opening book. The public weekly roster file inspected here
covers regular-season weeks 1–6, not preseason membership.

The current OTC dead-money list also includes a later Josh Tupou cut. Its
reported total differs from the sum of its individually displayed rows; that
residual cannot be assigned to invented players or assumed to exist before
preseason. None of these October charges, injury statuses or current roster
changes has been imported into MyNFL1 or its sidecar database.

## Concrete remaining input

A dated preseason roster plus the corresponding active contracts, retained/dead
charges and non-roster obligations are required. Reconstructing from transactions
also needs the contract terms that existed before later extensions/restructures;
current season-history rows alone cannot establish them. Do not subtract today's
dead money from the game's room or force an arbitrary cap reduction.

`python3 -m tools.audit_preseason_opening SAVE BINDINGS AUDIT --team Giants
--cutoff 2026-08-06` reports the saved amounts and outstanding coverage. It writes
nothing and never marks missing liabilities as known zero. Private evidence is
in `.local-runtime/opening-liabilities-v1/preseason-readiness.json`.

Sources:

- [NFL preseason schedule](https://operations.nfl.com/media/urolxkdj/05-14-26-preseason-schedule.pdf)
- [Giants McCarthy announcement](https://www.giants.com/news/j-j-mccarthy-trade-details-minnesota-vikings-quarterback-2027-nfl-draft-michigan-wolverines)
- [Current Giants cap table](https://overthecap.com/salary-cap/new-york-giants)
- [Contract snapshot release](https://github.com/nflverse/nflverse-data/releases/tag/contracts)
- [Contract field definitions](https://nflreadr.nflverse.com/articles/dictionary_contracts.html)

## Combined test candidate

The follow-on code supports successive agreements for one club, including a
second player, same-year calendar progress, accumulated bonus layers, earned
base salary, restart and latest-cap restoration. It rejects an unrecorded payroll
correction, stale saves, changed terms and a changed save during context reading.
A pending later offer must not disable restoration of the previous settled cap.
Cross-club amendment chains and season migration remain unsupported.

The native protocol validates the prior salary/bonus basis and conservative
payroll quantization; the Current Contract table uses the amended charges.
The owner's local policy remains signing-disabled in the staged private patch.
Fixtures and compilation do not certify a real Deck signing or a completed
preseason opening book. Do not install an older staged diagnostic or replace
loaded binaries. Keep the scheduled task off.

## Downloadable roster direction

The user now prefers a downloadable 2026 preseason roster over reconstructing
MyNFL1's later roster. Keep MyNFL1 untouched and establish a fresh, separate
franchise from the selected roster; do not replace SOFTDRINK gameplay blindly.

LostsouL's [roster index](https://github.com/lostsoul63b/NFL-Ratings) includes
NFL2026Camp, but the same download link exists in its
[August 11, 2025 revision](https://github.com/lostsoul63b/NFL-Ratings/blob/99fc30f7a06f/README.md).
It therefore cannot establish a 2026 preseason baseline from its name.
Its NFL2027Week1 archive was uploaded September 23, 2026 and is not an opening
preseason source either. Neither archive was downloaded for this investigation.

The better candidate is the roster already selectively obtained from the
[official NFL 2K27 distribution](https://www.nfl2kmod.com/nfl-2k), whose release
page says June 29, 2026. Read-only extraction of only its roster save from the
cached PS2 card found matching June 29 creation/modification metadata, 1,718
team memberships, and 60 Giants players. Giants include Dart and Winston and
exclude McCarthy. Save timestamps alone do not certify every historical
transaction, contract, injury status or retained liability.

The extracted roster is 593,984 bytes, SHA-256
`33bc2da5c3bb3d23ad103e308853e9d4e920b25931cb2e36cd24bb3c0520053e`. Private preview/evidence is
`.local-runtime/opening-liabilities-v1/2k27-roster-preview.json`.
Its original PS2 roster still needs isolated Xbox packaging/import and fresh-
franchise/load/save verification. The existing save converter supports roster
conversion; this does not certify the particular candidate. Credit the NFL 2K
Mod Team and BAD-AL's conversion tooling. No ISO/BIOS, full replacement mod,
main-save change or live installation was obtained/performed in this search.

## Batch validation

Full Python regression: 1,084 tests pass (39.415 seconds). Seven isolated Windows
checks pass, including the negotiation screen model, plus ten actual Python
bridge response cases through the Windows native validator. The final paired
EXE/addon passes isolated game `--validate`. An old authored protocol fixture
initially lacked accumulator fields required by the new check; its explicit
zero-valued observation was corrected and the Windows checks rerun.
This is not boot, interactive signing, financial reconciliation or save/reload
acceptance. Final receipts are in private `follow-on-v1`; live install is false.
