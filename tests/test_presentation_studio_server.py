"""Exercise the real editor HTTP protocol against disposable presentation files."""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

spec = importlib.util.spec_from_file_location('studio_server', Path(__file__).resolve().parents[1] / 'tools/presentation-studio/serve.py')
sys.path.insert(0, str(Path(spec.origin).parent))
studio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(studio)


class StudioTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'presentations'
        self.root.mkdir()
        self.saves = Path(self.temp.name) / 'saves'
        self.saves.mkdir()
        self.package = self.root / 'My Broadcast'
        self.package.mkdir()
        (self.package / 'mod.json').write_text(json.dumps(dict(type='html', name='Broadcast', entry='index.html')))
        (self.package / 'index.html').write_text('<h1>Score</h1>')
        self.server = studio.make_server(self.root, 0, self.saves)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, body=None, headers=None):
        try:
            response = urlopen(Request(self.url + path, data=body, headers=headers or {}), timeout=3)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.read()

    def test_editor_and_package_preview(self):
        self.assertIn(b'Presentation Studio', self.request('/')[1])
        status, body = self.request('/api/packages')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)[0]['folder'], 'My Broadcast')
        self.assertEqual(self.request('/mods/presentations/My%20Broadcast/index.html'), (200, b'<h1>Score</h1>'))

    def test_layout_upload_code_and_file_listing(self):
        self.assertEqual(self.request('/api/save-layout?package=My%20Broadcast', b'#score {color:red}')[0], 200)
        self.assertEqual((self.package / 'layout.css').read_bytes(), b'#score {color:red}')
        self.assertEqual(self.request('/api/upload-asset?package=My%20Broadcast&name=logo.png', b'png'), (200, b'assets/logo.png'))
        self.assertEqual(self.request('/api/write?package=My%20Broadcast&path=sub/extra.js', b'hello')[0], 200)
        files = json.loads(self.request('/api/files?package=My%20Broadcast')[1])
        self.assertIn('sub/extra.js', files)
        self.assertEqual(self.request('/mods/presentations/My%20Broadcast/sub/extra.js'), (200, b'hello'))

    def test_import_and_conflict(self):
        body = b'{"type":"html","name":"Imported"}'
        self.assertEqual(self.request('/api/create-package?name=Imported', body)[0], 200)
        self.assertEqual(self.request('/api/create-package?name=Imported', body)[0], 409)
        self.assertEqual(self.request('/api/create-package?name=Invalid', b'{"type":"native"}')[0], 400)
        self.assertEqual(self.request('/api/create-package?name=Invalid', b'[]')[0], 400)

    def test_traversal_and_non_web_files_are_blocked(self):
        for path in ('../outside.css', '%2fetc/passwd', 'bad.exe', 'C:/bad.css'):
            self.assertEqual(self.request('/api/write?package=My%20Broadcast&path=' + path, b'bad')[0], 400)
        self.assertEqual(self.request('/mods/presentations/../secret.json')[0], 400)
        self.assertEqual(self.request('/franchise/google_credentials.py')[0], 404)

    def test_symlink_escape_blocked(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (outside / 'private.json').write_text('secret')
        (self.package / 'assets').symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.request('/api/upload-asset?package=My%20Broadcast&name=logo.png', b'bad')[0], 400)
        self.assertEqual(self.request('/mods/presentations/My%20Broadcast/assets/private.json')[0], 400)
        self.assertFalse((outside / 'logo.png').exists())

    def test_other_site_cannot_write(self):
        path = '/api/save-layout?package=My%20Broadcast'
        for headers in ({'Origin': 'https://example.com'}, {'Host': 'example.com'}):
            self.assertEqual(self.request(path, b'bad', headers)[0], 403)
        self.assertFalse((self.package / 'layout.css').exists())

    def test_network_override_is_durable_and_never_writes_save(self):
        from tests.test_broadcast_networks import fixture
        folder=self.saves/'MyNFL1';folder.mkdir()
        save=folder/'SAVEGAME.DAT';before=bytes(fixture());save.write_bytes(before)
        self.assertEqual(json.loads(self.request('/api/network-saves')[1]),['MyNFL1/SAVEGAME.DAT'])
        endpoint='/api/networks?save=MyNFL1/SAVEGAME.DAT'
        status,body=self.request(endpoint);self.assertEqual(status,200)
        data=json.loads(body);key=data['games'][0]['key']
        self.assertEqual(self.request(endpoint,json.dumps({'key':key,'network':'NBC'}).encode())[0],200)
        self.assertEqual(json.loads(self.request(endpoint)[1])['settings']['overrides'][key],'NBC')
        self.assertEqual(self.request(endpoint,json.dumps({'key':key,'network':''}).encode())[0],200)
        self.assertNotIn(key,json.loads(self.request(endpoint)[1])['settings']['overrides'])
        for change in ({'key':'unknown','network':'CBS'},{'key':key,'network':'Unknown'},{'enabled':'yes'},{'packages':{'FOX':'../bad'}}):
            self.assertEqual(self.request(endpoint,json.dumps(change).encode())[0],400)
        self.assertEqual(save.read_bytes(),before)
        self.assertEqual(self.request('/api/networks?save=../SAVEGAME.DAT')[0],400)
        self.assertEqual(self.request('/networks')[0],200)


if __name__ == '__main__':
    unittest.main()
