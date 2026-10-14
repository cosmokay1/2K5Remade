"""Versioned reads distinguish immutable terms, amendment history and current time."""
import copy
import json
import unittest
from franchise.cap import Rejected
from franchise.store import FranchiseStore
from tests import test_calendar_restructure_store,test_layered_restructure_store,test_layered_release_store,test_layered_trade_store


class CalendarHistoryContextTests(unittest.TestCase):
    def fixture(self,module,class_name):
        fixture=getattr(module,class_name)();fixture.setUp();self.addCleanup(fixture.doCleanups)
        return fixture

    def context(self,fixture,team='a',gid=None):
        return fixture.store.calendar_contract_context(team,gid or fixture.gid,context_format='calendar_v4')

    def test_plain_and_single_amendment_reads_preserve_old_format_shapes(self):
        fixture=self.fixture(test_calendar_restructure_store,'CalendarRestructureStoreTests')
        before=fixture.path.read_bytes();plain=self.context(fixture)
        self.assertEqual(len(plain),11);self.assertEqual(plain['format'],5)
        self.assertIsNone(plain['amendment_history'])
        self.assertEqual(plain['original_contract']['elapsed_years'],0)
        self.assertEqual(fixture.path.read_bytes(),before)
        fixture.amend();old=fixture.store.calendar_contract_context('a',fixture.gid,context_format='calendar_v3')
        context=self.context(fixture);normalized=copy.deepcopy(context)
        normalized.pop('original_contract');normalized.pop('amendment_history');normalized['format']=4
        self.assertEqual(json.dumps(normalized,sort_keys=True),json.dumps(old,sort_keys=True))
        history=context['amendment_history'];self.assertEqual(history['format'],1)
        self.assertEqual(history['prior_restructures'],[])
        self.assertEqual(history['latest_restructure']['contract'],context['economic_archive']['contract'])
        self.assertEqual(history['latest_restructure']['original_contract']['elapsed_years'],1)
        self.assertEqual(context['original_contract']['elapsed_years'],0)

    def test_active_repeated_history_is_scoped_detached_and_never_rewrites_evidence(self):
        fixture=self.fixture(test_layered_restructure_store,'LayeredRestructureStoreTests');fixture.amend()
        fixture.store.bind_actor('a','v',{'money':0.8},{'trust':0.6},access_check=lambda:None)
        before=fixture.path.read_bytes();context=self.context(fixture)
        self.assertEqual(context['amendment_history'],fixture.store.load_team('a').generation_accounting(fixture.gid).amendment_history_snapshot())
        self.assertEqual(context['amendment_history']['latest_restructure']['contract'],context['economic_archive']['contract'])
        first=context['amendment_history']['prior_restructures'][0]['original_contract']
        birth=copy.deepcopy(context['original_contract']);birth['elapsed_years']=first['elapsed_years']
        self.assertEqual(first,birth)
        player=fixture.store.player_context('a','v',context_format='calendar_v4')
        self.assertEqual(player['calendar_contract_context'],context)
        self.assertIsNone(player['contract_accounting'])
        self.assertEqual(player['personality'],{'money':0.8});self.assertEqual(player['relationships'],{'trust':0.6})
        self.assertEqual(player['promise_history'],[])
        self.assertIsNone(fixture.store.player_context('b','v',context_format='calendar_v4')['calendar_contract_context'])
        with self.assertRaises(Rejected):fixture.store.calendar_contract_context('b',fixture.gid,context_format='calendar_v4')
        saved=copy.deepcopy(context);context['amendment_history']['prior_restructures'][0]['scope']['source']='mutated caller'
        context['original_contract']['offer']['salaries'][0]=1
        self.assertEqual(self.context(fixture),saved)
        self.assertEqual(FranchiseStore(fixture.path).calendar_contract_context('a',fixture.gid,context_format='calendar_v4'),saved)
        self.assertEqual(fixture.path.read_bytes(),before)

    def test_released_history_keeps_current_cash_and_closed_cursor_separate(self):
        fixture=self.fixture(test_layered_release_store,'LayeredReleaseStoreTests');fixture.release()
        context=self.context(fixture);history=copy.deepcopy(context['amendment_history'])
        self.assertEqual(context['calendar_accounting']['status'],'released')
        self.assertFalse(context['calendar_accounting']['ownership_current'])
        self.assertIsNone(context['calendar_accounting']['current_contract'])
        self.assertEqual(context['release_calendar']['elapsed_years'],2)
        self.assertEqual(context['economic_archive']['cash_obligation']['paid'],7000000)
        fixture.next_year();before=fixture.path.read_bytes();advanced=self.context(fixture)
        self.assertEqual(advanced['amendment_history'],history)
        self.assertEqual(advanced['original_contract'],context['original_contract'])
        self.assertEqual(advanced['calendar_accounting']['annual_charges'],[])
        self.assertEqual(advanced['economic_archive']['cash_obligation'],context['economic_archive']['cash_obligation'])
        self.assertEqual(fixture.path.read_bytes(),before)

    def test_assigned_history_stays_seller_only_after_buyer_payment_and_roll(self):
        fixture=self.fixture(test_layered_trade_store,'LayeredTradeStoreTests');receipt=fixture.trade()
        seller=self.context(fixture);buyer=self.context(fixture,'b',receipt['buyer_generation_id'])
        self.assertEqual(seller['calendar_accounting']['status'],'assigned')
        self.assertEqual(seller['trade_calendar']['elapsed_years'],2)
        self.assertEqual(seller['amendment_history'],receipt['amendment_history'])
        self.assertIsNone(buyer['amendment_history']);self.assertEqual(buyer['original_contract'],buyer['economic_archive']['contract'])
        fixture.fixture.pay('b','base:0',1800000);fixture.fixture.roll(('a','b'),2028)
        before=fixture.path.read_bytes();advanced=self.context(fixture)
        self.assertEqual(advanced['amendment_history'],seller['amendment_history'])
        self.assertEqual(advanced['original_contract'],seller['original_contract'])
        self.assertEqual(fixture.path.read_bytes(),before)

    def test_expired_history_remains_complete_and_unknown_formats_reject(self):
        fixture=self.fixture(test_layered_restructure_store,'LayeredRestructureStoreTests');fixture.amend();fixture.expire()
        before=fixture.path.read_bytes();context=self.context(fixture)
        self.assertEqual(context['calendar_accounting']['status'],'expired')
        self.assertEqual(context['economic_archive']['status'],'active')
        self.assertFalse(context['calendar_accounting']['ownership_current'])
        self.assertEqual(len(context['amendment_history']['prior_restructures']),1)
        for value in ('invented',True,4,None):
            with self.subTest(value=value),self.assertRaises(ValueError):
                fixture.store.calendar_contract_context('a',fixture.gid,context_format=value)
        self.assertEqual(fixture.path.read_bytes(),before)
