import copy
import hashlib
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.salary_rules import VeteranMinimumProfile
from franchise.store import FranchiseStore


class SalaryClassificationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name)/'league.sqlite'
        self.store = FranchiseStore(self.path)
        self.store.create_franchise({team: self.ledger() for team in ('a','b')}, seed='fixed-origin')
        self.profile = VeteranMinimumProfile(2026, (('v',(3,3),('active_inactive',)*2),))
        self.inputs = dict(request_id='opening-salary-inputs',source='authored credited-season evidence',
            profile=self.profile.to_dict(),expected_revisions={'a':0,'b':0})

    def ledger(self):
        return Ledger.from_opening(OpeningBooks(),cap=10_000_000,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={},observed_player_ids=frozenset({'v','unknown'}),
            observed_player_source='authored registry')

    def rows(self):
        with closing(sqlite3.connect(self.path)) as db:
            return (db.execute('select * from teams order by id').fetchall(),
                    db.execute('select * from events order by id').fetchall(),
                    db.execute('select * from franchise_metadata order by key').fetchall())

    def test_initialization_preserves_personality_history_and_balances_across_restart(self):
        before=self.rows(); actors={t:self.store.player_context(t,'v') for t in ('a','b')}
        with self.assertRaises(Rejected):self.store.preview_offer('a',Offer('v',(1_145_000,),0),0)
        batch=self.store.initialize_salary_classification(**self.inputs)
        restored=FranchiseStore(self.path)
        self.assertEqual(restored.initialize_salary_classification(**self.inputs),batch)
        self.assertEqual(before[0],self.rows()[0])  # Immutable team bootstrap.
        self.assertEqual(before[1],self.rows()[1][:len(before[1])])
        for team in ('a','b'):
            ledger=restored.load_team(team)
            self.assertEqual(ledger.revision,1);self.assertEqual(ledger.charges,(0,))
            context=restored.player_context(team,'v')
            self.assertEqual(context['personality'],actors[team]['personality'])
            self.assertEqual(context['relationships'],actors[team]['relationships'])
            self.assertNotIn('classification_pending',context)
            self.assertTrue(restored.player_context(team,'unknown')['classification_pending'])
        with self.assertRaises(Rejected):restored.preview_offer('a',Offer('v',(1_144_999,),0),1)
        self.assertEqual(restored.preview_offer('a',Offer('v',(1_145_000,),0),1)['contract_charges'],[1_145_000])

    def test_stale_or_incomplete_or_unknown_inputs_are_atomic(self):
        for change in ('stale','missing','unknown','boolean'):
            inputs=copy.deepcopy(self.inputs)
            if change=='stale':inputs['expected_revisions']['b']=1
            elif change=='missing':inputs['expected_revisions'].pop('b')
            elif change=='boolean':inputs['expected_revisions']['b']=False
            else:inputs['profile']['players'][0]['player_id']='other'
            before=self.rows()
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.store.initialize_salary_classification(**inputs)
            self.assertEqual(before,self.rows())

    def test_conflicting_retry_and_changed_membership_reject(self):
        self.store.initialize_salary_classification(**self.inputs)
        before=self.rows();changed=copy.deepcopy(self.inputs);changed['source']='replacement'
        with self.assertRaises(Rejected):self.store.initialize_salary_classification(**changed)
        with self.assertRaises(Rejected):self.store.create_team('c',self.ledger())
        self.assertEqual(before,self.rows())

    def test_deleted_or_tampered_group_refuses_replay_even_for_other_team(self):
        self.store.initialize_salary_classification(**self.inputs)
        with closing(sqlite3.connect(self.path)) as db, db:
            payload=json.loads(db.execute("select payload from events where team_id='b' and kind='salary_classification'").fetchone()[0])
            payload['batch_sha256']='0'*64
            db.execute("update events set payload=? where team_id='b' and kind='salary_classification'",(json.dumps(payload),))
        with self.assertRaises(ValueError):self.store.load_team('a')
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("delete from events where kind='salary_classification'")
        with self.assertRaises(ValueError):self.store.load_team('a')

    def test_existing_annual_credit_inputs_cannot_be_replaced_even_at_same_floor(self):
        ledger=self.ledger()
        original=VeteranMinimumProfile(2026,(('v',(7,),('active_inactive',)),))
        ledger.initialize_salary_classification(original,source='original inputs',expected_revision=0)
        changed=VeteranMinimumProfile(2026,(('v',(8,),('active_inactive',)),))
        before=ledger.negotiation_context('v')
        with self.assertRaises(Rejected):ledger.initialize_salary_classification(changed,source='replacement',expected_revision=1)
        self.assertEqual(ledger.negotiation_context('v'),before)

    def test_simultaneous_identical_imports_commit_only_one_group(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:FranchiseStore(self.path).initialize_salary_classification(**self.inputs),range(2)))
        self.assertEqual(results[0],results[1])
        self.assertEqual(self.store.load_team('a').revision,1)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("select count(*) from events where kind='salary_classification'").fetchone()[0],2)

    def test_prepared_guest_work_blocks_classification_without_mutation(self):
        from tools.check_native_saved_signing import fixture
        from franchise.snapshot_origin import bind
        from franchise import guest_signing
        root=self.path.parent/'guest';root.mkdir();data=fixture(root)
        store=data['store'];sample=data['sample']
        bind(store,sample.bindings,sample.before)
        guest_signing.prepare(store,'49ers','native-captured','journal',bindings=sample.bindings,
            before_payload=sample.before,guest_offer=sample.raw,
            expected_before_sha256=hashlib.sha256(sample.before).hexdigest(),
            expected_revision=1,access_check=lambda:None)
        before=Path(store.path).read_bytes()
        with self.assertRaisesRegex(Rejected,'awaits confirmation'):
            store.initialize_salary_classification(**self.inputs)
        self.assertEqual(Path(store.path).read_bytes(),before)
