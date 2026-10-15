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

### Expected isolated signing target

`tools.franchise_offer_state.expected_signed_state` derives the final financial
and identity comparison images from a pinned before-save, bound free-agent ID,
exact accepted offer/captured terms and target team. It returns comparison bytes,
not a modified save or memory-write command. The image moves only the selected
owner, updates its amount and the native mapped term/bonus/shape fields,
preserves the other packed bits, clears player byte8 bit3 and adds the exact
first-year raw charge to the target payroll. Complete roster identity membership
is restored; other records, cap, calendar and club fields remain exact.

Saved confirmation now checks this image after its existing detailed economic,
identity, calendar and payroll checks. Thus unrelated packed-status or bank-flag
changes cannot be hidden by equal decoded contract values. Existing result fields
and journal formats are unchanged. Unsupported identity changes (including any
native custom commentary-ID reassignment) still require separate validation;
this does not relax identity binding or claim every native signing variant.

A private isolated probe executes the actual generated shared signing routine,
with authored relocated memory, local legal constants, retail judgment bypassed
and UI/judgment calls configured to abort. Its pending-before image and final
financial/identity images match the expected projections, including preserved
packed bits and the cleared flag. This is generated-routine evidence, not game
execution, an uninterrupted transaction guarantee, a permit or save/reload proof.
The installed runtime remains unchanged and controlled signing remains held.

### Native judgment replacement boundary (production grants remain unavailable)

The host shim now recognizes a separate application-specific event,
`franchise.sign-application.v1`, using the existing stage/context payload and ABI2
transport. This does not change the reusable addon API. Exact reply2 means an
application authorizer approved that stage; other replies cannot grant a
controlled transaction. Existing sign-gate.v2 replies remain hold-only.

With negotiation and saved-signing modes explicitly requested, the judgment
hook can skip retail judgment, set EAX1 and enter the original judged-result
continuation. A thread-local context then requires a second, same-context reply2
at precommit. That context is consumed before calling the addon. Missing,
invalid, repeated, bypass/CPU or mismatched grants hold; beginning another call,
consuming/resetting hold state, lifecycle reset and intervening legacy holds
invalidate it. Turning either requested mode off after judgment holds that call.
The two application callbacks now also require the same nonzero runtime guest-lock
acquisition serial before/after each callback and between judgment/precommit.
Missing ownership or release/reacquisition consumes the attempt and holds it;
retry requires a fresh judgment. The serial is thread-local runtime evidence,
not a saved journal permit, and this does not keep the lock through original-game
writes after precommit. Completion evidence is still collected even if control
changes after application. Production grants remain unavailable.
The compiled and interpreter hooks follow the same continuations. Known v1/v2
cached patches upgrade explicitly; custom bodies or moved gates reject.

**The production franchise addon only checks pending-work refusal for this event
and issues no application authorization.** No service/remote permit issuer was added. Future
implementation must bind the prepared journal, exact current offer and complete
books, active franchise/runtime, current remote authority, durable one-use
permission and an uninterrupted mutation plan before either reply2. A trusted
addon return value is a local signal, not independent evidence of those facts.
The unresolved optional UI path after contract writes still prevents assuming
that every original signing call is uninterrupted. Do not enable live signing
based on this component.

Asset-free tests execute the production patches and host shim with authored
stage grants, proving retail judgment is skipped while original commit/history
branches remain, with retail behavior preserved when disabled. A private probe
also executes actual generated signing/callees and the actual shim with authored
grants and retail judgment/UI abort stubs. Its final financial and identity
images match the expected signing target. This is isolated generated-code
execution, not production authorization, live gameplay or saved-game proof.

### Native successful-completion notification

The original shared signing success epilogue now calls a thin completion hook
after its contract, roster/payroll and history calls, before register restoration.
Both generated and interpreter paths use0032404E. The pinned v0.6 bytes at that
address match the expected15-byte pop/result/return epilogue. Generated caches
with a moved or customized completion hook are refused rather than trusted.

Only an authorized same-context precommit arms the thread-local notification.
The hook consumes it before invoking the addon, so duplicate/reentrant/wrong-
context callbacks cannot repeat it. A new judgment/call, hold/hold-result reset
or lifecycle reset clears it. Failed or retail commits do not emit it. The
private event franchise.sign-completed.v1 carries the uint32 context; its reply
is ignored. Control disable after writes does not suppress this notification,
which is needed for recovery without authorizing further work.

