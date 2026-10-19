# Engine Sidecar

A small C++17 addon for connecting a native Windows or Linux application to an owned
companion process through bounded JSON-lines requests and replies. Extracted from
the original transport work in cosmokay1/2K5Remade. No game, franchise or AI needed.

## Boundary

The addon owns process launch, restricted handle/descriptor inheritance, cleanup,
one asynchronous request at a time, frame bounds and response envelope validation.
Applications own operation schemas, authorization, state freshness, UI and writes.
It does not expose arbitrary game memory or promise transactional game saves.
Windows 10/Server 2016+ and native Linux transports; portable envelope/launch
checks also run on macOS. This does not port a consuming Windows application.
The Remade game and franchise adapter still require Proton on Steam Deck.

Use engine_sidecar::PipeClient(executable, arguments), submit(json), ready(), take().
Callers can supply `submit(json, std::chrono::milliseconds(timeout))` for a bounded
1–65,000ms response wait; the default remains 5,000ms. Application adapters own
the choice of deadline, including any grace for a server's timeout response.
Call from a single owner thread. Do not destroy it from a render callback: cleanup
may wait for the owned process and worker. One pending request; no queue or retries.
Requests max 4095 bytes; replies max 65536 bytes, nesting max 32. Reply envelope:
protocol=1, matching request_id, result object or null, error string or null, detail
string or null. On Windows the reply deadline starts after the synchronous write;
a blocked write is released by owned-process destruction, not that deadline.
Linux uses nonblocking I/O with one deadline covering write and reply.
An application must reject obsolete replies and recheck authority before writes.

## Standalone checks

    cmake -S . -B build
    cmake --build build --config Release
    ctest --test-dir build -C Release --output-on-failure

Windows and Linux checks include a Python echo process with no external dependencies, assets,
credentials or paid calls. The franchise application in Remade is the first consumer
and adds its own contract validators, control handshake and launch configuration.
See NOTICE.md for provenance and current licensing scope.

## Linux ownership

Pass an absolute executable path and UTF-8 `std::string` arguments; Windows uses
`std::wstring`. Launch uses `execve` with exact argv, no shell, and inherits the
current environment. Unrelated descriptors are closed before exec. The owner must
retain the default SIGCHLD disposition and must not reap the client's child from
other code. A dead peer does not change or trigger the host's SIGPIPE disposition.

Normal abort/destruction stops the worker before closing its descriptors, gives
the peer 500ms to exit, then terminates its process group with a 100ms TERM grace
and KILL, with up to one second to reap. Abrupt parent death kills the direct peer
using Linux's parent-death signal. Descendants that leave the process group, or
survive abrupt parent death, require cooperative cleanup or application-owned
cgroups. This is not a sandbox or Windows job-object equivalence.

Linux process checks exercise exact argv, repeated requests, malformed/mismatched/
oversized replies, dead/stalled peers, timeout/abort, descriptor inheritance,
normal descendant cleanup and abrupt-parent death. They run without Proton.
