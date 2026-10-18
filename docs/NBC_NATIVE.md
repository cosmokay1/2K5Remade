# NBC SNF without WebView2

The Deck's WebView2 composition/capture path failed before producing a frame.
NBC now has a native `presentation.json` alongside its existing HTML Studio
preview. The existing loader prefers this native definition, retaining the same
package folder and display name. There is no silent switch to another network.

The native definition uses the original NBC `pod.png`, `rail.png` and away/home
alpha masks, the original 576px design coordinates, live team colours and logos,
silver text gradients, split quarter label, possession tabs and timeout markers.
Packaged team logos use the same legacy-to-modern abbreviation aliases as the
HTML source, with the original team-logo fallback where an NBC logo is absent.
The native renderer adds alpha-mask fills, cropped image windows and text
gradients. Original optional broadcast fonts are not redistributed; Arial Black
matches the HTML package's existing substitute font. Existing private artwork
and upstream attribution remain intact. Missing required plates prevent loading
the package rather than offering a text-only version.

Scores, both clocks, downs, possession and timeouts come directly from the game's
existing state reader. Play-clock changes are now included in the native frame
signature even when the period clock is stopped. No timer addresses, CPU presets,
franchise rules or save data are changed.

The HTML sources remain available for editing/reference; this does not execute
HTML in the native renderer. Full HTML pregame cinematics and every scoring
animation are not claimed to have visual parity. Native scorebug events use
silver/glass text inserts; title-provided player/lineup cards remain enabled
rather than being hidden for an unavailable browser replacement.

## Acceptance

The Windows render fixture uses the actual Direct2D renderer. Its browser factory
throws if called. With private NBC media supplied, it renders NBC, FOX and CBS,
compares output with HTML support enabled/disabled, and changes only the play
clock while holding the period clock fixed. Source-only CI can omit private NBC
media; that is a skip for NBC rendering, not an asset-complete pass.

Compilation and fixture pixels do not establish live gameplay or style acceptance.
The final Deck check must select NBC in the actual game, confirm the original
artwork, watch the play clock count down before a snap, exercise a score/timeout,
and check hide/return through play calling. Ask the user what is visible; do not
capture the Deck screen. Keep the scheduled task off.

October 17 candidate: `ee2c2fd6d72d1d9c91fc82c9aa7a834c4cbdd77bd9406baca6bc2c1671c85254`.
Final native and HTML-enabled fixture executables both rendered NBC using all
required original plates: 565x221 BGRA surface, 36,346 coloured pixels. Geometry
and pixel buffers match between the two builds. Changing the authored timer
from 40 to 39 with the period clock held at 13:11 produced a new frame and
different pixels. The browser factory is fail-on-use in both fixtures. NBC's
private media had to be linked into the fixture explicitly; a source-only run
that skipped NBC was rejected rather than counted as passing NBC coverage.
The isolated game `--validate` also passed with a fresh child completion marker.
Studio's seven HTTP compatibility checks pass. No live installation or gameplay
acceptance is implied: candidate is staged pending the user's normal game exit.
Private receipts/artifacts are under Deck `nbc-native-v1/` and local
`.local-runtime/nbc-native-v1/`; original media remains untracked/private.

Upstream redraw fix submitted separately as draft [PR #10](https://github.com/BeyondTomrrow/2K5Remade/pull/10), two added lines only. Fresh upstream CI is not claimed.
