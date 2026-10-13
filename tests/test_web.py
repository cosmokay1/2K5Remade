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
