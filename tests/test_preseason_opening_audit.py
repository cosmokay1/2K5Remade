"""Later roster/cap snapshots never silently establish a preseason opening book."""
import unittest
from unittest.mock import patch
from tools.audit_preseason_opening import audit_opening
from tests import test_legacy_contracts as fixtures


class PreseasonAuditTests(unittest.TestCase):
    def audit(self,cutoff='2026-08-06',as_of='2026-09-24T12:40:52Z'):
        payload=bytes(fixtures.LegacyContractsTests().fixture())
        bindings={'game_context':dict(season_year=2026,season_index=0,money_scale=4,league_cap_raw=80500)}
        source=dict(start_year=2026,as_of=as_of,audit_sha256='a'*64,
            teams={'49ers':{'unresolved':[]}})
        with patch('tools.audit_preseason_opening.reconcile_source',return_value=source):
            return audit_opening(bindings,payload,b'authored source',team='49ers',cutoff=cutoff)

    def test_later_source_is_flagged_without_adjusting_cap_or_declaring_missing_debt_zero(self):
        report=self.audit()
        self.assertEqual(report['saved_league_cap'],322000000)
        self.assertEqual(report['saved_roster_payroll'],19064000)
        self.assertFalse(report['retained_liabilities_known'])
        self.assertFalse(report['complete_opening_books']);self.assertFalse(report['write_authorized'])
        self.assertTrue(any('after the preseason cutoff' in b for b in report['blockers']))

    def test_dated_roster_source_alone_is_not_complete_retained_liability_coverage(self):
        report=self.audit(as_of='2026-08-01T00:00:00Z')
        self.assertFalse(report['ready_for_signing_test'])
        self.assertFalse(any('after the preseason cutoff' in b for b in report['blockers']))

    def test_cutoff_cannot_be_switched_to_another_season(self):
        with self.assertRaises(ValueError):self.audit(cutoff='2025-08-06')
