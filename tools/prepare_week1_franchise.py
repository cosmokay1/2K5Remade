"""Prepare a NEW isolated cap-bound hybrid from a game-created fresh save.

Never edit the supplied save, an existing database, or MyNFL1. This prepares a
copy for guarded installation after normal exit; it does not activate AI/signing.
"""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import secrets

from tools.build_week1_opening import build_opening
from tools.create_franchise import create_from_file
from franchise.opening_native import build,register
from franchise.snapshot_origin import bind as bind_origin
from franchise.store import FranchiseStore


def prepare(save,roster,fit,assembly,charges,cap_book,archive,output,*,loaded_image_sha256=None):
    save,output=Path(save),Path(output)
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(save.parent.resolve()):
        raise ValueError('New destination outside the source save container required')
    metadata={n:(save.parent/n).read_bytes() for n in ('TYPE','SaveMeta.xbx','EXTRA')}
    name=metadata['SaveMeta.xbx'].decode('utf-16').strip('\0\r\n').removeprefix('Name=')
    if name.casefold()=='mynfl1' or 'mynfl1' in [p.casefold() for p in save.parts]:
        raise ValueError('MyNFL1 is protected; use a newly created isolated franchise')
    if metadata['TYPE'].decode('utf-16le').rstrip('\0')!='FXG':
        raise ValueError('Game-created FXG franchise container required')
    payload=save.read_bytes();roster=Path(roster).read_bytes()
    if not hmac.compare_digest(metadata['EXTRA'],hmac.digest(bytes(16),payload,'sha1')):
        raise ValueError('Valid native PC save signature required')
    paths=[Path(p) for p in (fit,assembly,charges,cap_book,archive)]
    raw=[p.read_bytes() for p in paths];data=[json.loads(b) for b in raw]
    bundle,bindings,report=build_opening(payload,roster,*data[:4],data[4]['rows'],seed=secrets.token_hex(32),
        loaded_image_sha256=loaded_image_sha256)
    output.mkdir(parents=True,exist_ok=False)
    bootstrap=output/'bootstrap.json';bootstrap.write_text(json.dumps(bundle,indent=2)+'\n')
    (output/'bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
    database=output/'franchise.sqlite';creation=create_from_file(bootstrap,database);store=FranchiseStore(database)
    adjusted,proof=build(store,bindings,payload,source={p.name:hashlib.sha256(b).hexdigest() for p,b in zip(paths,raw)})
    register(store,proof,adjusted);bind_origin(store,bindings,adjusted)
    container=output/'save';container.mkdir()
    for n,b in dict(metadata,**{'SAVEGAME.DAT':adjusted,'EXTRA':hmac.digest(bytes(16),adjusted,'sha1')}).items():
        (container/n).write_bytes(b)
    manifest=save.parent/'.nfl2k5-save.ini'
    if manifest.exists():(container/manifest.name).write_bytes(manifest.read_bytes())
    if save.read_bytes()!=payload or any((save.parent/n).read_bytes()!=b for n,b in metadata.items()):
        raise ValueError('Source save changed during preparation; candidate must not be installed')
    (output/'opening-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    receipt=dict(format=1,save_name=name,source_save_sha256=hashlib.sha256(payload).hexdigest(),
        output_save_sha256=hashlib.sha256(adjusted).hexdigest(),bootstrap=creation,opening=report,
        source_unchanged=True,installed=False,game_load_verified=False,signing_authorized=False)
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('save','roster','fit','assembly','charges','cap-book','archive','output'):
        parser.add_argument('--'+name,required=True,type=Path)
    parser.add_argument('--loaded-image-sha256',help='Explicit observed load-input hash for required runtime handshake')
    args=parser.parse_args()
    r=prepare(args.save,args.roster,args.fit,args.assembly,args.charges,args.cap_book,args.archive,args.output,
        loaded_image_sha256=args.loaded_image_sha256)
    print(json.dumps({k:v for k,v in r.items() if k not in ('bootstrap','opening')},indent=2))


if __name__=='__main__':main()
