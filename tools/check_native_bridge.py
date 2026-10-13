"""Execute asset-free Windows C++ pipe client against a synthetic database."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from franchise.books import OpeningBooks,ActiveContract
from franchise.cap import Ledger,Offer
from franchise.cash import CashObligation
from franchise.store import FranchiseStore


def main():
    with tempfile.TemporaryDirectory(prefix="bridge fixture ") as directory:
        path = Path(directory) / "state with spaces.sqlite"
        store = FranchiseStore(path)
        store.create_team("a", Ledger.from_opening(OpeningBooks(), cap=100,
            roster_reserve=0, max_bonus_years=5, veteran_minimums={"v": (1,)}))
        agreement = None
        player_context = None
        for attempt in range(2):
            command = [sys.argv[1], sys.executable, str(path)]
            if attempt:
                command.append("--replay")
            result = subprocess.run(command,
                                    text=True, capture_output=True, timeout=20, check=True)
            responses = [json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses) == (3 if attempt else 6)
            assert responses[0]["result"]["ai_enabled"] is True
            if not attempt:
                assert all(responses[index]["error"] is None for index in (0, 1, 2, 4, 5))
                assert responses[1]["result"]["room_after"] == 90
                assert responses[2]["result"]["outcome"] == "player_rejected"
                assert responses[3]["error"] == "state_rejected"
                agreement = responses[4]
                assert agreement["result"]["outcome"] == "signed"
                assert agreement["result"]["decision_mode"] == "manual"
                assert agreement["result"]["charges"] == [10]
                assert agreement["result"]["offer"]["guaranteed_salaries"] == [10]
                player_context = responses[5]["result"]
                assert player_context == store.player_context("a", "v")
                assert player_context["initialized"] is True
                assert player_context["financial_revision"] == 1
            else:
                assert responses[1] == agreement
                assert responses[2]["error"] is None
                assert responses[2]["result"] == player_context
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
        release_path=Path(directory)/'release fixture.sqlite'
        releases=FranchiseStore(release_path)
        contract=ActiveContract(Offer('v',(10,20,30),9,(0,20,10)),'synthetic Windows original')
        releases.create_team('a',Ledger.from_opening(OpeningBooks(contracts=(contract,)),cap=30,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
        releases.initialize_cash('a',(CashObligation('contract:v','v',69,9,'synthetic bank',(('signing_bonus',9),)),),
                                source='synthetic payment coverage')
        original=None
        for attempt in range(2):
            result=subprocess.run([sys.argv[1],sys.executable,str(release_path),'--release'],
                                  text=True,capture_output=True,timeout=20,check=True)
            responses=[json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses)==2 and all(reply['error'] is None for reply in responses)
            if original is None: original=responses
            else: assert responses==original
            posting=responses[0]['result']['release']
            current=FranchiseStore(release_path).load_team('a')
            assert posting=={'financial':current.financial_snapshot(),'cash':current.cash_snapshot()}
            assert current.charges==(39,0,0) and current.room==-9 and current.revision==2
            assert current.cash_snapshot()['unpaid_total']==30
            assert current.financial_snapshot()['signed_players']==[]
            assert responses[1]['result']==releases.player_context('a','v')
        print("Native Windows pipe handshake, cap rejection, manual signing, player context and restart verified (synthetic).")
        print("Native Windows supported release, retained debt/cash and restart retry verified (synthetic).")
        trade_path=Path(directory)/'paired assignment.sqlite'
        trades=FranchiseStore(trade_path)
        for team in ('a','b'):
            trades.create_team(team,Ledger.from_opening(OpeningBooks(contracts=(contract,)) if team=='a' else OpeningBooks(),
                cap=100,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
            records=(CashObligation('contract:v','v',69,9,'synthetic paidbonus',(('signing_bonus',9),)),) if team=='a' else ()
            trades.initialize_cash(team,records,source='synthetic assignment cash')
        original=None
        for attempt in range(2):
            result=subprocess.run([sys.argv[1],sys.executable,str(trade_path),'--trade'],
                                  text=True,capture_output=True,timeout=20,check=True)
            responses=[json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses)==2 and all(reply['error'] is None for reply in responses)
            if original is None: original=responses
            else: assert responses==original
            posting=responses[0]['result']['trade']
            for team in ('a','b'):
                current=FranchiseStore(trade_path).load_team(team)
                assert posting[team]=={'financial':current.financial_snapshot(),'cash':current.cash_snapshot()}
                assert current.revision==2
            seller,buyer=trades.load_team('a'),trades.load_team('b')
            assert seller.charges==(9,0,0) and buyer.charges==(10,20,30)
            assert seller.financial_snapshot()['signed_players']==[] and buyer.financial_snapshot()['signed_players']==['v']
            assert seller.cash_snapshot()['nominal_total']+buyer.cash_snapshot()['nominal_total']==69
            assert buyer.contract_terms('v')['guaranteed_salaries']==[0,20,10]
            assert responses[1]['result']==trades.player_context('b','v')
        print("Native Windows paired assignment, inherited guarantees, conserved cash and restart retry verified (synthetic).")

        amendment_path=Path(directory)/'amendment fixture.sqlite'
        amendments=FranchiseStore(amendment_path)
        contract=ActiveContract(Offer('v',(10,10,10,20,30,40,50),10,(10,10,10,20,0,0,0)),
            'synthetic Windows original',elapsed_years=2)
        amendments.create_team('a',Ledger.from_opening(OpeningBooks(contracts=(contract,)),cap=200,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(2,)*5}))
        amendments.initialize_cash('a',(CashObligation('contract:v','v',180,30,'synthetic settled history',
            (('signing_bonus',10),('base:0',10),('base:1',10))),),source='synthetic cash coverage')
        original=None
        for attempt in range(2):
            result=subprocess.run([sys.argv[1],sys.executable,str(amendment_path),'--restructure'],
                text=True,capture_output=True,timeout=20,check=True)
            responses=[json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses)==2 and all(reply['error'] is None for reply in responses)
            if original is None:original=responses
            else:assert responses==original
            current=FranchiseStore(amendment_path).load_team('a')
            assert responses[0]['result']['restructure']=={'financial':current.financial_snapshot(),'cash':current.cash_snapshot()}
            assert current.revision==2 and current.cash_snapshot()['revision']==1
            assert [str(value) for value in current.charges]==['28/5','118/5','168/5','208/5','258/5']
            assert current.cash_snapshot()['nominal_total']==180 and current.cash_snapshot()['paid_total']==30
            assert current.guarantee_cash('v')['unpaid_signing_bonus']==8
            assert responses[1]['result']==amendments.player_context('a','v')
        print("Native Windows restructure, original/new bonus schedules, unpaid cash and restart retry verified (synthetic).")


if __name__ == "__main__":
    main()
