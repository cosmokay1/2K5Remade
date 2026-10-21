"""Durable saved-signing coordination for cooperative franchise clients.

No guest memory/file writes. Prepared work freezes this
store's other writes. A native coordinator still must apply/save/reload safely.
Old writers that do not implement the pending-work guard are unsupported.
"""
import hashlib
import json

from franchise.cap import Offer, Rejected
from franchise.guest_contracts import GuestContractTerms, GUEST_CONTRACT_FORMAT, SOFTDRINK_CONTRACT_FORMAT
from tools.confirm_saved_signing import confirm_saved_signing
from tools.export_legacy_contracts import legacy_contracts
from tools.franchise_snapshot_bindings import resolve_bindings, binding_money_scale
from tools.inspect_franchise_cap import inspect_cap
from tools.inspect_franchise_save import TEAMS


def _json(value):
    return json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':'))


def _hash(payload):
    return hashlib.sha256(payload).hexdigest()


def _access(check):
    if not callable(check):
        raise ValueError('A current authorization/quiescence check is required')
    if check() is False:
        raise Rejected('Required authorization/quiescence check did not succeed')


def _before_books(store,db,bindings,payload,offer,guest_offer,team_id,*,owned=False,native_signing=False):
    members=resolve_bindings(bindings,payload)
    player=[p for p in members.values() if p['player_id']==offer.player_id]
    if len(player)!=1 or player[0]['team']!=(team_id if owned else 'free_agents'):
        raise Rejected('Bound candidate with matching saved ownership required')
    scale=binding_money_scale(bindings)
    contract_format=SOFTDRINK_CONTRACT_FORMAT if scale==4 else GUEST_CONTRACT_FORMAT
    if type(guest_offer) is not dict or set(guest_offer)!={'amount_word','flags_word'}:
        raise ValueError('Complete captured guest offer required')
    if GuestContractTerms.from_context(**guest_offer).to_offer(offer.player_id,contract_format=contract_format)!=offer:
        raise Rejected('Captured terms differ from accepted proposal')
    if {row[0] for row in db.execute('SELECT id FROM teams')}!=set(TEAMS):
        raise Rejected('Complete supported league books required')
    from franchise.saved_checkpoint import projection,verify,charges as checkpoint_charges,verify_terms
    native,_,_=projection(payload)
    recorded=verify(store,db,payload) if owned or native_signing else False
    if native_signing and not recorded:
        raise Rejected('Native free-agent signing requires recorded complete cap books')
    cap=inspect_cap(native)
    if not recorded and any(row['original_team_flag_raw'] and row['original_first_year_accumulator_dollars']
           for row in cap['teams'].values()):
        raise Rejected('Unresolved guest first-year cap adjustments')
    saved=legacy_contracts(bindings,native)
    ledgers=store._load_teams(db,TEAMS)
    for team,ledger in ledgers.items():
        if ledger.cash_snapshot() is None:
            raise Rejected('Explicit coverage of league cash obligations required before guest signing')
        contracts=saved[team]
        financial=ledger.financial_snapshot()
        from franchise.opening_native import record as opening_record
        charges=checkpoint_charges(ledger,contracts,include_opening_adjustments=opening_record(db) is not None) if owned or native_signing else [
            sum(row[i] if i<len(row) else 0 for row in [c.charges() for c in contracts])
            for i in range(max((len(c.charges()) for c in contracts),default=0))]
        def trim(values):
            values=list(values)
            while values and values[-1]==0: values.pop()
            return values
        if (financial['cap']!=cap['league_cap_dollars']*scale
                or financial['signed_players']!=sorted(c.player_id for c in contracts)
                or trim(ledger.charges)!=trim(charges)):
            raise Rejected('Saved roster charges differ from league books; guest projection is unsupported')
        if owned or native_signing:
            verify_terms(ledger,contracts,original_sources=not recorded)
            continue
        for record in contracts:
            legacy=ledger._legacy_contracts.get(record.player_id)
            if legacy is not None:
                expected,actual=legacy.to_dict(),record.to_dict()
                expected.pop('source');actual.pop('source')
                if expected!=actual: raise Rejected('Saved legacy terms differ from league books')
            else:
                active=ledger.active_contract(record.player_id)
                observed=GuestContractTerms(record.amount_word,record.bonus_code,record.shape_code,record.original_years)
                if (active is None or active.elapsed_years or active.bonus_layers
                        or record.remaining_years!=record.original_years
                        or observed.to_offer(record.player_id,contract_format=contract_format)!=active.offer):
                    raise Rejected('Saved active terms differ from supported league books')
    return contract_format,ledgers[team_id]


