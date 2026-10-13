import json
from pathlib import Path
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer
from franchise.negotiation import Decision, Negotiation
from franchise.store import FranchiseStore, StoredLedger


class GuaranteeTests(unittest.TestCase):
    def test_negotiated_guarantees_survive_contract_story_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FranchiseStore(Path(directory) / "state.sqlite")
            store.create_team("a", Ledger.from_opening(OpeningBooks(), cap=100, roster_reserve=0,
                max_bonus_years=5, veteran_minimums={"v": (1, 1)}))
            session = Negotiation(StoredLedger(store, "a"), player_id="v", personality={"security": 0.9},
                                  performance={}, relationships={}, access_check=lambda: None)
            counter = session.respond("counter", Offer("v", (10, 20), 6), lambda _: json.dumps(dict(
                action="counter", reason="I want the second year protected", salaries=[10, 20],
                signing_bonus=6, guaranteed_salaries=[10, 15])))
            terms = Offer.from_dict(counter["counter"])
            self.assertEqual(terms.charges(5), (13, 23))
            seen = []
            def accept(context):
                seen.append(context)
                return json.dumps(dict(action="accept", reason="Security works", salaries=None,
                                       signing_bonus=None, guaranteed_salaries=None))
            session.respond("agreement", terms, accept)
            reopened = FranchiseStore(store.path)
            self.assertEqual(reopened.load_team("a").contract_terms("v")["guaranteed_salaries"], [10, 15])
            self.assertEqual(reopened.stories("a")[0]["offer"]["guaranteed_salaries"], [10, 15])
            self.assertEqual(seen[0]["offer"]["guaranteed_salaries"], [10, 15])
            self.assertEqual(reopened.load_team("a").charges, (13, 23))

    def test_bad_guarantees_reject_without_creating_cap_room(self):
        for guarantees in ((11,), (1, 2), (True,), (-1,)):
            with self.subTest(guarantees=guarantees), self.assertRaises(ValueError):
                Offer("v", (10,), 0, guarantees)
        legacy = Offer.from_dict(dict(player_id="v", salaries=[10], signing_bonus=0))
        self.assertEqual(legacy.guaranteed_salaries, ())
        self.assertNotIn("guaranteed_salaries", legacy.to_dict())
        with self.assertRaisesRegex(ValueError, "silently change"):
            Decision.parse(json.dumps(dict(action="accept", reason="Yes", salaries=None,
                signing_bonus=None, guaranteed_salaries=[10])), "v")
