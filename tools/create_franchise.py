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
from franchise.cash import CashObligation

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
    required = {'format','source','seed','teams'}
    if type(bundle) is not dict or set(bundle) not in (required, required | {'cash'}) or type(bundle['format']) is not int or bundle['format'] != 1:
        raise ValueError('Unsupported franchise bootstrap fields/version')
    if type(bundle['source']) is not str or not bundle['source'].strip() or type(bundle['teams']) is not dict or not bundle['teams']:
        raise ValueError('Declared import source and nonempty team configs required')
    if any(type(config) is not dict for config in bundle['teams'].values()):
        raise ValueError('Each team config must be a JSON object')
    teams = {team:from_config(config) for team,config in bundle['teams'].items()}
    cash = bundle.get('cash', {})
    if type(cash) is not dict or (set(cash) != set(teams) and 'cash' in bundle):
        raise ValueError('Declared cash import must cover every team exactly')
    cash_inputs = {}
    for team, opening in cash.items():
        if (type(opening) is not dict or set(opening) != {'source','records','unknown_legacy_players'} or
                type(opening['records']) is not list or any(type(record) is not dict for record in opening['records']) or
                type(opening['unknown_legacy_players']) is not list):
            raise ValueError('Explicit cash records, legacy unknown identities and source required')
        cash_inputs[team] = dict(records=tuple(CashObligation.from_dict(record) for record in opening['records']),
            source=opening['source'], unknown_legacy_players=tuple(opening['unknown_legacy_players']))
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
        for team, opening in cash_inputs.items():
            store.initialize_cash(team, **opening)
        with closing(sqlite3.connect(building)) as db:
            db.execute("INSERT INTO franchise_metadata VALUES ('bootstrap-source',?)",
                       (json.dumps({'source':bundle['source'],'input_sha256':digest,'format':1}),))
            db.commit()
        for team in teams:
            store.load_team(team)  # Original charges, ownership, actor coverage.
        os.link(building,destination)  # EEXIST also protects concurrent creators.
        return {'database':str(destination),'teams':len(teams),
                'players':len(set().union(*(ledger.registered_player_ids for ledger in teams.values()))),
                'cash_initialized_teams':len(cash_inputs),
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
