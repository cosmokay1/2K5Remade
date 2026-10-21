from copy import deepcopy
from types import SimpleNamespace
import unittest

from tools.assemble_week1_roster import gameplay_profile, validate_reusable_slots


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


class ReusableRosterSlotTests(unittest.TestCase):
    def document(self):
        players = {i: SimpleNamespace(index=i) for i in range(8)}
        return SimpleNamespace(by_pool=lambda pool: list(players.values()),
            by_offset=players, free_agents=[0, 1],
            teams=[SimpleNamespace(slots=[2, 3]) for _ in range(32)] +
                  [SimpleNamespace(slots=[4, 5])], reserves={'reserve': [6]})

    def test_vacated_active_and_free_records_can_preserve_full_creator_pool(self):
        validate_reusable_slots(self.document(), [0, 2], {1, 3})

    def test_selected_classic_reserve_unassigned_and_duplicate_records_rejected(self):
        for slots in ([1], [4], [6], [7], [8], [0, 0]):
            with self.subTest(slots=slots), self.assertRaises(ValueError):
                validate_reusable_slots(self.document(), slots, {1, 3})
