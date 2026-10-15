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

The owner thread controls lifecycle and poll/event delivery. Snapshot calls may
come from the renderer and must return an already-owned snapshot without I/O.
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
than interpreting the old callback table. The working Deck game remains on ABI1
until a separately verified pair is installed after normal exit. The pinned-host
installer must use hashes for the matching tested pair; changing its manifest does
not add compatibility to an older host.

Preserve upstream and addon provenance. Original public reuse licensing remains
undecided; this file does not grant a new license.
