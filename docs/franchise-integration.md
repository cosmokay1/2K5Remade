# Franchise negotiation and cap integration

## Current fork source audit, October 13, 2026

The actual game target is defined by root `config/game.cmake` and entered from
root `src/main.c`. Before the host-adapter work, neither target linkage nor main
contained a franchise client source, include, lifecycle call or transaction hook.
`native/franchise_bridge` builds a standalone protocol test and Windows pipe
fixture; passing those fixtures does not mean the game uses the financial engine.
The standard Build check explicitly configures `NFL2K5_BUILD_GAME=OFF`.

Generated guest code **is present**: 38 tracked files under `src/recomp/gen`.
The build-generated function-range source, Windows dependencies, retail XBE and
controlled saves are separate inputs. `original/` currently contains only its
README. Existing guest roster/overall accessors and season-limit patches do not
establish a salary field map, contract calling convention or financial hook.

A small C-compatible adapter now wraps the existing strict
Win32 PipeClient, with an explicit service mode, bounded response retrieval and
owned child lifetime. The added asset-free plain-C caller validates that ABI and
transport; its Windows execution passed in run 38503080961. Root lifecycle
source and restricted handle inheritance passed Windows run 38504026771.
It does not read or write guest
rosters, commit game contracts, supply unverified addresses or create a franchise
UI. Verified guest transaction callbacks
remain required work. A real transaction hook may only follow the controlled
save experiments below and runtime readback/reconciliation.

The nested `remade/` and `save-tools/` checkouts in the original audit are historical
reference copies. Current root game integration changes belong in root `src/`,
`config/` and `tools/`; they must not accidentally target the nested copy.

## Historical source audit, October 13, 2026

Inspected Remade revision `579c72b58153c37ceb9cf20502f9ac81a3de6f4e`
and BAD-AL save converter revision `e3afeece61896380a95e506ab43ae1abda0ae8a5`.
The checkouts are in `remade/` and `save-tools/`.

Remade runs generated Xbox guest code with native runtime bridges. No named
salary-cap, contract, or negotiation API was found in the public source.
This does not establish that the original game uses decision tables or identify
a defect in its cap accounting. Neither has been measured yet.

Relevant integration points:

- `remade/tools/apply-gen-patches.py`: existing address-anchored guest patches,
  reapplied during builds. A transaction hook belongs here only after its guest
  address and calling convention are verified.
- `remade/src/nfl2k5_save_library.cpp` and `remade/docs/SAVE-LIBRARY.md`: Xbox
  working saves and readable mirrors synchronize every 2.5 seconds. Editing a
  live mirror is not an authoritative transaction interface.
- `save-tools/lib/gamesave_tool.dart` and `GAMESAVE_SECTIONS.md`: team membership,
  player records, and performance data are mapped. Salary, bonus, guarantees,
  cap totals, and contract durations are not exposed by this converter.
- `remade/tools/xbe_peek.py`: existing raw guest-image inspection utility.

No game binary or franchise save is present in these public checkouts. The
Windows runtime cannot be verified in this macOS workspace.

## First experiment: discover and verify accounting

Use copies of one franchise at one fixed date, with the game closed when copying
saves. Preserve SAVEGAME.DAT and its signing/metadata companions together.

1. Save a baseline and record the displayed cap, cap room, roster, and selected
   player's full contract terms.
2. Save again without a transaction. Compare this control pair to identify
   ordinary save bookkeeping changes.
3. Restore the baseline. Complete exactly one signing with recorded terms and
   save again. Do not advance a week or make another roster move.
4. Repeat independently for release, trade, and re-signing. Vary one contract
   term at a time where the UI permits it.
5. Compare raw payloads with:
   `python3 tools/save_diff.py before/SAVEGAME.DAT after/SAVEGAME.DAT`.
   Add `--control-after control/SAVEGAME.DAT` when the no-transaction control
   was saved from the same restored baseline. The JSON retains every transaction
   span and separately reports changes at offsets unchanged in that control and
   changes overlapping control bookkeeping. Both groups include exact bytes and
   hashes; overlap is never discarded. A single control does not establish that
   an offset is always stable or identify a contract field. Restore the exact
   baseline for each experiment; unrelated franchise dates/rosters are invalid
   comparisons even if raw lengths happen to match.