def _read(store,db,request_id):
    row=db.execute('SELECT team_id,state,intent,before_payload,after_payload,confirmation FROM guest_signings WHERE request_id=?',(request_id,)).fetchone()
    if row is None: raise Rejected('Unknown guest signing journal')
    team,state,serialized,before,after,confirmation=row
    intent=json.loads(serialized)
    if intent.get('format')==2:
        from franchise.guest_application import read_amendment
        return read_amendment(store,db,request_id)
    fields={'format','request_id','team_id','proposal_request_id','expected_revision','proposal_sha256',
            'bindings','bindings_sha256','before_payload_sha256','guest_offer','offer','contract_format'}
    if (type(intent) is not dict or not fields<=set(intent) or set(intent)-fields-{'native_source'} or intent['format']!=1
            or type(intent['format']) is not int or type(intent['expected_revision']) is not int
            or intent['request_id']!=request_id or intent['team_id']!=team
            or _hash(before)!=intent['before_payload_sha256']
            or _hash(_json(intent['bindings']).encode())!=intent['bindings_sha256']):
        raise ValueError('Guest signing journal input fingerprint mismatch')
    proposal=db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=? AND kind='dialogue'",
                        (team,'dialogue:'+intent['proposal_request_id'])).fetchone()
    if proposal is None or _hash(_json(json.loads(proposal[0])['event']).encode())!=intent['proposal_sha256']:
        raise ValueError('Journal source proposal changed')
    event=json.loads(proposal[0])['event']
    store._validate_dialogue(event)
    if (event['outcome']!='accepted_proposal' or _json(event['offer'])!=_json(intent['offer'])
            or event['evidence']['financial_revision']!=intent['expected_revision']
            or event.get('contract_format')!=intent['contract_format']):
        raise ValueError('Journal intent differs from accepted proposal')
    if 'native_source' in intent:
        from franchise.salary_clock import bind_salary_clock
        n=intent['native_source']
        if type(n) is not dict or set(n)!={'salary_clock','observation','live_projection','preview','opening_books_sha256'}:
            raise ValueError('Complete native free-agent source required')
        if bind_salary_clock(intent['bindings'],before,n['observation'],n['salary_clock']).elapsed_periods:
            raise ValueError('Native free-agent journal lacks supported remaining-salary accounting')
        from tools.franchise_snapshot_bindings import resolve_signing_candidate
        candidate=resolve_signing_candidate(intent['bindings'],before,n['observation']['biography'])
        if candidate['candidate_player_id']!=intent['offer']['player_id'] or n['observation']['team']['table_index']!=TEAMS.index(team):
            raise ValueError('Native free-agent journal player/team changed')
        from franchise.free_agent_application import live_source,target
        live_source(intent['bindings'],before,intent['offer']['player_id'],n['live_projection'])
        ledger=store._load(db,team)
        if n['preview']!=event['proposal_preview'] or n['opening_books_sha256']!=store._checkpoint_hash(ledger._opening_books.to_dict()):
            raise ValueError('Native free-agent source or accepted finances changed')
        target(intent,before)
    sign=db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=? AND kind='sign'",(team,'sign:'+request_id)).fetchone()
    proof=None
    if state=='settled':
        if after is None or confirmation is None or sign is None:
            raise ValueError('Settled journal has no saved proof or ledger signing')
        proof=_confirm(intent,before,after)
        if _json(proof)!=_json(json.loads(confirmation)) or json.loads(sign[0]).get('proposal_request_id')!=intent['proposal_request_id']:
            raise ValueError('Saved signing proof differs from journal or ledger')
    elif state not in ('prepared','cancelled') or after is not None or confirmation is not None or sign is not None:
        raise ValueError('Unsettled journal has inconsistent saved or financial effects')
    return intent,state,before,after,proof


