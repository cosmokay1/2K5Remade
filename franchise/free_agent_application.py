"""Source-bound free-agent targets. No guest writes or control grants."""
from fractions import Fraction
import struct

from franchise.books import parse_amount
from franchise.cap import Offer, Rejected, json_amount
from tools.franchise_snapshot_bindings import binding_money_scale, resolve_bindings
from tools.inspect_franchise_save import TEAMS
from franchise.saved_checkpoint import projection
from tools.franchise_offer_state import expected_signed_state, saved_offer_screen_state


def live_source(bindings, before, player_id, observed):
    """Only the bound FA's temporary pool removal may differ from the save."""
    from franchise.guest_signing import _hash
    native,finance,identity=projection(before)
    full=(finance,identity)
    slots=[s for s,p in resolve_bindings(bindings,before).items()
           if p['player_id']==player_id and p['team']=='free_agents']
    if len(slots)!=1:raise Rejected('Bound saved free agent required')
    pending,missing=saved_offer_screen_state(native,slots[0])
    pending=bytearray(pending)
    for i in range(32):pending[48+12*i:52+12*i]=finance[48+12*i:52+12*i]
    for candidate in (full,(bytes(pending),missing)):
        if observed==dict(finance=_hash(candidate[0]),identity=_hash(candidate[1])):
            return candidate
    raise Rejected('Live free-agent source differs from saved league or bound pending offer')


def target(intent,before):
    """Exact accepted books govern payroll; native contracts remain comparison data."""
    offer=Offer.from_dict(intent['offer']);team=intent['team_id'];index=TEAMS.index(team)
    source=intent['native_source'];preview=source['preview']
    if preview['revision']!=intent['expected_revision'] or preview['contract_charges']!=[json_amount(v) for v in offer.charges(5)]:
        raise ValueError('Native free-agent preview differs from accepted contract')
    native,finance,_=projection(before)
    after,identity=expected_signed_state(intent['bindings'],native,offer=offer,
        guest_offer=intent['guest_offer'],team_id=team)
    raw=struct.unpack_from('<I',after,48+12*index)[0]
    scale=binding_money_scale(intent['bindings']);quantum=1000*scale
    cap=struct.unpack_from('<I',finance,12)[0]*quantum
    charge=parse_amount(preview['annual_team_charges_after'][0]);room=parse_amount(preview['room_after'])
    reserve=cap-charge-room
    _,flag,accumulator=struct.unpack_from('<III',finance,48+12*index)
    required=charge+reserve-(accumulator*quantum if flag else 0)
    value=Fraction(required)/quantum;rounded=(value.numerator+value.denominator-1)//value.denominator
    if reserve<0 or required<0 or room<0 or not 0<=rounded<0x7fffffff or cap-rounded*quantum-(accumulator*quantum if flag else 0)<0:
        raise Rejected('Native free-agent target exceeds accounted cap or currency range')
    after=bytearray(after)
    for i in range(32):after[48+12*i:52+12*i]=finance[48+12*i:52+12*i]
    struct.pack_into('<I',after,48+12*index,rounded)
    return bytes(after),identity,dict(native_payroll_after_raw=raw,enforced_payroll_raw=rounded)


def confirm(intent,before,after):
    from franchise.guest_signing import _hash
    from tools.confirm_saved_signing import confirm_saved_signing
    expected,identity,cap=target(intent,before)
    native_before,_,_=projection(before);native_after,finance,observed_identity=projection(after)
    if (finance,observed_identity)!=(expected,identity):
        raise ValueError('Saved free-agent effects differ from exact cap/ownership target')
    proof=confirm_saved_signing(intent['bindings'],native_before,native_after,
        expected_before_sha256=_hash(native_before),offer=Offer.from_dict(intent['offer']),
        guest_offer=intent['guest_offer'],team_id=intent['team_id'])
    proof.update(before_payload_sha256=_hash(before),after_payload_sha256=_hash(after),
        normalized_comparison_sha256=_hash(native_after),saved_enforced_payroll_raw=cap['enforced_payroll_raw'])
    return proof
