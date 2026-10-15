"""Explicit unknown legacy cash is never a zero balance or invented guarantee."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock

from franchise.books import OpeningBooks, ActiveContract
from franchise.bridge import Bridge
from franchise.cap import Ledger, Offer, Rejected
from franchise.cash import CashBook, CashObligation
from franchise import guest_signing
from franchise.legacy_contracts import LegacyContract
from franchise.store import FranchiseStore
from tools.export_legacy_contracts import legacy_contracts
from tools.inspect_franchise_save import TEAMS
import test_confirm_saved_signing as saved_fixtures


class LegacyCashScopeTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'legacy.sqlite'
        self.store=FranchiseStore(self.path)
        legacy=LegacyContract('old',900,4,2,8,7,'Authored preserved cap')
        self.store.create_team('a',Ledger.from_opening(OpeningBooks(legacy_contracts=(legacy,)),
            cap=1400000,roster_reserve=0,max_bonus_years=5,veteran_minimums={'free':(200000,)}))

    def initialize(self):
        self.store.initialize_cash('a',(),source='Authored explicit cash scope; prior cash unavailable',unknown_legacy_players=('old',))

    def test_explicit_inventory_preserves_unknown_totals_and_exact_new_cash_across_restart(self):
        before=self.store.load_team('a').financial_snapshot()
        with self.assertRaises(Rejected): self.store.initialize_cash('a',(),source='Cannot assume zero')
        self.initialize()
        cash=self.store.load_team('a').cash_snapshot()
        self.assertEqual(cash['unknown_legacy_players'],['old'])
        self.assertEqual(cash['known_totals'],dict(nominal_total=0,paid_total=0,unpaid_total=0))
        for key in cash['known_totals']: self.assertIsNone(cash[key])
        offer=Offer('free',(250000,),0)
        receipt=self.store.sign('a','new',offer,1)
        reopened=FranchiseStore(self.path)
        self.assertEqual(reopened.sign('a','new',offer,1),receipt)
        ledger=reopened.load_team('a');cash=ledger.cash_snapshot()
        self.assertEqual(ledger.charges,(1375000,*([1125000]*6)))
        self.assertEqual(ledger.financial_snapshot()['legacy_schedule_sha256'],before['legacy_schedule_sha256'])
        self.assertEqual(cash['known_totals'],dict(nominal_total=250000,paid_total=0,unpaid_total=250000))
        self.assertIsNone(cash['nominal_total']);self.assertEqual(cash['unknown_legacy_players'],['old'])
        self.assertEqual(cash['obligations'][0]['player_id'],'free')
        summary=ledger.negotiation_context('free')['cash_summary']
        self.assertEqual(summary['unknown_legacy_contract_count'],1)
        self.assertNotIn('unknown_legacy_players',summary)
        self.assertIsNone(summary['nominal_total'])
        self.assertEqual(reopened.player_context('a','old')['legacy_liability_scope'],
                         'original cap schedule; cash/protections/lifecycle unverified')
        with self.assertRaises(Rejected): reopened.load_team('a').active_contract('old')
        with self.assertRaises(Rejected): reopened.anchor_calendar(request_id='year',league_year=2026,
            source='Unsupported aging',expected_revisions={'a':2})
        with self.assertRaises(Rejected): reopened.initialize_cash('a',(),source='Reset',unknown_legacy_players=('old',))

    def test_missing_extra_duplicate_invalid_and_fabricated_known_coverage_reject(self):
        for unknown in ((),('other',),('old','other'),('old','old'),['old'],(True,)):
            with self.subTest(unknown=unknown),self.assertRaises((ValueError,Rejected)):
                self.store.initialize_cash('a',(),source='Invalid scope',unknown_legacy_players=unknown)
        with self.assertRaises(ValueError):
            self.store.initialize_cash('a',(CashObligation('contract:old','old',0,0,'Invented zero'),),
                source='Invalid zero',unknown_legacy_players=('old',))
        self.assertIsNone(self.store.load_team('a').cash_snapshot())
        with self.assertRaises(ValueError): CashBook((),'Invalid',unknown_legacy_players=('',))

    def test_unknown_cash_cannot_be_replaced_by_new_contract(self):
        book=CashBook((),'Authored scope',unknown_legacy_players=('old',))
        with self.assertRaises(Rejected): book.add_contract(Offer('old',(1,),0),'Invented replacement')
        self.assertEqual(book.snapshot()['obligations'],[])

    def test_new_contract_payments_update_only_known_totals_and_replay_exactly(self):
        self.initialize()
        self.store.sign('a','new',Offer('free',(250000,),0),1)
        cash=self.store.load_team('a').cash_snapshot()
        receipt=self.store.record_payment('a','pay','contract:free',25000,
            expected_cash_revision=cash['revision'],source='Authored pay feed',payment_reference='pay-1',component='base:0')
        reopened=FranchiseStore(self.path)
        self.assertEqual(reopened.record_payment('a','pay','contract:free',25000,
            expected_cash_revision=cash['revision'],source='Authored pay feed',payment_reference='pay-1',component='base:0'),receipt)
        updated=reopened.load_team('a').cash_snapshot()
        self.assertEqual(updated['known_totals'],dict(nominal_total=250000,paid_total=25000,unpaid_total=225000))
        self.assertEqual(updated['unknown_legacy_players'],['old'])
        self.assertTrue(all(updated[key] is None for key in updated['known_totals']))

    def test_unknown_scope_cannot_conceal_a_modern_opening_obligation(self):
        legacy=(LegacyContract('old2',900,4,2,8,7,'Authored other legacy'),)
        modern=Offer('modern',(10,),0)
        self.store.create_team('mixed',Ledger.from_opening(OpeningBooks(legacy_contracts=legacy,
            contracts=(ActiveContract(modern,'Authored modern original'),)),cap=2000000,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'modern':(1,)}))
        with self.assertRaises(ValueError):
            self.store.initialize_cash('mixed',(),source='Missing modern cash',unknown_legacy_players=('old2',))
        record=CashObligation('contract:modern','modern',10,0,'Authored complete modern cash')
        self.store.initialize_cash('mixed',(record,),source='Explicit scope',unknown_legacy_players=('old2',))
        self.assertEqual(self.store.load_team('mixed').cash_snapshot()['known_totals']['unpaid_total'],10)

    def test_lifecycle_bridge_refuses_incompatible_partial_receipts_before_writing(self):
        import test_release_bridge, test_trade_bridge, test_restructure_bridge, test_restructures
        self.initialize()
        self.store.sign('a','new',Offer('free',(250000,),0),1)
        self.store.create_team('b',Ledger.from_opening(OpeningBooks(),cap=1400000,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'free':(200000,)}))
        self.store.initialize_cash('b',(),source='Authored empty complete cash')
        fixture=test_restructure_bridge.RestructureBridgeTests()
        fixture.fixture=test_restructures.PreseasonRestructureTests()
        requests=[test_release_bridge.ReleaseBridgeTests().request(),
                  test_trade_bridge.TradeBridgeTests().request(),fixture.request()]
        provider=Mock(side_effect=AssertionError('No inference for manual operations'))
        bridge=Bridge(self.store,provider=provider,access_check=lambda:None)
        before=self.store.load_team('a').financial_snapshot()
        for request in requests:
            request['player_id']='free'
            with self.subTest(operation=request['operation']):
                reply=bridge.handle(request)
                self.assertEqual(reply['error'],'state_rejected',reply)
                self.assertIn('legacy cash remains unknown',reply['detail'])
                self.assertEqual(self.store.load_team('a').financial_snapshot(),before)
        provider.assert_not_called()

    def test_replay_rejects_scope_and_null_total_tampering(self):
        self.initialize()
        with sqlite3.connect(self.path) as db:
            row=db.execute("SELECT id,payload FROM events WHERE kind='cash_open'").fetchone()
        original=json.loads(row[1])
        for change in ('unknown','string','total','known_total'):
            value=json.loads(row[1])
            if change=='unknown': value['unknown_legacy_players']=[]
            if change=='string': value['unknown_legacy_players']='old'
            if change=='total': value['cash_posting']['nominal_total']=0
            if change=='known_total': value['cash_posting']['known_totals']['nominal_total']=1
            with sqlite3.connect(self.path) as db:
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(value),row[0]))
            with self.subTest(change=change),self.assertRaises((ValueError,Rejected)):
                FranchiseStore(self.path).load_team('a')
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(original),row[0]))
        self.assertIsNone(FranchiseStore(self.path).load_team('a').cash_snapshot()['nominal_total'])

    def test_saved_journal_prepares_and_confirms_new_contract_without_inventing_legacy_cash(self):
        sample=saved_fixtures.SavedSigningConfirmationTests();sample.setUp()
        self.addCleanup(sample.doCleanups)
        path=self.path.with_name('league.sqlite');store=FranchiseStore(path)
        saved=legacy_contracts(sample.bindings,sample.before)
        for team in TEAMS:
            contracts=tuple(saved[team])
            store.create_team(team,Ledger.from_opening(OpeningBooks(legacy_contracts=contracts),
                cap=80500000,roster_reserve=0,max_bonus_years=5,veteran_minimums={sample.player:(1000,)*15}))
            store.initialize_cash(team,(),source='Authored explicit legacy unknown cash',
                unknown_legacy_players=tuple(contract.player_id for contract in contracts))
        calls=Mock(return_value=json.dumps(dict(action='accept',reason='Authored deal',salaries=None,signing_bonus=None)))
        bridge=Bridge(store,provider=calls,access_check=lambda:None,guest_snapshot=(sample.bindings,sample.before),
            guest_signing_reader=lambda:sample.before)
        proposal=bridge.handle(dict(protocol=1,request_id='proposal',operation='negotiate_proposal',team_id='49ers',
            offer=sample.offer.to_dict(),contract_format='original_fxg_v1',expected_revision=1,timeout_ms=1000,
            personality={},performance={'games':16},relationships={}))
        self.assertIsNone(proposal['error'],proposal)
        before=store.load_team('49ers').financial_snapshot()
        request=dict(protocol=1,request_id='journal',operation='guest_signing_prepare',timeout_ms=5000,
            team_id='49ers',proposal_request_id='proposal',guest_offer=sample.raw,expected_revision=1,
            expected_before_sha256=hashlib.sha256(sample.before).hexdigest())
        prepared=bridge.handle(request);self.assertIsNone(prepared['error'],prepared)
        self.assertEqual(store.load_team('49ers').financial_snapshot(),before)
        with self.assertRaises(Rejected): store.sign('Bears','competing',sample.offer,1)
        bridge.guest_signing_reader=lambda:sample.after
        confirm=dict(protocol=1,request_id='confirm',operation='guest_signing_confirm',timeout_ms=5000,
            journal_request_id='journal',expected_after_sha256=hashlib.sha256(sample.after).hexdigest())
        receipt=bridge.handle(confirm);self.assertIsNone(receipt['error'],receipt)
        self.assertEqual(bridge.handle(confirm),receipt)
        self.assertEqual(receipt['result']['charges'],[4766000,3523000])
        ledger=FranchiseStore(path).load_team('49ers');cash=ledger.cash_snapshot()
        self.assertIsNone(cash['nominal_total'])
        self.assertEqual(cash['known_totals']['nominal_total'],sum(sample.offer.salaries)+sample.offer.signing_bonus)
        self.assertEqual(len(cash['obligations']),1);self.assertEqual(len(cash['unknown_legacy_players']),1)
        self.assertEqual(guest_signing.inspect(FranchiseStore(path),'journal',sample.after)['state'],'settled')
        calls.assert_called_once()
