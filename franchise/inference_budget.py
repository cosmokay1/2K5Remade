"""Durable attempt and conservative token-reservation ceilings, not billing.

Every reserved attempt consumes capacity, including provider failures and a
process crash before completion. Token allowances are never refunded.
No prompt, response or credentials are stored.
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
    def __init__(self,path,*,scope,request_limit,token_limit=None):
        limit=request_limit
        if type(scope) is not str or not scope.strip():
            raise ValueError('Explicit franchise/season budget scope required')
        if type(limit) is not int or limit<=0 or limit>2**63-1:
            raise ValueError('Positive integer inference request ceiling required')
        if token_limit is not None and (type(token_limit) is not int or not 0<token_limit<=2**63-1):
            raise ValueError('Positive integer cumulative token ceiling required')
        if not isinstance(path,(str,Path)) or not str(path).strip() or str(path)==':memory:':
            raise ValueError('Explicit persistent inference-budget file required')
        self.path=Path(path).absolute();self.scope=scope;self.request_limit=limit
        self.token_limit=token_limit
        with self._connection(write=True) as db:
            db.execute("CREATE TABLE IF NOT EXISTS policies(scope TEXT PRIMARY KEY, request_limit INTEGER NOT NULL CHECK(typeof(request_limit)='integer' AND request_limit>0))")
            db.execute("CREATE TABLE IF NOT EXISTS attempts(reservation_id TEXT PRIMARY KEY, scope TEXT NOT NULL REFERENCES policies(scope), model TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0,1)), outcome TEXT, prompt_token_count INTEGER, candidates_token_count INTEGER, total_token_count INTEGER, cached_content_token_count INTEGER, thoughts_token_count INTEGER, tool_use_prompt_token_count INTEGER)")
            db.execute("CREATE TABLE IF NOT EXISTS token_policies(scope TEXT PRIMARY KEY REFERENCES policies(scope), token_limit INTEGER NOT NULL CHECK(typeof(token_limit)='integer' AND token_limit>0))")
            db.execute("CREATE TABLE IF NOT EXISTS token_reservations(reservation_id TEXT PRIMARY KEY REFERENCES attempts(reservation_id), input_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL)")
            row=db.execute('SELECT request_limit FROM policies WHERE scope=?',(scope,)).fetchone()
            if row is None:
                if db.execute('SELECT 1 FROM attempts WHERE scope=? LIMIT 1',(scope,)).fetchone():
                    raise ValueError('Persisted attempts lack their immutable budget policy')
                db.execute('INSERT INTO policies VALUES(?,?)',(scope,limit))
            token_policy=db.execute('SELECT token_limit FROM token_policies WHERE scope=?',(scope,)).fetchone()
            if token_policy is None and token_limit is not None:
                if db.execute('SELECT 1 FROM attempts WHERE scope=? LIMIT 1',(scope,)).fetchone():
                    raise ValueError('Cannot add token policy to a scope with existing attempts')
                db.execute('INSERT INTO token_policies VALUES(?,?)',(scope,token_limit))
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
        if db.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('Persisted inference records have missing policy or attempt references')
        row=db.execute('SELECT request_limit FROM policies WHERE scope=?',(self.scope,)).fetchone()
        if row is None or type(row[0]) is not int or row[0]!=self.request_limit:
            raise ValueError('Persisted request ceiling differs from the declared immutable policy')
        rows=self._attempt_rows(db)
        if len(rows)>self.request_limit:
            raise ValueError('Persisted inference attempts exceed their policy')
        self._check_tokens(db,rows)
        return rows

    def _check_tokens(self,db,rows):
        policy=db.execute('SELECT token_limit FROM token_policies WHERE scope=?',(self.scope,)).fetchone()
        reservations=db.execute('SELECT r.reservation_id,r.input_tokens,r.output_tokens FROM token_reservations r JOIN attempts a USING(reservation_id) WHERE a.scope=?',(self.scope,)).fetchall()
        if self.token_limit is None:
            if policy is not None or reservations:
                raise ValueError('Persisted token policy cannot be removed')
            return 0
        if policy is None or type(policy[0]) is not int or policy[0]!=self.token_limit:
            raise ValueError('Persisted token ceiling differs from declared immutable policy')
        if {r[0] for r in reservations}!={r[0] for r in rows}:
            raise ValueError('Every token-limited attempt requires its original reservation')
        usage={r[0]:dict(zip(TOKEN_FIELDS,r[4:])) for r in rows}
        total=0
        for identity,input_tokens,output_tokens in reservations:
            self._token_allowance(input_tokens,output_tokens)
            total+=input_tokens+output_tokens
            tokens=usage[identity]
            if ((tokens['prompt_token_count'] is not None and tokens['prompt_token_count']>input_tokens)
                or (tokens['total_token_count'] is not None and tokens['total_token_count']>input_tokens+output_tokens)
                or any(tokens[field] is not None and tokens[field]>output_tokens
                       for field in ('candidates_token_count','thoughts_token_count'))
                or (tokens['candidates_token_count'] is not None and tokens['thoughts_token_count'] is not None
                    and tokens['candidates_token_count']+tokens['thoughts_token_count']>output_tokens)):
                raise ValueError('Reported usage exceeds reserved token allowance')
        if total>self.token_limit:
            raise ValueError('Persisted token reservations exceed their policy')
        return total

    @staticmethod
    def _token_allowance(input_tokens,output_tokens):
        if (type(input_tokens) is not int or input_tokens<0 or type(output_tokens) is not int
            or output_tokens<=0 or input_tokens+output_tokens>2**63-1):
            raise ValueError('Explicit nonnegative input and positive output token allowance required')

    @staticmethod
    def _identity(value):
        if type(value) is not str:
            raise ValueError('Canonical UUID reservation identity required')
        try:parsed=UUID(value)
        except (ValueError,AttributeError):raise ValueError('Canonical UUID reservation identity required') from None
        if str(parsed)!=value:
            raise ValueError('Canonical UUID reservation identity required')
        return value

    def reserve(self,*,model,input_tokens=None,output_tokens=None):
        """Reserve once before each actual provider attempt; failures never refund."""
        if type(model) is not str or not model.strip():
            raise ValueError('Explicit inference model required')
        if self.token_limit is not None:
            self._token_allowance(input_tokens,output_tokens)
        elif input_tokens is not None or output_tokens is not None:
            raise ValueError('Token allowances require an explicit cumulative token policy')
        identity=str(uuid4())
        with self._connection(write=True) as db:
            rows=self._check_policy(db)
            if len(rows)>=self.request_limit:
                raise BudgetExceeded('Durable inference request ceiling reached')
            if self.token_limit is not None:
                total=self._check_tokens(db,rows)
                if total+input_tokens+output_tokens>self.token_limit:
                    raise BudgetExceeded('Durable inference token ceiling reached')
            db.execute('INSERT INTO attempts(reservation_id,scope,model) VALUES(?,?,?)',(identity,self.scope,model))
            if self.token_limit is not None:
                db.execute('INSERT INTO token_reservations VALUES(?,?,?)',(identity,input_tokens,output_tokens))
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
        # Persist an observed overrun as evidence, then deny returning a paid
        # decision and deny subsequent admission. Never erase its reservation.
        if self.token_limit is not None:
            self.status()

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
            status={'scope':self.scope,'request_limit':self.request_limit,'attempts':len(rows),'completed':completed,
                'pending':len(rows)-completed,'known_token_usage':dict(zip(TOKEN_FIELDS,known)),
                'unknown_usage_count':unknown}
            if self.token_limit is not None:
                reserved=self._check_tokens(db,rows)
                status.update(token_limit=self.token_limit,reserved_tokens=reserved,remaining_tokens=self.token_limit-reserved)
            return status
