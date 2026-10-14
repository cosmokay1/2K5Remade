"""Back up and reconcile an existing franchise before generation migration.

Run from the repository root with python3 -m tools.prepare_generation_migration.
This command prepares evidence only; it does not advance the database format.
"""
import argparse
import json
from pathlib import Path
import sqlite3
from franchise.store import FranchiseStore


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database',type=Path,help='Existing format3 franchise database')
    args=parser.parse_args()
    try:
        report=FranchiseStore.prepare_generation_migration(args.database)
    except (OSError,ValueError,sqlite3.Error) as exc:
        parser.exit(2,f'prepare_generation_migration: {exc}\n')
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__=='__main__':
    main()
