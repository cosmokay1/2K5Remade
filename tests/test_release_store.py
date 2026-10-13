from dataclasses import replace
from datetime import date
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from franchise.books import ActiveContract,OpeningBooks
from franchise.cap import Ledger,Offer,Rejected
from franchise.cash import CashObligation
from franchise.control import AccessDisabled
from franchise.guarantees import DiscountProfile
from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
from franchise.store import FranchiseStore


class ReleaseStoreTests(unittest.TestCase):
    def setup_store(self,directory):
        store=FranchiseStore(Path(directory)/'release.sqlite')
        contract=ActiveContract(Offer('v',(10,20,30),9,(0,20,10)),'fixture original contract')
        store.create_team('a',Ledger.from_opening(OpeningBooks(contracts=(contract,)),cap=30,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(1,)*3,'other':(1,)*3}))
        store.create_team('b',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
        store.initialize_cash('a',(CashObligation('contract:v','v',69,9,'fixture payments',(('signing_bonus',9),)),),source='fixture coverage')
        return store

    def release(self,store,**changes):
        inputs=dict(scope=PreseasonReleaseScope(2026,date(2026,6,1),date(2026,9,10),EXCLUDED_LIABILITIES,
            True,True,0,'fixture supported termination'),discount=DiscountProfile(2026,Fraction(0),'synthetic zero rate'),
            payment_year_offsets=(0,1,2),expected_revision=1,access_check=lambda:None)
        inputs.update(changes)
        return store.release_preseason_veteran('a','release','v',**inputs)

    def test_release_replays_retains_debt_and_removes_exclusive_ownership(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            result=self.release(store)
            reopened=FranchiseStore(store.path)
            self.assertEqual(self.release(reopened),result)
            ledger=reopened.load_team('a')
            self.assertEqual(ledger.charges,(39,0,0))
            self.assertEqual(ledger.room,-9)
            self.assertEqual(ledger.financial_snapshot()['signed_players'],[])
            self.assertEqual(ledger.cash_snapshot()['unpaid_total'],30)
            self.assertEqual(ledger.revision,2)
            with self.assertRaises(Rejected):reopened.sign('a','new',Offer('other',(1,),0),2)
            with self.assertRaises(Rejected):reopened.sign('a','resign',Offer('v',(1,),0),2)
            reopened.sign('b','new-club',Offer('v',(10,),0),0)
            self.assertEqual(FranchiseStore(store.path).load_team('a').cash_snapshot()['unpaid_total'],30)
            self.assertEqual(reopened.load_team('b').financial_snapshot()['signed_players'],['v'])

    def test_release_rollback_stale_and_conflicting_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            before=store.load_team('a').financial_snapshot(),store.load_team('a').cash_snapshot()
            def disabled():raise AccessDisabled('fixture disconnect')
            with self.assertRaises(AccessDisabled):self.release(store,access_check=disabled)
            self.assertEqual((store.load_team('a').financial_snapshot(),store.load_team('a').cash_snapshot()),before)
            with self.assertRaises(Rejected):self.release(store,expected_revision=0)
            self.release(store)
            with self.assertRaises(Rejected):self.release(store,payment_year_offsets=(1,1,2))
            self.assertEqual(FranchiseStore(store.path).load_team('a').revision,2)

    def test_retained_payments_cannot_pay_cancelled_base_or_change_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            self.release(store)
            cash_revision=store.load_team('a').cash_snapshot()['revision']
            with self.assertRaises(ValueError):
                store.record_payment('a','cancelled','contract:v',1,expected_cash_revision=cash_revision,
                    source='fixture bank',payment_reference='cancelled',component='base:0')
            store.record_payment('a','protected','contract:v',5,expected_cash_revision=cash_revision,
                source='fixture bank',payment_reference='protected',component='base:1')
            ledger=FranchiseStore(store.path).load_team('a')
            self.assertEqual(ledger.charges,(39,0,0))
            self.assertEqual(ledger.cash_snapshot()['unpaid_total'],25)

    def test_post_june_release_and_tampered_cash_replay(self):
        import json,sqlite3
        from contextlib import closing
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            scope=PreseasonReleaseScope(2026,date(2026,6,2),date(2026,9,10),EXCLUDED_LIABILITIES,
                True,True,0,'fixture supported termination')
            self.release(store,scope=scope)
            self.assertEqual(FranchiseStore(store.path).load_team('a').charges,(33,6,0))
            with closing(sqlite3.connect(store.path)) as db:
                row=db.execute("SELECT id,payload FROM events WHERE kind='release'").fetchone()
                payload=json.loads(row[1])
                payload['cash_posting']['unpaid_total']=0
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),row[0]))
                db.commit()
            with self.assertRaisesRegex(ValueError,'cash posting'):store.load_team('a')

    def test_database_failure_after_ownership_delete_rolls_back_entire_release(self):
        import sqlite3
        from contextlib import closing
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            before=store.load_team('a').financial_snapshot(),store.load_team('a').cash_snapshot()
            with closing(sqlite3.connect(store.path)) as db:
                db.execute("CREATE TRIGGER reject_release BEFORE INSERT ON events WHEN NEW.kind='release' BEGIN SELECT RAISE(ABORT,'fixture rejection'); END")
                db.commit()
            with self.assertRaises(sqlite3.IntegrityError):self.release(store)
            reopened=FranchiseStore(store.path)
            self.assertEqual((reopened.load_team('a').financial_snapshot(),reopened.load_team('a').cash_snapshot()),before)
            with self.assertRaises(Rejected):reopened.sign('b','steal',Offer('v',(10,),0),0)
