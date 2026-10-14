# SDL3 build dependency

The cross-platform recompiler requires SDL3. CI builds the official SDL
release-3.2.20 source, pinned at 96292a5b464258a2b926e0a3d72f8b98c2a81aa6,
and installs an SDK privately within the job before configuring the runtime.
This avoids unavailable distro packages and an absent Windows SDK.

Source: https://github.com/libsdl-org/SDL/tree/96292a5b464258a2b926e0a3d72f8b98c2a81aa6
The exact source license is retained in sdl3-LICENSE.txt. Preserve its notice
when distributing SDL with a future permitted runtime. No SDL source/library
or retail assets are included in our source artifact by this workflow; no
playable game or binary release is implied by the SDK/runtime build.
