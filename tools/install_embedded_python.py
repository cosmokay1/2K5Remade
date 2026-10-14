"""Install a pinned private Windows interpreter; no system install or AI enablement.

Official package and PSF notice are retained. Application modules are reached
through an explicit isolated path; third-party packages must be vendored later.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from urllib.request import urlopen
import zipfile

VERSION = '3.13.16'
URL = f'https://www.python.org/ftp/python/{VERSION}/python-{VERSION}-embed-amd64.zip'
SHA256 = '97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297'


def install(archive: Path, destination: Path, application_root: Path) -> dict:
    import os
    destination, application_root = destination.resolve(), application_root.resolve()
    if destination.exists():
        raise ValueError('Private interpreter destination already exists; refusing overwrite')
    if not (application_root / 'franchise/sidecar.py').is_file():
        raise ValueError('Explicit franchise application root required')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError('Embedded interpreter checksum does not match pinned official release')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.python-stage-', dir=destination.parent) as temporary:
        stage = Path(temporary) / 'python'
        stage.mkdir()
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(stage)
        if not all((stage / name).is_file() for name in ('python.exe', 'python313._pth', 'LICENSE.txt')):
            raise ValueError('Pinned interpreter package lacks required runtime or license')
        relative = os.path.relpath(application_root, destination).replace(os.sep, '\\')
        if any(c in relative for c in '\r\n'):
            raise ValueError('Application path cannot be represented in isolated Python configuration')
        (stage / 'python313._pth').write_text('python313.zip\n.\n' + relative + '\n', encoding='utf-8')
        receipt = {'version': VERSION, 'architecture': 'Windows amd64', 'source_url': URL,
                   'archive_sha256': SHA256, 'application_path_relative': relative,
                   'license': 'LICENSE.txt', 'scope': 'private interpreter; no credentials, inference or control enablement'}
        (stage / 'PROVENANCE.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        # The final directory is absent; staging never replaces a live runtime.
        stage.rename(destination)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--application-root', type=Path, required=True)
    parser.add_argument('--archive', type=Path, help='Verified offline archive; otherwise download pinned official package')
    args = parser.parse_args(argv)
    try:
        if args.archive:
            receipt = install(args.archive, args.destination, args.application_root)
        else:
            with tempfile.TemporaryDirectory(prefix='2k5-python-download-') as temporary:
                archive = Path(temporary) / 'python.zip'
                with urlopen(URL, timeout=45) as response, archive.open('wb') as writer:
                    shutil.copyfileobj(response, writer)
                receipt = install(archive, args.destination, args.application_root)
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        parser.exit(2, f'install_embedded_python: {exc}\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
