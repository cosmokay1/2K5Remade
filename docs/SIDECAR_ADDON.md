# Sidecar addon boundary

Engine Sidecar is the reusable companion-process transport, published privately at
https://github.com/cosmokay1/engine-sidecar. It has no game hooks or franchise rules.
The NFL 2K5 application is a separately loadable Windows DLL, franchise-addon.dll.
Its adapter, service ownership, control policy and result validation are outside
the native game executable. This source change is not yet game execution proof.

## Native host integration

The host retains lifecycle forwarding, the existing input/FSM/signing callback
points, a checked read-only guest-memory capability, and the existing HUD display
consumer. No new hooks are inserted into generated game code. The DLL contains
game addresses, observations and signing diagnostics in nfl2k5_sidecar_adapter.c,
and uses nfl2k5_franchise_host.c plus the reusable transport to talk to the service.

The versioned C boundary is native/franchise_bridge/game_addon.h. The loader checks
ABI version/size and required entry points before starting. Host callbacks permit
range checks and bounded memory reads only. There is no guest write capability.
All events/polling stay on the established owner; the renderer gets an owned display
copy. A shared/exclusive lock prevents DLL unload during a display call. Shutdown
stops the service before unloading its code. This is a trusted native addon, not a
sandbox for untrusted code, and does not implement live hot-reload during gameplay.

## Build and install

Build the native game with NFL2K5_FRANCHISE_CLIENT enabled. The build creates the
franchise_game_addon shared-library target and copies it beside the game under
addons/franchise/franchise-addon.dll. Standalone native/franchise_bridge checks
also build the DLL and test load/query/forward/stop/reload without game assets.

Once a compatible host is installed, rebuild and replace the DLL while the game
is closed; the native executable does not need rebuilding for ABI-compatible addon
changes. Do not replace it in a running session. Include the DLL explicitly in
private package manifests. NFL2K5_SIDECAR_ADDON can select an explicit absolute path.
Default lookup is relative to the executable, never the working directory/PATH.

Missing default addon permits the original game with no sidecar feature. An
explicit bad path, incompatible module, or configured service startup failure
rejects startup; there is no inference/manual signing fallback from such failures.
A loaded addon still requires the existing explicit provider/database/control
configuration. Loading it does not enable AI. Original guest signing still runs;
intercepted judgment/commit/recovery remains unfinished.

## Verification limits

Offline transport CI does not establish game hooks, SOFTDRINK v0.6 compatibility,
legal signing or save/reload. The read-only adapter fixture checks authored RAM,
identity bounds, physical/ordinary memory access and unchanged memory. Actual game
build, execution and controlled SOFTDRINK saves remain acceptance gates. Public
licensing for our original addon code has not been selected; retain all notices.

Verified source6f75219: CI38656804337 passed Windows DLL ABI/load/forward/stop/reload
and all702 regressions on Windows/Ubuntu; Build38656804259 passed. The DLL fixture
keeps the service disabled; actual-game deployment and service-through-DLL checks
are still required.

## Mod manager integration

The existing Mods screen now includes a separate Franchise Sidecar row. Its
selection is independent of the content pack: SOFTDRINK can stay selected while
the addon is enabled or disabled. The file next to the installed addon,
addons/franchise/enabled.ini, stores exactly enabled=1 or enabled=0 with LF.
Missing/malformed state defaults off. Installing a DLL does not enable it.

The row shows Not installed when its DLL is absent, and On/Off - restart when
saved selection differs from the current loaded module. Changes persist for the
next launch; they do not restart the game, unload code during gameplay, or save a
franchise automatically. The prompt asks the player to save, exit and relaunch.
The current native menu has16 rows; one is reserved for the addon and15 for packs
in addon-enabled builds. Existing pack selection/restart behavior is retained.

An explicit diagnostic DLL path still obeys the manager selection. Enabling the
addon does not enable cloud AI or renew its remote grant. ABI/service checks still
apply at startup. Installation automation, runtime visuals/controller behavior
and SOFTDRINK v0.6 execution remain separate acceptance gates.


## Shared executable identity

