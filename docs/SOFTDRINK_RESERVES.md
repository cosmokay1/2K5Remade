# Stock SOFTDRINK reserve correction

Scope: official SOFTDRINK 2K28 v0.6.1, with its existing player data and runtime.
No franchise addon, hybrid roster, external ratings/contracts or new players.
Credit: SOFTDRINKTV/cruuz and Mod Studio's original RC112 roster/squad codec.
This correction is unofficial; the original release remains intact.

The October14 recipe omits 336 reserve-source entries because the disc roster
has no native franchise IR seed. Of those, 81 have complete existing player
records, with name, birth date, stable primary index and source club. This
includes Jaxson Dart and Brian Burns. The other 255 have no authored reserve
record in that recipe and no normalized full-name match in either stock player
pool. They are reported, not synthesized or confused with unrelated records.

`tools/restore_softdrink_reserves.py` restores those 81 to existing reserve-squad
lists across all32 NFL clubs. This uses SOFTDRINK's squad storage, **not native
injured reserve**: no injury diagnosis, return date or IR rules are invented.
Active lineups/depth charts, all player bytes (including ratings, contracts,
portraits and history pointers), free agents and alumni pointers stay intact.
Physical65-pointer capacity and the existing12-reserve limit are enforced.
An active promotion still needs an available active roster place under stock rules.

Only257 bytes change within the593792-byte default ROST resource. The candidate
overlay replaces that resource at vc_53450030/0 offset3815424. Restoring its stock
bytes reproduces the official194172928-byte volume SHA256 exactly; all other
overlay tables/literals and the original game image remain unchanged.
The original pack is retained; corrected overlay/literal files are separate.
Unchanged assets are linked to the official installation to avoid duplicating it.

Build with the user's private release and its pinned official codec:

```sh
python3 tools/restore_softdrink_reserves.py \
  --codec /path/to/rc112/codec \
  --patch /path/to/SOFTDRINK-2K28-v0.6.1.2k5patch \
  --roster /path/to/verified/default-roster-resource.bin \
  --pack /path/to/installed/official-pack \
  --output /path/to/new/correction
```

Output contains corrected overlay/literal files, roster bytes and a detailed
receipt. It does not install, activate, alter saves or include the unchanged
pack assets. Use the pinned v0.6.1 artifacts; modified sources are rejected.
No retail assets or codec copies are distributed with this tool.

Validation October21: four portable sparse-overlay tests plus three private
real-format tests; identity mismatch, duplicate identities and changed stock
inputs refuse. Full-volume recovery matches the original hash. On Deck, the
existing native overlay reader matches all corrected roster bytes at read sizes
593792/65536/32768/4096/2048/311. Ten original reserve-runtime code caves match
the stock executable; no executable rebuild or runtime patch is included.

Candidate staged at `native-05ac4e9/softdrink-reserve-correction-v1` on the Deck.
Not activated while the stock game is running. Scheduled task stays off.
Existing franchises retain their serialized roster: this correction targets
the default roster used by a **fresh franchise**, not existing save migration.
After normal exit, activate once and verify a fresh franchise's reserve lists
for Dart/Burns and another club, then save/reload. Those actual-game acceptance
steps remain unverified; structural/native-reader checks do not prove them.
