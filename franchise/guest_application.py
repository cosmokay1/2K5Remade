"""Accepted imported-contract journal and one-use native application evidence.

The native owner still checks the exact live state under its guest lock. No
function here writes guest memory, changes a save, or enables remote control.
"""
import hashlib
import json
import struct
from types import SimpleNamespace
from franchise.cap import Offer, Rejected, json_amount
from franchise.legacy_amendments import amendment_scope_from_dict
from franchise.guest_signing import _json, _hash, _access, _before_books
from tools.franchise_finance_state import saved_finance_state
from tools.franchise_identity_state import saved_identity_state
from tools.franchise_offer_state import expected_amended_state
from tools.inspect_franchise_save import TEAMS
from franchise.saved_checkpoint import projection


def prepare_amendment(store,team,proposal_id,request_id,*,bindings,before_payload,guest_offer,
                      expected_before_sha256,expected_revision,access_check,live_projection,observation,salary_clock):
    from franchise.salary_clock import bind_salary_clock
    from tools.reconcile_signing_context import reconcile_signing_context
    if (type(request_id) is not str or not request_id.strip() or request_id==proposal_id or
            type(expected_revision) is not int or _hash(before_payload)!=expected_before_sha256):
        raise ValueError('Distinct amendment journal identity and pinned save required')
    scope=bind_salary_clock(bindings,before_payload,observation,salary_clock)
    if live_projection!={'finance':_hash(projection(before_payload)[1]),
                         'identity':_hash(saved_identity_state(before_payload))}:
        raise Rejected('Live amendment state differs from the complete saved league')
    # Read-only checkpoint precedes the write transaction. The exact proposal,
    # book comparison and hashes are checked again under the write reservation.
    checkpoint=reconcile_signing_context(bindings,before_payload,observation,store,
        expected_revision=expected_revision,guest_offer=guest_offer,amendment_scope=scope)
    if checkpoint['team_id']!=team: raise Rejected('Owning team differs from live checkpoint')
    with store._connection(write=True,guest_recovery=True) as db:
        _access(access_check)
        prior=db.execute('SELECT intent FROM guest_signings WHERE request_id=?',(request_id,)).fetchone()
        if prior:
            intent,state,before,_,_=read_amendment(store,db,request_id)
            if (state!='prepared' or before!=before_payload or intent['proposal_request_id']!=proposal_id or
                    intent['guest_offer']!=guest_offer or intent['scope']!=scope.to_dict() or
                    intent['expected_revision']!=expected_revision or intent['team_id']!=team):
                raise Rejected('Amendment preparation retry changed')
        else:
            if db.execute("SELECT 1 FROM guest_signings WHERE state='prepared'").fetchone():
                raise Rejected('Another native signing awaits recovery')
            if db.execute("SELECT 1 FROM guest_signings WHERE state='settled' AND team_id!=? AND json_extract(intent,'$.format')=2",(team,)).fetchone():
                raise Rejected('Cross-team amendment chains require a multi-team native cap adapter')
            proposal=store._accepted_amendment(db,team,proposal_id)
            offer=Offer.from_dict(proposal['offer'])
            contract_format,ledger=_before_books(store,db,bindings,before_payload,offer,guest_offer,team,owned=True)
            comparison=store._preview_legacy_amendment(db,team,ledger,offer,expected_revision,scope=scope)
            if (proposal['evidence']['financial_revision']!=expected_revision or
                    proposal.get('contract_format')!=contract_format or
                    proposal['proposal_preview']!=comparison or not comparison['within_modeled_cap']):
                raise Rejected('Accepted amendment differs from current salary/cap checkpoint')
            if live_projection!={'finance':_hash(projection(before_payload)[1]),
                                 'identity':_hash(saved_identity_state(before_payload))}:
                raise Rejected('Live amendment state differs from the complete saved league')
            intent=dict(format=2,request_id=request_id,team_id=team,proposal_request_id=proposal_id,
                expected_revision=expected_revision,bindings=bindings,guest_offer=guest_offer,
                before_payload_sha256=expected_before_sha256,offer=offer.to_dict(),scope=scope.to_dict(),
                proposal_sha256=store._checkpoint_hash(proposal),comparison=comparison,
                salary_clock=salary_clock,observation=observation)
            if db.execute("SELECT 1 FROM guest_signings WHERE state='settled' AND json_extract(intent,'$.format')=2").fetchone():
                finance=projection(before_payload)[1]
                _,flag,accumulator=struct.unpack_from('<III',finance,48+12*TEAMS.index(team))
                if flag and accumulator:intent['accounted_accumulator_before_raw']=accumulator
            previous=ledger._legacy_amendments.get(offer.player_id)
            from franchise.opening_native import record as opening_record
            if previous is None and opening_record(db) is not None:
                from franchise.legacy_contracts import imported_components
                base,other=imported_components(ledger._opening_books,ledger._legacy_contracts[offer.player_id])
                intent['source_components']=dict(base=[json_amount(v) for v in base],nonbase=[json_amount(v) for v in other],
                    opening_books_sha256=store._checkpoint_hash(ledger._opening_books.to_dict()))
            if previous is not None:
                intent['previous_amendment']=previous.to_dict()
            # Build and validate the representable cap target before reserving.
            amendment_target(intent,before_payload)
            db.execute("INSERT INTO guest_signings VALUES (?,?,'prepared',?,?,NULL,NULL)",
                       (request_id,team,_json(intent),before_payload))
        _access(access_check)
        return dict(request_id=request_id,state='prepared',before_payload_sha256=expected_before_sha256,write_authorized=False)


