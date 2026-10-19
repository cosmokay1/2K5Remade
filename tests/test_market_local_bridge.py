"""Generated asking prices reach the existing local proposal path within IPC limits."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger
from franchise.local_runtime import LocalRulesRuntime
from franchise.market_pricing import build_pricebook
from franchise.store import FranchiseStore
from test_market_pricing import fixture


class MarketLocalBridgeTests(unittest.TestCase):
    def test_generated_quote_records_price_in_offline_proposal_without_spending_or_sdk(self):
        data=fixture()
        for row in data['market']['comparables']:row['source']='Authored detailed source '*100
        policy=build_pricebook(data)['policy']
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);config=root/'local.json';config.write_text(json.dumps(policy))
            store=FranchiseStore(root/'league.sqlite')
            store.create_team('club',Ledger.from_opening(OpeningBooks(),cap=data['league_cap'],
                roster_reserve=20000000,max_bonus_years=5,veteran_minimums={'player':(1000000,)*3}))
            provider=LocalRulesRuntime(config,clock=lambda:4)
            request=dict(protocol=1,request_id='priced-offer',operation='negotiate_proposal',team_id='club',
                offer=policy['quotes']['player']['offer'],expected_revision=0,timeout_ms=1000,
                personality={'money':.5,'patience':.5},performance={},relationships={'trust':.5,'respect':.5},
                contract_format=data['contract_format'])
            with patch('franchise.vertex_provider.VertexProvider.__init__',side_effect=AssertionError('No cloud client')):
                response=Bridge(store,provider=provider,access_check=provider.check).handle(request)
            self.assertIsNone(response['error'],response)
            self.assertEqual(response['result']['outcome'],'accepted_proposal')
            self.assertLessEqual(len(json.dumps(response).encode()),4095)
            recorded=FranchiseStore(root/'league.sqlite').negotiation_history('club','player')[0]
            self.assertEqual(recorded['local_rules']['asking_offer'],policy['quotes']['player']['offer'])
            self.assertEqual(store.load_team('club').charges,(0,))
