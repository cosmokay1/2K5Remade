"""Explicit saved calendar/money context; no executable-name policy selection."""
import struct
from tools.inspect_franchise_calendar import inspect_calendar


def context_fields(context):
    fields = {'season_year', 'season_index', 'money_scale', 'league_cap_raw'}
    if type(context) is not dict or not fields <= set(context) or set(context) - fields - {'source_image_sha256', 'loaded_image_sha256'}:
        raise ValueError('Complete explicit game context required')
    year, index, scale, cap = (context[k] for k in ('season_year', 'season_index', 'money_scale', 'league_cap_raw'))
    if (type(year) is not int or not 2000 <= year <= 2255 or
            type(index) is not int or not 0 <= index <= 255 or
            type(scale) is not int or scale not in (1, 4) or
            (cap is not None and (type(cap) is not int or not 1 <= cap <= 0x7fffffff))):
        raise ValueError('Supported explicit calendar, units and raw cap required')
    for key in ('source_image_sha256', 'loaded_image_sha256'):
        if key not in context:
            continue
        digest = context[key]
        if type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Canonical executable provenance digest required')
    return dict(context)


def raw_context(payload):
    calendar = inspect_calendar(payload)
    cap = struct.unpack_from('<i', payload, calendar['scheduler_offset'] + 0x83DC + 0x15D0)[0]
    return {'season_year': calendar['display_year'], 'season_index': calendar['season_index'],
            'money_scale': 1, 'league_cap_raw': cap if cap > 0 else None}


def validate_context(context, payload):
    result = context_fields(context)
    observed = raw_context(payload)
    if result['season_index'] != observed['season_index'] or result['league_cap_raw'] != observed['league_cap_raw']:
        raise ValueError('Saved calendar/cap differs from explicit game context; verified migration required')
    return result
