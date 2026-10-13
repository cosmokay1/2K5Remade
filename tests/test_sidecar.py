import json
import io
from unittest.mock import patch
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Event, Thread
import unittest
from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger
from franchise.sidecar import serve
from franchise.store import FranchiseStore
from queue import Queue


def request():
    return dict(protocol=1, request_id="one", operation="negotiate", team_id="a",
                offer=dict(player_id="v", salaries=[10], signing_bonus=0), expected_revision=0,
                timeout_ms=1000, personality={}, performance={}, relationships={})


class SidecarTests(unittest.TestCase):
    def test_real_process_handshake_preview_dialogue_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite"
            store = FranchiseStore(path)
            store.create_team("a", Ledger.from_opening(OpeningBooks(), cap=100,
                roster_reserve=0, max_bonus_years=5, veteran_minimums={"v": (1,)}))
            message_request = request()
            for attempt in range(2):
                process = subprocess.Popen([sys.executable, "-m", "franchise.sidecar", "--database", str(path),
                    "--provider", "offline-fixture"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True)
                try:
                    for message in (dict(protocol=1, request_id="hello", operation="hello"), message_request):
                        process.stdin.write(json.dumps(message) + "\n")
                        process.stdin.flush()
                        response = json.loads(process.stdout.readline())
                        self.assertIsNone(response["error"])
                    self.assertEqual(response["result"]["outcome"], "player_rejected")
                    process.stdin.close()
                    self.assertEqual(process.wait(timeout=5), 0)
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
                    for stream in (process.stdin, process.stdout, process.stderr):
                        stream.close()
            self.assertEqual(len(store.negotiation_history("a", "v")), 1)
            self.assertEqual(store.load_team("a").revision, 0)

    def test_busy_and_disconnect_do_not_commit_inflight_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FranchiseStore(Path(directory) / "state.sqlite")
            store.create_team("a", Ledger.from_opening(OpeningBooks(), cap=100,
                roster_reserve=0, max_bonus_years=5, veteran_minimums={"v": (1,)}))
            entered, release, closed = Event(), Event(), Event()
            incoming, outgoing = Queue(), Queue()
            class Reader:
                def readline(self, limit):
                    line = incoming.get(timeout=5)
                    if not line:
                        closed.set()
                    return line
            class Writer:
                def write(self, line):
                    outgoing.put(json.loads(line))
                def flush(self):
                    pass
            def provider(_):
                entered.set()
                release.wait(timeout=5)
                return json.dumps(dict(action="accept", reason="Yes", salaries=None, signing_bonus=None))
            bridge = Bridge(store, provider=provider, access_check=lambda: None)
            thread = Thread(target=serve, args=(bridge, Reader(), Writer()))
            thread.start()
            try:
                incoming.put(json.dumps(request()) + "\n")
                self.assertTrue(entered.wait(timeout=5))
                incoming.put(json.dumps({**request(), "request_id": "two"}) + "\n")
                self.assertEqual(outgoing.get(timeout=5)["error"], "busy")
                incoming.put("")
                self.assertTrue(closed.wait(timeout=5))
            finally:
                release.set()
                thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
            self.assertEqual(store.load_team("a").revision, 0)
            self.assertEqual(store.negotiation_history("a", "v"), [])

    def test_ai_initialization_failure_preserves_explicit_manual_financial_path(self):
        from franchise.sidecar import main
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite"
            store = FranchiseStore(path)
            store.create_team("a", Ledger.from_opening(OpeningBooks(), cap=100,
                roster_reserve=0, max_bonus_years=5, veteran_minimums={"v": (1,)}))
            manual = request()
            manual.update(operation="manual_sign", decision_mode="manual")
            for key in ("personality", "performance", "relationships"):
                del manual[key]
            messages = [dict(protocol=1, request_id="hello", operation="hello"), manual]
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(sys, "argv", ["sidecar", "--database", str(path), "--provider", "vertex"]), \
                 patch.object(sys, "stdin", io.StringIO("".join(json.dumps(item) + "\n" for item in messages))), \
                 patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr), \
                 patch("franchise.vertex_provider.VertexProvider", side_effect=RuntimeError("SECRET")):
                main()
            responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
            self.assertEqual(responses[0]["error"], "ai_disabled")
            self.assertEqual(responses[1]["result"]["decision_mode"], "manual")
            self.assertEqual(store.load_team("a").charges, (10,))
            self.assertNotIn("SECRET", stdout.getvalue() + stderr.getvalue())

    def test_denied_runtime_impersonation_never_initializes_owner_sdk_fallback(self):
        from franchise.sidecar import main
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite"
            store = FranchiseStore(path)
            store.create_team("a", Ledger.from_opening(OpeningBooks(), cap=100,
                roster_reserve=0, max_bonus_years=5, veteran_minimums={"v": (1,)}))
            manual = request()
            manual.update(operation="manual_sign", decision_mode="manual")
            for key in ("personality", "performance", "relationships"):
                del manual[key]
            expensive = {**manual, "request_id": "expensive", "offer": {**manual["offer"], "salaries": [101]}}
            messages = [dict(protocol=1, request_id="hello", operation="hello"), expensive, manual]
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(sys, "argv", ["sidecar", "--database", str(path), "--provider", "vertex", "--impersonate-runtime"]), \
                 patch.object(sys, "stdin", io.StringIO("".join(json.dumps(item) + "\n" for item in messages))), \
                 patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr), \
                 patch("franchise.google_credentials.runtime_credentials", side_effect=RuntimeError("SECRET permission denied")), \
                 patch("franchise.vertex_provider.VertexProvider") as sdk:
                main()
            responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
            self.assertEqual(responses[0]["error"], "ai_disabled")
            self.assertEqual(responses[1]["error"], "state_rejected")
            self.assertEqual(responses[2]["result"]["outcome"], "signed")
            self.assertFalse(sdk.called)
            self.assertEqual(store.load_team("a").charges, (10,))
            self.assertNotIn("SECRET", stdout.getvalue() + stderr.getvalue())
