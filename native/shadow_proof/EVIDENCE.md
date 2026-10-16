# Shadow proof execution evidence

The standalone GPU test executed successfully on the user's Steam Deck through
Proton Experimental, in a separate test prefix. No game assets were loaded and
no game installation, franchise save, sidecar or cloud configuration was changed.
This is an asset-free GPU correctness result, not game integration or a frame-rate
benchmark. The existing D3D11 game renderer remains unchanged.

Windows executable and HLSL compilation used the existing MSVC toolchain and
Windows SDK10.0.26100.0 DXC, targeting `cs_6_5`. The portable CPU reference also
builds and passes CTest on macOS. Actual Windows child output under Proton:

```text
CPU reference only: moved-light, finite-ray, symmetry and clear controls passed; shadow pixels=3364
GPU: AMD VANGOGH; DXR 1.1 and SM 6.5 supported
left: 0 mismatched pixels of 65536
right: 0 mismatched pixels of 65536
unoccluded: 0 mismatched pixels of 65536
```

The logged run returned0 and wrote a fresh `gpu/passed.txt` after the previous
receipt had been removed. The completion text is:

```text
DXR 1.1: all three shadow masks match the CPU reference exactly.
```

SHA256 of the executed artifacts:

| Artifact | SHA256 |
| --- | --- |
| shadow_dxr.exe | 0b62b216d80cf4d5f760bd66284db9bfe407c95de7e2695c0dba4bee7121e961 |
| shadow_reference.exe | a241e2b667438fffdf0b540298f1508a2f9d62c8cf9df17cf8412c513f80bf1e |
| shadow.cso | aed7f40b6e23ef8af8ccf5665e87dd950e995bf31badd65122ffa73820f61ab6 |
| gpu-left.ppm | d735c0a0d00bcffc5b4bf2c30255f06f1c7d401dccba67d6302e1a7e1c65c1f2 |
| gpu-right.ppm | 97b7ef6801f9619cd53c22e10bf4942e858f9a7cf7f6e7a0e20c082aae8bff51 |
| gpu-unoccluded.ppm | 3c52a98469420007f7de67ecda46feb76f2192d39a8d0f50696e7e26c0284bd2 |

Full private receipt, compiler/source manifests and original GPU images are in
`.local-runtime/shadow-proof` and the separate Deck `shadow-proof-a450` stage.
The reproducible source is in this directory; binary releases are not published.
CI compiles the Windows shader/client and runs the portable reference. A CI GPU
test skip on a runner without DXR does not supersede or fabricate hardware evidence.

## In-engine capture checkpoint (2026-10-16)

The separate capture-only game built and passed `--validate` on the Deck under
Proton. The actual D3D11 capture fixture passed, including exclusion of flat 2D
batches, bounded sampling, exact red-target readback and overwrite refusal.
All six offline capture-parser regressions passed locally.

A disposable SOFTDRINK 2K28 v0.6 exhibition reached live play and captured frame
4663, with presented target 2206695424. The PPM visibly contains the field,
players and scoreboard. The normal Steam launcher was restored immediately
after the isolated process started. The private runtime used a blank profile;
original franchise saves were not loaded or copied.

The analyzer matched constants c0-c3 against screen coordinates and captured W,
including 1,725 off-plane sample vertices for one stadium-plane candidate. This
is camera evidence, **not grass receiver identification**: the large planar
candidates include stadium surfaces and orthographic quads. The field draw still
needs identification before applying a shadow. No debug box or ray-traced
shadow has been rendered inside the game yet.

Private artifacts in `.local-runtime/shadow-engine`:

| Artifact | SHA256 |
| --- | --- |
| frame.jsonl | 64ea410fb294c632f1c4ae2a99be383748db8ef82cfe7f386576bdec023391ce |
| frame.ppm | 4d5df36ea33a367fbad2e1a249bf72c5154919754b728ced8131470bddad723a |
| analysis.json | 2833a042ece3b13ba1bcf4bc3f251d27db9c3483cb79f2912950d9d599172f34 |

The capture executable uses a frozen cached game build plus the two-file
renderer capture overlay, recorded in the private source manifest. It is not
claimed to be a full game build of this parent worktree's HEAD.

## Fixed box integration checkpoint (2026-10-16)

The later isolated game build rendered the matching closed blue box and its
hardware-traced shadow on the actual SOFTDRINK field. Captured controls show
box+shadow, box only and both off at the same camera. A second camera view also
shows the object/shadow anchored to the field. The logged receiver draw began
at frame4698, target83710000. This supersedes the capture-only checkpoint above.

