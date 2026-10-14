from contextlib import closing
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import sqlite3
import tempfile
import unittest
from franchise.books import ActiveContract, ChargeRecord, OpeningBooks
from franchise.cap import Ledger, Offer
from franchise.store import FranchiseStore
from tests import test_restructures, test_releases, test_trade_store, test_rookie_opening


class ContractGenerationViewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture=test_restructures.PreseasonRestructureTests()
        self.store=FranchiseStore(Path(self.temp.name)/'state.sqlite')
        self.store.create_team('a',Ledger.from_opening(OpeningBooks(contracts=(self.fixture.contract(),)),
            cap=200,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(2,)*5,'unsigned':(1,)}))
        self.store.initialize_cash('a',(self.fixture.cash(),),source='synthetic allocated cash')

    def test_identity_survives_amendment_payment_release_and_restart(self):
        original=self.store.contract_generations('a')
        identity=original['generations'][0]['generation_id']
        expected='legacy-contract:'+hashlib.sha256(b'["a","v"]').hexdigest()
        self.assertEqual(identity,expected)
        self.assertEqual(original['generations'][0]['status'],'active')
        self.store.restructure_preseason_veteran('a','conversion','v',scope=self.fixture.scope(),
            converted_base=8,expected_revision=1,access_check=lambda:None)
        self.store.record_payment('a','paid','contract:v',4,expected_cash_revision=1,
            source='synthetic payment',payment_reference='receipt-1',component='bonus:restructure:conversion')
        changed=self.store.contract_generations('a')
        self.assertEqual(changed['generations'][0]['generation_id'],identity)
        self.assertEqual((changed['financial_revision'],changed['cash_revision']),(3,2))
        self.assertEqual(changed['generations'][0]['cash_obligation']['paid'],34)
        release=test_releases.PreseasonReleaseTests().plan()
        self.store.release_preseason_veteran('a','release','v',scope=release.scope,discount=release.discount,
            payment_year_offsets=(0,)*5,expected_revision=3,access_check=lambda:None)
        closed=self.store.contract_generations('a')
        generation=closed['generations'][0]
        self.assertEqual(generation['generation_id'],identity)
        self.assertEqual(generation['status'],'released')
        self.assertEqual([record['annual_charges'] for record in generation['retained_records']],[[14],[22]])
        self.assertEqual(generation['contract']['bonus_layers'][0]['amount'],8)
        self.assertEqual(FranchiseStore(self.store.path).contract_generations('a'),closed)

    def test_assignment_identity_is_team_specific_and_closed_debt_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=test_trade_store.TradeStoreTests()
            store=fixture.setup_store(directory)
            seller_id=store.contract_generations('a')['generations'][0]['generation_id']
            fixture.trade(store)
            seller=store.contract_generations('a')['generations'][0]
            buyer=store.contract_generations('b')['generations'][0]
            self.assertEqual(seller['generation_id'],seller_id)
            self.assertNotEqual(seller['generation_id'],buyer['generation_id'])
            self.assertEqual((seller['status'],buyer['status']),('assigned','active'))
            self.assertEqual(seller['retained_records'][0]['annual_charges'],[9])
            self.assertEqual(buyer['retained_records'],[])

    def test_delimiter_containing_identities_remain_distinct_without_guessed_association(self):
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            identities=(('a:b','c'),('a','b:c'),('a\0b','c2'),('a2','b\0c2'))
            found=[]
            for team,player in identities:
                books=OpeningBooks(contracts=(ActiveContract(Offer(player,(10,),0),'synthetic contract'),),
                    retained=(ChargeRecord('unmapped-debt',(Fraction(1,3),2),'synthetic imported debt'),),
                    adjustments=(ChargeRecord('unmapped-adjustment',(-1,),'synthetic imported credit'),))
                store.create_team(team,Ledger.from_opening(books,cap=100,roster_reserve=0,max_bonus_years=5,
                    veteran_minimums={player:(1,)}))
                view=store.contract_generations(team)
                self.assertIsNone(view['cash_revision'])
                self.assertIsNone(view['generations'][0]['cash_obligation'])
                self.assertEqual(view['unassigned_opening']['retained'][0]['annual_charges'],['1/3',2])
                self.assertEqual(view['unassigned_opening']['adjustments'][0]['annual_charges'],[-1])
                self.assertEqual(view['generations'][0]['retained_records'],[])
                found.append(view['generations'][0]['generation_id'])
            self.assertEqual(len(set(found)),len(identities))

    def test_read_does_not_write_and_each_fresh_read_rejects_corrupt_source(self):
        before=self.store.load_team('a').financial_snapshot()
        with closing(sqlite3.connect(self.store.path)) as db:
            initial=(db.execute('SELECT count(*) FROM events').fetchone()[0],db.execute('PRAGMA user_version').fetchone()[0])
        view=self.store.contract_generations('a')
        self.assertEqual([item['player_id'] for item in view['generations']],['v'])
        self.assertEqual(self.store.load_team('a').financial_snapshot(),before)
        with closing(sqlite3.connect(self.store.path)) as db:
            self.assertEqual((db.execute('SELECT count(*) FROM events').fetchone()[0],db.execute('PRAGMA user_version').fetchone()[0]),initial)
            row=db.execute("SELECT id,payload FROM events WHERE kind='cash_open'").fetchone()
            corrupted=json.loads(row[1]);corrupted['cash_posting']['paid_total']=0
            db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(corrupted),row[0]));db.commit()
        with self.assertRaises(ValueError):
            self.store.contract_generations('a')

    def test_prior_cohort_contract_remains_visible_without_guessed_generation_or_status(self):
        from franchise.rookie_opening import RookiePoolOpening
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            prior=ActiveContract(Offer('u',(10,)*3,1),'synthetic prior signed UDFA')
            profile=RookiePoolOpening(2026,frozenset({'d','u','n'}),30,100,3,'synthetic cohort',(prior,))
            books=OpeningBooks(retained=(ChargeRecord('rookie-prior:u',(1,),'synthetic bonus settlement'),))
            ledger=test_rookie_opening.RookieOpeningTests().ledger(books,profile)
            store.create_team('a',ledger)
            view=store.contract_generations('a')
            self.assertEqual(view['generations'],[])
            self.assertEqual(view['unassigned_prior_cohort_contracts'],[prior.to_dict()])
            self.assertEqual(view['unassigned_opening']['retained'][0]['record_id'],'rookie-prior:u')
            self.assertNotIn('status',view['unassigned_prior_cohort_contracts'][0])
            self.assertNotIn('generation_id',view['unassigned_prior_cohort_contracts'][0])

    def test_unassigned_cash_is_preserved_and_unknown_distinct_from_empty(self):
        from franchise.cash import CashObligation
        store=FranchiseStore(Path(self.temp.name)/'unassigned.sqlite')
        store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={}))
        self.assertIsNone(store.contract_generations('a')['unassigned_cash_obligations'])
        extra=CashObligation('settlement:old','retired-player',40,5,'synthetic settlement record',(('settlement',5),))
        store.initialize_cash('a',(extra,),source='synthetic cash coverage')
        view=store.contract_generations('a')
        self.assertEqual(view['generations'],[])
        self.assertEqual(view['unassigned_cash_obligations'],[extra.to_dict()])
        self.assertEqual(self.store.contract_generations('a')['unassigned_cash_obligations'],[])

    def test_unsigned_tenders_are_not_fabricated_contract_generations(self):
        from franchise.books import RookieTender
        from franchise.rookie_opening import RookiePoolOpening
        registry=test_rookie_opening.RookieOpeningTests().registry()
        profile=RookiePoolOpening(2026,frozenset(registry),30,100,3,'synthetic cohort',())
        store=FranchiseStore(Path(self.temp.name)/'tenders.sqlite')
        store.create_team('a',Ledger.from_opening(OpeningBooks(tenders=(RookieTender('d',10),)),
            cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={},rookies=registry,
            rookie_pool_opening=profile))
        view=store.contract_generations('a')
        self.assertEqual(view['generations'],[])
        self.assertEqual(view['unsigned_tenders'],[{'player_id':'d','amount':10}])
