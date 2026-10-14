from contextlib import closing
import multiprocessing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from uuid import uuid4
from franchise.inference_budget import InferenceBudget,BudgetExceeded,TOKEN_FIELDS


def reserve_worker(path,gate,results):
    try:
        budget=InferenceBudget(path,scope='franchise/2028',request_limit=3)
        gate.wait(10);budget.reserve(model='synthetic-model');results.put('reserved')
    except BudgetExceeded:results.put('denied')
    except BaseException as error:results.put(type(error).__name__+':'+str(error))


class InferenceBudgetTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'inference.sqlite'

    def budget(self,**changes):
        return InferenceBudget(self.path,**{'scope':'franchise/2028','request_limit':3,**changes})

    def tokens(self,**changes):
        return {**dict.fromkeys(TOKEN_FIELDS),**changes}

    def test_restart_failures_and_pending_reservations_remain_counted(self):
        budget=self.budget();first=budget.reserve(model='synthetic-model')
        budget.complete(first,outcome='request_failed',tokens=None)
        budget.reserve(model='synthetic-model');third=self.budget().reserve(model='synthetic-model')
        with self.assertRaises(BudgetExceeded):self.budget().reserve(model='synthetic-model')
        tokens={field:0 for field in TOKEN_FIELDS};tokens.update(prompt_token_count=10,candidates_token_count=5,total_token_count=20)
        self.budget().complete(third,outcome='response_accepted',tokens=tokens)
        status=self.budget().status()
        self.assertEqual((status['attempts'],status['completed'],status['pending']),(3,2,1))
        self.assertEqual(status['known_token_usage'],tokens)
        self.assertEqual(status['unknown_usage_count'],2)
        for limit in (2,4):
            with self.assertRaises(ValueError):self.budget(request_limit=limit)
        self.assertEqual(self.budget().status(),status)

    def test_completion_retries_preserve_capacity_and_scope(self):
        budget=self.budget();identity=budget.reserve(model='synthetic-model')
        self.assertNotEqual(budget.reserve(model='synthetic-model'),identity)
        tokens=self.tokens(prompt_token_count=0)
        budget.complete(identity,outcome='response_rejected',tokens=tokens)
        before=self.path.read_bytes();budget.complete(identity,outcome='response_rejected',tokens=tokens)
        self.assertEqual(self.path.read_bytes(),before)
        with self.assertRaises(ValueError):budget.complete(identity,outcome='response_accepted',tokens=tokens)
        with self.assertRaises(ValueError):self.budget(scope='other/2028').complete(identity,outcome='request_failed',tokens=None)
        self.assertEqual(budget.status()['attempts'],2)

    def test_invalid_inputs_and_unknown_metadata_are_atomic(self):
        for changes in ({'scope':''},{'scope':True},{'request_limit':True},{'request_limit':0},{'request_limit':-1}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.budget(**changes)
        with self.assertRaises(ValueError):InferenceBudget(':memory:',scope='scope',request_limit=1)
        budget=self.budget();identity=budget.reserve(model='synthetic-model');before=self.path.read_bytes()
        for tokens in (self.tokens(prompt_token_count=True),self.tokens(candidates_token_count=-1),
                       self.tokens(total_token_count=1.5),{},self.tokens(extra=0)):
            with self.subTest(tokens=tokens),self.assertRaises(ValueError):budget.complete(identity,outcome='response_accepted',tokens=tokens)
            self.assertEqual(self.path.read_bytes(),before)
        with self.assertRaises(ValueError):budget.complete(identity,outcome='invented',tokens=None)
        with self.assertRaises(ValueError):budget.complete(str(uuid4()),outcome='request_failed',tokens=None)
        with self.assertRaises(ValueError):budget.reserve(model='')
        budget.complete(identity,outcome='request_failed',tokens=None)
        self.assertEqual(budget.status()['completed'],1)
        self.assertEqual(budget.status()['unknown_usage_count'],1)

    def test_policy_and_completion_tampering_fail_closed(self):
        budget=self.budget();identity=budget.reserve(model='synthetic-model')
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('UPDATE policies SET request_limit=4');db.commit()
        with self.assertRaises(ValueError):budget.reserve(model='synthetic-model')
        with self.assertRaises(ValueError):budget.status()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('UPDATE policies SET request_limit=3');db.execute('UPDATE attempts SET total_token_count=1.5 WHERE reservation_id=?',(identity,));db.commit()
        with self.assertRaises(ValueError):budget.status()
        with self.assertRaises(ValueError):budget.complete(identity,outcome='request_failed',tokens=None)
        with self.assertRaises(ValueError):budget.reserve(model='synthetic-model')

    def test_completed_without_outcome_cannot_authorize_another_attempt(self):
        budget=self.budget();identity=budget.reserve(model='synthetic-model')
        budget.complete(identity,outcome='request_failed',tokens=None)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('UPDATE attempts SET outcome=NULL WHERE reservation_id=?',(identity,));db.commit()
        before=self.path.read_bytes()
        for operation in (budget.status,lambda:budget.reserve(model='synthetic-model'),
                          lambda:budget.complete(identity,outcome='request_failed',tokens=None),self.budget):
            with self.assertRaises(ValueError):operation()
            self.assertEqual(self.path.read_bytes(),before)

    def test_multiprocess_ceiling_is_shared_and_exact(self):
        self.budget()
        ctx=multiprocessing.get_context('spawn');gate=ctx.Event();results=ctx.Queue()
        processes=[ctx.Process(target=reserve_worker,args=(str(self.path),gate,results)) for _ in range(7)]
        try:
            for process in processes:process.start()
            gate.set();outcomes=[results.get(timeout=20) for _ in processes]
            for process in processes:process.join(10);self.assertEqual(process.exitcode,0)
            self.assertEqual(outcomes.count('reserved'),3,outcomes)
            self.assertEqual(outcomes.count('denied'),4,outcomes)
            self.assertEqual(self.budget().status()['pending'],3)
        finally:
            for process in processes:
                if process.is_alive():process.terminate();process.join(5)
            results.close();results.join_thread()
