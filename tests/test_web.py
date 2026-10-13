import http.client
import json
import shutil
import ssl
import subprocess
from pathlib import Path
import tempfile
import threading
import unittest
from franchise.books import OpeningBooks
from franchise.cap import Ledger, Offer
from franchise.store import FranchiseStore
from franchise.web import make_server


class WebOriginTests(unittest.TestCase):
    def test_authenticated_preview_has_no_signing_or_inference_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FranchiseStore(Path(directory) / 'franchise.sqlite')
            store.create_team('a', Ledger.from_opening(OpeningBooks(), cap=100, roster_reserve=0,
                max_bonus_years=5, veteran_minimums={'p': (10,)}))
            server = make_server(store, 'a', 't' * 32, port=0)
            worker = threading.Thread(target=server.serve_forever)
            worker.start()
            try:
                def request(method, path, body=None, authorized=True):
                    connection = http.client.HTTPConnection(*server.server_address, timeout=5)
                    headers = {'Authorization': 'Bearer ' + 't'*32} if authorized else {}
                    connection.request(method, path, json.dumps(body) if body is not None else None, headers)
                    reply = connection.getresponse()
                    result = reply.status, json.loads(reply.read())
                    connection.close()
                    return result
                self.assertEqual(request('GET', '/api/franchise', authorized=False)[0], 401)
                before = request('GET', '/api/franchise')[1]
                self.assertEqual(request('POST', '/api/preview', {'offer': Offer('p', (20,), 0).to_dict(), 'revision': 0})[0], 200)
                self.assertEqual(request('POST', '/api/preview', {'offer': Offer('p', (101,), 0).to_dict(), 'revision': 0})[0], 409)
                self.assertEqual(request('POST', '/api/preview', {'offer': Offer('p', (20,), 0).to_dict(), 'revision': True})[0], 409)
                self.assertEqual(request('POST', '/api/sign', {})[0], 404)
                self.assertEqual(request('GET', '/api/franchise')[1], before)
            finally:
                server.shutdown()
                worker.join()
                server.server_close()

    def test_remote_negotiation_shutdown_and_durable_recall(self):
        from franchise.control import AccessDisabled
        with tempfile.TemporaryDirectory() as directory:
            store = FranchiseStore(Path(directory) / 'franchise.sqlite')
            store.create_team('a', Ledger.from_opening(OpeningBooks(), cap=100, roster_reserve=0,
                max_bonus_years=5, veteran_minimums={'p': (10,)}))
            enabled, calls, disable_during = True, [], False
            def check():
                if not enabled:
                    raise AccessDisabled('test shutdown')
            def provider(context):
                nonlocal enabled
                calls.append(context)
                if disable_during:
                    enabled = False
                return json.dumps({'action':'accept', 'reason':'Synthetic performance agreement',
                                   'salaries':None, 'signing_bonus':None})
            server = make_server(store, 'a', 't'*32, port=0, negotiation_provider=provider, ai_access_check=check)
            worker = threading.Thread(target=server.serve_forever)
            worker.start()
            request = {'protocol':1, 'request_id':'negotiation-1', 'operation':'negotiate',
                       'team_id':'a', 'offer':Offer('p', (20,), 0).to_dict(),
                       'expected_revision':0, 'timeout_ms':5000,
                       'personality':{'money':0.8}, 'performance':{'source':'synthetic', 'receiving_yards':1100},
                       'relationships':{}}
            def send(body):
                connection = http.client.HTTPConnection(*server.server_address, timeout=5)
                connection.request('POST', '/api/negotiate', json.dumps(body), {'Authorization':'Bearer '+'t'*32})
                response = connection.getresponse()
                result = response.status, json.loads(response.read())
                connection.close()
                return result
            try:
                before = store.load_team('a').financial_snapshot()
                enabled = False
                self.assertEqual(send(request)[1]['error'], 'ai_disabled')
                self.assertFalse(calls)
                enabled, disable_during = True, True
                self.assertEqual(send(request)[1]['error'], 'ai_disabled')
                self.assertEqual(store.load_team('a').financial_snapshot(), before)
                enabled, disable_during = True, False
                response = send(request)
                self.assertEqual(response[0], 200)
                self.assertEqual(response[1]['result']['outcome'], 'signed')
                count = len(calls)
                self.assertEqual(send(request), response)
                self.assertEqual(len(calls), count)
                self.assertEqual(FranchiseStore(store.path).load_team('a').revision, 1)
                enabled = False
                self.assertEqual(send(request)[1]['error'], 'ai_disabled')
                self.assertEqual(send({**request,'team_id':'another'})[0], 400)
            finally:
                server.shutdown()
                worker.join()
                server.server_close()

    @unittest.skipUnless(shutil.which('openssl'), 'TLS fixture generation requires OpenSSL CLI')
    def test_tls_origin_requires_trusted_certificate_and_matches_hostname(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cert, key = root / 'origin.crt', root / 'origin.key'
            subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1',
                '-keyout', str(key), '-out', str(cert)], check=True, capture_output=True)
            server = make_server(None, None, 't'*32, port=0, tls_cert=cert, tls_key=key)
            worker = threading.Thread(target=server.serve_forever)
            worker.start()
            try:
                connection = http.client.HTTPSConnection(*server.server_address, context=ssl.create_default_context(), timeout=5)
                try:
                    with self.assertRaises(ssl.SSLCertVerificationError):
                        connection.request('GET', '/health')
                finally:
                    connection.close()
                context = ssl.create_default_context(cafile=str(cert))
                connection = http.client.HTTPSConnection(*server.server_address, context=context, timeout=5)
                try:
                    connection.request('GET', '/health')
                    response = connection.getresponse()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(json.loads(response.read())['status'], 'ready')
                finally:
                    connection.close()
                import socket
                with socket.create_connection(server.server_address, timeout=5) as raw:
                    with self.assertRaises(ssl.SSLCertVerificationError):
                        context.wrap_socket(raw, server_hostname='wrong-host.invalid')
            finally:
                server.shutdown()
                worker.join()
                server.server_close()

    def test_authenticated_player_context_and_strict_query(self):
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            store.create_franchise({'a':Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
                max_bonus_years=5,veteran_minimums={'p':(1,)})},seed='fixture-world')
            server=make_server(store,'a','t'*32,port=0)
            worker=threading.Thread(target=server.serve_forever)
            worker.start()
            try:
                def get(path,authenticated=True):
                    connection=http.client.HTTPConnection(*server.server_address,timeout=5)
                    connection.request('GET',path,headers={'Authorization':'Bearer '+'t'*32} if authenticated else {})
                    response=connection.getresponse()
                    result=response.status,json.loads(response.read())
                    connection.close()
                    return result
                self.assertEqual(get('/api/player?player_id=p',False)[0],401)
                self.assertEqual(get('/api/players',False)[0],401)
                status,players=get('/api/players')
                self.assertEqual(status,200)
                self.assertEqual(players,store.registered_players('a'))
                self.assertEqual(players['players'],[{'player_id':'p','contract_classification':'veteran','initialized':True}])
                status,profile=get('/api/player?player_id=p')
                self.assertEqual(status,200)
                self.assertTrue(profile['initialized'])
                self.assertEqual(profile['personality'],store.load_team('a')._actors['p']['personality'])
                self.assertEqual(get('/api/player?player_id=p&player_id=p')[0],400)
                self.assertEqual(get('/api/player?player_id=')[0],400)
                self.assertEqual(get('/api/player?player_id=unknown')[0],404)
                self.assertEqual(get('/api/player?player_id=p&team_id=other')[0],400)
                self.assertEqual(store.load_team('a').revision,0)
            finally:
                server.shutdown()
                worker.join()
                server.server_close()
