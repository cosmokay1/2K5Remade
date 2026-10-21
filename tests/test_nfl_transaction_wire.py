import unittest

from tools.nfl_transaction_wire import collect_month, audit_espn_pages


def html(*, name='Authored Player', day='09/07', next_url=None):
    row = ('<tr><td><a href="/teams/new-york-giants/">Giants</a></td><td>--</td>'
           f'<td>{day}</td><td><a href="/players/authored-player/">{name}</a></td>'
           '<td>LB</td><td>Terminated, Vested Veteran, all contracts</td></tr>')
    link = f'<a href="{next_url}">More</a>' if next_url else ''
    return f'<html>NFL Transactions<table>{row}</table>{link}</html>'.encode()


class WireTests(unittest.TestCase):
    def collect(self, fetch, **kwargs):
        return collect_month(fetch, year=2026, month=9, category='terminations',
                             cutoff='2026-09-10', **kwargs)

    def test_complete_month_keeps_profile_and_filters_future_moves(self):
        report = self.collect(lambda _: html()+html(name='Later Player', day='09/14'))
        self.assertEqual(len(report['rows']), 1)
        self.assertEqual(report['rows'][0]['profile'], '/players/authored-player/')
        self.assertTrue(report['pagination_complete'])
        self.assertFalse(report['availability_verified'])

    def test_provider_cursor_is_preserved_exactly_and_repeating_page_refuses_completion(self):
        urls = []
        def fetch(url):
            urls.append(url)
            return html(next_url='?after=abc+def=')
        with self.assertRaisesRegex(ValueError, 'repeated'):
            self.collect(fetch)
        self.assertEqual(urls[1].split('?', 1)[1], 'after=abc+def=')

    def test_unlinked_source_row_is_retained_without_inventing_a_player_profile(self):
        report=self.collect(lambda _:html().replace(b'<a href="/players/authored-player/">',b'<span>').replace(b'Authored Player</a>',b'Authored Player</span>'))
        self.assertIsNone(report['rows'][0]['profile'])
        self.assertFalse(report['availability_verified'])

    def test_outside_month_host_or_page_limit_refuses(self):
        for next_url in ('https://example.test/?after=x',
                         '/transactions/league/terminations/2026/8?after=x'):
            with self.assertRaises(ValueError):
                self.collect(lambda _: html(next_url=next_url))
        with self.assertRaisesRegex(ValueError, 'limit'):
            self.collect(lambda _: html(next_url='?after=x'), max_pages=1)
        with self.assertRaisesRegex(ValueError, 'Empty'):
            self.collect(lambda _: b'<html>NFL Transactions loading...</html>')

    def pages(self):
        return [dict(status='success', requestedYear={'year':2026}, count=2,
                     pageSize=1, pageCount=2, pageIndex=i,
                     transactions=[dict(date=f'2026-09-0{i}T07:00Z',
                                        team={'abbreviation':'NYG'}, description=description)])
                for i, description in enumerate(('Released LB Authored Player.', ''), 1)]

    def test_complete_alternative_feed_does_not_invent_availability_or_drop_empty_rows(self):
        report = audit_espn_pages(self.pages(), start='2026-01-01', cutoff='2026-09-10')
        self.assertEqual(report['empty_description_count'], 1)
        self.assertEqual(len(report['rows']), 2)
        self.assertFalse(report['availability_verified'])

    def test_missing_repeated_truncated_or_wrong_date_pages_refuse(self):
        for change in ('missing', 'repeated', 'truncated', 'future', 'count'):
            pages = self.pages()
            if change == 'missing':pages.pop()
            elif change == 'repeated':pages[1]['pageIndex']=1
            elif change == 'truncated':pages[1]['transactions']=[]
            elif change == 'future':pages[1]['transactions'][0]['date']='2026-09-11T07:00Z'
            else:pages[1]['count']=3
            with self.subTest(change=change), self.assertRaises(ValueError):
                audit_espn_pages(pages, start='2026-01-01', cutoff='2026-09-10')
