"""Build a private portrait-only hybrid preview, never a signed game save.

Verified NFL Week 1 identity matches select SOFTDRINK's photo IDs. The source
record bank, team/depth pointers, names, ratings and contract words stay intact.
Incomplete previews require an explicit flag and must never be installed.
Financial reconciliation and actual title acceptance are independent gates.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import struct

from tools.resolve_week1_players import resolve_week1


def portrait_preview(native, source, weekly_rows, *, season_year, allow_incomplete=False,
                     allow_biography_corrections=False):
    report = resolve_week1(native, source, weekly_rows, season_year=season_year,
                          allow_biography_corrections=allow_biography_corrections)
    if report['unresolved_source'] and not allow_incomplete:
        raise ValueError('Unresolved player images; only an explicit non-installable preview is permitted')
    output = bytearray(source)
    allowed = set()
    for player in report['matched']:
        field = 0xAFA8 + player['source_slot']*0x54 + 6
        struct.pack_into('<H', output, field, player['preserve_native_photo_id'])
        allowed.update((field, field+1))
    changed = [index for index, (before, after) in enumerate(zip(source, output)) if before != after]
    if len(output) != len(source) or not set(changed) <= allowed:
        raise ValueError('Portrait preview modified a non-portrait byte')
    report.update({'preview_sha256': hashlib.sha256(output).hexdigest(),
                   'changed_bytes': len(changed), 'changed_fields': 'verified player Photo uint16 only',
                   'original_contract_words_preserved': True,
                   'original_contracts_are_not_reconciled': True,
                   'ready_for_franchise_test': False, 'signing_authorized': False,
                   'save_container_or_signature_created': False})
    return bytes(output), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('native_roster', 'source_roster', 'weekly_roster', 'destination'):
        parser.add_argument(arg, type=Path)
    parser.add_argument('--season-year', required=True, type=int)
    parser.add_argument('--allow-incomplete-preview', action='store_true')
    parser.add_argument('--allow-profile-matches', action='store_true',
                        help='Allow audited profile matches; does not rewrite birth dates')
    args = parser.parse_args()
    opener = gzip.open if args.weekly_roster.suffix == '.gz' else open
    with opener(args.weekly_roster, 'rt') as stream:
        rows = list(csv.DictReader(stream))
    payload, report = portrait_preview(args.native_roster.read_bytes(), args.source_roster.read_bytes(),
        rows, season_year=args.season_year, allow_incomplete=args.allow_incomplete_preview,
        allow_biography_corrections=args.allow_profile_matches)
    args.destination.mkdir(parents=True, exist_ok=False)
    (args.destination/'NOT_FOR_INSTALL.roster-preview').write_bytes(payload)
    (args.destination/'receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'matched_images': len(report['matched']),
                      'unresolved_images': len(report['unresolved_source']),
                      'ready_for_franchise_test': False}))


if __name__ == '__main__':
    main()
