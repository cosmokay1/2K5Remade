# Stock SOFTDRINK playable roster correction

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

The first correction restored reserve ownership only. The user could not see
those players on playable rosters and explicitly requested full playability.
That reserve-only v1 is superseded by active-roster v2.

`tools/restore_softdrink_reserves.py` appends the 81 existing players to their
32 clubs' active lists. Every previous active player remains in the same order;
existing reserve identities/order, all player bytes (ratings, contracts,
portraits, history and depth fields), free agents and alumni pointers stay intact.
Active counts are 54–58 (Giants56), within the existing65 physical pointers
including reserves. No player is given a new injury or hidden reserve status.
This does not force starters: depth-chart choices and normal cutdowns still
apply, and stock accounting must include the added players' existing contracts.
No cap credits, contract edits or rule bypass is included.

Only397 bytes change within the593792-byte default ROST resource. The candidate
replaces that resource at vc_53450030/0 offset3815424. Reversing those roster
bytes reproduces the official194172928-byte volume SHA256 exactly; all other
overlay tables/literals and the game image remain unchanged. Original pack
retained; unchanged assets are linked to avoid duplicating the installation.

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
receipt. It does not install, activate, alter saves or include unchanged assets.
Use pinned v0.6.1 artifacts; modified sources are rejected. No retail assets or
codec copies are distributed with this tool.

Validation October21: four portable sparse-overlay tests plus three private
real-format tests; identity mismatch, duplicate identities and changed stock
inputs refuse. All81 additions have eligible NFL-player flags. Tests prove
active membership (including Dart/Burns), preservation of every original player
record/member, existing reserves, all-star memberships and physical capacity.
Full-volume recovery matches the original hash. Deck native reader matches the
corrected bytes at sizes593792/65536/32768/4096/2048/311. No executable rebuild.

Active v2 installed at `native-05ac4e9/softdrink-active-correction-v2` on the Deck
after confirmed normal exit. No addon or EXE change. Installer recorded433 unique
payload hashes and verified457 protected files retain their inode/size/timestamps;
large virtual disks were not repeatedly hashed. Same Steam entry relaunched game
process4252. Actual roster visibility/playability still needs user confirmation.
Scheduled task stays off. This changes defaults for a FRESH franchise;
existing saves serialize their own rosters and are not silently migrated.
Verify Dart/Burns on the playable roster, another club, depth-chart selection
and a fresh save/reload before claiming actual-game acceptance. Those checks
remain unverified; native-reader checks alone do not prove playability.