def amendment_target(intent,before):
    from tools.export_legacy_contracts import legacy_contracts
    from franchise.native_cap import amendment_payroll_projection
    from franchise.legacy_contracts import original_annual_rows
    offer=Offer.from_dict(intent['offer']);team=intent['team_id'];index=TEAMS.index(team)
    normalized,finance,_=projection(before)
    original=next(c for c in legacy_contracts(intent['bindings'],normalized)[team] if c.player_id==offer.player_id)
    rows=original_annual_rows(original.amount_word,original.bonus_code,original.shape_code,original.original_years)[-original.remaining_years:]
    offset=48+12*index
    payroll,flag,accumulator=struct.unpack_from('<III',finance,offset)
    bonus=sum(r['allocated_bonus_dollars'] for r in rows)*original.game_dollar_scale
    acceleration=bool(flag and bonus)
    native,identity=expected_amended_state(intent['bindings'],normalized,offer=offer,
        guest_offer=intent['guest_offer'],team_id=team,native_bonus_accelerated=acceleration)
    after_accumulator=struct.unpack_from('<I',native,offset+8)[0]
    raw_payroll=struct.unpack_from('<I',saved_finance_state(normalized),offset)[0]
    cap=amendment_payroll_projection(intent['comparison'],native_payroll_before_raw=raw_payroll,
        native_old_charge=original.charges()[0],native_new_charge=offer.charges(5)[0],
        native_old_unamortized_bonus=bonus,native_accumulator_before_raw=accumulator,
        native_accumulator_after_raw=after_accumulator,team_adjustment_applies=bool(flag),
        game_dollar_scale=original.game_dollar_scale,
        accounted_accumulator_before_raw=intent.get('accounted_accumulator_before_raw',0))
    if not cap['within_cap']: raise Rejected('Native salary/cap target has insufficient room')
    target=bytearray(native)
    for i in range(32):
        if i!=index:target[48+12*i:52+12*i]=finance[48+12*i:52+12*i]
    struct.pack_into('<I',target,offset,cap['enforced_payroll_raw'])
    return bytes(target),identity,cap


