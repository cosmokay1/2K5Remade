from copy import deepcopy
from types import SimpleNamespace
import unittest

from tools.assemble_week1_roster import gameplay_profile


class EstimatedGameplayProfileTests(unittest.TestCase):
    def inputs(self):
        codec = SimpleNamespace(RATING_BYTE_ORDER=('speed', 'catch', 'consistency'))
        estimate = dict(gsis_id='player', position=3, ratings=dict(speed=89, catch=70, consistency=65),
                        basis=dict(model='authored-fixture', season=2025),
                        sources=[dict(source_url='https://example.com/evidence', sha256='a' * 64)])
        return codec, dict(position=3, gameplay_estimate=estimate)

    def test_estimate_is_copied_without_mutating_source_or_contract(self):
        codec, assignment = self.inputs()
        assignment['native_contract_projection'] = dict(contract_value=100)
        before = deepcopy(assignment)
        ratings = gameplay_profile(codec, assignment, 'player', 2026)
        ratings['speed'] = 1
        self.assertEqual(assignment, before)

    def test_unsourced_default_and_wrong_identity_or_position_are_refused(self):
        codec, assignment = self.inputs()
        with self.assertRaises(ValueError):
            gameplay_profile(codec, dict(position=3), 'player', 2026)
        for key, bad in [('gsis_id', 'namesake'), ('position', 4), ('sources', [])]:
            changed = deepcopy(assignment)
            changed['gameplay_estimate'][key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                gameplay_profile(codec, changed, 'player', 2026)

    def test_future_statistics_missing_attributes_and_invalid_values_are_refused(self):
        codec, assignment = self.inputs()
        changes = [lambda e: e['basis'].update(season=2026),
                   lambda e: e['ratings'].pop('catch'),
                   lambda e: e['ratings'].update(speed=True),
                   lambda e: e['ratings'].update(speed=100),
                   lambda e: e['sources'][0].update(sha256='not pinned')]
        for change in changes:
            changed = deepcopy(assignment)
            change(changed['gameplay_estimate'])
            with self.assertRaises(ValueError):
                gameplay_profile(codec, changed, 'player', 2026)
