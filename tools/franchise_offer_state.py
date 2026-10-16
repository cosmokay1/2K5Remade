"""Expected offer/signing comparison images; never a save edit or write permit."""
import struct

from tools.franchise_finance_state import saved_finance_state, HEADER_SIZE as FINANCE_HEADER, RECORD_SIZE as FINANCE_RECORD
from tools.franchise_identity_state import saved_identity_state, HEADER_SIZE as IDENTITY_HEADER, RECORD_SIZE as IDENTITY_RECORD


def saved_offer_screen_state(payload: bytes, source_slot: int):
    """The selected saved free agent may be temporarily absent from the pool.

    Keep every contract, cap/calendar/team field and other biography exact.
    The caller must bind this slot to its accepted proposal; arbitrary missing
    players, owned players and roster changes are not equivalent states.
    """
    finance = bytearray(saved_finance_state(payload))
    identity = saved_identity_state(payload)
    _, count, members = struct.unpack_from('<3I', identity)
    if type(source_slot) is not int or not 0 <= source_slot < count:
        raise ValueError('Bound saved free-agent slot required')
    owner_offset = FINANCE_HEADER + source_slot * FINANCE_RECORD + 7
    if struct.unpack_from('<I', finance, owner_offset)[0] != 32:
        raise ValueError('Only a saved free agent can be pending on its offer screen')
    records = [identity[i:i+IDENTITY_RECORD]
               for i in range(IDENTITY_HEADER, len(identity), IDENTITY_RECORD)]
    kept = [record for record in records if struct.unpack_from('<I', record)[0] != source_slot]
    if len(kept) != members - 1:
        raise ValueError('Exactly one bound free-agent biography required')
    struct.pack_into('<I', finance, owner_offset, 0xffffffff)
    return bytes(finance), struct.pack('<3I', 1, count, members - 1) + b''.join(kept)


def expected_signed_state(bindings, payload: bytes, *, offer, guest_offer, team_id):
    """Predict isolated native contract/owner/payroll effects, without editing a save.

    This is an expected comparison image, not a permitted memory-write plan.
    Identity remains the complete bound membership, including the candidate who
    was temporarily removed while its offer screen was open. Full books,
    roster eligibility, runtime authority and uninterrupted application remain
    the coordinator's responsibility.
    """
    from franchise.cap import Offer
    from franchise.guest_contracts import GuestContractTerms, GUEST_CONTRACT_FORMAT, SOFTDRINK_CONTRACT_FORMAT
    from tools.franchise_snapshot_bindings import resolve_bindings, binding_money_scale
    from tools.inspect_franchise_save import TEAMS
    if not isinstance(offer, Offer) or team_id not in TEAMS:
        raise ValueError('Typed accepted offer and supported target team required')
    if type(guest_offer) is not dict or set(guest_offer) != {'amount_word', 'flags_word'}:
        raise ValueError('Complete captured guest offer required')
    scale = binding_money_scale(bindings)
    contract_format = SOFTDRINK_CONTRACT_FORMAT if scale == 4 else GUEST_CONTRACT_FORMAT
    terms = GuestContractTerms.from_context(**guest_offer)
    if terms.to_offer(offer.player_id, contract_format=contract_format) != offer:
        raise ValueError('Captured guest terms differ from accepted offer')
    members = resolve_bindings(bindings, payload)
    selected = [slot for slot, player in members.items()
                if player['player_id'] == offer.player_id and player['team'] == 'free_agents']
    if len(selected) != 1:
        raise ValueError('Bound saved free-agent candidate required')
    finance = bytearray(saved_finance_state(payload))
    record = FINANCE_HEADER + selected[0] * FINANCE_RECORD
    # 323D80 changes only these mapped bits at player+24, the amount at +0A,
    # and clears bit3 at +08. Preserve all other packed status bits.
    packed = struct.unpack_from('<I', finance, record + 3)[0]
    mask = 0x0FF7000F
    replacement = (terms.years << 24) | (terms.bonus_code << 20) | (terms.shape_code << 16) | terms.years
    finance[record] &= 0xF7
    struct.pack_into('<HI', finance, record + 1, terms.amount_word, (packed & ~mask) | replacement)
    struct.pack_into('<I', finance, record + 7, TEAMS.index(team_id))
    payroll_offset = 48 + 12 * TEAMS.index(team_id)
    payroll = struct.unpack_from('<I', finance, payroll_offset)[0]
    charge = offer.charges(5)[0] / (1000 * scale)
    if charge.denominator != 1 or payroll + charge > 0xFFFFFFFF:
        raise ValueError('Exact representable native payroll required')
    struct.pack_into('<I', finance, payroll_offset, payroll + int(charge))
    return bytes(finance), saved_identity_state(payload)


