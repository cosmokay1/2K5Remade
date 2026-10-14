from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from franchise.books import OpeningBooks
from franchise.cap import Ledger
from franchise.bridge import Bridge
from franchise.control import AccessDisabled
from franchise.store import FranchiseStore
from tests import test_restructures,test_releases


class ContractContextBridgeTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store=FranchiseStore(Path(directory.name)/'state.sqlite')
        self.fixture=test_restructures.PreseasonRestructureTests()
        self.store.create_team('a',Ledger.from_opening(OpeningBooks(contracts=(self.fixture.contract(),)),
            cap=200,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(2,)*5}))
        self.store.create_team('b',Ledger.from_opening(OpeningBooks(),cap=200,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(2,)*5}))
        self.store.initialize_cash('a',(self.fixture.cash(),),source='synthetic allocated cash')
        self.identity=self.store.contract_generations('a')['generations'][0]['generation_id']
        def disabled():raise AccessDisabled('fixture shutdown')
        def provider(_):raise AssertionError('Read-only context must not invoke model')
        self.bridge=Bridge(self.store,provider=provider,access_check=disabled)
        self.request=dict(protocol=1,request_id='inspect',operation='contract_context',
            team_id='a',generation_id=self.identity,timeout_ms=1000)

    def test_native_agreement_read_is_team_scoped_and_available_with_ai_disabled(self):
        before=self.store.load_team('a').financial_snapshot()
        reply=self.bridge.handle(self.request)
        self.assertIsNone(reply['error'])
        self.assertEqual(reply['result']['accounting'],self.store.player_context('a','v')['contract_accounting'])
        self.assertEqual(reply['result']['generation_id'],self.identity)
        self.assertEqual(reply['result']['team_id'],'a')
        self.assertEqual(self.store.load_team('a').financial_snapshot(),before)
        self.assertEqual(self.bridge.handle({**self.request,'team_id':'b'})['error'],'state_rejected')
        self.assertEqual(self.bridge.handle({**self.request,'generation_id':'unknown'})['error'],'state_rejected')

    def test_closed_agreement_remains_readable_after_release_payment_and_restart(self):
        release=test_releases.PreseasonReleaseTests().plan()
        self.store.release_preseason_veteran('a','release','v',scope=release.scope,discount=release.discount,
            payment_year_offsets=(0,)*5,expected_revision=1,access_check=lambda:None)
        self.store.record_payment('a','pay','contract:v',2,expected_cash_revision=1,
            source='synthetic guarantee payment',payment_reference='receipt',component='base:2')
        reply=self.bridge.handle(self.request)
        self.assertIsNone(reply['error'])
        accounting=reply['result']['accounting']
        self.assertEqual(accounting['status'],'released')
        self.assertEqual(accounting['cash_obligation']['paid'],32)
        self.assertEqual(accounting['generation_id'],self.identity)
        self.assertEqual(FranchiseStore(self.store.path).contract_context('a',self.identity),reply['result'])

    def test_request_validation_and_disconnect(self):
        for changes in ({'timeout_ms':True},{'generation_id':''},{'generation_id':True},{'extra':1}):
            with self.subTest(changes=changes):
                self.assertEqual(self.bridge.handle({**self.request,**changes})['error'],'invalid_request')
        self.bridge.connection_check=lambda:(_ for _ in ()).throw(TimeoutError('disconnected'))
        self.assertEqual(self.bridge.handle(self.request)['error'],'timeout')

    def test_oversized_agreement_reply_does_not_break_next_read(self):
        with patch.object(self.store,'contract_context',return_value={'large':'x'*65536}):
            reply=self.bridge.handle(self.request)
        self.assertEqual(reply['error'],'context_too_large')
        self.assertIsNone(reply['result'])
        self.assertIsNone(self.bridge.handle(self.request)['error'])
