"""Prepare an isolated roster trial using an actual native ROS container.

BAD-AL documents the shared PS2/Xbox ROST record layout. A valid signature and
PC-library import do not prove title-level loading. Preserve the game-created
container ID, type and SaveMeta bytes; change only ROST payload and its HMAC.
Never apply the output to an existing container or the user's main profile.
"""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re

from tools.inspect_roster_save import inspect_roster


def prepare_roster(source, destination, *, expected_sha256, source_url, native_template):
    source, destination, native_template = Path(source), Path(destination), Path(native_template)
    payload = source.read_bytes(); digest = hashlib.sha256(payload).hexdigest()
    if not re.fullmatch('[0-9a-f]{64}', expected_sha256) or digest != expected_sha256:
        raise ValueError('Roster differs from pinned input')
    if not source_url.startswith('https://'):
        raise ValueError('Explicit HTTPS creator source required')
    report = inspect_roster(payload)
    template_bytes = native_template.read_bytes(); inspect_roster(template_bytes)
    parent = native_template.parent
    template = {name:(parent/name).read_bytes() for name in ('TYPE','EXTRA','SaveMeta.xbx','.nfl2k5-save.ini')}
    if template['TYPE'].decode('utf-16le').rstrip('\0') != 'ROS':
        raise ValueError('Reference must be the game-created standalone ROS container')
    if not hmac.compare_digest(template['EXTRA'], hmac.digest(bytes(16),template_bytes,'sha1')):
        raise ValueError('Reference must have a valid PC-runtime signature')
    fields = dict(line.split('=',1) for line in template['.nfl2k5-save.ini'].decode().splitlines() if '=' in line)
    name,container = fields.get('name',''),fields.get('container','')
    if (fields.get('format')!='1' or fields.get('type')!='ROS' or
            not re.fullmatch('[A-F0-9]{12}',container) or not re.fullmatch('[A-Za-z0-9]{1,7}',name)):
        raise ValueError('Bound native container manifest required')
    metadata=template['SaveMeta.xbx'].decode('utf-16').rstrip('\0\r\n')
    if metadata!='Name='+name:raise ValueError('Native metadata and manifest name differ')
    destination.mkdir(parents=True,exist_ok=False)
    files={'SAVEGAME.DAT':payload,'EXTRA':hmac.digest(bytes(16),payload,'sha1'),
           'TYPE':template['TYPE'],'SaveMeta.xbx':template['SaveMeta.xbx']}
    for relative in (Path('saves/rosters')/name,Path('saves/UDATA/53450030')/container):
        out=destination/relative;out.mkdir(parents=True)
        for filename,data in files.items():
            with (out/filename).open('xb') as writer:writer.write(data)
    (destination/'saves/rosters'/name/'.nfl2k5-save.ini').write_bytes(template['.nfl2k5-save.ini'])
    if source.read_bytes()!=payload or native_template.read_bytes()!=template_bytes:
        raise ValueError('Source/reference changed during packaging')
    if any((parent/n).read_bytes()!=data for n,data in template.items()):
        raise ValueError('Reference metadata changed during packaging')
    receipt={'source_url':source_url,'source_sha256':digest,'save_name':name,'container':container,
        'native_type':'ROS','native_template_sha256':hashlib.sha256(template_bytes).hexdigest(),
        'roster_payload_preserved':True,'native_container_metadata_preserved':True,
        'pc_signature_verified':True,'roster':report,'live_installed':False,
        'game_load_verified':False,'fresh_franchise_verified':False,'cap_reconciled':False}
    (destination/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
    p.add_argument('--sha256',required=True);p.add_argument('--source-url',required=True)
    p.add_argument('--native-template',type=Path,required=True);a=p.parse_args()
    r=prepare_roster(a.source,a.destination,expected_sha256=a.sha256,source_url=a.source_url,native_template=a.native_template)
    print(json.dumps({k:v for k,v in r.items() if k!='roster'},indent=2))


if __name__=='__main__':main()