def read_amendment(store,db,request_id):
    row=db.execute('SELECT team_id,state,intent,before_payload,after_payload,confirmation FROM guest_signings WHERE request_id=?',(request_id,)).fetchone()
    if row is None: raise Rejected('Unknown native amendment journal')
    team,state,text,before,after,proof=row;intent=json.loads(text)
    fields={'format','request_id','team_id','proposal_request_id','expected_revision','bindings','guest_offer',
            'before_payload_sha256','offer','scope','proposal_sha256','comparison','salary_clock','observation'}
    if (not fields<=set(intent) or set(intent)-fields-{'previous_amendment','accounted_accumulator_before_raw','source_components'} or type(intent['format']) is not int or intent['format']!=2 or
            intent['request_id']!=request_id or intent['team_id']!=team or _hash(before)!=intent['before_payload_sha256']):
        raise ValueError('Amendment journal fingerprint mismatch')
    from franchise.salary_clock import bind_salary_clock
    if bind_salary_clock(intent['bindings'],before,intent['observation'],intent['salary_clock']).to_dict()!=intent['scope']:
        raise ValueError('Amendment journal salary clock changed')
    source=db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=? AND kind='dialogue'",
                      (team,'dialogue:'+intent['proposal_request_id'])).fetchone()
    if source is None: raise ValueError('Missing accepted amendment history')
    event=json.loads(source[0])['event'];store._validate_dialogue(event)
    if (store._checkpoint_hash(event)!=intent['proposal_sha256'] or event['outcome']!='accepted_amendment_proposal' or
            event['offer']!=intent['offer'] or event['proposal_preview']!=intent['comparison']):
        raise ValueError('Amendment journal changed accepted terms')
    if 'accounted_accumulator_before_raw' in intent:
        prior=db.execute("SELECT after_payload FROM guest_signings WHERE state='settled' AND team_id=? AND rowid<(SELECT rowid FROM guest_signings WHERE request_id=?) ORDER BY rowid DESC LIMIT 1",(team,request_id)).fetchone()
        value=intent['accounted_accumulator_before_raw']
        if prior is None or type(value) is not int or value<=0:
            raise ValueError('Accounted accumulator lacks a prior saved settlement')
        current=projection(before)[1];recorded=projection(prior[0])[1];offset=48+12*TEAMS.index(team)
        if (current[offset+4:offset+12]!=recorded[offset+4:offset+12] or
                struct.unpack_from('<I',current,offset+8)[0]!=value):
            raise ValueError('Recorded accumulator coverage changed')
    if 'source_components' in intent:
        from franchise.opening_native import record as opening_record
        from franchise.legacy_contracts import imported_components
        ledger=store._load(db,team)
        original=ledger._legacy_contracts[Offer.from_dict(intent['offer']).player_id]
        base,other=imported_components(ledger._opening_books,original)
        expected=dict(base=[json_amount(v) for v in base],nonbase=[json_amount(v) for v in other],
            opening_books_sha256=store._checkpoint_hash(ledger._opening_books.to_dict()))
        if opening_record(db) is None or 'previous_amendment' in intent or intent['source_components']!=expected:
            raise ValueError('Imported amendment components differ from recorded opening books')
    if 'previous_amendment' in intent:
        previous=intent['previous_amendment']
        prior=db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=? AND kind='legacy_amendment'",
            (team,'legacy-amendment:'+previous['request_id'])).fetchone()
        if prior is None or json.loads(prior[0])['agreement']!=previous:
            raise ValueError('Prior amendment differs from its durable settlement')
    posting=db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=? AND kind='legacy_amendment'",
                       (team,'legacy-amendment:'+request_id)).fetchone()
    if state=='settled':
        if after is None or proof is None or posting is None: raise ValueError('Amendment settlement is incomplete')
        posting=json.loads(posting[0])
        if (posting['proposal_request_id']!=intent['proposal_request_id'] or posting['scope']!=intent['scope'] or
                posting['expected_revision']!=intent['expected_revision']):
            raise ValueError('Amendment settlement differs from accepted journal')
        actual=confirm_amendment(intent,before,after)
        if actual!=json.loads(proof): raise ValueError('Amendment saved proof changed')
    elif state not in ('prepared','cancelled') or after is not None or proof is not None or posting is not None:
        raise ValueError('Unsettled amendment has financial or saved effects')
    return intent,state,before,after,json.loads(proof) if proof else None


def saved_amendment_projection(intent,before,after):
    """Normalize an in-memory comparison copy after verifying its saved cap.

    Original readers require roster-only payroll. The addon deliberately stores
    enforced payroll instead. Restore only that cached word in a private copy to
    reuse their strict roster validation, then put the verified cap word back in
    the canonical comparison. No save file is edited.
    """
    target,identity,cap=amendment_target(intent,before)
    index=TEAMS.index(intent['team_id']);offset=0x44A8+0x1F4*index+0x124
    if struct.unpack_from('<I',after,offset)[0]!=cap['enforced_payroll_raw']:
        raise ValueError('Saved payroll differs from accepted cap enforcement')
    normalized,finance,identity=projection(after)
    raw=struct.unpack_from('<I',saved_finance_state(normalized),48+12*index)[0]
    if raw!=cap['native_payroll_after_raw']:
        raise ValueError('Saved native roster payroll differs from accepted amendment')
    return finance,identity,normalized


