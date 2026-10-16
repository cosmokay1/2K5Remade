"""Salary-period amendment accounting; no real NFL payroll/calendar claims."""
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from franchise.cap import Offer,Rejected
from franchise.legacy_amendments import (RULE,FullYearAmendmentScope,
    InSeasonAmendmentScope,amendment_scope_from_dict)
from franchise.negotiation import Negotiation
from franchise.store import FranchiseStore,StoredLedger
from tests import test_legacy_amendment


class EarnedAmendmentTests(unittest.TestCase):
    def ledger(self,**kwargs):
        return test_legacy_amendment.LegacyAmendmentTests().ledger(**kwargs)

    def scope(self,elapsed=8,*,year=2026,total=17,source='authored salary clock'):
        return InSeasonAmendmentScope(year,elapsed,total,source)

    def apply(self,ledger,offer,scope,name='one'):
        return ledger.apply_legacy_amendment(name,offer,ledger.revision,
            proposal_request_id='proposal-'+name,source='authored consent',scope=scope)

    def test_paycut_preserves_earned_base_and_old_bonus_as_obligations(self):
        ledger=self.ledger();offer=Offer('dart',(1000000,2000000),2000000)
        scope=self.scope();before=ledger.financial_snapshot()
        preview=ledger.preview_legacy_amendment(offer,0,scope=scope)
        earned=Fraction(1544000*8,17);remaining=Fraction(1000000*9,17)
        self.assertEqual(Fraction(preview['earned_pay']['earned_base_obligation']),earned)
        self.assertEqual(Fraction(preview['combined_player_charges'][0]),earned+remaining+3320000)
        self.assertEqual(before,ledger.financial_snapshot())
        agreement=self.apply(ledger,offer,scope)
        self.assertEqual(agreement.charges()[0],earned+remaining+3320000)
        self.assertEqual(agreement.bonus_charges(),(3320000,3320000,2320000))
        self.assertEqual(Fraction(agreement.to_dict()['new_cash_commitment']),remaining+4000000)
        self.assertNotIn('paid',agreement.to_dict())
        json.dumps(agreement.to_dict(),allow_nan=False)

    def test_later_agreement_accrues_each_rate_only_over_its_own_periods(self):
        ledger=self.ledger();first=self.apply(ledger,Offer('dart',(2000000,)*3,3000000),self.scope(4))
        second=self.apply(ledger,Offer('dart',(1000000,),0),self.scope(10),'two')
        earned=Fraction(1544000*4+2000000*6,17)
        self.assertEqual(second.earned_base,earned)
        self.assertEqual(second.charges()[0],earned+Fraction(1000000*7,17)+3320000)
        self.assertEqual(second.bonus_charges(),first.bonus_charges())
        third=self.apply(ledger,Offer('dart',(1500000,),0),self.scope(10),'three')
        self.assertEqual(third.earned_base,earned)
        self.assertEqual(third.charges()[0],earned+Fraction(1500000*7,17)+3320000)

    def test_clock_cannot_rewind_reset_year_or_change_period_count(self):
        ledger=self.ledger();self.apply(ledger,Offer('dart',(1000000,),0),self.scope())
        before=ledger.financial_snapshot()
        for scope in (None,FullYearAmendmentScope(0,'not an excuse to erase pay'),self.scope(7),
                      self.scope(year=2027),self.scope(total=18)):
            with self.subTest(scope=scope),self.assertRaises(ValueError):
                ledger.preview_legacy_amendment(Offer('dart',(1000000,),0),1,scope=scope)
        self.assertEqual(before,ledger.financial_snapshot())

    def test_earned_obligation_prevents_false_affordability(self):
        ledger=self.ledger(cap=4500000);offer=Offer('dart',(1000000,),0)
        self.assertTrue(ledger.preview_legacy_amendment(offer,0)['within_modeled_cap'])
        p=ledger.preview_legacy_amendment(offer,0,scope=self.scope(17))
        self.assertFalse(p['within_modeled_cap'])
        with self.assertRaises(Rejected):self.apply(ledger,offer,self.scope(17))
        self.assertEqual(ledger.revision,0)

    def test_zero_and_all_periods_are_exact_and_minimum_applies_to_annual_rate(self):
        offer=Offer('dart',(1000000,),0)
        zero=self.ledger().preview_legacy_amendment(offer,0,scope=self.scope(0))
        full=self.ledger().preview_legacy_amendment(offer,0)
        self.assertEqual(zero['combined_player_charges'],full['combined_player_charges'])
        all_pay=self.apply(self.ledger(),offer,self.scope(17))
        self.assertEqual(all_pay.to_dict()['new_cash_commitment'],0)
        self.assertEqual(all_pay.charges()[0],3864000)
        with self.assertRaises(Rejected):
            self.ledger().preview_legacy_amendment(Offer('dart',(999999,),0),0,scope=self.scope(17))

    def test_scope_json_is_strict(self):
        for value in (dict(league_year=2026,elapsed_periods=True,total_periods=17,source='x'),
                      dict(league_year=2026,elapsed_periods=18,total_periods=17,source='x'),
                      dict(league_year=2026,elapsed_periods=0,total_periods=0,source='x'),
                      dict(league_year=2026,elapsed_periods=0,total_periods=17,source=' ')):
            with self.subTest(value=value),self.assertRaises(ValueError):amendment_scope_from_dict(value)
        self.assertEqual(amendment_scope_from_dict(self.scope().to_dict()),self.scope())
        self.assertEqual(amendment_scope_from_dict(FullYearAmendmentScope(0,'x').to_dict()),FullYearAmendmentScope(0,'x'))

    def test_consent_binds_earned_scope_before_provider_and_survives_reopen(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ledger.sqlite';store=FranchiseStore(path)
            store.create_franchise({'Giants':self.ledger()},seed='earned')
            actor=store.player_context('Giants','dart');offer=Offer('dart',(1000000,),0)
            def session(scope):
                return Negotiation(StoredLedger(store,'Giants',amendment_rule=RULE,amendment_scope=scope),
                    player_id='dart',personality=actor['personality'],relationships=actor['relationships'],
                    performance={},access_check=lambda:None,proposal_only=True)
            provider=Mock(return_value=json.dumps(dict(action='accept',reason='Agreed.',salaries=None,signing_bonus=None)))
            event=session(self.scope()).respond('offer',offer,provider,expected_revision=0)
            self.assertEqual(event['amendment_basis']['earned_pay']['scope'],self.scope().to_dict())
            self.assertIn('earned_pay',provider.call_args.args[0]['accounting']['amendment_comparison'])
            for scope in (self.scope(9),FullYearAmendmentScope(0,'incorrect zero')):
                with self.assertRaises(Rejected):
                    store.commit_accepted_amendment('Giants','offer','settle',0,scope=scope,access_check=lambda:None)
            with self.assertRaises(Rejected):session(self.scope(9)).respond('offer',offer,provider,expected_revision=0)
            receipt=store.commit_accepted_amendment('Giants','offer','settle',0,scope=self.scope(),access_check=lambda:None)
            reopened=FranchiseStore(path)
            self.assertEqual(reopened.load_team('Giants').financial_snapshot(),store.load_team('Giants').financial_snapshot())
            self.assertEqual(receipt,store.commit_accepted_amendment('Giants','offer','settle',0,scope=self.scope(),access_check=lambda:None))
            self.assertFalse(receipt['guest_write_authorized']);provider.assert_called_once()
