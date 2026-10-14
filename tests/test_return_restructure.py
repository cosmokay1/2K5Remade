from contextlib import closing
from dataclasses import asdict,replace
from fractions import Fraction
from datetime import date
import json
import sqlite3
import unittest
from franchise.bridge import Bridge
from franchise.cap import Rejected
from franchise.store import FranchiseStore
from tests import test_return_store,test_restructures


class ReturnedRestructureTests(unittest.TestCase):
    def setUp(self):
        fixture=test_return_store.ReturnStoreTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.migrate();fixture.sign();self.fixture=fixture;self.store=fixture.store
        ledger=self.store.load_team('a');self.gid=ledger.contract_identity('v').generation_id
        self.store.record_payment('a','new-bonus',self.gid,3,expected_cash_revision=4,
            source='synthetic bank',payment_reference='new bonus paid',component='signing_bonus')
        self.scope=test_restructures.PreseasonRestructureTests().scope()

    def amend(self,**changes):
        args=dict(scope=self.scope,converted_base=4,expected_revision=6,access_check=lambda:None,generation_id=self.gid)
        args.update(changes)
        return self.store.restructure_preseason_veteran('a','conversion','v',**args)

    def test_generation_amendment_preserves_birth_old_debt_replay_and_release(self):
        before=self.store.load_team('a');old=before.generation_accounting(self.fixture.old_id)
        oldcash=before.generation_cash(self.fixture.old_id);birth=before.generation_accounting(self.gid).original_contract
        result=self.amend()
        ledger=FranchiseStore(self.store.path).load_team('a')
        self.assertEqual(ledger.charges,(Fraction(127,3),Fraction(22,3),Fraction(22,3)))
        self.assertEqual(ledger.generation_accounting(self.fixture.old_id),old)
        self.assertEqual(ledger.generation_cash(self.fixture.old_id),oldcash)
        self.assertEqual(ledger.generation_accounting(self.gid).original_contract,birth)
        self.assertEqual(ledger.generation_cash(self.gid).amount,18)
        self.assertEqual(ledger.generation_cash(self.gid).paid,3)
        self.assertEqual(self.amend(),result)
        self.store.release_preseason_veteran('a','second-release','v',scope=self.fixture.release.scope,
            discount=self.fixture.release.discount,payment_year_offsets=(0,1,2),expected_revision=7,access_check=lambda:None)
        self.assertEqual(self.amend(),result)
        closed=FranchiseStore(self.store.path).load_team('a')
        self.assertEqual(closed.generation_cash(self.fixture.old_id),oldcash)
        self.assertEqual(closed.generation_cash(self.gid).amount,8)
        self.assertEqual(closed.generation_guarantee_cash(self.gid)['unpaid_signing_bonus'],4)
        with closing(sqlite3.connect(self.store.path)) as db:
            self.assertEqual(db.execute("SELECT kind FROM events WHERE request_key='restructure:conversion'").fetchone()[0],'generation_restructure')

    def test_negative_floor_scope_revision_disconnect_identity_keep_all_archives(self):
        before=self.store.load_team('a').generation_snapshot()
        for changes in ({'converted_base':5},{'expected_revision':5},{'generation_id':self.fixture.old_id},
                        {'scope':replace(self.scope,amended_on=date(2026,5,1))}):
            with self.subTest(changes=changes),self.assertRaises((Rejected,ValueError)):self.amend(**changes)
            self.assertEqual(self.store.load_team('a').generation_snapshot(),before)
        def disconnect():raise TimeoutError('disconnected')
        with self.assertRaises(TimeoutError):self.amend(access_check=disconnect)
        self.assertEqual(self.store.load_team('a').generation_snapshot(),before)

    def test_bridge_explicit_generation_and_ai_off_receipt(self):
        scope=asdict(self.scope);scope.update(amended_on=self.scope.amended_on.isoformat(),
            first_regular_season_game=self.scope.first_regular_season_game.isoformat(),exclusions=sorted(self.scope.exclusions))
        request=dict(protocol=1,request_id='conversion',operation='manual_restructure',team_id='a',player_id='v',
            expected_revision=6,timeout_ms=1000,decision_mode='manual',scope=scope,converted_base=4,generation_id=self.gid)
        bridge=Bridge(self.store,provider=lambda _:self.fail('model called'),access_check=lambda:self.fail('AI check called'))
        missing=dict(request);missing.pop('generation_id')
        self.assertEqual(bridge.handle(missing)['error'],'invalid_request')
        result=bridge.handle(request)
        self.assertEqual(result['result']['generation_id'],self.gid,result)
        self.assertEqual(bridge.handle(request),result)

    def test_versioned_original_and_archive_tampering_rejected(self):
        self.amend()
        with closing(sqlite3.connect(self.store.path)) as db:
            original=db.execute("SELECT payload FROM events WHERE kind='generation_restructure'").fetchone()[0]
        for field in ('generation_id','before_generation_posting','generation_posting','scope'):
            data=json.loads(original)
            if field=='generation_id':data[field]=self.fixture.old_id
            elif field=='scope':data[field]['amended_on']='20260601'
            else:data[field]['format']=True
            with closing(sqlite3.connect(self.store.path)) as db,db:
                db.execute("UPDATE events SET payload=? WHERE kind='generation_restructure'",(json.dumps(data),))
            with self.assertRaises(ValueError):self.store.load_team('a')
            with closing(sqlite3.connect(self.store.path)) as db,db:
                db.execute("UPDATE events SET payload=? WHERE kind='generation_restructure'",(original,))

    def test_superseded_bonus_layer_identity_cannot_be_reused(self):
        from franchise.cap import Offer
        from tests import test_generation_identity,test_releases
        fixture=test_generation_identity.ConsumedGenerationIdentityTests();fixture.setUp()
        ledger=fixture.ledger();ledger.bind_team_identity('a')
        ledger.apply_preseason_restructure('v',scope=self.scope,converted_base=8,record_id='old-layer',expected_revision=0)
        release=test_releases.PreseasonReleaseTests().plan()
        ledger.apply_preseason_release('v',scope=release.scope,discount=release.discount,
            payment_year_offsets=(0,)*5,record_id='old-release',expected_revision=1)
        ledger.return_sign('return',Offer('v',(5,5),0,(5,0)),2,scope=self.fixture.scope)
        before=ledger.generation_snapshot()
        with self.assertRaisesRegex(Rejected,'identity already exists'):
            ledger.apply_preseason_restructure('v',scope=self.scope,converted_base=3,record_id='old-layer',expected_revision=3)
        self.assertEqual(ledger.generation_snapshot(),before)