6. Trace candidate fields into generated guest functions, then verify against
   displayed accounting and a save/load round trip. Include CPU-controlled
   transactions and offseason advancement in the hook audit.

## Intended negotiation boundary

Personality, performance, relationships, and remembered promises inform LLM
offers, counteroffers, and willingness to accept. The LLM never supplies an
authoritative cap total or writes game memory directly.

A validated transaction must calculate the full team's cap usage from a
verified ledger, including existing obligations and any applicable release or
trade charges. Apply offers against the latest state; reject stale proposals
and duplicate commits. Commit the agreement and its narrative consequences
together. A rejected offer changes no contract or roster data.

Money uses integer units with verified conversion to the game's representation.
Cap equality must be allowed and a one-unit excess rejected. Tests must cover
bonus allocation, releases, trades, duplicate requests, competing offers, and
season advancement before game writes are enabled.

The user selected modern NFL-style contracts, including the rookie wage scale.
The ruleset therefore needs an authoritative external ledger if the native
contract representation cannot express those obligations. Modern guarantees,
bonus proration, cap growth, and post-June-1 treatment must not be assumed to
exist in the native game. Runtime enforcement must cover every roster transaction
and season transition; merely displaying external cap room cannot enforce it.

Future commitments should be visible in negotiations. Today's binding cap
limit and any policy reserving space for future rosters are separate checks;
do not silently prohibit a contract using invented future cap assumptions.

## Next required inputs

The user currently has no game binary or save. Offline engine development can
continue with synthetic data. Connecting it to the game still requires an
extracted Xbox `default.xbe`, a raw franchise save with its companion files, and
paired saves from the controlled experiment. These allow actual contract-field
mapping and cap bug reproduction. Until then, the implementation is an offline
prototype, not an installed franchise modification.


## C host adapter

`native/franchise_bridge/host_client.h` exposes an opaque, single-owner-thread C
handle around the C++ PipeClient. The Windows `franchise_host_client` static
library and `franchise_c_host_check` plain-C executable exercise the same adapter.
Explicit Python/database paths and fixture/runtime modes are required. The
existing child inherits the caller's working directory; the franchise Python
package must be importable there. This is not yet an installed game launcher.

Submission is bounded to the existing 4095-byte client frame. A pending or unread
reply returns BUSY; readiness never waits. Taking a ready reply into a short
buffer preserves it and reports the required size including the terminator.
Exceptions produce static C statuses. AI negotiation requires a validated
successful hello; failed hello, ai_disabled and transport failures clear that
local grant, while the server checks fresh access for every AI request. Manual
and read operations remain independently available.

Destruction closes the owned kill-on-close job before joining the worker, keeping
the parent's pipe handles alive until the worker finishes. This releases a write
blocked by a peer that stops reading. It belongs outside render-time callbacks.
The Windows stalled-peer CTest fills stdin and checks destruction and child exit;
the strengthened write-stall fixture passed Windows CI in run 38503835760.
The inherited-handle exclusion check also passed Windows run 38504026771. The response timeout still starts after
the synchronous write, so it is not an end-to-end request timeout.
Real game-host lifecycle and performance tests remain
necessary before linking/enabling this transport in an integrated runtime.

The synthetic C caller tests early AI denial, explicit modes, null arguments,
frame bounds, BUSY, nonblocking polling and short-buffer retrieval. The Python
Windows fixture checks handshake, preview, manual signing, context, stale preview
and identical historical signing across two client processes. Portable C-header
syntax and the exact JSON sequence passed locally; that is not Windows execution
or guest game/save validation.

## Opt-in root host lifecycle

