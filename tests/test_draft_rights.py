from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger,Offer,Rejected
from franchise.control import AccessDisabled
from franchise.draft_order import DraftOrder,DraftSlot
from franchise.rookie import RookieScale
from franchise.store import FranchiseStore


class DraftRightsTests(unittest.TestCase):
    def setup_store(self,directory):
        store=FranchiseStore(Path(directory)/'state.sqlite')
        for team in ('a','b'):
            store.create_team(team,Ledger.from_opening(OpeningBooks(),cap=30,roster_reserve=0,max_bonus_years=5,
                veteran_minimums={},rookies={p:RookieScale(1,(1,)*4,1,30,150) for p in ('p','q')},
                rookie_year_one_allocation=30,rookie_total_allocation=150))
        order=DraftOrder('fixture-draft',2026,'synthetic two-pick order',
            (DraftSlot(1,1,'a'),DraftSlot(2,1,'b')),frozenset({'p','q'}))
        store.initialize_draft(order)
        return store,order

    def pick(self,store,team,pick,player,revision=0,check=lambda:None):
        return store.commit_draft_pick(team,'pick-'+str(pick),'fixture-draft',pick,Offer(player,(10,)*4,0),revision,
            funding_source='synthetic slot contract estimate',access_check=check,decision_mode='manual')

    def test_order_rights_funding_restart_and_owner_signing(self):
        with tempfile.TemporaryDirectory() as directory:
            store,order=self.setup_store(directory)
            store.initialize_draft(order)
            offer=Offer('p',(10,)*4,0)
            self.assertEqual(store.preview_draft_offer('a',offer,0)['room_after'],20)
            with self.assertRaisesRegex(Rejected,'not been selected'):
                store.sign('a','early',offer,0)
            with self.assertRaisesRegex(Rejected,'order'):
                self.pick(store,'b',2,'q')
            first=self.pick(store,'a',1,'p')
            restarted=FranchiseStore(store.path)
            self.assertEqual(self.pick(restarted,'a',1,'p'),first)
            self.assertEqual(restarted.load_team('a').room,20)
            self.assertEqual(restarted.load_team('a').charges,(0,))
            with self.assertRaisesRegex(Rejected,'rights'):
                restarted.sign('b','steal',offer,0)
            with self.assertRaisesRegex(Rejected,'remain reserved'):
                restarted.withdraw_draft_funding('a','withdraw','p',1,source='fixture')
            self.pick(restarted,'b',2,'q')
            restarted.sign('a','contract',offer,1)
            self.assertEqual(FranchiseStore(store.path).load_team('a').room,20)
            self.assertEqual(restarted.load_team('a').charges[0],10)
            self.assertEqual(restarted.load_team('a').financial_snapshot()['draft_rights']['p']['overall_pick'],1)

    def test_shutdown_and_over_cap_pick_commit_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            store,_=self.setup_store(directory)
            def disabled():
                raise AccessDisabled('synthetic switch')
            with self.assertRaises(AccessDisabled):
                self.pick(store,'a',1,'p',check=disabled)
            self.assertEqual(store.load_team('a').revision,0)
            with self.assertRaises(Rejected):
                store.commit_draft_pick('a','bad','fixture-draft',1,Offer('p',(30,)*4,4),0,
                    funding_source='fixture',access_check=lambda:None,decision_mode='manual')
            self.assertNotIn('draft_rights',store.load_team('a').financial_snapshot())
            self.pick(store,'a',1,'p')
            with self.assertRaises(Rejected):
                self.pick(store,'b',2,'p')
            self.assertEqual(store.load_team('b').revision,0)

    def test_ai_pick_commits_only_latest_recorded_matching_recommendation(self):
        import json
        from franchise.draft import DraftScouting,Prospect
        from franchise.performance import PerformanceEvidence,Observation
        from franchise.store import StoredLedger
        with tempfile.TemporaryDirectory() as directory:
            store,_=self.setup_store(directory)
            evidence=PerformanceEvidence('p','synthetic season','cpu_played',
                (Observation('receptions',50,'synthetic fixture'),),'synthetic prospect record')
            offer=Offer('p',(10,)*4,0)
            prospect=Prospect('p','WR','slot','synthetic college','fixture',(evidence,),{},'fixture',offer,'fixture estimate')
            session=DraftScouting(StoredLedger(store,'a'),access_check=lambda:None)
            session.recommend('advice',lambda _:json.dumps({'action':'recommend','player_id':'p','reason':'Observed production','uncertainty':'Targets unknown'}),
                expected_revision=0,draft_round=1,overall_pick=1,prospects=(prospect,),team_needs=[])
            with self.assertRaises(Rejected):
                store.commit_draft_pick('a','bad','fixture-draft',1,offer,0,funding_source='fixture estimate',
                    access_check=lambda:None,decision_mode='ai',scouting_request_id='invented')
            store.commit_draft_pick('a','ai-pick','fixture-draft',1,offer,0,funding_source='fixture estimate',
                access_check=lambda:None,decision_mode='ai',scouting_request_id='advice')
            self.assertEqual(FranchiseStore(store.path).load_team('a').revision,1)
            self.assertEqual(store.load_team('a').room,20)

    def test_ai_pick_rejects_personality_established_after_advice(self):
        import json
        from franchise.draft import DraftScouting,Prospect
        from franchise.performance import PerformanceEvidence
        from franchise.store import StoredLedger
        with tempfile.TemporaryDirectory() as directory:
            store,_=self.setup_store(directory)
            offer=Offer('p',(10,)*4,0)
            evidence=PerformanceEvidence('p','fixture season','cpu_played',(),'unavailable fixture evidence')
            prospect=Prospect('p','WR','slot','fixture college','fixture',(evidence,),{},'authored fixture',offer,'fixture estimate')
            DraftScouting(StoredLedger(store,'a'),access_check=lambda:None).recommend('advice',lambda _:json.dumps(
                {'action':'recommend','player_id':'p','reason':'Role fits','uncertainty':'Production unavailable'}),
                expected_revision=0,draft_round=1,overall_pick=1,prospects=(prospect,),team_needs=[])
            store.bind_actor('b','p',{'money':0.8},{},access_check=lambda:None)
            before=store.load_team('a').financial_snapshot()
            with self.assertRaisesRegex(Rejected,'cross-team'):
                store.commit_draft_pick('a','stale','fixture-draft',1,offer,0,funding_source='fixture estimate',
                    access_check=lambda:None,decision_mode='ai',scouting_request_id='advice')
            self.assertEqual(store.load_team('a').financial_snapshot(),before)
            self.assertEqual(store.load_team('b').revision,0)
