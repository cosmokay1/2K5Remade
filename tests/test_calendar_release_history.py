"""Whole Store lifecycle chains retain original bonus and assignment economics."""
from datetime import date
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from franchise.books import ActiveContract,OpeningBooks
from franchise.cap import Ledger,Offer
from franchise.cash import CashObligation
from franchise.guarantees import DiscountProfile
from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
from franchise.restructures import PreseasonRestructureScope,EXCLUDED_RESTRUCTURE_TERMS
from franchise.trades import PreseasonTradeScope,EXCLUDED_TRADE_LIABILITIES
from franchise.salary_rules import VeteranMinimumProfile
from franchise.store import FranchiseStore


class CalendarReleaseHistoryTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'history.sqlite';self.store=FranchiseStore(self.path)

    def profile(self,year):
        return VeteranMinimumProfile(year,(('v',(7,7,7),('active_inactive',)*3),))

    def create(self,team,contract=None):
        profile=self.profile(2026)
        self.store.create_team(team,Ledger.from_opening(OpeningBooks(contracts=(contract,) if contract else ()),
            cap=20000000,roster_reserve=0,max_bonus_years=5,veteran_minimums=profile.floors(),veteran_minimum_profile=profile))
        records=(CashObligation('contract:v','v',contract.nominal_cash,3000000,
            'synthetic paid original bonus',(('signing_bonus',3000000),)),) if contract else ()
        self.store.initialize_cash(team,records,source='synthetic complete allocated cash')

    def pay(self,team,component,amount):
        ledger=self.store.load_team(team)
        self.store.record_payment(team,component,ledger.contract_cash_id('v'),amount,
            expected_cash_revision=ledger.cash_snapshot()['revision'],source='synthetic payroll evidence',
            payment_reference=team+component,component=component)

    def roll(self,teams,from_year):
        inputs={team:dict(expected_revision=self.store.load_team(team).revision,next_cap=20000000,
            next_cap_source='synthetic cap',roster_reserve=0,reserve_source='synthetic reserve',
            next_minimum_profile=self.profile(from_year+1).to_dict(),expired_generation_ids=[],
            exclusions=sorted(FranchiseStore.YEAR_TRANSITION_EXCLUSIONS),source='synthetic reconciled closing') for team in teams}
        self.store.advance_league_year(request_id='roll-'+str(from_year),from_year=from_year,to_year=from_year+1,
            source='synthetic common league transition',teams=inputs)

    def anchor(self,teams):
        self.store.anchor_calendar(request_id='anchor',league_year=2026,source='synthetic calendar',
            expected_revisions={team:self.store.load_team(team).revision for team in teams})
        self.store.migrate_generations(self.path)

    def release(self,team):
        ledger=self.store.load_team(team)
        return self.store.release_calendar_preseason_veteran(team,'later-release','v',
            generation_id=ledger.contract_identity('v').generation_id,
            scope=PreseasonReleaseScope(2027,date(2027,7,1),date(2027,9,10),EXCLUDED_LIABILITIES,
                True,True,0,'synthetic healthy calendar release'),
            discount=DiscountProfile(2027,Fraction(0),'synthetic zero rate'),payment_year_offsets=(0,1),
            expected_revision=ledger.revision,access_check=lambda:None)

    def test_restructured_bonus_and_earned_base_survive_release_restart_and_second_roll(self):
        self.create('a',ActiveContract(Offer('v',(2000000,)*3,3000000,(2000000,0,0)),'synthetic original'))
        self.store.restructure_preseason_veteran('a','conversion','v',converted_base=100000,
            scope=PreseasonRestructureScope(2026,date(2026,6,1),date(2026,9,10),0,True,True,True,
                EXCLUDED_RESTRUCTURE_TERMS,self.profile(2026).source,'synthetic guaranteed conversion'),
            expected_revision=1,access_check=lambda:None)
        self.pay('a','bonus:restructure:conversion',100000);self.pay('a','base:0',1900000)
        self.anchor(('a',));gid=self.store.load_team('a').contract_identity('v').generation_id
        original=self.store.load_team('a').generation_accounting(gid)
        self.roll(('a',),2026);self.release('a')
        self.store=FranchiseStore(self.path);ledger=self.store.load_team('a')
        released=ledger.generation_accounting(gid)
        self.assertEqual(released.original_contract,original.original_contract)
        self.assertEqual(released.contract,original.contract)
        self.assertEqual(released.restructure,original.restructure)
        self.assertEqual(released.release.original_contract.elapsed_years,1)
        self.assertEqual(ledger.charges,(Fraction(3100000,3),)*2)
        self.assertEqual(ledger.cash_snapshot()['nominal_total'],5000000)
        self.assertEqual(ledger.cash_snapshot()['paid_total'],5000000)
        before=self.store.calendar_contract_context('a',gid,context_format='calendar_v2')
        self.roll(('a',),2027)
        after=FranchiseStore(self.path).calendar_contract_context('a',gid,context_format='calendar_v2')
        self.assertEqual(after['economic_archive'],before['economic_archive'])
        self.assertEqual(after['calendar_accounting']['annual_charges'],before['calendar_accounting']['annual_charges'][1:])

    def test_assigned_base_guarantees_remain_separate_from_seller_bonus_debt(self):
        self.create('a',ActiveContract(Offer('v',(2000000,)*3,3000000,(0,2000000,1000000)),'synthetic original'))
        self.create('b')
        self.store.trade_preseason_veteran('assignment','a','b','v',
            scope=PreseasonTradeScope(2026,date(2026,6,2),date(2026,9,10),date(2026,9,10),
                EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'synthetic consenting assignment'),
            seller_revision=1,buyer_revision=1,access_check=lambda:None)
        self.pay('b','base:0',2000000);self.anchor(('a','b'))
        gid=self.store.load_team('b').contract_identity('v').generation_id
        original=self.store.load_team('b').generation_accounting(gid)
        self.roll(('a','b'),2026);seller=self.store.load_team('a').financial_snapshot()
        self.release('b');self.store=FranchiseStore(self.path)
        buyer=self.store.load_team('b');released=buyer.generation_accounting(gid)
        self.assertEqual(released.incoming_trade,original.incoming_trade)
        self.assertEqual(released.contract,original.contract)
        self.assertEqual(released.contract.offer.signing_bonus,0)
        self.assertEqual(buyer.charges,(3000000,0))
        self.assertEqual(buyer.cash_snapshot()['nominal_total'],5000000)
        self.assertEqual(buyer.cash_snapshot()['paid_total'],2000000)
        self.assertEqual(self.store.load_team('a').financial_snapshot(),seller)
        self.assertEqual(self.store.load_team('a').charges,(2000000,0))
        self.pay('b','base:1',2000000);self.roll(('a','b'),2027)
        reopened=FranchiseStore(self.path)
        self.assertEqual(reopened.load_team('a').charges,(0,))
        self.assertEqual(reopened.load_team('b').charges,(0,))
        self.assertEqual(reopened.load_team('b').cash_snapshot()['unpaid_total'],1000000)