The production addon still grants no applications. Its completion consumer now
queues the live target comparison described below. Actual saved/reloaded proof
and application authority remain required before final delivery. This notification alone is not a commit receipt, save proof or
evidence that the original routine never yielded. The optional post-contract
UI path and all existing authority/accounting gates remain unresolved.

### Read-only comparison of completed live projections

The existing guest_signing_status request optionally accepts both canonical
live_finance_sha256 and live_identity_sha256. When supplied together it adds
only live_application_matches, comparing both client-reported digests against
the exact native target reconstructed from that journal's persisted original
save, bindings and accepted terms. Missing/invalid pairs fail; cancelled journals
cannot validate an application. Requests without projections keep the existing
seven-field response. The native response validator requires the conditional
boolean and refuses unsolicited, missing or malformed extensions.

A live match is independent of save_position: it may be true while the current
save still equals the original. It does not settle a journal, advance finances,
change cash or grant a write. Recovery remains available with AI disabled and
without inference. These are client-reported hashes, not independent proof of
current guest state, lock continuity, active runtime or application authority.
The completion consumer described below now queues this status request.
Saved confirmation still requires an exact candidate after-save and current
settlement authority; actual game signing/save/reload remains unverified.

### Native completion handoff to the prepared journal

A nonzero, correctly sized completion event now enters the franchise transport
owner. It samples the existing whole-league financial/identity projections in
that addon invocation, validates snapshot framing and copies their SHA256s into
the validated prepared journal. The callback never waits for transport. It can
record while an older status request is pending; the next idle status request
includes the immutable projection pair. Identical repeats are harmless, changed
observations reject. No application event handler or write grant was added.

The native journal must compare a captured completion before queuing a saved
confirmation, even when an older pending reply already identifies a candidate
after-save. A live mismatch stops automatic coordination. A matching live result
with an unchanged save continues read-only status checks; confirmation still
requires the saved candidate and current AI/control grant, rechecked by the
service. Completion capture and status reads do not require AI to remain enabled.
Wrong-thread, unreadable or unbound completion sets a failure flag consumed by
the owner, leaving durable prepared work for recovery. Start/stop reset the flag.
This does not cancel a server operation already submitted. Future application
authorization must pin the transaction to that owner; foreign completion is
refused rather than passing live pointers between threads.

This is source-level integration, not an enabled game signing flow. The installed
runtime is unchanged. Complete opening accounting, application permits, runtime/
franchise binding, uninterrupted mutation and actual signing/save/reload remain
required. Restart recovery still relies on independently verified saved effects.

### Pending native work before an application attempt

Before either application stage can proceed, the production addon now samples
the selected bank player and the original15 trade rows/100 offer records. It
holds unreadable or changing data and active records involving that player.
It returns no grant when the queues are clear. This prevents an application
attempt from proceeding to the original cleanup of those pending transactions;
the guard itself does not submit a negotiation or mutate guest memory.

The inspected original shared signing routine calls002BB6E0 after contract
writes. Its matching trade/offer cleanup can trigger the blocking warning popup
at00323FC7. With neither lookup matching the selected player, that helper returns
zero and the popup branch is skipped. The five relevant lookup/cleanup code
ranges are byte-identical in the local retail and pinned SOFTDRINK v0.6 assets.
A private cross-check agrees with the actual generated lookups across771 authored
queue cases. This does not prove the full transaction cannot yield: the permit
issuer still needs pinned runtime/pack identity, exclusive mutation ownership
and current authority. Other packs or pending-work scenarios need revalidation;
no popup was removed or silently skipped by a native patch.


### SOFTDRINK signing call graph still needs interpreter validation

A private comparison of full generated function extents against the legally local
retail XBE and pinned v0.6 XBE covers all43 functions used by the authored signing
probe. Thirty-six extents are identical; seven differ. Entries000C3EE0,
000C4D50,00242560,0013ECA0 and0013ED30 redirect into mod code;00247AF0 changes
a mask, and00323D80 redirects one helper call to00295320. The private receipts
are native-application-probe/callgraph-code-receipt.json and
callgraph-instruction-changes.json. No executable bytes or retail generated
source are published with this evidence.

Consequently, the existing probe's exact expected finance/identity result proves
the generated retail-body path under authored application grants only. It does
not establish the patched pack's post-signing behavior or absence of yielding.
The next application check must execute the dirty-function interpreter routes,
including these detours, with the production signing hooks and compare the final
images before any live permit can rely on that path. Active runtime/pack binding,
complete books and actual signing/save/reload remain required independently.
