"""Bounded JSON-lines process transport; stdout is protocol data only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys
from threading import Event, Lock
from franchise.bridge import Bridge
from franchise.control import AccessDisabled, GoogleControl
from franchise.store import FranchiseStore

MAX_LINE = 65536


def read_guest_save(path):
    """Bound one regular-file read; paths are selected at service startup only."""
    import stat
    from tools.inspect_franchise_save import SIZE
    before=path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError('Pinned guest save must be a regular file')
    with path.open('rb') as source:
        opened=os.fstat(source.fileno())
        payload=source.read(SIZE+1)
        after=os.fstat(source.fileno())
    def identity(value):
        return value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns
    final=path.stat()
    # Windows stat may expose creation time while fstat exposes change time.
    # Compare ctime only within each API, retaining both mutation checks.
    if (len(payload)>SIZE or identity(before)!=identity(opened)
            or identity(opened)!=identity(after) or identity(after)!=identity(final)
            or before.st_ctime_ns!=final.st_ctime_ns
            or opened.st_ctime_ns!=after.st_ctime_ns):
        raise ValueError('Pinned guest save changed during read or exceeds the supported layout')
    return payload


def serve(bridge, reader, writer):
    disconnected, busy = Event(), Event()
    output_lock = Lock()
    original_check = bridge.access_check
    original_connection = bridge.connection_check
    def connection_check():
        if disconnected.is_set():
            raise AccessDisabled("Client disconnected")
        if original_connection() is False:
            raise AccessDisabled("Client connection check denied")
    bridge.connection_check = connection_check
    def check():
        if disconnected.is_set():
            raise AccessDisabled("Client disconnected")
        if original_check() is False:
            raise AccessDisabled("AI control denied")
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
                if type(request) is dict and request.get("operation") in ("negotiate", "negotiate_proposal", "guest_signing_prepare", "guest_signing_confirm"):
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
    parser.add_argument('--ai-token-limit', type=int, help='Immutable cumulative reserved input plus generated token ceiling')
    parser.add_argument('--guest-save', default=os.environ.get('NFL2K5_FRANCHISE_GUEST_SAVE'),
                        help='Pinned original saved payload for read-only signing reconciliation')
    parser.add_argument('--guest-bindings', default=os.environ.get('NFL2K5_FRANCHISE_GUEST_BINDINGS'),
                        help='Existing pinned player bindings; requires --guest-save')
    journal_mode=os.environ.get('NFL2K5_FRANCHISE_GUEST_SIGNING','0')
    if journal_mode not in ('0','1'):
        parser.error('NFL2K5_FRANCHISE_GUEST_SIGNING must be 0 or 1')
    parser.add_argument('--guest-signing', action='store_true',default=journal_mode=='1',
                        help='Experimental saved-signing journal coordination; requires pinned save/bindings, never writes game files')
    args = parser.parse_args()
    if args.impersonate_runtime and args.provider != "vertex":
        parser.error("Runtime impersonation applies only to Vertex mode")
    if not Path(args.database).is_file():
        parser.error("An existing verified franchise database is required")
    guest_snapshot = None
    guest_signing_reader = None
    if args.guest_signing and (not args.guest_save or not args.guest_bindings):
        parser.error('Saved-signing coordination requires pinned guest save and bindings')
    if args.guest_save is not None or args.guest_bindings is not None:
        if not args.guest_save or not args.guest_bindings:
            parser.error('Both pinned guest save and bindings are required')
        try:
            from tools.franchise_snapshot_bindings import resolve_bindings
            guest_path=Path(args.guest_save).resolve()
            guest_snapshot = (json.loads(Path(args.guest_bindings).read_text()), read_guest_save(guest_path))
            resolve_bindings(*guest_snapshot)
            if args.guest_signing:
                guest_signing_reader=lambda:read_guest_save(guest_path)
        except (OSError, ValueError):
            parser.error('Pinned guest snapshot could not be validated')
    sdk_provider = None
    if args.provider == "offline-fixture":
        def provider(_):
            return json.dumps(dict(action="reject", reason="Offline transport fixture",
                                   salaries=None, signing_bonus=None))
        access_check = lambda: None  # Explicit synthetic test mode, no live inference.
    else:
        try:
            from franchise.runtime_budget import runtime_request_budget
            budget=runtime_request_budget(args.database,args.ai_budget_database,args.ai_budget_scope,args.ai_request_limit,args.ai_token_limit)
            from franchise.vertex_provider import VertexProvider
            config = json.loads((Path(__file__).resolve().parents[1] / "config/google.json").read_text())
            credentials = None
            control_credentials = None
            if args.impersonate_runtime:
                from franchise.google_credentials import runtime_credentials
                credentials = runtime_credentials(config["project"], config["runtime_service_account"])
                control_credentials = runtime_credentials(config["project"], config["runtime_service_account"])
            provider = VertexProvider(project=config["project"], location=config["location"], model=config["model"], credentials=credentials,request_budget=budget,max_input_tokens=16384)
            sdk_provider = provider
            access_check = GoogleControl(project=config["project"], bucket=config["control_bucket"], object_name=config["control_object"], credentials=control_credentials)
        except Exception:
            # Financial/manual operations stay authoritative. Never substitute
            # scripted player decisions or owner credentials after AI failure.
            def unavailable(*_):
                raise AccessDisabled("AI initialization unavailable")
            provider = access_check = unavailable
            print("AI unavailable: check persistent budget configuration, runtime authentication and optional dependencies.", file=sys.stderr)
    try:
        serve(Bridge(FranchiseStore(args.database), provider=provider, access_check=access_check,
                     guest_snapshot=guest_snapshot, guest_signing_reader=guest_signing_reader), sys.stdin, sys.stdout)
    finally:
        if sdk_provider is not None:
            try:
                sdk_provider.close()
            except Exception:
                print('AI client cleanup unavailable.', file=sys.stderr)


if __name__ == "__main__":
    main()