def _confirm(intent,before,after):
    if 'native_source' in intent:
        from franchise.free_agent_application import confirm
        return confirm(intent,before,after)
    return confirm_saved_signing(intent['bindings'],before,after,
            expected_before_sha256=intent['before_payload_sha256'],offer=Offer.from_dict(intent['offer']),
            guest_offer=intent['guest_offer'],team_id=intent['team_id'])


def _validate_live_projection(live_projection):
    if (type(live_projection) is not dict or set(live_projection) != {'finance', 'identity'} or
            any(type(v) is not str or len(v) != 64 or any(c not in '0123456789abcdef' for c in v)
                for v in live_projection.values())):
        raise ValueError('Canonical live financial and identity digests required')


def _check_live_preparation(payload, bindings, player_id, live_projection):
    if live_projection is None:
        return  # Direct offline journal callers do not claim a live capture.
    _validate_live_projection(live_projection)
    from tools.franchise_finance_state import saved_finance_state
    from tools.franchise_identity_state import saved_identity_state
    actual = (live_projection['finance'], live_projection['identity'])
    full = (saved_finance_state(payload), saved_identity_state(payload))
    if actual == tuple(_hash(value) for value in full):
        return
    # Bind the only allowed transient omission to the durable accepted proposal,
    # never to a client-supplied slot or an arbitrary missing player.
    members = resolve_bindings(bindings, payload)
    selected = [slot for slot, player in members.items()
                if player['player_id'] == player_id and player['team'] == 'free_agents']
    if len(selected) == 1:
        from tools.franchise_offer_state import saved_offer_screen_state
        pending = saved_offer_screen_state(payload, selected[0])
        if actual == tuple(_hash(value) for value in pending):
            return
    raise Rejected('Live financial/identity projections differ from the saved state or bound pending offer; signing remains held')


