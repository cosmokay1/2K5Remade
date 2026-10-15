"""Atomic engine settlement of acceptance; no guest write or save verification."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger, Offer, Rejected
from franchise.control import AccessDisabled
from franchise.guest_contracts import GuestContractTerms
from franchise.store import FranchiseStore


class ProposalSettlementTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'franchise.sqlite'
        self.store=FranchiseStore(self.path)
        for team in ('a','b'):
            self.store.create_team(team,Ledger.from_opening(OpeningBooks(),cap=100_000_000,
                roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1000,)*15,'other':(1000,)*15}))
        self.store.initialize_cash('a',(),source='Authored complete empty opening cash')
        self.revision=self.store.load_team('a').revision
        self.offer=GuestContractTerms(829,4,1,2).to_offer('v')
        self.calls=0
        def provider(_):
            self.calls+=1
            return json.dumps(dict(action='accept',reason='An authored agreement',salaries=None,signing_bonus=None))
        self.bridge=Bridge(self.store,provider=provider,access_check=lambda:None)

    def propose(self,**changes):
        request=dict(protocol=1,request_id='proposal',operation='negotiate_proposal',team_id='a',
            offer=self.offer.to_dict(),expected_revision=self.revision,timeout_ms=1000,
            personality={},performance={'games':16},relationships={},contract_format='original_fxg_v1')
        reply=self.bridge.handle({**request,**changes})
        self.assertIsNone(reply['error'],reply)
        return reply['result']

    def settle(self,store=None,**changes):
        return (store or self.store).commit_accepted_proposal('a','proposal',
            changes.get('request_id','settlement'),changes.get('revision',self.revision),
            access_check=changes.get('access_check',lambda:None))

    def test_terms_cash_promises_story_and_retry_survive_restart(self):
        goals=[dict(goal_id='starter',metric='starts',target=12,importance=80,window='season',source='Authored offer')]
        event=self.propose(promise_goals=goals)
        before=self.store.load_team('a').financial_snapshot()
        receipt=self.settle()
        reopened=FranchiseStore(self.path)
        ledger=reopened.load_team('a')
        self.assertEqual(receipt.offer,self.offer)
        self.assertEqual(ledger.charges,tuple(event['proposal_preview']['contract_charges']))
        self.assertEqual(ledger.revision,before['revision']+1)
        self.assertEqual(ledger.cash_snapshot()['nominal_total'],sum(self.offer.salaries)+self.offer.signing_bonus)
        self.assertEqual(ledger._promise_agreements,{'settlement':{'player_id':'v','goals':goals}})
        history=reopened.negotiation_history('a','v')
        self.assertEqual([e['request_id'] for e in history],['proposal','settlement'])
        self.assertEqual(history[0],event)
        self.assertEqual(history[1]['outcome'],'signed')
        self.assertEqual(history[1]['reason'],event['reason'])
        self.assertEqual(history[1]['evidence'],event['evidence'])
        self.assertEqual(history[1]['guest_offer'],event['guest_offer'])
        self.assertEqual(history[1]['decision_mode'],'proposal_settlement')
        self.assertEqual(self.settle(reopened),receipt)
        self.assertEqual(reopened.load_team('a').financial_snapshot(),ledger.financial_snapshot())
        self.assertEqual(self.calls,1)
        with self.assertRaises(Rejected): self.settle(request_id='second-settlement')
        with self.assertRaises(Rejected): self.settle(revision=self.revision+1)

    def test_softdrink_scaled_acceptance_keeps_exact_game_words(self):
        from franchise.guest_contracts import guest_offer_encoding
        offer=GuestContractTerms(829,4,1,2).to_offer('v',contract_format='softdrink_fxg_v1')
        event=self.propose(team_id='b',offer=offer.to_dict(),expected_revision=0,
                           contract_format='softdrink_fxg_v1')
        receipt=self.store.commit_accepted_proposal('b','proposal','settlement',0,access_check=lambda:None)
        self.assertEqual(receipt.offer,offer)
        self.assertEqual(event['guest_offer'],guest_offer_encoding(offer,contract_format='softdrink_fxg_v1'))
        reopened=FranchiseStore(self.path)
        self.assertEqual(reopened.load_team('b').charges,tuple(event['proposal_preview']['contract_charges']))
        self.assertEqual(reopened.negotiation_history('b','v')[-1]['guest_offer'],event['guest_offer'])

    def test_missing_rejected_or_superseded_acceptance_cannot_settle(self):
        with self.assertRaises(Rejected): self.settle()
        self.propose()
        self.bridge.provider=lambda _:json.dumps(dict(action='reject',reason='Changed mind',salaries=None,signing_bonus=None))
        self.assertEqual(self.propose(request_id='new-response')['outcome'],'player_rejected')
        with self.assertRaisesRegex(Rejected,'current negotiation'): self.settle()
        with self.assertRaisesRegex(Rejected,'accepted proposal'):
            self.store.commit_accepted_proposal('a','new-response','rejected-settlement',self.revision,access_check=lambda:None)
        self.assertEqual(self.store.load_team('a').charges,(0,))

    def test_unrelated_negotiation_does_not_invalidate_accepted_player(self):
        self.propose()
        self.propose(request_id='other-proposal',offer=Offer('other',self.offer.salaries,self.offer.signing_bonus).to_dict())
        self.settle()
        self.assertEqual(self.store.load_team('a').financial_snapshot()['signed_players'],['v'])

    def test_revision_and_foreign_ownership_are_rechecked(self):
        self.propose()
        self.store.sign('a','unrelated',Offer('other',(1000,),0),self.revision)
        with self.assertRaises(Rejected): self.settle()
        self.store.sign('b','foreign',self.offer,0)
        with self.assertRaises(Rejected): self.settle()
        self.assertNotIn('v',self.store.load_team('a').financial_snapshot()['signed_players'])

    def test_shutdown_after_insert_rolls_back_all_financial_effects(self):
        self.propose()
        before=self.store.load_team('a').financial_snapshot()
        checks=0
        def disable():
            nonlocal checks
            checks+=1
            if checks==2: raise AccessDisabled('Disabled before commit')
        with self.assertRaises(AccessDisabled): self.settle(access_check=disable)
        self.assertEqual(checks,2)
        reopened=FranchiseStore(self.path)
        self.assertEqual(reopened.load_team('a').financial_snapshot(),before)
        self.assertEqual(reopened.load_team('a').cash_snapshot()['nominal_total'],0)
        self.assertEqual(len(reopened.negotiation_history('a','v')),1)
        self.settle(reopened)
        self.assertEqual(self.calls,1)

    def test_abrupt_exit_before_sql_commit_restarts_without_phantom_contract(self):
        self.propose()
        code='''import os,sys
from franchise.store import FranchiseStore
checks=0
def terminate():
 global checks
 checks+=1
 if checks==2: os._exit(73)
FranchiseStore(sys.argv[1]).commit_accepted_proposal('a','proposal','settlement',int(sys.argv[2]),access_check=terminate)
'''
        child=subprocess.run([sys.executable,'-c',code,str(self.path),str(self.revision)],timeout=15)
        self.assertEqual(child.returncode,73)
        reopened=FranchiseStore(self.path)
        self.assertEqual(reopened.load_team('a').revision,self.revision)
        self.assertEqual(reopened.load_team('a').cash_snapshot()['nominal_total'],0)
        self.settle(reopened)
        self.assertEqual(self.calls,1)

    def test_competing_settlement_ids_cannot_consume_acceptance_twice(self):
        self.propose()
        def attempt(request):
            try: return self.settle(FranchiseStore(self.path),request_id=request)
            except Rejected: return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(attempt,['first','second']))
        self.assertEqual(sum(r is not None for r in results),1)
        self.assertEqual(self.store.load_team('a').revision,self.revision+1)
        self.assertEqual(len(self.store.negotiation_history('a','v')),2)

    def test_historical_retry_preserves_later_financial_changes(self):
        self.propose();receipt=self.settle()
        self.store.sign('a','later',Offer('other',(2000,),0),self.revision+1)
        before=self.store.load_team('a').financial_snapshot()
        self.assertEqual(self.settle(FranchiseStore(self.path)),receipt)
        self.assertEqual(self.store.load_team('a').financial_snapshot(),before)

    def test_same_settlement_retry_is_atomic_across_connections(self):
        self.propose()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:self.settle(FranchiseStore(self.path)),range(2)))
        self.assertEqual(results[0],results[1])
        self.assertEqual(self.store.load_team('a').revision,self.revision+1)

    def test_replay_rejects_changed_settlement_story_or_missing_source_link(self):
        self.propose();self.settle()
        with closing(sqlite3.connect(self.path)) as db:
            original=db.execute("SELECT payload FROM events WHERE request_key='sign:settlement'").fetchone()[0]
        for mutation in ('reason','link','offer'):
            payload=json.loads(original)
            if mutation=='reason': payload['story']['reason']='Not the accepted reason'
            elif mutation=='link': del payload['proposal_request_id']
            else: payload['offer']['salaries'][0]+=1000
            with closing(sqlite3.connect(self.path)) as db,db:
                db.execute("UPDATE events SET payload=? WHERE request_key='sign:settlement'",(json.dumps(payload),))
            with self.assertRaises(ValueError): self.store.load_team('a')
            with closing(sqlite3.connect(self.path)) as db,db:
                db.execute("UPDATE events SET payload=? WHERE request_key='sign:settlement'",(original,))
        self.store.load_team('a')

    def test_manual_path_cannot_relabel_a_settlement_or_bypass_access(self):
        self.propose();self.settle()
        story=self.store.negotiation_history('a','v')[-1]
        with self.assertRaises(Rejected): self.store.sign('a','forged',self.offer,self.revision,story=story)
        def disabled(): raise AccessDisabled('Disabled')
        with self.assertRaises(AccessDisabled): self.settle(access_check=disabled)
        with self.assertRaises(ValueError): self.settle(access_check=None)
        with self.assertRaises(ValueError): self.settle(request_id='proposal')
