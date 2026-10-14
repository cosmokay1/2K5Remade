import json
from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger,Offer
from franchise.cash import CashObligation
from franchise.negotiation import Negotiation
from franchise.store import FranchiseStore,StoredLedger
from tests import test_releases


class NegotiationAvailabilityTests(unittest.TestCase):
    def session(self,store,team):
        return Negotiation(StoredLedger(store,team),player_id='v',personality={},performance={},
            relationships={},access_check=lambda:None)

    def test_release_retains_story_but_old_receipt_does_not_close_new_dialogue(self):
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
                max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
            original=self.session(store,'a').respond('original',Offer('v',(10,20,30),9,(0,20,10)),
                lambda _:json.dumps({'action':'accept','reason':'Initial agreement','salaries':None,'signing_bonus':None}))
            store.initialize_cash('a',(CashObligation('contract:v','v',69,9,'synthetic paid bonus',(('signing_bonus',9),)),),source='synthetic cash')
            plan=test_releases.PreseasonReleaseTests().plan()
            store.release_preseason_veteran('a','release','v',scope=plan.scope,discount=plan.discount,
                payment_year_offsets=(0,1,2),expected_revision=2,access_check=lambda:None)
            session=self.session(FranchiseStore(store.path),'a')
            def forbidden(_):raise AssertionError('Old receipt must not call provider')
            self.assertEqual(session.respond('original',Offer('v',(10,20,30),9,(0,20,10)),forbidden),original)
            before=store.load_team('a').financial_snapshot()
            def reject(context):
                self.assertFalse(context['accounting']['current_contract_owned'])
                self.assertEqual(context['history'][0]['outcome'],'signed')
                return json.dumps({'action':'reject','reason':'Remembered earlier agreement','salaries':None,'signing_bonus':None})
            self.assertEqual(session.respond('new-dialogue',Offer('v',(1,),0),reject)['outcome'],'player_rejected')
            self.assertEqual(store.load_team('a').financial_snapshot(),before)
            # The generation guard still prevents a return signing from erasing old debt.
            with self.assertRaisesRegex(ValueError,'generation'):
                store.sign('a','return',Offer('v',(1,),0),before['revision'])

    def test_current_league_ownership_blocks_new_provider_calls_even_without_signed_story(self):
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            fixture=test_releases.PreseasonReleaseTests()
            for team in ('a','b'):
                store.create_team(team,Ledger.from_opening(OpeningBooks(contracts=(fixture.contract(),)) if team=='a' else OpeningBooks(),
                    cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
            def forbidden(_):raise AssertionError('Owned player must not trigger free-agent inference')
            for team in ('a','b'):
                with self.subTest(team=team),self.assertRaisesRegex(ValueError,'currently signed'):
                    self.session(store,team).respond('new',Offer('v',(1,),0),forbidden)
