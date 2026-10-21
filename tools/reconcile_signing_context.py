"""Read-only signing checkpoint against a pinned saved legacy book.

Matching this checkpoint does not authorize a model request or a guest write.
Bank rebuilds, season transitions and modern ledger changes need another verified
reconciliation path; they are not silently accepted by this initial adapter.
"""
import argparse
import hashlib
import json
from pathlib import Path

from franchise.books import parse_amount
from franchise.cap import Rejected
import struct
from franchise.store import FranchiseStore
from tools.export_legacy_contracts import legacy_contracts
from tools.franchise_snapshot_bindings import resolve_signing_candidate, binding_money_scale
from tools.inspect_franchise_calendar import inspect_calendar
from tools.inspect_franchise_cap import inspect_cap
from tools.inspect_franchise_save import TEAMS


def reconcile_signing_context(bindings, payload, observation, store, *, expected_revision,guest_offer=None,amendment_scope=None):
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError('Explicit nonnegative financial revision required')
    if type(observation) is not dict or set(observation) != {'biography', 'team', 'calendar'}:
        raise ValueError('Complete live signing checkpoint required')
    if guest_offer is not None and (type(guest_offer) is not dict or set(guest_offer)!={'amount_word','flags_word'}):
        raise ValueError('Complete raw guest offer required')
    candidate = resolve_signing_candidate(bindings, payload, observation['biography'])
    scale = binding_money_scale(bindings)
    team = observation['team']
    fields = {'table_index', 'table_mode', 'payroll_raw', 'league_cap_raw',
              'team_flag_raw', 'first_year_accumulator_raw'}
    if type(team) is not dict or set(team) != fields or any(type(v) is not int or v < 0 for v in team.values()):
        raise ValueError('Typed complete original team checkpoint required')
    if team['table_mode'] != 2 or not 0 <= team['table_index'] < len(TEAMS):
        raise ValueError('Observed franchise team table required')
    calendar = inspect_calendar(payload)
    live_calendar = observation['calendar']
    calendar_fields = {'season_index', 'display_year', 'phase_01_raw', 'phase_02_raw',
                       'step_04_raw', 'step_05_raw', 'counter_08_raw'}
    if (type(live_calendar) is not dict or set(live_calendar) != calendar_fields
            or any(type(v) is not int or v != calendar[k] for k, v in live_calendar.items())):
        raise ValueError('Live calendar differs from pinned snapshot')
    name = TEAMS[team['table_index']]
    from franchise.saved_checkpoint import projection,verify,charges,verify_terms
    native,canonical_finance,_=projection(payload)
    cap = inspect_cap(native)
    saved = cap['teams'][name]
    if (team['league_cap_raw'] * 1000 != cap['league_cap_dollars']
            or team['payroll_raw'] != struct.unpack_from('<I',canonical_finance,48+12*team['table_index'])[0]
            or team['team_flag_raw'] != saved['original_team_flag_raw']
            or team['first_year_accumulator_raw'] * 1000 != saved['original_first_year_accumulator_dollars']):
        raise ValueError('Live cap inputs differ from pinned snapshot')
    contracts = legacy_contracts(bindings, native)[name]
    def file_version():
        metadata = Path(store.path).stat()
        return metadata.st_dev,metadata.st_ino,metadata.st_size,metadata.st_mtime_ns,metadata.st_ctime_ns
    original_file = file_version()
    # Reconstruct once inside one SQLite read snapshot. Keep freshness checking
    # after releasing that snapshot: data_version changes for other connections'
    # commits, including edits to existing rows that do not advance an event ID.
    with store._connection() as db:
        version = db.execute('PRAGMA data_version').fetchone()[0]
        ledger = store._load(db,name)
        inventory = store._contract_generations_from_ledger(name,ledger)
        recorded=verify(store,db,payload)
        if inventory['generations'] and not recorded:
            raise ValueError('Ledger contract inventory differs from pinned legacy snapshot')
        try:
            verify_terms(ledger,contracts,original_sources=not recorded)
        except Rejected as error:
            raise ValueError('Ledger contract inventory differs from checkpoint') from error
        financial = ledger.financial_snapshot()
        from franchise.opening_native import record as opening_record
        expected_charges = charges(ledger,contracts,include_opening_adjustments=opening_record(db) is not None)
        if (financial['revision'] != expected_revision or inventory['financial_revision'] != expected_revision
                or financial['cap'] != cap['league_cap_dollars'] * scale
                or financial['signed_players'] != sorted(record.player_id for record in contracts)
                or [parse_amount(v) for v in financial['charges']] != expected_charges):
            raise ValueError('Ledger revision, ownership or current cap differs from checkpoint')
        context = store._player_context_from_ledger(db,name,candidate['candidate_player_id'],ledger)
        if context['financial_revision'] != expected_revision or not context['initialized']:
            raise ValueError('Persisted player context unavailable or changed during inspection')
        offer_context=None
        if guest_offer is not None:
            from franchise.guest_contracts import _preview_guest_offer, GUEST_CONTRACT_FORMAT, SOFTDRINK_CONTRACT_FORMAT
            offer_context=_preview_guest_offer(candidate['candidate_player_id'],**guest_offer,
                expected_revision=expected_revision,
                contract_format=SOFTDRINK_CONTRACT_FORMAT if scale==4 else GUEST_CONTRACT_FORMAT,
                preview_offer=lambda offer:store._preview_offer(db,name,ledger,offer,expected_revision))
            if context.get('legacy_contract') is not None and offer_context['offer'] is not None:
                from franchise.cap import Offer
                try:
                    comparison=store._preview_legacy_amendment(db,name,ledger,
                        Offer.from_dict(offer_context['offer']),expected_revision,scope=amendment_scope)
                except Rejected as error:
                    offer_context.update(outcome='accounting_rejected',preview=None,reason=str(error))
                else:
                    # Distinct from eligible_preview: cannot enter proposal or
                    # saved-signing authority through the free-agent path.
                    offer_context.update(outcome='amendment_comparison',preview=None,reason=None,
                                         amendment=comparison)
        db.commit()
        if db.execute('PRAGMA data_version').fetchone()[0] != version or file_version() != original_file:
            raise ValueError('Financial state changed during inspection')
    return {'player_id': candidate['candidate_player_id'], 'team_id': name,
            'financial_revision': expected_revision, 'saved_payload_sha256': hashlib.sha256(payload).hexdigest(),
            'source_slot': candidate['source_slot'], 'player_context': context,
            **({'offer_context':offer_context} if guest_offer is not None else {}),
            'scope': 'matching saved legacy roster and explicit retained opening debt; complete opening liabilities, active franchise selection, cash/rookie obligations and write authorization remain unverified',
            'write_authorized': False, 'ai_authorized': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('bindings', type=Path)
    parser.add_argument('observation', type=Path)
    parser.add_argument('database', type=Path)
    parser.add_argument('--expected-revision', required=True, type=int)
    args = parser.parse_args(argv)
    if not args.database.is_file():
        parser.error('Existing verified franchise database required')
    try:
        result = reconcile_signing_context(json.loads(args.bindings.read_text()), args.save.read_bytes(),
            json.loads(args.observation.read_text()), FranchiseStore(args.database), expected_revision=args.expected_revision)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
