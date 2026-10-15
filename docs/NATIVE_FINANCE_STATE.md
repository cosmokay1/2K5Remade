# Native financial comparison

The franchise addon exposes the read-only `franchise.finance-state.v1` snapshot
through the existing ABI2 snapshot callback. The host supplies a
`FranchiseFinanceSnapshot` buffer with exactly its declared capacity. Success is
1; `size` selects the used bytes. Failure is 0 and clears the output buffer for
a correctly sized request. No game patch, guest write callback, model request or
authorization is involved. Request this on the guest owner thread; it is an
explicit comparison operation, not something to run on every rendered frame.

`python -m tools.franchise_finance_state SAVEGAME.DAT native-state.dat` compares
those used bytes with an independently read, payroll-reconciled saved projection.
The file paths are explicit local diagnostic inputs; the addon does not open
these paths, return an entire save or accept arbitrary memory addresses.

The little-endian image contains:

| Offset | Content |
| --- | --- |
| 0 | Version 1, bank count, table mode, league cap: four uint32 words |
| 16 | Seven uint32 calendar words, in existing observation order |
| 44 | Reserved zero uint32 |
| 48 | 32 payroll/flag/accumulator triples, each three uint32 words |
| 432 | One 11-byte record per bank slot: byte8 flags, uint16 amount, uint32 packed contract, uint32 owner |

Owner is team index 0–31, free agents 32, or `0xffffffff` for a non-rostered
record. Raw guest money units are retained; no modern-dollar conversion is
performed here. Contracts in every bank slot are included. Roster ordering and
relocated pointer values are excluded. This does not export names or ratings.

The live reader uses the bank at `B72918`, its count/base and 0x54 stride;
mode/table/calendar globals already used by the signing adapter; 0x1F4 club
records with count at 0x11C, payroll at 0x124 and accumulator at 0x19C. The
free-agent vector is bank+0x38: `324060` passes it to `2425C0`, which reads a
DWORD count and a relocated pointer list at +4. It must not be read as a Team
object or a serialized relative-pointer table. The saved projection uses the
existing independent roster, calendar and reconciled-cap readers.

The reader rejects unsupported modes/counts, overflowing/out-of-range pointers,
misaligned bank members, duplicate membership (including across clubs/free
agents), aliased club records and header/table changes during capture. It
rechecks bank, calendar, cap and table metadata at the end.

The native owner captures this image and its companion roster identity image
when preparing a captured accepted proposal. The C client requires their used
bytes, hashes them with Windows CNG, and adds `live_finance_sha256` and
`live_identity_sha256` to the otherwise captured preparation request.
The service requires both canonical SHA256s and compares them to independently
read saved projections before reserving the journal. Missing captures, unsupported
images and differing financial states cannot prepare work through this path.
The existing saved-file/control/connection/deadline checks still run inside the
preparation transaction. A failed local capture keeps signing held.

This is a cooperative-client consistency check; a client-supplied digest is not
proof of the active process or atomicity. The new C wrapper signature and service
preparation schema must be deployed together. Older requests without the digest
are refused; saved-status/confirmation recovery and persisted journal formats
are unchanged. No additional provider request is used for comparison or retry.

**This is not an atomic world snapshot or a signing permit.** Contracts and
roster entries could change while reading. A future application coordinator
must establish guest quiescence, match the prepared journal's expected financial
projection, verify all bound identities and active pack/runtime, check current
remote authority, and consume a one-use permit at the actual transaction.
Equal financial bytes do not prove those conditions. Existing controlled
signing remains held, and no current code consumes this snapshot to authorize
application. Cash and other unsupported opening obligations remain separate
requirements.

The companion `franchise.identity-state.v1` snapshot uses
`FranchiseIdentitySnapshot`, allocated on the heap rather than the Windows
stack. Its used bytes begin with three little-endian uint32 words: version1,
bank count and member count. Each member then has 211 bytes: uint32 bank slot,
four raw PBP/photo bytes, three raw DOB-region bytes, and two100-byte UTF-16LE
name fields. Members are sorted by bank slot. Each name is nonempty, terminated
within50 code units and zero padded; valid surrogate pairs are preserved, while
control characters below32 and malformed UTF-16 are refused. Each record's raw
biography fields and name pointers are checked again after reading its names;
the bank header is rechecked at the end. Pointer relocation and roster order
do not change it.

