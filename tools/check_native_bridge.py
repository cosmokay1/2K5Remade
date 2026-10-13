"""Execute asset-free Windows C++ pipe client against a synthetic database."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from franchise.books import OpeningBooks
from franchise.cap import Ledger
from franchise.store import FranchiseStore


def main():
    with tempfile.TemporaryDirectory(prefix="bridge fixture ") as directory:
        path = Path(directory) / "state with spaces.sqlite"
        store = FranchiseStore(path)
        store.create_team("a", Ledger.from_opening(OpeningBooks(), cap=100,
            roster_reserve=0, max_bonus_years=5, veteran_minimums={"v": (1,)}))
        agreement = None
        for attempt in range(2):
            command = [sys.argv[1], sys.executable, str(path)]
            if attempt:
                command.append("--replay")
            result = subprocess.run(command,
                                    text=True, capture_output=True, timeout=20, check=True)
            responses = [json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses) == (2 if attempt else 5)
            assert responses[0]["result"]["ai_enabled"] is True
            if not attempt:
                assert all(responses[index]["error"] is None for index in (0, 1, 2, 4))
                assert responses[1]["result"]["room_after"] == 90
                assert responses[2]["result"]["outcome"] == "player_rejected"
                assert responses[3]["error"] == "state_rejected"
                agreement = responses[4]
                assert agreement["result"]["outcome"] == "signed"
                assert agreement["result"]["decision_mode"] == "manual"
                assert agreement["result"]["charges"] == [10]
                assert agreement["result"]["offer"]["guaranteed_salaries"] == [10]
            else:
                assert responses[1] == agreement
        for python, database in ((sys.executable, str(Path(directory) / "missing.sqlite")),
                                 (str(Path(directory) / "missing-python.exe"), str(path))):
            failed = subprocess.run([sys.argv[1], python, database],
                                    text=True, capture_output=True, timeout=20)
            assert failed.returncode != 0, "Native client must fail closed on launch/service failure"
        # Keep a process handle open before triggering parent termination, so PID
        # reuse cannot turn this ownership check into a false positive.
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        parent = subprocess.Popen([sys.argv[1], sys.executable, str(path), "--abrupt"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        child = None
        try:
            child_pid = int(parent.stdout.readline())
            child = kernel.OpenProcess(0x00100000, False, child_pid)  # SYNCHRONIZE
            assert child, "Could not observe sidecar process"
            parent.stdin.write("exit\n")
            parent.stdin.flush()
            assert parent.wait(timeout=5) == 0
            assert kernel.WaitForSingleObject(child, 5000) == 0, "Sidecar survived abrupt native parent exit"
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=5)
            for stream in (parent.stdin, parent.stdout, parent.stderr):
                stream.close()
            if child:
                kernel.CloseHandle(child)
        assert store.load_team("a").revision == 1
        assert store.load_team("a").charges == (10,)
        assert store.load_team("a").contract_terms("v")["guaranteed_salaries"] == [10]
        assert len(store.negotiation_history("a", "v")) == 2
        print("Native Windows pipe handshake, cap rejection, manual signing and restart verified (synthetic).")


if __name__ == "__main__":
    main()
