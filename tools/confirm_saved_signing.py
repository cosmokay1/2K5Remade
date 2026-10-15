"""Confirm one isolated saved free-agent signing; never apply or settle it.

This checks the observed Xbox FXG roster/contract/payroll boundary. It does not
prove complete modern opening books, live memory, cash, or save atomicity. A
coordinator must bind these immutable inputs to its durable intent separately.
"""
import hashlib
import json
import struct

from franchise.cap import Offer, json_amount
from franchise.guest_contracts import GuestContractTerms, GUEST_CONTRACT_FORMAT, SOFTDRINK_CONTRACT_FORMAT
from tools.franchise_snapshot_bindings import resolve_bindings, binding_money_scale
from tools.inspect_franchise_save import inspect_save, PLAYER_START, PLAYER_STRIDE, TEAMS
from tools.inspect_franchise_calendar import inspect_calendar
from tools.inspect_franchise_cap import inspect_cap


def _contract(payload,slot):
    offset=PLAYER_START+slot*PLAYER_STRIDE
    amount=struct.unpack_from('<H',payload,offset+0x0A)[0]
    flags=struct.unpack_from('<I',payload,offset+0x24)[0]
    return amount,(flags>>20)&15,(flags>>16)&15,(flags>>24)&15,flags&15


def confirm_saved_signing(bindings,before,after,*,expected_before_sha256,offer,guest_offer,team_id):
    """Compare saved effects to exact accepted terms without mutation/authority."""
    if not isinstance(offer,Offer) or team_id not in TEAMS:
        raise ValueError('Typed accepted offer and supported target team required')
    if (type(expected_before_sha256) is not str or len(expected_before_sha256)!=64
            or any(c not in '0123456789abcdef' for c in expected_before_sha256)):
        raise ValueError('Pinned before-save SHA256 required')
    if (type(before) is not bytes or type(after) is not bytes
            or hashlib.sha256(before).hexdigest()!=expected_before_sha256 or before==after):
        raise ValueError('Pinned distinct before/after save payloads required')
    if type(guest_offer) is not dict or set(guest_offer)!={'amount_word','flags_word'}:
        raise ValueError('Complete captured guest offer required')
    scale=binding_money_scale(bindings)
    contract_format=SOFTDRINK_CONTRACT_FORMAT if scale==4 else GUEST_CONTRACT_FORMAT
    terms=GuestContractTerms.from_context(guest_offer['amount_word'],guest_offer['flags_word'])
    if terms.to_offer(offer.player_id,contract_format=contract_format)!=offer:
        raise ValueError('Captured guest terms differ from accepted offer')
    before_members=resolve_bindings(bindings,before)
    after_members=resolve_bindings(bindings,after)
    before_roster,after_roster=inspect_save(before),inspect_save(after)
    if before_roster['player_record_count']!=after_roster['player_record_count']:
        raise ValueError('Player-bank size changed during signing')
    slots=[slot for slot,p in before_members.items() if p['player_id']==offer.player_id]
    if len(slots)!=1:
        raise ValueError('Accepted player is absent from pinned bindings')
    slot=slots[0]
    if before_members[slot]['team']!='free_agents' or after_members[slot]['team']!=team_id:
        raise ValueError('Saved signing must move the bound free agent to the target team')
    for source,player in before_members.items():
        if source!=slot and player['team']!=after_members[source]['team']:
            raise ValueError('Another player changed roster membership')
    expected=(terms.amount_word,terms.bonus_code,terms.shape_code,terms.years,terms.years)
    if _contract(after,slot)!=expected:
        raise ValueError('Saved contract differs from captured accepted terms')
    # Include unbound/non-roster bank records: silently changing their contracts
    # would not constitute an isolated signing even if current payroll matched.
    for source in range(before_roster['player_record_count']):
        if source!=slot and _contract(before,source)!=_contract(after,source):
            raise ValueError('Another player contract changed during signing')
    before_calendar,after_calendar=inspect_calendar(before),inspect_calendar(after)
    calendar_fields=('table_mode','season_index','display_year','phase_01_raw','phase_02_raw',
                     'step_04_raw','step_05_raw','counter_08_raw')
    if any(before_calendar[key]!=after_calendar[key] for key in calendar_fields):
        raise ValueError('Saved calendar changed during signing')
    before_cap,after_cap=inspect_cap(before),inspect_cap(after)
    if before_cap['league_cap_dollars']!=after_cap['league_cap_dollars']:
        raise ValueError('League cap changed during signing')
    charges=offer.charges(5)
    for team in TEAMS:
        previous,current=before_cap['teams'][team],after_cap['teams'][team]
        for field in ('original_team_flag_raw','original_first_year_accumulator_dollars'):
            if previous[field]!=current[field]:
                raise ValueError('Saved team cap adjustment changed during signing')
        delta=(current['roster_payroll_dollars']-previous['roster_payroll_dollars'])*scale
        if delta!=(charges[0] if team==team_id else 0):
            raise ValueError('Saved payroll change differs from the accepted contract charge')
    # Check the raw financial comparison boundary too. Decoded economic fields
    # alone omit other packed status bits and byte8 flags, including unbound
    # bank records. The same target image can be used by a native coordinator.
    from tools.franchise_offer_state import expected_signed_state
    from tools.franchise_finance_state import saved_finance_state
    from tools.franchise_identity_state import saved_identity_state
    expected_finance, expected_identity = expected_signed_state(bindings, before,
        offer=offer, guest_offer=guest_offer, team_id=team_id)
    if saved_finance_state(after) != expected_finance or saved_identity_state(after) != expected_identity:
        raise ValueError('Saved raw financial/identity effects differ from the isolated signing target')
    previous,current=before_cap['teams'][team_id],after_cap['teams'][team_id]
    return {'format':'saved-signing-confirmation-v1','franchise_id':bindings['franchise_id'],
        'bindings_sha256':hashlib.sha256(json.dumps(bindings,sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest(),
        'before_payload_sha256':expected_before_sha256,'after_payload_sha256':after_cap['payload_sha256'],
        'player_id':offer.player_id,'source_slot':slot,'team_id':team_id,'contract_format':contract_format,
        'guest_offer':{'amount_word':terms.amount_word,'flags_word':(terms.shape_code<<29)|(terms.years<<16)|terms.bonus_code},
        'offer':offer.to_dict(),'contract_charges':[json_amount(value) for value in charges],
        'calendar':{key:before_calendar[key] for key in calendar_fields},
        'before_roster_payroll':previous['roster_payroll_dollars']*scale,
        'after_roster_payroll':current['roster_payroll_dollars']*scale,
        'scope':'isolated saved roster/contract/payroll effects only; live state, complete books and settlement unverified',
        'write_authorized':False}
