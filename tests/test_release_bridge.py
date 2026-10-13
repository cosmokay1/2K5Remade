import tempfile
import unittest
from franchise.bridge import Bridge
from franchise.control import AccessDisabled
from tests import test_release_store


class ReleaseBridgeTests(unittest.TestCase):
    def request(self):
        from franchise.releases import EXCLUDED_LIABILITIES
        return {'protocol':1,'request_id':'manual','operation':'manual_release','team_id':'a','player_id':'v',
            'expected_revision':1,'timeout_ms':1000,'decision_mode':'manual',
            'scope':{'league_year':2026,'removed_on':'2026-06-01','first_regular_season_game':'2026-09-10',
                'exclusions':sorted(EXCLUDED_LIABILITIES),'covered_guarantees':True,'healthy':True,
                'current_year_earned_base':0,'source':'fixture source'},
            'discount':{'league_year':2026,'annual_rate':0,'rate_source':'synthetic zero'},'payment_year_offsets':[0,1,2]}

    def test_explicit_manual_release_works_ai_off_and_retries_without_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            store=test_release_store.ReleaseStoreTests().setup_store(directory)
            def forbidden(*_):raise AssertionError('Manual release must not call model')
            def disabled():raise AccessDisabled('fixture switch off')
            bridge=Bridge(store,provider=forbidden,access_check=disabled)
            reply=bridge.handle(self.request())
            self.assertIsNone(reply['error'])
            self.assertEqual(reply['result']['release']['financial']['signed_players'],[])
            self.assertEqual(reply['result']['release']['cash']['unpaid_total'],30)
            self.assertEqual(bridge.handle(self.request()),reply)
            self.assertEqual(store.load_team('a').revision,2)

    def test_disconnect_and_invalid_scope_leave_release_uncommitted(self):
        with tempfile.TemporaryDirectory() as directory:
            store=test_release_store.ReleaseStoreTests().setup_store(directory)
            calls=[]
            def check():
                calls.append(1)
                if len(calls)>1:raise TimeoutError('fixture disconnect')
            bridge=Bridge(store,provider=lambda _:None,access_check=lambda:None,connection_check=check)
            before=store.load_team('a').financial_snapshot()
            self.assertEqual(bridge.handle(self.request())['error'],'timeout')
            self.assertEqual(store.load_team('a').financial_snapshot(),before)
            bridge.connection_check=lambda:None
            for changed in ({'decision_mode':'ai'},{'expected_revision':0},{'timeout_ms':True},
                            {'scope':{**self.request()['scope'],'healthy':False}},
                            {'scope':{**self.request()['scope'],'removed_on':'20260601'}},
                            {'scope':{**self.request()['scope'],'first_regular_season_game':'20260910'}}):
                self.assertIsNotNone(bridge.handle({**self.request(),**changed})['error'])
            self.assertEqual(store.load_team('a').financial_snapshot(),before)