Configure the real game target with NFL2K5_FRANCHISE_CLIENT=ON to link the C
transport and src/nfl2k5_franchise_host.c. The default remains OFF. Runtime
activation requires NFL2K5_FRANCHISE_PROVIDER=vertex,
NFL2K5_FRANCHISE_PYTHON and NFL2K5_FRANCHISE_DATABASE. No fixture fallback
is allowed in the game host. Missing or invalid opted-in configuration stops
startup before guest entry. Without the provider variable no sidecar starts.

Startup owns the sidecar immediately before guest entry; normal guest return,
crash handling and normal process exit clean it up. Each child inherits only
its own stdin/stdout and duplicated stderr (NUL if unavailable). No hello or
AI request is sent automatically. This is lifecycle wiring only: verified
franchise callbacks still need to consume the handshake, reconcile the ledger
and guest state, and complete verified save/readback transactions. The shared
C lifecycle source is compiled by the asset-free Windows fixture. Actual root
game build and execution remain unverified.

## Calendar-aware contract inspection

contract_context accepts explicit context_format=calendar_v1. This requests
format2 current calendar accounting alongside a separately labeled economic
archive. Native validation binds the requested generation/team, original terms
and bonus layers, exact elapsed-year cursor/charges, ownership and sourced fully
settled expiry. Legacy context stays unchanged before rollover and rejects
afterward rather than displaying archived terms as current. This read is available
with AI disabled and never invokes the model or changes finances.

The native synthetic fixture reads a surviving and expired generation twice
across owned sidecar process restarts. Windows run 38507267705 passed at 57c0d4c;
this is contract-inspection transport evidence.
This is engine inspection, not verified guest save or in-game interface behavior.

player_context also accepts explicit context_format=calendar_v1. Its personality,
relationships, promises and negotiation history come from the same store snapshot
as a nested calendar_contract_context envelope. Legacy contract_accounting is null
in this format. The nested envelope preserves economic archives separately from
current calendar status, elapsed years, charges and ownership. Classified players
with no held agreement receive a null nested context. Legacy requests retain
their existing pre-rollover behavior and reject stale post-rollover accounting.

The native validator binds nested team/player/revision to the requested player
snapshot and validates the complete calendar agreement. Portable C++ checks have
accepted actual Python-generated active, expired and never-held snapshots. The
extended Windows pipe scenario adds saved personality and compares complete
snapshots across two sidecar launches without changing the database; execution
for that extension passed in Windows run 38509950333 on revision 11cac7d.

`calendar_v2` explicitly requests format3 inspection, adding `release_calendar`
to the same archive/current-state envelope. Calendar releases report their sourced
release year and original salary-year cursor separately from archived economic
terms. Allocated prior base payments remain owed/paid; cancelled future base is
excluded while guarantees and bonus layers remain liabilities. Native validation
checks these component ceilings, settled prior base and unpaid guarantees. Other
agreements carry a null release calendar. `calendar_v1` continues rejecting these
new release archives instead of silently changing its format.

Both contract and player inspection support this version without inference or
financial writes. Actual Python replies passed the portable C++ validator. A new
Windows fixture reads released/expired agreements and personalities across two
sidecar launches; Windows run 38513985171 passed at ee92067. Inspection alone grants no release
authority and does not establish guest gameplay/save integration.

Manual release now accepts explicit `calendar_format=calendar_v1` plus
`generation_id` to select the calendar-aware Store transaction. Legacy requests
keep their existing guards. Full and target_v1 compact receipts retain format2,
agreement ID and league year; native checks bind these facts, revision, allocated
cash and prior salary settlement. The connection/deadline and encoded receipt
capacity are checked within the atomic transaction before commit. AI may be off
for this manual action. The synthetic Windows fixture now performs and retries
the transaction across processes, then reads its archives and personality;
execution passed Windows run 38514505285 at dcea1b2. Actual guest writes and
in-game release interaction remain unimplemented.

