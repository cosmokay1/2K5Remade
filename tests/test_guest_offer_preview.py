from pathlib import Path
import tempfile
import unittest

from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer
from franchise.store import FranchiseStore
from franchise.guest_contracts import preview_guest_offer


class GuestOfferPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.store=FranchiseStore(Path(self.temporary.name)/'franchise.sqlite')
        self.store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=10000000,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'free':(200000,)*5,'owned':(200000,)*5},
            observed_player_ids=frozenset({'pending'}),observed_player_source='authored registry'))

    def preview(self,amount=829,flags=(1<<29)|(2<<16)|4,player='free',revision=0):
        return preview_guest_offer(self.store,'a',player,amount_word=amount,flags_word=flags,expected_revision=revision)

    def test_exact_calibrated_offer_is_advisory_and_changes_no_money(self):
        before=self.store.load_team('a').financial_snapshot()
        result=self.preview()
        self.assertEqual(result['outcome'],'eligible_preview')
        self.assertEqual(result['preview']['contract_charges'],[4766000,3523000])
        self.assertEqual(result['offer']['signing_bonus'],3316000)
        self.assertIsNone(result['reason'])
        self.assertEqual(before,self.store.load_team('a').financial_snapshot())

    def test_softdrink_preview_uses_display_scale_for_cap_validation(self):
        before=self.store.load_team('a').financial_snapshot()
        result=preview_guest_offer(self.store,'a','free',amount_word=829,
            flags_word=(1<<29)|(2<<16)|4,expected_revision=0,
            contract_format='softdrink_fxg_v1')
        self.assertEqual(result['outcome'],'accounting_rejected')
        self.assertEqual(result['offer']['signing_bonus'],13264000)
        self.assertEqual(result['contract_format'],'softdrink_fxg_v1')
        self.assertEqual(self.store.load_team('a').financial_snapshot(),before)

    def test_modern_horizon_rounding_and_zero_amount_do_not_repair_terms(self):
        for amount,flags,reason in ((1949,(2<<29)|(6<<16)|4,'five-year'),
                                   (500,(2<<29)|(3<<16)|4,'rounding'),(0,2<<16,'inputs')):
            with self.subTest(amount=amount):
                result=self.preview(amount,flags)
                self.assertEqual(result['outcome'],'format_rejected')
                self.assertIn(reason,result['reason'])
                self.assertIsNone(result['offer']); self.assertIsNone(result['preview'])

    def test_pending_minimum_over_cap_stale_and_owned_players_stay_rejected(self):
        self.assertEqual(self.preview(player='pending')['outcome'],'accounting_rejected')
        self.assertEqual(self.preview(6000,(2<<29)|(3<<16))['outcome'],'accounting_rejected')
        self.assertEqual(self.preview(revision=1)['outcome'],'accounting_rejected')
        self.store.sign('a','owned',Offer('owned',(200000,),0),0)
        self.assertIn('belongs',self.preview(player='owned',revision=1)['reason'])

    def test_malformed_word_types_do_not_become_financial_previews(self):
        for amount,flags in ((True,1),(1,False),(65536,1),(1,-1),(1,2**32)):
            with self.subTest(amount=amount,flags=flags),self.assertRaises(ValueError):
                self.preview(amount,flags)
