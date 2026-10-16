"""One offline agent/consent/settlement/reopen loop; never a game application."""
from pathlib import Path
import copy
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock

from franchise.books import OpeningBooks
from franchise.cap import Ledger,Offer,Rejected
from franchise.legacy_amendments import RULE,FullYearAmendmentScope
from franchise.legacy_contracts import LegacyContract
from franchise.negotiation import Negotiation
from franchise.store import FranchiseStore,StoredLedger
from franchise.bridge import Bridge


class LegacyAmendmentNegotiationTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.path=Path(self.temporary.name)/'franchise.sqlite';self.store=FranchiseStore(self.path)
        self.store.create_franchise({'Giants':Ledger.from_opening(OpeningBooks(legacy_contracts=(
            LegacyContract('dart',348,5,6,3,3,'authored original',4),)),cap=301200000,
            roster_reserve=1000000,max_bonus_years=5,veteran_minimums={'dart':(1000000,)*10})},seed='amendment-negotiation')
        self.offer=Offer('dart',(4708000,7060000,9412000),21180000)
        self.accept=Mock(return_value=json.dumps(dict(action='accept',reason='The bonus and annual pay work for us.',salaries=None,signing_bonus=None)))

    def session(self,store=None,*,access=None,amendment=True):
        store=store or self.store;actor=store.player_context('Giants','dart')
        return Negotiation(StoredLedger(store,'Giants',amendment_rule=RULE if amendment else None),
            player_id='dart',personality=actor['personality'],relationships=actor['relationships'],
            performance={'passing_yards':3100,'games':17},access_check=access or (lambda:None),proposal_only=True)

    def propose(self,name='offer',offer=None,provider=None,revision=0):
        return self.session().respond(name,offer or self.offer,provider or self.accept,expected_revision=revision)

    def settle(self,proposal='offer',request='agreement',revision=0,access=None):
        return self.store.commit_accepted_amendment('Giants',proposal,request,revision,
            scope=FullYearAmendmentScope(0,'authored before regular season'),access_check=access or (lambda:None))

    def test_complete_engine_loop_preserves_bonus_ownership_actor_and_replays(self):
        before=self.store.load_team('Giants').financial_snapshot();actor=self.store.player_context('Giants','dart')
        event=self.propose()
        self.assertEqual(event['outcome'],'accepted_amendment_proposal')
        self.assertEqual(self.store.load_team('Giants').financial_snapshot(),before)
        context=self.accept.call_args.args[0]
        self.assertEqual(context['decision_mode'],'amendment_proposal')
        self.assertEqual(context['accounting']['amendment_comparison']['carried_bonus_charges'],[2320000]*3)
        receipt=self.settle()
        self.assertFalse(receipt['guest_write_authorized'])
        self.assertEqual(receipt['new_cash_commitment'],42360000)
        reopened=FranchiseStore(self.path);ledger=reopened.load_team('Giants')
        self.assertEqual(ledger.revision,1);self.assertEqual(ledger.charges,(14088000,16440000,18792000))
        self.assertEqual(ledger.financial_snapshot()['signed_players'],['dart'])
        self.assertEqual(reopened.player_context('Giants','dart')['personality'],actor['personality'])
        self.assertEqual(reopened.player_context('Giants','dart')['relationships'],actor['relationships'])
        self.assertEqual(self.settle(),receipt)
        self.assertEqual(reopened.load_team('Giants').financial_snapshot(),ledger.financial_snapshot())
        self.accept.assert_called_once()

    def test_rejection_and_counter_keep_reason_without_changing_contract(self):
        before=self.store.load_team('Giants').financial_snapshot()
        rejected=self.propose(provider=Mock(return_value=json.dumps(dict(action='reject',reason='Come back with a stronger guarantee.',salaries=None,signing_bonus=None))))
        self.assertEqual(rejected['outcome'],'player_rejected')
        self.assertEqual(rejected['reason'],'Come back with a stronger guarantee.')
        with self.assertRaises(Rejected):self.settle()
        counter=self.propose('counter',provider=Mock(return_value=json.dumps(dict(action='counter',reason='We need more up front.',salaries=[6000000,7000000],signing_bonus=8000000))))
        self.assertEqual(counter['outcome'],'counteroffer');self.assertEqual(counter['counter_validation']['status'],'eligible')
        self.assertEqual(self.store.load_team('Giants').financial_snapshot(),before)

    def test_second_agreement_retains_original_and_first_new_bonus(self):
        self.propose();self.settle()
        next_offer=Offer('dart',(1000000,),0)
        event=self.propose('second',offer=next_offer,revision=1)
        self.assertEqual(event['amendment_basis']['carried_bonus_charges'],[9380000]*3)
        receipt=self.settle('second','second-agreement',1)
        self.assertEqual(receipt['combined_player_charges'],[10380000,9380000,9380000])
        self.assertEqual(receipt['new_cash_commitment'],1000000)
        self.assertEqual(FranchiseStore(self.path).load_team('Giants').charges,(10380000,9380000,9380000))
        with self.assertRaises(Rejected):self.settle('offer','reuse-old',0)

    def test_stale_over_cap_and_below_floor_never_call_provider(self):
        for offer,revision in ((self.offer,1),(Offer('dart',(999999,),0),0),
                               (Offer('dart',(300000000,),10000000),0)):
            with self.subTest(offer=offer),self.assertRaises(Rejected):self.propose(offer=offer,revision=revision)
        self.accept.assert_not_called()
        self.assertEqual(self.store.load_team('Giants').revision,0)

    def test_acceptance_cannot_be_spent_after_financial_or_history_changes(self):
        self.propose();self.store.update_budget('Giants',cap=302000000,roster_reserve=1000000,expected_revision=0)
        with self.assertRaises(Rejected):self.settle()
        self.assertEqual(self.store.load_team('Giants').revision,1)

    def test_later_dialogue_invalidates_earlier_consent(self):
        self.propose();self.propose('later',provider=Mock(return_value=json.dumps(dict(action='reject',reason='We are waiting.',salaries=None,signing_bonus=None))))
        with self.assertRaises(Rejected):self.settle()
        self.assertEqual(self.store.load_team('Giants').revision,0)

    def test_shutdown_after_validation_rolls_back_whole_settlement(self):
        self.propose();before=self.store.load_team('Giants').financial_snapshot()
        access=Mock(side_effect=[None,False])
        with self.assertRaises(Rejected):self.settle(access=access)
        self.assertEqual(self.store.load_team('Giants').financial_snapshot(),before)
        self.assertEqual(access.call_count,2)
        self.assertEqual(self.settle()['combined_player_charges'],[14088000,16440000,18792000])

    def test_free_agent_settlement_cannot_consume_amendment_acceptance(self):
        self.propose()
        with self.assertRaises(Rejected):self.store.commit_accepted_proposal('Giants','offer','wrong-kind',0,access_check=lambda:None)
        self.assertEqual(self.store.load_team('Giants').revision,0)

    def test_mode_and_proposal_retries_cannot_change_terms_or_recall_after_settlement(self):
        event=self.propose();recalled=self.session().respond('offer',self.offer,self.accept,expected_revision=0)
        self.assertEqual(event,recalled);self.accept.assert_called_once()
        with self.assertRaises(Rejected):self.session(amendment=False).respond('offer',self.offer,self.accept,expected_revision=0)
        self.settle()
        with self.assertRaises(Rejected):self.session().respond('offer',self.offer,self.accept,expected_revision=1)
        self.accept.assert_called_once()

    def test_replay_rejects_tampered_bonus_debt_and_source_proposal(self):
        self.propose();self.settle()
        with sqlite3.connect(self.path) as db:
            key,payload=db.execute("SELECT id,payload FROM events WHERE kind='legacy_amendment'").fetchone()
            payload=json.loads(payload);payload['agreement']['carried_bonus_charges'][0]=0
            db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),key))
        with self.assertRaises(ValueError):FranchiseStore(self.path).load_team('Giants')

    def test_bridge_routes_explicit_amendments_and_remote_denial_prevents_provider(self):
        actor=self.store.player_context('Giants','dart')
        request=dict(protocol=1,request_id='bridge-offer',operation='negotiate_proposal',team_id='Giants',
            offer=self.offer.to_dict(),expected_revision=0,timeout_ms=5000,personality=actor['personality'],
            relationships=actor['relationships'],performance={'passing_yards':3100},amendment_rule=RULE)
        bridge=Bridge(self.store,provider=self.accept,access_check=lambda:False)
        self.assertEqual(bridge.handle(request)['error'],'ai_disabled');self.accept.assert_not_called()
        bridge.access_check=lambda:None
        response=bridge.handle(request)
        self.assertIsNone(response['error']);self.assertEqual(response['result']['outcome'],'accepted_amendment_proposal')
        self.assertEqual(self.store.load_team('Giants').revision,0)
        self.settle('bridge-offer','bridge-agreement')
        self.assertEqual(FranchiseStore(self.path).load_team('Giants').charges,(14088000,16440000,18792000))

    def test_lowball_rejection_changes_respect_once_and_survives_reopen(self):
        actor=self.store.player_context('Giants','dart');provider=Mock(return_value=json.dumps(dict(
            action='reject',reason='That offer is insulting. We are not negotiating on those terms.',
            salaries=None,signing_bonus=None,reaction='offended')))
        lowball=Offer('dart',(1000000,),0)
        event=self.propose('lowball',offer=lowball,provider=provider)
        reopened=FranchiseStore(self.path)
        self.assertEqual(reopened.player_context('Giants','dart')['relationships']['respect'],
                         round(actor['relationships']['respect']-0.05,6))
        recalled=self.session(reopened).respond('lowball',lowball,provider,expected_revision=0)
        self.assertEqual(recalled,event);provider.assert_called_once()
        self.assertEqual(reopened.load_team('Giants').revision,0)

    def test_accepted_promises_join_the_amended_agreement_and_replay(self):
        from franchise.promises import PromiseGoal
        goal=PromiseGoal('starts','starts',12,50,'2026 regular season','authored proposal')
        self.session().respond('offer',self.offer,self.accept,expected_revision=0,promise_goals=(goal,))
        self.settle()
        context=FranchiseStore(self.path).player_context('Giants','dart')
        self.assertEqual(context['agreed_promises'][0]['agreement_request_id'],'agreement')
        self.assertEqual(context['agreed_promises'][0]['goals'][0]['target'],12)

    def test_full_year_scope_rejects_earned_pay_unknown_calendar_and_untyped_inputs(self):
        self.propose();before=self.store.load_team('Giants').financial_snapshot()
        for value,source in ((1,'authored'),(-1,'authored'),(False,'authored'),(0,''),(0,'   ')):
            with self.subTest(value=value,source=source),self.assertRaises(ValueError):
                FullYearAmendmentScope(value,source)
        for scope in (None,dict(current_year_earned_base=0,source='authored')):
            with self.subTest(scope=scope),self.assertRaises(ValueError):
                self.store.commit_accepted_amendment('Giants','offer','agreement',0,scope=scope,access_check=lambda:None)
        self.assertEqual(self.store.load_team('Giants').financial_snapshot(),before)

    def test_explicit_false_denies_direct_session_before_and_after_provider(self):
        before=self.store.load_team('Giants').financial_snapshot()
        with self.assertRaises(Rejected):self.session(access=lambda:False)
        self.accept.assert_not_called()
        enabled=True
        session=self.session(access=lambda:enabled)
        def revoked(_):
            nonlocal enabled
            enabled=False
            return self.accept.return_value
        with self.assertRaises(Rejected):session.respond('disabled',self.offer,revoked,expected_revision=0)
        self.assertEqual(self.store.negotiation_history('Giants','dart'),[])
        self.assertEqual(self.store.load_team('Giants').financial_snapshot(),before)

    def test_settlement_retries_cannot_change_scope_and_do_not_reenable_control(self):
        self.propose();receipt=self.settle()
        with self.assertRaises(Rejected):self.settle(access=lambda:False)
        with self.assertRaises(Rejected):self.store.commit_accepted_amendment('Giants','offer','agreement',0,
            scope=FullYearAmendmentScope(0,'different season evidence'),access_check=lambda:None)
        self.assertEqual(self.settle(),receipt)

    def test_amended_legacy_debt_cannot_escape_through_unsupported_lifecycle(self):
        self.propose();self.settle();ledger=self.store.load_team('Giants');before=ledger.financial_snapshot()
        operations=(
            lambda:ledger.apply_preseason_release('dart',scope=None,discount=None,payment_year_offsets=(),record_id='cut',expected_revision=1),
            lambda:ledger.apply_preseason_restructure('dart',scope=None,converted_base=0,record_id='convert',expected_revision=1),
            lambda:ledger.apply_preseason_trade_out('dart',scope=None,record_id='trade',expected_revision=1),
            lambda:ledger.apply_year_transition(from_year=2026,to_year=2027,expected_revision=1,next_cap=301200000,
                roster_reserve=1000000,next_minimum_profile=None,source='authored'),
        )
        for operation in operations:
            with self.subTest(operation=operation),self.assertRaises(Rejected):operation()
            self.assertEqual(ledger.financial_snapshot(),before)

    def test_fractional_bonus_layers_remain_exact_through_repeated_agreement_and_reopen(self):
        from fractions import Fraction
        self.propose(offer=Offer('dart',(1000000,)*3,1));self.settle()
        self.propose('second',offer=Offer('dart',(1000000,),0),revision=1)
        self.settle('second','second-agreement',1)
        charges=FranchiseStore(self.path).load_team('Giants').charges
        self.assertEqual(charges,(3320000+Fraction(1,3),2320000+Fraction(1,3),2320000+Fraction(1,3)))