The synthetic Windows check also runs the complete restructuring and assignment
histories through a fixture-only native stdin request mode. It executes full and
compact release receipts, agreement/player reads, saved personality and retry
across two sidecar launches, then verifies later payroll/rollover/reopen. Local
Python fixture orchestration passes; Windows execution passed run 38515051781
at 642d533. This mode belongs only to the smoke checker, not the game client API.

`calendar_v3` explicitly requests format4 inspection, adding `trade_calendar` to
format3's envelope. Sourced outgoing trade year/cursor remains separate from the
original economic contract. Seller cash includes settled bonuses and earned prior
base; transferred future base/guarantees are zero seller liabilities. Native checks
bind the marker to assigned status/year and reconcile exact component ceilings,
full allocated settlement and zero remaining guarantees. Null markers use the
legacy economic cursor, so removing a later-trade marker cannot bypass cash
reconciliation. Other agreements use a null trade calendar and preserve release
inspection. Both contract/player requests are read-only and available with AI off.
Legacy v1/v2 Store requests reject new calendar assignment archives.

Portable native fixtures and eight actual Python seller/buyer contract/player
replies across rollover passed C++ validation. Windows pipe fixtures now compare
these snapshots and saved personalities across two processes in two years; their
inspection execution passed Windows run 38516814959 at 481027c. Inspection alone
grants no trade-write authority and does not prove actual guest interaction.

Manual trades now accept explicit `calendar_format=calendar_v1` with canonical
seller and nullable prior-buyer generation IDs. This selects the atomic calendar
Store transaction; legacy requests retain their guards. Full/compact receipts
carry typed format2, matching calendar format/year and both participant identities.
Native validation checks revision/ownership, original/retained/transferred cash
conservation, allocated full inventories or compact summaries, and exact remaining
buyer salaries/guarantees with no transferred bonus layers. Seller bonus and earned
prior base must be fully settled; transferred future base is not a seller liability.
Receipt size and final connection/deadline checks precede commit. Manual trades
work with AI off without inference.

Windows fixtures now execute full/compact calendar trades twice across sidecar
processes, then inspect both parties through rollover. The new transaction fixture
passed Windows run 38517734890 at 8ea3682. Prior inspection passed run 38516814959 at 481027c.
Actual guest trade interaction and save writes remain unimplemented.


## First franchise screen trace — October14,2026

Source inspection identifies existing FSM probes, not an established financial
hook. tools/apply-gen-patches.py injects DIAG_FSMPUSH in sub_0006E390 and a
matching pop. Root src/main.c now logs those existing events only when
NFL2K5_TRACE_FRANCHISE=1, with a256-event process-lifetime ceiling. The trace
contains sequence, push/pop, object and descriptor addresses; it performs no
guest memory reads/writes and starts no AI requests. It is silent by default.

Once the legal game runs, enable this environment flag for a fresh session and
navigate franchise roster -> selected player -> contract -> back. Record the
visible screen/player and correlate the logged descriptors across repetitions.
Use a separate fresh session for a different player. A descriptor is only a
candidate until it reproduces on the real franchise screens; none is hardcoded
as a signing hook. Disable the flag after collecting this bounded trace.

The pregame PLAYERCARD_PROBE in sub_002604D0 obtains a script context and card
kind at+0x48. The single-player fact-card code in
src/nfl2k5_presentation.cpp validates a player pointer against away/home roster
arrays, but only in fresh_pregame state. Neither proves a persistent franchise
player ID, club ownership, contract fields or negotiation-menu context. Do not
attach negotiation to that pregame probe or reuse its hidden-rating ranking.

The SIM_PICK_EMPTY patch in sub_00204930 selects an active collection entry and
protects a modulo-by-zero case. Its caller sub_0020B670 writes a two-word tuple
whose business meaning is unproven. It is not an evidenced contract commit or
cap calculation. Existing source therefore does not justify a financial hook.

Next evidence: correlate selected records across franchise navigation and
save/reload, inspect the controlled signing save differences, then trace the
proven accept/commit caller before enabling writes. Initial integration should
provide selected-player context/preview before committing a contract.

