from contextlib import closing
from datetime import date
from pathlib import Path
import sqlite3
import json
import tempfile
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger, Rejected
from franchise.store import FranchiseStore


class CalendarAnchorTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'league.sqlite'
        self.store = FranchiseStore(self.path)
        for team in ('a','b'):
            self.store.create_team(team, Ledger.from_opening(OpeningBooks(), cap=100,
                roster_reserve=0, max_bonus_years=5, veteran_minimums={}))
        self.terms = dict(request_id='calendar-2026', league_year=2026,
                          source='synthetic declared league year', expected_revisions={'a':0,'b':0})

    def test_complete_atomic_anchor_replays_without_cash_or_cap_changes(self):
        before = {team:self.store.load_team(team).financial_snapshot() for team in ('a','b')}
        self.assertIsNone(self.store.league_calendar())
        anchor = self.store.anchor_calendar(**self.terms)
        restarted = FranchiseStore(self.path)
        self.assertEqual(restarted.league_calendar(), anchor)
        for team in ('a','b'):
            ledger = restarted.load_team(team)
            expected = dict(before[team], revision=1)
            self.assertEqual(ledger.financial_snapshot(), expected)
            ledger._check_transaction_date(2026, date(2026,7,1))
            with self.assertRaises(Rejected):
                ledger._check_transaction_date(2027, date(2027,7,1))
        raw = self.path.read_bytes()
        self.assertEqual(restarted.anchor_calendar(**self.terms), anchor)
        self.assertEqual(self.path.read_bytes(), raw)
        with self.assertRaises(Rejected):
            restarted.anchor_calendar(**dict(self.terms, league_year=2027))
        with self.assertRaises(Rejected):
            restarted.create_team('c', Ledger.from_opening(OpeningBooks(), cap=100,
                roster_reserve=0, max_bonus_years=5, veteran_minimums={}))

    def test_missing_team_stale_revision_and_invalid_year_change_nothing(self):
        raw = self.path.read_bytes()
        for changes in ({'expected_revisions':{'a':0}}, {'expected_revisions':{'a':0,'b':1}},
                        {'league_year':True}, {'league_year':2031}):
            with self.subTest(changes=changes), self.assertRaises((ValueError,Rejected)):
                self.store.anchor_calendar(**dict(self.terms, **changes))
            self.assertEqual(self.path.read_bytes(), raw)
        self.assertIsNone(self.store.league_calendar())

    def test_missing_or_changed_peer_anchor_refuses_replay(self):
        self.store.anchor_calendar(**self.terms)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DELETE FROM events WHERE team_id='b' AND kind='calendar_anchor'")
            db.commit()
        with self.assertRaisesRegex(ValueError, 'complete league'):
            self.store.load_team('a')

    def test_calendar_anchor_survives_generation_migration_in_both_orders(self):
        self.store.anchor_calendar(**self.terms)
        self.store.migrate_generations(self.path)
        self.assertEqual(FranchiseStore(self.path).league_calendar()['league_year'], 2026)
        second_path = self.path.with_name('second.sqlite')
        second = FranchiseStore(second_path)
        for team in ('a','b'):
            second.create_team(team, Ledger.from_opening(OpeningBooks(), cap=100,
                roster_reserve=0, max_bonus_years=5, veteran_minimums={}))
        second.migrate_generations(second_path)
        second.anchor_calendar(**self.terms)
        self.assertEqual(FranchiseStore(second_path).load_team('a').revision, 1)
        self.assertEqual(second.league_calendar()['league_year'], 2026)

    def test_boolean_revision_cannot_impersonate_integer_posting(self):
        self.store.anchor_calendar(**self.terms)
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute("SELECT id,payload FROM events WHERE team_id='a' AND kind='calendar_anchor'").fetchone()
            payload = json.loads(row[1])
            payload['posting']['revision'] = True
            db.execute('UPDATE events SET payload=? WHERE id=?', (json.dumps(payload),row[0]))
            db.commit()
        with self.assertRaisesRegex(ValueError, 'posting types'):
            self.store.load_team('b')

    def test_sourced_profile_year_disagreement_rolls_back_entire_league(self):
        from franchise.salary_rules import VeteranMinimumProfile
        path = self.path.with_name('sourced.sqlite')
        store = FranchiseStore(path)
        for team,year in (('a',2026),('b',2025)):
            store.create_team(team, Ledger.from_opening(OpeningBooks(), cap=100,
                roster_reserve=0, max_bonus_years=5, veteran_minimums={},
                veteran_minimum_profile=VeteranMinimumProfile(year, ())))
        raw = path.read_bytes()
        with self.assertRaisesRegex(Rejected, 'sourced rules'):
            store.anchor_calendar(**self.terms)
        self.assertEqual(path.read_bytes(), raw)
        self.assertIsNone(store.league_calendar())
