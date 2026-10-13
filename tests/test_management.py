from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger
from franchise.management import ManagementProfile
from franchise.store import FranchiseStore, StoredLedger


class ManagementTests(unittest.TestCase):
    def test_priorities_survive_restart_without_changing_financial_authority(self):
        profile = ManagementProfile('gm-a', 'authored simulation personality',
                                    (('development', 0.9), ('financial_flexibility', 0.8)))
        ledger = Ledger.from_opening(OpeningBooks(), cap=100, roster_reserve=10,
            max_bonus_years=5, veteran_minimums={'p': (1,)}, management_profile=profile)
        expected = ledger.management_context()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.sqlite'
            store = FranchiseStore(path)
            store.create_team('a', ledger)
            reopened = FranchiseStore(path).load_team('a')
            self.assertEqual(StoredLedger(store, 'a').management_context(), expected)
            self.assertEqual(reopened.management_context(), expected)
            self.assertEqual(reopened.room, 90)
            self.assertNotIn('management_profile', reopened.negotiation_context('p'))
            returned = reopened.management_context()
            returned['management_profile']['priorities']['development'] = 0
            self.assertEqual(reopened.management_context(), expected)

    def test_unknown_ratings_duplicates_and_invalid_weights_reject(self):
        for priorities in ((('overall', 0.8),), (('development', True),), (('risk_tolerance', float('nan')),),
                           (('win_now', 1.1),), (('continuity', 0.5), ('continuity', 0.9))):
            with self.subTest(priorities=priorities), self.assertRaises(ValueError):
                ManagementProfile('gm', 'authored fixture', priorities)
