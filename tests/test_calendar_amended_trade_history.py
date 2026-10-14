"""Durable amendment-to-assignment chain keeps each club's economic history."""
from dataclasses import asdict
from datetime import date
from fractions import Fraction
import unittest
from franchise.books import ActiveContract
from franchise.bridge import Bridge
from franchise.cap import Offer
from franchise.guarantees import DiscountProfile
from franchise.receipts import compact_lifecycle_result
from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
from franchise.restructures import PreseasonRestructureScope,EXCLUDED_RESTRUCTURE_TERMS
from franchise.store import FranchiseStore
from franchise.trades import PreseasonTradeScope,EXCLUDED_TRADE_LIABILITIES
from tests import test_calendar_release_history


class CalendarAmendedTradeHistoryTests(unittest.TestCase):
    def test_conversion_assignment_roll_release_and_historical_receipts(self):
        fixture=test_calendar_release_history.CalendarReleaseHistoryTests()
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.create('a',ActiveContract(Offer('v',(2000000,)*3,3000000,(0,2000000,0)),
            'synthetic immutable original'))
        fixture.create('b');fixture.pay('a','base:0',2000000)
        fixture.anchor(('a','b'));fixture.roll(('a','b'),2026)
        store=fixture.store;ledger=store.load_team('a');gid=ledger.contract_identity('v').generation_id
        original=ledger.generation_accounting(gid).original_contract
        store.restructure_calendar_preseason_veteran('a','convert-2027','v',generation_id=gid,
            scope=PreseasonRestructureScope(2027,date(2027,6,1),date(2027,9,10),0,True,True,True,
                EXCLUDED_RESTRUCTURE_TERMS,fixture.profile(2027).source,'synthetic amendment'),
            converted_base=100000,expected_revision=ledger.revision,access_check=lambda:None)
        fixture.pay('a','bonus:calendar-restructure:convert-2027',100000)
        scope=asdict(PreseasonTradeScope(2027,date(2027,7,1),date(2027,9,10),date(2027,9,10),
            EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'synthetic assignment'))
        scope['exclusions']=sorted(scope['exclusions'])
        for field in ('traded_on','seller_first_regular_season_game','buyer_first_regular_season_game'):
            scope[field]=scope[field].isoformat()
        request=dict(protocol=1,operation='manual_trade',request_id='amended-trade',seller='a',buyer='b',player_id='v',
            seller_revision=store.load_team('a').revision,buyer_revision=store.load_team('b').revision,
            seller_generation_id=gid,buyer_previous_generation_id=None,scope=scope,decision_mode='manual',
            calendar_format='calendar_v1',timeout_ms=5000)
        def forbidden(_):raise AssertionError('Manual lifecycle invoked inference')
        bridge=Bridge(store,provider=forbidden,access_check=lambda:None)
        full=bridge.handle(request);self.assertIsNone(full['error'])
        compact_request={**request,'receipt_format':'target_v1'}
        compact=bridge.handle(compact_request);self.assertIsNone(compact['error'])
        self.assertEqual(compact['result'],compact_lifecycle_result(full['result'],'manual_trade'))
        self.assertEqual(set(full['result']),{'decision_mode','seller','buyer','player_id','trade',
            'seller_generation_id','buyer_generation_id','buyer_previous_generation_id','calendar_format','format','league_year'})
        self.assertEqual(full['result']['format'],2);self.assertEqual(full['result']['league_year'],2027)
        buyerid=full['result']['buyer_generation_id'];seller=store.load_team('a');buyer=store.load_team('b')
        saved=seller.generation_accounting(gid)
        self.assertEqual(saved.original_contract,original)
        self.assertEqual(saved.contract.elapsed_years,1)
        self.assertEqual(saved.restructure_calendar_year,2027)
        self.assertEqual(saved.outgoing_trade_calendar_year,2027)
        self.assertEqual(saved.restructure.contract.bonus_layers[0].record_id,'calendar-restructure:convert-2027')
        self.assertEqual(saved.restructure.contract.bonus_layers[0].amount,100000)
        self.assertEqual(saved.payment_ceilings()['base:0'],2000000)
        self.assertEqual(saved.payment_ceilings()['base:1'],0)
        self.assertEqual(saved.payment_ceilings()['bonus:calendar-restructure:convert-2027'],100000)
        self.assertEqual(seller.generation_cash(gid).amount,5100000)
        self.assertEqual(seller.generation_cash(gid).paid,5100000)
        self.assertEqual(buyer.active_contract('v').offer.salaries,(1900000,2000000))
        self.assertEqual(buyer.active_contract('v').offer.guaranteed_salaries,(1900000,0))
        self.assertEqual(buyer.active_contract('v').bonus_layers,())
        self.assertEqual(buyer.generation_cash(buyerid).amount,3900000)
        self.assertEqual(buyer.generation_cash(buyerid).paid_components,())
        fixture.pay('b','base:0',1900000);fixture.roll(('a','b'),2027)
        buyer=store.load_team('b');self.assertEqual(buyer.active_contract('v').elapsed_years,1)
        self.assertEqual(store.load_team('a').generation_accounting(gid),saved)
        store.release_calendar_preseason_veteran('b','buyer-release','v',generation_id=buyerid,
            scope=PreseasonReleaseScope(2028,date(2028,6,1),date(2028,9,10),EXCLUDED_LIABILITIES,
                True,True,0,'synthetic release'),discount=DiscountProfile(2028,Fraction(0),'synthetic rate'),
            payment_year_offsets=(0,),expected_revision=buyer.revision,access_check=lambda:None)
        restarted=FranchiseStore(fixture.path);buyer=restarted.load_team('b')
        self.assertEqual(buyer.generation_cash(buyerid).amount,1900000)
        self.assertEqual(buyer.generation_cash(buyerid).paid,1900000)
        self.assertEqual(buyer.generation_cash(buyerid).paid_components,(('base:0',1900000),))
        self.assertEqual(buyer.generation_accounting(buyerid).release_calendar_year,2028)
        self.assertEqual(restarted.load_team('a').generation_accounting(gid),saved)
        before=fixture.path.read_bytes()
        retry=Bridge(restarted,provider=forbidden,access_check=lambda:None)
        self.assertEqual(retry.handle(request),full)
        self.assertEqual(retry.handle(compact_request),compact)
        self.assertEqual(fixture.path.read_bytes(),before)
