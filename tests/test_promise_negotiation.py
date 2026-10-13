from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger,Offer
from franchise.control import AccessDisabled
from franchise.negotiation import Negotiation
from franchise.promises import PromiseGoal
from franchise.store import FranchiseStore,StoredLedger


class PromiseNegotiationTests(unittest.TestCase):
    def setup_session(self,directory,access=lambda:None):
        store=FranchiseStore(Path(directory)/'state.sqlite')
        store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'p':(1,)}))
        return store,self.session(store,access)
    def session(self,store,access=lambda:None):
        return Negotiation(StoredLedger(store,'a'),player_id='p',personality={'security':0.8},
                           performance={'source':'synthetic fixture'},relationships={},access_check=access)
    def goal(self,target=8):
        return PromiseGoal('starts','starts',target,80,'synthetic next season','authored proposal')
    def accept(self,_):
        return json.dumps({'action':'accept','reason':'The starting role matters to me',
            'salaries':None,'signing_bonus':None,'guaranteed_salaries':None,'promise_goals':None})

    def test_goals_commit_with_contract_and_restart_recall_requires_same_terms(self):
        with tempfile.TemporaryDirectory() as directory:
            store,session=self.setup_session(directory)
            offer=Offer('p',(20,),0)
            goals=(self.goal(),)
            event=session.respond('deal',offer,self.accept,promise_goals=goals)
            self.assertEqual(event['promise_goals'],[asdict(goals[0])])
            self.assertEqual(event['outcome'],'signed')
            restarted=FranchiseStore(store.path)
            def forbidden(_):
                raise AssertionError('Promise agreement cannot be regenerated')
            self.assertEqual(self.session(restarted).respond('deal',offer,forbidden,promise_goals=goals),event)
            with self.assertRaisesRegex(ValueError,'different promises'):
                self.session(restarted).respond('deal',offer,forbidden,promise_goals=(self.goal(12),))
            self.assertEqual(restarted.load_team('a').charges[0],20)

    def test_counter_must_explicitly_preserve_change_or_withdraw_goals(self):
        with tempfile.TemporaryDirectory() as directory:
            store,session=self.setup_session(directory)
            offer=Offer('p',(20,),0)
            counter={'action':'counter','reason':'I want twelve starts','salaries':[20],
                     'signing_bonus':0,'guaranteed_salaries':None}
            with self.assertRaisesRegex(ValueError,'explicitly'):
                session.respond('missing',offer,lambda _:json.dumps(counter),promise_goals=(self.goal(),))
            event=session.respond('counter',offer,lambda _:json.dumps({**counter,'promise_goals':[asdict(self.goal(12))]}),promise_goals=(self.goal(),))
            self.assertEqual(event['counter_promises'][0]['target'],12)
            self.assertEqual(store.load_team('a').revision,0)
            self.assertEqual(store.negotiation_history('a','p')[0],event)

    def test_promises_cannot_override_cap_or_remote_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            store,session=self.setup_session(directory)
            event=session.respond('overcap',Offer('p',(101,),0),self.accept,promise_goals=(self.goal(),))
            self.assertEqual(event['outcome'],'accounting_rejected')
            self.assertEqual(store.load_team('a').revision,0)
            enabled=True
            def check():
                if not enabled:
                    raise AccessDisabled('fixture switch')
            session=self.session(store,check)
            def shutdown(context):
                nonlocal enabled
                enabled=False
                return self.accept(context)
            with self.assertRaises(AccessDisabled):
                session.respond('disabled',Offer('p',(20,),0),shutdown,promise_goals=(self.goal(),))
            self.assertEqual(store.load_team('a').revision,0)
