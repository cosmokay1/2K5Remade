"""Create an initialized franchise DB from declared source-backed team configs."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from franchise.store import FranchiseStore,from_config

MAX_INPUT = 16 * 1024 * 1024


def unique_object(pairs):
    result = {}
    for key,value in pairs:
        if key in result:
            raise ValueError('Duplicate bootstrap JSON field')
        result[key] = value
    return result


def create_from_file(input_path,database_path):
    with Path(input_path).open('rb') as incoming:
        raw = incoming.read(MAX_INPUT+1)
    if len(raw) > MAX_INPUT:
        raise ValueError('Bootstrap exceeds 16 MiB')
    bundle = json.loads(raw,object_pairs_hook=unique_object)
    if type(bundle) is not dict or set(bundle) != {'format','source','seed','teams'} or type(bundle['format']) is not int or bundle['format'] != 1:
        raise ValueError('Unsupported franchise bootstrap fields/version')
    if type(bundle['source']) is not str or not bundle['source'].strip() or type(bundle['teams']) is not dict or not bundle['teams']:
        raise ValueError('Declared import source and nonempty team configs required')
    if any(type(config) is not dict for config in bundle['teams'].values()):
        raise ValueError('Each team config must be a JSON object')
    teams = {team:from_config(config) for team,config in bundle['teams'].items()}
    destination = Path(database_path).absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Refusing to overwrite an existing franchise')
    digest = hashlib.sha256(raw).hexdigest()
    # Publish only the complete replay-verified DB, with an atomic no-replace link.
    with tempfile.NamedTemporaryFile(prefix='.2k5-bootstrap-',suffix='.sqlite',dir=destination.parent,delete=False) as temporary:
        building = Path(temporary.name)
    try:
        store = FranchiseStore(building)
        origin = store.create_franchise(teams,seed=bundle['seed'])
        with closing(sqlite3.connect(building)) as db:
            db.execute("INSERT INTO franchise_metadata VALUES ('bootstrap-source',?)",
                       (json.dumps({'source':bundle['source'],'input_sha256':digest,'format':1}),))
            db.commit()
        for team in teams:
            store.load_team(team)  # Original charges, ownership, actor coverage.
        os.link(building,destination)  # EEXIST also protects concurrent creators.
        return {'database':str(destination),'teams':len(teams),
                'players':len(set().union(*(ledger._veteran_minimums.keys() | ledger._rookies.keys() for ledger in teams.values()))),
                'personality_version':origin['version'],'input_sha256':digest,'game_runtime_verified':False}
    finally:
        for suffix in ('','-journal','-wal','-shm'):
            building.with_name(building.name+suffix).unlink(missing_ok=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True)
    parser.add_argument('--database',required=True)
    args=parser.parse_args()
    print(json.dumps(create_from_file(args.input,args.database),indent=2))


if __name__ == '__main__':
    main()
