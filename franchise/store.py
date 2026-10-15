"""SQLite-backed transaction history for the supported prototype operations.

Each write rebuilds from immutable bootstrap data under a database write lock.
Contracts, ownership and optional story data commit in one transaction. No
retail game state is imported or modified by this store.
"""
from contextlib import contextmanager, closing
from dataclasses import asdict
import json
import hashlib
import os
import math
from pathlib import Path
import sqlite3
import uuid
from franchise.cap import Ledger, Offer, Rejected, json_amount, money
from franchise.rookie import RookieScale, UndraftedScale
from franchise.books import OpeningBooks, parse_amount
from franchise.cash import CashBook, CashObligation


class GenerationPreflightError(ValueError):
    """Replay failed after preserving a consistent private source backup."""
    def __init__(self, backup_path, backup_sha256):
        self.backup_path = str(backup_path)
        self.backup_sha256 = backup_sha256
        super().__init__('Generation preflight validation failed; preserved backup: ' + str(backup_path))


def from_config(config: dict) -> Ledger:
    config = dict(config)
    if config.get("management_profile") is not None:
        from franchise.management import ManagementProfile
        config["management_profile"] = ManagementProfile.from_dict(config["management_profile"])
    if config.get("rookie_pool_opening") is not None:
        from franchise.rookie_opening import RookiePoolOpening
        config["rookie_pool_opening"] = RookiePoolOpening.from_dict(config["rookie_pool_opening"])
    if config.get("veteran_minimum_profile") is not None:
        from franchise.salary_rules import VeteranMinimumProfile
        config["veteran_minimum_profile"] = VeteranMinimumProfile.from_dict(config["veteran_minimum_profile"])
    if config.get("opening_books") is None:
        raise ValueError("Source opening books are missing; explicit migration required")
    config["existing_charges"] = tuple(parse_amount(value) for value in config["existing_charges"])
    if config.get("opening_books") is not None:
        config["opening_books"] = OpeningBooks.from_dict(config["opening_books"])
    config["signed_player_ids"] = frozenset(config["signed_player_ids"])
    if 'observed_player_ids' in config:
        if type(config['observed_player_ids']) is not list or len(config['observed_player_ids']) != len(set(config['observed_player_ids'])):
            raise ValueError('Unique observed registry identities required')
        config['observed_player_ids'] = frozenset(config['observed_player_ids'])
    config["veteran_minimums"] = {key: tuple(value) for key, value
                                   in config["veteran_minimums"].items()}
    config["rookies"] = {key: (RookieScale if "draft_round" in value else UndraftedScale)(**{**value,
                              "minimum_salaries": tuple(value["minimum_salaries"])})
                         for key, value in config["rookies"].items()}
    return Ledger(**config)