Asset intake may use original/disc/default.xbe plus the complete extracted disc
structure (including vc_53450030). The existing analyzer's default is the legacy
original/default.xbe path; pass -Xbe original/disc/default.xbe explicitly for the
folder described to the user. No duplication or public upload is required.


## User-provided executable analysis — October14,2026

The completed user archive contains a6300958720-byte Xbox image. Its directory
lists19files; extracted sizes match and the complete disc is private in
original/disc. default.xbe is11948032bytes, identifies title ESPN NFL2K5 /
0x53450030 / retail, and hashes SHA256
73105b17a3161c546fea792a1c84ce37f9966a67c416f474cdbfab74b911a4a9.
Asset and raw analysis paths are Git-ignored and remain local. Header identity
is not runtime execution or a redistribution grant.

Existing parser/disassembler produced31081detected entries and278523crossrefs.
A bounded raw UTF16 scan found101occurrences of franchise/contract/salary/
free-agent/negotiation terms, with96distinct string starts. ASCII-only string
search would have missed these. Detected function ends can merge neighboring
callbacks: inspect exact instruction ranges instead of trusting aggregate labels.

Actual static Sign Contract chain:

- Descriptor0x00557B2C names Sign Contract via0x00EACD5C and uses message
  list0x00557AA0. Message11 entry0x00557AB0 points to type1record0x00557980,
  whose function slot0x00557984 holds0x003478A0.
- Entry path0x002B8820 calls0x00323140; its returned negotiation context is
  installed by0x00347890 at0x002B882F. Descriptor is loaded intoEDX at
  0x002B884C and pushed through existing FSM0x0006E390 at0x002B8851.
- Callback0x003478A0 ends at0x003478FB and calls shared0x00323D80 at
  0x003478B1, with contextECX, &0x00CB8C38 inEDX and FSM/zero stack arguments.
  An automated record-iteration path also calls the shared routine.
- Global0x00CB8C34 is a negotiation-context pointer, not a durable player ID.
  [context] points to the player; [context+4] points to a separate object used
  in roster-count checks. Screen message6 callback0x00347B00 modifies
  context+8/+0x0A/+0x0C; these are not player fields at the same offsets.

Additional financial-display evidence: player salary getter0x000E5FE0 reads
uint16[player+0x0A]*10; its monetary unit still requires UI/save confirmation.
The accepted signing path writes its allocation candidate into the high nibble
of player+0x26 (dword+0x24 bits20..23), using mask0x00F00000 at
0x00323F77. The low nibble is a separate field; do not conflate them. Transaction-history reads use player+0x27 low nibble for
the integer term. Team salary display0x00362640 reads object+0x124 and displays
cap room using0x0013ECA0 minus that value. These establish candidates, not modern
cap/guarantee rules or a safe write interface. The Counter Offer string belongs
to message/result construction; it does not itself establish offer submission.

Actual Deck navigation now records descriptor0x00557B2C during a user Sign
Contract attempt. The engine remains vanilla at that screen. Keep
context/player/object pointers separate, verify UI amounts and controlled save
changes, and only then intercept the offer-judgment boundary. No financial write
or signing interception has been implemented.


## Read-only actual franchise-save inspection

