from contextlib import closing
from dataclasses import replace
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger, Rejected
from franchise.store import FranchiseStore
from tests import test_restructures as fixtures


class RestructureStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store=FranchiseStore(Path(self.temp.name)/'state.sqlite')
        self.fixture=fixtures.PreseasonRestructureTests()
        ledger=Ledger.from_opening(OpeningBooks(contracts=(self.fixture.contract(),)),cap=200,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(2,)*5})
        self.store.create_team('a',ledger)
        self.store.initialize_cash('a',(self.fixture.cash(),),source='synthetic allocated opening')

    def amend(self,**changes):
        args=dict(scope=self.fixture.scope(),converted_base=8,expected_revision=1,access_check=lambda:None)
        args.update(changes)
        return self.store.restructure_preseason_veteran('a','conversion','v',**args)

    def test_restart_and_retry_preserve_cash_and_new_component(self):
        receipt=self.amend()
        reopened=FranchiseStore(self.store.path)
        ledger=reopened.load_team('a')
        self.assertEqual(ledger.revision,2)
        self.assertEqual(ledger.active_contract('v').charges(),self.fixture.plan().contract.charges())
        self.assertEqual(ledger.guarantee_cash('v')['unpaid_signing_bonus'],8)
        self.assertEqual(receipt['cash']['nominal_total'],180)
        self.assertEqual(receipt['cash']['paid_total'],30)
        self.assertEqual(self.amend(),receipt)
        with self.assertRaises(Rejected):self.amend(converted_base=7)
        with self.assertRaises(ValueError):self.amend(expected_revision=True)

    def test_payment_tracks_bonus_without_changing_cap_and_rejects_overpay(self):
        self.amend()
        before=self.store.load_team('a').charges
        self.store.record_payment('a','paid','contract:v',4,expected_cash_revision=1,
            source='synthetic payment',payment_reference='payment-1',component='bonus:restructure:conversion')
        ledger=self.store.load_team('a')
        self.assertEqual(ledger.charges,before)
        self.assertEqual(ledger.guarantee_cash('v')['unpaid_signing_bonus'],4)
        self.assertEqual(ledger.cash_snapshot()['paid_total'],34)
        with self.assertRaises(ValueError):
            self.store.record_payment('a','excess','contract:v',5,expected_cash_revision=2,
                source='synthetic payment',payment_reference='payment-2',component='bonus:restructure:conversion')
        self.assertEqual(self.store.load_team('a').cash_snapshot()['paid_total'],34)

    def test_final_access_failure_and_stale_revision_roll_back_everything(self):
        before=self.store.load_team('a').financial_snapshot()
        cash=self.store.load_team('a').cash_snapshot()
        def denied():raise RuntimeError('access denied')
        with self.assertRaises(RuntimeError):self.amend(access_check=denied)
        with self.assertRaises(Rejected):self.amend(expected_revision=0)
        self.assertEqual(self.store.load_team('a').financial_snapshot(),before)
        self.assertEqual(self.store.load_team('a').cash_snapshot(),cash)
        self.assertEqual(self.amend()['financial']['revision'],2)

    def test_tampered_original_or_posting_fails_replay(self):
        self.amend()
        with closing(sqlite3.connect(self.store.path)) as db, db:
            original=db.execute("SELECT payload FROM events WHERE kind='restructure'").fetchone()[0]
        for field in ('original_contract','cash_posting','before_posting'):
            payload=json.loads(original)
            if field=='original_contract':payload[field]['offer']['signing_bonus']=11
            elif field=='cash_posting':payload[field]['paid_total']=31
            else:payload[field]['revision']=0
            with closing(sqlite3.connect(self.store.path)) as db, db:
                db.execute("UPDATE events SET payload=? WHERE kind='restructure'",(json.dumps(payload),))
            with self.assertRaises(ValueError):self.store.load_team('a')
            with closing(sqlite3.connect(self.store.path)) as db, db:
                db.execute("UPDATE events SET payload=? WHERE kind='restructure'",(original,))
        self.assertEqual(self.store.load_team('a').revision,2)

    def test_release_retains_unpaid_conversion_and_original_retry_does_not_restore_ownership(self):
        from datetime import date
        from tests import test_releases as release_fixtures
        self.amend()
        f=release_fixtures.PreseasonReleaseTests()
        plan=f.plan()
        receipt=self.store.release_preseason_veteran('a','release','v',scope=f.scope(date(2026,6,2)),
            discount=plan.discount,payment_year_offsets=(0,1,2,3,4),expected_revision=2,access_check=lambda:None)
        self.assertEqual(receipt['cash']['nominal_total'],60)
        self.assertEqual(receipt['cash']['unpaid_total'],30)
        before=self.store.load_team('a').financial_snapshot()
        self.amend()
        self.assertEqual(self.store.load_team('a').financial_snapshot(),before)
        self.assertEqual(self.store.load_team('a').guarantee_cash('v')['unpaid_signing_bonus'],8)

    def test_paid_conversion_assignment_replays_all_layers_at_seller(self):
        from tests import test_trades as trade_fixtures
        self.amend()
        self.store.record_payment('a','paid','contract:v',8,expected_cash_revision=1,
            source='synthetic payment',payment_reference='payment-1',component='bonus:restructure:conversion')
        buyer=Ledger.from_opening(OpeningBooks(),cap=200,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(2,)*5})
        self.store.create_team('b',buyer)
        self.store.initialize_cash('b',(),source='synthetic empty cash')
        self.store.trade_preseason_veteran('assign','a','b','v',scope=trade_fixtures.PreseasonTradeTests().scope(),
            seller_revision=3,buyer_revision=1,access_check=lambda:None)
        seller=self.store.load_team('a')
        buyer=self.store.load_team('b')
        self.assertEqual(seller.cash_snapshot()['nominal_total'],38)
        self.assertEqual(buyer.cash_snapshot()['nominal_total'],142)
        self.assertEqual(buyer.active_contract('v').bonus_layers,())
        self.assertEqual(seller.guarantee_cash('v')['unpaid_signing_bonus'],0)
        self.assertEqual(seller.financial_snapshot()['outgoing_trades']['v']['original_contract']['bonus_layers'][0]['amount'],8)

    def test_liability_dict_and_duplicate_exclusions_cannot_be_normalized_away(self):
        self.amend()
        with closing(sqlite3.connect(self.store.path)) as db, db:
            original=db.execute("SELECT payload FROM events WHERE kind='restructure'").fetchone()[0]
        exclusions=json.loads(original)['scope']['exclusions']
        for altered in ({key:True for key in exclusions},exclusions+[exclusions[0]]):
            payload=json.loads(original)
            payload['scope']['exclusions']=altered
            with closing(sqlite3.connect(self.store.path)) as db, db:
                db.execute("UPDATE events SET payload=? WHERE kind='restructure'",(json.dumps(payload),))
            with self.assertRaisesRegex(ValueError,'exclusion list'):self.store.load_team('a')
            with closing(sqlite3.connect(self.store.path)) as db, db:
                db.execute("UPDATE events SET payload=? WHERE kind='restructure'",(original,))

    def test_event_insert_failure_rolls_back_amendment(self):
        before=self.store.load_team('a').financial_snapshot()
        cash=self.store.load_team('a').cash_snapshot()
        with closing(sqlite3.connect(self.store.path)) as db, db:
            db.execute("CREATE TRIGGER reject_amendment BEFORE INSERT ON events WHEN NEW.kind='restructure' BEGIN SELECT RAISE(ABORT,'synthetic insert failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.amend()
        self.assertEqual(self.store.load_team('a').financial_snapshot(),before)
        self.assertEqual(self.store.load_team('a').cash_snapshot(),cash)
