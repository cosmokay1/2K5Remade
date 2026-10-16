"""Lazy, local historical season cache. No game, model or financial authority."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from threading import Lock
from urllib.request import urlopen

SOURCES = {
    'rosters': ('rosters/roster_', 1920),
    'player_stats': ('stats_player/stats_player_reg_', 1999),
}
ATTRIBUTION = 'nflverse'
LICENSE_URL = 'https://github.com/nflverse/nflverse-data/blob/main/LICENSE.md'
MAX_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True)
class SeasonDataset:
    dataset: str
    season: int
    source_url: str
    sha256: str
    csv: bytes


def _download(url):
    with urlopen(url, timeout=10) as response:
        payload = response.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise ValueError('Historical season dataset exceeds the supported size')
    return payload


class SeasonCache:
    """poll returns None while pending; failures remain explicit, never zero stats.

    Construction is inert. Only a requested dataset/year starts disk/network work,
    on one background worker. A completed cache entry is immutable: restarting or
    another player lookup uses the same source bytes. The caller must match real
    player identities and keep imported history separate from simulated seasons.
    """
    def __init__(self, directory, *, opening_season, fetch=_download):
        if type(opening_season) is not int or not 1921 <= opening_season <= 2100:
            raise ValueError('Explicit franchise opening season required')
        self.directory = Path(directory)
        self.opening_season = opening_season
        self.fetch = fetch
        self.lock = Lock()
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix='historical-season')
        self.requests = {}
        self.closed = False

    def poll(self, dataset, season, *, completed_game_seasons):
        if type(completed_game_seasons) is not int or completed_game_seasons != 0:
            raise ValueError('External history is a fallback only before a complete in-game season')
        if (type(dataset) is not str or dataset not in SOURCES or type(season) is not int or
                not SOURCES[dataset][1] <= season < self.opening_season):
            raise ValueError('Supported historical dataset and pre-franchise season required')
        with self.lock:
            if self.closed:
                raise RuntimeError('Historical season cache is closed')
            key = dataset, season
            if key not in self.requests:
                self.requests[key] = self.worker.submit(self._load, dataset, season)
            future = self.requests[key]
        return future.result() if future.done() else None

    def _load(self, dataset, season):
        url = ('https://github.com/nflverse/nflverse-data/releases/download/' +
               SOURCES[dataset][0] + str(season) + '.csv')
        target = self.directory / f'{dataset}-{season}.json'
        def read():
            # The cache is application-owned, not a caller-provided URL or path.
            if target.stat().st_size > MAX_BYTES * 2:
                raise ValueError('Historical cache exceeds supported size')
            record = json.loads(target.read_text(encoding='utf-8'))
            if (record.get('version') != 1 or record.get('dataset') != dataset or
                    record.get('season') != season or record.get('source_url') != url):
                raise ValueError('Historical cache identity differs')
            payload = record['csv'].encode('utf-8')
            if len(payload) > MAX_BYTES or hashlib.sha256(payload).hexdigest() != record['sha256']:
                raise ValueError('Historical cache content differs')
            return SeasonDataset(dataset, season, url, record['sha256'], payload)
        if target.exists():
            return read()
        payload = self.fetch(url)
        if type(payload) is not bytes or not payload or len(payload) > MAX_BYTES:
            raise ValueError('Bounded nonempty historical CSV required')
        text = payload.decode('utf-8')
        # Reject an HTML error/landing page before pinning it as a season CSV.
        if not text.splitlines() or ',' not in text.splitlines()[0] or text.lstrip().startswith('<'):
            raise ValueError('Historical source did not return a CSV')
        payload = text.encode('utf-8')
        record = dict(version=1, dataset=dataset, season=season, source_url=url,
                      sha256=hashlib.sha256(payload).hexdigest(), csv=text,
                      attribution=ATTRIBUTION, license_url=LICENSE_URL)
        self.directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.directory,
                                         prefix='.historical-', delete=False) as file:
            temporary = Path(file.name)
            try:
                json.dump(record, file, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            # Never replace a season already pinned by another cache instance.
            try:
                os.link(temporary, target)
            except FileExistsError:
                pass
        finally:
            temporary.unlink(missing_ok=True)
        return read()

    def close(self):
        with self.lock:
            self.closed = True
        self.worker.shutdown(wait=True, cancel_futures=True)
