# Native addon interface, ABI2

api.h is the domain-neutral C interface between the Windows host and a trusted
native DLL. It has no franchise, AI, JSON, financial or renderer types. Export
nfl2k5_addon_query(abi); return NULL for unsupported versions. The host checks ABI,
exact table size and required callbacks before starting the module.

Callbacks are start, stop, poll, named event and named snapshot. Applications own
message names and payload definitions; use versioned names. Event/snapshot buffers
are borrowed for one synchronous call and must not be retained. Validate sizes
before reading/writing. Unknown names and invalid sizes return0. The start host
structure is also borrowed: copy its function pointers if needed after start.
The current host provides checked memory-range/read callbacks and no guest-write
capability. A native DLL still runs in the host process; this is not a sandbox.

The current host grants memory reads only during a synchronous addon invocation
on a thread holding the enabled global guest lock. Each lock acquisition has a
non-reused serial. Retaining callback pointers, nesting an invocation that began
without ownership, or releasing/reacquiring the lock cannot extend a read scope.
Disabled locking, host-only callbacks and a changed serial return unavailable;
the host does not acquire or pin the guest lock for the addon. Range queries
remain available without reading memory. Start/stop must tolerate unavailable
guest state. The callback table and ABI2 number are unchanged.

The owner thread controls lifecycle and poll/event delivery. Snapshot calls may
come from the renderer; render-facing channels must return an already-owned
snapshot without I/O. Explicit world-reading channels return unavailable unless
invoked in a guest-owned read scope and must never wait for I/O.
The loader serializes unload against callbacks; callbacks must not reenter loader
lifecycle operations. Application synchronization remains the addon's responsibility.
There is no gameplay hot reload, queue, discovery registry or arbitrary hook API.

example_addon.c only includes api.h and standard headers. It accepts/returns a
uint32 counter through example.counter.v1; polling increments it. The existing
Windows fixture loads it through the same loader as the franchise DLL and checks
message delivery, snapshot size, unknown channels and unload. legacy_addon.c is
an ABI1-only refusal fixture. Build/run the fixtures without game assets:

    cmake -S native/franchise_bridge -B build-franchise-bridge
    cmake --build build-franchise-bridge --config Release
    ctest --test-dir build-franchise-bridge -C Release --output-on-failure

Franchise-specific payloads live in ../franchise_bridge/franchise_addon.h. The
host wrapper game_addon_adapter.c translates the existing call sites; the DLL
adapter implements their handlers. Existing game hooks and presentation are still
franchise-specific. Manager selection and installation still support one explicit
Franchise Sidecar slot. This change generalizes the public ABI and module dispatch,
not the entire manager or every host integration point.

ABI2 requires a matching rebuilt host and DLL. It deliberately rejects ABI1 rather
than interpreting the old callback table. Deployment requires a separately
verified pair installed after normal exit; source builds and fixtures do not
change the existing Deck installation. The pinned-host
installer must use hashes for the matching tested pair; changing its manifest does
not add compatibility to an older host.

`native/guest_execution` builds the actual runtime lock with authored threads.
Its checks cover disabled/unowned reads, recursive ownership, cross-thread
exclusion, full release/reacquire and blocking-yield invalidation. The Windows
loader fixture also checks a real DLL making two reads while its host changes
the sampled serial between them. This protects cooperative sampled reads only;
it neither authenticates a runtime nor authorizes writes. A serial does not stop
DMA/host writers or survive a guest yield during a later transaction.

Preserve upstream and addon provenance. Original public reuse licensing remains
undecided; this file does not grant a new license.
