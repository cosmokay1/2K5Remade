import unittest
from tests import test_plan_hybrid_roster as fixtures
from tests import test_resolve_week1_players as identity_fixtures
from tools.build_hybrid_portraits import portrait_preview


class HybridPortraitTests(unittest.TestCase):
    def test_only_verified_portrait_bytes_change_and_contracts_stay_unapproved(self):
        native = fixtures.HybridPlanTests().roster()
        source = bytearray(native)
        source[0xAFA8+6:0xAFA8+8] = b'\x34\x12'
        before = bytes(native), bytes(source)
        output, report = portrait_preview(*before, identity_fixtures.Week1IdentityTests().rows(),
                                         season_year=2026)
        self.assertEqual(output, bytes(native))
        self.assertEqual((bytes(native), bytes(source)), before)
        self.assertTrue(report['original_contract_words_preserved'])
        self.assertFalse(report['ready_for_franchise_test'])
        self.assertFalse(report['signing_authorized'])
        self.assertFalse(report['save_container_or_signature_created'])

    def test_unknown_image_refuses_normal_build_and_preview_keeps_unknown_record(self):
        native = fixtures.HybridPlanTests().roster()
        source = bytearray(native);source[0xAFA8+0x1A] = 3
        rows = identity_fixtures.Week1IdentityTests().rows()
        with self.assertRaises(ValueError):
            portrait_preview(bytes(native), bytes(source), rows, season_year=2026)
        output, report = portrait_preview(bytes(native), bytes(source), rows,
                                         season_year=2026, allow_incomplete=True)
        self.assertEqual(output, bytes(source))
        self.assertFalse(report['all_source_images_verified'])
        self.assertFalse(report['ready_for_franchise_test'])
