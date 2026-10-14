from dataclasses import replace
from datetime import date
import copy
import unittest
from franchise.cap import Offer,Rejected
from franchise.returns import PreseasonReturnScope,RETURN_EXCLUSIONS
from franchise.generations import generation_identity
from tests import test_generation_identity,test_releases


class ReturnSigningLedgerTests(unittest.TestCase):
    def setup_ledger(self):
        fixture=test_generation_identity.ConsumedGenerationIdentityTests();fixture.setUp()
        ledger=fixture.ledger();ledger.bind_team_identity('a')
        plan=test_releases.PreseasonReleaseTests().plan()
        old=ledger.contract_identity('v').generation_id
        ledger.apply_preseason_release('v',scope=plan.scope,discount=plan.discount,
            payment_year_offsets=(0,)*5,record_id='first',expected_revision=0)
        return ledger,old,plan

    def scope(self):
        return PreseasonReturnScope(2026,date(2026,6,1),date(2026,9,10),True,RETURN_EXCLUSIONS,'synthetic verified return')

    def test_return_and_second_release_preserve_all_debt_cash_and_identity(self):
        ledger,old,plan=self.setup_ledger()
        debt=ledger.generation_accounting(old);oldcash=ledger.generation_cash(old)
        offer=Offer('v',(10,20),6,(10,0))
        receipt=ledger.return_sign('return',offer,1,scope=self.scope())
        identity=generation_identity('a','v','return')
        self.assertEqual(ledger.contract_identity('v'),identity)
        self.assertEqual(ledger.generation_cash(identity.generation_id).amount,36)
        self.assertEqual(ledger.generation_cash(old),oldcash)
        self.assertIs(ledger.generation_accounting(old),debt)
        self.assertEqual(ledger._charges[0],sum(debt.annual_charges()[:1])+13)
        self.assertEqual(ledger.guarantee_cash('v')['unpaid_signing_bonus'],6)
        self.assertEqual(ledger.generation_guarantee_cash(old)['unpaid_signing_bonus'],0)
        ledger.bind_team_identity('a')
        self.assertEqual(ledger.return_sign('return',offer,-1,scope=self.scope()),receipt)
        with self.assertRaises(Rejected):ledger.return_sign('return',offer,2,scope=replace(self.scope(),source='changed'))
        with self.assertRaises(Rejected):ledger.apply_preseason_trade_out('v',scope=None,record_id='x',expected_revision=2)
        with self.assertRaises(ValueError):ledger.apply_preseason_restructure('v',scope=None,converted_base=2,record_id='x',expected_revision=2)
        before=copy.deepcopy(ledger.generation_snapshot())
        with self.assertRaisesRegex(Rejected,'identity already exists'):
            ledger.apply_preseason_release('v',scope=plan.scope,discount=plan.discount,
                payment_year_offsets=(0,0),record_id='first',expected_revision=2)
        self.assertEqual(ledger.generation_snapshot(),before)
        ledger.apply_preseason_release('v',scope=plan.scope,discount=plan.discount,
            payment_year_offsets=(0,0),record_id='second',expected_revision=2)
        self.assertEqual(len(ledger.generation_agreements()),2)
        self.assertEqual(ledger.generation_accounting(identity.generation_id).status,'released')
        self.assertEqual(ledger.generation_cash(old),oldcash)
        with self.assertRaises(Rejected):ledger.sign('ordinary',offer,3)

    def test_failures_leave_all_money_archives_requests_unchanged(self):
        for scenario in ('stale','cap','floor','unknowncash','year','date','request'):
            with self.subTest(scenario=scenario):
                ledger,old,_=self.setup_ledger();scope=self.scope();offer=Offer('v',(10,20),6)
                revision=1;request='return'
                if scenario=='stale':revision=0
                if scenario=='cap':offer=Offer('v',(200,),0)
                if scenario=='floor':offer=Offer('v',(1,),0)
                if scenario=='unknowncash':ledger._cash=None
                if scenario=='year':scope=replace(scope,league_year=2027,signed_on=date(2027,6,1),first_regular_season_game=date(2027,9,10))
                if scenario=='date':scope=replace(scope,signed_on=date(2026,5,1))
                if scenario=='request':request=''
                before=copy.deepcopy((ledger.generation_snapshot(),ledger._requests))
                with self.assertRaises((Rejected,ValueError)):ledger.return_sign(request,offer,revision,scope=scope)
                self.assertEqual((ledger.generation_snapshot(),ledger._requests),before)

    def test_scope_explicit_and_id_framing(self):
        scope=self.scope()
        for changes in ({'healthy':False},{'healthy':1},{'exclusions':frozenset()},
                        {'signed_on':scope.first_regular_season_game},{'league_year':True}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):replace(scope,**changes)
        self.assertNotEqual(generation_identity('a:b','c','d'),generation_identity('a','b:c','d'))
        self.assertNotEqual(generation_identity('a','v','one'),generation_identity('a','v','two'))

    def test_assigned_return_preserves_seller_cash_and_unpaid_base_assignment(self):
        from franchise.books import OpeningBooks
        from franchise.cap import Ledger
        from franchise.cash import CashBook
        from tests import test_trades
        fixture=test_trades.PreseasonTradeTests();plan=fixture.plan()
        ledger=Ledger.from_opening(OpeningBooks(contracts=(plan.original_contract,)),cap=200,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3})
        ledger._cash=CashBook((plan.original_cash,),'synthetic');ledger.bind_team_identity('a')
        old=ledger.contract_identity('v').generation_id
        ledger.apply_preseason_trade_out('v',scope=plan.scope,record_id='trade',expected_revision=0)
        oldcash=ledger.generation_cash(old)
        scope=replace(self.scope(),signed_on=plan.scope.traded_on)
        ledger.return_sign('return',Offer('v',(10,),0),1,scope=scope)
        self.assertEqual(ledger.generation_cash(old),oldcash)
        self.assertEqual(ledger.generation_accounting(old).status,'assigned')
        self.assertEqual(ledger.generation_guarantee_cash(old)['unpaid_signing_bonus'],0)
        self.assertEqual(ledger.generation_accounting(old).payment_ceilings()['base:0'],0)
        self.assertEqual(ledger._charges[0],19)
