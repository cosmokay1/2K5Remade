from dataclasses import replace,FrozenInstanceError
from fractions import Fraction
import unittest
from franchise.books import ActiveContract,OpeningBooks
from franchise.cap import Ledger,Offer,Rejected
from franchise.cash import CashBook,CashObligation
from franchise.generations import assignment_identity,generation_identity
from tests import test_releases,test_trades,test_restructures,test_return_sign_ledger


class AssignmentGenerationTests(unittest.TestCase):
    def buyer(self,team,cap=200):
        ledger=Ledger.from_opening(OpeningBooks(),cap=cap,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3})
        ledger._cash=CashBook((),'synthetic complete cash');ledger.bind_team_identity(team)
        return ledger

    def source(self):
        ledger=Ledger.from_opening(OpeningBooks(contracts=(ActiveContract(Offer('v',(10,20,30),9,(0,20,10)),'synthetic original'),)),
            cap=200,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3})
        ledger._cash=CashBook((CashObligation('contract:v','v',69,9,'synthetic original paid bonus',(('signing_bonus',9),)),),'synthetic complete')
        ledger.bind_team_identity('a');old=ledger.contract_identity('v').generation_id
        release=test_releases.PreseasonReleaseTests().plan()
        ledger.apply_preseason_release('v',scope=release.scope,discount=release.discount,payment_year_offsets=(0,)*3,record_id='release',expected_revision=0)
        ledger.return_sign('return',Offer('v',(5,5,5),3,(5,0,0)),1,scope=test_return_sign_ledger.ReturnSigningLedgerTests().scope())
        returned=ledger.contract_identity('v').generation_id
        ledger._cash.records[returned]=replace(ledger.generation_cash(returned),paid=3,paid_components=(('signing_bonus',3),))
        return ledger,old,returned

    def transfer(self,seller,buyer,request):
        source=seller.contract_identity('v').generation_id
        target=assignment_identity(buyer._team_identity,'v',request)
        plan=seller.apply_preseason_trade_out('v',scope=test_trades.PreseasonTradeTests().scope(),record_id='trade:'+request,
            expected_revision=seller.revision,buyer_cash_id=target.cash_obligation_id)
        buyer.apply_preseason_trade_in(plan,expected_revision=buyer.revision,assignment_request_id=request,
            assigned_from_team=seller._team_identity,assigned_from_generation_id=source)
        return target

    def test_return_assignment_back_to_former_club_preserves_all_money_and_sources(self):
        a,old,returned=self.source();b=self.buyer('b')
        original=a.generation_accounting(old);oldcash=a.generation_cash(old)
        first=self.transfer(a,b,'a-b')
        self.assertEqual(a.charges,(42,0,0));self.assertEqual(b.charges,(5,5,5))
        agreement=b.generation_accounting(first.generation_id)
        self.assertEqual((agreement.assignment_request_id,agreement.assigned_from_team,agreement.assigned_from_generation_id),('a-b','a',returned))
        self.assertIsNone(agreement.return_scope)
        second=self.transfer(b,a,'b-a')
        self.assertEqual(a.charges,(47,5,5));self.assertEqual(b.charges,(0,0,0))
        self.assertEqual(a.contract_identity('v'),second)
        self.assertEqual(a.generation_accounting(old),original);self.assertEqual(a.generation_cash(old),oldcash)
        self.assertEqual(a.generation_cash(returned).amount,3)
        self.assertEqual(a.generation_accounting(returned).status,'assigned')
        self.assertEqual(a.generation_cash(second.generation_id).amount,15)
        self.assertEqual(sum(r.amount for r in a._cash.records.values())+sum(r.amount for r in b._cash.records.values()),57)
        self.assertEqual(len(a.generation_agreements()),3)
        a.bind_team_identity('a')
        scope=test_restructures.PreseasonRestructureTests().scope()
        a.apply_preseason_restructure('v',scope=scope,converted_base=4,record_id='new-conversion',expected_revision=a.revision)
        self.assertEqual(a.charges,(Fraction(133,3),Fraction(19,3),Fraction(19,3)))
        self.assertEqual(a.generation_accounting(second.generation_id).original_contract.offer.salaries,(5,5,5))
        release=test_releases.PreseasonReleaseTests().plan()
        a.apply_preseason_release('v',scope=release.scope,discount=release.discount,payment_year_offsets=(0,)*3,
            record_id='new-release',expected_revision=a.revision)
        self.assertEqual(a.charges,(47,0,0))
        self.assertEqual(a.generation_guarantee_cash(second.generation_id)['unpaid_signing_bonus'],4)
        self.assertEqual(a.generation_cash(old),oldcash)

    def test_virgin_and_known_active_metadata_floor_cash_and_source_failures_are_atomic(self):
        a,old,returned=self.source();b=self.buyer('b')
        target=assignment_identity('b','v','a-b')
        plan=a.apply_preseason_trade_out('v',scope=test_trades.PreseasonTradeTests().scope(),record_id='trade:a-b',
            expected_revision=a.revision,buyer_cash_id=target.cash_obligation_id)
        defaults=dict(expected_revision=0,assignment_request_id='a-b',assigned_from_team='a',assigned_from_generation_id=returned)
        cases=({'assigned_from_team':None},{'assigned_from_team':'b'},{'assigned_from_generation_id':'bad'},
               {'assigned_from_generation_id':old},{'expected_revision':1})
        for changes in cases:
            before=b.generation_snapshot()
            with self.subTest(changes=changes),self.assertRaises((Rejected,ValueError)):
                b.apply_preseason_trade_in(plan,**{**defaults,**changes})
            self.assertEqual(b.generation_snapshot(),before)
        for changed in (replace(plan,buyer_cash=replace(plan.buyer_cash,obligation_id='foreign')),
                        replace(plan,assigned_base=16)):
            with self.assertRaises(ValueError):b.apply_preseason_trade_in(changed,**defaults)
        b.apply_preseason_trade_in(plan,**defaults)
        with self.assertRaises(Rejected):b.apply_preseason_trade_in(plan,**{**defaults,'expected_revision':1})
        with self.assertRaises(ValueError):replace(b.generation_accounting(target.generation_id),assigned_from_team=None)
        with self.assertRaises(FrozenInstanceError):b.generation_accounting(target.generation_id).assignment_request_id='changed'

    def test_assignment_namespace_is_distinct_and_legacy_postings_omit_metadata(self):
        self.assertNotEqual(assignment_identity('a','v','one'),generation_identity('a','v','one'))
        self.assertNotEqual(assignment_identity('a:b','c','d'),assignment_identity('a','b:c','d'))
        a,old,_=self.source()
        archive=next(row for row in a.generation_snapshot()['agreements'] if row['identity']['generation_id']==old)
        self.assertNotIn('assignment_request_id',archive)

    def test_cap_floor_unknown_prior_cash_and_active_prior_agreement_reject(self):
        seller,_,source=self.source()
        for scenario in ('cap','floor','unknowncash','active'):
            buyer=self.buyer('b',cap=4 if scenario=='cap' else 200)
            target=assignment_identity('b','v','a-b')
            from franchise.trades import calculate_preseason_trade
            plan=calculate_preseason_trade(seller.active_contract('v'),seller.generation_cash(source),
                scope=test_trades.PreseasonTradeTests().scope(),record_id='trade:a-b',
                expected_cash_id=source,buyer_cash_id=target.cash_obligation_id)
            if scenario=='floor':buyer._veteran_minimums['v']=(6,)*3
            if scenario=='unknowncash':buyer._cash=None
            if scenario=='active':
                buyer.sign('original',Offer('v',(1,),0),0)
                buyer._cash.add_contract(Offer('v',(1,),0),'synthetic active')
            before=buyer.generation_snapshot()
            with self.subTest(scenario=scenario),self.assertRaises(Rejected):
                buyer.apply_preseason_trade_in(plan,expected_revision=buyer.revision,
                    assignment_request_id='a-b',assigned_from_team='a',assigned_from_generation_id=source)
            self.assertEqual(buyer.generation_snapshot(),before)

    def test_custom_source_without_destination_identity_rejects_before_mutation(self):
        seller,_,_=self.source()
        before=seller.generation_snapshot()
        with self.assertRaisesRegex(Rejected,'Explicit destination'):
            seller.apply_preseason_trade_out('v',scope=test_trades.PreseasonTradeTests().scope(),
                record_id='trade:no-destination',expected_revision=seller.revision)
        self.assertEqual(seller.generation_snapshot(),before)
