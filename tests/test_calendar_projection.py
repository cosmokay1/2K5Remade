from datetime import date
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from franchise.books import ActiveContract, BonusLayer, OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.cash import CashObligation
from franchise.generations import GenerationAgreement, legacy_identity, project_agreement
from franchise.guarantees import DiscountProfile
from franchise.releases import PreseasonReleaseScope, EXCLUDED_LIABILITIES, calculate_preseason_release
from franchise.store import FranchiseStore


class CalendarProjectionTests(unittest.TestCase):
    def test_closing_inspection_keeps_unknown_cash_unknown_and_paid_expiry_unapproved(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FranchiseStore(Path(directory)/'closing.sqlite')
            contract = ActiveContract(Offer('p',(10,),0),'synthetic one-year agreement')
            store.create_team('a',Ledger.from_opening(OpeningBooks(contracts=(contract,)),
                cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={'p':(1,)}))
            store.anchor_calendar(request_id='year',league_year=2026,source='synthetic year',expected_revisions={'a':0})
            unknown = store.calendar_closing_state('a')['agreements'][0]
            self.assertIsNone(unknown['recorded_base_settled'])
            self.assertIsNone(unknown['unpaid_nominal_cash'])
            self.assertTrue(unknown['scheduled_term_ends_after_year'])
            store.initialize_cash('a',(CashObligation('contract:p','p',10,10,'synthetic payroll',(('base:0',10),)),),source='synthetic complete cash')
            paid = store.calendar_closing_state('a')['agreements'][0]
            self.assertTrue(paid['recorded_base_settled'])
            self.assertTrue(paid['all_nominal_cash_recorded_paid'])
            self.assertFalse(paid['expiry_authorized'])
            self.assertIn('p',store.load_team('a').financial_snapshot()['signed_players'])

    def contract(self):
        return ActiveContract(Offer('p',(10,20,30),9,(5,10,0)), 'synthetic agreement',
            bonus_layers=(BonusLayer('conversion',6,1,2,'synthetic original layer'),))

    def test_projected_bonus_layers_expiry_and_cash_preserve_stored_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'league.sqlite'
            store = FranchiseStore(path)
            contract = ActiveContract(Offer('p',(10,20,30),9,(5,10,0)), 'synthetic agreement')
            store.create_team('a', Ledger.from_opening(OpeningBooks(contracts=(contract,)),
                cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={'p':(1,1,1)}))
            store.initialize_cash('a',(CashObligation('contract:p','p',69,0,'synthetic cash',()),),source='synthetic cash coverage')
            revision = store.load_team('a').revision
            store.anchor_calendar(request_id='year',league_year=2026,source='synthetic year',expected_revisions={'a':revision})
            raw = path.read_bytes()
            closing = store.calendar_closing_state('a')
            self.assertFalse(closing['revenue_gate'])
            self.assertTrue(closing['normal_payroll_owner_funded'])
            self.assertFalse(closing['agreements'][0]['recorded_base_settled'])
            self.assertEqual(closing['agreements'][0]['required_past_and_outgoing_base'],{'base:0':10})
            self.assertFalse(closing['agreements'][0]['expiry_authorized'])
            projected = store.calendar_projection('a',target_year=2027)
            self.assertEqual(projected['modeled_remaining_charges'],[23,33])
            self.assertEqual(projected['agreements'][0]['remaining_charges'],[23,33])
            self.assertEqual(projected['agreements'][0]['projected_original_year_index'],1)
            self.assertEqual(projected['unchanged_cash']['unpaid_total'],69)
            expired = store.calendar_projection('a',target_year=2029)
            self.assertTrue(expired['agreements'][0]['scheduled_term_complete'])
            self.assertEqual(expired['modeled_remaining_charges'],[])
            self.assertEqual(expired['unchanged_cash']['unpaid_total'],69)
            self.assertFalse(expired['ownership_changed'])
            self.assertEqual(store.load_team('a').active_contract('p'),contract)
            self.assertEqual(path.read_bytes(),raw)
            with self.assertRaises(Rejected): store.calendar_projection('a',target_year=2025)

    def test_closed_projection_never_restores_cancelled_base_payment_rights(self):
        contract = self.contract()
        cash = CashObligation('contract:p','p',75,15,'synthetic paid bonuses',
                              (('signing_bonus',9),('bonus:conversion',6)))
        scope = PreseasonReleaseScope(2026,date(2026,7,1),date(2026,9,1),
            EXCLUDED_LIABILITIES,True,True,0,'synthetic healthy release')
        release = calculate_preseason_release(contract,cash,scope=scope,
            discount=DiscountProfile(2026,Fraction(0),'synthetic explicit zero rate'),
            payment_year_offsets=(0,1,2),record_id='release')
        agreement = GenerationAgreement(legacy_identity('a','p'),contract,contract,release=release)
        original = agreement.payment_ceilings()
        next_year = project_agreement(agreement,years_forward=1)
        self.assertEqual(next_year['remaining_charges'],[12])
        self.assertEqual(next_year['unchanged_payment_ceilings'],original)
        projected = project_agreement(agreement,years_forward=2)
        self.assertEqual(projected['remaining_charges'],[])
        self.assertEqual(projected['unchanged_payment_ceilings'],original)
        self.assertEqual(original['base:0'],5)
        self.assertEqual(original['base:2'],0)
        self.assertEqual(agreement.release.original_contract,contract)
        self.assertEqual(agreement.release.cash_obligation.amount,30)

    def test_assignment_projections_keep_seller_debt_and_buyer_base_separate(self):
        from franchise.trades import PreseasonTradeScope, EXCLUDED_TRADE_LIABILITIES, calculate_preseason_trade
        contract = self.contract()
        cash = CashObligation('contract:p','p',75,15,'synthetic paid bonuses',
                              (('signing_bonus',9),('bonus:conversion',6)))
        scope = PreseasonTradeScope(2026,date(2026,7,1),date(2026,9,1),date(2026,9,1),
            EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'synthetic eligible assignment')
        plan = calculate_preseason_trade(contract,cash,scope=scope,record_id='assignment')
        seller = GenerationAgreement(legacy_identity('a','p'),contract,contract,outgoing_trade=plan)
        buyer = GenerationAgreement(legacy_identity('b','p'),plan.buyer_contract,plan.buyer_contract,incoming_trade=plan)
        seller_next = project_agreement(seller,years_forward=1)
        buyer_next = project_agreement(buyer,years_forward=1)
        self.assertEqual(seller_next['remaining_charges'],[12])
        self.assertEqual(buyer_next['remaining_charges'],[20,30])
        self.assertEqual(seller_next['unchanged_payment_ceilings']['base:1'],0)
        self.assertEqual(buyer_next['unchanged_payment_ceilings']['base:1'],20)
        self.assertEqual(plan.seller_cash.amount,15)
        self.assertEqual(plan.buyer_cash.amount,60)
