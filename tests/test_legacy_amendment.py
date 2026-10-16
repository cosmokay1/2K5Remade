"""Imported contract comparisons preserve bonus debt without granting settlement."""
from dataclasses import replace
from fractions import Fraction
import tempfile
from pathlib import Path
import unittest
import json

from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.legacy_contracts import LegacyContract
from franchise.store import FranchiseStore


class LegacyAmendmentTests(unittest.TestCase):
    def ledger(self, *, cap=301200000, original=None):
        original=original or LegacyContract('dart',348,5,6,3,3,'authored saved schedule',4)
        return Ledger.from_opening(OpeningBooks(legacy_contracts=(original,)),cap=cap,
            roster_reserve=1000000,max_bonus_years=5,
            veteran_minimums={'dart':(1000000,)*10})

    def test_dart_retains_old_bonus_and_adds_new_bonus_without_double_counting_base(self):
        ledger=self.ledger();before=ledger.financial_snapshot()
        offer=Offer('dart',(4708000,7060000,9412000),21180000)
        p=ledger.preview_legacy_amendment(offer,0)
        self.assertEqual(p['current_charges'],[3864000,4640000,5412000])
        self.assertEqual(p['carried_bonus_charges'],[2320000]*3)
        self.assertEqual(p['new_contract_charges'],[11768000,14120000,16472000])
        self.assertEqual(p['combined_player_charges'],[14088000,16440000,18792000])
        self.assertEqual(p['annual_team_charges_after'],p['combined_player_charges'])
        self.assertEqual(p['room_before']-p['room_after'],10224000)
        self.assertFalse(p['settlement_authorized']);self.assertTrue(p['requires_player_agreement'])
        json.dumps(p,allow_nan=False)
        self.assertEqual(before,ledger.financial_snapshot())

    def test_shorter_contract_does_not_erase_bonus_after_new_term_ends(self):
        p=self.ledger().preview_legacy_amendment(Offer('dart',(1000000,),0),0)
        self.assertEqual(p['combined_player_charges'],[3320000,2320000,2320000])
        self.assertEqual(p['annual_team_charges_after'],[3320000,2320000,2320000])

    def test_extension_does_not_spread_old_bonus_into_added_years(self):
        p=self.ledger().preview_legacy_amendment(Offer('dart',(1000000,)*5,5000000),0)
        self.assertEqual(p['combined_player_charges'],[4320000]*3+[2000000]*2)

    def test_aged_and_long_legacy_bonuses_keep_original_allocation(self):
        original=LegacyContract('dart',700,4,2,7,6,'legacy seven year deal')
        p=self.ledger(original=original).preview_legacy_amendment(Offer('dart',(1000000,),0),0)
        self.assertEqual(p['carried_bonus_charges'],[400000]*6)
        self.assertEqual(p['combined_player_charges'],[1400000]+[400000]*5)

    def test_fractional_new_bonus_remains_exact(self):
        p=self.ledger().preview_legacy_amendment(Offer('dart',(1000000,)*3,1),0)
        self.assertEqual(Fraction(p['combined_player_charges'][0]),Fraction(3320000)+Fraction(1,3))

    def test_over_cap_comparison_is_visible_but_not_authorized(self):
        p=self.ledger(cap=5000000).preview_legacy_amendment(Offer('dart',(8000000,),0),0)
        self.assertFalse(p['within_modeled_cap']);self.assertLess(p['room_after'],0)
        self.assertFalse(p['settlement_authorized'])

    def test_stale_unknown_and_below_minimum_reject_without_mutation(self):
        ledger=self.ledger();before=ledger.financial_snapshot()
        for offer,revision in ((Offer('dart',(1000000,),0),True),
                               (Offer('dart',(1000000,),0),1),
                               (Offer('other',(1000000,),0),0),
                               (Offer('dart',(999999,),0),0)):
            with self.subTest(offer=offer,revision=revision),self.assertRaises(Rejected):
                ledger.preview_legacy_amendment(offer,revision)
        self.assertEqual(before,ledger.financial_snapshot())
        with self.assertRaises(Rejected):ledger.preview_offer(Offer('dart',(1000000,),0),0)

    def test_owning_team_required_and_store_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            store=FranchiseStore(Path(temporary)/'franchise.sqlite')
            store.create_team('Giants',self.ledger())
            before=store.load_team('Giants').financial_snapshot()
            offer=Offer('dart',(1000000,),0)
            with store._connection() as db:
                p=store._preview_legacy_amendment(db,'Giants',store._load(db,'Giants'),offer,0)
                self.assertFalse(p['settlement_authorized'])
                with self.assertRaises(Rejected):
                    store._preview_legacy_amendment(db,'Other',store._load(db,'Giants'),offer,0)
            self.assertEqual(before,store.load_team('Giants').financial_snapshot())
