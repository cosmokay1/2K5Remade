from contextlib import closing
from dataclasses import replace
from datetime import date
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger,Offer,Rejected
from franchise.returns import PreseasonReturnScope,RETURN_EXCLUSIONS
from franchise.store import FranchiseStore
from tests import test_releases


class ReturnStoreTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.store=FranchiseStore(Path(temp.name)/'state.sqlite')
        self.store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=200,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
        self.store.initialize_cash('a',(),source='synthetic complete cash')
        self.old_offer=Offer('v',(10,20,30),9,(0,20,10))
        self.original=self.store.sign('a','original',self.old_offer,1)
        self.store.record_payment('a','bonus','contract:v',9,expected_cash_revision=1,
            source='synthetic bank',payment_reference='bonus receipt',component='signing_bonus')
        self.release=test_releases.PreseasonReleaseTests().plan()
        self.store.release_preseason_veteran('a','first-release','v',scope=self.release.scope,
            discount=self.release.discount,payment_year_offsets=(0,1,2),expected_revision=3,access_check=lambda:None)
        self.old_id=self.store.contract_generations('a')['generations'][0]['generation_id']
        self.scope=PreseasonReturnScope(2026,date(2026,6,1),date(2026,9,10),True,
            RETURN_EXCLUSIONS,'synthetic independent return agreement')
        self.offer=Offer('v',(5,5,5),3,(5,0,0))

    def migrate(self):FranchiseStore.migrate_generations(self.store.path)

    def sign(self,**changes):
        args=dict(scope=self.scope,access_check=lambda:None)
        args.update(changes)
        return self.store.return_sign('a','return',self.offer,4,**args)

    def test_release_return_payment_second_release_and_restart_preserve_both_agreements(self):
        self.migrate()
        receipt=self.sign()
        ledger=self.store.load_team('a')
        self.assertEqual(ledger.charges,(45,6,6))
        gid=ledger.contract_identity('v').generation_id
        self.assertNotEqual(gid,self.old_id)
        self.assertEqual(ledger.generation_cash(self.old_id).amount,39)
        self.assertEqual(ledger.generation_cash(gid).amount,18)
        self.assertEqual(self.store.sign('a','original',self.old_offer,1),self.original)
        self.store.record_payment('a','old-debt','contract:v',4,expected_cash_revision=4,
            source='synthetic bank',payment_reference='old debt receipt',component='base:1')
        self.assertEqual(self.store.load_team('a').generation_cash(gid).paid,0)
        self.store.release_preseason_veteran('a','second-release','v',scope=self.release.scope,
            discount=self.release.discount,payment_year_offsets=(0,1,2),expected_revision=6,access_check=lambda:None)
        reopened=FranchiseStore(self.store.path)
        ledger=reopened.load_team('a')
        self.assertEqual(ledger.charges,(47,0,0))
        self.assertEqual(ledger.generation_cash(self.old_id).paid,13)
        self.assertEqual(ledger.generation_cash(gid).amount,8)
        self.assertEqual(ledger.generation_guarantee_cash(self.old_id)['unpaid_guaranteed_base_by_original_year'],[0,16,10])
        self.assertEqual(len(reopened.contract_generations('a')['generations']),2)
        self.assertEqual(reopened.return_sign('a','return',self.offer,4,scope=self.scope,access_check=lambda:None),receipt)
        self.assertEqual(reopened.load_team('a').generation_snapshot(),ledger.generation_snapshot())

    def test_format3_and_final_access_failure_leave_every_obligation_unchanged(self):
        before=self.store.load_team('a').generation_snapshot()
        with self.assertRaises(Rejected):self.sign()
        self.assertEqual(self.store.load_team('a').generation_snapshot(),before)
        self.migrate()
        def interrupted():raise TimeoutError('disconnected')
        with self.assertRaises(TimeoutError):self.sign(access_check=interrupted)
        self.assertEqual(self.store.load_team('a').generation_snapshot(),before)
        with closing(sqlite3.connect(self.store.path)) as db:
            self.assertIsNone(db.execute("SELECT 1 FROM ownership WHERE player_id='v'").fetchone())
            self.assertIsNone(db.execute("SELECT 1 FROM events WHERE kind='return_sign'").fetchone())

    def test_competing_owner_and_changed_retry_scope_reject(self):
        self.migrate();self.sign()
        with self.assertRaises(Rejected):self.sign(scope=replace(self.scope,source='changed'))
        with self.assertRaises(Rejected):
            self.store.return_sign('a','another',self.offer,5,scope=self.scope,access_check=lambda:None)
        self.assertEqual(len(self.store.contract_generations('a')['generations']),2)

    def test_new_generation_posting_corruption_and_downgrade_reject(self):
        self.migrate();self.sign()
        with closing(sqlite3.connect(self.store.path)) as db:
            event,payload=db.execute("SELECT id,payload FROM events WHERE kind='return_sign'").fetchone()
            original=json.loads(payload)
        for mutated in ({**original,'generation_posting':{**original['generation_posting'],'format':True}},
                        {key:value for key,value in original.items() if key!='generation_posting'}):
            with closing(sqlite3.connect(self.store.path)) as db:
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(mutated),event));db.commit()
            with self.assertRaises(ValueError):self.store.load_team('a')

    def test_second_release_cannot_be_downgraded_to_legacy_event(self):
        self.migrate();self.sign()
        self.store.release_preseason_veteran('a','second-release','v',scope=self.release.scope,
            discount=self.release.discount,payment_year_offsets=(0,1,2),expected_revision=5,access_check=lambda:None)
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute("UPDATE events SET kind='release' WHERE kind='generation_release'");db.commit()
        with self.assertRaisesRegex(ValueError,'versioned generation'):
            self.store.load_team('a')

    def test_manual_return_request_cannot_be_reused_as_normal_signing_or_story(self):
        self.migrate();self.sign()
        self.assertEqual(self.store.stories('a'),[])
        with self.assertRaises(Rejected):self.store.sign('a','return',self.offer,4)
        with self.assertRaises(Rejected):self.store.recalled_negotiation('a','return',self.offer)

    def test_old_release_retry_does_not_close_new_agreement(self):
        self.migrate();self.sign()
        before=self.store.load_team('a').generation_snapshot()
        self.store.release_preseason_veteran('a','first-release','v',scope=self.release.scope,
            discount=self.release.discount,payment_year_offsets=(0,1,2),expected_revision=3,access_check=lambda:None)
        self.assertEqual(self.store.load_team('a').generation_snapshot(),before)

    def test_closed_new_agreement_cannot_pay_cancelled_unguaranteed_base(self):
        self.migrate();self.sign()
        gid=self.store.load_team('a').contract_identity('v').generation_id
        self.store.release_preseason_veteran('a','second-release','v',scope=self.release.scope,
            discount=self.release.discount,payment_year_offsets=(0,1,2),expected_revision=5,access_check=lambda:None)
        before=self.store.load_team('a').generation_snapshot()
        with self.assertRaises(ValueError):
            self.store.record_payment('a','invalid-payment',gid,1,expected_cash_revision=5,
                source='synthetic bank',payment_reference='invalid receipt',component='base:1')
        self.assertEqual(self.store.load_team('a').generation_snapshot(),before)

    def test_two_former_clubs_cannot_acquire_same_player(self):
        self.store.create_team('b',Ledger.from_opening(OpeningBooks(),cap=200,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
        self.store.initialize_cash('b',(),source='synthetic other club cash')
        self.store.sign('b','other-original',Offer('v',(1,1,1),0),1)
        self.store.release_preseason_veteran('b','other-release','v',scope=self.release.scope,
            discount=self.release.discount,payment_year_offsets=(0,1,2),expected_revision=2,access_check=lambda:None)
        self.migrate();self.sign()
        before=self.store.load_team('b').generation_snapshot()
        with self.assertRaisesRegex(Rejected,'belongs to a team'):
            self.store.return_sign('b','competing-return',self.offer,3,scope=self.scope,access_check=lambda:None)
        self.assertEqual(self.store.load_team('b').generation_snapshot(),before)
        self.assertEqual(self.store.load_team('a').financial_snapshot()['signed_players'],['v'])

    def test_third_agreement_retains_both_closed_generations(self):
        self.migrate();self.sign()
        second=self.store.load_team('a').contract_identity('v').generation_id
        self.store.release_preseason_veteran('a','second-release','v',scope=self.release.scope,
            discount=self.release.discount,payment_year_offsets=(0,1,2),expected_revision=5,access_check=lambda:None)
        self.store.return_sign('a','third',self.offer,6,scope=self.scope,access_check=lambda:None)
        ledger=FranchiseStore(self.store.path).load_team('a')
        self.assertEqual(ledger.charges,(53,6,6))
        self.assertEqual(len(ledger.generation_agreements()),3)
        self.assertEqual(ledger.generation_cash(self.old_id).amount,39)
        self.assertEqual(ledger.generation_cash(second).amount,8)
        self.assertEqual(ledger.generation_cash(ledger.contract_identity('v').generation_id).amount,18)

    def test_failed_journal_insert_rolls_back_ownership_and_new_obligation(self):
        self.migrate()
        before=self.store.load_team('a').generation_snapshot()
        with closing(sqlite3.connect(self.store.path)) as db:
            db.execute("CREATE TRIGGER reject_return BEFORE INSERT ON events WHEN NEW.kind='return_sign' BEGIN SELECT RAISE(ABORT,'injected return failure'); END")
            db.commit()
        with self.assertRaises(sqlite3.IntegrityError):self.sign()
        self.assertEqual(self.store.load_team('a').generation_snapshot(),before)
        with closing(sqlite3.connect(self.store.path)) as db:
            self.assertIsNone(db.execute("SELECT 1 FROM ownership WHERE player_id='v'").fetchone())
