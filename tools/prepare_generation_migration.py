"""Back up and reconcile an existing franchise before generation migration.

Run from the repository root with python3 -m tools.prepare_generation_migration.
Default mode prepares evidence only. Use --migrate to commit the verified format4 checkpoint.
"""
import argparse
import json
from pathlib import Path
import sqlite3
from franchise.store import FranchiseStore


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database',type=Path,help='Existing format3 franchise database')
    parser.add_argument('--migrate',action='store_true',help='Commit backed-up format3 to format4 migration')
    args=parser.parse_args()
    try:
        report=(FranchiseStore.migrate_generations(args.database) if args.migrate else
                FranchiseStore.prepare_generation_migration(args.database))
    except (OSError,ValueError,sqlite3.Error) as exc:
        parser.exit(2,f'prepare_generation_migration: {exc}\n')
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__=='__main__':
    main()
