"""Compare an opt-in read-only game capture with a reconciled franchise save."""
import argparse
import hashlib
from pathlib import Path
import struct

from tools.franchise_finance_state import saved_finance_state, HEADER_SIZE as FINANCE_HEADER, RECORD_SIZE as FINANCE_RECORD
from tools.franchise_identity_state import saved_identity_state, HEADER_SIZE as IDENTITY_HEADER, RECORD_SIZE as IDENTITY_RECORD


def read_capture(data):
    if len(data) < 16 or data[:8] != b'2K5CAP1\0':
        raise ValueError('Invalid live capture header')
    financial_size, identity_size = struct.unpack_from('<2I', data, 8)
    if (financial_size < FINANCE_HEADER or identity_size < IDENTITY_HEADER or
            financial_size > FINANCE_HEADER + 5198 * FINANCE_RECORD or
            identity_size > IDENTITY_HEADER + 5198 * IDENTITY_RECORD or
            len(data) != 16 + financial_size + identity_size):
        raise ValueError('Incomplete or oversized live capture')
    finance, identity = data[16:16+financial_size], data[16+financial_size:]
    version, count = struct.unpack_from('<2I', finance)
    identity_version, identity_count, members = struct.unpack_from('<3I', identity)
    if (version != 1 or identity_version != 1 or not 1 <= count <= 5198 or
            identity_count != count or members > count or
            financial_size != FINANCE_HEADER + count * FINANCE_RECORD or
            identity_size != IDENTITY_HEADER + members * IDENTITY_RECORD):
        raise ValueError('Invalid live capture dimensions')
    return finance, identity


def compare(payload, capture, *, pending_free_agent_slot=None):
    finance, identity = read_capture(capture)
    expected_finance, expected_identity = saved_finance_state(payload), saved_identity_state(payload)
    scope = {}
    if pending_free_agent_slot is not None:
        from tools.franchise_offer_state import saved_offer_screen_state
        expected_finance, expected_identity = saved_offer_screen_state(payload, pending_free_agent_slot)
        scope = {'comparison_scope': 'offer_screen_pending_free_agent',
                 'pending_free_agent_slot': pending_free_agent_slot}
    return {**scope, 'financial_match': finance == expected_finance,
            'identity_match': identity == expected_identity,
            'financial_sha256': hashlib.sha256(finance).hexdigest(),
            'identity_sha256': hashlib.sha256(identity).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--pending-free-agent-slot', type=int,
                        help='Explicit diagnostic for the selected saved free agent temporarily absent from its pool')
    args = parser.parse_args(argv)
    result = compare(args.save.read_bytes(), args.capture.read_bytes(),
                     pending_free_agent_slot=args.pending_free_agent_slot)
    import json
    print(json.dumps(result, indent=2))
    if not result['financial_match'] or not result['identity_match']:
        parser.exit(1, 'Live franchise differs from the saved projection; signing remains held.\n')
    print('Saved projections match. Active franchise, authority and application remain unverified.')


if __name__ == '__main__':
    main()
