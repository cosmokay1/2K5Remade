"""Bounded JSON-lines process transport; stdout is protocol data only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
from threading import Event, Lock
from franchise.bridge import Bridge
from franchise.control import AccessDisabled, GoogleControl
from franchise.store import FranchiseStore

MAX_LINE = 65536


def serve(bridge, reader, writer):
    disconnected, busy = Event(), Event()
    output_lock = Lock()
    original_check = bridge.access_check
    original_connection = bridge.connection_check
    def connection_check():
        if disconnected.is_set():
            raise AccessDisabled("Client disconnected")
        original_connection()
    bridge.connection_check = connection_check
    def check():
        if disconnected.is_set():
            raise AccessDisabled("Client disconnected")
        original_check()
        if disconnected.is_set():
            raise AccessDisabled("Client disconnected")
    bridge.access_check = check
    def emit(response):
        with output_lock:
            if disconnected.is_set():
                return
            try:
                writer.write(json.dumps(response, allow_nan=False) + "\n")
                writer.flush()
            except (BrokenPipeError, OSError):
                disconnected.set()
    def process(request):
        try:
            emit(bridge.handle(request))
        finally:
            busy.clear()
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            while not disconnected.is_set():
                line = reader.readline(MAX_LINE + 1)
                if not line:
                    disconnected.set()
                    break
                if len(line) > MAX_LINE:
                    emit(Bridge._reply(None, error="request_too_large"))
                    disconnected.set()  # Never interpret a truncated frame tail.
                    break
                try:
                    request = json.loads(line)
                except (ValueError, TypeError):
                    emit(Bridge._reply(None, error="invalid_request"))
                    continue
                request_id = request.get("request_id") if type(request) is dict else None
                if type(request) is dict and request.get("operation") == "negotiate":
                    if busy.is_set():
                        emit(Bridge._reply(request_id, error="busy"))
                    else:
                        busy.set()
                        executor.submit(process, request)
                else:
                    emit(bridge.handle(request))
    finally:
        disconnected.set()
        bridge.access_check = original_check
        bridge.connection_check = original_connection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--provider", required=True, choices=("vertex", "offline-fixture"))
    parser.add_argument("--impersonate-runtime", action="store_true",
                        help="Use the configured keyless runtime service account; requires authorized source ADC")
    parser.add_argument('--ai-budget-database', help='Separate durable AI usage database')
    parser.add_argument('--ai-budget-scope', help='Explicit persistent franchise/season budget identity')
    parser.add_argument('--ai-request-limit', type=int, help='Immutable maximum SDK attempts for this scope')
    args = parser.parse_args()
    if args.impersonate_runtime and args.provider != "vertex":
        parser.error("Runtime impersonation applies only to Vertex mode")
    if not Path(args.database).is_file():
        parser.error("An existing verified franchise database is required")
    if args.provider == "offline-fixture":
        def provider(_):
            return json.dumps(dict(action="reject", reason="Offline transport fixture",
                                   salaries=None, signing_bonus=None))
        access_check = lambda: None  # Explicit synthetic test mode, no live inference.
    else:
        try:
            from franchise.runtime_budget import runtime_request_budget
            budget=runtime_request_budget(args.database,args.ai_budget_database,args.ai_budget_scope,args.ai_request_limit)
            from franchise.vertex_provider import VertexProvider
            config = json.loads((Path(__file__).resolve().parents[1] / "config/google.json").read_text())
            credentials = None
            control_credentials = None
            if args.impersonate_runtime:
                from franchise.google_credentials import runtime_credentials
                credentials = runtime_credentials(config["project"], config["runtime_service_account"])
                control_credentials = runtime_credentials(config["project"], config["runtime_service_account"])
            provider = VertexProvider(project=config["project"], location=config["location"], model=config["model"], credentials=credentials,request_budget=budget)
            access_check = GoogleControl(project=config["project"], bucket=config["control_bucket"], object_name=config["control_object"], credentials=control_credentials)
        except Exception:
            # Financial/manual operations stay authoritative. Never substitute
            # scripted player decisions or owner credentials after AI failure.
            def unavailable(*_):
                raise AccessDisabled("AI initialization unavailable")
            provider = access_check = unavailable
            print("AI unavailable: check persistent budget configuration, runtime authentication and optional dependencies.", file=sys.stderr)
    serve(Bridge(FranchiseStore(args.database), provider=provider, access_check=access_check), sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
