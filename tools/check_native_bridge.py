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

        capacity_path=Path(directory)/'oversized receipt.sqlite'
        capacity_store=FranchiseStore(capacity_path)
        capacity_store.create_team('a',Ledger.from_opening(OpeningBooks(contracts=(contract,)),cap=100,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
        capacity_store.initialize_cash('a',(CashObligation('contract:v','v',69,9,'x'*70000,
            (('signing_bonus',9),)),),source='synthetic oversized source record')
        unchanged=capacity_path.read_bytes()
        rejection=None
        for attempt in range(2):
            result=subprocess.run([sys.argv[1],sys.executable,str(capacity_path),'--receipt-capacity'],
                text=True,capture_output=True,timeout=20,check=True)
            responses=[json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses)==1
            response=responses[0]
            assert response['error']=='response_too_large' and response['result'] is None
            assert response['request_id']=='release'
            assert len(result.stdout.encode('utf-8'))<=65536
            if rejection is None:rejection=response
            else:assert response==rejection
            assert capacity_path.read_bytes()==unchanged
            current=capacity_store.load_team('a')
            assert current.revision==1 and current.financial_snapshot()['signed_players']==['v']
            assert current.cash_snapshot()['nominal_total']==69 and current.cash_snapshot()['paid_total']==9
        print("Native Windows oversized lifecycle receipt rejection and unchanged restart state verified (synthetic).")

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
        from datetime import date
        from fractions import Fraction
        from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
        from franchise.guarantees import DiscountProfile
        return_path=Path(directory)/'return fixture.sqlite'
        returns=FranchiseStore(return_path)
        return_contract=ActiveContract(Offer('v',(10,20,30),9,(0,20,10)),'synthetic Windows prior agreement')
        returns.create_team('a',Ledger.from_opening(OpeningBooks(contracts=(return_contract,)),cap=200,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
        returns.initialize_cash('a',(CashObligation('contract:v','v',69,9,'synthetic bank',(('signing_bonus',9),)),),
            source='synthetic complete return cash')
        returns.release_preseason_veteran('a','prior-release','v',scope=PreseasonReleaseScope(2026,
            date(2026,6,1),date(2026,9,10),EXCLUDED_LIABILITIES,True,True,0,'synthetic prior removal'),
            discount=DiscountProfile(2026,Fraction(0),'synthetic zero rate'),payment_year_offsets=(0,1,2),
            expected_revision=1,access_check=lambda:None)
        old_id=returns.contract_generations('a')['generations'][0]['generation_id']
        FranchiseStore.migrate_generations(return_path)
        committed=None
        for attempt in range(2):
            result=subprocess.run([sys.argv[1],sys.executable,str(return_path),
                '--return-replay' if attempt else '--return'],text=True,capture_output=True,timeout=20,check=True)
            responses=[json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses)==(2 if attempt else 3) and all(r['error'] is None for r in responses)
            if not attempt:
                assert responses[0]['result']['annual_team_charges_after']==[45,6,6]
                committed=responses[1:]
            else:
                assert responses==committed
            ledger=returns.load_team('a')
            gid=ledger.contract_identity('v').generation_id
            assert gid!=old_id and gid.startswith('contract-gen:')
            assert ledger.charges==(45,6,6) and ledger.revision==3
            assert ledger.generation_cash(old_id).amount==39 and ledger.generation_cash(old_id).paid==9
            assert ledger.generation_cash(gid).amount==18 and ledger.generation_cash(gid).paid==0
            assert responses[-1]['result']==returns.player_context('a','v')
            assert responses[-2]['result']['outcome']=='signed'
            assert responses[-2]['result']['return_scope']['source']=='synthetic Windows return'
        print("Native Windows return preview, agreement, old debt and restart retry verified (synthetic).")
        returned=returns.load_team('a')
        gid=returned.contract_identity('v').generation_id
        returns.record_payment('a','returned-bonus',gid,3,expected_cash_revision=returned.cash_snapshot()['revision'],
            source='synthetic bank',payment_reference='returned bonus receipt',component='signing_bonus')
        amended_reply=None
        for attempt in range(2):
            result=subprocess.run([sys.argv[1],sys.executable,str(return_path),'--returned-restructure'],
                text=True,capture_output=True,timeout=20,check=True)
            responses=[json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses)==2 and all(r['error'] is None for r in responses)
            if amended_reply is None:amended_reply=responses
            else:assert responses==amended_reply
            current=returns.load_team('a')
            assert [str(v) for v in current.charges]==['127/3','22/3','22/3']
            assert current.revision==5 and current.generation_cash(old_id).amount==39
            assert current.generation_cash(old_id).paid==9
            assert current.generation_cash(gid).amount==18 and current.generation_cash(gid).paid==3
            assert responses[0]['result']['generation_id']==gid
            assert responses[1]['result']==returns.player_context('a','v')
        print("Native Windows returned agreement restructure, old debt and restart retry verified (synthetic).")
        amended=returns.load_team('a')
        returns.record_payment('a','converted-bonus',gid,4,expected_cash_revision=amended.cash_snapshot()['revision'],
            source='synthetic bank',payment_reference='converted bonus receipt',component='bonus:restructure:return-conversion')
        returns.create_team('b',Ledger.from_opening(OpeningBooks(),cap=200,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(1,)*3}))
        returns.initialize_cash('b',(),source='synthetic new receiver cash')
        traded_reply=None
        for attempt in range(2):
            result=subprocess.run([sys.argv[1],sys.executable,str(return_path),'--generation-trade'],
                text=True,capture_output=True,timeout=20,check=True)
            responses=[json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses)==2 and all(r['error'] is None for r in responses)
            if traded_reply is None:traded_reply=responses
            else:assert responses==traded_reply
            source,buyer=returns.load_team('a'),returns.load_team('b')
            buyer_id=buyer.contract_identity('v').generation_id
            assert buyer_id!=gid and buyer_id.startswith('contract-gen:')
            assert source.charges==(46,0,0) and buyer.charges==(1,5,5)
            assert source.generation_cash(old_id).amount==39 and source.generation_cash(old_id).paid==9
            assert source.generation_cash(gid).amount==7 and source.generation_cash(gid).paid==7
            assert buyer.generation_cash(buyer_id).amount==11 and buyer.generation_cash(buyer_id).paid==0
            assert source.cash_snapshot()['nominal_total']+buyer.cash_snapshot()['nominal_total']==57
            assert responses[0]['result']['buyer_generation_id']==buyer_id
            assert responses[1]['result']==returns.player_context('b','v')
        print("Native Windows generation assignment, separate receiver agreement, retained debt and restart retry verified (synthetic).")

        compact_path=Path(directory)/'long franchise compact receipt.sqlite'
        compact_store=FranchiseStore(compact_path)
        players=['v']+['player-'+str(i) for i in range(1,53)]
        contracts=tuple(ActiveContract(Offer(player,(1000000,)*3,9000000,(0,1000000,1000000)),
            'synthetic original contract') for player in players)
        compact_store.create_team('a',Ledger.from_opening(OpeningBooks(contracts=contracts),cap=600000000,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={player:(1,)*3 for player in players}))
        compact_store.initialize_cash('a',tuple(CashObligation('contract:'+player,player,12000000,9000000,
            'synthetic original payment',(('signing_bonus',9000000),)) for player in players),source='synthetic complete cash')
        for i in range(1,31):
            compact_store.release_preseason_veteran('a','prior-'+str(i),players[i],
                scope=PreseasonReleaseScope(2026,date(2026,6,1),date(2026,9,10),EXCLUDED_LIABILITIES,
                    True,True,0,'synthetic prior release'),discount=DiscountProfile(2026,Fraction(0),'synthetic zero rate'),
                payment_year_offsets=(0,1,2),expected_revision=i,access_check=lambda:None)
        original=None
        for attempt in range(2):
            result=subprocess.run([sys.argv[1],sys.executable,str(compact_path),'--compact-release'],
                text=True,capture_output=True,timeout=20,check=True)
            responses=[json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses)==1 and responses[0]['error'] is None
            reply=responses[0]
            assert reply['result']['receipt_format']=='target_v1'
            assert len(result.stdout.encode('utf-8'))<65536
            if original is None:original=reply
            else:assert reply==original
            current=compact_store.load_team('a')
            posting=reply['result']['release']
            assert current.revision==32 and current.charges==(429000000,88000000,88000000)
            assert posting['financial']['charges']==[429000000,88000000,88000000]
            assert list(posting['financial']['released_contracts'])==['v']
            assert 'v' not in posting['financial']['signed_players']
            assert posting['cash']['nominal_total']==605000000 and posting['cash']['paid_total']==477000000
            assert posting['cash']['other_obligations']==dict(count=52,nominal_total=594000000,
                paid_total=468000000,unpaid_total=126000000)
            assert len(posting['cash']['obligations'])==1
            assert len(json.dumps(dict(financial=current.financial_snapshot(),cash=current.cash_snapshot())).encode('utf-8'))>65536
        print("Native Windows compact long-franchise receipt, reconciled cash and restart verified (synthetic).")

        from dataclasses import replace
        from franchise.negotiation import Negotiation
        from franchise.promises import PromiseGoal,GoalObservation,PromiseCircumstances
        from franchise.store import StoredLedger
        promise_path=Path(directory)/'promise circumstances.sqlite'
        promises=FranchiseStore(promise_path)
        promises.create_team('a',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'p':(1,)}))
        session=Negotiation(StoredLedger(promises,'a'),player_id='p',personality={},performance={'source':'synthetic'},
            relationships={'trust':0.6},access_check=lambda:None)
        session.respond('deal',Offer('p',(20,),0),lambda _:json.dumps(dict(action='accept',reason='Synthetic role agreement',
            salaries=None,signing_bonus=None)),promise_goals=(PromiseGoal('starts','starts',8,80,'fixture season','synthetic proposal'),))
        observed=(GoalObservation('starts','fixture season',4,'synthetic measured starts','synthetic full window',
            'Source-backed circumstances supplied separately',True),)
        known=PromiseCircumstances('p','a','fixture season','cpu_played',17,12,5,3,
            'synthetic availability report','synthetic full window',True,None)
        unknown=replace(known,available_games=None,coaching_dnp_games=None,complete_window=False,
            unavailable_reason='Synthetic source did not measure eligibility or coaching DNPs')
        promises.record_promise_score('a','progress','deal',observed,window_closed=False,expected_revision=1,
            source='synthetic interim evaluation',circumstances=(unknown,))
        promises.record_promise_score('a','final','deal',observed,window_closed=True,expected_revision=2,
            source='synthetic final evaluation',circumstances=(known,))
        original=None;unchanged=promise_path.read_bytes()
        for attempt in range(2):
            result=subprocess.run([sys.argv[1],sys.executable,str(promise_path),'--promise-context'],
                text=True,capture_output=True,timeout=20,check=True)
            responses=[json.loads(line) for line in result.stdout.splitlines()]
            assert len(responses)==1 and responses[0]['error'] is None
            reply=responses[0]
            if original is None:original=reply
            else:assert reply==original
            context=reply['result']
            assert context==promises.player_context('a','p')
            assert context['financial_revision']==3 and context['relationships']['trust']==0.6
            assert context['promise_history'][0]['circumstances'][0]['available_games'] is None
            assert context['promise_history'][0]['score']['final_achievement_score'] is None
            assert context['promise_history'][1]['circumstances']==[known.to_dict()]
            assert context['promise_history'][1]['score']['final_achievement_score']=='1/2'
            assert promises.load_team('a').charges==(20,) and promise_path.read_bytes()==unchanged
        print("Native Windows sourced promise circumstances, unknown counts, raw score and restart verified (synthetic).")

        if len(sys.argv)>2:
            c_path=Path(directory)/'C host ownership.sqlite'
            c_store=FranchiseStore(c_path)
            c_store.create_team('a',Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
                max_bonus_years=5,veteran_minimums={'v':(1,)}))
            agreement=None;context=None
            for attempt in range(2):
                result=subprocess.run([sys.argv[2],sys.executable,str(c_path)],
                    text=True,capture_output=True,timeout=20,check=True)
                replies=[json.loads(line) for line in result.stdout.splitlines()]
                assert len(replies)==4
                assert replies[0]['error'] is None and replies[0]['result']['ai_enabled'] is True
                if attempt==0:
                    assert replies[1]['error'] is None and replies[1]['result']['room_after']==90
                    agreement=replies[2];context=replies[3]
                else:
                    assert replies[1]['error']=='state_rejected'
                    assert replies[2]==agreement and replies[3]==context
                assert replies[2]['error'] is None and replies[2]['result']['outcome']=='signed'
                assert replies[3]['error'] is None
                current=c_store.load_team('a')
                assert current.charges==(10,) and current.revision==1 and current._players=={'v'}
                assert replies[3]['result']==c_store.player_context('a','v')
            print("Native Windows plain-C host adapter, bounded response retrieval and restart verified (synthetic).")








if __name__ == "__main__":
    main()
