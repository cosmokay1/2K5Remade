# Installing the franchise sidecar DLL on a pinned Remade host

The native host must already contain the loader, compatible callbacks and manager
row. This installer does not convert an arbitrary repack or patch NFL2K5.exe.
Its current destination is addons/franchise/franchise-addon.dll; a general addon
registry and domain-neutral game ABI remain separate work.

Close the game before installing or upgrading. A trusted private package contains:

- franchise-addon.dll, built and tested for the listed hosts;
- addon-package.json, with exactly these fields:

```json
{
  "format": 1,
  "supported_host_sha256": ["<64 lowercase hex characters from a verified NFL2K5.exe>"],
  "dll_sha256": "<64 lowercase hex characters from the tested franchise-addon.dll>"
}
```

Run with Python3.10 or newer:

```sh
python -m tools.install_sidecar_addon --package /path/to/package --game-root /path/to/game
```

A package author lists only host executable hashes actually validated with that
DLL. Hashes check package integrity and exact compatibility selection; they are
not signatures or evidence of who supplied a package. Addons are trusted native
code, and the runtime still checks the exported ABI before starting one.

The installer rejects unlisted hosts, corrupt/non-AMD64 DLLs and symlinked addon
paths before replacing files. Upgrades retain the previous DLL in the addon folder
under a name containing its SHA256. Replacement is atomic; failure to replace a
loaded/locked DLL leaves the installed DLL intact. Reinstalling identical bytes
is a no-op. Output records host, new and previous DLL hashes.

It does not write saves, content packs, manager selection, launcher, host EXE,
credentials or service configuration. A new install remains Off; an upgrade retains
its existing selection. Start the game and use Options > Mod Packs to select the
addon. On - restart means the next launch will use that selection; On without the
suffix means the selected addon is loaded in this session. AI configuration and
remote authorization belong to the franchise application and remain independent.

No retail files or compiled releases are included here. Original addon reuse
licensing is still undecided; preserve Remade and third-party provenance.