def prepare(store,team_id,proposal_request_id,request_id,*,bindings,before_payload,guest_offer,
            expected_before_sha256,expected_revision,access_check,live_projection=None,observation=None,salary_clock=None):
    """Persist original save/accepted terms. This does not authorize guest writes."""
    if (any(type(v) is not str or not v.strip() for v in (team_id,proposal_request_id,request_id))
            or request_id==proposal_request_id or type(before_payload) is not bytes
            or _hash(before_payload)!=expected_before_sha256 or type(expected_revision) is not int):
        raise ValueError('Distinct journal identities, pinned save and exact revision required')
    native=salary_clock is not None or observation is not None
    if native:
        with store._connection() as db:
            proposal=db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=? AND kind='dialogue'",(team_id,'dialogue:'+proposal_request_id)).fetchone()
        if proposal and json.loads(proposal[0])['event']['outcome']=='accepted_amendment_proposal':
            from franchise.guest_application import prepare_amendment
            return prepare_amendment(store,team_id,proposal_request_id,request_id,bindings=bindings,
                before_payload=before_payload,guest_offer=guest_offer,expected_before_sha256=expected_before_sha256,
                expected_revision=expected_revision,access_check=access_check,live_projection=live_projection,
                observation=observation,salary_clock=salary_clock)
        from franchise.salary_clock import bind_salary_clock
        scope=bind_salary_clock(bindings,before_payload,observation,salary_clock)
        if scope.elapsed_periods:
            raise Rejected('In-season free-agent salary proration is not yet supported; no full-year overcharge')
    bindings=json.loads(_json(bindings));guest_offer=json.loads(_json(guest_offer))
    with store._connection(write=True,guest_recovery=True) as db:
        _access(access_check)
        prior=db.execute('SELECT 1 FROM guest_signings WHERE request_id=?',(request_id,)).fetchone()
        if prior:
            intent,state,before,_,_=_read(store,db,request_id)
            if (state!='prepared' or intent['team_id']!=team_id or intent['proposal_request_id']!=proposal_request_id
                    or before!=before_payload or _json(intent['bindings'])!=_json(bindings)
                    or _json(intent['guest_offer'])!=_json(guest_offer) or intent['expected_revision']!=expected_revision):
                raise Rejected('Journal preparation retry changed or is already resolved')
            if native:
                if intent.get('native_source',{}).get('salary_clock')!=salary_clock or intent['native_source']['observation']!=observation or intent['native_source']['live_projection']!=live_projection:
                    raise Rejected('Native free-agent preparation retry changed')
                from franchise.free_agent_application import live_source
                live_source(bindings,before_payload,intent['offer']['player_id'],live_projection)
            else:_check_live_preparation(before_payload, bindings, intent['offer']['player_id'], live_projection)
            return {'request_id':request_id,'state':'prepared','before_payload_sha256':expected_before_sha256,'write_authorized':False}
        if db.execute("SELECT 1 FROM guest_signings WHERE state='prepared'").fetchone():
            raise Rejected('Another guest signing awaits recovery')
        if db.execute('SELECT 1 FROM events WHERE team_id=? AND request_key IN (?,?)',
                      (team_id,'sign:'+request_id,'dialogue:'+request_id)).fetchone():
            raise Rejected('Journal request already belongs to financial or negotiation history')
        story=store._settlement_story(db,team_id,proposal_request_id,request_id)
        offer=Offer.from_dict(story['offer'])
        if native:
            from franchise.free_agent_application import live_source
            live_source(bindings,before_payload,offer.player_id,live_projection)
        else:_check_live_preparation(before_payload, bindings, offer.player_id, live_projection)
        contract_format,ledger=_before_books(store,db,bindings,before_payload,offer,guest_offer,team_id,native_signing=native)
        if (story.get('contract_format')!=contract_format or expected_revision!=story['evidence']['financial_revision']
                or store._checkpoint_hash(ledger.preview_offer(offer,expected_revision))!=store._checkpoint_hash(story['proposal_preview'])):
            raise Rejected('Journal proposal, format or financial preview changed')
        if db.execute('SELECT 1 FROM ownership WHERE player_id=?',(offer.player_id,)).fetchone():
            raise Rejected('Player is already contracted')
        source=db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?",(team_id,'dialogue:'+proposal_request_id)).fetchone()
        intent=dict(format=1,request_id=request_id,team_id=team_id,proposal_request_id=proposal_request_id,
            expected_revision=expected_revision,proposal_sha256=_hash(_json(json.loads(source[0])['event']).encode()),
            bindings=bindings,bindings_sha256=_hash(_json(bindings).encode()),before_payload_sha256=expected_before_sha256,
            guest_offer=guest_offer,offer=offer.to_dict(),contract_format=contract_format)
        if native:
            from tools.reconcile_signing_context import reconcile_signing_context
            checkpoint=reconcile_signing_context(bindings,before_payload,observation,store,expected_revision=expected_revision)
            if checkpoint['team_id']!=team_id or checkpoint['player_id']!=offer.player_id:
                raise Rejected('Native free-agent ownership context changed')
            intent['native_source']=dict(salary_clock=salary_clock,observation=observation,live_projection=live_projection,
                preview=story['proposal_preview'],opening_books_sha256=store._checkpoint_hash(ledger._opening_books.to_dict()))
            from franchise.free_agent_application import target
            target(intent,before_payload)
        db.execute("INSERT INTO guest_signings VALUES (?,?,'prepared',?,?,NULL,NULL)",(request_id,team_id,_json(intent),before_payload))
        _access(access_check)
        return {'request_id':request_id,'state':'prepared','before_payload_sha256':expected_before_sha256,'write_authorized':False}


