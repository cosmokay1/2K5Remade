# Native style comparison

This executes the existing Direct2D FOX/CBS renderer with authored test match
state, comparing its CPU BGRA pixels and HUD placement with HTML support compiled
in and out. The enabled variant has a fail-on-use browser factory: neither
executable links WebView2. No game/retail assets, game window or AI are needed.
The fixture waits for unchanged frames after font initialization and the entrance
fade; a fixed wall-clock delay can capture different intermediate animation frames.

On Windows:

    cmake -S native/presentation -B build-presentation
    cmake --build build-presentation --config Release
    ctest --test-dir build-presentation -C Release --output-on-failure

Outputs are under `build-presentation/rendered`. Package logos missing from the
repository remain missing in both variants; this is not a replacement for an
asset-complete gameplay review or an animation comparison. Original renderer,
package geometry, colors, fonts, image paths and animation code are retained.

The game build accepts `-DNFL2K5_HTML_PRESENTATIONS=OFF` to omit the WebView2
implementation, SDK requirement and loader library. That build lists native JSON
packages only and logs skipped HTML packages. The option defaults to ON while
NBC's HTML package still needs a visually verified native equivalent. Keep the
installed game's selected presentation intact until that work passes.

This is a Windows renderer check (also runnable in an isolated Proton prefix).
It does not port Direct2D, the game or the franchise adapter to Linux.
