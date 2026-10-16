import json
from pathlib import Path
import tempfile
from threading import Event
import unittest
from unittest.mock import Mock
from franchise.nflverse import SeasonCache

CSV = b'player_id,season,passing_yards\nsource-id,2025,2500\n'


class HistoricalSeasonCacheTests(unittest.TestCase):
    def ready(self, cache, dataset='player_stats', year=2025):
        cache.poll(dataset, year, completed_game_seasons=0)
        # Wait for the authored worker explicitly; no polling sleeps or network.
        cache.requests[dataset, year].result(timeout=2)
        return cache.poll(dataset, year, completed_game_seasons=0)

    def test_inert_startup_requested_year_only_and_restart_pins_source(self):
        with tempfile.TemporaryDirectory() as directory:
            fetch = Mock(return_value=CSV)
            cache = SeasonCache(directory, opening_season=2026, fetch=fetch)
            self.assertFalse(list(Path(directory).iterdir())); fetch.assert_not_called()
            result = self.ready(cache)
            self.assertEqual(result.csv, CSV)
            self.assertEqual(result.season, 2025)
            self.assertIn('/stats_player/stats_player_reg_2025.csv', result.source_url)
            self.assertEqual(cache.poll('player_stats', 2025, completed_game_seasons=0), result)
            fetch.assert_called_once()
            cache.close()
            offline = Mock(side_effect=AssertionError('Cache restart must not fetch'))
            cache = SeasonCache(directory, opening_season=2026, fetch=offline)
            self.assertEqual(self.ready(cache), result); offline.assert_not_called(); cache.close()

    def test_pending_is_nonblocking_and_duplicate_player_requests_share_fetch(self):
        entered, release = Event(), Event()
        def fetch(_):
            entered.set()
            if not release.wait(2): raise RuntimeError('Fixture not released')
            return CSV
        with tempfile.TemporaryDirectory() as directory:
            cache = SeasonCache(directory, opening_season=2026, fetch=fetch)
            try:
                self.assertIsNone(cache.poll('player_stats',2025,completed_game_seasons=0)); self.assertTrue(entered.wait(1))
                self.assertIsNone(cache.poll('player_stats',2025,completed_game_seasons=0)); self.assertEqual(len(cache.requests),1)
            finally:
                release.set(); cache.close()

    def test_bad_cache_failure_and_source_failure_do_not_invent_stats_or_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            fetch=Mock(side_effect=OSError('offline'))
            cache=SeasonCache(directory,opening_season=2026,fetch=fetch)
            with self.assertRaises(OSError): self.ready(cache)
            with self.assertRaises(OSError): cache.poll('player_stats',2025,completed_game_seasons=0)
            fetch.assert_called_once(); cache.close()
            cache=SeasonCache(directory,opening_season=2026,fetch=lambda _:CSV)
            self.ready(cache);cache.close()
            path=Path(directory)/'player_stats-2025.json';record=json.loads(path.read_text())
            record['csv']+='changed';path.write_text(json.dumps(record))
            fetch=Mock(return_value=CSV);cache=SeasonCache(directory,opening_season=2026,fetch=fetch)
            with self.assertRaisesRegex(ValueError,'content differs'):self.ready(cache)
            fetch.assert_not_called();cache.close()

    def test_completed_game_season_disables_external_fetch_even_with_missing_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            fetch=Mock(return_value=CSV);cache=SeasonCache(directory,opening_season=2026,fetch=fetch)
            for completed in (1,2,True,None,-1):
                with self.subTest(completed=completed),self.assertRaises(ValueError):
                    cache.poll('player_stats',2025,completed_game_seasons=completed)
            fetch.assert_not_called();cache.close()

    def test_only_supported_past_seasons_no_arbitrary_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            fetch=Mock(return_value=CSV);cache=SeasonCache(directory,opening_season=2026,fetch=fetch)
            for kind,year in [('player_stats',2026),('player_stats',True),('snap_counts',2025),('../other',2025)]:
                with self.subTest(kind=kind,year=year),self.assertRaises(ValueError):cache.poll(kind,year,completed_game_seasons=0)
            fetch.assert_not_called();cache.close()
            with self.assertRaises(RuntimeError):cache.poll('player_stats',2025,completed_game_seasons=0)
