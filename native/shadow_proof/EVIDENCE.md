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