def confirm_amendment(intent,before,after):
    from tools.confirm_saved_amendment import confirm_saved_amendment
    target,identity,cap=amendment_target(intent,before)
    finance,observed_identity,normalized=saved_amendment_projection(intent,before,after)
    if (finance,observed_identity)!=(target,identity):
        raise ValueError('Saved amendment differs from enforced cap/contract target')
    proof=confirm_saved_amendment(intent['bindings'],before,normalized,
        expected_before_sha256=intent['before_payload_sha256'],offer=Offer.from_dict(intent['offer']),
        guest_offer=intent['guest_offer'],team_id=intent['team_id'],comparison=intent['comparison'],
        previous_amendment=intent.get('previous_amendment'),source_components=intent.get('source_components'),
        accounted_accumulator_before_raw=intent.get('accounted_accumulator_before_raw',0))
    proof.update(normalized_comparison_sha256=proof['after_payload_sha256'],after_payload_sha256=_hash(after),
        saved_enforced_payroll_raw=cap['enforced_payroll_raw'])
    return proof


def settle_amendment(store,request_id,after_payload,*,access_check,receipt_check=None):
    with store._connection(write=True,guest_recovery=True) as db:
        _access(access_check)
        intent,state,before,after,proof=read_amendment(store,db,request_id)
        if state=='cancelled': raise Rejected('Amendment was cancelled')
        if state=='settled' and after!=after_payload: raise Rejected('Settled save retry changed')
        if state=='prepared':
            proof=confirm_amendment(intent,before,after_payload)
            agreement=store.commit_accepted_amendment(intent['team_id'],intent['proposal_request_id'],request_id,
                intent['expected_revision'],scope=amendment_scope_from_dict(intent['scope']),access_check=access_check,_db=db)
            db.execute("UPDATE guest_signings SET state='settled',after_payload=?,confirmation=? WHERE request_id=?",
                       (after_payload,_json(proof),request_id))
        else:
            store._load(db,intent['team_id'])
            agreement=json.loads(db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?",
                (intent['team_id'],'legacy-amendment:'+request_id)).fetchone()[0])['agreement']
        receipt=SimpleNamespace(request_id=request_id,offer=Offer.from_dict(agreement['offer']),
            revision=intent['expected_revision']+1,charges=tuple(agreement['combined_player_charges']))
        # Receipt money may be canonical rational strings; normalize exactly.
        from franchise.books import parse_amount
        receipt.charges=tuple(parse_amount(v) for v in receipt.charges)
        if receipt_check: receipt_check(receipt)
        _access(access_check)
        return receipt


def authorize(store,request_id,journal_id,current_payload,*,access_check,live_projection):
    """Persist a single issuance; a fresh remote control check is mandatory.

    A native deadline starts at request submission, not reply receipt. Retrying a
    lost issuance never produces a second permit. Recovery remains read-only.
    """
    from franchise.guest_signing import _read
    if (any(type(v) is not str or not v.strip() or len(v)>400 for v in (request_id,journal_id)) or request_id==journal_id):
        raise ValueError('Distinct bounded native issuance identities required')
    with store._connection(write=True,guest_recovery=True) as db:
        _access(access_check)
        intent,state,before,_,_=_read(store,db,journal_id)
        if state!='prepared' or before!=current_payload: raise Rejected('Prepared unchanged native source required')
        if intent['format']==2:
            _check={'finance':_hash(projection(before)[1]),'identity':_hash(saved_identity_state(before))}
            if live_projection!=_check: raise Rejected('Live amendment source changed')
            target,identity,cap=amendment_target(intent,before)
            pre=projection(before)[1]
            epoch=intent['salary_clock']['source_epoch']
        else:
            raise Rejected('Live issuance currently requires an imported amendment with a bound salary clock')
        # Other writes are already blocked by the pending journal. Recheck the
        # immutable proposal and full ledger replay before issuing authority.
        from franchise.saved_checkpoint import verify
        verify(store,db,before)
        ledger=store._load(db,intent['team_id'])
        comparison=store._preview_legacy_amendment(db,intent['team_id'],ledger,Offer.from_dict(intent['offer']),
            intent['expected_revision'],scope=amendment_scope_from_dict(intent['scope']))
        if comparison!=intent['comparison']: raise Rejected('Accepted finances changed before issuance')
        changes=[[i,value] for i,value in enumerate(target) if value!=pre[i]]
        if len(changes)>32: raise Rejected('Unexpected native amendment effect coverage')
        plan=dict(format='native-signing-permit-v1',journal_request_id=journal_id,source_epoch=epoch,
            team_index=TEAMS.index(intent['team_id']),source_slot=intent['observation']['biography']['source_slot'],
            guest_offer=intent['guest_offer'],before_finance_sha256=_hash(pre),identity_sha256=_hash(identity),
            after_finance_sha256=_hash(target),finance_changes=changes,native_payroll_raw=cap['native_payroll_after_raw'],
            enforced_payroll_raw=cap['enforced_payroll_raw'],valid_for_ms=5000)
        db.execute('CREATE TABLE IF NOT EXISTS guest_signing_authorizations (journal_id TEXT PRIMARY KEY REFERENCES guest_signings(request_id), request_id TEXT UNIQUE NOT NULL, plan TEXT NOT NULL)')
        if db.execute('SELECT 1 FROM guest_signing_authorizations WHERE journal_id=?',(journal_id,)).fetchone():
            raise Rejected('Native signing authorization already issued; inspect recovery instead of rearming')
        db.execute('INSERT INTO guest_signing_authorizations VALUES (?,?,?)',(journal_id,request_id,_json(plan)))
        _access(access_check)
        return dict(request_id=request_id,application_plan=plan)


