"""Authenticated HTTP origin for franchise inspection and contract previews."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import ssl
from urllib.parse import parse_qs
from threading import Lock
from pathlib import Path
from franchise.cap import Offer, Rejected
from franchise.store import FranchiseStore
from franchise.bridge import Bridge


def make_server(store, team_id, token, *, port=8786, tls_cert=None, tls_key=None,
                negotiation_provider=None, ai_access_check=None):
    if (negotiation_provider is None) != (ai_access_check is None):
        raise ValueError('Negotiation provider and remote access check required together')
    if negotiation_provider is not None and (not callable(negotiation_provider) or not callable(ai_access_check)):
        raise ValueError('Callable negotiation provider and access check required')
    negotiation_lock = Lock()
    if bool(tls_cert) != bool(tls_key):
        raise ValueError('TLS certificate and key are required together')
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
            elif self.path.partition('?')[0] == '/api/player':
                if not self.authorized():
                    return
                if store is None:
                    self.reply(503, {'error': 'franchise_not_configured'})
                    return
                try:
                    query = self.path.partition('?')[2]
                    if len(query) > 4096:
                        raise ValueError('Query too large')
                    fields = parse_qs(query,keep_blank_values=True,strict_parsing=True)
                    if set(fields) != {'player_id'} or len(fields['player_id']) != 1:
                        raise ValueError('Single player identity required')
                    result = store.player_context(team_id,fields['player_id'][0])
                except Rejected:
                    self.reply(404, {'error': 'player_unavailable'})
                except (ValueError,TypeError):
                    self.reply(400, {'error': 'invalid_request'})
                except Exception:
                    self.reply(503, {'error': 'franchise_unavailable'})
                else:
                    self.reply(200,result)
            elif self.path == '/api/players':
                if not self.authorized():
                    return
                if store is None:
                    self.reply(503, {'error': 'franchise_not_configured'})
                    return
                try:
                    self.reply(200,store.registered_players(team_id))
                except Exception:
                    self.reply(503, {'error': 'franchise_unavailable'})
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
            if self.path not in ('/api/preview', '/api/negotiate'):
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
                if self.path == '/api/negotiate':
                    if type(data) is not dict or data.get('operation') != 'negotiate' or data.get('team_id') != team_id:
                        raise ValueError('Negotiation must belong to the configured franchise')
                    if negotiation_provider is None:
                        self.reply(503, {'error': 'ai_not_configured'})
                        return
                    if not negotiation_lock.acquire(blocking=False):
                        self.reply(429, {'error': 'busy'})
                        return
                    try:
                        result = Bridge(store, provider=negotiation_provider, access_check=ai_access_check).handle(data)
                    finally:
                        negotiation_lock.release()
                    status = {None: 200, 'ai_disabled': 503, 'state_rejected': 409,
                              'timeout': 504, 'service_failure': 503}.get(result['error'], 400)
                    self.reply(status, result)
                    return
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

    context = None
    if tls_cert:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(tls_cert, tls_key)

    class OriginServer(ThreadingHTTPServer):
        def get_request(self):
            connection, address = super().get_request()
            connection.settimeout(5)
            if context is not None:
                try:
                    connection = context.wrap_socket(connection, server_side=True)
                except BaseException:
                    connection.close()
                    raise
            return connection, address

    return OriginServer(('127.0.0.1', port), Handler)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database')
    parser.add_argument('--team')
    parser.add_argument('--port', type=int, default=8786)
    parser.add_argument('--tls-cert')
    parser.add_argument('--tls-key')
    parser.add_argument('--ai', choices=('disabled', 'vertex-runtime'), default='disabled')
    args = parser.parse_args()
    if bool(args.database) != bool(args.team):
        parser.error('--database and --team must be supplied together')
    if args.database and not Path(args.database).is_file():
        parser.error('An existing franchise database is required')
    store = FranchiseStore(args.database) if args.database else None
    provider = access_check = None
    if args.ai == 'vertex-runtime':
        if store is None:
            parser.error('Live negotiation requires an existing configured franchise')
        try:
            from franchise.google_credentials import runtime_credentials
            from franchise.vertex_provider import VertexProvider
            from franchise.control import GoogleControl
            config = json.loads((Path(__file__).resolve().parents[1] / 'config/google.json').read_text())
            provider = VertexProvider(project=config['project'], location=config['location'], model=config['model'],
                credentials=runtime_credentials(config['project'], config['runtime_service_account']))
            access_check = GoogleControl(project=config['project'], bucket=config['control_bucket'],
                object_name=config['control_object'],
                credentials=runtime_credentials(config['project'], config['runtime_service_account']))
        except Exception:
            from franchise.control import AccessDisabled
            def unavailable(*_):
                raise AccessDisabled('Runtime authentication unavailable')
            provider = access_check = unavailable
    server = make_server(store, args.team, os.environ.get('FRANCHISE_WEB_TOKEN'), port=args.port,
                         tls_cert=args.tls_cert, tls_key=args.tls_key,
                         negotiation_provider=provider, ai_access_check=access_check)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