The full-field draw tests depth without writing it. Its captured Y=0 bounds
are X ±2926.08008, Z ±5852.16016, with c0–c3 matching 1,518 off-plane samples.
The first box geometry run rejected two boundary pixels; that failed receipt
was retained. The revised box uses ±0.73m, Y0.07–1.47m and passed all65,536 pixels
for each of left/right/unoccluded on AMD VANGOGH. No mismatch allowance was added.

Verified fixed mask SHA256:
`4e2dc87209a84a0ff062b064e225221c8d01553c415768071d3e80e6602ed4af`.
Screenshots are private in `.local-runtime/shadow-engine/boxon.png`,
`boxonly.png`, `boxoff.png`, `boxplay.png` and `frame-box.png`.
One ten-second engine sample reported60.0FPS, low1%59.3 and low0.1%58.9. That is
smoke evidence for this fixed-mask case, not a controlled performance benchmark.
A window-close request did not terminate that private game; the exact scoped
process was subsequently stopped before replacing the private executable.

## Moving-light hardware checkpoint (2026-10-16)

The persistent DXR worker completed121 moving-light masks in8.044seconds on
AMD VANGOGH, with every mask independently checked and zero mismatches. The
light traversed both X extremes. Private receipt:
`.local-runtime/shadow-engine/live-check-receipt.json` (copied after execution).
The bounded test was repeated after adding explicit worker shutdown.
This verifies live GPU mask production; it does not alone verify game consumption.

## Live in-engine and recording checkpoint (2026-10-16)

The game consumed thousands of fresh moving-light sequences. The final clear
recording uses the original game's replay camera, held at the start of the play:
the box stays still while its shadow changes direction, followed by box-only,
fully-off, and restored states. The14-second H.264 MP4 is1280×800 and resides at
`.local-runtime/shadow-engine/clear-video/dynamic-shadow.mp4`. Its33 actual
Gamescope captures use measured timestamps;15FPS encoding repeats captures and
does not claim15FPS screen-capture throughput. No generated/interpolated frames
or audio were added. Earlier cutaway/clipped-box attempts were not used as the
final demonstration.

At4,620 consumed updates, measured render-thread CPU copy/upload averaged0.072ms
and peaked at1.076ms. Worker publication targeted67ms intervals. Engine samples
included57.6,57.9 and60.0FPS, with recording-related frame-time dips; these are
smoke measurements, not a controlled total-GPU-cost benchmark. The explicit
three-minute producer completed at180.035seconds, advancing from sequence5064
to7752. Runtime logging and the video verify live consumption; the bounded
correctness run separately checked every one of121 masks.

The first concurrent game boot hit the previously observed guest divide-by-zero
fault before the field; its log was preserved and an unchanged retry booted.
Gamescope presentation inheritance and a mismatched X display were diagnosed and
corrected as described in the README. A stopped producer's stale shadow
vanished while the box remained; explicit resume restored live updates.

Video quality correction: the screenshot-based clip is diagnostic evidence only.
The user correctly rejected its low capture frame rate. Its15FPS stream header
is not15FPS of distinct captured images. A replacement using a real-time screen
capture path is required; do not present that screenshot sequence as a smooth
video or a frame-rate demonstration. The Deck was unreachable when replacement
capture setup began.

## Replacement real-time recording (2026-10-16)

The low-rate screenshot sequence was replaced with Steam's native continuous
recorder, temporarily set to on-demand60FPS. A rejected direct PipeWire format
negotiation stopped the compositor's recording source; restarting the supported
`gamescope-session.target` restored it. Native recording then received actual
video. Its separate intro test decoded1,790 frames with521 distinct downscaled
images and1,182 adjacent image changes.

The delivered replacement is `.local-runtime/shadow-engine/native-video/dynamic-shadow-60fps.mp4`:
20.000175seconds,1,200 decoded H.264 frames,1280×800, approximately60FPS,
13,576,897bytes. It is a lossless remux of the first20seconds of native capture,
with no screenshot sampling, motion interpolation or audio. Extracted frames
show the fixed box's shadow changing with the moving light. The producer still
runs at the experiment's15Hz target; recording60FPS does not change that rate.
SHA256: `47cadf2ffce71ec56389a23298ef09957595a43158c5bf07e36771073823c60b`.

The original launcher and all205 original saves were hash-verified unchanged.
The exact disposable game was stopped and Steam's previous recording mode0
(disabled) restored. The separate long full-clip export was unnecessary; the
completed short replacement was saved before restarting Steam normally to
cancel that extra encoding work.
