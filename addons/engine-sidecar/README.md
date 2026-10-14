# Engine Sidecar

A small C++17 addon for connecting a native Windows application to an owned
companion process through bounded JSON-lines requests and replies. Extracted from
the original transport work in cosmokay1/2K5Remade. No game, franchise or AI needed.

## Boundary

The addon owns process launch, restricted handle inheritance, job-based cleanup,
one asynchronous request at a time, frame bounds and response envelope validation.
Applications own operation schemas, authorization, state freshness, UI and writes.
It does not expose arbitrary game memory or promise transactional game saves.
Windows 10/Server 2016+ transport; portable envelope/launch checks also run on Linux
and macOS. Steam Deck use currently depends on the Windows host under Proton;
a native Linux process transport is not implemented.

Use engine_sidecar::PipeClient(executable, arguments), submit(json), ready(), take().
Call from a single owner thread. Do not destroy it from a render callback: cleanup
may wait for the owned process and worker. One pending request; no queue or retries.
Requests max 4095 bytes; replies max 65536 bytes, nesting max 32. Reply envelope:
protocol=1, matching request_id, result object or null, error string or null, detail
string or null. Five-second reply deadline starts after the synchronous write;
a blocked write is released by owned-process destruction, not that deadline.
An application must reject obsolete replies and recheck authority before writes.

## Standalone checks

    cmake -S . -B build
    cmake --build build --config Release
    ctest --test-dir build -C Release --output-on-failure

Windows checks include a Python echo process with no external dependencies, assets,
credentials or paid calls. The franchise application in Remade is the first consumer
and adds its own contract validators, control handshake and launch configuration.
See NOTICE.md for provenance and current licensing scope.
