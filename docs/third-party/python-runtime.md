# Private Python sidecar runtime

Pinned runtime: CPython 3.13.16, Windows amd64 embeddable package, from the
[official release](https://www.python.org/downloads/release/python-31316/).
Archive SHA256:
`97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297`.

`tools.install_embedded_python` verifies that exact archive before extracting to
an absent private destination. It retains `LICENSE.txt` and writes
`PROVENANCE.json`. The runtime is distributed under its included PSF/license
notices. No game assets, credentials or control grants are included by this tool.
No system interpreter, registry or PATH installation is performed.

The isolated `python313._pth` contains the standard-library ZIP, interpreter
folder and an explicit relative application root. It does not enable `site` or
user-installed packages. This follows the
[embeddable application guidance](https://docs.python.org/3.13/using/windows.html#the-embeddable-package).
Optional third-party SDK packages must be deliberately vendored with their
notices and validated; pip is not installed into the embedded interpreter.

Example, from a private package root containing `source/franchise/sidecar.py`:

```sh
python3 source/tools/install_embedded_python.py dependencies/python-3.13.16 \
  --application-root source --archive dependencies/python-3.13.16-embed-amd64.zip
```

Existing destinations reject overwrite. This is interpreter packaging only:
the game still needs explicit provider/database configuration, authorized runtime
credentials, a valid remote control grant and verified real-franchise import.
Running the synthetic native fixture does not establish game AI integration.
