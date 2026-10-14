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