def restore_cap(store,request_id,payload,*,source_epoch,loaded_payload_sha256,live_projection,finance_payrolls,connection_check):
    """Rebind recorded debt after load, without AI or another signing grant.

    Only cached payroll words may differ in the live comparison. Every contract,
    owner, flag, accumulator and calendar word must still match the saved proof.
    """
    if (type(source_epoch) is not int or not 0<source_epoch<2**64 or _hash(payload)!=loaded_payload_sha256 or
            type(finance_payrolls) is not list or len(finance_payrolls)!=32 or
            any(type(v) is not int or not 0<=v<=0xffffffff for v in finance_payrolls)):
        raise ValueError('Fresh loaded source and complete cached payroll sample required')
    _access(connection_check)
    with store._connection() as db:
        from franchise.opening_native import restore_plans
        opening=restore_plans(store,db,payload,source_epoch=source_epoch,
            live_projection=live_projection,finance_payrolls=finance_payrolls)
        if opening is not None:
            _access(connection_check)
            return dict(request_id=request_id,loaded_payload_sha256=loaded_payload_sha256,
                        cap_plan=opening[0],additional_cap_plans=opening[1:])
        journals=[row[0] for row in db.execute("SELECT request_id FROM guest_signings WHERE state!='cancelled' AND json_extract(intent,'$.format')=2 ORDER BY rowid DESC LIMIT 1")]
        if not journals:
            return dict(request_id=request_id,loaded_payload_sha256=loaded_payload_sha256,cap_plan=None)
        intent,state,before,after,_=read_amendment(store,db,journals[0])
        if payload==before and state=='prepared':
            prior=db.execute("SELECT request_id FROM guest_signings WHERE state='settled' AND json_extract(intent,'$.format')=2 ORDER BY rowid DESC LIMIT 1").fetchone()
            if prior is None:
                return dict(request_id=request_id,loaded_payload_sha256=loaded_payload_sha256,cap_plan=None)
            intent,state,before,after,_=read_amendment(store,db,prior[0])
        if state=='settled':
            from franchise.saved_checkpoint import verify
            verify(store,db,payload)
            _,target,identity=projection(payload)
            _,_,cap_projection=amendment_target(intent,before)
        else:
            confirm_amendment(intent,before,payload)
            target,identity,cap_projection=amendment_target(intent,before)
        observed=bytearray(target)
        for i,value in enumerate(finance_payrolls):struct.pack_into('<I',observed,48+12*i,value)
        if live_projection!={'finance':_hash(bytes(observed)),'identity':_hash(identity)}:
            raise Rejected('Loaded live contracts/calendar/ownership differ from the saved amendment')
        store._load(db,intent['team_id'])
        cap_plan=dict(format='native-cap-restore-v1',source_epoch=source_epoch,team_index=TEAMS.index(intent['team_id']),
            native_payroll_raw=cap_projection['native_payroll_after_raw'],enforced_payroll_raw=cap_projection['enforced_payroll_raw'],
            finance_sha256=_hash(target),identity_sha256=_hash(identity),
            canonical_payrolls=[struct.unpack_from('<I',target,48+12*i)[0] for i in range(32)])
        _access(connection_check)
        return dict(request_id=request_id,loaded_payload_sha256=loaded_payload_sha256,cap_plan=cap_plan)
