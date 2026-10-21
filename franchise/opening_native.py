"""Recorded all-club opening cap projection. No live write or signing authority.

Opening source corrections stay in typed books, separate from approximate native
contracts. A saved projection is accepted only against its originating ledger and
complete native finance/identity checkpoint; it cannot replenish a later budget.
"""
from fractions import Fraction
from hashlib import sha256
from itertools import zip_longest
import json
import struct

from franchise.cap import Rejected
from franchise.books import json_amount, parse_amount
from tools.inspect_franchise_save import TEAMS

KEY = 'native-opening-cap-v1'


def _hash(value):
    return sha256(value).hexdigest()


def _json(value):
    return json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':'))


def record(db):
    row=db.execute('SELECT value FROM franchise_metadata WHERE key=?',(KEY,)).fetchone()
    return json.loads(row[0]) if row else None


def current_payrolls(ledgers, scale, finance):
    quantum=1000*scale; result=[]
    if set(ledgers)!=set(TEAMS) or scale not in (1,4):
        raise Rejected('Complete supported league opening books required')
    for i,team in enumerate(TEAMS):
        ledger=ledgers[team]
        _,flag,accumulator=struct.unpack_from('<III',finance,48+12*i)
        # Both the original adjusted accessor and payroll must count debt once.
        exact=ledger.charges[0]+ledger.roster_reserve+ledger._draft_reserved()[0]
        required=exact-(accumulator*quantum if flag else 0)
        raw=Fraction(required)/quantum
        rounded=(raw.numerator+raw.denominator-1)//raw.denominator
        if required<0 or not 0<=rounded<0x7fffffff:
            raise Rejected('Opening obligations exceed supported native payroll range')
        result.append(rounded)
    return result


def build(store,bindings,payload,*,source):
    """Prepare one isolated opening image against already-created exact books."""
    from franchise.saved_checkpoint import projection,charges,verify_terms
    from tools.franchise_snapshot_bindings import binding_money_scale,resolve_bindings
    from tools.export_legacy_contracts import legacy_contracts
    from tools.inspect_franchise_calendar import inspect_calendar
    from tools.inspect_franchise_cap import inspect_cap
    if type(source) is not dict or not source or any(not isinstance(v,str) or not v for v in source.values()):
        raise ValueError('Explicit pinned opening source provenance required')
    resolve_bindings(bindings,payload)
    native,finance,identity=projection(payload)
    calendar=inspect_calendar(native);scale=binding_money_scale(bindings)
    if native!=payload:
        raise Rejected('Reconciled fresh first-season payroll required')
    cap=inspect_cap(native)
    if any(t['original_team_flag_raw'] and t['original_first_year_accumulator_dollars'] for t in cap['teams'].values()):
        raise Rejected('Unresolved original opening debt accumulator')
    with store._connection() as db:
        if record(db) is not None or db.execute('SELECT 1 FROM guest_signings LIMIT 1').fetchone():
            raise Rejected('Opening projection cannot replace an existing checkpoint or negotiation')
        ledgers=store._load_teams(db,TEAMS);contracts=legacy_contracts(bindings,native)
        for team,ledger in ledgers.items():
            verify_terms(ledger,contracts[team],original_sources=False)
            if (ledger.cap!=cap['league_cap_dollars']*scale or
                    ledger.financial_snapshot()['signed_players']!=sorted(c.player_id for c in contracts[team]) or
                    any(a!=b for a,b in zip_longest(ledger.charges,charges(ledger,contracts[team],include_opening_adjustments=True),fillvalue=0))):
                raise Rejected('Native inventory or exact opening books differ')
        payrolls=current_payrolls(ledgers,scale,finance)
        obligations={team:json_amount(ledger.charges[0]) for team,ledger in ledgers.items()}
    output=bytearray(payload)
    for i,value in enumerate(payrolls):struct.pack_into('<I',output,0x44a8+0x1f4*i+0x124,value)
    output=bytes(output);_,target,after_identity=projection(output)
    if identity!=after_identity:
        raise Rejected('Opening projection changed identity')
    proof=dict(format=1,franchise_id=bindings['franchise_id'],bindings_sha256=_hash(_json(bindings).encode()),
        source=source,before_payload_sha256=_hash(payload),after_payload_sha256=_hash(output),
        finance_hex=target.hex(),identity_sha256=_hash(identity),game_dollar_scale=scale,
        opening_obligations=obligations,signing_authorized=False)
    return output,proof