All rostered and free-agent identities are included, matching the binding
registry's membership scope. Unrostered bank biographies have no bound actor
and are omitted; their contracts remain covered by the financial image. This
does not issue new IDs, reroll personalities, prove real-world uniqueness or
establish identity across bank/season migrations. The existing server binding
checks remain authoritative for its saved actor mapping. No raw identity image
is sent to the model or over the preparation protocol: only its SHA256 is sent.

Both captures remain sampled comparisons. Equal identities and finances cannot
prove that the active process selected the intended franchise namespace, that
the pinned runtime is executing or that guest mutations have stopped. These
conditions and revalidation at the actual transaction remain required before
granting a one-use application permit. Current signing is still held.

The rebuilt host now restricts guest-memory reads to one uninterrupted
guest-lock-owned addon invocation. Both images in the native preparation path
are captured inside the same poll invocation. A disabled lock, an unowned call
or any full lock release/reacquire makes subsequent reads unavailable. This
excludes competing translated guest threads during a successful capture on this
host; it is not a DMA/host-writer lock or a permit for later writes. The original
transaction may yield at kernel/blocking boundaries, so checking ownership at
entry does not establish an uninterrupted commit. Older host builds do not
gain this restriction from a DLL update, and runtime compatibility remains open.

The CI command `python -m tools.check_native_finance_state <fixture executable>`
runs the actual addon snapshot callback against authored relocated-memory files
and compares it with saved semantics. It covers expanded banks, benign pointer
relocation/free-agent ordering, financial and membership changes, malformed
layouts and truncated memory. It neither boots the game nor verifies save/load.
The same executable's `identity` mode is exercised by
`python -m tools.check_native_identity_state <fixture executable>`, covering
relocation, reordered free agents, expanded banks, unrelated player guard/name
changes, valid Unicode and bounded/malformed name handling.

### Opt-in live capture for reconciliation

On a compatible rebuilt host/addon pair, set `NFL2K5_FRANCHISE_CAPTURE` to a new
absolute output filename in an existing directory. For example, a private Deck
test can use `Z:/home/deck/live-franchise.dat`. Open a player's offer screen in
the loaded franchise without submitting. The existing screen event captures the
financial and identity projections through the host's scoped read callbacks.
No provider, cloud grant or negotiation mode is required. With the variable unset,
this diagnostic performs no capture. It attempts one file creation per addon start
after valid reads, refuses to overwrite a file, and logs written/failed. Invalid
memory can retry at a later screen event. Keep captured player data private.

Compare against the corresponding saved franchise payload:

```sh
python3 -m tools.compare_live_franchise SAVEGAME.DAT live-franchise.dat
```

The file contains the 8-byte `2K5CAP1\0` magic, two little-endian 32-bit payload
lengths, then financial and identity projection bytes. The reader bounds both
images, requires matching bank counts and exact dimensions, and rejects partial
or trailing data. Existing saved-state builders independently derive both
expected projections. A mismatch exits nonzero; matching hashes do not establish
the active franchise namespace, official NFL obligations, current AI authority,
host/DMA exclusion or permission to apply a transaction. This is diagnostic
evidence and is never consumed as an application permit.

### A free agent reserved by the offer screen

Actual SOFTDRINK v0.6 execution showed that opening Will Hernandez's offer removes
his pointer from the free-agent pool before signing. His bank contract stays
unchanged. The captured MyNFL1 state had identical cap/calendar fields, all32 team
financial rows and all2619 bank contract/flag records, but slot2371 had no listed
owner and its biography was absent from the member-only identity image. The
remaining2069 sampled biographies matched the saved2070-member roster exactly.

A strict saved-state comparison continues to reject this state. For an explicit
read-only diagnostic, use the selected saved free-agent slot:

```sh
python3 -m tools.compare_live_franchise SAVEGAME.DAT live-franchise.dat --pending-free-agent-slot 2371
```

The expected offer-screen projection changes only that saved free agent's owner
to unlisted and removes its identity row. It preserves every bank contract,
calendar field, club financial row and other biography. Owned/unbound candidates,
a different missing player, changed finances or mixed full/pending hashes fail.
The comparison is explicitly scoped; the omitted player's live biography is not
established by this image. Its current selected-player observation and eventual
transaction checks remain necessary.

Game-facing journal preparation accepts either the exact full saved pair or this
exact transient pair for the player in the durable accepted proposal. Both hashes
are checked together inside the journal transaction, including retries. The
service derives the slot from its pinned bindings and accepted player ID; clients
cannot supply a missing-player exception. Complete books, exact terms, current
control, revision and save/recovery checks remain required. No game write or
application permit is granted. The CLI diagnostic itself is not journal authority.
