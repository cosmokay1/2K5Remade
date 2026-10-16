# Ray-traced shadow proof

An asset-free, standalone experiment. It does **not** replace the game's D3D11
renderer or add shadows to NFL 2K5 yet. No franchise, sidecar, addon ABI, game
installation, save, or cloud configuration changes are required.

The scene is an opaque square one metre above an eight-metre ground receiver.
One finite shadow ray travels from each receiver pixel toward a point light.
The GPU builds a triangle BLAS and one-instance TLAS, then uses DXR 1.1 inline
`RayQuery` in a compute shader. The output is a top-down shadow mask, not a
perspective rendering of a stadium. There is no screen-space approximation,
software fallback, denoiser, animation or performance claim.

## Acceptance

- A light on the left produces a nonempty shadow.
- Moving the light right moves/mirrors the shadow.
- Excluding the blocker by instance mask produces no shadow.
- All65,536 GPU pixels in **each** case match an independent analytic CPU
  rectangle-intersection reference exactly. Any disagreement fails the proof.
- Only completed, matching GPU runs write `gpu/passed.txt`. Unsupported hardware
  exits77 and appears as a skipped CTest; that is not a successful GPU proof.
  An earlier completion receipt is removed before attempting hardware creation.

The CPU test also checks known hit/miss rays, a parallel ray and a blocker beyond
the light. It independently checks shadow coverage and mirrored-light symmetry.
The shader receives only the fixed scene/light settings; it does not read or copy
the CPU mask. GPU results are read back after an explicit completion fence.

## Build

CPU reference, on macOS/Linux/Windows with CMake and a C++17 compiler:

```sh
cmake -S native/shadow_proof -B build-shadow
cmake --build build-shadow --config Release
ctest --test-dir build-shadow -C Release --output-on-failure
```

Windows additionally requires a Windows SDK with DXR 1.1 headers, the DirectX
Shader Compiler (`dxc.exe`) supporting `cs_6_5`, and a D3D12 driver exposing DXR
Tier1.1 and Shader Model6.5. CMake finds DXC on PATH, or supply its full path:

```powershell
cmake -S native/shadow_proof -B build-shadow -A x64 `
  -DDXC_EXECUTABLE="C:/path/to/Windows SDK/bin/x64/dxc.exe"