def verify(store,db,payload,*,proof=None):
    from franchise.saved_checkpoint import projection
    from tools.inspect_franchise_calendar import inspect_calendar
    proof=record(db) if proof is None else proof
    if proof is None:return False
    if proof.get('format')!=1 or proof.get('signing_authorized') is not False or not proof.get('source'):
        raise Rejected('Invalid recorded opening cap checkpoint')
    native,finance,identity=projection(payload)
    expected=bytearray.fromhex(proof['finance_hex']);comparable=bytearray(finance)
    if len(expected)!=len(comparable) or _hash(identity)!=proof['identity_sha256']:
        raise Rejected('Saved opening ownership, terms or identity changed')
    # Same-year play can advance; no rollback or new-season opening replay.
    calendar=inspect_calendar(native)
    if struct.unpack_from('<I',expected,36)[0]!=calendar['season_index']:
        raise Rejected('Opening projection cannot carry across seasons')
    old_tick=struct.unpack_from('<I',expected,40)[0]
    if calendar['counter_08_raw']<old_tick:
        raise Rejected('Opening calendar moved backward')
    for offset in (16,20,28,32,40):comparable[offset:offset+4]=expected[offset:offset+4]
    if comparable!=expected:
        raise Rejected('Saved opening cap checkpoint changed')
    ledgers=store._load_teams(db,TEAMS)
    payrolls=current_payrolls(ledgers,proof['game_dollar_scale'],finance)
    if payrolls!=[struct.unpack_from('<I',finance,48+12*i)[0] for i in range(32)]:
        raise Rejected('Opening saved payroll differs from exact durable books')
    if any(parse_amount(proof['opening_obligations'][t])!=ledger.charges[0] for t,ledger in ledgers.items()):
        raise Rejected('Opening budgets cannot be reapplied after spending')
    return True


def register(store,proof,payload):
    """Persist evidence in a new private DB; neither game nor source files written."""
    with store._connection(write=True) as db:
        if record(db) is not None or db.execute('SELECT 1 FROM guest_signings LIMIT 1').fetchone():
            raise Rejected('Opening checkpoint already exists or negotiation started')
        if _hash(payload)!=proof['after_payload_sha256']:
            raise Rejected('Prepared opening image changed')
        verify(store,db,payload,proof=proof)
        db.execute('INSERT INTO franchise_metadata VALUES (?,?)',(KEY,_json(proof)))


def restore_plans(store,db,payload,*,source_epoch,live_projection,finance_payrolls):
    """Rebind all32 already-accounted budgets; no top-ups or signing permits."""
    from franchise.saved_checkpoint import projection,verify as verify_checkpoint
    proof=record(db)
    if proof is None:return None
    verify_checkpoint(store,db,payload)
    native,finance,identity=projection(payload)
    observed=bytearray(finance)
    for i,value in enumerate(finance_payrolls):struct.pack_into('<I',observed,48+12*i,value)
    if live_projection!={'finance':_hash(bytes(observed)),'identity':_hash(identity)}:
        raise Rejected('Live opening contracts or ownership differ from saved source')
    ledgers=store._load_teams(db,TEAMS)
    payrolls=current_payrolls(ledgers,proof['game_dollar_scale'],finance)
    expected=[struct.unpack_from('<I',finance,48+12*i)[0] for i in range(32)]
    if payrolls!=expected:
        raise Rejected('Recorded budgets disagree with current saved payrolls')
    raw=projection(native)[1]
    return [dict(format='native-cap-restore-v1',source_epoch=source_epoch,team_index=i,
        native_payroll_raw=struct.unpack_from('<I',raw,48+12*i)[0],enforced_payroll_raw=payrolls[i],
        finance_sha256=_hash(finance),identity_sha256=_hash(identity),canonical_payrolls=payrolls) for i in range(32)]
