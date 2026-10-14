from contextlib import closing
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from franchise.books import ActiveContract, OpeningBooks
from franchise.bridge import Bridge, ResponseTooLarge
from franchise.cap import Ledger, Offer
from franchise.cash import CashObligation
from franchise.store import FranchiseStore
from tests import test_release_bridge, test_trade_bridge, test_restructures


class LifecycleReceiptCapacityTests(unittest.TestCase):
    def test_oversized_native_receipts_reject_before_financial_or_ownership_commit(self):
        amendment = asdict(test_restructures.PreseasonRestructureTests().scope())
        for key in ('amended_on','first_regular_season_game'):
            amendment[key] = amendment[key].isoformat()
        amendment['exclusions'] = sorted(amendment['exclusions'])
        requests = [test_release_bridge.ReleaseBridgeTests().request(),
                    test_trade_bridge.TradeBridgeTests().request(),
                    dict(protocol=1,request_id='amend',operation='manual_restructure',team_id='a',player_id='v',
                         expected_revision=1,timeout_ms=5000,decision_mode='manual',scope=amendment,converted_base=4)]
        for request in requests:
            with self.subTest(operation=request['operation']), tempfile.TemporaryDirectory() as directory:
                store = FranchiseStore(Path(directory)/'state.sqlite')
                contract = ActiveContract(Offer('v',(10,20,30),9,(10,20,10)),'synthetic original')
                for team in ('a','b'):
                    store.create_team(team,Ledger.from_opening(
                        OpeningBooks(contracts=(contract,)) if team == 'a' else OpeningBooks(),
                        cap=200,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
                    # A sourced cash record is intentionally too large for the native receipt.
                    cash = (CashObligation('contract:v','v',69,9,'x'*70000,(('signing_bonus',9),)),) if team == 'a' else ()
                    store.initialize_cash(team,cash,source='synthetic complete cash')
                before = {team:store.load_team(team).generation_snapshot() for team in ('a','b')}
                def forbidden(*_):self.fail('Manual lifecycle called AI')
                reply = Bridge(store,provider=forbidden,access_check=forbidden).handle(request)
                self.assertEqual(reply['error'],'response_too_large',reply)
                self.assertLess(len(json.dumps(reply).encode('utf-8'))+1,65536)
                self.assertEqual(before,{team:store.load_team(team).generation_snapshot() for team in ('a','b')})
                with closing(sqlite3.connect(store.path)) as db:
                    self.assertEqual(db.execute("SELECT team_id FROM ownership WHERE player_id='v'").fetchone(),('a',))
                    self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0],2)

    def test_exact_json_frame_capacity_includes_newline_and_escaped_unicode(self):
        value = {'text':'é'}
        size = len(json.dumps(Bridge._reply('id',result=value),allow_nan=False).encode('utf-8'))+1
        value['text'] = 'x'*(65536-size+6)
        Bridge._require_frame('id',value)
        value['text'] += 'x'
        with self.assertRaises(ResponseTooLarge):Bridge._require_frame('id',value)
