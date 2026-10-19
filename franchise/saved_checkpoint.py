"""Read-only separation of native roster payroll and recorded cap enforcement.

Normalizing a private comparison copy supplies no write authority. Any mismatch
must separately match a settled journal before use as a negotiation checkpoint.
"""
import struct
from tools.reconcile_franchise_payroll import reconcile_payroll
from tools.franchise_finance_state import saved_finance_state
from tools.franchise_identity_state import saved_identity_state
from tools.inspect_franchise_save import TEAMS
from franchise.cap import Rejected


def projection(payload):
    payroll=reconcile_payroll(payload)
    native=bytearray(payload)
    for i,team in enumerate(TEAMS):
        struct.pack_into('<I',native,0x44a8+0x1f4*i+0x124,
                         payroll['teams'][team]['reconstructed_roster_payroll_dollars']//1000)
    native=bytes(native)
    finance=bytearray(saved_finance_state(native))
    for i,team in enumerate(TEAMS):
        struct.pack_into('<I',finance,48+12*i,payroll['teams'][team]['stored_payroll_dollars']//1000)
    return native,bytes(finance),saved_identity_state(payload)


def verify(store,db,payload):
    """Bind an enforced checkpoint to its latest settled saved transaction."""
    native,finance,identity=projection(payload)
    row=db.execute("SELECT request_id FROM guest_signings WHERE state='settled' "
                   "AND json_extract(intent,'$.format')=2 ORDER BY rowid DESC LIMIT 1").fetchone()
    if row is None:
        if native!=payload:
            raise Rejected('Unrecorded saved payroll correction')
        return False
    from franchise.guest_application import read_amendment
    after=None
    for journal, in db.execute("SELECT request_id FROM guest_signings WHERE state='settled' AND json_extract(intent,'$.format')=2 ORDER BY rowid").fetchall():
        _,_,_,after,_=read_amendment(store,db,journal)
    _,expected_finance,expected_identity=projection(after)
    from franchise.local_runtime import saved_calendar_tick
    from tools.inspect_franchise_calendar import inspect_calendar
    old_calendar,new_calendar=inspect_calendar(after),inspect_calendar(payload)
    if (old_calendar['season_index']!=new_calendar['season_index'] or
            saved_calendar_tick(lambda:payload)<saved_calendar_tick(lambda:after)):
        raise Rejected('Saved negotiation calendar moved backward or changed season')
    # Same-year progress may advance after games. All ownership, terms, cap,
    # accumulator and enforced payroll words must remain unchanged.
    comparable=bytearray(finance);expected=bytearray(expected_finance)
    for offset in (16,20,28,32,40):
        comparable[offset:offset+4]=expected[offset:offset+4]
    if (bytes(comparable),identity)!=(bytes(expected),expected_identity):
        raise Rejected('Saved checkpoint differs from the latest settled amendment')
    return True


def charges(ledger,records):
    """Exact current obligations, including already agreed salary/bonus layers."""
    schedules=[ledger._legacy_amendments[r.player_id].charges()
               if r.player_id in ledger._legacy_amendments else r.charges() for r in records]
    schedules.extend(r.annual_charges for r in ledger._opening_books.retained)
    return [sum(row[i] if i<len(row) else 0 for row in schedules)
            for i in range(max(map(len,schedules),default=0))]


def verify_terms(ledger,records,*,original_sources):
    from franchise.guest_contracts import guest_terms_for_offer
    from franchise.legacy_contracts import LegacyContract
    for record in records:
        expected=ledger._legacy_contracts.get(record.player_id)
        if expected is None:
            raise Rejected('Supported imported contract inventory required')
        if record.player_id in ledger._legacy_amendments:
            offer=ledger._legacy_amendments[record.player_id].offer
            # Use the registered constants; no mod-name-driven policy.
            from franchise.guest_contracts import SOFTDRINK_CONTRACT_FORMAT,GUEST_CONTRACT_FORMAT
            fmt=SOFTDRINK_CONTRACT_FORMAT if record.game_dollar_scale==4 else GUEST_CONTRACT_FORMAT
            terms=guest_terms_for_offer(offer,contract_format=fmt)
            expected=LegacyContract(record.player_id,terms.amount_word,terms.bonus_code,
                terms.shape_code,terms.years,terms.years,record.source,record.game_dollar_scale)
        a,b=expected.to_dict(),record.to_dict()
        if not original_sources:
            a.pop('source');b.pop('source')
        if a!=b:
            raise Rejected('Saved legacy terms differ from ledger inventory')
