"""Create a local Proton candidate ZIP from an explicit runtime file manifest."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def package(root, manifest, output):
    root = Path(root).resolve()
    spec = json.loads(Path(manifest).read_text())
    if set(spec) != {'entrypoint', 'files'} or not isinstance(spec['files'], list):
        raise ValueError('Manifest requires entrypoint and files')
    paths = spec['files']
    if not paths or any(not isinstance(p, str) or not p for p in paths):
        raise ValueError('Explicit runtime files required')
    if any(p.split('/')[0].casefold() == 'package-receipt.json' for p in paths):
        raise ValueError('Reserved receipt path')
    if len(set(p.casefold() for p in paths)) != len(paths):
        raise ValueError('Duplicate Windows paths')
    if spec['entrypoint'] not in paths or not spec['entrypoint'].lower().endswith('.exe'):
        raise ValueError('Entrypoint must be an included Windows executable')
    folded_paths = {name.casefold() for name in paths}
    directory_spellings = {}
    for name in paths:
        parts = name.casefold().split('/')
        if any('/'.join(parts[:length]) in folded_paths for length in range(1, len(parts))):
            raise ValueError('Windows file/directory path collision')
        original_parts = name.split('/')
        for length in range(1, len(original_parts)):
            prefix = '/'.join(original_parts[:length])
            prior = directory_spellings.setdefault(prefix.casefold(), prefix)
            if prior != prefix:
                raise ValueError('Use consistent directory casing for portable extraction')
    payload = []
    for name in paths:
        p = PurePosixPath(name)
        if p.is_absolute() or any(x in ('', '..', '.') for x in name.split('/')) or '\\' in name or ':' in name:
            raise ValueError('Use relative POSIX runtime paths')
        if any(x.startswith('.') for x in p.parts) or p.suffix.lower() in ('.pem', '.key', '.sqlite', '.db'):
            raise ValueError('Private configuration, keys and existing saves are excluded')
        reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10)),
                    *(prefix + digit for prefix in ('COM', 'LPT') for digit in '¹²³')}
        if any(x.endswith((' ', '.')) or x.split('.')[0].upper() in reserved or any(c in x for c in '<>"|?*') or any(ord(c) < 32 for c in x) for x in p.parts):
            raise ValueError('Invalid Windows runtime path')
        source = root.joinpath(*p.parts)
        if any(parent.is_symlink() for parent in [source, *source.parents] if parent != root.parent):
            raise ValueError('Symlink runtime paths are excluded')
        if not source.is_file() or not source.resolve().is_relative_to(root):
            raise ValueError('Missing runtime file')
        if source.resolve() == Path(output).resolve():
            raise ValueError('Output cannot be an input file')
        payload.append((name, source))
    receipt = {'format': 1, 'status': 'unverified-proton-candidate',
               'entrypoint': spec['entrypoint'], 'sha256': {}}
    # Stream game-sized files and hash exactly the bytes archived.
    with Path(output).open('xb') as target:
        try:
            with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
                for name, source in payload:
                    digest = hashlib.sha256()
                    with source.open('rb') as incoming, archive.open('LLM-2K5/' + name, 'w', force_zip64=True) as outgoing:
                        while chunk := incoming.read(1024 * 1024):
                            digest.update(chunk)
                            outgoing.write(chunk)
                    receipt['sha256'][name] = digest.hexdigest()
                archive.writestr('LLM-2K5/package-receipt.json', json.dumps(receipt, indent=2))
        except BaseException:
            target.close()
            Path(output).unlink()
            raise
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    package(args.root, args.manifest, args.output)
