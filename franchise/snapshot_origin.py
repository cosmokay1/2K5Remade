"""Explicit registry-to-database association, never active-guest or financial authority."""
import hashlib
import json

from franchise.cap import Rejected
from tools.franchise_snapshot_bindings import migrate_context, resolve_bindings
from tools.inspect_franchise_save import TEAMS

KEY = 'snapshot-origin-v1'


def _json(value):
    return json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False)


def _identity(bindings,payload):
    canonical=migrate_context(bindings,payload)
    context=canonical['game_context']
    # Source/load-image provenance and JSON representation do not choose a namespace.
    return dict(format=1,franchise_id=canonical['franchise_id'],
        baseline_year=canonical['baseline_year'],baseline_payload_sha256=canonical['baseline_payload_sha256'],
        personality_seed_sha256=hashlib.sha256(canonical['personality_seed'].encode()).hexdigest(),
        players_sha256=hashlib.sha256(_json(sorted(canonical['players'],key=lambda row:row['source_slot'])).encode()).hexdigest(),
        calendar={key:context[key] for key in ('season_year','season_index','money_scale','league_cap_raw')})


def _actors(store,db,bindings,payload):
    origin=store._franchise_origin(db)
    if origin is None or origin['seed']!=bindings['personality_seed']:
        raise Rejected('Snapshot registry differs from the persisted personality origin')
    teams={row[0] for row in db.execute('SELECT id FROM teams')}
    if teams!=set(TEAMS):
        raise Rejected('Snapshot association requires the complete supported league')
    members=resolve_bindings(bindings,payload)
    from franchise.initialization import initial_actor
    from franchise.store import from_config
    expected={team:from_config(json.loads(config)).registered_player_ids
              for team,config in db.execute('SELECT id,config FROM teams')}
    actors={team:set() for team in teams}
    generated={}
    # Check immutable actor origins, not every financial posting. Replaying all
    # club books here would duplicate transaction validation and can exceed the
    # handshake deadline on real leagues with every actor registered per club.
    for team,key,serialized in db.execute("SELECT team_id,request_key,payload FROM events WHERE kind='actor'"):
        event=json.loads(serialized)
        if type(event) is not dict or set(event)!={'player_id','actor','posting'}:
            raise Rejected('Invalid persisted actor registration')
        player=event['player_id']
        if type(player) is not str or team not in actors or key!='actor:'+player or player in actors[team]:
            raise Rejected('Invalid persisted actor registration')
        if player not in generated:
            generated[player]=initial_actor(origin['seed'],player)
        if _json(event['actor'])!=_json(generated[player]):
            raise Rejected('Persisted actor differs from its franchise personality origin')
        actors[team].add(player)
    if (any(not expected[team]<=actors[team] for team in teams) or
            set().union(*actors.values())!={player['player_id'] for player in members.values()}):
        raise Rejected('Snapshot player identities differ from the persisted actor registry')
    return members


def bind(store,bindings,payload):
    """Explicitly register once, preserving actor state and original journal bytes.

    The store's ordinary write guard rejects pending guest work. Existing matching
    origins are idempotent, and different namespaces require a separate verified
    migration. This command does not edit the supplied registry or game save.
    """
    bindings=json.loads(_json(bindings))
    identity=_identity(bindings,payload)
    with store._connection(write=True) as db:
        identity['bootstrap_sha256']=store._checkpoint_hash(list(db.execute('SELECT id,config FROM teams ORDER BY id')))
        members=_actors(store,db,bindings,payload)
        row=db.execute('SELECT value FROM franchise_metadata WHERE key=?',(KEY,)).fetchone()
        if row is not None:
            if _json(json.loads(row[0]))!=_json(identity):
                raise Rejected('Database already belongs to a different snapshot registry')
        else:
            expected={player['player_id']:player['team'] for player in members.values() if player['team']!='free_agents'}
            if dict(db.execute('SELECT player_id,team_id FROM ownership'))!=expected:
                raise Rejected('Initial snapshot ownership differs from the database')
            db.execute('INSERT INTO franchise_metadata VALUES (?,?)',(KEY,_json(identity)))
        return identity


def verify(store,bindings,payload):
    """Read the association and bootstrap fingerprint, without replaying every club.

    Actor origins are exhaustively checked at registration. Current actor history,
    money and ownership are validated by their transaction/checkpoint operations.

    In particular, recovery may observe a saved signing before ledger settlement.
    It must not lose its namespace just because those temporary owners differ.
    """
    bindings=json.loads(_json(bindings))
    identity=_identity(bindings,payload)
    with store._connection() as db:
        identity['bootstrap_sha256']=store._checkpoint_hash(list(db.execute('SELECT id,config FROM teams ORDER BY id')))
        row=db.execute('SELECT value FROM franchise_metadata WHERE key=?',(KEY,)).fetchone()
        if row is None or _json(json.loads(row[0]))!=_json(identity):
            raise Rejected('Explicit matching snapshot/database association required')
        origin=store._franchise_origin(db)
        if origin is None or origin['seed']!=bindings['personality_seed']:
            raise Rejected('Snapshot registry differs from the persisted personality origin')
    return identity
