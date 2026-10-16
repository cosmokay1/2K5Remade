"""Preview or explicitly import declared salary inputs without rebuilding a franchise."""
import argparse
import json
from pathlib import Path
import sqlite3
import tempfile

from franchise.store import FranchiseStore
from tools.create_franchise import MAX_INPUT, unique_object


def import_inputs(database, batch, *, apply=False):
    database = Path(database).absolute()
    if not database.is_file():
        raise ValueError('Existing franchise database required')
    FranchiseStore._validate_salary_classification(batch)
    # Preview through an SQLite snapshot, including committed WAL state. Opening
    # the original through FranchiseStore would perform schema initialization.
    with tempfile.TemporaryDirectory(prefix='2k5-salary-preview-') as directory:
        copy = Path(directory)/'franchise.sqlite'
        with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as original:
            with sqlite3.connect(copy) as target:
                original.backup(target)
        store = FranchiseStore(copy)
        before = {team:store.load_team(team).financial_snapshot() for team in batch['expected_revisions']}
        result = store.initialize_salary_classification(**{k:batch[k] for k in ('request_id','source','profile','expected_revisions')})
        after = {team:FranchiseStore(copy).load_team(team).financial_snapshot() for team in before}
        for team in before:
            if {k:v for k,v in before[team].items() if k!='revision'} != {k:v for k,v in after[team].items() if k!='revision'}:
                raise ValueError('Salary classification changed contract balances')
        if apply:
            result = FranchiseStore(database).initialize_salary_classification(
                **{k:batch[k] for k in ('request_id','source','profile','expected_revisions')})
        return {'applied':apply,'teams':len(before),'classified_veterans':len(result['profile']['players']),
                'source':result['source'],'revisions':{team:row['revision'] for team,row in after.items()},
                'contract_balances_unchanged':True,'ai_authorized':False,'guest_write_authorized':False,
                'scope':'Salary inputs only; opening liabilities, rookie rules and native application require separate verification'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database',type=Path)
    parser.add_argument('input',type=Path)
    parser.add_argument('--apply',action='store_true',help='Explicit atomic import; default previews a private copy')
    args=parser.parse_args(argv)
    try:
        with args.input.open('rb') as incoming:raw=incoming.read(MAX_INPUT+1)
        if len(raw)>MAX_INPUT:raise ValueError('Salary input exceeds 16 MiB')
        batch=json.loads(raw,object_pairs_hook=unique_object)
        result=import_inputs(args.database,batch,apply=args.apply)
    except (OSError,ValueError,sqlite3.Error) as error:
        parser.exit(2,f'import_salary_classification: {error}\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
