#!/usr/bin/env python3
"""Local Presentation Studio server; Python standard library, Linux/Deck/Windows."""
import argparse
import json
import mimetypes
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from networks import NETWORKS, load_settings, read_schedule, save_settings

WEB = {'.html', '.css', '.js', '.json', '.png', '.jpg', '.jpeg', '.gif',
       '.svg', '.webp', '.ttf', '.otf', '.woff', '.woff2', '.mp4', '.webm', '.mp3'}
PAGE = '/tools/presentation-studio/index.html'


def contained(root, relative):
    """Reject traversal and symlink escapes, including not-yet-created files."""
    relative = relative.replace('\\', '/')
    if ':' in relative or '..' in relative.split('/') or relative.startswith('/'):
        raise ValueError('bad path')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError('path escapes root')
    return path


def package_name(name):
    if not name or name.startswith(('.', '_')) or len(name) > 64 or re.search(r'[\\/:*?"<>|]', name):
        raise ValueError('bad package name')
    return name


def make_server(presentations, port=8735, saves=None):
    presentations = Path(presentations).resolve()
    editor = Path(__file__).with_name('index.html')
    saves = Path(saves).resolve() if saves else None
    settings_file = presentations.parent / 'broadcast-networks.json'
    write_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def send(self, code, body, kind='text/plain; charset=utf-8'):
            if isinstance(body, str):
                body = body.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def package(self, name):
            path = contained(presentations, package_name(name))
            manifest = contained(path, 'mod.json')
            if json.loads(manifest.read_text()).get('type') != 'html':
                raise ValueError('not an HTML package')
            return path

        def do_GET(self):
            self.handle_request(False)

        def do_POST(self):
            with write_lock:
                self.handle_request(True)

        def handle_request(self, post):
            # Restrict Host as well as Origin: protects local writes from other sites.
            authority = f'127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host') != authority or self.headers.get('Origin', f'http://{authority}') != f'http://{authority}':
                self.send(403, 'use the local editor URL')
                return
            url = urlsplit(self.path)
            path = unquote(url.path)
            query = parse_qs(url.query)
            arg = lambda key: query.get(key, [''])[0]
            try:
                if path == '/api/network-saves' and not post:
                    files = [str(f.relative_to(saves)) for f in sorted(saves.rglob('SAVEGAME.DAT'))
                             if f.resolve().is_relative_to(saves) and f.is_file()] if saves else []
                    self.send(200, json.dumps(files), 'application/json')
                    return
                if path == '/api/networks':
                    if not saves:
                        raise ValueError('Start with --saves pointing at your game saves directory')
                    save = contained(saves, arg('save'))
                    if save.name != 'SAVEGAME.DAT':
                        raise ValueError('Select a franchise SAVEGAME.DAT')
                    schedule = read_schedule(save.read_bytes())
                    settings = load_settings(settings_file)
                    if post:
                        length = int(self.headers.get('Content-Length', '-1'))
                        if not 0 <= length <= 65536:
                            raise ValueError('Invalid settings request size')
                        change = json.loads(self.rfile.read(length))
                        if not isinstance(change, dict):
                            raise ValueError('Invalid settings request')
                        if 'enabled' in change:
                            if type(change['enabled']) is not bool:
                                raise ValueError('Enabled must be true or false')
                            settings['enabled'] = change['enabled']
                        if 'key' in change:
                            if change['key'] not in {g['key'] for g in schedule['games']} or change.get('network') not in ('', *NETWORKS):
                                raise ValueError('Unknown game or network')
                            if change['network']:
                                settings['overrides'][change['key']] = change['network']
                            else:
                                settings['overrides'].pop(change['key'], None)
                        if 'packages' in change:
                            if not isinstance(change['packages'], dict):
                                raise ValueError('Invalid network package mapping')
                            for network, folder in change['packages'].items():
                                if network not in NETWORKS or not isinstance(folder, str):
                                    raise ValueError('Invalid network package mapping')
                                if folder:
                                    directory = contained(presentations, package_name(folder))
                                    if not any(contained(directory, f).is_file() for f in ('mod.json', 'presentation.json')):
                                        raise ValueError('Unknown presentation package')
                                settings['packages'][network] = folder
                        save_settings(settings_file, settings)
                    packages = []
                    for directory in sorted(presentations.iterdir()):
                        if directory.name.startswith(('.', '_')) or not directory.is_dir():
                            continue
                        for manifest in ('presentation.json', 'mod.json'):
                            try:
                                info = json.loads(contained(presentations, directory.name + '/' + manifest).read_text())
                                packages.append(dict(folder=directory.name, name=info.get('name',directory.name)))
                                break
                            except (ValueError, OSError):
                                continue
                    self.send(200, json.dumps(dict(**schedule, settings=settings, networks=NETWORKS, packages=packages)), 'application/json')
                    return
                if not post:
                    if path == '/api/packages':
                        packages = []
                        for child in sorted(presentations.iterdir()):
                            try:
                                folder = self.package(child.name)
                                mod = json.loads((folder / 'mod.json').read_text())
                                packages.append(dict(folder=child.name, name=mod.get('name', child.name),
                                                     entry=mod.get('entry', 'index.html'), canvas=mod.get('canvas')))
                            except (ValueError, OSError):
                                continue
                        self.send(200, json.dumps(packages), 'application/json')
                        return
                    if path == '/api/files':
                        folder = self.package(arg('package'))
                        files = [str(f.relative_to(folder)) for f in sorted(folder.rglob('*'))
                                 if f.is_file() and f.resolve().is_relative_to(folder)]
                        self.send(200, json.dumps(files), 'application/json')
                        return
                    if path == '/networks':
                        file = editor.with_name('networks.html')
                    elif path in ('/', '/tools/presentation-studio', '/tools/presentation-studio/', PAGE):
                        file = editor
                    elif path.startswith('/mods/presentations/'):
                        file = contained(presentations, path[len('/mods/presentations/'):])
                    else:
                        self.send(404, 'not found')
                        return
                    if file.suffix.lower() not in WEB:
                        raise ValueError('unsupported file type')
                    self.send(200, file.read_bytes(), mimetypes.guess_type(file)[0] or 'application/octet-stream')
                    return
                if path not in ('/api/create-package', '/api/save-layout', '/api/upload-asset', '/api/write'):
                    self.send(404, 'not found')
                    return
                length = int(self.headers.get('Content-Length', '-1'))
                if not 0 <= length <= 32 * 1024 * 1024:
                    self.send(413, 'request must have a length of at most 32 MiB')
                    return
                body = self.rfile.read(length)
                if len(body) != length:
                    raise ValueError('incomplete body')
                if path == '/api/create-package':
                    name = package_name(arg('name'))
                    folder = contained(presentations, name)
                    if folder.exists():
                        self.send(409, 'package already exists')
                        return
                    manifest = json.loads(body)
                    if not isinstance(manifest, dict) or manifest.get('type') != 'html':
                        raise ValueError('mod.json type must be html')
                    folder.mkdir()
                    (folder / 'mod.json').write_bytes(body)
                    self.send(200, name)
                    return
                folder = self.package(arg('package'))
                relative = ('layout.css' if path == '/api/save-layout' else
                            'assets/' + arg('name').replace('\\', '/').split('/')[-1]
                            if path == '/api/upload-asset' else arg('path'))
                file = contained(folder, relative)
                if file.suffix.lower() not in WEB:
                    raise ValueError('unsupported file type')
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(body)
                self.send(200, relative if path == '/api/upload-asset' else 'saved')
            except FileNotFoundError:
                self.send(404, 'not found')
            except (ValueError, OSError) as error:
                self.send(400, str(error))

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--presentations', type=Path,
                        default=Path(__file__).resolve().parents[2] / 'mods/presentations')
    parser.add_argument('--port', type=int, default=8735)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--saves', type=Path, help='Read-only root containing franchise SAVEGAME.DAT files')
    args = parser.parse_args()
    if not args.presentations.is_dir():
        parser.error('presentation directory does not exist')
    with make_server(args.presentations, args.port, args.saves) as server:
        address = f'http://127.0.0.1:{server.server_port}{PAGE}'
        print(f'Presentation Studio: {address}\nEditing: {args.presentations.resolve()}', flush=True)
        if not args.no_browser:
            webbrowser.open(address)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
