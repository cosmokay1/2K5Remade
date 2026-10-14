# Steam Deck delivery

Delivery route: portable Windows runtime launched by Steam through Proton. This
is a candidate packaging route; neither gameplay nor the native franchise pipe
has been tested under Proton. The current repository does not build an integrated
playable game without the reviewed guest integration and legal assets.

The local packager accepts an explicit manifest, preserves relative file paths,
records SHA-256 hashes and refuses to overwrite an existing ZIP. It rejects
case-insensitive file/directory collisions, inconsistent directory-prefix spelling
and descendants of the reserved receipt file. Directory casing stays consistent
so extraction on a case-sensitive filesystem does not split one Windows logical
directory. Win32 reserved device names include superscript COM/LPT variants; see
[Microsoft naming rules](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file). It does not fetch
assets, install Proton, create credentials or publish a release. Inspect every
listed file for credentials before packaging; filename checks cannot establish
that arbitrary JSON or executable contents are safe to distribute. Redistribution
requires the permissions recorded in FORK_NOTICE.md.

Example manifest for a future verified runtime (filenames are illustrative):

```json
{"entrypoint":"Game.exe","files":["Game.exe","runtime.dll"]}
```

Include the actual runtime dependencies and legally supplied assets explicitly.
Build locally with:

```sh
python3 tools/package_steamdeck.py --root /path/to/runtime --manifest /path/to/runtime-files.json --output /path/to/LLM-2K5-deck.zip
```

On Deck, extract the ZIP in Desktop Mode, add the manifest's executable as a
non-Steam game, set its working directory to its containing folder and select a
Valve Proton compatibility tool in Steam Properties. Record the tested Proton
version rather than promising compatibility with an untested version.

Acceptance requires actual Deck execution: launch in Gaming Mode, controller-only
navigation, readable 1280x800 UI, gameplay/frame pacing, franchise negotiation and
draft, exact cap/rookie accounting, save/load/restart, suspend/resume, offline and
remote-switch-disabled recovery. Test the Win32 child-process pipe and job-object
cleanup under Proton. A portable Windows Python runtime and provider dependencies
must be validated if the game still launches the Python sidecar; a macOS/Linux
virtual environment cannot be copied as its Windows runtime. Cloud authentication
must use the restricted runtime identity, never bundled administrator credentials.

Sources: [Valve compatibility requirements](https://partner.steamgames.com/doc/steamhardware/compat)
and [Valve Proton](https://github.com/ValveSoftware/Proton).
