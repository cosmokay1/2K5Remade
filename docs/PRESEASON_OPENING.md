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


## Live isolated trial (October 18)

### Current direction: preserve SOFTDRINK presentation in a hybrid

The user confirmed the player images are correct in SOFTDRINK and requested a
hybrid rather than replacing its roster wholesale. The direct-import acceptance
request is superseded. Normal Steam routing was restored exactly (SHA-256
cc04c51a70ae38c5faa4ba47bc8815acd88323d88b6a090e9ee59c02fa9467db);
this changes the next launch, not the running game or saves.

`tools/plan_hybrid_roster.py` is a read-only comparison, not a merge. Preserve native
player slots, portrait IDs and appearance data. It matches exact case-insensitive
names plus decoded DOB, rejecting ambiguous/unknown/conflicting identities. The
DOB byte's low nibble is not part of the birth date; comparing raw bytes would
incorrectly reject appearance differences. Native unassigned records are searched
when their names are readable; unreadable records remain explicitly unresolved.
No PS2 financial words or ratings are copied and no hybrid save is produced.

Pinned inputs yield1380 matched preseason members and527 unresolved:435 absent
from the readable native bank,84 DOB conflicts and8 ambiguous names. Giants have
43/60 matches. A match is provisional cross-roster evidence, not a permanent ID
or proof of portrait content. Unresolved players need verified identity/asset
mapping before generating a hybrid. Private report: hybrid-plan.json in the
existing local trial directory. MyNFL1 and the game binaries remain untouched.

### Earlier direct-import investigation

Prepared `preseason-roster-v1` on the Deck with the live known-good EXE
`9e30ec9...`, independently copied settings and no franchise/AI addon/ledger.
Immutable game assets and the existing SOFTDRINK pack were shared to avoid
another full installation. All 19 installed v0.6 pack-file hashes match the
pinned overlay receipt. The test launch log confirms actual v0.6 overlay dispatch.
Normal Steam routing was restored immediately after the isolated process started.
All 211 original main-save files were verified byte-identical after PRECAP saved.
The scheduled task remains PAUSED.

The PC importer accepted PRE26, but that did not prove title-level loading.
The user's saved `precap` is 720,044 bytes, SHA-256
`9a1529ffd1bb3a1eec3f6ac4c65451d2ec50ba76e97e31d679f419f16d64561a`,
and its PC signature verifies. Its 2,619-record player bank and 53 Giants players
are the SOFTDRINK disc baseline, not the candidate's 2,479-record bank and 60
Giants players. The native schedules reconcile for all 32 clubs; Giants saved
cap/payroll/room are $301.2M/$211.984M/$89.216M. This is mathematical agreement
with that default save, not proof of accurate modern opening obligations.
Do not issue an identity registry or financial import for the candidate from it.

PREOFF TYPE=TMM retry was reported damaged. A proposed settings-prefix
explanation was disproved by the user's actual game-created NATIVE reference:
it is a 593,984-byte bare ROST with TYPE ROS, SHA-256
`445161c0d7a0da4a9bd55f91c6eccf0547f8846f4a74bc4540b5fadd6577399d`.
The TMM sizing routines describe a different save path and were insufficient
proof for this roster type. That prefix conversion was withdrawn. PREOK's
untested queued prefix package was preserved outside the importer, not validated
or installed as a successful roster. Never reuse that explanation as a fix.

The current trial helper instead requires the actual signed native ROS container,
preserves its container ID, TYPE, SaveMeta bytes and manifest exactly, and replaces
only the ROST payload and its HMAC. The source roster bytes remain unchanged.
The isolated trial uses the native display name NATIVE and physical container
12430F5113A1; the user's original game-created NATIVE remains in the main profile.
Failed PRE26/PREOFF candidates are preserved outside the test profile's active
save list. This is a controlled container/metadata comparison, not a claim that
metadata was conclusively the root cause. The source's header +8 is 2 while the
native reference is 0; that field must not be blindly zeroed or called a platform
marker without following its additional-data handling.

A game restart returned the user to the normal profile because initial temporary
Steam routing had already been restored. MyNFL1's physical and logical payloads
were checked again and remain identical to their pre-test hashes. Subsequent
trial routing is retained only for the authorized isolated test, with the exact
normal wrapper backed up for restoration afterward. User saves, game EXE/addon,
AI controls and inference budgets are not changed by the roster trial.

Until the preserved-container trial actually loads and yields the expected fresh
franchise plus save/reload evidence, compatibility remains unverified. Do not
transplant an unrelated franchise's player-history tail or claim PRECAP proves
that the candidate roster was used.

New source-only helpers: `tools/inspect_roster_save.py`,
`tools/prepare_roster_trial.py`, and `tools/reconcile_roster_trial.py`.
They report source/target roster identity and terms separately from native payroll,
explicitly retain unsupported schedules, and never authorize financial writes.
The audit reader reports auxiliary name pointers; it does not broaden the strict
production identity reader. The candidate has two such name pointers for Odell
Beckham. One Saints contract (Barion Brown) has remaining years greater than its
zero original term. Its preserved legacy amounts also cannot be interpreted as
SOFTDRINK-scaled real contracts: Giants raw charges total $85.903M, or $343.612M
at four-to-one. A successful load will still need a modern source reconciliation.

Current nflverse contract coverage has unambiguous name candidates for 59 of 60
Giants, with Dru Phillips needing an independently verified name mapping. That
is not identity or preseason schedule proof. Full player season-history repeats
across contract rows, so the read-only preview deduplicates it instead of summing
contract copies. Nothing from the October snapshot has been imported.
Private evidence: `.local-runtime/preseason-roster-v1/` and
`.local-runtime/preseason-roster-v2/`; fixtures contain authored bytes only.

The targeted roster fixtures cover exact container metadata, HMAC/pin rejection,
non-overwrite, malformed references and read-only cap audits. Hybrid fixtures
add decoded DOB, native photo preservation, ambiguity, unknown/missing identity
and unassigned-bank matching. No game EXE/addon rebuilt or replaced for this batch.
Final full working-tree regression:1,099 Python tests pass in44.047 seconds,
including the existing credential edits that are excluded from this source batch.
