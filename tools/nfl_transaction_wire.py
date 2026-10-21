"""Read the public NFL transaction wire without granting roster/cap authority.

Keep every page receipt: one screen of 25 rows is not a complete month. Player
profile links identify wire entries, not GSIS identities. Unknown transaction
labels and same-day moves require review before availability can be established.
"""
from datetime import date
import hashlib
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

CATEGORIES = ('trades', 'signings', 'reserve-list', 'waivers', 'terminations', 'other')


class WirePage(HTMLParser):
    def __init__(self, url, year, month):
        super().__init__(convert_charrefs=True)
        self.url, self.year, self.month = url, year, month
        self.rows, self.next_urls = [], set()
        self.cells = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr':
            self.cells = []
        elif tag in ('td', 'th') and self.cells is not None:
            self.cell = {'text': '', 'links': []}
        elif tag == 'a':
            href = attrs.get('href', '')
            if self.cell is not None:
                self.cell['links'].append(href)
            if 'after=' in href:
                target = urljoin(self.url, href)
                here, there = urlsplit(self.url), urlsplit(target)
                if there.scheme != 'https' or there.netloc != 'www.nfl.com' or there.path != here.path:
                    raise ValueError('Transaction pagination left its original NFL month')
                if not there.query.startswith('after=') or '&' in there.query or there.fragment:
                    raise ValueError('Unsupported transaction cursor')
                # Preserve the provider's opaque cursor URL exactly. Encoding
                # its trailing base64 '=' returned page one on the live wire.
                # Content/row loop checks below still reject repeated pages.
                self.next_urls.add(target)

    def handle_data(self, data):
        if self.cell is not None:
            self.cell['text'] += data

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.cells.append(self.cell)
            self.cell = None
        elif tag == 'tr' and self.cells is not None:
            cells, self.cells = self.cells, None
            if len(cells) != 6 or cells[2]['text'].strip() == 'Date':
                return
            mm, dd = map(int, cells[2]['text'].strip().split('/'))
            if mm != self.month:
                raise ValueError('Transaction belongs to a different month')
            profile = [x for x in cells[3]['links'] if x.startswith('/players/')]
            if len(profile) > 1:
                raise ValueError('Ambiguous NFL player profile')
            clubs = []
            for cell in cells[:2]:
                links = [x for x in cell['links'] if x.startswith('/teams/')]
                if len(links) > 1 or not links and cell['text'].strip() != '--':
                    raise ValueError('Unsupported transaction club cell')
                clubs.append(links[0] if links else None)
            self.rows.append({'date': date(self.year, mm, dd).isoformat(),
                              'player': cells[3]['text'].strip(), 'profile': profile[0] if profile else None,
                              'from_club': clubs[0], 'to_club': clubs[1],
                              'transaction': cells[5]['text'].strip()})


def collect_month(fetch, *, year, month, category, cutoff, max_pages=100):
    """Fetch injected, bounded bytes; refuse loops/truncation rather than certify them."""
    day = date.fromisoformat(cutoff)
    if (type(year) is not int or type(month) is not int or year != day.year
            or not 1 <= month <= day.month or category not in CATEGORIES
            or type(max_pages) is not int or not 1 <= max_pages <= 100):
        raise ValueError('Explicit cutoff year/month and supported category required')
    url = f'https://www.nfl.com/transactions/league/{category}/{year}/{month}'
    seen, row_pages, receipts, rows = set(), set(), [], []
    for _ in range(max_pages):
        if url in seen:
            raise ValueError('Transaction cursor repeated; month is incomplete')
        seen.add(url)
        payload = fetch(url)
        if type(payload) is not bytes or len(payload) > 1_000_000:
            raise ValueError('Bounded transaction HTML required')
        page = WirePage(url, year, month)
        page.feed(payload.decode('utf-8'))
        if len(page.next_urls) > 1:
            raise ValueError('Ambiguous transaction pagination')
        if not page.rows:
            raise ValueError('Empty transaction page requires explicit provider review')
        fingerprint=tuple(tuple(sorted(row.items())) for row in page.rows)
        if fingerprint in row_pages:
            raise ValueError('Transaction page content repeated; month is incomplete')
        row_pages.add(fingerprint)
        receipts.append({'url': url, 'sha256': hashlib.sha256(payload).hexdigest(),
                         'bytes': len(payload), 'rows': len(page.rows)})
        rows.extend(row for row in page.rows if row['date'] <= cutoff)
        if not page.next_urls:
            unique = {tuple(sorted(row.items())): row for row in rows}
            return {'year': year, 'month': month, 'category': category, 'cutoff': cutoff,
                    'pages': receipts, 'rows': list(unique.values()),
                    'pagination_complete': True, 'availability_verified': False,
                    'writes_performed': False}
        url = next(iter(page.next_urls))
    raise ValueError('Page limit reached; month is incomplete')


def audit_espn_pages(pages, *, start, cutoff):
    """Validate a complete alternative feed, preserving prose for explicit review.

    Pagination completeness is not a guarantee that the provider recorded every
    NFL move. Do not infer an unsigned player's availability from missing text.
    """
    first, last = date.fromisoformat(start), date.fromisoformat(cutoff)
    if first.year != last.year or first > last or not pages:
        raise ValueError('Explicit same-season date range and all pages required')
    count, size, total = (pages[0].get(k) for k in ('count', 'pageSize', 'pageCount'))
    if any(type(n) is not int or n <= 0 for n in (count, size, total)):
        raise ValueError('Positive feed pagination metadata required')
    if total != (count + size - 1) // size or len(pages) != total:
        raise ValueError('Missing transaction pages')
    rows, indexes = [], set()
    for page in pages:
        index = page.get('pageIndex')
        if (type(index) is not int or index in indexes or not 1 <= index <= total
                or page.get('status') != 'success'
                or page.get('requestedYear', {}).get('year') != first.year
                or any(page.get(k) != n for k, n in zip(('count', 'pageSize', 'pageCount'), (count, size, total)))):
            raise ValueError('Repeated or inconsistent transaction page')
        indexes.add(index)
        items = page.get('transactions')
        if type(items) is not list or len(items) != min(size, count - (index - 1)*size):
            raise ValueError('Truncated transaction page')
        for item in items:
            day = date.fromisoformat(item['date'][:10])
            if not first <= day <= last:
                raise ValueError('Transaction outside requested dates')
            team = item.get('team', {}).get('abbreviation')
            description = item.get('description')
            if not team or type(description) is not str:
                raise ValueError('Missing transaction club or description')
            rows.append({'date': day.isoformat(), 'team': team, 'description': description})
    if len({tuple(sorted(row.items())) for row in rows}) != count:
        raise ValueError('Duplicate transaction rows; feed coverage requires review')
    return {'start': start, 'cutoff': cutoff, 'rows': rows,
            'pagination_complete': True,
            'empty_description_count': sum(not row['description'].strip() for row in rows),
            'availability_verified': False, 'writes_performed': False}
