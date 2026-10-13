from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer, Rejected
from franchise.control import AccessDisabled
from franchise.rookie import RookieScale
from franchise.store import FranchiseStore


class DraftFundingTests(unittest.TestCase):
    def ledger(self, cap=20, one=100, total=400):
        return Ledger.from_opening(OpeningBooks(), cap=cap, roster_reserve=0, max_bonus_years=5,
            veteran_minimums={'v':(1,)}, rookies={p:RookieScale(2,(1,)*4,1,30,150) for p in ('d','n')},
            rookie_year_one_allocation=one, rookie_total_allocation=total,
            undrafted_bonus_reservation=3, undrafted_reservation_source='synthetic reservation')

    def test_cap_earmark_preserves_exact_funding_and_replaces_it_at_signing(self):
        ledger = self.ledger()
        ledger.reserve_draft_funding(Offer('d',(10,)*4,1),0,source='synthetic draft cost estimate')
        self.assertEqual(ledger.charges,(0,))
        self.assertEqual(ledger.room,Fraction(39,4))
        self.assertEqual(ledger.negotiation_context('d')['room_for_replacing_player_tender'],20)
        with self.assertRaises(Rejected):
            ledger.sign('veteran',Offer('v',(10,),0),1)
        preview = ledger.preview_offer(Offer('d',(15,)*4,0),1)
        self.assertEqual(preview['room_after'],5)
        ledger.sign('rookie',Offer('d',(15,)*4,0),1)
        self.assertEqual(ledger.room,5)
        self.assertEqual(ledger.rookie_remaining,(85,340))
        self.assertNotIn('draft_management_reservations',ledger.financial_snapshot())

    def test_pool_earmark_preserves_reserved_udfa_share_and_withdraws_explicitly(self):
        ledger = self.ledger(cap=100,one=20,total=80)
        ledger.reserve_draft_funding(Offer('d',(10,)*4,1),0,source='synthetic estimate')
        self.assertEqual(ledger.rookie_remaining,(20,80))
        available=ledger.negotiation_context('n')['rookie_available_to_player']
        self.assertEqual(available,{'year_one':'35/4','total':36})
        with self.assertRaises(Rejected):
            ledger.sign('next',Offer('n',(10,)*4,0),1)
        ledger.withdraw_draft_funding('d',1,source='synthetic management withdrawal')
        ledger.sign('next',Offer('n',(10,)*4,0),2)
        self.assertEqual(ledger.rookie_remaining,(10,40))

    def test_durable_reservation_replay_retry_and_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'state.sqlite'
            store=FranchiseStore(path)
            store.create_team('a',self.ledger())
            offer=Offer('d',(10,)*4,1)
            def disabled():
                raise AccessDisabled('synthetic shutdown')
            with self.assertRaises(AccessDisabled):
                store.reserve_draft_funding('a','reserve',offer,0,source='fixture',access_check=disabled)
            self.assertEqual(store.load_team('a').revision,0)
            first=store.reserve_draft_funding('a','reserve',offer,0,source='fixture',access_check=lambda:None)
            reopened=FranchiseStore(path)
            self.assertEqual(reopened.reserve_draft_funding('a','reserve',offer,0,source='fixture',access_check=lambda:None),first)
            self.assertEqual(reopened.load_team('a').room,Fraction(39,4))
            reopened.sign('a','sign',offer,1)
            self.assertEqual(FranchiseStore(path).load_team('a').room,Fraction(39,4))
            self.assertEqual(reopened.load_team('a').rookie_remaining,(Fraction(359,4),359))

    def test_reservation_cannot_be_replaced_or_created_for_a_veteran(self):
        ledger=self.ledger()
        ledger.reserve_draft_funding(Offer('d',(10,)*4,0),0,source='fixture')
        with self.assertRaises(Rejected):
            ledger.reserve_draft_funding(Offer('d',(11,)*4,0),1,source='fixture')
        with self.assertRaises(Rejected):
            ledger.reserve_draft_funding(Offer('v',(10,),0),1,source='fixture')
        self.assertEqual(ledger.revision,1)

    def test_existing_tender_is_not_reserved_or_charged_twice(self):
        from franchise.books import RookieTender
        base=self.ledger()
        ledger=Ledger.from_opening(OpeningBooks(tenders=(RookieTender('d',1),)),
            cap=20, roster_reserve=0, max_bonus_years=5, veteran_minimums={}, rookies=base._rookies,
            rookie_year_one_allocation=100, rookie_total_allocation=400)
        offer=Offer('d',(10,)*4,1)
        ledger.reserve_draft_funding(offer,0,source='synthetic tender-adjusted estimate')
        self.assertEqual(ledger.room,Fraction(39,4))
        self.assertEqual(ledger.charges,(1,))
        ledger.sign('rookie',offer,1)
        self.assertEqual(ledger.charges[0],Fraction(41,4))
        self.assertEqual(ledger.room,Fraction(39,4))
