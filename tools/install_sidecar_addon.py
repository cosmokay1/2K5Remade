"""Install only the franchise DLL into an explicitly compatible Remade host.

Package manifests are trusted release inputs, not signatures. Close the game first.
No host patching, activation, service configuration or game assets are included.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def install(package, game_root):
    package, root = Path(package).resolve(), Path(game_root).resolve(strict=True)
    spec = json.loads((package / 'addon-package.json').read_text())
    required = {'format', 'supported_host_sha256', 'dll_sha256'}
    if not isinstance(spec, dict) or set(spec) != required or type(spec['format']) is not int or spec['format'] != 1:
        raise ValueError('Unsupported addon package manifest')
    hosts = spec['supported_host_sha256']
    hashes = [spec['dll_sha256']]
    if not isinstance(hosts, list) or not hosts:
        raise ValueError('Explicit compatible host hashes required')
    hashes += hosts
    if any(not isinstance(h, str) or not re.fullmatch('[0-9a-f]{64}', h) for h in hashes):
        raise ValueError('Invalid SHA256')
    host = root / 'NFL2K5.exe'
    if host.is_symlink() or not host.is_file():
        raise ValueError('Expected a regular NFL2K5.exe')
    host_hash = digest(host.read_bytes())
    if host_hash not in hosts:
        raise ValueError('Unsupported native host; install a verified addon-capable build first')
    source = package / 'franchise-addon.dll'
    if source.is_symlink() or not source.is_file():
        raise ValueError('Expected a regular package DLL')
    payload = source.read_bytes()
    if digest(payload) != spec['dll_sha256']:
        raise ValueError('Package DLL checksum mismatch')
    pe = struct.unpack_from('<I', payload, 0x3c)[0] if len(payload) >= 64 else len(payload)
    if (payload[:2] != b'MZ' or pe < 64 or pe + 24 > len(payload)
            or payload[pe:pe + 4] != b'PE\0\0'
            or struct.unpack_from('<H', payload, pe + 4)[0] != 0x8664
            or not struct.unpack_from('<H', payload, pe + 22)[0] & 0x2000):
        raise ValueError('Package requires an AMD64 Windows DLL')
    destination = root / 'addons' / 'franchise' / 'franchise-addon.dll'
    for path in (destination.parent.parent, destination.parent, destination):
        if path.is_symlink():
            raise ValueError('Addon installation paths must not be symlinks')
    previous = destination.read_bytes() if destination.exists() else None
    receipt = {'host_sha256': host_hash, 'dll_sha256': spec['dll_sha256'],
               'previous_sha256': digest(previous) if previous is not None else None,
               'changed': previous != payload}
    if previous == payload:
        return receipt
    destination.parent.mkdir(parents=True, exist_ok=True)
    if previous is not None:
        backup = destination.with_name('franchise-addon.previous-' + digest(previous) + '.dll')
        if backup.is_symlink():
            raise ValueError('Addon backup must not be a symlink')
        if backup.exists():
            if backup.read_bytes() != previous:
                raise ValueError('Existing addon backup checksum mismatch')
        else:
            with backup.open('xb') as stream:
                stream.write(previous)
    # Replace one file only. A failed replace (e.g. a loaded DLL on Windows)
    # leaves the installed DLL and selection intact; retain the previous backup.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.addon-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--game-root', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.package, args.game_root), indent=2))
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
