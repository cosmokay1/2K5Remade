from pathlib import Path
import tempfile
import unittest
from franchise.cap import Ledger, Offer, Rejected
from franchise.books import OpeningBooks, ChargeRecord, RookieTender
from franchise.rookie import RookieScale
from franchise.store import FranchiseStore


class TenderTests(unittest.TestCase):
    def ledger(self, *, cap=10, tender=1, existing=1):
        return Ledger.from_opening(OpeningBooks(retained=(ChargeRecord("fixture", (existing-tender,), "synthetic retained fixture"),), tenders=(RookieTender("r", tender),)), cap=cap, roster_reserve=0,
                      max_bonus_years=5, veteran_minimums={},
                      rookies={"r": RookieScale(1, (1,) * 4, 1, 20, 80)},
                      rookie_year_one_allocation=20, rookie_total_allocation=80)

    def test_contract_replaces_tender_without_double_count(self):
        ledger = self.ledger(cap=1)
        receipt = ledger.sign("one", Offer("r", (1,) * 4, 0), 0)
        self.assertEqual(receipt.charges, (1,) * 4)
        self.assertEqual(ledger.charges, (1,) * 4)
        self.assertEqual(ledger.room, 0)
        self.assertEqual(ledger.rookie_remaining, (19, 76))
        self.assertEqual(ledger.sign("one", Offer("r", (1,) * 4, 0), 0), receipt)
        self.assertEqual(ledger.charges, (1,) * 4)

    def test_over_cap_offer_rejects_without_releasing_tender(self):
        ledger = self.ledger(cap=1)
        with self.assertRaises(Rejected):
            ledger.sign("one", Offer("r", (2,) * 4, 0), 0)
        self.assertEqual(ledger.charges, (1,))
        self.assertEqual(ledger.negotiation_context("r")["existing_player_tender"], 1)
        ledger.sign("one", Offer("r", (1,) * 4, 0), 0)

    def test_restart_does_not_deduct_tender_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite"
            store = FranchiseStore(path)
            store.create_team("a", self.ledger(cap=1))
            store.sign("a", "one", Offer("r", (1,) * 4, 0), 0)
            reopened = FranchiseStore(path)
            reopened.sign("a", "one", Offer("r", (1,) * 4, 0), 0)
            self.assertEqual(reopened.load_team("a").charges, (1,) * 4)

    def test_tenders_cannot_exceed_declared_balance_or_belong_to_unknown_player(self):
        with self.assertRaises(ValueError):
            self.ledger(tender=2, existing=1)
        with self.assertRaises(ValueError):
            Ledger(cap=10, existing_charges=(1,), roster_reserve=0,
                   max_bonus_years=5, veteran_minimums={"v": (1,)}, rookie_tenders={"v": 1})