def settle(store,request_id,after_payload,*,access_check,receipt_check=None):
    """Confirm saved effects and atomically commit ledger plus journal outcome."""
    if receipt_check is not None and not callable(receipt_check):
        raise ValueError('Callable receipt check required')
    with store._connection() as db:
        row=db.execute('SELECT intent FROM guest_signings WHERE request_id=?',(request_id,)).fetchone()
    if row and json.loads(row[0]).get('format')==2:
        from franchise.guest_application import settle_amendment
        return settle_amendment(store,request_id,after_payload,access_check=access_check,receipt_check=receipt_check)
    with store._connection(write=True,guest_recovery=True) as db:
        _access(access_check)
        intent,state,before,after,proof=_read(store,db,request_id)
        if state=='cancelled': raise Rejected('Guest signing was cancelled')
        if state=='settled':
            if after_payload!=after: raise Rejected('Settled retry changed the confirmed save')
        else:
            proof=_confirm(intent,before,after_payload)
            db.execute("UPDATE guest_signings SET state='settled',after_payload=?,confirmation=? WHERE request_id=?",
                       (after_payload,_json(proof),request_id))
        receipt=store._sign(intent['team_id'],request_id,None,intent['expected_revision'],
            access_check=access_check,proposal_request_id=intent['proposal_request_id'],_db=db)
        if receipt_check is not None:
            receipt_check(receipt) # Unsendable replies roll back journal and finances together.
            _access(access_check)
        return receipt


def cancel(store,request_id,current_payload,*,game_stopped_check):
    """Release pending work only against its original save with a stopped game.

    Caller must verify quiescence; this function never restores files or memory.
    Recovery remains available while AI is disabled and never re-enables it.
    """
    with store._connection(write=True,guest_recovery=True) as db:
        _access(game_stopped_check)
        _,state,before,_,_=_read(store,db,request_id)
        if state=='settled' or type(current_payload) is not bytes or current_payload!=before:
            raise Rejected('Stopped-game cancellation requires the unchanged original save')
        db.execute("UPDATE guest_signings SET state='cancelled' WHERE request_id=?",(request_id,))
        _access(game_stopped_check)
        return {'request_id':request_id,'state':'cancelled'}


def inspect(store,request_id,current_payload,*,live_projection=None):
    """Read recovery status/verified backups even while AI is disabled."""
    with store._connection() as db:
        intent,state,before,after,proof=_read(store,db,request_id)
        store._load(db,intent['team_id'])
        position='before' if current_payload==before else 'confirmed_after' if after is not None and current_payload==after else 'unrecognized'
        candidate=None
        if state=='prepared' and position=='unrecognized':
            try:
                if intent['format']==2:
                    from franchise.guest_application import confirm_amendment
                    candidate=confirm_amendment(intent,before,current_payload)
                else:
                    candidate=_confirm(intent,before,current_payload)
            except ValueError:
                pass
            else:
                position='candidate_after'
        result={'request_id':request_id,'state':state,'save_position':position,
                'before_payload':before,'after_payload':after,'confirmation':proof,
                'candidate_confirmation':candidate,'write_authorized':False}
        if live_projection is not None:
            _validate_live_projection(live_projection)
            if state=='cancelled':
                raise Rejected('Cancelled signing cannot validate a live application')
            from tools.franchise_offer_state import expected_signed_state
            if intent['format']==2:
                from franchise.guest_application import amendment_target
                finance,identity,_=amendment_target(intent,before);target=(finance,identity)
            elif 'native_source' in intent:
                from franchise.free_agent_application import target as free_target
                finance,identity,_=free_target(intent,before);target=(finance,identity)
            else:
                target=expected_signed_state(intent['bindings'],before,
                    offer=Offer.from_dict(intent['offer']),guest_offer=intent['guest_offer'],team_id=intent['team_id'])
            result['live_application_matches']=tuple(live_projection[k] for k in ('finance','identity'))==tuple(_hash(v) for v in target)
        return result
