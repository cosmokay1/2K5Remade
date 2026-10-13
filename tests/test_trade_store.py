from datetime import date
from pathlib import Path
import json
import sqlite3
from contextlib import closing
import tempfile
import unittest
from franchise.books import ActiveContract,OpeningBooks
from franchise.cap import Ledger,Offer,Rejected
from franchise.cash import CashObligation
from franchise.control import AccessDisabled
from franchise.trades import PreseasonTradeScope,EXCLUDED_TRADE_LIABILITIES
from franchise.store import FranchiseStore


class TradeStoreTests(unittest.TestCase):
    def setup_store(self,directory,*,buyer_cap=100,bonus=9,seller_cap=30):
        store=FranchiseStore(Path(directory)/'trade.sqlite')
        contract=ActiveContract(Offer('v',(10,20,30),bonus,(0,20,10)),'fixture original')
        for team in ('a','b','c'):
            store.create_team(team,Ledger.from_opening(OpeningBooks(contracts=(contract,)) if team=='a' else OpeningBooks(),
                cap=seller_cap if team=='a' else buyer_cap,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3,'free':(1,)}))
            records=(CashObligation('contract:v','v',60+bonus,bonus,'fixture paidbonus',(('signing_bonus',bonus),)),) if team=='a' else ()
            store.initialize_cash(team,records,source='fixture complete cash')
        return store

    def trade(self,store,request='assignment',seller='a',buyer='b',seller_revision=1,buyer_revision=1,check=lambda:None):
        scope=PreseasonTradeScope(2026,date(2026,6,1),date(2026,9,10),date(2026,9,11),
            EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'fixture supported assignment')
        return store.trade_preseason_veteran(request,seller,buyer,'v',scope=scope,seller_revision=seller_revision,
                                             buyer_revision=buyer_revision,access_check=check)

    def states(self,store):
        return {team:(store.load_team(team).financial_snapshot(),store.load_team(team).cash_snapshot()) for team in ('a','b','c')}

    def test_atomic_assignment_replays_and_retries_with_guarantees_and_cash_conserved(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            result=self.trade(store)
            reopened=FranchiseStore(store.path)
            self.assertEqual(self.trade(reopened),result)
            seller,buyer=reopened.load_team('a'),reopened.load_team('b')
            self.assertEqual(seller.charges,(9,0,0))
            self.assertEqual(buyer.charges,(10,20,30))
            self.assertEqual(seller.cash_snapshot()['nominal_total']+buyer.cash_snapshot()['nominal_total'],69)
            self.assertEqual(seller.cash_snapshot()['unpaid_total'],0)
            self.assertEqual(buyer.cash_snapshot()['unpaid_total'],60)
            self.assertEqual(buyer.contract_terms('v')['guaranteed_salaries'],[0,20,10])
            self.assertEqual(seller.guarantee_cash('v')['unpaid_guaranteed_base_by_original_year'],[0,0,0])
            self.assertEqual(seller.financial_snapshot()['signed_players'],[])
            self.assertEqual(buyer.financial_snapshot()['signed_players'],['v'])
            self.assertEqual((seller.revision,buyer.revision),(2,2))

    def test_stale_affordability_and_final_access_rejection_commit_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            before=self.states(store)
            for inputs in ({'seller_revision':0},{'buyer_revision':0}):
                with self.assertRaises(Rejected):self.trade(store,**inputs)
            def disabled():raise AccessDisabled('fixture shutdown')
            with self.assertRaises(AccessDisabled):self.trade(store,check=disabled)
            self.assertEqual(self.states(FranchiseStore(store.path)),before)
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory,buyer_cap=9)
            before=self.states(store)
            with self.assertRaises(Rejected):self.trade(store)
            self.assertEqual(self.states(store),before)

    def test_partial_database_failure_rolls_back_owner_and_first_event(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            before=self.states(store)
            with closing(sqlite3.connect(store.path)) as db:
                db.execute("CREATE TRIGGER reject_in BEFORE INSERT ON events WHEN NEW.kind='trade_in' BEGIN SELECT RAISE(ABORT,'fixture reject'); END")
                db.commit()
            with self.assertRaises(sqlite3.IntegrityError):self.trade(store)
            self.assertEqual(self.states(FranchiseStore(store.path)),before)
            with closing(sqlite3.connect(store.path)) as db:
                self.assertEqual(db.execute("SELECT team_id FROM ownership WHERE player_id='v'").fetchone(),('a',))
                self.assertEqual(db.execute("SELECT count(*) FROM events WHERE kind LIKE 'trade_%'").fetchone()[0],0)

    def test_competing_buyer_conflicting_retry_and_three_club_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            original=self.trade(store)
            with self.assertRaises(Rejected):self.trade(store,buyer='c')
            with self.assertRaises(Rejected):self.trade(store,request='competing',buyer='c',seller_revision=2)
            self.trade(store,request='second',seller='b',buyer='c',seller_revision=2)
            reopened=FranchiseStore(store.path)
            self.assertEqual(reopened.load_team('c').financial_snapshot()['signed_players'],['v'])
            self.assertEqual(reopened.load_team('a').charges,(9,0,0))
            self.assertEqual(reopened.load_team('b').charges,(0,0,0))
            self.assertEqual(sum(reopened.load_team(team).cash_snapshot()['nominal_total'] for team in ('a','b','c')),69)
            before=self.states(reopened)
            self.assertEqual(self.trade(reopened),original)
            self.assertEqual(self.states(reopened),before)
            with self.assertRaises(Rejected):self.trade(reopened,request='return',seller='c',buyer='a',seller_revision=2,buyer_revision=2)

    def test_missing_or_identically_forged_paired_source_rejects_recipient_read(self):
        for corruption in ('missing','same-source'):
            with self.subTest(corruption=corruption),tempfile.TemporaryDirectory() as directory:
                store=self.setup_store(directory)
                self.trade(store)
                with closing(sqlite3.connect(store.path)) as db:
                    if corruption=='missing':db.execute("DELETE FROM events WHERE kind='trade_out'")
                    else:
                        for event_id,text in db.execute("SELECT id,payload FROM events WHERE kind LIKE 'trade_%'").fetchall():
                            # Forge both source fields and all derived archive strings,
                            # so recipient-only replay would be internally consistent.
                            forged=text.replace('fixture original','invented source')
                            db.execute('UPDATE events SET payload=? WHERE id=?',(forged,event_id))
                    db.commit()
                with self.assertRaises(ValueError):FranchiseStore(store.path).load_team('b')

    def test_seller_acceleration_over_cap_still_retains_obligation(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory,bonus=90,seller_cap=45)
            self.trade(store)
            seller=FranchiseStore(store.path).load_team('a')
            self.assertEqual(seller.charges,(90,0,0))
            self.assertEqual(seller.room,-45)
            with self.assertRaises(Rejected):store.sign('a','new',Offer('free',(1,),0),2)

    def test_assigned_cash_payments_belong_to_buyer_without_changing_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            receipt=self.trade(store)
            before_a=store.load_team('a').financial_snapshot()
            before_b=store.load_team('b').financial_snapshot()
            with self.assertRaises(Rejected):
                store.record_payment('a','wrong-club','contract:v',1,expected_cash_revision=1,
                    source='fixture bank',payment_reference='wrong-club',component='base:0')
            store.record_payment('b','assigned-payment','contract:v',5,expected_cash_revision=1,
                source='fixture bank',payment_reference='assigned-payment',component='base:0')
            reopened=FranchiseStore(store.path)
            self.assertEqual(reopened.load_team('a').financial_snapshot(),before_a)
            self.assertEqual(reopened.load_team('b').charges,tuple(before_b['charges']))
            self.assertEqual(reopened.load_team('b').cash_snapshot()['unpaid_total'],55)
            self.assertEqual(self.trade(reopened),receipt)
            self.assertEqual(reopened.load_team('b').revision,3)

    def test_buyer_release_retains_guarantees_without_original_seller_bonus(self):
        from fractions import Fraction
        from franchise.guarantees import DiscountProfile
        from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            original=self.trade(store)
            scope=PreseasonReleaseScope(2026,date(2026,6,2),date(2026,9,11),EXCLUDED_LIABILITIES,
                True,True,0,'fixture later buyer release')
            store.release_preseason_veteran('b','buyer-release','v',scope=scope,
                discount=DiscountProfile(2026,Fraction(0),'synthetic zero rate'),payment_year_offsets=(0,1,2),
                expected_revision=2,access_check=lambda:None)
            reopened=FranchiseStore(store.path)
            self.assertEqual(reopened.load_team('a').charges,(9,0,0))
            self.assertEqual(reopened.load_team('b').charges,(30,0,0))
            self.assertEqual(reopened.load_team('b').cash_snapshot()['unpaid_total'],30)
            self.assertEqual(sum(reopened.load_team(team).cash_snapshot()['nominal_total'] for team in ('a','b','c')),39)
            self.assertEqual(reopened.load_team('b').financial_snapshot()['signed_players'],[])
            revision=reopened.load_team('b').cash_snapshot()['revision']
            reopened.record_payment('b','protected-after-release','contract:v',5,expected_cash_revision=revision,
                source='fixture bank',payment_reference='protected-after-release',component='base:1')
            before=self.states(reopened)
            self.assertEqual(self.trade(reopened),original)
            self.assertEqual(self.states(FranchiseStore(store.path)),before)
            self.assertEqual(reopened.load_team('b').cash_snapshot()['unpaid_total'],25)

    def test_incoming_assignment_establishes_chronology_for_later_release(self):
        from fractions import Fraction
        from franchise.guarantees import DiscountProfile
        from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            self.trade(store)
            before=self.states(store)
            for year,day in ((2026,date(2026,5,31)),(2027,date(2027,6,1))):
                scope=PreseasonReleaseScope(year,day,date(year,9,11),EXCLUDED_LIABILITIES,
                    True,True,0,'fixture contradictory later release')
                with self.assertRaises(Rejected):
                    store.release_preseason_veteran('b','wrong-'+str(year),'v',scope=scope,
                        discount=DiscountProfile(year,Fraction(0),'synthetic zero'),payment_year_offsets=(0,1,2),
                        expected_revision=2,access_check=lambda:None)
            self.assertEqual(self.states(FranchiseStore(store.path)),before)

    def test_paired_retry_still_revalidates_unrequested_team_history(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.setup_store(directory)
            self.trade(store)
            with closing(sqlite3.connect(store.path)) as db:
                row=db.execute("SELECT id,payload FROM events WHERE team_id='c' AND kind='cash_open'").fetchone()
                payload=json.loads(row[1])
                payload['cash_posting']['unpaid_total']=1
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),row[0]))
                db.commit()
            with self.assertRaisesRegex(ValueError,'cash posting'):
                self.trade(FranchiseStore(store.path))
