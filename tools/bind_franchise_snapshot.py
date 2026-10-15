"""Persist a verified registry/database association; no save edits or AI authorization."""
import argparse
import json
from pathlib import Path

from franchise.cap import Rejected
from franchise.snapshot_origin import bind
from franchise.store import FranchiseStore


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database',type=Path)
    parser.add_argument('save',type=Path)
    parser.add_argument('bindings',type=Path)
    args=parser.parse_args(argv)
    try:
        if not args.database.is_file():
            raise ValueError('Existing initialized franchise database required')
        result=bind(FranchiseStore(args.database),json.loads(args.bindings.read_text()),args.save.read_bytes())
    except (OSError,ValueError,Rejected) as error:
        parser.exit(2,f'bind_franchise_snapshot: {error}\n')
    print(json.dumps(dict(association=result,game_runtime_verified=False,write_authorized=False),indent=2))


if __name__=='__main__':main()
