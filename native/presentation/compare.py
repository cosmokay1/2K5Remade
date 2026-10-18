"""Compare actual retained native style output with/without HTML support."""
import hashlib
from pathlib import Path
import subprocess
import sys

native,legacy,root,output=sys.argv[1:]
output=Path(output).resolve()
for label,executable in (('native',native),('legacy',legacy)):
    folder=output/label
    folder.mkdir(parents=True,exist_ok=True)
    for pattern in ('*.txt','*.bgra'):
        for previous in folder.glob(pattern):previous.unlink()
    subprocess.run([str(Path(executable).resolve()),str(Path(root).resolve()),str(output/label)],check=True,timeout=12)
styles=sorted(p.stem for p in (output/'native').glob('*.txt'))
assert {'0','1'}<=set(styles)
assert set(styles)=={p.stem for p in (output/'legacy').glob('*.txt')}
for style in styles:
    for suffix in ('.txt','.bgra'):
        first=(output/'native'/(style+suffix)).read_bytes()
        second=(output/'legacy'/(style+suffix)).read_bytes()
        if not first or first!=second:
            raise SystemExit(f'Native style {style}{suffix} changed when browser support was removed')
    print(f'Style {style}: identical geometry/BGRA; sha256='+hashlib.sha256(first).hexdigest())
print('Native styles retain identical pixels without WebView')