class FranchiseStore:
    YEAR_TRANSITION_EXCLUSIONS = frozenset({'unsettled_incentives','unresolved_cap_adjustments','carryover','other_calendar_liabilities'})

    @staticmethod
    def _calendar_posting(ledger):
        records = []
        for agreement in ledger.generation_agreements():
            view = ledger.generation_calendar_view(agreement.identity.generation_id)
            records.append({'generation_id':agreement.identity.generation_id,
                'anchor_year':view.anchor_year,'current_year':view.current_year,
                'status':view.status,'expiry_source':view.expiry_source,
                'current_contract':view.current_contract.to_dict() if view.current_contract is not None else None,
                'annual_charges':[json_amount(value) for value in view.annual_charges()],
                'payment_ceilings':view.payment_ceilings()})
        return {'league_year':ledger._league_year,'agreements':records}

    def _year_transition_group(self, db, transition):
        required = {'format','request_id','from_year','to_year','source','teams'}
        if (type(transition) is not dict or set(transition) != required
                or type(transition['format']) is not int or transition['format'] != 1
                or type(transition['from_year']) is not int or type(transition['to_year']) is not int
                or not 2020 <= transition['from_year'] < transition['to_year'] <= 2030
                or transition['to_year'] != transition['from_year'] + 1
                or any(type(transition[key]) is not str or not transition[key].strip() for key in ('request_id','source'))
                or type(transition['teams']) is not dict):
            raise ValueError('Invalid common year transition')
        teams = {row[0] for row in db.execute('SELECT id FROM teams')}
        if set(transition['teams']) != teams or not teams:
            raise ValueError('Year transition requires complete league coverage')
        rows = db.execute("SELECT team_id,payload FROM events WHERE kind='year_transition' AND request_key=?",
                          ('year:'+transition['request_id'],)).fetchall()
        if len(rows) != len(teams) or {row[0] for row in rows} != teams:
            raise ValueError('Partial league year transition')
        for team, serialized in rows:
            payload = json.loads(serialized)
            fields={'transition','before','posting','cash_posting','calendar_posting'}
            history_fields={'generation_format','before_generation_posting','generation_posting'}
            if (type(payload) is not dict or set(payload) not in (fields,fields|history_fields)
                    or (history_fields & set(payload) and (type(payload.get('generation_format')) is not int or payload['generation_format']!=2))
                    or self._checkpoint_hash(payload['transition']) != self._checkpoint_hash(transition)):
                raise ValueError('Common year transition records disagree')

    def _apply_year_input(self, ledger, transition, team):
        from franchise.salary_rules import VeteranMinimumProfile
        item = transition['teams'][team]
        keys = {'expected_revision','next_cap','next_cap_source','roster_reserve','reserve_source',
                'next_minimum_profile','expired_generation_ids','exclusions','source'}
        if (type(item) is not dict or set(item) != keys
                or any(type(item[key]) is not str or not item[key].strip() for key in ('next_cap_source','reserve_source','source'))
                or type(item['exclusions']) is not list or len(item['exclusions']) != len(self.YEAR_TRANSITION_EXCLUSIONS)
                or any(type(value) is not str for value in item['exclusions'])
                or set(item['exclusions']) != self.YEAR_TRANSITION_EXCLUSIONS
                or type(item['expired_generation_ids']) is not list
                or any(type(value) is not str or not value.strip() for value in item['expired_generation_ids'])):
            raise ValueError('Complete sourced closing and next-year inputs required')
        ledger.apply_year_transition(from_year=transition['from_year'],to_year=transition['to_year'],
            expected_revision=item['expected_revision'],next_cap=item['next_cap'],roster_reserve=item['roster_reserve'],
            next_minimum_profile=VeteranMinimumProfile.from_dict(item['next_minimum_profile']),
            source=item['source'],expired_generation_ids=tuple(item['expired_generation_ids']))

    def advance_league_year(self, *, request_id, from_year, to_year, source, teams):
        """Atomic supported transition; no guest write or inferred future rules."""
        if (type(request_id) is not str or not request_id.strip()
                or type(source) is not str or not source.strip()
                or type(from_year) is not int or type(to_year) is not int
                or not 2020 <= from_year < to_year <= 2030 or to_year != from_year + 1
                or type(teams) is not dict):
            raise ValueError('Explicit adjacent sourced league years and team inputs required')
        transition = json.loads(json.dumps({'format':1,'request_id':request_id,'from_year':from_year,
            'to_year':to_year,'source':source,'teams':teams},allow_nan=False))
        with self._connection(write=True) as db:
            if db.execute('PRAGMA user_version').fetchone()[0] != 4:
                raise Rejected('Year transition requires explicit generation migration')
            known = {row[0] for row in db.execute('SELECT id FROM teams')}
            if not known or set(teams) != known or self._calendar_anchor(db) is None:
                raise Rejected('Anchored complete league required for year transition')
            # Cohort/rights advancement is still unsupported; never drop history.
            if db.execute('SELECT 1 FROM draft_orders LIMIT 1').fetchone():
                raise Rejected('Draft cohort calendar transition is not implemented')
            existing = db.execute("SELECT payload FROM events WHERE kind='year_transition' AND request_key=? LIMIT 1",
                                  ('year:'+request_id,)).fetchone()
            if existing is not None:
                previous = json.loads(existing[0])['transition']
                if self._checkpoint_hash(previous) != self._checkpoint_hash(transition):
                    raise Rejected('Year transition retry changed its terms')
                self._year_transition_group(db, previous)
                self._load_teams(db,tuple(sorted(known)))
                return previous
            ledgers = self._load_teams(db,tuple(sorted(known)))
            postings = {}
            for team, ledger in sorted(ledgers.items()):
                before = {'financial':ledger.financial_snapshot(),'cash':ledger.cash_snapshot(),
                          'calendar':self._calendar_posting(ledger)}
                history_before=ledger.generation_snapshot(history_format=2) if self._has_amendment_history(ledger) else None
                self._apply_year_input(ledger,transition,team)
                postings[team] = {'transition':transition,'before':before,
                    'posting':ledger.financial_snapshot(),'cash_posting':ledger.cash_snapshot(),
                    'calendar_posting':self._calendar_posting(ledger)}
                if history_before is not None:
                    postings[team].update(generation_format=2,before_generation_posting=history_before,
                        generation_posting=ledger.generation_snapshot(history_format=2))
            for team, payload in postings.items():
                db.execute("INSERT INTO events(team_id,request_key,kind,payload) VALUES(?,?,'year_transition',?)",
                           (team,'year:'+request_id,json.dumps(payload,allow_nan=False)))
                db.execute('DELETE FROM ownership WHERE team_id=?',(team,))
                for player in ledgers[team]._players:
                    db.execute('INSERT INTO ownership VALUES(?,?)',(player,team))
            return transition
    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path == ":memory:":
            raise ValueError("Durable franchise state requires a database file")
        with self._connection(write=True, guest_recovery=True) as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 3, 4):
                raise ValueError("Unsupported franchise database version")
            db.execute("CREATE TABLE IF NOT EXISTS teams (id TEXT PRIMARY KEY, config TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS ownership (player_id TEXT PRIMARY KEY, team_id TEXT NOT NULL REFERENCES teams(id))")
            db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, team_id TEXT NOT NULL REFERENCES teams(id), request_key TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, UNIQUE(team_id, request_key))")
            db.execute("CREATE TABLE IF NOT EXISTS draft_orders (id TEXT PRIMARY KEY, league_year INTEGER UNIQUE NOT NULL, config TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS draft_picks (draft_id TEXT NOT NULL REFERENCES draft_orders(id), overall_pick INTEGER NOT NULL, player_id TEXT UNIQUE NOT NULL, team_id TEXT NOT NULL REFERENCES teams(id), PRIMARY KEY(draft_id,overall_pick))")
            db.execute("CREATE TABLE IF NOT EXISTS franchise_metadata (key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS guest_signings (request_id TEXT PRIMARY KEY, team_id TEXT NOT NULL REFERENCES teams(id), state TEXT NOT NULL CHECK(state IN ('prepared','settled','cancelled')), intent TEXT NOT NULL, before_payload BLOB NOT NULL, after_payload BLOB, confirmation TEXT)")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_pending_guest_signing ON guest_signings((1)) WHERE state='prepared'")
            if version == 0:
                db.execute("PRAGMA user_version=3")

    @classmethod
    @contextmanager
    def _generation_reservation(cls, path):
        """Back up and verify format 3 without migrating or rewriting its data."""
        path = Path(path).absolute()
        if not path.is_file():
            raise ValueError('Generation preflight requires an existing database')
        instance = cls.__new__(cls)
        instance.path = str(path)
        backup = path.with_name(path.stem + '.generation-backup-' + uuid.uuid4().hex + '.sqlite')
        with instance._connection(write=True, existing=True) as db:
            if db.execute('PRAGMA user_version').fetchone()[0] != 3:
                raise ValueError('Generation preflight supports only database format 3')
            created = False
            try:
                with backup.open('xb'):
                    created = True
                    os.chmod(backup, 0o600)
                with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as source, \
                        closing(sqlite3.connect(backup.as_uri() + '?mode=rw', uri=True)) as target:
                    source.backup(target)
            except BaseException:
                if created:
                    backup.unlink(missing_ok=True)
                raise
            digest = hashlib.sha256()
            with backup.open('rb') as incoming:
                while chunk := incoming.read(1024 * 1024):
                    digest.update(chunk)
            checksum = digest.hexdigest()
            try:
                if db.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
                    raise ValueError('Database integrity check failed')
                if db.execute('PRAGMA foreign_key_check').fetchall():
                    raise ValueError('Database foreign-key integrity check failed')
                instance._franchise_origin(db)  # Metadata is authoritative even with no teams.
                from franchise.draft_order import DraftOrder
                for draft_id, league_year, config in db.execute('SELECT id,league_year,config FROM draft_orders'):
                    order = DraftOrder.from_dict(json.loads(config))
                    if (type(draft_id) is not str or type(league_year) is not int
                            or order.draft_id != draft_id or order.league_year != league_year):
                        raise ValueError('Draft order identity disagrees with source columns')
                team_ids = tuple(team for (team,) in db.execute('SELECT id FROM teams ORDER BY id'))
                ledgers = instance._load_teams(db, team_ids)
                teams = {team:{'financial':ledger.financial_snapshot(), 'cash':ledger.cash_snapshot(),
                    'contracts':instance._contract_generations_from_ledger(team,ledger)} for team,ledger in ledgers.items()}
            except Exception as exc:
                raise GenerationPreflightError(backup, checksum) from exc
            report = {'format':1, 'status':'preflight_only', 'source_database_version':3,
                    'backup_path':str(backup), 'backup_sha256':checksum, 'teams':teams}
            try:
                yield instance, db, report, ledgers
            except Exception as exc:
                raise GenerationPreflightError(backup, checksum) from exc

    @classmethod
    def prepare_generation_migration(cls, path):
        with cls._generation_reservation(path) as (_, _, report, _):
            return report

    @staticmethod
    def _checkpoint_team(ledger):
        return {'financial':ledger.financial_snapshot(), 'cash':ledger.cash_snapshot(),
            'agreements':[{'identity':asdict(a.identity), 'status':a.status,
                'original_contract':a.original_contract.to_dict(), 'contract':a.contract.to_dict(),
                'retained_records':[{'record_id':r.record_id, 'source':r.source,
                    'annual_charges':[json_amount(v) for v in r.annual_charges]} for r in a.retained_records]}
                for a in ledger.generation_agreements()]}

    @staticmethod
    def _checkpoint_source(db, anchor, keys=None):
        tables={'teams':('id','SELECT id,config FROM teams ORDER BY id'),
            'franchise_metadata':('key','SELECT key,value FROM franchise_metadata ORDER BY key'),
            'draft_orders':('id','SELECT id,league_year,config FROM draft_orders ORDER BY id')}
        data={}
        for table,(_,query) in tables.items():
            rows=db.execute(query).fetchall()
            data[table]=[list(row) for row in rows if keys is None or row[0] in keys[table]]
        data['events']=[list(row) for row in db.execute(
            'SELECT id,team_id,request_key,kind,payload FROM events WHERE id<=? ORDER BY id',(anchor,))]
        return data

    @staticmethod
    def _checkpoint_hash(value):
        return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
            separators=(',',':')).encode('utf-8')).hexdigest()

    @classmethod
    def migrate_generations(cls,path):
        with cls._generation_reservation(path) as (instance,db,report,ledgers):
            anchor=db.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0]
            source=instance._checkpoint_source(db,anchor)
            manifest={'format':1,'anchor_event_id':anchor,
                'source_keys':{table:[row[0] for row in source[table]] for table in
                    ('teams','franchise_metadata','draft_orders')},
                'source_sha256':instance._checkpoint_hash(source),
                'teams':{team:instance._checkpoint_team(ledger) for team,ledger in ledgers.items()}}
            db.execute('CREATE TABLE generation_checkpoint (id INTEGER PRIMARY KEY CHECK(id=1), manifest TEXT NOT NULL)')
            db.execute('INSERT INTO generation_checkpoint VALUES(1,?)',
                (json.dumps(manifest,ensure_ascii=False,sort_keys=True,separators=(',',':')),))
            db.execute('PRAGMA user_version=4')
            instance._validate_generation_checkpoint(db)
            return {**report,'status':'migrated','database_version':4,'target_database_version':4,'anchor_event_id':anchor}

    def _validate_generation_checkpoint(self,db):
        if db.execute('PRAGMA user_version').fetchone()[0] != 4:
            return
        rows=db.execute('SELECT id,manifest FROM generation_checkpoint').fetchall()
        if len(rows)!=1 or rows[0][0]!=1:
            raise ValueError('Generation checkpoint singleton required')
        def unique_object(pairs):
            result={}
            for key,value in pairs:
                if key in result:
                    raise ValueError('Duplicate generation checkpoint key')
                result[key]=value
            return result
        manifest=json.loads(rows[0][1],object_pairs_hook=unique_object)
        if (type(manifest) is not dict or set(manifest) !=
                {'format','anchor_event_id','source_keys','source_sha256','teams'}
                or type(manifest['format']) is not int or manifest['format']!=1
                or type(manifest['anchor_event_id']) is not int or manifest['anchor_event_id']<0):
            raise ValueError('Invalid generation checkpoint manifest')
        keys=manifest['source_keys']
        if (type(keys) is not dict or set(keys)!={'teams','franchise_metadata','draft_orders'}
                or any(type(values) is not list or any(type(v) is not str for v in values)
                    or len(values)!=len(set(values)) for values in keys.values())
                or type(manifest['teams']) is not dict or set(manifest['teams'])!=set(keys['teams'])):
            raise ValueError('Invalid generation checkpoint source identities')
        source=self._checkpoint_source(db,manifest['anchor_event_id'],keys)
        if self._checkpoint_hash(source)!=manifest['source_sha256']:
            raise ValueError('Generation checkpoint source history changed')
        for team,expected in manifest['teams'].items():
            ledger=self._load_one(db,team,through_event_id=manifest['anchor_event_id'])
            if self._checkpoint_hash(self._checkpoint_team(ledger))!=self._checkpoint_hash(expected):
                raise ValueError('Generation checkpoint accounting disagrees with replay')

    @classmethod
    def migrate_v2(cls, path: str | Path, books_by_team: dict[str, OpeningBooks]) -> Path:
        """Attach verified source books without changing recorded financial results.

        Requires every team and exact reconciliation. A consistent SQLite backup
        is taken before writes; any failed reconciliation rolls back the migration.
        """
        path = Path(path)
        if not path.is_file():
            raise ValueError("Migration requires an existing database")
        instance = cls.__new__(cls)
        instance.path = str(path)
        backup = path.with_name(path.stem + ".v2-backup-" + uuid.uuid4().hex + ".sqlite")
        with instance._connection(write=True) as db:
            if db.execute("PRAGMA user_version").fetchone()[0] != 2:
                raise ValueError("Only posting-verified format 2 can use this migration")
            teams = {team for (team,) in db.execute("SELECT id FROM teams")}
            if type(books_by_team) is not dict or set(books_by_team) != teams:
                raise ValueError("Migration requires opening books for every team")
            if any(not isinstance(books, OpeningBooks) for books in books_by_team.values()):
                raise ValueError("Typed source books required")
            # This connection holds the write reservation. A separate read
            # connection can back up the unchanged, committed source consistently.
            with closing(sqlite3.connect(path)) as source, closing(sqlite3.connect(backup)) as target:
                source.backup(target)
            db.execute("CREATE TABLE IF NOT EXISTS draft_orders (id TEXT PRIMARY KEY, league_year INTEGER UNIQUE NOT NULL, config TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS draft_picks (draft_id TEXT NOT NULL REFERENCES draft_orders(id), overall_pick INTEGER NOT NULL, player_id TEXT UNIQUE NOT NULL, team_id TEXT NOT NULL REFERENCES teams(id), PRIMARY KEY(draft_id,overall_pick))")
            db.execute("CREATE TABLE IF NOT EXISTS franchise_metadata (key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            for team, books in books_by_team.items():
                config = json.loads(db.execute("SELECT config FROM teams WHERE id=?", (team,)).fetchone()[0])
                config["opening_books"] = books.to_dict()
                db.execute("UPDATE teams SET config=? WHERE id=?", (json.dumps(config), team))
            for team in teams:
                instance._load(db, team)
            db.execute("PRAGMA user_version=3")
        return backup

    @contextmanager
    def _connection(self, *, write=False, existing=False, guest_recovery=False):
        database = Path(self.path).absolute().as_uri() + '?mode=rw' if existing else self.path
        db = sqlite3.connect(database, timeout=10, uri=existing)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            self._validate_generation_checkpoint(db)
            if write and not guest_recovery and db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='guest_signings'").fetchone():
                if db.execute("SELECT 1 FROM guest_signings WHERE state='prepared'").fetchone():
                    raise Rejected('Guest signing awaits confirmation or stopped-game recovery')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def create_team(self, team_id: str, ledger: Ledger):
        with self._connection(write=True) as db:
            self._insert_team(db,team_id,ledger)

    def _insert_team(self,db,team_id,ledger):
        if db.execute("SELECT 1 FROM events WHERE kind='calendar_anchor' LIMIT 1").fetchone():
            raise Rejected('League membership is fixed after calendar anchoring')
        if type(team_id) is not str or not team_id.strip():
            raise ValueError("Stable team ID required")
        config = ledger.bootstrap_config()
        if ledger._rookies.keys() & ledger._players and ledger._rookie_pool_opening is None:
            raise ValueError("Durable starting rookie roster requires explicit cohort/pool source")
        if config["opening_books"] is None:
            raise ValueError("Durable teams require source opening books, not aggregate-only balances")
        if db.execute("SELECT 1 FROM teams WHERE id=?", (team_id,)).fetchone():
            raise Rejected("Team already exists; refusing to overwrite financial state")
        db.execute("INSERT INTO teams VALUES (?, ?)", (team_id, json.dumps(config)))
        for player in config["signed_player_ids"]:
            if db.execute("SELECT 1 FROM ownership WHERE player_id=?", (player,)).fetchone():
                raise Rejected("Player already belongs to another team")
            db.execute("INSERT INTO ownership VALUES (?, ?)", (player, team_id))
        origin = self._franchise_origin(db)
        if origin is not None:
            from franchise.initialization import initial_actor
            registered = ledger.registered_player_ids
            if not ledger._players <= registered:
                raise ValueError('Every roster player requires registered classification')
            for player in sorted(registered):
                actor = initial_actor(origin['seed'],player)
                self._validate_actor(actor)
                payload = {'player_id':player,'actor':actor,'posting':ledger.financial_snapshot()}
                db.execute("INSERT INTO events (team_id,request_key,kind,payload) VALUES (?,?,'actor',?)",
                           (team_id,'actor:'+player,json.dumps(payload,allow_nan=False)))

    @staticmethod
    def _validate_calendar_year(ledger, year):
        if ledger._legacy_contracts:
            raise Rejected('Legacy schedules require verified calendar migration before anchoring')
        years = []
        if ledger._veteran_minimum_profile is not None:
            years.append(ledger._veteran_minimum_profile.start_year)
        if ledger._rookie_pool_opening is not None:
            years.append(ledger._rookie_pool_opening.league_year)
        if ledger._last_transaction_date is not None:
            years.append(ledger._last_transaction_date.year)
        if any(value != year for value in years):
            raise Rejected('Calendar year disagrees with sourced rules or transaction history')

    @classmethod
    def _calendar_anchor(cls, db):
        rows = db.execute("SELECT team_id,request_key,payload FROM events WHERE kind='calendar_anchor'").fetchall()
        if not rows:
            return None
        first = json.loads(rows[0][2])
        if type(first) is not dict:
            raise ValueError('Invalid league calendar record')
        anchor = first.get('anchor')
        if (type(anchor) is not dict or set(anchor) != {'format','request_id','league_year','source','expected_revisions'}
                or type(anchor['format']) is not int or anchor['format'] != 1
                or type(anchor['league_year']) is not int or not 2020 <= anchor['league_year'] <= 2030
                or any(type(anchor[key]) is not str or not anchor[key].strip() for key in ('request_id','source'))
                or type(anchor['expected_revisions']) is not dict
                or any(type(value) is not int or value < 0 for value in anchor['expected_revisions'].values())):
            raise ValueError('Invalid league calendar anchor')
        teams = {row[0] for row in db.execute('SELECT id FROM teams')}
        if (set(anchor['expected_revisions']) != teams or len(rows) != len(teams)
                or {row[0] for row in rows} != teams):
            raise ValueError('Calendar anchor does not cover the complete league')
        for team, key, serialized in rows:
            payload = json.loads(serialized)
            if (key != 'calendar:' + anchor['request_id'] or type(payload) is not dict
                    or set(payload) != {'anchor','posting'}
                    or cls._checkpoint_hash(payload['anchor']) != cls._checkpoint_hash(anchor)):
                raise ValueError('League calendar records disagree')
        return anchor

    def anchor_calendar(self, *, request_id, league_year, source, expected_revisions):
        """Bind the initial sourced year atomically; this does not advance a season."""
        if (type(request_id) is not str or not request_id.strip()
                or type(source) is not str or not source.strip()
                or type(league_year) is not int or not 2020 <= league_year <= 2030
                or type(expected_revisions) is not dict
                or any(type(key) is not str or not key.strip() or type(value) is not int or value < 0
                       for key, value in expected_revisions.items())):
            raise ValueError('Explicit sourced calendar year and team revisions required')
        anchor = {'format':1,'request_id':request_id,'league_year':league_year,
                  'source':source,'expected_revisions':dict(expected_revisions)}
        with self._connection(write=True) as db:
            teams = {row[0] for row in db.execute('SELECT id FROM teams')}
            if not teams or teams != set(expected_revisions):
                raise Rejected('Calendar anchoring requires complete league team coverage')
            previous = self._calendar_anchor(db)
            if previous is not None:
                if self._checkpoint_hash(previous) != self._checkpoint_hash(anchor):
                    raise Rejected('League calendar already anchored with different terms')
                self._load_teams(db, tuple(sorted(teams)))
                return previous
            ledgers = self._load_teams(db, tuple(sorted(teams)))
            for team, ledger in ledgers.items():
                if ledger.revision != expected_revisions[team]:
                    raise Rejected('Calendar anchoring is based on stale team state')
                self._validate_calendar_year(ledger, league_year)
            for team, ledger in sorted(ledgers.items()):
                ledger.revision += 1
                payload = {'anchor':anchor,'posting':ledger.financial_snapshot()}
                db.execute("INSERT INTO events(team_id,request_key,kind,payload) VALUES(?,?,'calendar_anchor',?)",
                           (team,'calendar:'+request_id,json.dumps(payload,allow_nan=False)))
            return anchor

    def league_calendar(self):
        with self._connection() as db:
            anchor = self._calendar_anchor(db)
            if anchor is not None:
                ledgers = self._load_teams(db, tuple(sorted(anchor['expected_revisions'])))
                years = {ledger._league_year for ledger in ledgers.values()}
                if len(years) != 1:
                    raise ValueError('League teams disagree on current calendar')
                current = years.pop()
                if current != anchor['league_year']:
                    return {**anchor,'initial_league_year':anchor['league_year'],'league_year':current}
            return anchor

    def calendar_projection(self, team_id, *, target_year):
        """Project recorded schedules only; no future cap, settlement or ownership grant."""
        from franchise.generations import GenerationCalendarView
        if type(target_year) is not int or not 2020 <= target_year <= 2030:
            raise ValueError('Explicit published-CBA projection year required')
        with self._connection() as db:
            anchor = self._calendar_anchor(db)
            if anchor is None or target_year < anchor['league_year']:
                raise Rejected('Anchored calendar and current/future projection year required')
            ledger = self._load(db, team_id)
            if target_year < ledger._league_year:
                raise Rejected('Projection precedes current league year')
            offset = target_year - ledger._league_year
            return {'team_id':team_id,'financial_revision':ledger.revision,
                    'recorded_league_year':ledger._league_year,'target_year':target_year,
                    'calendar_source':anchor['source'],
                    'modeled_remaining_charges':[json_amount(value) for value in ledger.charges[offset:]],
                    'agreements':[GenerationCalendarView(item,ledger.generation_calendar_view(item.identity.generation_id).anchor_year,
                                                       target_year).to_projection()
                                  for item in ledger.generation_agreements()],
                    **({'current_calendar':self._calendar_posting(ledger)}
                       if ledger._generation_calendar_anchor is not None else {}),
                    'unchanged_cash':ledger.cash_snapshot(),
                    'season_advanced':False,'ownership_changed':False,'future_cap':None}

    def calendar_closing_state(self, team_id):
        """Inspect recorded settlement needs; owner funding is not a paid record."""
        with self._connection() as db:
            anchor = self._calendar_anchor(db)
            if anchor is None:
                raise Rejected('Anchored league calendar required for closing inspection')
            ledger = self._load(db, team_id)
            agreements = []
            for agreement in ledger.generation_agreements():
                cash = ledger.generation_cash(agreement.identity.generation_id)
                allocations = dict(cash.paid_components) if cash is not None and cash.paid_components is not None else None
                view = ledger.generation_calendar_view(agreement.identity.generation_id)
                active = view.status == 'active' and view.current_contract is not None
                index = view.current_contract.elapsed_years if active else None
                required = {'base:'+str(i):amount for i,amount in enumerate(agreement.contract.offer.salaries) if i <= index} if active else None
                settled = None if allocations is None or required is None else all(allocations.get(key,0) == amount for key,amount in required.items())
                term_ends = active and index + 1 == len(agreement.contract.offer.salaries)
                all_paid = None if allocations is None else cash.paid == cash.amount
                agreements.append({'generation_id':agreement.identity.generation_id,
                    'recorded_status':view.status,
                    'outgoing_year_original_index':index if active else None,
                    'required_past_and_outgoing_base':required,
                    'recorded_base_settled':settled,
                    'scheduled_term_ends_after_year':term_ends,
                    'all_nominal_cash_recorded_paid':all_paid,
                    'unpaid_nominal_cash':cash.amount-cash.paid if cash is not None else None,
                    'expiry_authorized':False})
            return {'team_id':team_id,'financial_revision':ledger.revision,
                    'league_year':ledger._league_year,'agreements':agreements,
                    'normal_payroll_owner_funded':True,'revenue_gate':False,
                    'season_advanced':False,'scope':'recorded settlement inspection; actual closing facts and transition required'}

    @staticmethod
    def _franchise_origin(db):
        from franchise.initialization import VERSION,validate_seed
        row = db.execute("SELECT value FROM franchise_metadata WHERE key='personality-origin'").fetchone()
        if row is None:
            return None
        origin = json.loads(row[0])
        if type(origin) is not dict or set(origin) != {'version','seed','source'} or origin['version'] != VERSION or origin['source'] != 'authored fictional franchise initialization':
            raise ValueError('Unsupported franchise personality origin')
        validate_seed(origin['seed'])
        return origin

    def create_franchise(self,teams,*,seed=None):
        """Atomic league bootstrap with personalities for every registered player."""
        from franchise.initialization import VERSION,initial_actor,validate_seed
        import secrets
        if type(teams) is not dict or not teams or any(type(team) is not str or not team.strip() for team in teams) or any(not isinstance(ledger,Ledger) for ledger in teams.values()):
            raise ValueError('Source-backed team ledgers required')
        seed = secrets.token_hex(32) if seed is None else seed
        validate_seed(seed)
        origin = {'version':VERSION,'seed':seed,'source':'authored fictional franchise initialization'}
        with self._connection(write=True) as db:
            if db.execute('SELECT 1 FROM teams LIMIT 1').fetchone() or self._franchise_origin(db) is not None:
                raise Rejected('Franchise already initialized; refusing to reroll players')
            db.execute("INSERT INTO franchise_metadata VALUES ('personality-origin',?)", (json.dumps(origin),))
            for team,ledger in sorted(teams.items()):
                self._insert_team(db,team,ledger)
        return origin

    def _load(self,db,team_id):
        return self._load_teams(db,(team_id,))[team_id]

    def _load_teams(self,db,team_ids):
        # One read transaction may replay the same generated player for many
        # clubs. Expected origins are immutable comparisons, never live actors.
        actor_origins={}
        ledgers={team:self._load_one(db,team,actor_origins=actor_origins) for team in team_ids}
        # One fresh read transaction validates the league, without persistent cache.
        if db.execute("SELECT 1 FROM events WHERE kind IN ('year_transition','calendar_anchor','trade_out','trade_in','generation_trade_out','generation_trade_in') LIMIT 1").fetchone():
            for (other,) in db.execute('SELECT id FROM teams').fetchall():
                if other not in ledgers:
                    self._load_one(db,other,actor_origins=actor_origins)
        return ledgers

    def _load_one(self, db, team_id, *, through_event_id=None, actor_origins=None) -> Ledger:
        row = db.execute("SELECT config FROM teams WHERE id=?", (team_id,)).fetchone()
        if row is None:
            raise Rejected("Unknown team")
        ledger = from_config(json.loads(row[0]))
        ledger.bind_team_identity(team_id)
        ledger._actors = {}
        ledger._scouting = []
        origin = self._franchise_origin(db)
        relationship_sources = set()
        payment_references = set()
        efficiency_cache = {}  # Keep only the last derivation within this chronological read.
        actor_origins={} if actor_origins is None else actor_origins
        actor_posting=actor_registered=None
        for event_id, kind, serialized in db.execute("SELECT id, kind, payload FROM events WHERE team_id=? AND (? IS NULL OR id<=?) ORDER BY id", (team_id,through_event_id,through_event_id)):
            payload = json.loads(serialized)
            if kind != 'actor':
                actor_posting=actor_registered=None
            if kind == "sign":
                if 'proposal_request_id' in payload:
                    expected=self._settlement_story(db,team_id,payload['proposal_request_id'],payload['request_id'],before_event_id=event_id)
                    if (self._checkpoint_hash(expected)!=self._checkpoint_hash(payload['story'])
                            or payload['expected_revision']!=expected['evidence']['financial_revision']
                            or self._checkpoint_hash(payload['offer'])!=self._checkpoint_hash(expected['offer'])
                            or self._checkpoint_hash(ledger.preview_offer(Offer.from_dict(payload['offer']),payload['expected_revision']))
                               !=self._checkpoint_hash(expected['proposal_preview'])):
                        raise ValueError('Settled signing differs from its accepted proposal')
                elif payload['story'] is not None and ('proposal_request_id' in payload['story'] or payload['story'].get('decision_mode')=='proposal_settlement'):
                    raise ValueError('Settlement story has no source proposal')
                self._validate_story_evidence(payload["story"], efficiency_cache=efficiency_cache)
                data = payload["offer"]
                receipt = ledger.sign(payload["request_id"], Offer.from_dict(data), payload["expected_revision"])
                self._remember_promises(ledger,payload)
                if ledger._cash is not None:
                    ledger._cash.add_contract(receipt.offer, "sign:" + payload["request_id"], track_components=payload.get("cash_components", False),
                        obligation_id=ledger.contract_cash_id(receipt.offer.player_id))
                    if payload.get("cash_posting") != ledger.cash_snapshot():
                        raise ValueError("Recorded signing cash disagrees with replay")
                if payload.get("contract_charges") != [json_amount(value) for value in receipt.charges]:
                    raise ValueError("Recorded contract charges disagree with replay")
            elif kind == 'return_sign':
                if (db.execute('PRAGMA user_version').fetchone()[0]!=4 or
                        set(payload) not in ({'format','request_id','offer','scope','expected_revision','generation_id',
                            'posting','cash_posting','contract_charges','generation_posting'},
                            {'format','request_id','offer','scope','expected_revision','generation_id',
                            'posting','cash_posting','contract_charges','generation_posting','story'}) or
                        type(payload['format']) is not int or payload['format']!=1):
                    raise ValueError('Versioned return signing required')
                if 'story' in payload:
                    self._validate_story_evidence(payload['story'],efficiency_cache=efficiency_cache)
                    if (payload['story'].get('return_scope')!=payload['scope']
                            or payload['story'].get('request_id')!=payload['request_id']
                            or payload['story'].get('offer')!=payload['offer']
                            or payload['story'].get('action')!='accept' or payload['story'].get('outcome')!='signed'):
                        raise ValueError('Return story disagrees with sourced agreement')
                receipt=ledger.return_sign(payload['request_id'],Offer.from_dict(payload['offer']),
                    payload['expected_revision'],scope=self._return_scope(payload['scope']))
                if 'story' in payload:
                    self._remember_promises(ledger,payload)
                if (ledger.contract_identity(receipt.offer.player_id).generation_id!=payload['generation_id'] or
                        self._checkpoint_hash(payload['cash_posting'])!=self._checkpoint_hash(ledger.cash_snapshot()) or
                        self._checkpoint_hash(payload['contract_charges'])!=self._checkpoint_hash([json_amount(v) for v in receipt.charges])):
                    raise ValueError('Return signing identity or obligations disagree with replay')
            elif kind == "cash_open":
                if ledger._cash is not None:
                    raise ValueError("Duplicate opening cash state")
                records = tuple(CashObligation.from_dict(record) for record in payload["records"])
                raw_unknown=payload.get('unknown_legacy_players',[])
                if type(raw_unknown) is not list:
                    raise ValueError('Recorded unknown legacy cash inventory must be a list')
                book=CashBook(records, payload["source"],unknown_legacy_players=tuple(raw_unknown))
                if list(book.unknown_legacy_players)!=raw_unknown:
                    raise ValueError('Noncanonical recorded legacy cash inventory')
                self._check_opening_cash(ledger, records,book.unknown_legacy_players)
                ledger._cash=book
                self._check_cash_components(ledger)
                ledger.revision += 1
                if payload["cash_posting"] != ledger.cash_snapshot():
                    raise ValueError("Opening cash posting disagrees with records")
            elif kind == "cash_payment":
                if type(payload.get("source")) is not str or not payload["source"].strip():
                    raise ValueError("Recorded payment source is missing")
                if "payment_reference" in payload:
                    reference = payload["payment_reference"]
                    if type(reference) is not str or not reference.strip():
                        raise ValueError("Recorded payment reference is invalid")
                    identity = (payload["source"], reference)
                    if identity in payment_references:
                        raise ValueError("Duplicate recorded payment evidence")
                    payment_references.add(identity)
                if ledger._cash is None:
                    raise ValueError("Payment has no opening cash state")
                ledger._cash.pay(payload["obligation_id"], payload["amount"], payload["expected_cash_revision"], component=payload.get("component"))
                self._check_cash_components(ledger)
                ledger.revision += 1
                if payload["cash_posting"] != ledger.cash_snapshot():
                    raise ValueError("Cash payment posting disagrees with replay")
            elif kind in ('restructure','generation_restructure','calendar_restructure','calendar_layered_restructure'):
                layered=kind=='calendar_layered_restructure'
                history_format=2 if layered else 1
                extra=set()
                if kind in ('generation_restructure','calendar_restructure','calendar_layered_restructure'):
                    extra={'format','generation_id','before_generation_posting','generation_posting'}
                    if (db.execute('PRAGMA user_version').fetchone()[0]!=4
                            or type(payload.get('format')) is not int or payload['format']!=history_format
                            or payload.get('generation_id')!=ledger.contract_identity(payload['player_id']).generation_id
                            or self._checkpoint_hash(payload.get('before_generation_posting'))!=self._checkpoint_hash(ledger.generation_snapshot(history_format=history_format))):
                        raise ValueError('Generation restructure opening state disagrees with replay')
                    if kind in ('calendar_restructure','calendar_layered_restructure'):
                        extra.update({'calendar_format','before_calendar_posting','calendar_posting'})
                        if (type(payload.get('calendar_format')) is not int or payload['calendar_format']!=1
                                or ledger._generation_calendar_anchor is None
                                or self._checkpoint_hash(payload.get('before_calendar_posting'))!=self._checkpoint_hash(self._calendar_posting(ledger))):
                            raise ValueError('Calendar restructure opening state disagrees with replay')
                elif ledger.contract_identity(payload['player_id']).generation_id.startswith('contract-gen:'):
                    raise ValueError('Return agreement restructure requires versioned generation event')
                if set(payload) != extra | {'player_id','scope','converted_base','record_id','expected_revision',
                    'before_posting','before_cash','original_contract','original_cash','posting','cash_posting'}:
                    raise ValueError('Unexpected restructure event fields')
                if (self._checkpoint_hash(payload['original_contract']) != self._checkpoint_hash(ledger.active_contract(payload['player_id']).to_dict())
                        or ledger._cash is None or self._checkpoint_hash(payload['original_cash']) != self._checkpoint_hash(ledger._cash.records[ledger.contract_cash_id(payload['player_id'])].to_dict())):
                    raise ValueError('Restructure original obligations disagree with replay')
                if self._checkpoint_hash(payload['before_posting']) != self._checkpoint_hash(ledger.financial_snapshot()) or self._checkpoint_hash(payload['before_cash']) != self._checkpoint_hash(ledger.cash_snapshot()):
                    raise ValueError('Restructure opening state disagrees with replay')
                self._apply_restructure_payload(ledger,payload,calendar_restructure=kind in ('calendar_restructure','calendar_layered_restructure'),layered=layered)
                self._check_cash_components(ledger)
                if kind in ('generation_restructure','calendar_restructure','calendar_layered_restructure') and self._checkpoint_hash(payload['posting']) != self._checkpoint_hash(ledger.financial_snapshot()):
                    raise ValueError('Generation restructure financial posting disagrees with replay')
                if self._checkpoint_hash(payload['cash_posting']) != self._checkpoint_hash(ledger.cash_snapshot()):
                    raise ValueError('Restructure cash posting disagrees with replay')
            elif kind in ('release','generation_release','calendar_release','calendar_layered_release'):
                layered=kind=='calendar_layered_release'
                history_format=2 if layered else 1
                if layered and not ledger.generation_accounting(payload['generation_id']).prior_restructures:
                    raise ValueError('Layered release requires sourced prior amendment history')
                if kind in ('calendar_release','calendar_layered_release'):
                    fields={'player_id','scope','discount','payment_year_offsets','record_id','expected_revision',
                        'generation_id','format','calendar_format','before_posting','before_cash',
                        'before_generation_posting','before_calendar_posting','posting','cash_posting',
                        'generation_posting','calendar_posting'}
                    if (set(payload)!=fields or type(payload['calendar_format']) is not int
                            or payload['calendar_format']!=1 or ledger._generation_calendar_anchor is None
                            or self._checkpoint_hash(payload['before_calendar_posting'])!=self._checkpoint_hash(self._calendar_posting(ledger))):
                        raise ValueError('Calendar release opening state disagrees with replay')
                if kind=='release' and ledger.contract_identity(payload['player_id']).generation_id.startswith('contract-gen:'):
                    raise ValueError('Return agreement release requires versioned generation event')
                if kind in ('generation_release','calendar_release','calendar_layered_release'):
                    if (type(payload.get('format')) is not int or payload['format']!=history_format or
                            payload.get('generation_id')!=ledger.contract_identity(payload['player_id']).generation_id or
                            self._checkpoint_hash(payload.get('before_generation_posting'))!=self._checkpoint_hash(ledger.generation_snapshot(history_format=history_format))):
                        raise ValueError('Generation release opening state disagrees with replay')
                if (self._checkpoint_hash(payload['before_posting']) != self._checkpoint_hash(ledger.financial_snapshot())
                        or self._checkpoint_hash(payload['before_cash']) != self._checkpoint_hash(ledger.cash_snapshot())):
                    raise ValueError('Release opening state disagrees with replay')
                self._apply_release_payload(ledger,payload,calendar_release=kind in ('calendar_release','calendar_layered_release'))
                self._check_cash_components(ledger)
                if payload['cash_posting'] != ledger.cash_snapshot():
                    raise ValueError('Release cash posting disagrees with replay')
            elif kind in ('trade_out','trade_in','generation_trade_out','generation_trade_in','calendar_trade_out','calendar_trade_in','calendar_layered_trade_out','calendar_layered_trade_in'):
                self._replay_trade(db,ledger,team_id,kind,payload)
            elif kind == "actor":
                # Actor registration changes neither classification nor finances.
                # Compare every recorded posting, but calculate that unchanged
                # value only once per contiguous actor block.
                if actor_posting is None:
                    actor_registered=ledger.registered_player_ids
                    actor_posting=ledger.financial_snapshot()
                if payload["player_id"] not in actor_registered:
                    raise Rejected("Player is unknown or contract classification is missing")
                self._validate_actor(payload["actor"])
                from franchise.initialization import VERSION,initial_actor
                personality = payload["actor"]["personality"]
                if origin is not None:
                    key=(origin['seed'],payload['player_id'])
                    if key not in actor_origins:
                        actor_origins[key]=initial_actor(*key)
                    if payload['actor'] != actor_origins[key]:
                        raise ValueError('Player personality/initial relationships disagree with franchise origin')
                elif personality.get('generation_version') == VERSION:
                    raise ValueError('Generated player personality has no franchise origin')
                if payload["player_id"] in ledger._actors:
                    raise ValueError("Duplicate actor registration")
                ledger._actors[payload["player_id"]] = payload["actor"]
            elif kind == "relationship":
                identity = (payload["player_id"], payload["relationship"], payload["source_request_id"])
                if identity in relationship_sources:
                    raise ValueError("Relationship consequence already applied")
                relationship_sources.add(identity)
                self._relationship_source(db, team_id, payload["player_id"], payload["source_request_id"], before_revision=ledger.revision, before_event_id=event_id)
                actor = ledger._actors.get(payload["player_id"])
                self._apply_relationship(actor, payload["relationship"], payload["delta"])
                if actor != payload["actor_after"]:
                    raise ValueError("Relationship posting disagrees with replay")
                ledger.revision += 1
            elif kind == "promise_score":
                result = self._compute_promise_score(ledger,payload)
                if (self._checkpoint_hash(result)!=self._checkpoint_hash(payload['result']) if 'format' in payload else result!=payload['result']):
                    raise ValueError('Promise score disagrees with recorded observations')
                ledger._promise_scores.append(result)
                ledger.revision += 1
            elif kind == "draft_pick":
                order = self._draft_order(db, payload["draft_id"])
                slot = order.slots[payload["overall_pick"] - 1]
                if (slot.team_id != team_id or slot.draft_round != payload["draft_round"]
                        or payload["order_source"] != order.source or payload["player_id"] not in order.player_ids):
                    raise ValueError("Recorded pick disagrees with source order")
                offer = Offer.from_dict(payload["offer"])
                if offer.player_id != payload["player_id"]:
                    raise ValueError("Pick and funding estimate identities disagree")
                self._validate_pick_decision(ledger,payload)
                self._validate_pick_personalities(db,ledger,payload,before_event=event_id)
                self._draft_fund_pick(ledger, offer, payload["expected_revision"], payload["funding_source"])
                ledger._draft_rights[offer.player_id] = {"draft_id": order.draft_id, "league_year": order.league_year,
                    "overall_pick": slot.overall_pick, "draft_round": slot.draft_round}
            elif kind == "draft_reserve":
                ledger.reserve_draft_funding(Offer.from_dict(payload["offer"]), payload["expected_revision"], source=payload["source"])
            elif kind == "draft_withdraw":
                ledger.withdraw_draft_funding(payload["player_id"], payload["expected_revision"], source=payload["source"])
            elif kind == "draft_scouting":
                from franchise.draft import validate_scouting
                validate_scouting(payload["event"], ledger)
                for prospect in payload['event']['evidence']['prospects']:
                    self._validate_prior_personality(db,prospect['player_id'],prospect['personality'],before_event=event_id)
                ledger._scouting.append(payload["event"])
            elif kind == "dialogue":
                self._validate_dialogue(payload["event"], efficiency_cache=efficiency_cache)
                if payload['event']['outcome'] == 'accepted_proposal':
                    event = payload['event']
                    preview = ledger.preview_offer(Offer.from_dict(event['offer']), event['evidence']['financial_revision'])
                    if self._checkpoint_hash(preview) != self._checkpoint_hash(event['proposal_preview']):
                        raise ValueError('Accepted proposal preview disagrees with financial replay')
            elif kind == "budget":
                ledger.update_budget(**{key: payload[key] for key in ("cap", "roster_reserve", "expected_revision")})
            elif kind == 'calendar_anchor':
                anchor = self._calendar_anchor(db)
                if (type(payload) is not dict or set(payload) != {'anchor','posting'}
                        or self._checkpoint_hash(payload['anchor']) != self._checkpoint_hash(anchor)
                        or anchor['expected_revisions'][team_id] != ledger.revision):
                    raise ValueError('Calendar anchor disagrees with league replay')
                self._validate_calendar_year(ledger, anchor['league_year'])
                ledger._league_year = anchor['league_year']
                ledger.revision += 1
                if self._checkpoint_hash(payload['posting']) != self._checkpoint_hash(ledger.financial_snapshot()):
                    raise ValueError('Calendar financial posting types disagree with replay')
            elif kind == 'year_transition':
                if db.execute('PRAGMA user_version').fetchone()[0] != 4:
                    raise ValueError('Year transition requires versioned generation replay')
                self._year_transition_group(db,payload['transition'])
                history=self._has_amendment_history(ledger)
                if history:
                    if (type(payload.get('generation_format')) is not int or payload['generation_format']!=2
                            or self._checkpoint_hash(payload.get('before_generation_posting'))!=self._checkpoint_hash(ledger.generation_snapshot(history_format=2))):
                        raise ValueError('Closing-year amendment history disagrees with replay')
                elif 'generation_format' in payload:
                    raise ValueError('History-aware closing requires sourced amendment history')
                before = {'financial':ledger.financial_snapshot(),'cash':ledger.cash_snapshot(),
                          'calendar':self._calendar_posting(ledger)}
                if self._checkpoint_hash(payload['before']) != self._checkpoint_hash(before):
                    raise ValueError('Closing-year state disagrees with replay')
                self._apply_year_input(ledger,payload['transition'],team_id)
                if history and self._checkpoint_hash(payload.get('generation_posting'))!=self._checkpoint_hash(ledger.generation_snapshot(history_format=2)):
                    raise ValueError('Next-year amendment history disagrees with replay')
                for key, actual in (('posting',ledger.financial_snapshot()),
                                    ('cash_posting',ledger.cash_snapshot()),
                                    ('calendar_posting',self._calendar_posting(ledger))):
                    if self._checkpoint_hash(payload[key]) != self._checkpoint_hash(actual):
                        raise ValueError('Year-transition posting disagrees with replay')
            else:
                raise ValueError("Unknown financial event; refusing to reconstruct state")
            history_payment=kind=='cash_payment' and self._has_amendment_history(ledger)
            if history_payment:
                required={'obligation_id','amount','source','payment_reference','expected_cash_revision','component',
                    'posting','cash_posting','format','generation_posting','calendar_format','calendar_posting'}
                if set(payload)!=required:
                    raise ValueError('Complete history-aware payment event required')
            if kind in ('return_sign','generation_release','generation_restructure','calendar_release','calendar_layered_release','calendar_restructure','calendar_layered_restructure') or (kind=='cash_payment' and (self._has_new_generations(ledger) or history_payment)):
                generation_format=2 if history_payment or kind in ('calendar_layered_restructure','calendar_layered_release') else 1
                if ('generation_posting' not in payload or type(payload.get('format')) is not int or payload['format']!=generation_format or
                        db.execute('PRAGMA user_version').fetchone()[0]!=4 or
                        self._checkpoint_hash(payload['generation_posting'])!=self._checkpoint_hash(ledger.generation_snapshot(history_format=generation_format))):
                    raise ValueError('Versioned generation posting disagrees with replay')
                if (self._checkpoint_hash(payload.get('posting'))!=self._checkpoint_hash(ledger.financial_snapshot()) or
                        self._checkpoint_hash(payload.get('cash_posting'))!=self._checkpoint_hash(ledger.cash_snapshot())):
                    raise ValueError('Versioned financial or cash posting types disagree with replay')
            if kind=='cash_payment' and not history_payment and payload.get('format')==2:
                raise ValueError('History payment requires sourced prior amendment history')
            calendar_fields = {'calendar_format','calendar_posting'}
            if ledger._generation_calendar_anchor is not None and kind in ('sign','cash_payment','calendar_release','calendar_layered_release','calendar_restructure','calendar_layered_restructure'):
                marked = bool(calendar_fields & set(payload))
                if ((kind in ('sign','calendar_release','calendar_layered_release','calendar_restructure','calendar_layered_restructure') or marked) and
                        (not calendar_fields <= set(payload) or type(payload['calendar_format']) is not int
                         or payload['calendar_format'] != 1
                         or self._checkpoint_hash(payload['calendar_posting']) != self._checkpoint_hash(self._calendar_posting(ledger)))):
                    raise ValueError('Calendar-aware transaction posting disagrees with replay')
                # Earlier supported cash-payment events did not carry calendar
                # views; payments cannot age agreements, but their amounts/types
                # still must match exact replay.
                if (self._checkpoint_hash(payload['posting']) != self._checkpoint_hash(ledger.financial_snapshot())
                        or self._checkpoint_hash(payload.get('cash_posting')) != self._checkpoint_hash(ledger.cash_snapshot())):
                    raise ValueError('Calendar-aware transaction posting disagrees with replay')
            elif 'calendar_format' in payload or ('calendar_posting' in payload and kind != 'year_transition'):
                raise ValueError('Unexpected calendar transaction posting')
            posting=actor_posting if kind=='actor' else ledger.financial_snapshot()
            if payload.get("posting") != posting:
                raise ValueError("Recorded financial posting disagrees with replay")
        if origin is not None and set(ledger._actors) != ledger.registered_player_ids:
            raise ValueError('Initialized player personality coverage is incomplete')
        if through_event_id is not None:
            return ledger
        owned = {player for (player,) in db.execute("SELECT player_id FROM ownership WHERE team_id=?", (team_id,))}
        if owned != set(ledger.financial_snapshot()["signed_players"]):
            raise ValueError("Ownership records disagree with contract history")
        rights = {player: {"draft_id": draft, "league_year": self._draft_order(db, draft).league_year,
                            "overall_pick": pick, "draft_round": self._draft_order(db, draft).slots[pick-1].draft_round}
                  for draft, pick, player in db.execute("SELECT draft_id,overall_pick,player_id FROM draft_picks WHERE team_id=?", (team_id,))}
        if rights != ledger._draft_rights:
            raise ValueError("Draft rights disagree with recorded pick history")
        return ledger

    def registered_players(self,team_id):
        """Declared identities, not a claim of current guest roster membership."""
        with self._connection() as db:
            ledger=self._load(db,team_id)
            players=[]
            for player in sorted(ledger.registered_player_ids):
                context=ledger.negotiation_context(player)
                players.append({'player_id':player,'contract_classification':('pending' if context.get('classification_pending') else 'legacy' if player in ledger._legacy_contracts else context['rookie_type'] or 'veteran'),
                                'initialized':player in ledger._actors})
            return {'team_id':team_id,'financial_revision':ledger.revision,'players':players,
                    'scope':'registered contract identities; guest roster membership unverified'}

    def negotiation_history_page(self,team_id,player_id,*,before_event_id=None,limit=10):
        if type(limit) is not int or not 1 <= limit <= 20:
            raise ValueError('History page limit must be 1 through 20')
        if before_event_id is not None and (type(before_event_id) is not int or not 1 <= before_event_id <= 2**63-1):
            raise ValueError('Positive SQLite event identity required')
        with self._connection() as db:
            ledger=self._load(db,team_id)
            ledger.negotiation_context(player_id)
            rows=db.execute("""SELECT id,kind,payload FROM events WHERE team_id=?
                AND (? IS NULL OR id < ?) AND
                ((kind='dialogue' AND json_extract(payload,'$.event.offer.player_id')=?) OR
                 (kind IN ('sign','return_sign') AND json_extract(payload,'$.story.offer.player_id')=?))
                ORDER BY id DESC LIMIT ?""",(team_id,before_event_id,before_event_id,player_id,player_id,limit+1)).fetchall()
            page=rows[:limit]
            events=[]
            for event_id,kind,serialized in reversed(page):
                payload=json.loads(serialized)
                event=payload['event'] if kind == 'dialogue' else {**payload['story'],'charges':payload['contract_charges']}
                events.append({'event_id':event_id,'story':event})
            return {'player_id':player_id,'financial_revision':ledger.revision,'events':events,
                    'next_before_event_id':page[-1][0] if len(rows)>limit else None}

    def player_context(self,team_id,player_id,*,context_format=None):
        """One validated read snapshot; never generates/rebinds an actor."""
        if type(player_id) is not str or not player_id.strip():
            raise ValueError('Stable player identity required')
        if context_format is not None and (type(context_format) is not str or context_format not in ('calendar_v1','calendar_v2','calendar_v3','calendar_v4')):
            raise ValueError('Unsupported player context format')
        with self._connection() as db:
            ledger = self._load(db,team_id)
            return self._player_context_from_ledger(db,team_id,player_id,ledger,context_format=context_format)

    def _player_context_from_ledger(self,db,team_id,player_id,ledger,*,context_format=None):
        context = ledger.negotiation_context(player_id)  # Require declared identity; floors may remain unknown.
        actor = ledger._actors.get(player_id)
        history=self._negotiation_history(db,team_id,player_id)
        accounting = None
        calendar_accounting = None
        if player_id in ledger._contracts:
            agreement=ledger.generation_accounting(ledger.contract_identity(player_id).generation_id)
            if context_format in ('calendar_v1','calendar_v2','calendar_v3','calendar_v4'):
                calendar_accounting=self._calendar_contract_context_from_ledger(team_id,ledger,agreement,context_format=context_format)
            else:
                accounting=self._generation_accounting_view(ledger,agreement)
        result = {'player_id':player_id,'financial_revision':ledger.revision,'initialized':actor is not None,
                **({'classification_pending':True,'observed_player_source':context['observed_player_source']}
                   if context.get('classification_pending') else {}),
                **({'legacy_contract':ledger._legacy_contracts[player_id].to_dict(),
                    'legacy_liability_scope':'original cap schedule; cash/protections/lifecycle unverified'}
                   if player_id in ledger._legacy_contracts else {}),
                'contract_accounting':accounting,
                'personality':actor['personality'] if actor else None,
                'relationships':actor['relationships'] if actor else None,
                'agreed_promises':[{'agreement_request_id':request,'goals':agreement['goals']}
                    for request,agreement in ledger._promise_agreements.items() if agreement['player_id'] == player_id],
                'promise_history':ledger.promise_history(player_id),
                'negotiation_history':history[-10:],
                'negotiation_history_total':len(history),
                'negotiation_history_has_more':len(history)>10}
        if context_format in ('calendar_v1','calendar_v2','calendar_v3','calendar_v4'):
            result.update(context_format=context_format,calendar_contract_context=calendar_accounting)
        return result

    def contract_generations(self, team_id):
        """Legacy contract identities and unresolved opening/prior-cohort records.

        This read does not assign players to unassociated debt, create a new
        contract generation, or establish game import or return-signing rights.
        """
        if type(team_id) is not str or not team_id.strip():
            raise ValueError('Stable team identity required')
        with self._connection() as db:
            return self._contract_generations_from_ledger(team_id,self._load(db,team_id))

    @staticmethod
    def _generation_accounting_view(ledger,agreement,*,archive_only=False,calendar_release=False,calendar_trade=False):
        if agreement.outgoing_trade_calendar_year is not None and not calendar_trade:
            raise Rejected('Calendar assignment archives require versioned lifecycle accounting')
        if agreement.release_calendar_year is not None and not calendar_release:
            raise Rejected('Calendar release archives require versioned lifecycle accounting')
        if ledger._generation_calendar_anchor is not None and not archive_only:
            raise Rejected('Legacy contract context cannot represent advanced calendar; use calendar contract context')
        identity=agreement.identity
        cash=ledger.generation_cash(identity.generation_id)
        return {'generation_id':identity.generation_id,'status':agreement.status,
            'contract':agreement.contract.to_dict(),
            'annual_charges':[json_amount(value) for value in agreement.annual_charges()],
            'charge_scope':'active_contract' if agreement.status=='active' else 'retained_obligations',
            'cash_obligation':cash.to_dict() if cash is not None else None,
            'guarantees':ledger.generation_guarantee_cash(identity.generation_id)}

    def contract_context(self,team_id,generation_id):
        """Read one exact team-book agreement, including its closed obligations."""
        if any(type(value) is not str or not value.strip() for value in (team_id,generation_id)):
            raise ValueError('Stable team and agreement identities required')
        with self._connection() as db:
            ledger=self._load(db,team_id)
            agreement=ledger.generation_accounting(generation_id)
            return {'team_id':team_id,'generation_id':generation_id,'financial_revision':ledger.revision,
                'accounting':self._generation_accounting_view(ledger,agreement)}

    def calendar_contract_context(self,team_id,generation_id,*,context_format='calendar_v1'):
        """Versioned current calendar state with a separately labeled economic archive."""
        if any(type(value) is not str or not value.strip() for value in (team_id,generation_id)):
            raise ValueError('Stable team and agreement identities required')
        with self._connection() as db:
            ledger=self._load(db,team_id)
            agreement=ledger.generation_accounting(generation_id)
            return self._calendar_contract_context_from_ledger(team_id,ledger,agreement,context_format=context_format)

    def _calendar_contract_context_from_ledger(self,team_id,ledger,agreement,*,context_format='calendar_v1'):
        if type(context_format) is not str or context_format not in ('calendar_v1','calendar_v2','calendar_v3','calendar_v4'):
            raise ValueError('Unsupported calendar accounting format')
        generation_id=agreement.identity.generation_id
        view=ledger.generation_calendar_view(generation_id)
        result = {'format':5 if context_format=='calendar_v4' else 4 if context_format=='calendar_v3' else 3 if context_format=='calendar_v2' else 2,'team_id':team_id,'generation_id':generation_id,
            'financial_revision':ledger.revision,'league_year':ledger._league_year,
            'calendar_accounting':{'status':view.status,
                'anchor_year':view.anchor_year,
                'current_contract':view.current_contract.to_dict() if view.current_contract is not None else None,
                'annual_charges':[json_amount(value) for value in view.annual_charges()],
                'ownership_current':ledger._active_generation_ids.get(agreement.identity.player_id)==generation_id,
                'expiry_source':view.expiry_source},
            'economic_archive':self._generation_accounting_view(ledger,agreement,archive_only=True,
                calendar_release=context_format in ('calendar_v2','calendar_v3','calendar_v4'),calendar_trade=context_format in ('calendar_v3','calendar_v4'))}
        if context_format in ('calendar_v2','calendar_v3','calendar_v4'):
            result['release_calendar']=({'league_year':agreement.release_calendar_year,
                'elapsed_years':agreement.release.original_contract.elapsed_years,
                'source':agreement.release.scope.source} if agreement.release_calendar_year is not None else None)
        if context_format in ('calendar_v3','calendar_v4'):
            result['trade_calendar']=({'league_year':agreement.outgoing_trade_calendar_year,
                'elapsed_years':agreement.outgoing_trade.original_contract.elapsed_years,
                'source':agreement.outgoing_trade.scope.source} if agreement.outgoing_trade_calendar_year is not None else None)
        if context_format=='calendar_v4':
            history=agreement.amendment_history_snapshot()
            if history is None and agreement.restructure is not None:
                history={'format':1,'prior_restructures':[],
                    'latest_restructure':ledger._restructure_snapshot(agreement.restructure)}
            result.update(original_contract=agreement.original_contract.to_dict(),amendment_history=history)
        return result

    @staticmethod
    def _contract_generations_from_ledger(team_id,ledger):
        if ledger._generation_calendar_anchor is not None:
            raise Rejected('Legacy generation inventory cannot represent advanced calendar')
        def charge_record(record):
            return {'record_id':record.record_id, 'annual_charges':[json_amount(value) for value in record.annual_charges],
                    'source':record.source}
        generations = []
        agreements=ledger.generation_agreements()
        for agreement in sorted(agreements,key=lambda item:(item.identity.player_id,item.identity.generation_id)):
            identity=agreement.identity
            cash=ledger.generation_cash(identity.generation_id)
            generations.append({'generation_id':identity.generation_id,
                'player_id':identity.player_id,'status':agreement.status,'contract':agreement.contract.to_dict(),
                'cash_obligation':cash.to_dict() if cash is not None else None,
                'retained_records':[charge_record(record) for record in agreement.retained_records]})
        books = ledger._opening_books
        linked_cash_ids = {agreement.identity.cash_obligation_id for agreement in agreements}
        return {'format':1, 'team_id':team_id, 'financial_revision':ledger.revision,
            **({'preserved_legacy_contracts':[contract.to_dict() for _,contract in sorted(ledger._legacy_contracts.items())]}
               if ledger._legacy_contracts else {}),
            'cash_revision':ledger._cash.revision if ledger._cash is not None else None,
            'generations':generations,
            'unassigned_cash_obligations':[record.to_dict() for key,record in sorted(ledger._cash.records.items())
                if key not in linked_cash_ids] if ledger._cash is not None else None,
            'unsigned_tenders':[{'player_id':player,'amount':amount} for player,amount in sorted(ledger._tenders.items())],
            'unassigned_prior_cohort_contracts':[contract.to_dict() for contract in ledger._rookie_pool_opening.prior_contracts]
                if ledger._rookie_pool_opening is not None else [],
            'unassigned_opening':{'retained':[charge_record(record) for record in books.retained],
                                  'adjustments':[charge_record(record) for record in books.adjustments]}}

    def load_team(self, team_id: str) -> Ledger:
        with self._connection() as db:
            return self._load(db, team_id)

    def roster_components(self, team, *, phase, league_year, classifications,
                          classification_source, selected_top51=None):
        """Read-only phase projection; does not alter signing authority or calendar."""
        from fractions import Fraction
        from franchise.minimums import minimum_salary
        from franchise.roster_accounting import RosterSalary, roster_charge
        if type(classification_source) is not str or not classification_source.strip():
            raise ValueError("Roster classification provenance required")
        ledger = self.load_team(team)
        if ledger._legacy_contracts:
            raise Rejected('Legacy roster-status projection requires verified conversion')
        if getattr(ledger, '_league_year', None) is not None and ledger._league_year != league_year:
            raise Rejected('Projection year disagrees with anchored league calendar')
        if ledger._opening_books is None:
            raise Rejected("Original obligation records required")
        if (ledger._veteran_minimum_profile is not None
                and ledger._veteran_minimum_profile.start_year != league_year):
            raise Rejected("Projection year disagrees with salary profile")
        players = set(ledger._active_contracts) | set(ledger._tenders)
        if type(classifications) is not dict or set(classifications) != players:
            raise ValueError("Explicit credited-season/UDFA inputs for every salary entry required")
        entries = []
        gross = Fraction(0)
        for player in sorted(players):
            inputs = classifications[player]
            if type(inputs) is not tuple or len(inputs) != 2:
                raise ValueError("Credited seasons and UDFA status required")
            credits, undrafted = inputs
            minimum = minimum_salary(league_year, credits, "active_inactive")
            if player in ledger._active_contracts:
                contract = ledger._active_contracts[player]
                base = contract.offer.salaries[contract.elapsed_years]
                value = contract.charges()[0]
                source = contract.source
            else:
                if undrafted is not False:
                    raise ValueError("Drafted rookie tender cannot be classified as UDFA")
                base = ledger._tenders[player]
                value = Fraction(base)
                source = "declared unsigned drafted rookie tender"
            gross += value
            entries.append(RosterSalary(player, base, value - base, minimum, undrafted, source))
        result = roster_charge(tuple(entries), phase=phase, selected_top51=selected_top51)
        retained = ledger.charges[0] - gross
        total = Fraction(result["supported_roster_charge"]) + retained
        if total < 0:
            raise Rejected("Phase projection credits exceed modeled liabilities")
        return {**result, "revision": ledger.revision, "league_year": league_year,
                "classification_source": classification_source,
                "retained_and_adjustment_charge": json_amount(retained),
                "projected_modeled_team_charge": json_amount(total),
                "current_authoritative_charge": json_amount(ledger.charges[0]),
                "signing_authority_changed": False}

    def termination_components(self, team, player, *, removed_on, discount, payment_year_offsets):
        """Read-only covered-bonus/base components; no release or cap-room grant."""
        from franchise.guarantees import DiscountProfile, guaranteed_base_liability
        from franchise.termination import signing_bonus_acceleration
        if not isinstance(discount, DiscountProfile):
            raise ValueError("Explicit discount profile required")
        ledger = self.load_team(team)
        contract = ledger.active_contract(player)
        if (ledger._veteran_minimum_profile is not None
                and ledger._veteran_minimum_profile.start_year != discount.league_year):
            raise Rejected("Termination year disagrees with franchise salary profile")
        cash = ledger.guarantee_cash(player)
        if cash is None:
            raise Rejected("Unpaid guarantee allocation is unavailable")
        guarantees = cash["unpaid_guaranteed_base_by_original_year"]
        if any(guarantees[:contract.elapsed_years]):
            raise Rejected("Unsettled prior-year guarantees require separate reconciliation")
        bonus = signing_bonus_acceleration(contract, league_year=discount.league_year,
            removed_on=removed_on, record_id="bonus:" + player)
        base = guaranteed_base_liability(contract,
            unpaid_by_year=tuple(guarantees[contract.elapsed_years:]),
            payment_year_offsets=payment_year_offsets, discount=discount,
            record_id="protected-base:" + player)
        return {"revision": ledger.revision, "player_id": player,
                "bonus_retained_charges": [json_amount(value) for value in bonus.annual_charges],
                "covered_base_present_value_charge": json_amount(base.cap_charge.annual_charges[0]),
                "nominal_unpaid_protected_base": base.nominal_unpaid,
                "nominal_unpaid_signing_bonus": cash["unpaid_signing_bonus"],
                "contract_source": contract.source, "rate_source": discount.rate_source,
                "release_authorized": False,
                "unresolved": ["covered termination facts and guarantee voids/offsets",
                               "earned salary, termination pay and injury protections",
                               "roster replacement/phase accounting"]}

    @staticmethod
    def _check_cash_components(ledger):
        if ledger._cash is None:
            return
        unknown=set(ledger._cash.unknown_legacy_players)
        if unknown and unknown!=set(ledger._legacy_contracts):
            raise ValueError('Unknown cash inventory disagrees with preserved legacy contracts')
        for agreement in ledger.generation_agreements():
            # The archive view validates canonical identities and archive-map coverage.
            record=ledger._cash.records.get(agreement.identity.cash_obligation_id)
            if record is None:
                raise ValueError('Known cash coverage lacks contract generation obligation')
            if record.paid_components is None:
                continue
            ceilings=agreement.payment_ceilings()
            if any(key not in ceilings or amount > ceilings[key] for key,amount in record.paid_components):
                raise ValueError('Paid component exceeds or disagrees with original contract')

    @staticmethod
    def _check_opening_cash(ledger, records, unknown_legacy_players=()):
        if set(unknown_legacy_players)!=set(ledger._legacy_contracts):
            raise Rejected('Explicit cash scope must identify every preserved legacy contract; cannot assume zero')
        by_id = {record.obligation_id: record for record in records}
        for player, offer in ledger._contracts.items():
            record = by_id.get(ledger.contract_cash_id(player))
            if record is None or record.player_id != player or record.amount != sum(offer.salaries) + offer.signing_bonus:
                raise ValueError("Opening cash must reconcile every original active contract")

    def initialize_cash(self, team_id, records: tuple[CashObligation, ...], *, source: str, unknown_legacy_players=()):
        book = CashBook(records, source,unknown_legacy_players=unknown_legacy_players)
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            if ledger._cash is not None:
                raise Rejected("Cash already initialized; refusing to reset payments")
            self._check_opening_cash(ledger, records,book.unknown_legacy_players)
            ledger._cash = book
            self._check_cash_components(ledger)
            ledger.revision += 1
            payload = {"records": [record.to_dict() for record in records], "source": source,
                       "cash_posting": book.snapshot(), "posting": ledger.financial_snapshot()}
            if book.unknown_legacy_players:
                payload['unknown_legacy_players']=list(book.unknown_legacy_players)
            db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, 'cash:opening', 'cash_open', ?)",
                       (team_id, json.dumps(payload, allow_nan=False)))

    def record_payment(self, team_id, request_id, obligation_id, amount, *, expected_cash_revision, source, payment_reference, component=None):
        if type(request_id) is not str or not request_id.strip() or type(source) is not str or not source.strip():
            raise ValueError("Payment request ID and evidence source required")
        if type(payment_reference) is not str or not payment_reference.strip():
            raise ValueError("Stable external payment reference required")
        money(amount)
        payload = dict(obligation_id=obligation_id, amount=amount, source=source, payment_reference=payment_reference,
                       expected_cash_revision=expected_cash_revision, component=component)
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            if ledger._cash is None:
                raise Rejected("Cash history is unavailable; explicit initialization required")
            key = "cash:payment:" + request_id
            prior = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, key)).fetchone()
            if prior:
                recorded = json.loads(prior[0])
                if "payment_reference" not in recorded:
                    raise Rejected("Legacy payment lacks external reference; audited migration required")
                if any(recorded[field] != payload[field] for field in ("obligation_id", "amount", "source", "payment_reference")) or recorded.get("component") != component:
                    raise Rejected("Payment request already recorded differently")
                return recorded["cash_posting"]
            for (serialized,) in db.execute("SELECT payload FROM events WHERE team_id=? AND kind='cash_payment'", (team_id,)):
                previous = json.loads(serialized)
                if previous.get("payment_reference") == payment_reference and previous["source"] == source:
                    raise Rejected("External payment evidence already recorded under another request")
            ledger._cash.pay(obligation_id, amount, expected_cash_revision, component=component)
            self._check_cash_components(ledger)
            ledger.revision += 1
            payload["cash_posting"] = ledger.cash_snapshot()
            payload["posting"] = ledger.financial_snapshot()
            if self._has_amendment_history(ledger):
                payload.update(format=2,generation_posting=ledger.generation_snapshot(history_format=2))
            elif self._has_new_generations(ledger):
                payload.update(format=1,generation_posting=ledger.generation_snapshot())
            if ledger._generation_calendar_anchor is not None:
                payload.update(calendar_format=1,calendar_posting=self._calendar_posting(ledger))
            db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'cash_payment', ?)",
                       (team_id, key, json.dumps(payload, allow_nan=False)))
            return payload["cash_posting"]

    @staticmethod
    def _scope_exclusions(value):
        if (type(value) is not list or any(type(item) is not str for item in value)
                or value != sorted(set(value))):
            raise ValueError('Canonical unique serialized exclusion list required')
        return frozenset(value)

    @staticmethod
    def _trade_plan(common):
        from datetime import date
        from franchise.books import ActiveContract
        from franchise.trades import PreseasonTradeScope,calculate_preseason_trade
        scope=dict(common['scope'])
        for field in ('traded_on','seller_first_regular_season_game','buyer_first_regular_season_game'):
            value=scope[field]
            parsed=date.fromisoformat(value)
            if parsed.isoformat()!=value:
                raise ValueError('Canonical trade dates required')
            scope[field]=parsed
        scope['exclusions']=FranchiseStore._scope_exclusions(scope['exclusions'])
        original=ActiveContract.from_dict(common['original_contract'])
        return calculate_preseason_trade(original,CashObligation.from_dict(common['original_cash']),
            scope=PreseasonTradeScope(**scope),record_id=common['record_id'],
            **({'expected_cash_id':common['original_cash']['obligation_id'],
                'buyer_cash_id':common['buyer_generation_id']} if common.get('format') in (1,2) else {}))

    def _replay_trade(self,db,ledger,team,kind,payload):
        if set(payload) != {'trade','posting','cash_posting'}:
            raise ValueError('Unexpected trade event fields')
        common=payload['trade']
        fields={'trade_id','seller','buyer','player_id','scope','record_id','expected_revisions',
                'original_contract','original_cash','before','after'}
        layered=kind in ('calendar_layered_trade_out','calendar_layered_trade_in')
        history_format=2 if layered else 1
        calendar=layered or kind in ('calendar_trade_out','calendar_trade_in')
        versioned=calendar or kind in ('generation_trade_out','generation_trade_in')
        if versioned:
            fields|={'format','seller_generation_id','buyer_generation_id','buyer_previous_generation_id','before_generations','after_generations'}
        if calendar:
            fields|={'calendar_format','before_calendars','after_calendars'}
        if (type(common) is not dict or set(common)!=fields or (versioned and
                (type(common['format']) is not int or common['format']!=history_format or db.execute('PRAGMA user_version').fetchone()[0]!=4))):
            raise ValueError('Complete paired trade source required')
        seller,buyer=common['seller'],common['buyer']
        if any(type(value) is not str or not value.strip() for value in (seller,buyer,common['trade_id'],common['player_id'])) or seller == buyer:
            raise ValueError('Distinct identified trade participants required')
        prefix='calendar-layered-trade:' if layered else 'calendar-trade:' if calendar else 'trade:'
        if calendar:
            if (type(common['calendar_format']) is not int or common['calendar_format']!=1
                    or ledger._generation_calendar_anchor is None
                    or any(type(common[name]) is not dict or set(common[name])!={seller,buyer}
                           for name in ('expected_revisions','before','after','before_generations','after_generations','before_calendars','after_calendars'))
                    or any(type(revision) is not int or revision<0 for revision in common['expected_revisions'].values())
                    or self._checkpoint_hash(common['before_calendars'][team])!=self._checkpoint_hash(self._calendar_posting(ledger))):
                raise ValueError('Complete current-calendar trade source required')
        roles={seller:'calendar_layered_trade_out' if layered else 'calendar_trade_out' if calendar else 'generation_trade_out' if versioned else 'trade_out',
               buyer:'calendar_layered_trade_in' if layered else 'calendar_trade_in' if calendar else 'generation_trade_in' if versioned else 'trade_in'}
        if roles.get(team) != kind or common['record_id'] != prefix+common['trade_id']:
            raise ValueError('Trade role or obligation identity disagrees')
        rows=db.execute('SELECT team_id,kind,payload FROM events WHERE request_key=?',(prefix+common['trade_id'],)).fetchall()
        if len(rows)!=2 or {participant:role for participant,role,_ in rows} != roles:
            raise ValueError('Exactly one paired trade event per participant required')
        for participant,role,serialized in rows:
            opposite=json.loads(serialized)
            if calendar and (type(opposite) is not dict or set(opposite)!={'trade','posting','cash_posting'}):
                raise ValueError('Unexpected paired calendar trade event fields')
            if ((self._checkpoint_hash(opposite.get('trade'))!=self._checkpoint_hash(common) or
                    self._checkpoint_hash(opposite.get('posting'))!=self._checkpoint_hash(common['after'][participant]['financial']) or
                    self._checkpoint_hash(opposite.get('cash_posting'))!=self._checkpoint_hash(common['after'][participant]['cash'])) if versioned else
                    (opposite.get('trade')!=common or opposite.get('posting')!=common['after'][participant]['financial'] or
                     opposite.get('cash_posting')!=common['after'][participant]['cash'])):
                raise ValueError('Paired trade postings disagree')
        before={'financial':ledger.financial_snapshot(),'cash':ledger.cash_snapshot()}
        if (self._checkpoint_hash(before)!=self._checkpoint_hash(common['before'][team]) if versioned else before!=common['before'][team]):
            raise ValueError('Trade source state disagrees with actual replay')
        if versioned:
            if self._checkpoint_hash(ledger.generation_snapshot(history_format=history_format))!=self._checkpoint_hash(common['before_generations'][team]):
                raise ValueError('Trade generation opening state disagrees with replay')
            from franchise.generations import assignment_identity
            if common['buyer_generation_id']!=assignment_identity(buyer,common['player_id'],common['trade_id']).generation_id:
                raise ValueError('Trade destination generation disagrees with source')
        plan=self._trade_plan(common)
        if plan.original_contract.offer.player_id != common['player_id']:
            raise ValueError('Trade and original player identity disagree')
        revision=common['expected_revisions'][team]
        if kind in ('trade_out','generation_trade_out','calendar_trade_out','calendar_layered_trade_out'):
            if versioned and common['seller_generation_id']!=ledger.contract_identity(common['player_id']).generation_id:
                raise ValueError('Trade seller generation disagrees with source')
            if (ledger.active_contract(common['player_id']) != plan.original_contract or ledger._cash is None
                    or ledger._cash.records.get(plan.original_cash.obligation_id) != plan.original_cash):
                raise ValueError('Trade original obligations disagree with seller history')
            if layered and not ledger.generation_accounting(common['seller_generation_id']).prior_restructures:
                raise ValueError('Layered assignment requires sourced seller amendment history')
            outgoing=ledger.apply_calendar_preseason_trade_out if calendar else ledger.apply_preseason_trade_out
            outgoing(common['player_id'],scope=plan.scope,record_id=common['record_id'],expected_revision=revision,
                **({'buyer_cash_id':common['buyer_generation_id']} if versioned else {}),
                **({'generation_id':common['seller_generation_id']} if calendar else {}))
        else:
            if versioned:
                parent=ledger.contract_identity(common['player_id']).generation_id if common['player_id'] in ledger._contracts else None
                if parent!=common['buyer_previous_generation_id']:
                    raise ValueError('Trade buyer prior agreement disagrees with source')
            incoming=ledger.apply_calendar_preseason_trade_in if calendar else ledger.apply_preseason_trade_in
            incoming(plan,expected_revision=revision,
                **({'assignment_request_id':common['trade_id'],'assigned_from_team':seller,
                    'assigned_from_generation_id':common['seller_generation_id']} if versioned else {}))
        if versioned and self._checkpoint_hash(ledger.generation_snapshot(history_format=history_format))!=self._checkpoint_hash(common['after_generations'][team]):
            raise ValueError('Trade generation resulting state disagrees with replay')
        if calendar and self._checkpoint_hash(self._calendar_posting(ledger))!=self._checkpoint_hash(common['after_calendars'][team]):
            raise ValueError('Trade calendar resulting state disagrees with replay')
        self._check_cash_components(ledger)
        after={'financial':ledger.financial_snapshot(),'cash':ledger.cash_snapshot()}
        if (self._checkpoint_hash(after)!=self._checkpoint_hash(common['after'][team]) if versioned else after!=common['after'][team]):
            raise ValueError('Trade resulting state disagrees with replay')

    def trade_preseason_veteran(self,request_id,seller,buyer,player_id,*,scope,seller_revision,buyer_revision,access_check,
                               seller_generation_id=None,buyer_previous_generation_id=None,require_generation_ids=False,include_generation_identity=False,receipt_check=None):
        return self._trade_preseason_veteran(request_id,seller,buyer,player_id,scope=scope,seller_revision=seller_revision,
            buyer_revision=buyer_revision,access_check=access_check,seller_generation_id=seller_generation_id,
            buyer_previous_generation_id=buyer_previous_generation_id,require_generation_ids=require_generation_ids,
            include_generation_identity=include_generation_identity,receipt_check=receipt_check,calendar_assignment=False)

    def trade_calendar_preseason_veteran(self,request_id,seller,buyer,player_id,*,scope,seller_revision,buyer_revision,
                                       seller_generation_id,buyer_previous_generation_id,access_check,receipt_check=None):
        if type(seller_generation_id) is not str or not seller_generation_id.strip():
            raise Rejected('Exact calendar seller generation required')
        return self._trade_preseason_veteran(request_id,seller,buyer,player_id,scope=scope,seller_revision=seller_revision,
            buyer_revision=buyer_revision,access_check=access_check,seller_generation_id=seller_generation_id,
            buyer_previous_generation_id=buyer_previous_generation_id,require_generation_ids=True,
            include_generation_identity=True,receipt_check=receipt_check,calendar_assignment=True)

    def trade_calendar_layered_preseason_veteran(self,request_id,seller,buyer,player_id,*,scope,seller_revision,buyer_revision,
                                               seller_generation_id,buyer_previous_generation_id,access_check,receipt_check=None):
        if type(seller_generation_id) is not str or not seller_generation_id.strip():
            raise Rejected('Exact calendar seller generation required')
        return self._trade_preseason_veteran(request_id,seller,buyer,player_id,scope=scope,seller_revision=seller_revision,
            buyer_revision=buyer_revision,access_check=access_check,seller_generation_id=seller_generation_id,
            buyer_previous_generation_id=buyer_previous_generation_id,require_generation_ids=True,
            include_generation_identity=True,receipt_check=receipt_check,calendar_assignment=True,layered=True)

    def _trade_preseason_veteran(self,request_id,seller,buyer,player_id,*,scope,seller_revision,buyer_revision,access_check,
                               seller_generation_id,buyer_previous_generation_id,require_generation_ids,include_generation_identity,
                               receipt_check,calendar_assignment,layered=False):
        from franchise.trades import PreseasonTradeScope
        if receipt_check is not None and not callable(receipt_check):
            raise ValueError('Callable lifecycle receipt validation required')
        if any(type(value) is not str or not value.strip() for value in (request_id,seller,buyer,player_id)) or seller == buyer:
            raise ValueError('Distinct identified trade participants required')
        if not isinstance(scope,PreseasonTradeScope) or not callable(access_check):
            raise ValueError('Sourced trade scope and final access check required')
        if any(type(revision) is not int or revision < 0 for revision in (seller_revision,buyer_revision)):
            raise ValueError('Integer participant revisions required')
        if type(require_generation_ids) is not bool or type(include_generation_identity) is not bool:
            raise ValueError('Explicit generation requirement flag required')
        if any(v is not None and (type(v) is not str or not v.strip()) for v in (seller_generation_id,buyer_previous_generation_id)):
            raise ValueError('Identified trade agreements required')
        scope_data=asdict(scope)
        for field in ('traded_on','seller_first_regular_season_game','buyer_first_regular_season_game'):
            scope_data[field]=getattr(scope,field).isoformat()
        scope_data['exclusions']=sorted(scope.exclusions)
        prefix='calendar-layered-trade:' if layered else 'calendar-trade:' if calendar_assignment else 'trade:'
        history_format=2 if layered else 1
        requested={'trade_id':request_id,'seller':seller,'buyer':buyer,'player_id':player_id,'scope':scope_data,
                   'record_id':prefix+request_id,'expected_revisions':{seller:seller_revision,buyer:buyer_revision}}
        with self._connection(write=True) as db:
            participants=self._load_teams(db,(seller,buyer))
            source,target=participants[seller],participants[buyer]
            key=prefix+request_id
            rows=db.execute('SELECT payload FROM events WHERE request_key=?',(key,)).fetchall()
            if rows:
                if len(rows)!=2:
                    raise ValueError('Incomplete trade receipt')
                common=json.loads(rows[0][0])['trade']
                if (require_generation_ids and common.get('format') in (1,2) and seller_generation_id is None):
                    raise ValueError('Versioned trade retry requires agreement identities')
                if seller_generation_id is not None and (common.get('seller_generation_id')!=seller_generation_id or
                        common.get('buyer_previous_generation_id')!=buyer_previous_generation_id):
                    raise Rejected('Trade request targets different agreements')
                if any(self._checkpoint_hash(common[field]) != self._checkpoint_hash(requested[field]) for field in requested):
                    raise Rejected('Trade request already recorded differently')
                receipt=self._trade_receipt(common,include_generation_identity)
                if receipt_check is not None:
                    receipt_check(receipt)
                access_check()
                return receipt
            if calendar_assignment and (db.execute('PRAGMA user_version').fetchone()[0]!=4
                    or source._generation_calendar_anchor is None or target._generation_calendar_anchor is None
                    or source._league_year!=scope.league_year or target._league_year!=scope.league_year):
                raise Rejected('Both participants require the current migrated league calendar')
            owner=db.execute('SELECT team_id FROM ownership WHERE player_id=?',(player_id,)).fetchone()
            if owner != (seller,):
                raise Rejected('Seller lacks exclusive player ownership')
            source_id=source.contract_identity(player_id).generation_id
            parent_id=target.contract_identity(player_id).generation_id if player_id in target._contracts else None
            if layered and not source.generation_accounting(source_id).prior_restructures:
                raise Rejected('Layered assignment requires sourced seller amendment history')
            versioned=seller_generation_id is not None or source_id.startswith('contract-gen:') or parent_id is not None or self._has_new_generations(source) or self._has_new_generations(target)
            if versioned and db.execute('PRAGMA user_version').fetchone()[0]!=4:
                raise Rejected('Versioned assignment requires explicit format4 migration')
            if versioned and require_generation_ids and seller_generation_id is None:
                raise ValueError('Versioned assignment requires explicit agreement identities')
            if seller_generation_id is not None and (seller_generation_id!=source_id or buyer_previous_generation_id!=parent_id):
                raise Rejected('Trade targets different current agreements')
            common={**requested,'before':{seller:{'financial':source.financial_snapshot(),'cash':source.cash_snapshot()},
                                         buyer:{'financial':target.financial_snapshot(),'cash':target.cash_snapshot()}}}
            if versioned:
                from franchise.generations import assignment_identity
                destination=assignment_identity(buyer,player_id,request_id)
                common.update(format=history_format,seller_generation_id=source_id,buyer_generation_id=destination.generation_id,
                    buyer_previous_generation_id=parent_id,before_generations={seller:source.generation_snapshot(history_format=history_format),buyer:target.generation_snapshot(history_format=history_format)})
            if calendar_assignment:
                common.update(calendar_format=1,before_calendars={seller:self._calendar_posting(source),buyer:self._calendar_posting(target)})
            outgoing=source.apply_calendar_preseason_trade_out if calendar_assignment else source.apply_preseason_trade_out
            plan=outgoing(player_id,scope=scope,record_id=key,expected_revision=seller_revision,
                **({'buyer_cash_id':destination.cash_obligation_id} if versioned else {}),
                **({'generation_id':source_id} if calendar_assignment else {}))
            incoming=target.apply_calendar_preseason_trade_in if calendar_assignment else target.apply_preseason_trade_in
            incoming(plan,expected_revision=buyer_revision,
                **({'assignment_request_id':request_id,'assigned_from_team':seller,
                    'assigned_from_generation_id':source_id} if versioned else {}))
            self._check_cash_components(source)
            self._check_cash_components(target)
            original=plan.original_contract
            common.update(original_contract=original.to_dict(),original_cash=plan.original_cash.to_dict(),
                after={seller:{'financial':source.financial_snapshot(),'cash':source.cash_snapshot()},
                       buyer:{'financial':target.financial_snapshot(),'cash':target.cash_snapshot()}})
            if versioned:
                common['after_generations']={seller:source.generation_snapshot(history_format=history_format),buyer:target.generation_snapshot(history_format=history_format)}
            if calendar_assignment:
                common['after_calendars']={seller:self._calendar_posting(source),buyer:self._calendar_posting(target)}
            receipt=self._trade_receipt(common,include_generation_identity)
            if receipt_check is not None:
                receipt_check(receipt)
            access_check()
            if db.execute('UPDATE ownership SET team_id=? WHERE player_id=? AND team_id=?',(buyer,player_id,seller)).rowcount != 1:
                raise Rejected('Trade ownership changed')
            for team,kind in ((seller,'calendar_layered_trade_out' if layered else 'calendar_trade_out' if calendar_assignment else 'generation_trade_out' if versioned else 'trade_out'),
                              (buyer,'calendar_layered_trade_in' if layered else 'calendar_trade_in' if calendar_assignment else 'generation_trade_in' if versioned else 'trade_in')):
                posting=common['after'][team]
                db.execute('INSERT INTO events (team_id,request_key,kind,payload) VALUES (?,?,?,?)',
                    (team,key,kind,json.dumps({'trade':common,'posting':posting['financial'],'cash_posting':posting['cash']},allow_nan=False)))
            return receipt

    @staticmethod
    def _trade_receipt(common,include_identity):
        if include_identity and common.get('format') in (1,2):
            return {'participants':common['after'],'seller_generation_id':common['seller_generation_id'],
                'buyer_generation_id':common['buyer_generation_id'],
                'buyer_previous_generation_id':common['buyer_previous_generation_id'],
                **({'format':3 if common.get('format')==2 else 2,'league_year':common['scope']['league_year']} if common.get('calendar_format')==1 else {}),
                **({'amendment_history':next(a['amendment_history'] for a in common['after_generations'][common['seller']]['agreements']
                    if a['identity']['generation_id']==common['seller_generation_id'])} if common.get('format')==2 else {})}
        return common['after']

    @staticmethod
    def _apply_release_payload(ledger,payload,*,calendar_release=False):
        from datetime import date
        from franchise.releases import PreseasonReleaseScope
        from franchise.guarantees import DiscountProfile
        scope=dict(payload['scope'])
        for field in ('removed_on','first_regular_season_game'):
            raw=scope[field]
            parsed=date.fromisoformat(raw)
            if calendar_release and parsed.isoformat()!=raw:
                raise ValueError('Canonical calendar release date required')
            scope[field]=parsed
        scope['exclusions']=FranchiseStore._scope_exclusions(scope['exclusions'])
        discount=dict(payload['discount'])
        discount['annual_rate']=parse_amount(discount['annual_rate'])
        if calendar_release and FranchiseStore._checkpoint_hash(payload['discount']['annual_rate']) != FranchiseStore._checkpoint_hash(json_amount(discount['annual_rate'])):
            raise ValueError('Canonical calendar release discount required')
        apply=ledger.apply_calendar_preseason_release if calendar_release else ledger.apply_preseason_release
        return apply(payload['player_id'],scope=PreseasonReleaseScope(**scope),
            discount=DiscountProfile(**discount),payment_year_offsets=tuple(payload['payment_year_offsets']),
            record_id=payload['record_id'],expected_revision=payload['expected_revision'],
            **({'generation_id':payload['generation_id']} if calendar_release else {}))

    @staticmethod
    def _apply_restructure_payload(ledger,payload,*,calendar_restructure=False,layered=False):
        from datetime import date
        from franchise.restructures import PreseasonRestructureScope
        scope=dict(payload['scope'])
        for field in ('amended_on','first_regular_season_game'):
            value=scope[field]
            if type(value) is not str:
                raise ValueError('Canonical restructure date required')
            parsed=date.fromisoformat(value)
            if parsed.isoformat()!=value:
                raise ValueError('Canonical restructure date required')
            scope[field]=parsed
        scope['exclusions']=FranchiseStore._scope_exclusions(scope['exclusions'])
        apply=(ledger.apply_calendar_layered_preseason_restructure if layered else
            ledger.apply_calendar_preseason_restructure if calendar_restructure else ledger.apply_preseason_restructure)
        return apply(payload['player_id'],scope=PreseasonRestructureScope(**scope),
            converted_base=payload['converted_base'],record_id=payload['record_id'],
            expected_revision=payload['expected_revision'],
            **({'generation_id':payload['generation_id']} if calendar_restructure else {}))

    def restructure_calendar_preseason_veteran(self,team_id,request_id,player_id,*,generation_id,
                                               scope,converted_base,expected_revision,access_check,receipt_check=None):
        return self._restructure_calendar_preseason_veteran(team_id,request_id,player_id,generation_id=generation_id,
            scope=scope,converted_base=converted_base,expected_revision=expected_revision,
            access_check=access_check,receipt_check=receipt_check,layered=False)

    def restructure_calendar_layered_preseason_veteran(self,team_id,request_id,player_id,*,generation_id,
                                                       scope,converted_base,expected_revision,access_check,receipt_check=None):
        return self._restructure_calendar_preseason_veteran(team_id,request_id,player_id,generation_id=generation_id,
            scope=scope,converted_base=converted_base,expected_revision=expected_revision,
            access_check=access_check,receipt_check=receipt_check,layered=True)

    def _restructure_calendar_preseason_veteran(self,team_id,request_id,player_id,*,generation_id,
                                              scope,converted_base,expected_revision,access_check,receipt_check,layered):
        from franchise.restructures import PreseasonRestructureScope
        if (any(type(value) is not str or not value.strip() for value in (team_id,request_id,player_id,generation_id))
                or not isinstance(scope,PreseasonRestructureScope) or not callable(access_check)
                or (receipt_check is not None and not callable(receipt_check))
                or type(expected_revision) is not int or expected_revision<0):
            raise ValueError('Exact calendar amendment identity and sourced typed inputs required')
        money(converted_base)
        scope_data=asdict(scope)
        scope_data.update(amended_on=scope.amended_on.isoformat(),
            first_regular_season_game=scope.first_regular_season_game.isoformat(),exclusions=sorted(scope.exclusions))
        kind='calendar_layered_restructure' if layered else 'calendar_restructure'
        history_format=2 if layered else 1
        key=('calendar-layered-restructure:' if layered else 'calendar-restructure:')+request_id
        requested={'player_id':player_id,'generation_id':generation_id,'scope':scope_data,
            'converted_base':converted_base,'record_id':key,'expected_revision':expected_revision}
        def receipt_for(saved):
            return {'format':3 if layered else 2,'generation_id':saved['generation_id'],'league_year':saved['scope']['league_year'],
                'financial':saved['posting'],'cash':saved['cash_posting'],
                **({'amendment_history':next(a['amendment_history'] for a in saved['generation_posting']['agreements']
                    if a['identity']['generation_id']==saved['generation_id'])} if layered else {})}
        with self._connection(write=True) as db:
            if db.execute('PRAGMA user_version').fetchone()[0]!=4:
                raise Rejected('Calendar restructure requires explicit format4 migration')
            ledger=self._load(db,team_id)
            row=db.execute('SELECT kind,payload FROM events WHERE team_id=? AND request_key=?',(team_id,key)).fetchone()
            if row:
                saved=json.loads(row[1])
                if row[0]!=kind or any(self._checkpoint_hash(saved[field])!=self._checkpoint_hash(value)
                        for field,value in requested.items()):
                    raise Rejected('Calendar amendment retry changed its terms')
                receipt=receipt_for(saved)
                if receipt_check is not None: receipt_check(receipt)
                access_check()
                return receipt
            if db.execute('SELECT team_id FROM ownership WHERE player_id=?',(player_id,)).fetchone()!=(team_id,):
                raise Rejected('Calendar amendment requires exclusive player ownership')
            contract=ledger.active_contract(player_id)
            cash=ledger.generation_cash(generation_id)
            if cash is None:
                raise Rejected('Allocated calendar amendment cash required')
            payload={**requested,'format':history_format,'calendar_format':1,
                'before_posting':ledger.financial_snapshot(),'before_cash':ledger.cash_snapshot(),
                'before_generation_posting':ledger.generation_snapshot(history_format=history_format),'before_calendar_posting':self._calendar_posting(ledger),
                'original_contract':contract.to_dict(),'original_cash':cash.to_dict()}
            self._apply_restructure_payload(ledger,payload,calendar_restructure=True,layered=layered)
            self._check_cash_components(ledger)
            payload.update(posting=ledger.financial_snapshot(),cash_posting=ledger.cash_snapshot(),
                generation_posting=ledger.generation_snapshot(history_format=history_format),calendar_posting=self._calendar_posting(ledger))
            receipt=receipt_for(payload)
            if receipt_check is not None: receipt_check(receipt)
            access_check()
            db.execute('INSERT INTO events(team_id,request_key,kind,payload) VALUES(?,?,?,?)',
                (team_id,key,kind,json.dumps(payload,allow_nan=False)))
            return receipt

    def restructure_preseason_veteran(self,team_id,request_id,player_id,*,scope,converted_base,
                                      expected_revision,access_check,generation_id=None,require_return_generation_id=False,receipt_check=None):
        from franchise.restructures import PreseasonRestructureScope
        if receipt_check is not None and not callable(receipt_check):
            raise ValueError('Callable lifecycle receipt validation required')
        if any(type(value) is not str or not value.strip() for value in (request_id,player_id)) or not callable(access_check):
            raise ValueError('Stable amendment identities and final access check required')
        if not isinstance(scope,PreseasonRestructureScope):
            raise ValueError('Typed sourced amendment scope required')
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError('Integer amendment revision required')
        if type(require_return_generation_id) is not bool:
            raise ValueError('Explicit agreement requirement flag required')
        if generation_id is not None and (type(generation_id) is not str or not generation_id.strip()):
            raise ValueError('Explicit agreement identity required')
        money(converted_base)
        scope_data=asdict(scope)
        scope_data.update(amended_on=scope.amended_on.isoformat(),
            first_regular_season_game=scope.first_regular_season_game.isoformat(),exclusions=sorted(scope.exclusions))
        key='restructure:'+request_id
        payload={'player_id':player_id,'scope':scope_data,'converted_base':converted_base,
                 'record_id':key,'expected_revision':expected_revision}
        with self._connection(write=True) as db:
            ledger=self._load(db,team_id)
            row=db.execute('SELECT payload FROM events WHERE team_id=? AND request_key=?',(team_id,key)).fetchone()
            if row:
                previous=json.loads(row[0])
                if require_return_generation_id and generation_id is None and 'generation_id' in previous:
                    raise ValueError('Returned amendment retry requires explicit generation identity')
                if generation_id is not None and previous.get('generation_id') != generation_id:
                    raise Rejected('Amendment request targets a different generation')
                if any(previous[field] != payload[field] for field in payload):
                    raise Rejected('Amendment request already recorded differently')
                receipt={'financial':previous['posting'],'cash':previous['cash_posting']}
                if receipt_check is not None:
                    receipt_check(receipt)
                access_check()
                return receipt
            if (require_return_generation_id and generation_id is None
                    and ledger.contract_identity(player_id).generation_id.startswith('contract-gen:')):
                raise ValueError('Returned agreement requires explicit generation identity')
            if generation_id is not None and ledger.contract_identity(player_id).generation_id != generation_id:
                raise Rejected('Amendment targets a different current generation')
            if db.execute('SELECT team_id FROM ownership WHERE player_id=?',(player_id,)).fetchone() != (team_id,):
                raise Rejected('Amendment requires exclusive player ownership')
            cash_id = ledger.contract_cash_id(player_id)
            if ledger._cash is None or cash_id not in ledger._cash.records:
                raise Rejected('Allocated contract cash required for amendment')
            kind='restructure'
            if ledger.contract_identity(player_id).generation_id.startswith('contract-gen:'):
                if db.execute('PRAGMA user_version').fetchone()[0]!=4:
                    raise Rejected('Generation restructure requires format4')
                kind='generation_restructure'
                payload.update(format=1,generation_id=ledger.contract_identity(player_id).generation_id,
                    before_generation_posting=ledger.generation_snapshot())
            payload.update(before_posting=ledger.financial_snapshot(),before_cash=ledger.cash_snapshot(),
                original_contract=ledger.active_contract(player_id).to_dict(),
                original_cash=ledger._cash.records[cash_id].to_dict())
            self._apply_restructure_payload(ledger,payload)
            self._check_cash_components(ledger)
            payload.update(posting=ledger.financial_snapshot(),cash_posting=ledger.cash_snapshot())
            if kind=='generation_restructure':
                payload['generation_posting']=ledger.generation_snapshot()
            receipt={'financial':payload['posting'],'cash':payload['cash_posting']}
            if receipt_check is not None:
                receipt_check(receipt)
            access_check()
            db.execute("INSERT INTO events (team_id,request_key,kind,payload) VALUES (?,?,?,?)",
                       (team_id,key,kind,json.dumps(payload,allow_nan=False)))
            return receipt

    def release_preseason_veteran(self,team_id,request_id,player_id,*,scope,discount,payment_year_offsets,
                                 expected_revision,access_check,receipt_check=None):
        return self._release_preseason_veteran(team_id,request_id,player_id,scope=scope,discount=discount,
            payment_year_offsets=payment_year_offsets,expected_revision=expected_revision,
            access_check=access_check,receipt_check=receipt_check,calendar_generation_id=None)

    def release_calendar_preseason_veteran(self,team_id,request_id,player_id,*,generation_id,scope,discount,
                                         payment_year_offsets,expected_revision,access_check,receipt_check=None):
        if type(generation_id) is not str or not generation_id.strip():
            raise Rejected('Exact calendar release generation required')
        return self._release_preseason_veteran(team_id,request_id,player_id,scope=scope,discount=discount,
            payment_year_offsets=payment_year_offsets,expected_revision=expected_revision,
            access_check=access_check,receipt_check=receipt_check,calendar_generation_id=generation_id)

    def release_calendar_layered_preseason_veteran(self,team_id,request_id,player_id,*,generation_id,scope,discount,
                                                 payment_year_offsets,expected_revision,access_check,receipt_check=None):
        if type(generation_id) is not str or not generation_id.strip():
            raise Rejected('Exact calendar release generation required')
        return self._release_preseason_veteran(team_id,request_id,player_id,scope=scope,discount=discount,
            payment_year_offsets=payment_year_offsets,expected_revision=expected_revision,
            access_check=access_check,receipt_check=receipt_check,calendar_generation_id=generation_id,layered=True)

    def _release_preseason_veteran(self,team_id,request_id,player_id,*,scope,discount,payment_year_offsets,
                                 expected_revision,access_check,receipt_check,calendar_generation_id,layered=False):
        from franchise.releases import PreseasonReleaseScope
        if receipt_check is not None and not callable(receipt_check):
            raise ValueError('Callable lifecycle receipt validation required')
        from franchise.guarantees import DiscountProfile
        if any(type(value) is not str or not value.strip() for value in (request_id,player_id)) or not callable(access_check):
            raise ValueError('Stable release identities and final access check required')
        if not isinstance(scope,PreseasonReleaseScope) or not isinstance(discount,DiscountProfile) or type(payment_year_offsets) is not tuple:
            raise ValueError('Typed sourced release inputs required')
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError('Integer release revision required')
        scope_data=asdict(scope)
        scope_data.update(removed_on=scope.removed_on.isoformat(),first_regular_season_game=scope.first_regular_season_game.isoformat(),
                          exclusions=sorted(scope.exclusions))
        prefix='calendar-layered-release:' if layered else 'calendar-release:' if calendar_generation_id is not None else 'release:'
        history_format=2 if layered else 1
        payload={'player_id':player_id,'scope':scope_data,'discount':{'league_year':discount.league_year,
            'annual_rate':json_amount(discount.annual_rate),'rate_source':discount.rate_source},
            'payment_year_offsets':list(payment_year_offsets),'record_id':prefix+request_id,'expected_revision':expected_revision}
        if calendar_generation_id is not None:
            payload['generation_id']=calendar_generation_id
        def receipt_for(saved):
            result={'financial':saved['posting'],'cash':saved['cash_posting']}
            if calendar_generation_id is not None:
                result.update(format=3 if layered else 2,generation_id=saved['generation_id'],league_year=saved['scope']['league_year'])
            if layered:
                result['amendment_history']=next(a['amendment_history'] for a in saved['generation_posting']['agreements']
                    if a['identity']['generation_id']==saved['generation_id'])
            return result
        with self._connection(write=True) as db:
            ledger=self._load(db,team_id)
            key=prefix+request_id
            row=db.execute('SELECT payload FROM events WHERE team_id=? AND request_key=?',(team_id,key)).fetchone()
            if row:
                previous=json.loads(row[0])
                if any(self._checkpoint_hash(previous[field]) != self._checkpoint_hash(payload[field]) for field in payload):
                    raise Rejected('Release request already recorded differently')
                receipt=receipt_for(previous)
                if receipt_check is not None:
                    receipt_check(receipt)
                access_check()
                return receipt
            kind='release'
            if calendar_generation_id is not None:
                if db.execute('PRAGMA user_version').fetchone()[0]!=4:
                    raise Rejected('Calendar release requires explicit format4 migration')
                kind='calendar_layered_release' if layered else 'calendar_release'
                if layered and not ledger.generation_accounting(calendar_generation_id).prior_restructures:
                    raise Rejected('Layered release requires sourced prior amendment history')
                payload.update(format=history_format,calendar_format=1,before_generation_posting=ledger.generation_snapshot(history_format=history_format),
                    before_calendar_posting=self._calendar_posting(ledger))
            elif ledger.contract_identity(player_id).generation_id.startswith('contract-gen:'):
                kind='generation_release'
                payload.update(format=1,generation_id=ledger.contract_identity(player_id).generation_id,
                    before_generation_posting=ledger.generation_snapshot(history_format=history_format))
            payload.update(before_posting=ledger.financial_snapshot(),before_cash=ledger.cash_snapshot())
            self._apply_release_payload(ledger,payload,calendar_release=kind in ('calendar_release','calendar_layered_release'))
            self._check_cash_components(ledger)
            payload.update(posting=ledger.financial_snapshot(),cash_posting=ledger.cash_snapshot())
            if kind in ('generation_release','calendar_release','calendar_layered_release'):
                payload['generation_posting']=ledger.generation_snapshot(history_format=history_format)
            if kind in ('calendar_release','calendar_layered_release'):
                payload['calendar_posting']=self._calendar_posting(ledger)
            receipt=receipt_for(payload)
            if receipt_check is not None:
                receipt_check(receipt)
            access_check()
            if db.execute('DELETE FROM ownership WHERE player_id=? AND team_id=?',(player_id,team_id)).rowcount != 1:
                raise Rejected('Release ownership is unavailable')
            db.execute("INSERT INTO events (team_id,request_key,kind,payload) VALUES (?,?,?,?)",
                       (team_id,key,kind,json.dumps(payload,allow_nan=False)))
            return receipt

    def preview_offer(self, team_id: str, offer: Offer, expected_revision: int) -> dict:
        with self._connection() as db:
            ledger = self._load(db, team_id)
            if db.execute("SELECT 1 FROM ownership WHERE player_id=?", (offer.player_id,)).fetchone():
                raise Rejected("Player already belongs to a team")
            self._check_draft_right(db, team_id, offer.player_id)
            return ledger.preview_offer(offer, expected_revision)

    def preview_draft_offer(self, team_id, offer, expected_revision):
        with self._connection() as db:
            ledger = self._load(db, team_id)
            if db.execute("SELECT 1 FROM ownership WHERE player_id=?", (offer.player_id,)).fetchone() or db.execute("SELECT 1 FROM draft_picks WHERE player_id=?", (offer.player_id,)).fetchone():
                raise Rejected('Prospect already selected or contracted')
            return ledger.preview_offer(offer, expected_revision)

    def sign(self, team_id: str, request_id: str, offer: Offer, expected_revision: int,
             *, access_check=None, story: dict | None = None):
        return self._sign(team_id,request_id,offer,expected_revision,access_check=access_check,story=story)

    def commit_accepted_proposal(self, team_id, proposal_request_id, request_id, expected_revision, *, access_check):
        """Engine-only settlement; not guest application or save confirmation.

        A future guest coordinator must journal/verify game effects separately.
        Neither this method nor a recorded acceptance grants guest write access.
        """
        if (type(proposal_request_id) is not str or not proposal_request_id.strip()
                or proposal_request_id==request_id or not callable(access_check)):
            raise ValueError('Distinct proposal/settlement IDs and current access check required')
        return self._sign(team_id,request_id,None,expected_revision,access_check=access_check,
                          proposal_request_id=proposal_request_id)

    def _settlement_story(self, db, team_id, proposal_request_id, request_id, *, before_event_id=None):
        row=db.execute("SELECT id,payload FROM events WHERE team_id=? AND request_key=? AND kind='dialogue' "
                       "AND (? IS NULL OR id<?)",
                       (team_id,'dialogue:'+proposal_request_id,before_event_id,before_event_id)).fetchone()
        if row is None:
            raise Rejected('Recorded accepted proposal required')
        proposal=json.loads(row[1])['event']
        self._validate_dialogue(proposal)
        if proposal['outcome']!='accepted_proposal':
            raise Rejected('Only an accepted proposal can settle')
        if db.execute("SELECT 1 FROM events WHERE team_id=? AND kind='sign' "
                      "AND json_extract(payload,'$.proposal_request_id')=? AND (? IS NULL OR id<?)",
                      (team_id,proposal_request_id,before_event_id,before_event_id)).fetchone():
            raise Rejected('Proposal already settled')
        player=proposal['offer']['player_id']
        history=[]
        for kind,serialized in db.execute("SELECT kind,payload FROM events WHERE team_id=? "
                "AND kind IN ('sign','return_sign','dialogue') AND (? IS NULL OR id<?) ORDER BY id",
                (team_id,before_event_id,before_event_id)):
            payload=json.loads(serialized)
            previous=payload['event'] if kind=='dialogue' else payload.get('story')
            if previous is not None and previous['offer']['player_id']==player:
                history.append(previous['request_id'])
        if not history or history[-1]!=proposal_request_id or history[:-1]!=proposal.get('history_request_ids'):
            raise Rejected('Accepted proposal is no longer the current negotiation')
        return {**proposal,'request_id':request_id,'outcome':'signed','decision_mode':'proposal_settlement',
                'proposal_request_id':proposal_request_id,'history_request_ids':history}

    def _sign(self, team_id, request_id, offer, expected_revision, *, access_check=None, story=None,
              proposal_request_id=None, _db=None):
        if type(request_id) is not str or not request_id.strip():
            raise Rejected("A request ID is required")
        if story is not None and type(story) is not dict:
            raise ValueError("Story must be a JSON object")
        if story is not None and ('proposal_request_id' in story or story.get('decision_mode')=='proposal_settlement'):
            raise Rejected('Proposal settlement requires its dedicated path')
        # The guest coordinator supplies its transaction so journal resolution
        # and all signing effects cannot commit separately.
        if _db is None:
            with self._connection(write=True) as db:
                return self._sign(team_id,request_id,offer,expected_revision,access_check=access_check,
                                  story=story,proposal_request_id=proposal_request_id,_db=db)
        db=_db
        ledger = self._load(db, team_id)
        prior = db.execute("SELECT id,kind,payload FROM events WHERE team_id=? AND request_key=?", (team_id, "sign:" + request_id)).fetchone()
        if proposal_request_id is not None:
            story=self._settlement_story(db,team_id,proposal_request_id,request_id,
                                        before_event_id=prior[0] if prior else None)
            offer=Offer.from_dict(story['offer'])
            if type(expected_revision) is not int or expected_revision!=story['evidence']['financial_revision']:
                raise Rejected('Settlement revision differs from accepted proposal')
        self._validate_story_evidence(story)
        payload = {"request_id": request_id, "offer": offer.to_dict(),
                   "expected_revision": expected_revision, "story": story}
        if proposal_request_id is not None:
            payload['proposal_request_id']=proposal_request_id
        serialized=json.dumps(payload,allow_nan=False)
        if db.execute("SELECT 1 FROM events WHERE team_id=? AND request_key=?", (team_id, "dialogue:" + request_id)).fetchone():
            raise Rejected("Request already belongs to a recorded negotiation")
        if prior:
            if prior[1] != 'sign':
                raise Rejected("Request belongs to an explicit return signing")
            previous = json.loads(prior[2])
            if "story" not in previous:
                raise Rejected("Request belongs to an explicit return signing")
            normalized = json.loads(serialized)
            if (previous["offer"] != normalized["offer"] or previous.get("story") != normalized["story"]
                    or previous.get('proposal_request_id')!=proposal_request_id):
                raise Rejected("Request already committed with different terms or story")
            return ledger.sign(request_id, offer, expected_revision, access_check=access_check)
        if db.execute("SELECT 1 FROM ownership WHERE player_id=?", (offer.player_id,)).fetchone():
            raise Rejected("Player already belongs to a team")
        self._check_draft_right(db, team_id, offer.player_id)
        if story is not None:
            self._check_history(db, team_id, offer.player_id, story)
        if proposal_request_id is not None:
            preview=ledger.preview_offer(offer,expected_revision)
            if self._checkpoint_hash(preview)!=self._checkpoint_hash(story['proposal_preview']):
                raise Rejected('Accepted proposal preview changed before settlement')
        receipt = ledger.sign(request_id, offer, expected_revision, access_check=access_check)
        self._remember_promises(ledger,payload)
        if ledger._cash is not None:
            ledger._cash.add_contract(offer, "sign:" + request_id, obligation_id=ledger.contract_cash_id(offer.player_id))
            payload["cash_components"] = True
            payload["cash_posting"] = ledger.cash_snapshot()
        payload["posting"] = ledger.financial_snapshot()
        payload["contract_charges"] = [json_amount(value) for value in receipt.charges]
        if ledger._generation_calendar_anchor is not None:
            payload.update(calendar_format=1,calendar_posting=self._calendar_posting(ledger))
        serialized = json.dumps(payload, allow_nan=False)
        db.execute("INSERT INTO ownership VALUES (?, ?)", (offer.player_id, team_id))
        db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'sign', ?)", (team_id, "sign:" + request_id, serialized))
        if proposal_request_id is not None:
            access_check()  # Shutdown here rolls back ownership, cash, story and cap together.
        return receipt

    @staticmethod
    def _has_amendment_history(ledger):
        return any(a.prior_restructures for a in ledger.generation_agreements())

    @staticmethod
    def _has_new_generations(ledger):
        return any(a.identity.generation_id.startswith('contract-gen:') for a in ledger.generation_agreements())

    @staticmethod
    def _return_scope(data):
        from datetime import date
        from franchise.returns import PreseasonReturnScope
        if type(data) is not dict or set(data)!={'league_year','signed_on','first_regular_season_game','healthy','exclusions','source'}:
            raise ValueError('Complete sourced return scope required')
        values=dict(data)
        values['exclusions']=FranchiseStore._scope_exclusions(values['exclusions'])
        for name in ('signed_on','first_regular_season_game'):
            if type(values[name]) is not str:
                raise ValueError('Canonical return dates required')
            parsed=date.fromisoformat(values[name])
            if parsed.isoformat()!=values[name]:
                raise ValueError('Canonical return dates required')
            values[name]=parsed
        return PreseasonReturnScope(**values)

    def preview_return(self,team_id,offer,expected_revision,*,scope):
        with self._connection() as db:
            if db.execute('PRAGMA user_version').fetchone()[0]!=4:
                raise Rejected('Return signing requires explicit format4 migration')
            ledger=self._load(db,team_id)
            if db.execute('SELECT 1 FROM ownership WHERE player_id=?',(offer.player_id,)).fetchone():
                raise Rejected('Player already belongs to a team')
            return ledger.preview_return(offer,expected_revision,scope=scope)

    def return_sign(self,team_id,request_id,offer,expected_revision,*,scope,access_check,story=None):
        from franchise.returns import PreseasonReturnScope
        if (type(request_id) is not str or not request_id.strip() or not isinstance(offer,Offer)
                or not isinstance(scope,PreseasonReturnScope) or not callable(access_check)
                or type(expected_revision) is not int or expected_revision<0):
            raise ValueError('Typed sourced return signing required')
        self._validate_story_evidence(story)
        if story is not None:
            if (story.get('request_id')!=request_id or story.get('offer')!=offer.to_dict()
                    or story.get('action')!='accept' or story.get('outcome')!='signed'):
                raise ValueError('Return story must describe the sourced signed agreement')
        scope_data=asdict(scope)
        scope_data.update(signed_on=scope.signed_on.isoformat(),
            first_regular_season_game=scope.first_regular_season_game.isoformat(),exclusions=sorted(scope.exclusions))
        requested={'format':1,'request_id':request_id,'offer':offer.to_dict(),
            'scope':scope_data,'expected_revision':expected_revision}
        if story is not None:
            if story.get('return_scope') != scope_data:
                raise ValueError('Return story scope disagrees with sourced agreement')
            requested['story']=json.loads(json.dumps(story,allow_nan=False))
        with self._connection(write=True) as db:
            if db.execute('PRAGMA user_version').fetchone()[0]!=4:
                raise Rejected('Return signing requires explicit format4 migration')
            ledger=self._load(db,team_id)
            key='sign:'+request_id
            row=db.execute('SELECT kind,payload FROM events WHERE team_id=? AND request_key=?',(team_id,key)).fetchone()
            if row:
                previous=json.loads(row[1])
                if ('story' in previous)!=('story' in requested):
                    raise Rejected('Return signing request mode already recorded differently')
                if row[0]!='return_sign' or any(self._checkpoint_hash(previous[field])!=self._checkpoint_hash(value)
                        for field,value in requested.items() if field!='expected_revision'):
                    raise Rejected('Return signing request already recorded differently')
                access_check()
                return ledger.return_sign(request_id,offer,expected_revision,scope=scope)
            if db.execute('SELECT 1 FROM events WHERE team_id=? AND request_key=?',(team_id,'dialogue:'+request_id)).fetchone():
                raise Rejected('Request already belongs to a recorded negotiation')
            if db.execute('SELECT 1 FROM ownership WHERE player_id=?',(offer.player_id,)).fetchone():
                raise Rejected('Player already belongs to a team')
            if story is not None:
                self._check_history(db,team_id,offer.player_id,story)
            receipt=ledger.return_sign(request_id,offer,expected_revision,scope=scope)
            if story is not None:
                self._remember_promises(ledger,requested)
            self._check_cash_components(ledger)
            payload={**requested,'generation_id':ledger.contract_identity(offer.player_id).generation_id,
                'posting':ledger.financial_snapshot(),'cash_posting':ledger.cash_snapshot(),
                'contract_charges':[json_amount(v) for v in receipt.charges],
                'generation_posting':ledger.generation_snapshot()}
            access_check()
            db.execute('INSERT INTO ownership VALUES (?,?)',(offer.player_id,team_id))
            db.execute('INSERT INTO events (team_id,request_key,kind,payload) VALUES (?,?,?,?)',
                (team_id,key,'return_sign',json.dumps(payload,allow_nan=False)))
            return receipt

    def update_budget(self, team_id: str, *, cap: int, roster_reserve: int, expected_revision: int):
        payload = dict(cap=cap, roster_reserve=roster_reserve, expected_revision=expected_revision)
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            ledger.update_budget(**payload)
            if ledger.revision != expected_revision:
                payload["posting"] = ledger.financial_snapshot()
                db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'budget', ?)", (team_id, f"budget:{expected_revision}", json.dumps(payload)))

    def stories(self, team_id: str) -> list[dict]:
        with self._connection() as db:
            self._load(db, team_id)  # Validate financial reconstruction first.
            return [payload.get("story") for (text,) in db.execute("SELECT payload FROM events WHERE team_id=? AND kind IN ('sign','return_sign') ORDER BY id", (team_id,))
                    if (payload := json.loads(text)).get("story") is not None]

    @staticmethod
    def _validate_actor(actor):
        from franchise.negotiation import validate_performance
        if type(actor) is not dict or set(actor) != {"personality", "relationships"}:
            raise ValueError("Personality and relationships required")
        if any(type(value) is not dict for value in actor.values()):
            raise ValueError("Actor fields must be JSON objects")
        validate_performance(actor)
        json.dumps(actor, allow_nan=False)

    def bind_actor(self, team_id, player_id, personality, relationships, *, access_check):
        actor = {"personality": personality, "relationships": relationships}
        self._validate_actor(actor)
        actor = json.loads(json.dumps(actor, allow_nan=False))
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            ledger.negotiation_context(player_id)
            access_check()
            key = "actor:" + player_id
            row = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, key)).fetchone()
            if row:
                return ledger._actors[player_id]
            origin = self._franchise_origin(db)
            if origin is not None:
                from franchise.initialization import initial_actor
                actor = initial_actor(origin['seed'],player_id)
            # Player priorities follow the player across clubs; relationships
            # remain team-specific. The write lock serializes first registration.
            existing = db.execute("SELECT payload FROM events WHERE kind='actor' AND request_key=? ORDER BY id LIMIT 1", (key,)).fetchone()
            if existing:
                actor["personality"] = json.loads(existing[0])["actor"]["personality"]
            payload = {"player_id": player_id, "actor": actor, "posting": ledger.financial_snapshot()}
            db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'actor', ?)",
                       (team_id, key, json.dumps(payload, allow_nan=False)))
            return actor

    @staticmethod
    def _apply_relationship(actor, key, delta):
        if actor is None or type(key) is not str or key not in actor["relationships"]:
            raise Rejected("Known actor relationship required")
        score = actor["relationships"][key]
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("Relationship score must be within zero and one")
        if type(delta) not in (int, float) or not math.isfinite(delta) or delta == 0 or abs(delta) > 0.1:
            raise ValueError("Relationship change must be nonzero and at most 0.1")
        actor["relationships"][key] = round(max(0, min(1, score + delta)), 6)

    @staticmethod
    def _relationship_source(db, team, player, request, *, before_revision, before_event_id=None):
        for event_id, kind, serialized in db.execute("SELECT id,kind,payload FROM events WHERE team_id=? AND request_key IN (?, ?, ?)",
                (team, "sign:" + request, "dialogue:" + request, "promise-score:" + request)):
            if before_event_id is not None and event_id >= before_event_id:
                continue
            data = json.loads(serialized)
            if kind == 'promise_score':
                result = data['result']
                if (result['player_id'] == player and result['score']['final_achievement_score'] is not None
                        and data['posting']['revision'] <= before_revision):
                    return
                continue
            event = data.get("story") if kind in ("sign","return_sign") else data["event"]
            if event is not None and event["offer"]["player_id"] == player and data["posting"]["revision"] <= before_revision:
                return
        raise Rejected("Recorded negotiation consequence required")

    def negotiation_inputs(self, team, player):
        with self._connection() as db:
            ledger = self._load(db, team)
            if player not in ledger._actors:
                raise Rejected("Registered actor required")
            return ledger._actors[player], {**ledger.negotiation_context(player),
                                           "current_contract_owned": db.execute("SELECT 1 FROM ownership WHERE player_id=?", (player,)).fetchone() is not None}

    def update_relationship(self, team, request_id, player, relationship, delta, *, source_request_id, expected_revision):
        for value in (request_id, player, relationship, source_request_id):
            if type(value) is not str or not value.strip():
                raise ValueError("Stable relationship identities required")
        payload = dict(player_id=player, relationship=relationship, delta=delta, source_request_id=source_request_id)
        with self._connection(write=True) as db:
            ledger = self._load(db, team)
            key = "relationship:" + request_id
            prior = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team, key)).fetchone()
            if prior:
                previous = json.loads(prior[0])
                if any(previous[field] != payload[field] for field in payload):
                    raise Rejected("Relationship request already recorded differently")
                return previous["actor_after"]
            if type(expected_revision) is not int or expected_revision != ledger.revision:
                raise Rejected("Relationship change is based on stale franchise state")
            for (serialized,) in db.execute("SELECT payload FROM events WHERE team_id=? AND kind='relationship'", (team,)):
                previous = json.loads(serialized)
                if all(previous[field] == payload[field] for field in ("player_id", "relationship", "source_request_id")):
                    raise Rejected("Relationship consequence already applied")
            self._relationship_source(db, team, player, source_request_id, before_revision=ledger.revision)
            actor = ledger._actors.get(player)
            self._apply_relationship(actor, relationship, delta)
            ledger.revision += 1
            payload.update(actor_after=actor, posting=ledger.financial_snapshot())
            db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'relationship', ?)",
                       (team, key, json.dumps(payload, allow_nan=False)))
            return actor

    @staticmethod
    def _remember_promises(ledger,payload):
        story = payload['story']
        if story is None or not story.get('promise_goals'):
            return
        from franchise.promises import goals_from_list
        goals_from_list(story['promise_goals'])
        if story.get('action') != 'accept' or story.get('outcome') != 'signed' or story.get('counter_promises') is not None:
            raise ValueError('Signed acceptance of original promise terms required')
        ledger._promise_agreements[payload['request_id']] = {'player_id':payload['offer']['player_id'],
                                                          'goals':story['promise_goals']}

    @staticmethod
    def _compute_promise_score(ledger,payload):
        from franchise.promises import goals_from_list,GoalObservation,score_promises
        if type(payload.get('expected_revision')) is not int or payload['expected_revision'] != ledger.revision:
            raise Rejected('Promise observation used stale franchise state')
        agreement = ledger._promise_agreements.get(payload['agreement_request_id'])
        if agreement is None:
            raise Rejected('Committed promise agreement required')
        for previous in ledger._promise_scores:
            if previous['agreement_request_id'] == payload['agreement_request_id'] and previous['score']['final_achievement_score'] is not None:
                raise Rejected('Final promise score already recorded; corrections unsupported')
        if type(payload['source']) is not str or not payload['source'].strip():
            raise ValueError('Evaluation/period-closure provenance required')
        observations = payload['observations']
        fields = {'goal_id','window','value','source','coverage','context'}
        if type(observations) is not list or any(type(o) is not dict or set(o) not in (fields,fields | {'complete_window'}) for o in observations):
            raise ValueError('Complete observed goal records required')
        circumstances=None
        if 'format' in payload or 'circumstances' in payload:
            from franchise.promises import PromiseCircumstances,validate_circumstances
            if (type(payload.get('format')) is not int or payload['format']!=1
                    or type(payload.get('circumstances')) is not list):
                raise ValueError('Versioned sourced promise circumstances required')
            required={'request_id','agreement_request_id','observations','window_closed','expected_revision','source','format','circumstances'}
            if set(payload) not in (required,required|{'result','posting'}):
                raise ValueError('Unexpected versioned promise-score fields')
            circumstances=validate_circumstances(tuple(PromiseCircumstances.from_dict(item) for item in payload['circumstances']),
                player_id=agreement['player_id'],team_id=ledger._team_identity,
                windows={goal['window'] for goal in agreement['goals']})
        score = score_promises(goals_from_list(agreement['goals']),tuple(GoalObservation(**o) for o in observations),
                               window_closed=payload['window_closed'])
        return {'request_id':payload['request_id'],'agreement_request_id':payload['agreement_request_id'],
                'player_id':agreement['player_id'],'source':payload['source'],'score':score,
                **({'circumstances':[item.to_dict() for item in circumstances]} if circumstances is not None else {})}

    def record_promise_performance(self,team_id,request_id,agreement_request_id,performance,*,window_closed,
                                   expected_revision,source,context,team_results=None,circumstances=None):
        from franchise.promises import goals_from_list,observe_promises,observe_promise_windows
        ledger = self.load_team(team_id)
        agreement = ledger._promise_agreements.get(agreement_request_id)
        if agreement is None:
            raise Rejected('Committed promise agreement required')
        if circumstances is not None:
            from franchise.promises import validate_circumstances
            validate_circumstances(circumstances,player_id=agreement['player_id'],team_id=team_id,
                windows={goal['window'] for goal in agreement['goals']})
            from franchise.performance import PerformanceEvidence
            performances=performance if type(performance) is tuple else (performance,)
            if not performances or any(not isinstance(item,PerformanceEvidence) for item in performances):
                raise ValueError('Typed observed performance windows required')
            by_window={item.window:item for item in performances}
            if any(item.window not in by_window or item.mode!=by_window[item.window].mode
                    or by_window[item.window].player_id!=item.player_id or by_window[item.window].team_id!=item.team_id
                    for item in circumstances):
                raise ValueError('Circumstances disagree with observed performance player/team/window/mode')
        mapper = observe_promise_windows if type(performance) is tuple else observe_promises
        observations = mapper(goals_from_list(agreement['goals']),performance,
            player_id=agreement['player_id'],team_id=team_id,context=context,
            team_results=() if type(performance) is tuple and team_results is None else team_results)
        return self.record_promise_score(team_id,request_id,agreement_request_id,observations,
            window_closed=window_closed,expected_revision=expected_revision,source=source,circumstances=circumstances)

    def record_promise_score(self,team_id,request_id,agreement_request_id,observations,*,window_closed,expected_revision,source,circumstances=None):
        from dataclasses import asdict
        from franchise.promises import GoalObservation
        if any(type(v) is not str or not v.strip() for v in (request_id,agreement_request_id)):
            raise ValueError('Stable score and agreement identities required')
        if type(observations) is not tuple or any(not isinstance(o,GoalObservation) for o in observations):
            raise ValueError('Immutable typed observations required')
        payload = {'request_id':request_id,'agreement_request_id':agreement_request_id,
                   'observations':[{key:value for key,value in asdict(o).items() if key != 'complete_window' or value is not None} for o in observations],'window_closed':window_closed,
                   'expected_revision':expected_revision,'source':source}
        if circumstances is not None:
            from franchise.promises import PromiseCircumstances
            if type(circumstances) is not tuple or not circumstances or any(not isinstance(item,PromiseCircumstances) for item in circumstances):
                raise ValueError('Nonempty immutable promise circumstances required')
            payload.update(format=1,circumstances=[item.to_dict() for item in circumstances])
        with self._connection(write=True) as db:
            ledger = self._load(db,team_id)
            key = 'promise-score:' + request_id
            row = db.execute('SELECT payload FROM events WHERE team_id=? AND request_key=?',(team_id,key)).fetchone()
            if row:
                previous = json.loads(row[0])
                if ('format' in previous)!=('format' in payload) or any(self._checkpoint_hash(previous[field]) != self._checkpoint_hash(payload[field]) for field in payload):
                    raise Rejected('Score request already recorded differently')
                return previous['result']
            result = self._compute_promise_score(ledger,payload)
            ledger._promise_scores.append(result)
            ledger.revision += 1
            payload.update(result=result,posting=ledger.financial_snapshot())
            db.execute("INSERT INTO events (team_id,request_key,kind,payload) VALUES (?,?,'promise_score',?)",
                       (team_id,key,json.dumps(payload,allow_nan=False)))
            return result

    @staticmethod
    def _validate_story_evidence(story, *, efficiency_cache=None):
        if story is not None and 'return_scope' in story:
            FranchiseStore._return_scope(story['return_scope'])
        if story is not None and "promise_goals" in story:
            from franchise.promises import goals_from_list
            goals_from_list(story["promise_goals"])
            if story.get("counter_promises") is not None:
                goals_from_list(story["counter_promises"])
        if story is None or "evidence" not in story:
            return  # Existing/manual records carry no model evidence claim.
        from franchise.negotiation import validate_performance
        evidence = story["evidence"]
        fields = {"personality", "performance", "relationships", "financial_revision"}
        if type(evidence) is not dict or set(evidence) not in (fields, fields | {"observed_efficiency"},fields | {"return_scope"},fields | {"observed_efficiency","return_scope"}):
            raise ValueError("Complete model evidence snapshot required")
        if 'return_scope' in evidence:
            FranchiseStore._return_scope(evidence['return_scope'])
            if FranchiseStore._checkpoint_hash(evidence['return_scope']) != FranchiseStore._checkpoint_hash(story.get('return_scope')):
                raise ValueError('Return evidence scope disagrees with request')
        elif 'return_scope' in story:
            raise ValueError('Return model evidence requires sourced scope')
        if type(evidence["financial_revision"]) is not int or evidence["financial_revision"] < 0:
            raise ValueError("Evidence requires its observed financial revision")
        if any(type(evidence[field]) is not dict for field in ("personality", "performance", "relationships")):
            raise ValueError("Evidence context fields must be JSON objects")
        validate_performance(evidence)
        if "observed_efficiency" in evidence:
            from franchise.performance import PerformanceEvidence
            player = Offer.from_dict(story['offer']).player_id
            key = (player, json.dumps(evidence['performance'], sort_keys=True, allow_nan=False)) if efficiency_cache is not None else None
            expected = efficiency_cache.get(key) if efficiency_cache is not None else None
            if expected is None:
                performance = PerformanceEvidence.from_context(evidence["performance"])
                if performance.player_id != player:
                    raise ValueError("Observed efficiency belongs to another player")
                expected = json.dumps(performance.efficiency_context(), sort_keys=True, allow_nan=False)
            # Canonical JSON also rejects bool/int substitutions that Python
            # object equality would otherwise consider equal.
            actual = json.dumps(evidence["observed_efficiency"], sort_keys=True, allow_nan=False)
            if actual != expected:
                raise ValueError("Observed efficiency disagrees with source counters")
            if efficiency_cache is not None:
                efficiency_cache.clear()
                efficiency_cache[key] = expected
        json.dumps(evidence, allow_nan=False)

    @staticmethod
    def _validate_dialogue(event, *, efficiency_cache=None):
        FranchiseStore._validate_story_evidence(event, efficiency_cache=efficiency_cache)
        if 'contract_format' in event:
            from franchise.guest_contracts import guest_money_scale, guest_offer_encoding
            guest_money_scale(event['contract_format'])
            if event.get('decision_mode') != 'proposal':
                raise ValueError('Invalid guest proposal contract format')
            if FranchiseStore._checkpoint_hash(event.get('guest_offer')) != FranchiseStore._checkpoint_hash(
                    guest_offer_encoding(Offer.from_dict(event['offer']), contract_format=event['contract_format'])):
                raise ValueError('Guest offer encoding disagrees with proposal')
            counter = event.get('counter')
            expected_encoding = None
            if counter is not None:
                try:
                    expected_encoding = guest_offer_encoding(Offer.from_dict(counter), contract_format=event['contract_format'])
                except ValueError:
                    if event.get('counter_validation', {}).get('status') != 'ineligible':
                        raise ValueError('Unrepresentable guest counter cannot be eligible')
            if 'guest_counter' not in event or FranchiseStore._checkpoint_hash(event['guest_counter']) != FranchiseStore._checkpoint_hash(expected_encoding):
                raise ValueError('Guest counter encoding disagrees with proposal')
        elif 'guest_offer' in event or 'guest_counter' in event:
            raise ValueError('Guest encoding requires explicit contract format')
        if type(event) is not dict or event.get("outcome") not in {
                "counteroffer", "player_rejected", "accounting_rejected", "accepted_proposal"}:
            raise ValueError("Noncommitted negotiation event required")
        if type(event.get("request_id")) is not str or not event["request_id"].strip():
            raise ValueError("Negotiation request ID required")
        from franchise.negotiation import Decision
        data = event["offer"]
        Offer.from_dict(data)
        counter = event.get("counter")
        decision = Decision.parse(json.dumps({"action": event["action"], "reason": event["reason"],
            "salaries": counter["salaries"] if counter else None,
            "signing_bonus": counter["signing_bonus"] if counter else None,
            "guaranteed_salaries": counter.get("guaranteed_salaries") if counter else None,
            **({"promise_goals": event["counter_promises"] if counter else None} if "counter_promises" in event else {})}), data["player_id"])
        expected = {"counter": "counteroffer", "reject": "player_rejected", "accept": "accounting_rejected"}
        if event['outcome'] == 'accepted_proposal':
            if (event.get('decision_mode') != 'proposal' or 'evidence' not in event
                    or type(event.get('proposal_preview')) is not dict or 'return_scope' in event
                    or type(event['proposal_preview'].get('revision')) is not int
                    or event['proposal_preview']['revision'] != event['evidence']['financial_revision']
                    or 'charges' in event):
                raise ValueError('Noncommitting proposal evidence required')
            expected['accept'] = 'accepted_proposal'
        if event["outcome"] != expected[decision.action] or (counter and counter["player_id"] != data["player_id"]):
            raise ValueError("Dialogue decision and outcome disagree")

    @staticmethod
    def _check_history(db, team_id, player_id, event):
        expected = event.get("history_request_ids")
        if expected is None:  # Historical/manual callers without model context.
            return
        if type(expected) is not list or any(type(key) is not str for key in expected):
            raise ValueError("Invalid negotiation history revision")
        actual = []
        for kind, serialized in db.execute("SELECT kind, payload FROM events WHERE team_id=? AND kind IN ('sign', 'return_sign', 'dialogue') ORDER BY id", (team_id,)):
            payload = json.loads(serialized)
            previous = payload["event"] if kind == "dialogue" else payload.get("story")
            if previous is not None and previous["offer"]["player_id"] == player_id:
                actual.append(previous["request_id"])
        if actual != expected:
            raise Rejected("Response was based on stale negotiation history")

    def record_negotiation(self, team_id, event, *, access_check):
        self._validate_dialogue(event)
        event = json.loads(json.dumps(event, allow_nan=False))
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            access_check()
            key = "dialogue:" + event["request_id"]
            if db.execute("SELECT 1 FROM events WHERE team_id=? AND request_key=?",
                          (team_id, "sign:" + event["request_id"])).fetchone():
                raise Rejected("Request already belongs to a signing")
            prior = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, key)).fetchone()
            if prior:
                recorded = json.loads(prior[0])["event"]
                if recorded != event:
                    raise Rejected("Negotiation request already recorded differently")
                return recorded
            if event.get("evidence") is not None and event["outcome"] != "accounting_rejected":
                if event["evidence"]["financial_revision"] != ledger.revision:
                    raise Rejected("Response was based on stale franchise context")
            if event['outcome'] == 'accepted_proposal':
                offer = Offer.from_dict(event['offer'])
                if db.execute('SELECT 1 FROM ownership WHERE player_id=?', (offer.player_id,)).fetchone():
                    raise Rejected('Player already belongs to a team')
                self._check_draft_right(db, team_id, offer.player_id)
                preview = ledger.preview_offer(offer, event['evidence']['financial_revision'])
                if self._checkpoint_hash(preview) != self._checkpoint_hash(event['proposal_preview']):
                    raise Rejected('Accepted proposal preview changed before recording')
            self._check_history(db, team_id, event["offer"]["player_id"], event)
            payload = {"event": event, "posting": ledger.financial_snapshot()}
            if 'return_scope' in event or event['outcome'] == 'accepted_proposal':
                access_check()
            db.execute("INSERT INTO events (team_id, request_key, kind, payload) VALUES (?, ?, 'dialogue', ?)",
                       (team_id, key, json.dumps(payload, allow_nan=False)))
            return event

    @staticmethod
    def _draft_order(db, draft_id):
        from franchise.draft_order import DraftOrder
        row = db.execute("SELECT config FROM draft_orders WHERE id=?", (draft_id,)).fetchone()
        if row is None:
            raise Rejected('Unknown draft')
        return DraftOrder.from_dict(json.loads(row[0]))

    def initialize_draft(self, order):
        from franchise.draft_order import DraftOrder
        if not isinstance(order, DraftOrder):
            raise ValueError('Typed source draft order required')
        config = json.dumps(order.to_dict(), sort_keys=True)
        with self._connection(write=True) as db:
            previous = db.execute("SELECT config FROM draft_orders WHERE id=?", (order.draft_id,)).fetchone()
            if previous:
                if previous[0] != config:
                    raise Rejected('Draft order cannot be overwritten')
                return
            for (existing,) in db.execute("SELECT config FROM draft_orders"):
                if order.player_ids & DraftOrder.from_dict(json.loads(existing)).player_ids:
                    raise Rejected('Prospect class overlaps another declared draft')
            registered = set()
            for team in {slot.team_id for slot in order.slots}:
                ledger = self._load(db, team)
                registered.update(ledger._rookies)
                if ledger._rookie_pool_opening and ledger._rookie_pool_opening.league_year != order.league_year:
                    raise ValueError('Draft and rookie allocation years disagree')
            if not order.player_ids <= registered:
                raise ValueError('Draft class contains unregistered prospects')
            if any(db.execute("SELECT 1 FROM ownership WHERE player_id=?", (player,)).fetchone() for player in order.player_ids):
                raise Rejected('Draft class includes contracted players')
            db.execute("INSERT INTO draft_orders VALUES (?,?,?)", (order.draft_id, order.league_year, config))

    @staticmethod
    def _check_draft_right(db, team, player, *, allow_unpicked=False):
        row = db.execute("SELECT team_id FROM draft_picks WHERE player_id=?", (player,)).fetchone()
        if row and row[0] != team:
            raise Rejected('Another team holds draft signing rights')
        if row is None and not allow_unpicked:
            from franchise.draft_order import DraftOrder
            for (config,) in db.execute("SELECT config FROM draft_orders"):
                if player in DraftOrder.from_dict(json.loads(config)).player_ids:
                    raise Rejected('Draft prospect has not been selected')

    @staticmethod
    def _draft_fund_pick(ledger, offer, revision, source):
        existing = ledger._draft_reservations.get(offer.player_id)
        if existing:
            if existing != (offer, source) or type(revision) is not int or ledger.revision != revision:
                raise Rejected('Pick funding differs from reserved estimate')
            ledger._validate_offer(offer, revision)
            ledger.revision += 1
        else:
            ledger.reserve_draft_funding(offer, revision, source=source)

    @staticmethod
    def _validate_pick_decision(ledger,payload):
        mode = payload['decision_mode']
        if mode == 'manual':
            if payload['scouting_request_id'] is not None:
                raise ValueError('Manual pick cannot claim an AI scouting decision')
            return
        if mode != 'ai' or not ledger._scouting:
            raise ValueError('Explicit decision mode and recorded AI advice required')
        advice = ledger._scouting[-1]
        if (advice['request_id'] != payload['scouting_request_id'] or advice['decision']['action'] != 'recommend'
                or advice['decision']['player_id'] != payload['player_id']
                or advice['evidence']['overall_pick'] != payload['overall_pick']
                or advice['evidence']['draft_round'] != payload['draft_round']
                or advice['evidence']['financial_revision'] != payload['expected_revision']):
            raise Rejected('Pick is not based on the latest matching scouting decision')
        estimate = next(item['contract_estimate'] for item in advice['evidence']['prospects'] if item['player_id'] == payload['player_id'])
        if estimate != payload['offer']:
            raise Rejected('Pick funding differs from scouted contract estimate')

    def _validate_pick_personalities(self, db, ledger, payload, *, before_event=None):
        if payload['decision_mode'] != 'ai':
            return
        for prospect in ledger._scouting[-1]['evidence']['prospects']:
            ledger.validate_scouting_personality(prospect['player_id'],prospect['personality'])
            self._validate_prior_personality(db,prospect['player_id'],prospect['personality'],before_event=before_event)

    def commit_draft_pick(self, team_id, request_id, draft_id, overall_pick, offer, expected_revision,
                          *, funding_source, access_check, decision_mode, scouting_request_id=None):
        if type(request_id) is not str or not request_id.strip() or type(overall_pick) is not int or overall_pick < 1:
            raise ValueError('Stable pick request and overall pick required')
        payload = {"draft_id": draft_id, "overall_pick": overall_pick, "player_id": offer.player_id,
                   "offer": offer.to_dict(), "expected_revision": expected_revision, "funding_source": funding_source,
                   "decision_mode": decision_mode, "scouting_request_id": scouting_request_id}
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            key = 'draft-pick:' + request_id
            row = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id,key)).fetchone()
            if row:
                previous = json.loads(row[0])
                if any(previous[field] != payload[field] for field in payload):
                    raise Rejected('Draft request already recorded differently')
                access_check()
                return previous['posting']
            order = self._draft_order(db, draft_id)
            picks = list(db.execute("SELECT overall_pick,team_id FROM draft_picks WHERE draft_id=? ORDER BY overall_pick", (draft_id,)))
            if [pick for pick,_ in picks] != list(range(1,len(picks)+1)) or any(order.slots[pick-1].team_id != team for pick,team in picks):
                raise ValueError('Draft pick index disagrees with declared order')
            for previous_team in {team for _,team in picks}:
                self._load(db,previous_team)
            count = len(picks)
            if overall_pick != count + 1 or overall_pick > len(order.slots):
                raise Rejected('Pick is out of declared draft order')
            slot = order.slots[overall_pick-1]
            if slot.team_id != team_id or offer.player_id not in order.player_ids:
                raise Rejected('Wrong team or prospect for declared pick')
            scale = ledger._rookies.get(offer.player_id)
            if getattr(scale,'draft_round',None) != slot.draft_round:
                raise Rejected('Prospect lacks matching draft-slot contract classification')
            if db.execute("SELECT 1 FROM draft_picks WHERE player_id=?", (offer.player_id,)).fetchone() or db.execute("SELECT 1 FROM ownership WHERE player_id=?", (offer.player_id,)).fetchone():
                raise Rejected('Prospect already selected or contracted')
            payload["draft_round"] = slot.draft_round
            self._validate_pick_decision(ledger,payload)
            self._validate_pick_personalities(db,ledger,payload)
            self._draft_fund_pick(ledger,offer,expected_revision,funding_source)
            ledger._draft_rights[offer.player_id] = {'draft_id':order.draft_id,'league_year':order.league_year,
                'overall_pick':overall_pick,'draft_round':slot.draft_round}
            payload.update(draft_round=slot.draft_round,order_source=order.source,posting=ledger.financial_snapshot())
            access_check()
            db.execute("INSERT INTO draft_picks VALUES (?,?,?,?)", (draft_id,overall_pick,offer.player_id,team_id))
            db.execute("INSERT INTO events (team_id,request_key,kind,payload) VALUES (?,?,'draft_pick',?)",
                       (team_id,key,json.dumps(payload,allow_nan=False)))
            return payload['posting']

    def reserve_draft_funding(self, team_id, request_id, offer, expected_revision, *, source, access_check):
        if type(request_id) is not str or not request_id.strip():
            raise ValueError('Stable funding request ID required')
        payload = {"offer": offer.to_dict(), "expected_revision": expected_revision, "source": source}
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            key = "draft-reserve:" + request_id
            row = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, key)).fetchone()
            if row:
                previous = json.loads(row[0])
                if any(previous[field] != payload[field] for field in payload):
                    raise Rejected('Funding request already recorded differently')
                access_check()
                return previous["posting"]
            if db.execute("SELECT 1 FROM ownership WHERE player_id=?", (offer.player_id,)).fetchone():
                raise Rejected('Player already belongs to a team')
            self._check_draft_right(db, team_id, offer.player_id, allow_unpicked=True)
            ledger.reserve_draft_funding(offer, expected_revision, source=source)
            access_check()
            payload["posting"] = ledger.financial_snapshot()
            db.execute("INSERT INTO events (team_id,request_key,kind,payload) VALUES (?,?,'draft_reserve',?)",
                       (team_id, key, json.dumps(payload, allow_nan=False)))
            return payload["posting"]

    def withdraw_draft_funding(self, team_id, request_id, player_id, expected_revision, *, source):
        if type(request_id) is not str or not request_id.strip():
            raise ValueError('Stable withdrawal request ID required')
        payload = {"player_id": player_id, "expected_revision": expected_revision, "source": source}
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            key = "draft-withdraw:" + request_id
            row = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, key)).fetchone()
            if row:
                previous = json.loads(row[0])
                if any(previous[field] != payload[field] for field in payload):
                    raise Rejected('Withdrawal request already recorded differently')
                return previous["posting"]
            if db.execute("SELECT 1 FROM draft_picks WHERE player_id=? AND team_id=?", (player_id,team_id)).fetchone():
                raise Rejected('Selected prospect funding must remain reserved until signing')
            ledger.withdraw_draft_funding(player_id, expected_revision, source=source)
            payload["posting"] = ledger.financial_snapshot()
            db.execute("INSERT INTO events (team_id,request_key,kind,payload) VALUES (?,?,'draft_withdraw',?)",
                       (team_id, key, json.dumps(payload, allow_nan=False)))
            return payload["posting"]

    @staticmethod
    def _validate_prior_personality(db, player_id, personality, *, before_event=None):
        row=db.execute("SELECT payload FROM events WHERE kind='actor' AND request_key=? AND (? IS NULL OR id < ?) ORDER BY id LIMIT 1",
                       ('actor:'+player_id,before_event,before_event)).fetchone()
        if row:
            actor=json.loads(row[0])['actor']
            FranchiseStore._validate_actor(actor)
            if personality != actor['personality']:
                raise Rejected('Scouting personality differs from saved cross-team player personality')

    def validate_scouting_personality(self, team_id, player_id, personality):
        with self._connection() as db:
            self._load(db,team_id).validate_scouting_personality(player_id,personality)
            self._validate_prior_personality(db,player_id,personality)

    def record_scouting(self, team_id, event, *, access_check):
        from franchise.draft import validate_scouting
        event = json.loads(json.dumps(event, allow_nan=False))
        with self._connection(write=True) as db:
            ledger = self._load(db, team_id)
            key = "draft-scouting:" + event["request_id"]
            row = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, key)).fetchone()
            if row:
                previous = json.loads(row[0])["event"]
                if previous != event:
                    raise Rejected("Scouting request already recorded differently")
                access_check()
                return previous
            validate_scouting(event, ledger)
            for prospect in event['evidence']['prospects']:
                self._validate_prior_personality(db,prospect['player_id'],prospect['personality'])
            access_check()  # Required inside the final durable transaction.
            payload = {"event": event, "posting": ledger.financial_snapshot()}
            db.execute("INSERT INTO events (team_id,request_key,kind,payload) VALUES (?,?,'draft_scouting',?)",
                       (team_id, key, json.dumps(payload, allow_nan=False)))
            return event

    def recalled_scouting(self, team_id, request_id):
        with self._connection() as db:
            self._load(db, team_id)
            row = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?",
                             (team_id, "draft-scouting:" + request_id)).fetchone()
            return json.loads(row[0])["event"] if row else None

    @staticmethod
    def _negotiation_history(db,team_id,player_id):
        history=[]
        for kind,serialized in db.execute("SELECT kind,payload FROM events WHERE team_id=? AND kind IN ('dialogue','sign','return_sign') ORDER BY id",(team_id,)):
            payload=json.loads(serialized)
            if kind == 'dialogue':
                event=payload['event']
            elif payload.get('story') is not None:
                event={**payload['story'],'charges':payload['contract_charges']}
            else:
                continue
            if event['offer']['player_id'] == player_id:
                history.append(event)
        return history

    def negotiation_history(self, team_id, player_id):
        with self._connection() as db:
            self._load(db,team_id)
            return self._negotiation_history(db,team_id,player_id)

    def recalled_negotiation(self, team_id: str, request_id: str, offer: Offer):
        with self._connection() as db:
            ledger = self._load(db, team_id)
            row = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?", (team_id, "sign:" + request_id)).fetchone()
            if row is None:
                dialogue = db.execute("SELECT payload FROM events WHERE team_id=? AND request_key=?",
                                      (team_id, "dialogue:" + request_id)).fetchone()
                if dialogue is None:
                    return None
                event = json.loads(dialogue[0])["event"]
                if event["offer"] != json.loads(json.dumps(offer.to_dict())):
                    raise Rejected("Negotiation request already recorded with different terms")
                return event
            payload = json.loads(row[0])
            if payload["offer"] != json.loads(json.dumps(offer.to_dict())):
                raise Rejected("Negotiation request already committed with different terms")
            if payload.get("story") is None:
                raise Rejected("Request belongs to a signing without negotiation history")
            return {**payload["story"], "charges": payload["contract_charges"]}