def expected_amended_state(bindings,payload: bytes,*,offer,guest_offer,team_id,native_bonus_accelerated=False):
    """Expected native owned-player effects, with supplemental debt kept separate.

    The native packed contract cannot hold multiple bonus schedules. This image
    describes its new terms only; it is never a cap-enforcement or write permit.
    """
    from franchise.cap import Offer
    from franchise.guest_contracts import GuestContractTerms,GUEST_CONTRACT_FORMAT,SOFTDRINK_CONTRACT_FORMAT
    from tools.franchise_snapshot_bindings import resolve_bindings,binding_money_scale
    from tools.export_legacy_contracts import legacy_contracts
    from tools.inspect_franchise_save import TEAMS
    if not isinstance(offer,Offer) or team_id not in TEAMS:
        raise ValueError('Typed accepted amendment and supported team required')
    if type(guest_offer) is not dict or set(guest_offer)!={'amount_word','flags_word'}:
        raise ValueError('Complete captured guest amendment required')
    scale=binding_money_scale(bindings)
    terms=GuestContractTerms.from_context(**guest_offer)
    if terms.to_offer(offer.player_id,contract_format=SOFTDRINK_CONTRACT_FORMAT if scale==4 else GUEST_CONTRACT_FORMAT)!=offer:
        raise ValueError('Captured terms differ from accepted amendment')
    members=resolve_bindings(bindings,payload)
    slots=[slot for slot,p in members.items() if p['player_id']==offer.player_id and p['team']==team_id]
    if len(slots)!=1:
        raise ValueError('Bound current owning team required for amendment')
    original=next(c for c in legacy_contracts(bindings,payload)[team_id] if c.player_id==offer.player_id)
    finance=bytearray(saved_finance_state(payload));record=FINANCE_HEADER+slots[0]*FINANCE_RECORD
    packed=struct.unpack_from('<I',finance,record+3)[0]
    replacement=(terms.years<<24)|(terms.bonus_code<<20)|(terms.shape_code<<16)|terms.years
    finance[record]&=0xF7
    struct.pack_into('<HI',finance,record+1,terms.amount_word,(packed&~0x0FF7000F)|replacement)
    payroll_offset=48+12*TEAMS.index(team_id)
    payroll=struct.unpack_from('<I',finance,payroll_offset)[0]
    if type(native_bonus_accelerated) is not bool:
        raise ValueError('Explicit observed native bonus branch required')
    if native_bonus_accelerated:
        from franchise.legacy_contracts import original_annual_rows
        rows=original_annual_rows(original.amount_word,original.bonus_code,original.shape_code,original.original_years)
        bonus=sum(row['allocated_bonus_dollars'] for row in rows[-original.remaining_years:])//1000
        flag,previous=struct.unpack_from('<II',finance,payroll_offset+4)
        if not flag or not bonus or previous+bonus>65535:
            raise ValueError('Native bonus acceleration branch is not representable')
        struct.pack_into('<I',finance,payroll_offset+8,previous+bonus)
    delta=(offer.charges(5)[0]-original.charges()[0])/(1000*scale)
    if delta.denominator!=1 or not 0<=payroll+delta<=0xffffffff:
        raise ValueError('Exact representable amended native payroll required')
    struct.pack_into('<I',finance,payroll_offset,payroll+int(delta))
    return bytes(finance),saved_identity_state(payload)
