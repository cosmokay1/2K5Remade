import tempfile
import unittest
from franchise.bridge import Bridge
from franchise.control import AccessDisabled
from franchise.trades import EXCLUDED_TRADE_LIABILITIES
from tests import test_trade_store


class TradeBridgeTests(unittest.TestCase):
    def request(self):
        return {'protocol':1,'request_id':'assign','operation':'manual_trade','seller':'a','buyer':'b','player_id':'v',
            'seller_revision':1,'buyer_revision':1,'timeout_ms':1000,'decision_mode':'manual',
            'scope':{'league_year':2026,'traded_on':'2026-06-01','seller_first_regular_season_game':'2026-09-10',
                'buyer_first_regular_season_game':'2026-09-11','exclusions':sorted(EXCLUDED_TRADE_LIABILITIES),
                'healthy':True,'current_year_earned_base':0,'assignment_consent':True,'transaction_eligible':True,'source':'fixture source'}}

    def test_manual_assignment_ai_off_and_idempotent_without_model(self):
        with tempfile.TemporaryDirectory() as directory:
            store=test_trade_store.TradeStoreTests().setup_store(directory)
            def forbidden(*_):raise AssertionError('No model call for explicit manual assignment')
            def disabled():raise AccessDisabled('fixture shutdown')
            bridge=Bridge(store,provider=forbidden,access_check=disabled)
            result=bridge.handle(self.request())
            self.assertIsNone(result['error'])
            self.assertEqual(result['result']['trade']['a']['financial']['charges'],[9,0,0])
            self.assertEqual(result['result']['trade']['b']['financial']['signed_players'],['v'])
            self.assertEqual(bridge.handle(self.request()),result)
            self.assertEqual(bridge.handle({**self.request(),'buyer_revision':True})['error'],'invalid_request')
            self.assertEqual(store.load_team('a').revision,2)
            self.assertEqual(store.load_team('b').revision,2)

    def test_invalid_scope_and_final_disconnect_leave_both_teams_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=test_trade_store.TradeStoreTests()
            store=fixture.setup_store(directory)
            before=fixture.states(store)
            calls=[]
            def check():
                calls.append(1)
                if len(calls)>1:raise TimeoutError('fixture disconnect')
            bridge=Bridge(store,provider=lambda _:None,access_check=lambda:None,connection_check=check)
            self.assertEqual(bridge.handle(self.request())['error'],'timeout')
            self.assertEqual(fixture.states(store),before)
            bridge.connection_check=lambda:None
            for changes in ({'decision_mode':'ai'},{'seller_revision':0},{'buyer_revision':True},
                            {'scope':{**self.request()['scope'],'assignment_consent':False}},
                            {'scope':{**self.request()['scope'],'traded_on':'20260601'}}):
                self.assertIsNotNone(bridge.handle({**self.request(),**changes})['error'])
            self.assertEqual(fixture.states(store),before)
