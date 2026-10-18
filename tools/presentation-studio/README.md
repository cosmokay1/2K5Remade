# Presentation Studio on Linux and Steam Deck

The existing browser editor works with Python 3.9+ using only the standard
library. No Proton, game rebuild or cloud service is needed for the editor.

From a source checkout:

```sh
python3 tools/presentation-studio/serve.py
```

For a separate installed game directory:

```sh
python3 tools/presentation-studio/serve.py --presentations /path/to/game/mods/presentations
```

Open `http://127.0.0.1:8735/`. The server accepts connections only from this
computer. Ctrl+C stops it. `--no-browser` suppresses automatic browser opening;
`--port` selects another port. The server serves only the editor and presentation
web files, and writes stay within HTML presentation packages.

On the Deck, use **Desktop Mode** and double-click **Presentation Studio** on
the desktop (approve Execute if KDE asks). Its terminal must stay open while
editing; closing it stops the server. A second click reopens the existing editor.
Use a trackpad or mouse; this is a desktop editor rather than a controller UI.

Select **NBC Sunday Night Football** for a complete HTML broadcast package.
Select an element in the preview to move/resize it or change its properties.
Use **Save layout** to persist those changes. Asset imports and code saves also
write directly to the selected package. Reload the presentation in the game
after saving; choose it through Coach Match Up → Presentation, or cycle with F2.
Menu selection and in-game rendering still need verification on the installed build.

Presentation Studio edits **HTML** packages, including their scorebugs and other
broadcast graphics. Native JSON presentation themes do not appear in its package
list. It does not convert native themes to HTML.

## Current private Deck installation

Tool: `/home/deck/.local/share/2k5-franchise-build/presentation-studio`.
The desktop shortcut points at the shared game folder
`manager-addon-5605345/runtime/mods/presentations` under the same build directory.
The simulation profile links to that folder too. Existing source packages were
copied into the missing game presentation directory; no assets were downloaded.
Original presentations are backed up as `original-presentations.tar.gz` in the
tool directory. Saves, game settings, binaries and AI controls were not edited.

Validation: six HTTP regression tests cover the editor protocol, import, layout,
asset/code writes, traversal/symlink restrictions and cross-origin write rejection.
On the Deck, both installed HTML entry pages, the shared presentation runtime and
a disposable layout save/readback passed. The temporary package was removed.
Browser interaction and the edited presentation's in-game appearance require
user confirmation; HTTP checks alone do not establish those results.
