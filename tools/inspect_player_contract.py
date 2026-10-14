"""Read original-game contract fields and supported static annual calculations.

Field evidence: controlled AIGILDON signing, runtime mutation audit and the
Gildon offer UI. Slot identifies this snapshot only. Assets are not bundled.
"""
import argparse
import json
from pathlib import Path
import struct

from tools.inspect_franchise_save import inspect_save, PLAYER_START, PLAYER_STRIDE


def _float32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def original_annual_rows(amount_word: int, bonus_code: int, shape_code: int, years: int) -> list:
    """Original E6020/E6040 rules in whole thousands, not modern accounting.

    Descending/Balanced only. Explicit float stores and final truncation match
    the guest's x87/SSE conversion boundaries. No rounding residual is repaired.
    """
    if any(type(value) is not int for value in (amount_word, bonus_code, shape_code, years)):
        raise ValueError('Original contract inputs must be integers')
    if not 1 <= amount_word <= 65535 or not 0 <= bonus_code <= 10 or shape_code not in (1, 2) or not 1 <= years <= 15:
        raise ValueError('Unsupported original contract inputs')
    average = int(_float32(amount_word * 10 / years))
    bonus = amount_word * bonus_code // years
    base = average - bonus
    rows = []
    for index in range(years):
        salary = base
        if shape_code == 1:
            fraction = _float32(2 * ((index + 0.5) / years) - 1)
            salary = int(_float32(base - (base // 2) * fraction))
        rows.append({'contract_year_index': index, 'salary_dollars': salary * 1000,
                     'allocated_bonus_dollars': bonus * 1000,
                     'original_game_charge_dollars': (salary + bonus) * 1000})
    return rows


def inspect_player_contract(payload: bytes, source_slot: int) -> dict:
    if type(source_slot) is not int or source_slot < 0:
        raise ValueError('Source slot must be a nonnegative integer')
    roster = inspect_save(payload)
    entries = [(team, player) for team, players in roster['teams'].items() for player in players]
    entries += [('free_agents', player) for player in roster['free_agents']]
    found = [(team, player) for team, player in entries if player['source_slot'] == source_slot]
    if len(found) != 1:
        raise ValueError('Source slot must identify one supported roster member')
    team, player = found[0]
    record = PLAYER_START + source_slot * PLAYER_STRIDE
    amount = struct.unpack_from('<H', payload, record + 0x0A)[0]
    packed = struct.unpack_from('<I', payload, record + 0x24)[0]
    term_low, term_high = packed & 15, (packed >> 24) & 15
    bonus_code, shape_code = (packed >> 20) & 15, (packed >> 16) & 7
    if not term_low or not term_high or not amount:
        raise ValueError('No supported active contract; do not infer expired/free-agent obligations')
    if term_low > term_high or bonus_code > 10 or shape_code not in (1, 2):
        raise ValueError('Contract fields outside observed term/bonus/style support')
    return {
        'scope': 'observed original-game contract readback; not modern accounting',
        'payload_sha256': roster['payload_sha256'],
        'source_slot_semantics': roster['source_slot_semantics'],
        'source_slot': source_slot, 'team': team,
        'first_name': player['first_name'], 'last_name': player['last_name'],
        'game_contract_total_dollars': amount * 10000,
        'game_bonus_percent': bonus_code * 10,
        'game_payment_style': {1: 'Descending', 2: 'Balanced'}[shape_code],
        # Both nibbles receive the entered years at signing; aging unverified.
        'term_low_nibble_raw': term_low, 'term_high_nibble_raw': term_high,
        'amount_word_raw': amount, 'bonus_code_raw': bonus_code,
        'shape_code_raw': shape_code, 'packed_contract_word_raw': packed,
        'original_annual_rows': original_annual_rows(amount, bonus_code, shape_code, term_high),
        'annual_rows_scope': 'static original-game calculation; no modern guarantees or calendar-aging verification',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('source_slot', type=int)
    args = parser.parse_args(argv)
    try:
        report = inspect_player_contract(args.save.read_bytes(), args.source_slot)
    except (ValueError, OSError) as exc:
        parser.exit(2, f'inspect_player_contract: {exc}\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