The AIBASELIN user save supplies a verified retail Xbox FXG baseline.
`python3 -m tools.inspect_franchise_save /path/to/SAVEGAME.DAT` reads the
observed 720044-byte layout and prints year, named roster/free-agent membership,
source slots and payload hash. The independent reader attributes format facts to
[BAD-AL's pinned converter source](https://github.com/BAD-AL/nfl2k5tool_dart/blob/e3afeece61896380a95e506ab43ae1abda0ae8a5/lib/gamesave_tool.dart);
no converter code or proprietary save fixture is bundled. Its license and
binary redistribution gate remain unresolved.

AIBASELIN resolves 32 team rosters, 1937 unique members and 241 free agents.
Player records start at B288 with stride54; relative roster/name pointers are
checked, including duplicate memberships and bounded UTF16 termination.
`source_slot` is a location in this snapshot, not a durable player ID. The reader
exposes no ratings and infers no salary, cap, bonus or contract field. Other
formats/layouts are rejected rather than guessed.

Next controlled pair: reload the baseline and save with no roster/calendar
change as a control, then reload it and accept exactly one documented contract.
Record player/team and visible terms before/after, preserve companion files,
compare via `tools.save_diff --control-after`, and verify game reload/readback.
Financial mapping remains incomplete until these observations agree.


## Signing transaction boundaries reviewed against the actual executable

Shared routine0x00323D80 performs roster and cap preconditions before interactive
offer judgment0x00323A60 at0x00323F0E. A rejected judgment returns before player
contract writes. A conditional0x0013ED30 call follows acceptance before those
writes; it updates a separate old-contract accumulator (see the money audit). Subsequent player-state, roster,
team-refresh and history calls are part of the original transaction. Replacing
the whole routine with an AI acceptance boolean would skip these effects.

The accepted path copies context word+0x0C into player word+0x0A at0x00323F4D,
copies context byte+0x0A low nibble into player dword+0x24 bits0..3 and24..27,
and copies context+8 low nibble into bits20..23. Dollar units and the meanings
of the two term-like fields remain unverified by visible amounts/save reload.
The observer logs complete bytes and needs no change for the nibble correction.

The actual baseline bank header at0x320 declares2479 records, with its relative
pointer at0x324 resolving to0xB288. Runtime relocation0x000C0500 walks records
with stride0x54 and calls0x000E5E70, which relocates college/name/stats pointers
while leaving candidate monetary and packed bytes untouched. The current reader
restricts roster references to2317 slots from the converter-supported scope;
that limit is not the actual bank capacity. This static relationship does not
yet bind a live signing target to a persistent player identity.

Runtime verification must bind the observed pointer to a bank slot and name,
then compare salary-only and term-only contracts from AIBASELIN with an unchanged
save control. Keep the user's current game running; the compiled observer remains
staged until it can be applied safely after exit.


The opt-in signing observer now resolves global0x00B72918 as a count/base bank
and accepts the selected pointer only on a complete, aligned0x54-byte record
inside ordinary RAM or the runtime's separate contiguous window. It reads bounded relocated first/last UTF16 pointers and
logs bank_slot and names separately from unverified financial units. Slot/name
readback remains a current-bank locator, not a durable identity. Malformed,
unreadable, unterminated and unsupported surrogate names report identity unknown;
no relative-pointer fallback is attempted. This code is compiled and fixture-tested
but has not yet observed the actual AIBASELIN player in the running game.


Offer judgment0x00323A60 calls score routine0x003232A0 and displays original
refusal/decline/accept/generous-accept messages at score thresholds70/80/110.
Acceptance is determined by the score output referenced by EDI, not simply the
score routine's EAX return. That routine also participates in automated franchise
paths. Any AI replacement must be scoped to the verified interactive boundary and
preserve result/message state; do not override the shared scorer indiscriminately.


The original demand chain includes hidden-rating dependencies:0x002BD440 reads
player+0x3B and+0x4C (Durability/Leadership per the attributed layout) and calls
position-specific weighted evaluation. Other helpers derive behavior from bank
slot modulo and experience buckets; these are not durable personalities. A
conditional RNG call in0x003232A0 advances shared random state. The future AI
path must supply its own performance/personality decision, avoiding these ratings
as valuation inputs, while explicitly preserving the surrounding score/status
interface and deciding RNG sequencing. The current observer exposes no ratings.


Actual Trotter-screen execution reached the observer but reported unreadable
records at physical pointers0x811FCCE8/0x811FF3A0 and team0x811D3054. Those
pointers lie in the runtime's separately backed contiguous window, not low RAM
aliases. The observer now validates complete reads and the full bank against
either declared region using overflow-safe arithmetic, then copies the original
guest address through the fault-safe leaf. Never strip0x80000000 to read low RAM.
The trace includes the complete raw context+0x0C word and context+8 packed dword
for later UI comparison; units remain unverified.

Gaming Mode sends startup output to runtime-logs/steam-launch.log but actual
game stderr is redirected to the private prefix's
pfx/drive_c/users/steamuser/AppData/Local/NFL2K5-PC/logs/session.log. Read that
file for signing observations; absence from the launcher log proves nothing.


Team identity is a separate verification:0x000C4CA0 scans the active table for
a matching record pointer, returning index or0xFFFF.0x000C4D50 then reads
0x00E5775C[index]. In the bank-backed branch,0x000C4BE0 uses bank+0x18 count
and0x000C4C50 uses bank+0x1C base with stride0x1F4. Baseline header0x338
declares52 records and its relative pointer0x33C resolves0x44A8; the current
roster inspector names only its supported first32 clubs. Do not assert other[0]
is a stable team ID or derive the live club from a guessed franchise base.
Current-mode selection and live team-table binding still need evidence.


User-visible Gildon calibration: the current raw offer word829 matches$8.29M,
context+0x0A=2 matches2years, context+8 low byte4 matches40%bonus and bits29..31
value1 matchesDescending. The displayed total is an offer total, not an annual
cap charge. Display helpers multiply the word by10 (0x000E5FF0), then
0x0031E580 formats thousands/millions; this supports$10000 per raw offer-word
unit for this verified signing path. The completed controlled signing below
verifies persistence and the first-year charge; broader styles/aging remain open. Earlier Trotter word1949 versus user report$19.9M
remains unresolved; do not silently reinterpret it as verified$19.49M.

Completed controlled-save sequence: preserved AIBASELIN; save a separate unchanged
copy as AICNTRL without submitting an offer; capture payload and companions;
reload AIBASELIN before one documented Gildon signing; save its result separately
as AIGILDON and reload for contract readback. Record visible terms/cap before
and after, and compare with tools.save_diff --control-after. Original-game
signing is still vanilla; this experiment verifies mapping, not AI integration.


The controlled AIGILDON signing moves slot1792 from free agents to Giants.
Salary word+0x0A becomes829 and packed+0x24 becomes0x02410BA2, matching the
observed offer's2years/40%/Descending fields. Only this player's candidate
financial fields change. There are22 transaction-only bytes versus14405 bytes
shared with the no-signing control. The Giants' stored+0x124 total changes
72272→77038; its+0x19C accumulator stays0.

User-visible cap limit$80.50M, team totals$72.27M→$77.03M and room$8.22M→$3.46M
match native-thousand totals$72.272M→$77.038M and exact room$8.228M→$3.462M.
The display truncates to two decimal places; never derive spendable dollars by
subtracting the displayed rounded/truncated numbers. This establishes the
original first-year charge delta$4.766M, not modern proration/guarantee correctness.

`python3 -m tools.inspect_player_contract /path/to/SAVEGAME.DAT 1792` independently
reads supported named active contract records without writing or reading ratings.
It exposes calibrated game total/style/bonus and both raw term nibbles, refusing
unsupported codes or missing terms. Only observed Descending/Balanced styles are
interpreted. It now exposes annual rows calculated from original static rules
for those two styles; these are not modern cap allocations or guarantees.
Original-field aging still needs controlled season evidence, and slot is not a
persistent ID.


Original annual calculation evidence: E6020 computes allocated bonus in whole
thousands as floor(amount_word * bonus_code / original_years). E6040 first
truncates a float32(total_thousands / original_years), then subtracts allocated
bonus. Balanced (table code2) returns that salary directly. Descending (code1)
uses the half-salary integer and a float32 year-position fraction, then truncates
the final float32 salary. Verified jump-table entries and constants0.5/1.0
were read from the private supplied image; no binary or disassembly is bundled.

The decoder preserves this rounding rather than repairing the residual: Gildon
year0 salary3108K + bonus1658K =4766K; year1 salary1865K + bonus1658K =3523K.
Total original postings are8289K versus the displayed8290K offer. Year0 matches
the exact controlled team charge; both annual rows match the user's post-reload
UI (3.10M/1.65M and1.86M/1.65M). Year1 exact native charge is a static
reconstruction, not a verified subsequent-season posting. This read-only
calculation does not modify the modern engine's exact bonus conservation.


`python3 -m tools.reconcile_franchise_payroll /path/to/SAVEGAME.DAT` now checks
all32 supported clubs' original current roster contract charges against stored
team+0x124 totals. It reads all raw schedule codes0..7 using the static annual
calculation; unnamed codes do not gain invented UI labels. Remaining/original
term fields select the current contract-year index as E6380 does. Zero remaining
terms are explicitly excluded, not imported as released or retained obligations.
Unsupported active fields fail; a payroll mismatch returns CLI exit3 and retains
the exact difference. Neither a match nor original payroll establishes spendable
modern cap room, cash coverage, guarantees, or absence of other obligations.

Actual private AIBASELIN/AICNTRL/AIGILDON reports match all32 club totals, with
1696/1696/1697 active contracts. Giants reconcile72272K/72272K/77038K. This
checks the authored reconstruction against independently stored guest totals,
not an expected value generated by the same function. The three payload hashes
remain unchanged. Extra mode-specific obligations from246F20 are not decoded;
if they cause a difference the report refuses a match. An eventual game/modern
ledger importer must consume reconciliation evidence and supported obligation
data before authorizing writes; this tool itself imports or mutates nothing.


## Packed original player history boundary

Player+0x2C is the relocated history pointer (E5E70). E8A0 in the14xxxx
region reads it and tail-calls14E800. That iterator filters bits16..22 for
a statistic code, bits23..27 for a period code and bit29 for a selected mode;
bit28 marks deleted entries and bit31 ends the list. A terminal entry can still
contain a value and must not be discarded.14EE40 sign-extends the low16-bit
value after lookup. Mode selection is external state atBD7F98, so the inspector
retains both modes and deleted entries rather than guessing a combined total.

The bank header has count at360 and relative pointer at364 (runtime bank+40/+44).
AIBASELIN declares36866 four-byte records at41D54..65D5C.
`python3 -m tools.inspect_player_history /path/to/SAVEGAME.DAT SOURCE_SLOT`
checks selected named membership, declared bank extent, aligned relative player
pointer and a terminator inside that bank. Null pointers report missing evidence;
they are not zero performance. Output retains raw statistic/period/mode codes
and flags with explicit unverified metric/calendar/units scope. No hidden
ratings or model inputs are produced. Verified names/units and controlled
played/CPU/fast-sim changes are still required before negotiation consumption.


## Named passing-history metrics

The private original descriptor table atA8A510 has stride1C; offset0C maps
current-match stat fields to saved history codes. Existing named live-QB
accessor fields04/23/4C/40/16 map to7/6/8/9/10 respectively. Thus history
codes6..10 represent pass attempts, completions, passing yards, passing
touchdowns and interceptions thrown. The history reader adds these names and
count/yard units while retaining raw codes, periods, modes and flags. Passing
touchdowns and interceptions thrown are specifically named to avoid combining
them with rushing/receiving touchdowns or defensive interceptions.

Independent corroboration: AIBASELIN McNabb slot1146 period5/mode0 contains
478 attempts,275 completions,3216 yards,16 passing touchdowns and11 interceptions,
matching [NFL's 2003 McNabb row](https://www.nfl.com/players/donovan-mcnabb/stats/career).
The selected source period matches that historical row; this does not establish
a general calendar conversion or played/CPU/fast-sim classification. Sparse
missing entries remain absent, deleted entries remain marked, and no complete
window or zero count is invented. These are built-in historical game records;
future simulated-season and live observations still require controlled pairs.
Other statistic codes and defensive units remain unverified.
