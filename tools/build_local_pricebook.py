"""Generate a new offline local-rules policy; never edit saves or activate signing.

Inputs contain actual annual contract values (NOT fitted remaining cap charges),
reference/current cap, explicit classifications/minimums and optional canonical
performance. stdout previews both policy and provenance; --output creates a new
policy file exclusively, for explicit selection through --local-config.
"""
import argparse
import json
from pathlib import Path
from franchise.market_pricing import build_pricebook
from tools.create_franchise import MAX_INPUT, unique_object


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    try:
        with args.input.open('rb') as stream:raw=stream.read(MAX_INPUT+1)
        if len(raw)>MAX_INPUT:raise ValueError('Pricebook input exceeds 16 MiB')
        result=build_pricebook(json.loads(raw,object_pairs_hook=unique_object))
        if args.output:
            with args.output.open('x',encoding='utf-8') as stream:
                json.dump(result['policy'],stream,indent=2,allow_nan=False);stream.write('\n')
    except (ValueError,OSError) as error:
        parser.exit(2,f'build_local_pricebook: {error}\n')
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