class StoredLedger:
    """Negotiation-facing view; every operation reads current durable state."""
    def __init__(self, store: FranchiseStore, team_id: str, *, return_scope=None):
        self.store, self.team_id = store, team_id
        if return_scope is not None:
            from franchise.returns import PreseasonReturnScope
            if not isinstance(return_scope,PreseasonReturnScope):
                raise ValueError('Typed return scope required')
        self.return_scope=return_scope
        store.load_team(team_id)

    def scouting_history(self):
        return self.store.load_team(self.team_id).scouting_history()

    def validate_scouting_personality(self, player_id, personality):
        self.store.validate_scouting_personality(self.team_id, player_id, personality)

    def recalled_scouting(self, request_id):
        return self.store.recalled_scouting(self.team_id, request_id)

    def record_scouting(self, event, *, access_check):
        return self.store.record_scouting(self.team_id, event, access_check=access_check)

    def management_context(self):
        return self.store.load_team(self.team_id).management_context()

    def return_scope_context(self):
        if self.return_scope is None:
            return None
        scope=self.return_scope
        return {'league_year':scope.league_year,'signed_on':scope.signed_on.isoformat(),
            'first_regular_season_game':scope.first_regular_season_game.isoformat(),
            'healthy':scope.healthy,'exclusions':sorted(scope.exclusions),'source':scope.source}

    def negotiation_context(self, player_id):
        return self.store.load_team(self.team_id).negotiation_context(player_id)

    def preview_draft_offer(self, offer, expected_revision):
        return self.store.preview_draft_offer(self.team_id, offer, expected_revision)

    def preview_offer(self, offer, expected_revision):
        if self.return_scope is not None:
            return self.store.preview_return(self.team_id,offer,expected_revision,scope=self.return_scope)
        return self.store.preview_offer(self.team_id, offer, expected_revision)

    def commit_negotiation(self, request_id, offer, expected_revision, *, access_check, story):
        if self.return_scope is not None:
            return self.store.return_sign(self.team_id,request_id,offer,expected_revision,scope=self.return_scope,
                access_check=access_check,story=story)
        return self.store.sign(self.team_id, request_id, offer, expected_revision,
                               access_check=access_check, story=story)

    def bind_actor(self, player_id, personality, relationships, *, access_check):
        return self.store.bind_actor(self.team_id, player_id, personality, relationships,
                                     access_check=access_check)

    def negotiation_inputs(self, player_id, actor):
        return self.store.negotiation_inputs(self.team_id, player_id)

    def record_negotiation(self, event, *, access_check):
        return self.store.record_negotiation(self.team_id, event, access_check=access_check)

    def negotiation_history(self, player_id):
        return self.store.negotiation_history(self.team_id, player_id)

    def recalled_negotiation(self, request_id, offer):
        result=self.store.recalled_negotiation(self.team_id,request_id,offer)
        if self.return_scope is not None and result is not None and result.get('decision_mode') == 'manual':
            raise Rejected('Return negotiation request already recorded in manual mode')
        if result is not None and self.store._checkpoint_hash(result.get('return_scope'))!=self.store._checkpoint_hash(self.return_scope_context()):
            raise Rejected('Negotiation request already recorded with different return scope or mode')
        return result

    @property
    def room(self):
        return self.store.load_team(self.team_id).room
