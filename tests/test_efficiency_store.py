import copy
from contextlib import closing
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest

from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer
from franchise.performance import Observation, PerformanceEvidence
from franchise.store import FranchiseStore


class EfficiencyStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = FranchiseStore(Path(self.temp.name) / 'efficiency.sqlite')
        self.store.create_team('a', Ledger.from_opening(OpeningBooks(), cap=100,
            roster_reserve=0, max_bonus_years=5, veteran_minimums={'p': (1,)}))
        self.offer = Offer('p', (20,), 0)
        self.performance = PerformanceEvidence('p', 'synthetic season', 'cpu_played', (
            Observation('receptions', 2, 'synthetic catches'),
            Observation('targets', 3, 'synthetic measured targets'),
            Observation('rush_attempts', 4, 'synthetic carries'),
            Observation('rushing_yards', 4, 'synthetic rushing yards'),
        ), 'synthetic full season', team_id='a', complete_window=True)

    def story(self, *, derived=True, request='deal'):
        evidence = {'personality': {}, 'performance': self.performance.to_context(),
                    'relationships': {}, 'financial_revision': 0}
        if derived:
            evidence['observed_efficiency'] = self.performance.efficiency_context()
        return {'request_id': request, 'offer': self.offer.to_dict(), 'action': 'accept',
                'outcome': 'signed', 'reason': 'Synthetic observed production', 'counter': None,
                'evidence': evidence}

    def mutations(self):
        def mutate(story, scenario):
            evidence = story['evidence']
            derived = evidence['observed_efficiency']
            catch = derived['efficiencies']['reception_per_target']
            if scenario == 'ratio': catch['value'] = '3/4'
            if scenario == 'sample': catch['sample_count'] = 2
            if scenario == 'window': derived['window'] = 'another season'
            if scenario == 'source': catch['numerator']['source'] = 'invented catches'
            if scenario == 'missing': evidence['performance']['missing_counters'].append('targets')
            if scenario == 'bool': derived['efficiencies']['rushing_yards_per_rush_attempt']['value'] = True
            if scenario == 'identity':
                evidence['performance']['player_id'] = 'other'
                derived['player_id'] = 'other'
            return story
        return mutate, ('ratio', 'sample', 'window', 'source', 'missing', 'bool', 'identity')

    def test_signing_replay_and_retry_preserve_derived_sources_without_extra_money(self):
        story = self.story()
        receipt = self.store.sign('a', 'deal', self.offer, 0, story=story)
        reopened = FranchiseStore(self.store.path)
        self.assertEqual(reopened.sign('a', 'deal', self.offer, 0, story=story), receipt)
        saved = reopened.stories('a')[0]['evidence']['observed_efficiency']
        self.assertEqual(saved, self.performance.efficiency_context())
        self.assertEqual(saved['efficiencies']['reception_per_target']['value'], '2/3')
        self.assertIsNone(saved['efficiencies']['passing_yards_per_pass_attempt']['value'])
        self.assertEqual(reopened.load_team('a').charges, (20,))
        self.assertEqual(reopened.load_team('a').revision, 1)

    def test_invalid_derivation_rejects_before_financial_or_dialogue_write(self):
        mutate, scenarios = self.mutations()
        before = self.store.load_team('a').financial_snapshot()
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                bad = mutate(self.story(), scenario)
                with self.assertRaises(ValueError):
                    self.store.sign('a', 'deal', self.offer, 0, story=bad)
                bad.update(action='reject', outcome='player_rejected')
                with self.assertRaises(ValueError):
                    self.store.record_negotiation('a', bad, access_check=lambda: None)
                self.assertEqual(self.store.load_team('a').financial_snapshot(), before)
        with closing(sqlite3.connect(self.store.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0], 0)

    def test_tampered_saved_derivation_fails_replay(self):
        self.store.sign('a', 'deal', self.offer, 0, story=self.story())
        with closing(sqlite3.connect(self.store.path)) as db:
            original = json.loads(db.execute("SELECT payload FROM events WHERE kind='sign'").fetchone()[0])
        mutate, scenarios = self.mutations()
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                bad = copy.deepcopy(original)
                mutate(bad['story'], scenario)
                with closing(sqlite3.connect(self.store.path)) as db:
                    db.execute("UPDATE events SET payload=? WHERE kind='sign'", (json.dumps(bad),))
                    db.commit()
                with self.assertRaises(ValueError):
                    FranchiseStore(self.store.path).load_team('a')
                with closing(sqlite3.connect(self.store.path)) as db:
                    db.execute("UPDATE events SET payload=? WHERE kind='sign'", (json.dumps(original),))
                    db.commit()
        self.assertEqual(self.store.load_team('a').revision, 1)

    def test_dialogue_sources_persist_and_legacy_evidence_keeps_original_shape(self):
        event = self.story(request='rejected')
        event.update(action='reject', outcome='player_rejected')
        self.store.record_negotiation('a', event, access_check=lambda: None)
        reopened = FranchiseStore(self.store.path)
        self.assertEqual(reopened.record_negotiation('a', event, access_check=lambda: None), event)
        self.assertEqual(reopened.negotiation_history('a', 'p')[0]['evidence'], event['evidence'])
        legacy = self.story(derived=False)
        reopened.sign('a', 'deal', self.offer, 0, story=legacy)
        saved = FranchiseStore(self.store.path).stories('a')[0]['evidence']
        self.assertNotIn('observed_efficiency', saved)
        self.assertEqual(saved, legacy['evidence'])