The addon must use one negotiation/accounting/story pipeline for vanilla Remade
and compatible mod packs. Mod names and a predefined executable whitelist must
not select application behavior. Differences in calendar, units, roster and
contract data must be supplied as verified context to the same rules. New v2 snapshot registries persist explicit calendar/units/cap context. Copy-only
conversion preserves old franchise/player identities, personalities and legacy
schedules. Named profiles remain a read-only v1 compatibility path for existing
registries and recovery journals, never a new-creation policy selector. Live
store/journal migration and active service binding remain unverified. See
[franchise-creation.md](franchise-creation.md#shared-snapshot-context).

The host now sends optional ABI2 metadata engine.loaded-image.v1 immediately
after addon startup. native/game_addon/runtime_identity.h defines its65-byte
canonical lowercase SHA256 payload. The digest describes the XBE bytes supplied
to the loader after built-in file patches, before later runtime/guest writes.
The same event is used for every image; there is no vanilla/mod-name branch or
hash whitelist. Other addons may ignore it. The generic example and franchise
addon expose an immutable owned copy through a same-name snapshot.

The host binds the digest before startup, refuses a different binding while a
DLL is loaded and prevents ordinary forwarded events from impersonating this
startup message. Invalid unbound input clears stale metadata; stop/reload clears
the addon's copy and receives the host's current binding again. This is trusted
local metadata, not a sandbox or independent attestation. It grants no guest
writes, remote AI access, franchise identity or compatibility with unknown code.
The franchise host now forwards this digest in hello. A configured explicit
loaded_image_sha256 in the v2 registry must match before the service allows
inference or saved-journal writes. That handshake also requires an explicit
persisted database/registry association, created with tools.bind_franchise_snapshot.
Registration audits actor origins and initial ownership; runtime verification
checks the stored namespace and immutable bootstrap fingerprint. It neither
replaces old journal intents nor proves active guest-franchise selection.
The native response validator requires an exact
image echo plus well-formed configured franchise/registry/snapshot identities.
Negotiation-enabled game callbacks fail closed when loader metadata is missing;
legacy engine-only fixtures can still use hello without a load-image claim.
Failed re-handshakes revoke the session match, and remote shutdown remains an
independent requirement. This is a connection-to-configured-snapshot check,
not proof of the active guest save, complete opening books or application authority.
Actual game-boot delivery/handshake and live signing/save-reload remain unverified.

Franchise interpreter hooks are now registered independently of an executable
name/hash. The dispatcher compatibility path follows whether the interpreter
is active, rather than a SOFTDRINK-specific digest. Actual signing/save/reload
acceptance on each supported runtime remains required.


## Native file-read observation

The runtime fork supplies a synchronous read-only file observer. Before guest
startup, an addon-enabled host registers one forwarding callback; it publishes
engine.file-read.v1 through ABI2 without choosing behavior by pack/image name.
The native handle and delivered bytes are borrowed during event delivery, before
a successful read signals its completion event. Unknown events may be ignored.
The generic counter addon exposes the observed byte total as an example.

The handler runs on the reading thread, which may not own the process transport
or guest lock. It must copy bounded data and hand off application work. This
metadata grants no extra memory access, writes or inference. It exposes no file
offset and does not prove source stability, deserialization success or active
franchise identity. Binding a verified container/read to its completed load and
current franchise projections remains application work. No real game load or
signing/save-reload acceptance is established by notification fixtures.

The Windows franchise application now consumes full720044-byte deliveries that
match the supported FXG roster envelope. Its optional franchise.save-read.v1
snapshot owns a sequence, delivered-payload SHA256 and native file identity/size/
write-time values sampled during that callback. Failed, partial, malformed and
wrong-sized native-file deliveries do not replace the last candidate. Restart
clears it. No handle or buffer is retained; no guest memory, process transport,
ledger or model is accessed from this callback. Opt-in franchise trace emits the
last new candidate from the owner poll, outside the file callback.

This is the most recent matching read, not the selected/active franchise. The
filter is not the full roster/calendar validator, and unchanged native metadata
does not prove immutable disk contents or absence of a runtime overlay. Its hash
is of delivered bytes. Split reads have no candidate until a supported complete
delivery can be established. Causal load completion, selected container, current
projections and durable registry/database association remain required before any
application permit. The same checks apply without image/mod-name branches.

Destination correlation uses optional engine.file-read.v2: bounded host-to-guest
translation supplies an owned guest locator without granting memory access.
Legacy engine.file-read.v1 delivery remains unchanged. The current source
franchise.save-read.v2 snapshot consumes the richer event once per delivery and
records the locator or explicit unknown; the earlier installed v1 snapshot
remains historical read evidence. Guest locators can be reused and do not prove
load completion. Causal load-boundary checks are still required.
