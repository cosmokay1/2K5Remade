"""Authenticated HTTP origin for franchise inspection and contract previews."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from franchise.cap import Offer, Rejected
from franchise.store import FranchiseStore


def make_server(store, team_id, token, *, port=8786):
    if type(token) is not str or len(token) < 32 or not token.isascii() or not token.isprintable():
        raise ValueError('A private ASCII API token of at least 32 characters is required')
    if store is not None:
        store.load_team(team_id)

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *_):
            pass  # Never log credentials, requests or financial bodies.

        def reply(self, status, body):
            data = json.dumps(body, allow_nan=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(data)

        def authorized(self):
            values = self.headers.get_all('Authorization') or []
            provided = values[0] if len(values) == 1 else ''
            if not hmac.compare_digest(provided.encode(), ('Bearer ' + token).encode()):
                self.reply(401, {'error': 'authentication_required'})
                return False
            return True

        def do_GET(self):
            if self.path == '/health':
                self.reply(200, {'service': 'llm-2k5', 'status': 'ready', 'protocol': 1})
            elif self.path == '/':
                self.reply(200, {'project': 'LLM 2K5', 'franchise_api': '/api/franchise',
                    'package_status': 'playable_build_unavailable',
                    'source': 'https://github.com/cosmokay1/2K5Remade',
                    'capabilities': ['authenticated_franchise_inspection', 'contract_preview'],
                    'game_integration': 'unfinished', 'paid_inference': False})
            elif self.path == '/api/franchise':
                if not self.authorized():
                    return
                if store is None:
                    self.reply(503, {'error': 'franchise_not_configured'})
                    return
                try:
                    self.reply(200, store.load_team(team_id).financial_snapshot())
                except Exception:
                    self.reply(503, {'error': 'franchise_unavailable'})
            else:
                self.reply(404, {'error': 'not_found'})

        def do_POST(self):
            self.close_connection = True
            if not self.authorized():
                return
            if self.path != '/api/preview':
                self.reply(404, {'error': 'not_found'})
                return
            if store is None:
                self.reply(503, {'error': 'franchise_not_configured'})
                return
            try:
                lengths = self.headers.get_all('Content-Length') or []
                if len(lengths) != 1 or not lengths[0].isdecimal() or self.headers.get('Transfer-Encoding'):
                    raise ValueError('Invalid framing')
                length = int(lengths[0])
                if not 0 < length <= 65536:
                    raise ValueError('Invalid frame size')
                self.connection.settimeout(5)
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError('Incomplete request')
                data = json.loads(raw)
                if type(data) is not dict or set(data) != {'offer', 'revision'}:
                    raise ValueError('Invalid preview fields')
                result = store.preview_offer(team_id, Offer.from_dict(data['offer']), data['revision'])
            except Rejected:
                self.reply(409, {'error': 'offer_ineligible_or_stale'})
            except (ValueError, TypeError, KeyError, TimeoutError):
                self.reply(400, {'error': 'invalid_request'})
            except Exception:
                self.reply(503, {'error': 'franchise_unavailable'})
            else:
                self.reply(200, result)

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database')
    parser.add_argument('--team')
    parser.add_argument('--port', type=int, default=8786)
    args = parser.parse_args()
    if bool(args.database) != bool(args.team):
        parser.error('--database and --team must be supplied together')
    if args.database and not Path(args.database).is_file():
        parser.error('An existing franchise database is required')
    store = FranchiseStore(args.database) if args.database else None
    server = make_server(store, args.team, os.environ.get('FRANCHISE_WEB_TOKEN'), port=args.port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
