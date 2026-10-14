from dataclasses import FrozenInstanceError, replace
import unittest
from tests import test_generation_identity
from tests import test_releases, test_trades
from franchise.cap import Rejected


class ArchivedGenerationTests(unittest.TestCase):
    def ledger(self):
        fixture=test_generation_identity.ConsumedGenerationIdentityTests();fixture.setUp()
        ledger=fixture.ledger();ledger.bind_team_identity('a')
        return ledger,fixture

    def test_original_effective_closed_and_live_cash(self):
        ledger,fixture=self.ledger()
        identity=ledger.contract_identity('v');gid=identity.generation_id
        original=ledger.generation_accounting(gid)
        snapshot=ledger.financial_snapshot()
        self.assertEqual(original.status,'active')
        self.assertEqual(original.annual_charges(),original.contract.charges())
        self.assertEqual(original.payment_ceilings(),original.contract.compensation_components())
        self.assertEqual(ledger.financial_snapshot(),snapshot)
        with self.assertRaises(FrozenInstanceError): original.contract=None
        ledger.apply_preseason_restructure('v',scope=fixture.fixture.scope(),converted_base=8,
            record_id='convert',expected_revision=0)
        amended=ledger.generation_accounting(gid)
        self.assertEqual(amended.original_contract,original.contract)
        self.assertNotEqual(amended.contract,original.contract)
        release=test_releases.PreseasonReleaseTests().plan()
        plan=ledger.apply_preseason_release('v',scope=release.scope,discount=release.discount,
            payment_year_offsets=(0,)*5,record_id='release',expected_revision=1)
        closed=ledger.generation_accounting(gid)
        self.assertEqual(closed.status,'released')
        self.assertEqual(closed.original_contract,original.contract)
        self.assertEqual(closed.contract,amended.contract)
        self.assertEqual(closed.retained_records,plan.retained)
        self.assertEqual(closed.annual_charges(),plan.charges())
        self.assertEqual(closed.payment_ceilings()['base:4'],0)
        self.assertEqual(closed.payment_ceilings()['base:2'],2)
        self.assertEqual(ledger.generation_cash(gid),plan.cash_obligation)
        self.assertEqual(ledger.generation_guarantee_cash(gid),ledger.guarantee_cash('v'))
        settled=replace(plan.cash_obligation,paid=plan.cash_obligation.paid+8,
            paid_components=plan.cash_obligation.paid_components+((amended.contract.bonus_layers[0].cash_component,8),))
        ledger._cash.records[identity.cash_obligation_id]=settled
        self.assertEqual(ledger.generation_cash(gid),settled)
        self.assertEqual(ledger.generation_guarantee_cash(gid)['unpaid_signing_bonus'],0)
        self.assertIs(ledger.generation_accounting(gid),closed)
        self.assertEqual(ledger.generation_agreements(),(closed,))
        self.assertEqual(original.status,'active')
        with self.assertRaises(Rejected):ledger.generation_accounting('foreign')

    def test_assigned_generation_keeps_debt_and_payment_ceilings(self):
        from franchise.books import OpeningBooks
        from franchise.cap import Ledger
        from franchise.cash import CashBook
        fixture=test_trades.PreseasonTradeTests();plan=fixture.plan()
        ledger=Ledger.from_opening(OpeningBooks(contracts=(plan.original_contract,)),cap=200,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3})
        ledger._cash=CashBook((plan.original_cash,),'synthetic');ledger.bind_team_identity('a')
        gid=ledger.contract_identity('v').generation_id
        posted=ledger.apply_preseason_trade_out('v',scope=plan.scope,record_id='trade',expected_revision=0)
        agreement=ledger.generation_accounting(gid)
        self.assertEqual(agreement.status,'assigned')
        self.assertEqual(agreement.retained_records,(posted.retained_bonus,))
        self.assertEqual(agreement.payment_ceilings()['base:0'],0)
        self.assertEqual(agreement.payment_ceilings()['signing_bonus'],9)
        self.assertEqual(ledger.generation_cash(gid),posted.seller_cash)
        self.assertEqual(ledger.generation_guarantee_cash(gid)['unpaid_signing_bonus'],0)

    def test_invalid_archive_contract_plan_and_lookup_key_reject(self):
        ledger,_=self.ledger()
        agreement=ledger.generation_agreements()[0]
        for changes in ({'contract':None}, {'identity':None}, {'release':object()},
                        {'contract':replace(agreement.contract,offer=replace(agreement.contract.offer,player_id='other'))}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                replace(agreement,**changes)
        ledger._generation_agreements['foreign']=agreement
        with self.assertRaises(Rejected): ledger.generation_accounting('foreign')

    def test_generation_guarantees_do_not_resolve_current_player_cash(self):
        from unittest.mock import patch
        ledger,_=self.ledger()
        gid=ledger.contract_identity('v').generation_id
        expected=ledger.generation_guarantee_cash(gid)
        with patch.object(ledger,'contract_cash_id',side_effect=AssertionError('current player alias used')):
            self.assertEqual(ledger.generation_guarantee_cash(gid),expected)
