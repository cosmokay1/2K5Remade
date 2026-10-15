"""Compare pinned SOFTDRINK fitted schedules with their dated source liabilities.

Read-only correction proposals, not a complete opening book or cash authority.
The pinned audit only covers its original roster, not all retained/reserve debt.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct

from franchise.books import ChargeRecord
from tools.export_legacy_contracts import legacy_contracts
from tools.franchise_snapshot_bindings import resolve_bindings, binding_money_scale
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE, TEAMS

AUDIT_SHA256 = 'dc34704beaf7219119f377584a753ae03b74973d09625deee061e7780e98e466'
AUDIT_COMMIT = 'e19384123c23a3601949dda67c9a3ab754d65fd6'


def reconcile_source(bindings, payload, source_bytes):
    if type(source_bytes) is not bytes or hashlib.sha256(source_bytes).hexdigest() != AUDIT_SHA256:
        raise ValueError('Exact pinned September 24 contract audit required')
    members = resolve_bindings(bindings, payload)
    if binding_money_scale(bindings) != 4:
        raise ValueError('Verified SOFTDRINK opening profile required')
    contracts = legacy_contracts(bindings, payload)
    audit = json.loads(source_bytes)
    index = defaultdict(list)
    for row in audit['ledger']:
        index[row['name']].append(row)
    name_counts = Counter(p['first_name'] + ' ' + p['last_name'] for p in members.values())
    teams = {}
    for team in TEAMS:
        matched, unresolved = [], []
        for slot, player in members.items():
            if player['team'] != team:
                continue
            entry = {'player_id': player['player_id'], 'source_slot': slot,
                     'name': player['first_name'] + ' ' + player['last_name']}
            candidates = index[entry['name']]
            reason = None
            if len(candidates) != 1 or name_counts[entry['name']] != 1:
                reason = 'source identity is absent or ambiguous'
            else:
                row = candidates[0]
                offset = PLAYER_START + slot * PLAYER_STRIDE
                packed = struct.unpack_from('<I', payload, offset + 0x24)[0]
                fields = {'contract_value': struct.unpack_from('<H', payload, offset + 10)[0],
                          'contract_type': (packed >> 16) & 15, 'contract_bonus': (packed >> 20) & 15,
                          'contract_length': (packed >> 24) & 15, 'contract_remaining': packed & 15}
                if row['fit']['fields'] != fields:
                    reason = 'saved terms differ from pinned fitted terms'
                elif (row['team_name'] != team or row['source_team'] not in
                      {team, {'Redskins': 'Commanders'}.get(team, team)}):
                    reason = 'source ownership differs; retained debt allocation requires review'
                elif row['schedule_kind'] != 'observed' or row['fallback'] is not None:
                    reason = 'source schedule is modeled; exact liabilities are unknown'
            if reason:
                unresolved.append({**entry, 'reason': reason})
                continue
            contract = next(c for c in contracts[team] if c.player_id == player['player_id'])
            fitted = contract.charges()
            source = row['fit']['source_cap_dollars']
            if (row['fit']['represented_cap_dollars'] != list(fitted) or
                    len(source) != len(fitted) or
                    any(type(v) is not int or v < 0 for v in source)):
                raise ValueError('Pinned source schedule does not reconcile with decoded fitted schedule')
            provenance = ('contract-audit:' + AUDIT_COMMIT + ':sha256:' + AUDIT_SHA256 +
                          ':as-of:' + audit['source_receipt']['asset_updated_at'] +
                          ':player:' + str(row['otc_id']))
            correction = ChargeRecord('source-cap:' + player['player_id'],
                                      tuple(a-b for a,b in zip(source,fitted)), provenance)
            matched.append({**entry, 'source_url': row['source'],
                            'fitted_charges_dollars': list(fitted),
                            'source_charges_dollars': source,
                            'opening_adjustment': {'record_id': correction.record_id,
                                'annual_charges': list(correction.annual_charges),
                                'source': correction.source}})
        teams[team] = {'matched': matched, 'unresolved': unresolved,
                      'matched_first_year_correction_dollars': sum(
                          r['opening_adjustment']['annual_charges'][0] for r in matched)}
    return {'scope': 'dated source-cap correction proposals; no complete obligations or cash authority',
            'payload_sha256': hashlib.sha256(payload).hexdigest(),
            'audit_sha256': AUDIT_SHA256, 'audit_commit': AUDIT_COMMIT,
            'as_of': audit['source_receipt']['asset_updated_at'],
            'matched_contracts': sum(len(t['matched']) for t in teams.values()),
            'unresolved_contracts': sum(len(t['unresolved']) for t in teams.values()),
            'complete_opening_books': False, 'write_authorized': False, 'teams': teams}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('bindings', type=Path)
    parser.add_argument('contract_audit', type=Path)
    args = parser.parse_args(argv)
    try:
        report = reconcile_source(json.loads(args.bindings.read_text()), args.save.read_bytes(),
                                  args.contract_audit.read_bytes())
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
