"""Conservative durable token reservations never imply exact dollar billing."""
from contextlib import closing
import multiprocessing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from franchise.inference_budget import InferenceBudget,BudgetExceeded,TOKEN_FIELDS


def token_worker(path,gate,results):
    try:
        budget=InferenceBudget(path,scope='franchise/2028',request_limit=10,token_limit=30)
        gate.wait(10);budget.reserve(model='synthetic-model',input_tokens=5,output_tokens=5)
        results.put('reserved')
    except BudgetExceeded:results.put('denied')
    except BaseException as error:results.put(type(error).__name__+':'+str(error))


class InferenceTokenBudgetTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'token-budget.sqlite'

    def budget(self,**changes):
        return InferenceBudget(self.path,**{'scope':'franchise/2028','request_limit':10,'token_limit':30,**changes})

    def test_failure_unknown_usage_and_crash_pending_never_refund_reserved_tokens(self):
        budget=self.budget();first=budget.reserve(model='synthetic-model',input_tokens=5,output_tokens=5)
        budget.complete(first,outcome='request_failed',tokens=None)
        second=budget.reserve(model='synthetic-model',input_tokens=5,output_tokens=5)
        tokens=dict.fromkeys(TOKEN_FIELDS);tokens.update(prompt_token_count=2,candidates_token_count=1,total_token_count=3)
        budget.complete(second,outcome='response_accepted',tokens=tokens)
        self.budget().reserve(model='synthetic-model',input_tokens=5,output_tokens=5)
        status=self.budget().status()
        self.assertEqual((status['token_limit'],status['reserved_tokens'],status['remaining_tokens']),(30,30,0))
        self.assertEqual((status['attempts'],status['completed'],status['pending']),(3,2,1))
        self.assertEqual(status['known_token_usage']['total_token_count'],3)
        with self.assertRaises(BudgetExceeded):self.budget().reserve(model='synthetic-model',input_tokens=0,output_tokens=1)
        before=self.path.read_bytes();budget.complete(second,outcome='response_accepted',tokens=tokens)
        self.assertEqual(self.path.read_bytes(),before)

    def test_policy_cannot_change_disappear_or_upgrade_attempted_legacy_scope(self):
        budget=self.budget();budget.reserve(model='synthetic-model',input_tokens=1,output_tokens=1)
        for value in (None,29,31):
            with self.subTest(token_limit=value),self.assertRaises(ValueError):self.budget(token_limit=value)
        legacy=self.budget(scope='legacy/2028',token_limit=None);legacy.reserve(model='synthetic-model')
        with self.assertRaises(ValueError):self.budget(scope='legacy/2028',token_limit=30)
        self.assertEqual(self.budget(scope='legacy/2028',token_limit=None).status()['attempts'],1)
        self.assertNotIn('token_limit',legacy.status())
        fresh=self.budget(scope='new-season/2029',token_limit=20)
        self.assertEqual(fresh.status()['reserved_tokens'],0)
        self.assertEqual(fresh.status()['remaining_tokens'],20)

    def test_required_exact_reservation_bounds_reject_before_mutation(self):
        budget=self.budget();before=self.path.read_bytes()
        for values in ({},{'input_tokens':0},{'output_tokens':1},{'input_tokens':True,'output_tokens':1},
                       {'input_tokens':0,'output_tokens':True},{'input_tokens':-1,'output_tokens':1},
                       {'input_tokens':0,'output_tokens':0},{'input_tokens':1.5,'output_tokens':1},
                       {'input_tokens':2**63-1,'output_tokens':1}):
            with self.subTest(values=values),self.assertRaises(ValueError):budget.reserve(model='synthetic-model',**values)
            self.assertEqual(self.path.read_bytes(),before)
        for limit in (True,0,-1,2**63):
            with self.subTest(limit=limit),self.assertRaises(ValueError):self.budget(scope='invalid',token_limit=limit)
        with self.assertRaises(BudgetExceeded):budget.reserve(model='synthetic-model',input_tokens=30,output_tokens=1)
        self.assertEqual(budget.status()['attempts'],0)

    def test_input_output_and_total_overrun_disable_future_authorization(self):
        cases=({'prompt_token_count':6},
            {'candidates_token_count':4,'thoughts_token_count':7},
            {'total_token_count':16},{'candidates_token_count':11},{'thoughts_token_count':11})
        for index,usage in enumerate(cases):
            budget=self.budget(scope='overrun/'+str(index))
            identity=budget.reserve(model='synthetic-model',input_tokens=5,output_tokens=10)
            tokens=dict.fromkeys(TOKEN_FIELDS);tokens.update(usage)
            with self.assertRaises(ValueError):budget.complete(identity,outcome='response_accepted',tokens=tokens)
            with closing(sqlite3.connect(self.path)) as db:
                self.assertEqual(db.execute('SELECT completed FROM attempts WHERE reservation_id=?',(identity,)).fetchone(),(1,))
                for field,value in usage.items():
                    self.assertEqual(db.execute('SELECT '+field+' FROM attempts WHERE reservation_id=?',(identity,)).fetchone(),(value,))
            with self.subTest(usage=usage):
                with self.assertRaises(ValueError):budget.status()
                with self.assertRaises(ValueError):budget.reserve(model='synthetic-model',input_tokens=0,output_tokens=1)
                with self.assertRaises(ValueError):self.budget(scope='overrun/'+str(index))

    def test_exact_boundary_and_unknown_thinking_usage_are_not_fabricated(self):
        budget=self.budget();identity=budget.reserve(model='synthetic-model',input_tokens=5,output_tokens=10)
        tokens=dict.fromkeys(TOKEN_FIELDS);tokens.update(prompt_token_count=5,candidates_token_count=10,total_token_count=15)
        budget.complete(identity,outcome='response_accepted',tokens=tokens)
        self.assertEqual(budget.status()['unknown_usage_count'],1)
        self.assertEqual(budget.status()['reserved_tokens'],15)
        other=budget.reserve(model='synthetic-model',input_tokens=0,output_tokens=15)
        self.assertNotEqual(identity,other);self.assertEqual(budget.status()['remaining_tokens'],0)

    def test_multiprocess_token_ceiling_is_shared_and_exact(self):
        self.budget();ctx=multiprocessing.get_context('spawn');gate=ctx.Event();results=ctx.Queue()
        processes=[ctx.Process(target=token_worker,args=(str(self.path),gate,results)) for _ in range(7)]
        try:
            for process in processes:process.start()
            gate.set();outcomes=[results.get(timeout=20) for _ in processes]
            for process in processes:process.join(10);self.assertEqual(process.exitcode,0)
            self.assertEqual(outcomes.count('reserved'),3,outcomes)
            self.assertEqual(outcomes.count('denied'),4,outcomes)
            self.assertEqual(self.budget().status()['reserved_tokens'],30)
        finally:
            for process in processes:
                if process.is_alive():process.terminate();process.join(5)
            results.close();results.join_thread()

    def test_missing_malformed_or_orphan_token_reservations_fail_closed(self):
        for scenario in ('missing','fraction','zero_output','policy','orphan'):
            path=self.path.with_name(scenario+'.sqlite')
            budget=InferenceBudget(path,scope='franchise/2028',request_limit=10,token_limit=30)
            identity=budget.reserve(model='synthetic-model',input_tokens=5,output_tokens=5)
            with closing(sqlite3.connect(path)) as db:
                if scenario=='missing':db.execute('DELETE FROM token_reservations WHERE reservation_id=?',(identity,))
                elif scenario=='fraction':db.execute('UPDATE token_reservations SET input_tokens=5.5 WHERE reservation_id=?',(identity,))
                elif scenario=='zero_output':db.execute('UPDATE token_reservations SET output_tokens=0 WHERE reservation_id=?',(identity,))
                elif scenario=='policy':db.execute('UPDATE token_policies SET token_limit=31')
                else:db.execute("INSERT INTO token_reservations VALUES('00000000-0000-4000-8000-000000000000',0,1)")
                db.commit()
            with self.subTest(scenario=scenario):
                with self.assertRaises(ValueError):budget.status()
                with self.assertRaises(ValueError):budget.reserve(model='synthetic-model',input_tokens=0,output_tokens=1)
