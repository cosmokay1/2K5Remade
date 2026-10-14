"""Offline optional-SDK check; never discovers credentials or submits inference.

Use --output with pythonw.exe to retain a no-console Windows result. This checks
packaging/client construction only, not authorized Google access or game AI.
"""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys


def check():
    from cryptography.hazmat.primitives import hashes
    from google.auth.credentials import AnonymousCredentials
    from google.auth.transport.requests import Request
    from google.genai import types
    from franchise.control import AccessDisabled, GoogleControl
    from franchise.vertex_provider import VertexProvider, VERTEX_SCHEMA

    digest = hashes.Hash(hashes.SHA256())
    digest.update(b'authored packaging fixture')
    if digest.finalize() != hashlib.sha256(b'authored packaging fixture').digest():
        raise RuntimeError('Bundled cryptography check failed')
    types.GenerateContentConfig(response_mime_type='application/json',
                                response_schema=VERTEX_SCHEMA)
    credentials = AnonymousCredentials()
    provider = VertexProvider(project='offline-packaging-fixture', location='global',
                              model='offline-packaging-fixture', credentials=credentials)
    provider._client.close()
    Request().session.close()
    control = GoogleControl(project='offline-packaging-fixture', bucket='unused',
                            object_name='unused', credentials=credentials)
    try:
        control()
    except AccessDisabled:
        pass
    else:
        raise RuntimeError('Credential-free control must reject access')
    return {'scope': 'offline SDK import/client construction; no cloud or game calls',
            'python': sys.version,
            'versions': {name: version(name) for name in ('google-genai', 'google-auth',
                         'pydantic', 'pydantic-core', 'cryptography')},
            'passes': ['compiled crypto', 'response schema', 'explicit anonymous client',
                       'requests transport', 'credential-free control rejection']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    status = 0
    try:
        result = check()
    except Exception as error:
        result = {'scope': 'offline SDK packaging check', 'error_type': type(error).__name__}
        status = 1
    if args.output:
        with args.output.open('x', encoding='utf-8') as writer:
            json.dump(result, writer, indent=2)
    else:
        print(json.dumps(result, indent=2))
    return status


if __name__ == '__main__':
    sys.exit(main())
