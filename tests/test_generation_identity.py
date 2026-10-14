from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import copy
import json
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.cash import CashBook
from franchise.generations import GenerationIdentity, legacy_identity
from franchise.store import FranchiseStore
from tests import test_restructures,test_releases,test_trades


class ConsumedGenerationIdentityTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_restructures.PreseasonRestructureTests()

    def ledger(self):
        ledger=Ledger.from_opening(OpeningBooks(contracts=(self.fixture.contract(),)),cap=200,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(2,)*5,'free':(1,)})
        ledger._cash=CashBook((self.fixture.cash(),),'synthetic complete cash')
        return ledger

    def test_binding_immutable_identity_preserves_every_legacy_posting_shape(self):
        ledger=self.ledger()
        snapshot,cash,config=copy.deepcopy(ledger.financial_snapshot()),ledger.cash_snapshot(),ledger.bootstrap_config()
        self.assertIsNone(ledger.contract_identity('v'))
        self.assertEqual(ledger.contract_cash_id('v'),'contract:v')
        ledger.bind_team_identity('a')
        identity=ledger.contract_identity('v')
        self.assertEqual(identity,legacy_identity('a','v'))
        self.assertEqual(ledger._active_generation_ids,{'v':identity.generation_id})
        with self.assertRaises(FrozenInstanceError):
            identity.cash_obligation_id='different'
        ledger.bind_team_identity('a')
        self.assertIs(ledger.contract_identity('v'),identity)
        self.assertEqual((ledger.financial_snapshot(),ledger.cash_snapshot(),ledger.bootstrap_config()),(snapshot,cash,config))
        with self.assertRaises(Rejected):
            ledger.bind_team_identity('different')
        self.assertEqual(ledger.contract_identity('v'),identity)

    def test_identity_survives_restructure_release_and_closed_active_pointer_rejects(self):
        ledger=self.ledger();ledger.bind_team_identity('a')
        identity=ledger.contract_identity('v')
        ledger.apply_preseason_restructure('v',scope=self.fixture.scope(),converted_base=8,
            record_id='convert',expected_revision=0)
        self.assertIs(ledger.contract_identity('v'),identity)
        release=test_releases.PreseasonReleaseTests().plan()
        ledger.apply_preseason_release('v',scope=release.scope,discount=release.discount,
            payment_year_offsets=(0,)*5,record_id='release',expected_revision=1)
        self.assertIs(ledger.contract_identity('v'),identity)
        self.assertNotIn('v',ledger._active_generation_ids)
        self.assertEqual(ledger.guarantee_cash('v')['unpaid_signing_bonus'],8)
        with self.assertRaisesRegex(Rejected,'generation IDs'):
            ledger.preview_offer(Offer('v',(2,),0),2)
        ledger._active_generation_ids['v']=identity.generation_id
        with self.assertRaisesRegex(Rejected,'Closed contract'):
            ledger.contract_cash_id('v')
        with self.assertRaises(Rejected):
            ledger.bind_team_identity('a')
        self.assertIn('v',ledger._active_generation_ids)  # Binding must not repair corruption.

    def test_resolver_checks_key_team_player_cash_and_active_mapping_without_repair(self):
        for scenario in ('key','cash','active','missing'):
            with self.subTest(scenario=scenario):
                ledger=self.ledger();ledger.bind_team_identity('a')
                identity=ledger.contract_identity('v')
                if scenario=='key':ledger._generation_identities[identity.generation_id]=replace(identity,generation_id='wrong')
                if scenario=='cash':ledger._generation_identities[identity.generation_id]=replace(identity,cash_obligation_id='foreign')
                if scenario=='active':ledger._active_generation_ids['v']='wrong'
                if scenario=='missing':del ledger._generation_by_player['v']
                maps=copy.deepcopy((ledger._generation_by_player,ledger._generation_identities,ledger._active_generation_ids))
                with self.assertRaises(Rejected):ledger.contract_cash_id('v')
                with self.assertRaises(Rejected):ledger.bind_team_identity('a')
                self.assertEqual((ledger._generation_by_player,ledger._generation_identities,ledger._active_generation_ids),maps)

    def test_atomic_binding_rejects_invalid_team_or_encoding_before_state_changes(self):
        ledger=self.ledger()
        for team in ('',True,'\ud800'):
            with self.subTest(team=team),self.assertRaises(ValueError):
                ledger.bind_team_identity(team)
            self.assertIsNone(ledger._team_identity)
            self.assertEqual(ledger._generation_by_player,{})
        ledger.bind_team_identity('a')
        before=ledger.financial_snapshot()
        ledger._veteran_minimums['\ud800']=(1,)
        with self.assertRaises(ValueError):
            ledger.sign('bad',Offer('\ud800',(1,),0),0)
        self.assertEqual(ledger.financial_snapshot(),before)

    def test_incoming_foreign_cash_rejects_before_financial_cash_or_identity_mutation(self):
        buyer=Ledger.from_opening(OpeningBooks(),cap=200,roster_reserve=0,max_bonus_years=5,
            veteran_minimums={'v':(1,)*3})
        buyer._cash=CashBook((),'synthetic buyer cash');buyer.bind_team_identity('buyer')
        plan=test_trades.PreseasonTradeTests().plan()
        changed=replace(plan,buyer_cash=replace(plan.buyer_cash,obligation_id='foreign'))
        before=copy.deepcopy((buyer.financial_snapshot(),buyer.cash_snapshot(),buyer._generation_identities,buyer._active_generation_ids))
        with self.assertRaises((Rejected,ValueError)):
            buyer.apply_preseason_trade_in(changed,expected_revision=0)
        self.assertEqual((buyer.financial_snapshot(),buyer.cash_snapshot(),buyer._generation_identities,buyer._active_generation_ids),before)
        buyer.apply_preseason_trade_in(plan,expected_revision=0)
        self.assertEqual(buyer.contract_identity('v'),legacy_identity('buyer','v'))

    def test_durable_inventory_and_context_consume_bound_resolver_and_new_sign_replays(self):
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=200,roster_reserve=0,
                max_bonus_years=5,veteran_minimums={'v':(1,)}))
            store.initialize_cash('a',(),source='synthetic known empty cash')
            store.sign('a','sign',Offer('v',(10,),0),1)
            view=store.contract_generations('a')
            context=store.player_context('a','v')
            self.assertEqual(view['generations'][0]['generation_id'],legacy_identity('a','v').generation_id)
            self.assertEqual(context['contract_accounting']['cash_obligation']['obligation_id'],'contract:v')
            reopened=FranchiseStore(store.path)
            self.assertEqual(reopened.contract_generations('a'),view)
            self.assertEqual(reopened.load_team('a').contract_identity('v'),legacy_identity('a','v'))

    def test_team_player_delimiters_and_invalid_generation_fields(self):
        identities=(legacy_identity('a:b','c'),legacy_identity('a','b:c'),legacy_identity('a\0b','c'),legacy_identity('a','b\0c'))
        self.assertEqual(len({identity.generation_id for identity in identities}),4)
        for fields in (('', 'v','contract:v'),('id',True,'contract:v'),('id','v','')):
            with self.assertRaises(ValueError):GenerationIdentity(*fields)
