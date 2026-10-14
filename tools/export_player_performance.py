"""Pinned saved history for negotiation; no invented coverage or salary credit."""
from tools.franchise_snapshot_bindings import resolve_bindings
from tools.inspect_player_history import NAMED_METRICS, calendar_candidates


def saved_player_performance(bindings: dict, payload: bytes, source_slot: int) -> dict:
    if type(source_slot) is not int or source_slot < 0:
        raise ValueError('Supported integer player slot required')
    player = resolve_bindings(bindings, payload).get(source_slot)
    if player is None:
        raise ValueError('Saved performance requires a pinned roster member')
    history = calendar_candidates(payload, source_slot)
    source = 'original-fxg:' + history['payload_sha256'] + ':slot:' + str(source_slot)
    observations, excluded = [], {'deleted': 0, 'unknown_bit30': 0, 'unmapped_code': 0, 'negative_count': 0}
    for index, entry in enumerate(history['entries']):
        if entry['deleted']:
            excluded['deleted'] += 1
        elif entry['bit30_raw']:
            excluded['unknown_bit30'] += 1
        elif 'mapped_metric_name' not in entry:
            excluded['unmapped_code'] += 1
        elif entry['mapped_unit'] == 'count' and entry['signed_value_raw'] < 0:
            excluded['negative_count'] += 1
        else:
            observations.append({'metric': entry['mapped_metric_name'], 'unit': entry['mapped_unit'],
                'value': entry['signed_value_raw'], 'period_code_raw': entry['period_code_raw'],
                'candidate_calendar_year': entry['candidate_calendar_year'],
                'mode_code_raw': entry['mode_code_raw'], 'source': source + ':entry:' + str(index)})
    present = {row['metric'] for row in observations}
    return {'player_id': player['player_id'], 'source': source,
        'saved_display_year': history['saved_display_year'],
        'saved_history': observations, 'excluded_entries': excluded,
        'missing_named_metrics': sorted({name for name, _ in NAMED_METRICS.values()} - present),
        'unmapped_requested_metrics': ['tackles', 'targets', 'pressures', 'qb_hits'],
        'history_present': history['history_present'],
        'scope': 'Saved historical counters only; calendar years are candidates. Raw modes are not played/CPU/fast-sim coverage. Entries are not summed and missing metrics are not zero. No current-week, salary-credit or promise-goal attribution.'}
