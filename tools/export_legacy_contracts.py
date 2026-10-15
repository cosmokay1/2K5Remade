"""Produce typed legacy schedules from a pinned, reconciled snapshot.

No database/game writes. Paid cash, protections and lifecycle conversion remain
unknown; these records must not be passed off as modern ActiveContract objects.
"""
import struct

from franchise.legacy_contracts import LegacyContract
from tools.franchise_snapshot_bindings import resolve_bindings, binding_money_scale
from tools.inspect_franchise_cap import inspect_cap
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE, TEAMS


def legacy_contracts(bindings: dict, payload: bytes) -> dict[str, tuple[LegacyContract, ...]]:
    members = resolve_bindings(bindings, payload)
    cap = inspect_cap(payload)
    scale = binding_money_scale(bindings)
    result = {}
    for team in TEAMS:
        contracts = []
        for slot, player in members.items():
            if player['team'] != team:
                continue
            offset = PLAYER_START + slot * PLAYER_STRIDE
            amount = struct.unpack_from('<H', payload, offset + 0x0A)[0]
            packed = struct.unpack_from('<I', payload, offset + 0x24)[0]
            contracts.append(LegacyContract(player['player_id'], amount, (packed >> 20) & 15,
                (packed >> 16) & 15, (packed >> 24) & 15, packed & 15,
                'original-fxg:' + cap['payload_sha256'] + ':slot:' + str(slot), scale))
        if sum(contract.charges()[0] for contract in contracts) != cap['teams'][team]['roster_payroll_dollars'] * scale:
            raise ValueError('Legacy schedules disagree with reconciled current payroll')
        result[team] = tuple(contracts)
    return result
