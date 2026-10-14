from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks,ActiveContract
from franchise.cap import Ledger,Offer,Rejected
from franchise.initialization import initial_actor
from franchise.store import FranchiseStore


class FranchiseInitializationTests(unittest.TestCase):
    def test_observed_free_agent_initializes_without_inventing_salary_classification(self):
        from franchise.bridge import Bridge
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'state.sqlite'; store = FranchiseStore(path)
            ledger = Ledger.from_opening(OpeningBooks(), cap=100, roster_reserve=0,
                max_bonus_years=5, veteran_minimums={}, observed_player_ids=frozenset({'pending'}),
                observed_player_source='authored pinned roster')
            store.create_franchise({'a':ledger}, seed='observed-world')
            reopened = FranchiseStore(path); context = reopened.player_context('a','pending')
            self.assertTrue(context['initialized']); self.assertTrue(context['classification_pending'])
            self.assertEqual(context['personality'], initial_actor('observed-world','pending')['personality'])
            self.assertEqual(reopened.registered_players('a')['players'][0]['contract_classification'],'pending')
            self.assertIsNone(reopened.load_team('a').negotiation_context('pending')['veteran_minimum_salaries'])
            before = reopened.load_team('a').financial_snapshot()
            with self.assertRaises(Rejected): reopened.sign('a','manual',Offer('pending',(10,),0),0)
            provider = Mock(side_effect=AssertionError('Unclassified player must not reach model'))
            bridge = Bridge(reopened,provider=provider,access_check=lambda:None)
            reply=bridge.handle({'protocol':1,'request_id':'unknown-floor','operation':'negotiate','team_id':'a',
                'offer':{'player_id':'pending','salaries':[10],'signing_bonus':0},'expected_revision':0,
                'timeout_ms':1000,'personality':{},'performance':{},'relationships':{}})
            self.assertEqual(reply['error'],'state_rejected'); provider.assert_not_called()
            self.assertEqual(reopened.load_team('a').financial_snapshot(),before)

    def test_observed_identity_registry_cannot_authorize_missing_owned_classification(self):
        with self.assertRaises(ValueError):
            Ledger.from_opening(OpeningBooks(contracts=(ActiveContract(Offer('pending',(10,),0),'authored'),)),
                cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={},
                observed_player_ids=frozenset({'pending'}),observed_player_source='authored snapshot')
        with self.assertRaises(ValueError):
            Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,max_bonus_years=5,
                veteran_minimums={},observed_player_ids=frozenset({'pending'}))

    def ledger(self,owned):
        return Ledger.from_opening(OpeningBooks(contracts=(ActiveContract(Offer(owned,(10,),0),'synthetic roster'),)),
            cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={'p':(1,),'q':(1,),'free-agent':(1,)})

    def test_creation_assigns_all_players_and_preserves_identity_across_teams_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            origin=store.create_franchise({'b':self.ledger('q'),'a':self.ledger('p')},seed='fixture-world')
            self.assertEqual(origin['seed'],'fixture-world')
            reopened=FranchiseStore(store.path)
            for team in ('a','b'):
                ledger=reopened.load_team(team)
                self.assertEqual(set(ledger._actors),{'p','q','free-agent'})
                self.assertEqual(ledger._actors['p'],initial_actor('fixture-world','p'))
                self.assertEqual(ledger.revision,0)
                self.assertEqual(ledger.charges[0],10)
            actor=reopened.bind_actor('a','p',{'money':0},{'trust':0},access_check=lambda:None)
            self.assertEqual(actor,initial_actor('fixture-world','p'))
            with self.assertRaises(Rejected):
                reopened.create_franchise({'a':self.ledger('p')},seed='reroll')

    def test_new_worlds_vary_and_player_streams_do_not_depend_on_roster_order(self):
        self.assertEqual(initial_actor('world','p'),initial_actor('world','p'))
        self.assertNotEqual(initial_actor('world','p'),initial_actor('different-world','p'))
        self.assertNotEqual(initial_actor('world','p'),initial_actor('world','q'))

    def test_invalid_roster_creation_rolls_back_every_team_and_personality(self):
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            with self.assertRaises(Rejected):
                store.create_franchise({'a':self.ledger('p'),'b':self.ledger('p')},seed='fixture-world')
            with self.assertRaises(Rejected):store.load_team('a')
            store.create_franchise({'a':self.ledger('p')},seed='fixture-world')
            self.assertEqual(store.load_team('a').revision,0)

    def test_late_team_creation_and_missing_actor_integrity(self):
        import sqlite3
        from contextlib import closing
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            store.create_franchise({'a':self.ledger('p')},seed='world')
            store.create_team('b',self.ledger('q'))
            self.assertEqual(set(store.load_team('b')._actors),{'p','q','free-agent'})
            with closing(sqlite3.connect(store.path)) as db:
                db.execute("DELETE FROM events WHERE team_id='b' AND request_key='actor:q'")
                db.commit()
            with self.assertRaisesRegex(ValueError,'coverage'):
                store.load_team('b')

    def test_initial_relationship_tampering_is_not_a_valid_consequence(self):
        import json,sqlite3
        from contextlib import closing
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            store.create_franchise({'a':self.ledger('p')},seed='world')
            with closing(sqlite3.connect(store.path)) as db:
                id,text=db.execute("SELECT id,payload FROM events WHERE request_key='actor:p'").fetchone()
                payload=json.loads(text)
                payload['actor']['relationships']['trust']=0.9
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),id))
                db.commit()
            with self.assertRaisesRegex(ValueError,'origin'):
                store.load_team('a')

    def test_seed_encoding_golden_traits_and_legacy_authored_actors(self):
        self.assertNotEqual(initial_actor('a\0b','c'),initial_actor('a','b\0c'))
        personality=initial_actor('golden-world','player-1')['personality']
        self.assertEqual({key:personality[key] for key in ('money','security','playing_time','winning','loyalty','patience','risk_tolerance')},
            {'money':0.660713,'security':0.731402,'playing_time':0.373895,'winning':0.544513,'loyalty':0.670475,'patience':0.609277,'risk_tolerance':0.142663})
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            store.create_team('a',self.ledger('p'))
            expected=store.bind_actor('a','p',{'money':0.8},{'trust':0.6},access_check=lambda:None)
            self.assertEqual(FranchiseStore(store.path).load_team('a')._actors['p'],expected)

    def test_default_seed_differs_between_new_franchises(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            first=FranchiseStore(Path(a)/'state.sqlite').create_franchise({'a':self.ledger('p')})
            second=FranchiseStore(Path(b)/'state.sqlite').create_franchise({'a':self.ledger('p')})
            self.assertNotEqual(first['seed'],second['seed'])
