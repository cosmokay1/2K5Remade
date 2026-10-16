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
