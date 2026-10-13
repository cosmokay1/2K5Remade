from dataclasses import asdict
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger
from franchise.control import AccessDisabled
from franchise.store import FranchiseStore
from tests import test_restructures


class RestructureBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture = test_restructures.PreseasonRestructureTests()
        self.store = FranchiseStore(Path(self.temp.name)/'state.sqlite')
        ledger = Ledger.from_opening(OpeningBooks(contracts=(self.fixture.contract(),)),cap=200,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(2,)*5})
        self.store.create_team('a',ledger)
        self.store.initialize_cash('a',(self.fixture.cash(),),source='synthetic allocated cash')
        def forbidden(*_):
            raise AssertionError('Manual restructure must never call AI provider or grant')
        self.bridge = Bridge(self.store,provider=forbidden,access_check=forbidden)

    def request(self):
        scope = asdict(self.fixture.scope())
        scope.update(amended_on=scope['amended_on'].isoformat(),
                     first_regular_season_game=scope['first_regular_season_game'].isoformat(),
                     exclusions=sorted(scope['exclusions']))
        return {'protocol':1,'request_id':'conversion','operation':'manual_restructure','team_id':'a','player_id':'v',
                'expected_revision':1,'timeout_ms':1000,'decision_mode':'manual','scope':scope,'converted_base':8}

    def test_manual_operation_works_ai_disabled_and_retries_without_inference(self):
        def disabled(): raise AccessDisabled('fixture AI off')
        self.bridge.access_check = disabled
        reply = self.bridge.handle(self.request())
        self.assertIsNone(reply['error'])
        self.assertEqual(reply['result']['team_id'],'a')
        self.assertEqual(reply['result']['player_id'],'v')
        self.assertEqual(reply['result']['restructure']['cash']['nominal_total'],180)
        self.assertEqual(reply['result']['restructure']['cash']['paid_total'],30)
        self.assertEqual(reply['result']['restructure']['financial']['charges'][0],'28/5')
        self.assertEqual(self.bridge.handle(self.request()),reply)
        self.assertEqual(self.bridge.handle({**self.request(),'converted_base':7})['error'],'state_rejected')
        self.assertEqual(FranchiseStore(self.store.path).load_team('a').revision,2)

    def test_strict_fields_modes_money_revisions_dates_and_scope_reject_without_commit(self):
        original = self.request()
        scope = original['scope']
        changes = ({'decision_mode':'ai'},{'expected_revision':True},{'expected_revision':0},
                   {'converted_base':True},{'converted_base':8.0},{'converted_base':'8'},{'converted_base':0},
                   {'converted_base':-1},{'timeout_ms':True},{'timeout_ms':60001},{'extra':1},
                   {'scope':{**scope,'extra':True}},{'scope':{**scope,'amended_on':'20260601'}},
                   {'scope':{**scope,'first_regular_season_game':'20260910'}},
                   {'scope':{**scope,'exclusions':scope['exclusions']+[scope['exclusions'][0]]}},
                   {'scope':{**scope,'healthy':False}},{'scope':{**scope,'current_year_earned_base':False}},
                   {'scope':{key:value for key,value in scope.items() if key!='minimum_source'}})
        before,cash = self.store.load_team('a').financial_snapshot(),self.store.load_team('a').cash_snapshot()
        for change in changes:
            with self.subTest(change=change):
                self.assertIsNotNone(self.bridge.handle({**original,**change})['error'])
                self.assertEqual(self.store.load_team('a').financial_snapshot(),before)
                self.assertEqual(self.store.load_team('a').cash_snapshot(),cash)

    def test_final_disconnect_and_expiry_roll_back_restructure(self):
        calls=[]
        def connection():
            calls.append(1)
            if len(calls)>1: raise TimeoutError('fixture disconnect')
        self.bridge.connection_check = connection
        before = self.store.load_team('a').financial_snapshot()
        self.assertEqual(self.bridge.handle(self.request())['error'],'timeout')
        self.assertEqual(self.store.load_team('a').financial_snapshot(),before)
        self.bridge.connection_check = lambda:None
        with patch('franchise.bridge.time.monotonic',side_effect=(0,0,2)):
            self.assertEqual(self.bridge.handle(self.request())['error'],'timeout')
        self.assertEqual(self.store.load_team('a').financial_snapshot(),before)

    def test_handshake_advertises_manual_restructure(self):
        self.bridge.access_check = lambda:None
        reply = self.bridge.handle({'protocol':1,'request_id':'hello','operation':'hello'})
        self.assertIn('manual_restructure',reply['result']['operations'])