cmake --build build-shadow --config Release
ctest --test-dir build-shadow -C Release --output-on-failure
```

The Windows GPU command can also be run directly:

```powershell
build-shadow/Release/shadow_dxr.exe build-shadow/shadow.cso build-shadow/gpu
```

Artifacts are binary PPM images: `reference/cpu-{left,right,unoccluded}.ppm`
and, if the hardware test executes, `gpu/gpu-{left,right,unoccluded}.ppm`.
Inspect the current exit code/log and completion receipt; images left by a failed
run alone are not acceptance evidence. GPU work is deliberately small and finite;
the completion fence has a15-second timeout and CTest has a60-second timeout.

## Route into the game

1. Compile the shader/client and validate real GPU output against the reference.
2. Export one actual static mesh, camera/depth context and a verified light from
   the current renderer. Establish the coordinate system with a debug view.
3. Reproduce one shadow on a verified game receiver, with an enable/disable
   comparison and measured GPU/frame-time cost.
4. Add dynamic geometry only after the static case works; retain the existing
   rendering path when disabled or unsupported.

Steps2–4 remain open. They need new rendering integration beyond the current
addon screen/input hooks. This experiment earns that work by testing the GPU
path first; it does not introduce a general renderer abstraction in advance.

Step1 has passed on the user's Steam Deck under Proton, including actual GPU
readback with zero mismatches in all three cases. See [EVIDENCE.md](EVIDENCE.md).

API behavior follows Microsoft's [DXR specification](https://microsoft.github.io/DirectX-Specs/d3d/Raytracing.html)
and [DXR1.1 inline-raytracing overview](https://devblogs.microsoft.com/directx/dxr-1-1/).
All test geometry and source in this directory are authored for this fork; no
game assets or external sample implementation are included. Existing repository
provenance and licensing notices continue to apply.

## Isolated in-engine experiment

`shadow_dxr shadow.cso output-directory --box` traces a closed box instead of the
original plate. The box spans X/Z ±0.73m and Y 0.07–1.47m. It exports three raw
256×256 little-endian uint32 masks, checks every pixel against a separate AABB
segment test, and writes completion only after all three comparisons pass.
The original plate experiment is unchanged when `--box` is omitted.

The experimental runtime overlay in `nv2a_gpu_shadow_box.inc.c` is disabled by
default. `RECOMP_SHADOW_BOX` names the verified `box-left.mask`. It projects a
matching blue box and ground shadow at X=0, Z=2000cm, using the live c0–c3 camera.
F8 cycles box/shadow, box only, and off. All custom D3D11 bindings invalidate the
normal renderer's state cache so subsequent game draws restore their state.

This deliberately uses a **precomputed hardware ray-traced mask for a fixed box
and light**. It does not ray-trace players, stadium geometry or changing lights,
and is not a real-time DXR renderer. The mask should be generated and verified on
the target hardware before testing. It is an integration experiment, not a
production graphics option or a franchise addon.

Receiver selection uses the captured world-space Y=0 full-field dimensions and
depth-test convention, never a texture/memory address or mod name. Only that
known coordinate convention is supported. This experimental predicate still
needs broader camera/stadium validation; unsupported geometry is skipped.
Use a disposable portable runtime, no franchise addon, copied/read-only assets,
AI/signing disabled, and an isolated Proton prefix. Do not install over a running
game or replace a user's runtime merely to obtain a capture.

`RECOMP_SHADOW_CAPTURE` optionally names a new absolute output prefix. Create
`<prefix>.request` while the field is visible. One bounded frame produces a
JSONL draw/sample record and a presented-target PPM. Existing output is refused.
The CPU vertex-transform path is forced for that capture frame only. Run
`python3 tools/analyze_shadow_capture.py <prefix>.jsonl` to inspect candidate
planes and camera matches. A planar match alone does not validate a 3D box;
the analyzer also checks off-plane samples. Depth testing without depth writes
is valid for the captured field. Geometry behind/crossing the camera is retained
for matrix checks rather than discarded solely by W sign.

## Moving-light experiment

`shadow_dxr shadow.cso output-directory --live-check Local\unique-name 8` keeps
the DXR device, pipeline and acceleration structures loaded, moves the point
light sinusoidally along X, and checks every completed mask against the analytic
box reference. The bounded duration is 1–600 seconds. `--live` uses the same GPU
path without recurring CPU correctness comparisons. `--stop Local\unique-name`
signals that producer to exit. Fresh mapping names prevent an old producer from
being mistaken for a new session.

Set `RECOMP_SHADOW_LIVE=Local\unique-name` alongside `RECOMP_SHADOW_BOX` in the
isolated game process. A Windows shared-memory block and zero-timeout mutex
transfer completed masks from the worker. D3D12 fence waits stay in the worker;
the game copies a fresh completed mask and updates its D3D11 texture. A busy
producer is skipped, and an absent/stale producer hides the shadow after two
seconds. The box and F8 controls continue to work. This uses a measured CPU
readback/copy/upload path, **not shared D3D11/D3D12 GPU resources**.

The target is one update every67ms, approximately15Hz. Logs distinguish worker
publication counts from game-consumed sequences and measure render-thread CPU
copy/upload time. Those timings do not measure total GPU cost. Player/stadium
ray tracing, animated geometry, moving-box acceleration-structure updates and
production graphics settings remain outside this experiment.

On the tested Deck, the compute worker must use the **same X display and Proton
prefix** as the game, while disabling `ENABLE_GAMESCOPE_WSI` and removing its
Steam overlay `LD_PRELOAD`/Gamescope presentation variables. Giving the worker
Gamescope's presentation layer produced a black compositor view even while the
game consumed masks. Moving it to a different X display in the same Wine session
caused an X11 window teardown error. These were launch-environment failures;
neither is hidden as a passing graphics test.

`--resume-live` explicitly resumes an already stopped, stale graphics transport
for testing, preserving its sequence counter. It requires exclusive producer
ownership and a transport older than two seconds; ordinary `--live` still
requires a fresh mapping. This does not enable any AI/franchise controls.

## Reusable tooling

Native Steam recording is now maintained independently in the public MIT-licensed
[steam-capture-tools](https://github.com/cosmokay1/steam-capture-tools) repository
(initial extraction `c4f6c9a`). It takes a Steam game ID, bounded duration and
recovery receipt; it contains no 2K5 assets, runtime paths or franchise policy.
Nine offline lifecycle tests passed at extraction. The original Deck recording
is verified in EVIDENCE.md; the extracted CLI still needs a live acceptance run.

The bounded renderer capture remains in the runtime fork
[cosmokay1/xboxrecomp](https://github.com/cosmokay1/xboxrecomp/tree/codex/shadow-box-live-proof)
at `484a568`, already pinned by this branch. It depends on NV2A/D3D11 renderer
internals, so a separate generic capture library would add coupling without a
current consumer. Companion-process messaging remains independently maintained
in [engine-sidecar](https://github.com/cosmokay1/engine-sidecar).
