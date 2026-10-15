"""Expected transient offer-screen membership; never a save edit or write permit."""
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
