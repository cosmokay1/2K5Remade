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

## Optional Windows Google SDK

`requirements-google-windows.lock` pins the 25 wheels selected for Windows amd64
CPython3.13, including google-genai1.75.0 and compiled dependencies. It is separate
from the general development requirements; do not use these platform hashes for
another Python/platform. Wheels are obtained from PyPI and installed with their
dist-info license notices retained. No SDK binaries are committed here.

On a build host with pip, download and stage them in a new private directory:

```sh
python3 -m pip download --index-url https://pypi.org/simple --require-hashes \
  --only-binary=:all: --platform win_amd64 --python-version 3.13 \
  --implementation cp --abi cp313 -r requirements-google-windows.lock \
  --dest private-wheels
python3 -m pip install --no-index --find-links private-wheels --require-hashes \
  --only-binary=:all: --platform win_amd64 --python-version 3.13 \
  --implementation cp --abi cp313 --no-compile \
  -r requirements-google-windows.lock --target dependencies/google-windows-sdk
```

Keep the target absent before staging; retain the wheels' hashes, names and
included license/notice paths in package provenance. Add the relative SDK folder
as a separate line in a private interpreter's `python313._pth`, without enabling
site or user packages. For the example sibling folders this is
`..\google-windows-sdk`. Test with that Windows interpreter:

```sh
pythonw.exe -m tools.check_google_runtime --output sdk-check-result.json
```

The check imports compiled cryptography, validates the response schema,
constructs/closes the actual Vertex SDK client with explicit anonymous fixture
credentials, opens/closes the Requests transport and verifies credential-free
control rejection. It does not discover ADC, contact cloud services, invoke a
model, renew control or authorize a game transaction. A successful SDK packaging
check leaves scoped runtime authentication and actual remote execution pending.
