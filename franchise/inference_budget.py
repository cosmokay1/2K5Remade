"""Durable inference-attempt ceilings, not a dollar-cost guarantee.

Every reserved attempt consumes capacity, including provider failures and a
process crash before completion. No prompt, response or credentials are stored.
"""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from uuid import UUID,uuid4


TOKEN_FIELDS=('prompt_token_count','candidates_token_count','total_token_count','cached_content_token_count',
    'thoughts_token_count','tool_use_prompt_token_count')
OUTCOMES=('response_accepted','response_rejected','request_failed')


class BudgetExceeded(RuntimeError):
    pass


class InferenceBudget:
    def __init__(self,path,*,scope,request_limit):
        limit=request_limit
        if type(scope) is not str or not scope.strip():
            raise ValueError('Explicit franchise/season budget scope required')
        if type(limit) is not int or limit<=0 or limit>2**63-1:
            raise ValueError('Positive integer inference request ceiling required')
        if not isinstance(path,(str,Path)) or not str(path).strip() or str(path)==':memory:':
            raise ValueError('Explicit persistent inference-budget file required')
        self.path=Path(path).absolute();self.scope=scope;self.request_limit=limit
        with self._connection(write=True) as db:
            db.execute("CREATE TABLE IF NOT EXISTS policies(scope TEXT PRIMARY KEY, request_limit INTEGER NOT NULL CHECK(typeof(request_limit)='integer' AND request_limit>0))")
            db.execute("CREATE TABLE IF NOT EXISTS attempts(reservation_id TEXT PRIMARY KEY, scope TEXT NOT NULL REFERENCES policies(scope), model TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0,1)), outcome TEXT, prompt_token_count INTEGER, candidates_token_count INTEGER, total_token_count INTEGER, cached_content_token_count INTEGER, thoughts_token_count INTEGER, tool_use_prompt_token_count INTEGER)")
            row=db.execute('SELECT request_limit FROM policies WHERE scope=?',(scope,)).fetchone()
            if row is None:
                if db.execute('SELECT 1 FROM attempts WHERE scope=? LIMIT 1',(scope,)).fetchone():
                    raise ValueError('Persisted attempts lack their immutable budget policy')
                db.execute('INSERT INTO policies VALUES(?,?)',(scope,limit))
            self._check_policy(db)

    @contextmanager
    def _connection(self,*,write=False):
        db=sqlite3.connect(self.path,timeout=30,isolation_level=None)
        try:
            db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            yield db
            db.commit()
        except BaseException:
            db.rollback();raise
        finally:
            db.close()

    def _check_policy(self,db):
        row=db.execute('SELECT request_limit FROM policies WHERE scope=?',(self.scope,)).fetchone()
        if row is None or type(row[0]) is not int or row[0]!=self.request_limit:
            raise ValueError('Persisted request ceiling differs from the declared immutable policy')
        rows=self._attempt_rows(db)
        if len(rows)>self.request_limit:
            raise ValueError('Persisted inference attempts exceed their policy')
        return rows

    @staticmethod
    def _identity(value):
        if type(value) is not str:
            raise ValueError('Canonical UUID reservation identity required')
        try:parsed=UUID(value)
        except (ValueError,AttributeError):raise ValueError('Canonical UUID reservation identity required') from None
        if str(parsed)!=value:
            raise ValueError('Canonical UUID reservation identity required')
        return value

    def reserve(self,*,model):
        """Reserve once before each actual provider attempt; failures never refund."""
        if type(model) is not str or not model.strip():
            raise ValueError('Explicit inference model required')
        identity=str(uuid4())
        with self._connection(write=True) as db:
            rows=self._check_policy(db)
            if len(rows)>=self.request_limit:
                raise BudgetExceeded('Durable inference request ceiling reached')
            db.execute('INSERT INTO attempts(reservation_id,scope,model) VALUES(?,?,?)',(identity,self.scope,model))
        return identity

    def complete(self,reservation_id,*,outcome,tokens):
        identity=self._identity(reservation_id)
        if type(outcome) is not str or outcome not in OUTCOMES:
            raise ValueError('Explicit inference completion outcome required')
        if tokens is None:tokens=dict.fromkeys(TOKEN_FIELDS)
        if type(tokens) is not dict or set(tokens)!=set(TOKEN_FIELDS):
            raise ValueError('Complete nullable provider token metadata required')
        usage=tuple(tokens[field] for field in TOKEN_FIELDS)
        if any(value is not None and (type(value) is not int or not 0<=value<=2**63-1) for value in usage):
            raise ValueError('Nullable nonnegative integer token metadata required')
        with self._connection(write=True) as db:
            self._check_policy(db)
            row=db.execute('SELECT completed,outcome,'+','.join(TOKEN_FIELDS)+' FROM attempts WHERE reservation_id=? AND scope=?',
                (identity,self.scope)).fetchone()
            if row is None:raise ValueError('Reservation does not belong to this budget scope')
            completion=(outcome,*usage)
            if row[0]==1:
                if row[1:]!=completion:raise ValueError('Inference completion was already recorded differently')
                return
            if row[0]!=0 or any(value is not None for value in row[1:]):
                raise ValueError('Invalid persisted pending completion state')
            db.execute('UPDATE attempts SET completed=1,outcome=?,'+','.join(field+'=?' for field in TOKEN_FIELDS)+' WHERE reservation_id=? AND scope=?',
                (*completion,identity,self.scope))

    def _attempt_rows(self,db):
        rows=db.execute('SELECT reservation_id,model,completed,outcome,'+','.join(TOKEN_FIELDS)+' FROM attempts WHERE scope=?',
            (self.scope,)).fetchall()
        for identity,model,done,outcome,*usage in rows:
            self._identity(identity)
            if type(model) is not str or not model.strip():raise ValueError('Invalid persisted inference model')
            if type(done) is not int or done not in (0,1) or (done==1 and outcome not in OUTCOMES):
                raise ValueError('Invalid persisted inference completion')
            if any(v is not None and (type(v) is not int or not 0<=v<=2**63-1) for v in usage):
                raise ValueError('Invalid persisted token metadata')
            if done==0 and (outcome is not None or any(v is not None for v in usage)):
                raise ValueError('Invalid persisted pending completion')
        return rows

    def status(self):
        """Known usage sums are partial; unknown count includes any missing field."""
        with self._connection() as db:
            rows=self._check_policy(db)
            completed=0;known=[0]*len(TOKEN_FIELDS);unknown=0
            for identity,model,done,outcome,*usage in rows:
                completed+=done;unknown+=any(v is None for v in usage)
                for index,value in enumerate(usage):
                    if value is not None:known[index]+=value
            return {'scope':self.scope,'request_limit':self.request_limit,'attempts':len(rows),'completed':completed,
                'pending':len(rows)-completed,'known_token_usage':dict(zip(TOKEN_FIELDS,known)),
                'unknown_usage_count':unknown}
