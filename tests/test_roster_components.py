from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks, ActiveContract, ChargeRecord
from franchise.cap import Ledger, Offer
from franchise.store import FranchiseStore


class StoredRosterComponentsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = FranchiseStore(Path(directory.name) / "state.sqlite")
        contracts = tuple(ActiveContract(Offer(str(i), (2_000_000,), 0), "synthetic roster contract") for i in range(51))
        contracts += (ActiveContract(Offer("last", (1_000_000,), 900_000), "synthetic bonus contract"),)
        books = OpeningBooks(contracts=contracts, retained=(ChargeRecord("dead", (5_000_000,), "synthetic retained liability"),))
        self.store.create_team("a", Ledger.from_opening(books, cap=200_000_000, roster_reserve=1_000_000,
            max_bonus_years=5, veteran_minimums={entry.offer.player_id: (885_000,) for entry in contracts}))
        self.classes = {entry.offer.player_id: (0, False) for entry in contracts}

    def project(self, phase, classes=None):
        return self.store.roster_components("a", phase=phase, league_year=2026,
            classifications=self.classes if classes is None else classes, classification_source="synthetic roster classification fixture")

    def test_phase_projection_retains_bonus_and_dead_charges_without_authority_change(self):
        before = self.store.load_team("a").financial_snapshot()
        offseason = self.project("offseason")
        regular = self.project("regular_season")
        self.assertEqual(offseason["projected_modeled_team_charge"], 107_900_000)
        self.assertEqual(regular["projected_modeled_team_charge"], 108_900_000)
        self.assertEqual(offseason["retained_and_adjustment_charge"], 5_000_000)
        self.assertFalse(offseason["signing_authority_changed"])
        self.assertEqual(self.store.load_team("a").financial_snapshot(), before)

    def test_incomplete_classification_and_phase_reject(self):
        incomplete = dict(self.classes)
        del incomplete["last"]
        with self.assertRaises(ValueError):
            self.project("offseason", incomplete)
        with self.assertRaises(ValueError):
            self.project("unknown")
