import http.client
import json
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
