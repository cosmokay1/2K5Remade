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

        from franchise.salary_rules import VeteranMinimumProfile
        calendar_path=Path(directory)/'Advanced calendar.sqlite'
        calendar=FranchiseStore(calendar_path)
        terms={}
        for team,term in (('a',3),('b',1)):
            contract=ActiveContract(Offer(team,(2000000,)*term,3000000),'synthetic calendar contract')
            profile=VeteranMinimumProfile(2026,((team,(7,)*term,('active_inactive',)*term),))
            calendar.create_team(team,Ledger.from_opening(OpeningBooks(contracts=(contract,)),
                cap=10000000,roster_reserve=0,max_bonus_years=5,veteran_minimums=profile.floors(),veteran_minimum_profile=profile))
            calendar.initialize_cash(team,(CashObligation('contract:'+team,team,contract.nominal_cash,5000000,
                'synthetic settled payroll',(('signing_bonus',3000000),('base:0',2000000))),),source='synthetic cash coverage')
            terms[team]=dict(expected_revision=2,next_cap=9000000,next_cap_source='synthetic next cap',
                roster_reserve=0,reserve_source='synthetic reserve',
                next_minimum_profile=VeteranMinimumProfile(2027,((team,(7,7,7),('active_inactive',)*3),)).to_dict(),
                expired_generation_ids=[calendar.load_team(team).contract_identity(team).generation_id] if team=='b' else [],
                exclusions=sorted(FranchiseStore.YEAR_TRANSITION_EXCLUSIONS),source='synthetic eligible closing')
        calendar.anchor_calendar(request_id='initial',league_year=2026,source='synthetic year',expected_revisions={'a':1,'b':1})
        calendar.migrate_generations(calendar_path)
        calendar.advance_league_year(request_id='next',from_year=2026,to_year=2027,source='synthetic transition',teams=terms)
        for team in ('a','b'):
            calendar.bind_actor(team,team,{'money':0.8},{'trust':0.6},access_check=lambda:None)
        unchanged=calendar_path.read_bytes();previous=None
        for attempt in range(2):
            result=subprocess.run([sys.argv[1],sys.executable,str(calendar_path),'--calendar-context'],
                text=True,capture_output=True,timeout=20,check=True)
            replies=[json.loads(line) for line in result.stdout.splitlines()]
            assert len(replies)==4 and all(reply['error'] is None for reply in replies)
            if previous is not None:assert replies==previous
            previous=replies
            active,expired=(reply['result']['calendar_accounting'] for reply in replies[:2])
            assert active['status']=='active' and active['current_contract']['elapsed_years']==1
            assert active['annual_charges']==[3000000,3000000] and active['ownership_current'] is True
            assert expired['status']=='expired' and expired['current_contract'] is None and expired['ownership_current'] is False
            for team,reply in zip(('a','b'),replies[2:]):
                assert reply['result']==calendar.player_context(team,team,context_format='calendar_v1')
                assert reply['result']['initialized'] is True
                assert reply['result']['personality']=={'money':0.8}
                assert reply['result']['contract_accounting'] is None
            assert calendar_path.read_bytes()==unchanged
        print("Native Windows advanced calendar contract/player contexts, personality, settled expiry and restart verified (synthetic).")

        from datetime import date
        from fractions import Fraction
        from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
        from franchise.guarantees import DiscountProfile
        released_id=calendar.load_team('a').contract_identity('a').generation_id
        previous=None
        for attempt in range(2):
            result=subprocess.run([sys.argv[1],sys.executable,str(calendar_path),'--calendar-release'],
                text=True,capture_output=True,timeout=20,check=True)
            replies=[json.loads(line) for line in result.stdout.splitlines()]
            assert len(replies)==5 and all(reply['error'] is None for reply in replies)
            if previous is not None:assert replies==previous
            previous=replies
            receipt=calendar.release_calendar_preseason_veteran('a','calendar-release','a',generation_id=released_id,
                scope=PreseasonReleaseScope(2027,date(2027,7,1),date(2027,9,10),EXCLUDED_LIABILITIES,
                    True,True,0,'synthetic Windows calendar release'),
                discount=DiscountProfile(2027,Fraction(0),'synthetic discount'),payment_year_offsets=(0,1),
                expected_revision=3,access_check=lambda:None)
            assert replies[0]['result']==dict(decision_mode='manual',player_id='a',release=receipt)
            replies=replies[1:]
            released=replies[0]['result']
            assert released==calendar.calendar_contract_context('a',released_id,context_format='calendar_v2')
            assert released['economic_archive']['contract']['elapsed_years']==0
            assert released['release_calendar']['elapsed_years']==1
            assert released['calendar_accounting']['status']=='released'
            assert released['calendar_accounting']['ownership_current'] is False
            assert released['economic_archive']['cash_obligation']['amount']==5000000
            assert replies[1]['result']['release_calendar'] is None
            for team,reply in zip(('a','b'),replies[2:]):
                assert reply['result']==calendar.player_context(team,team,context_format='calendar_v2')
                assert reply['result']['personality']=={'money':0.8}
            if attempt:assert calendar_path.read_bytes()==unchanged
            else:unchanged=calendar_path.read_bytes()
        print("Native Windows calendar-release transaction, archives and player contexts survive restart (synthetic).")

        # Reuse complete economic histories, replacing only the release boundary
        # with an actual native client call. The test assertions still check the
        # subsequent payment/rollover/reopen and original assignment/amendment.
        from dataclasses import asdict
        from tests import test_calendar_release_history
        from franchise.receipts import compact_lifecycle_result
        for method in ('test_restructured_bonus_and_earned_base_survive_release_restart_and_second_roll',
                       'test_assigned_base_guarantees_remain_separate_from_seller_bonus_debt'):
            fixture=test_calendar_release_history.CalendarReleaseHistoryTests(method)
            fixture.setUp()
            original_release=fixture.store.release_calendar_preseason_veteran
            def native_release(team,request_id,player,**inputs):
                scope=asdict(inputs['scope'])
                scope.update(exclusions=sorted(scope['exclusions']),removed_on=scope['removed_on'].isoformat(),
                    first_regular_season_game=scope['first_regular_season_game'].isoformat())
                assert inputs['discount'].annual_rate==0
                request=dict(protocol=1,request_id=request_id,operation='manual_release',team_id=team,
                    player_id=player,expected_revision=inputs['expected_revision'],timeout_ms=5000,
                    decision_mode='manual',calendar_format='calendar_v1',generation_id=inputs['generation_id'],
                    scope=scope,discount=dict(league_year=inputs['discount'].league_year,annual_rate=0,
                        rate_source=inputs['discount'].rate_source),payment_year_offsets=list(inputs['payment_year_offsets']))
                fixture.store.bind_actor(team,player,{'money':0.8},{'trust':0.6},access_check=lambda:None)
                requests=[request,{**request,'receipt_format':'target_v1'},
                    dict(protocol=1,request_id='history-contract',operation='contract_context',team_id=team,
                        generation_id=inputs['generation_id'],timeout_ms=5000,context_format='calendar_v2'),
                    dict(protocol=1,request_id='history-player',operation='player_context',team_id=team,
                        player_id=player,timeout_ms=5000,context_format='calendar_v2')]
                payload=''.join(json.dumps(item,separators=(',',':'))+'\n' for item in requests)
                previous=None
                for attempt in range(2):
                    result=subprocess.run([sys.argv[1],sys.executable,str(fixture.path),'--calendar-history'],
                        input=payload,text=True,capture_output=True,timeout=30,check=True)
                    replies=[json.loads(line) for line in result.stdout.splitlines()]
                    assert len(replies)==4 and all(reply['error'] is None for reply in replies)
                    receipt=original_release(team,request_id,player,**inputs)
                    expected=dict(decision_mode='manual',player_id=player,release=receipt)
                    assert replies[0]['result']==expected
                    assert replies[1]['result']==compact_lifecycle_result(expected,'manual_release')
                    assert replies[2]['result']==fixture.store.calendar_contract_context(team,inputs['generation_id'],context_format='calendar_v2')
                    assert replies[3]['result']==fixture.store.player_context(team,player,context_format='calendar_v2')
                    assert replies[3]['result']['personality']=={'money':0.8}
                    if attempt:
                        assert replies==previous and fixture.path.read_bytes()==unchanged
                    else:unchanged=fixture.path.read_bytes()
                    previous=replies
                return receipt
            fixture.store.release_calendar_preseason_veteran=native_release
            try:getattr(fixture,method)()
            finally:fixture.doCleanups()
        print("Native Windows layered/assigned calendar releases, full/compact receipts, personality and next rollover verified (synthetic).")

        from tests import test_calendar_trade_store
        trade_fixture=test_calendar_trade_store.CalendarTradeStoreTests()
        trade_fixture.setUp()
        try:
            request=trade_fixture.bridge_request();request.update(request_id='assignment',timeout_ms=5000)
            payload=''.join(json.dumps(item,separators=(',',':'))+'\n' for item in (request,{**request,'receipt_format':'target_v1'}))
            previous=None
            for attempt in range(2):
                result=subprocess.run([sys.argv[1],sys.executable,str(trade_fixture.path),'--calendar-history'],
                    input=payload,text=True,capture_output=True,timeout=30,check=True)
                replies=[json.loads(line) for line in result.stdout.splitlines()]
                assert len(replies)==2 and all(reply['error'] is None for reply in replies)
                receipt=trade_fixture.trade()
                expected=dict(decision_mode='manual',player_id='v',seller='a',buyer='b',trade=receipt['participants'],
                    seller_generation_id=receipt['seller_generation_id'],buyer_generation_id=receipt['buyer_generation_id'],
                    buyer_previous_generation_id=receipt['buyer_previous_generation_id'],calendar_format='calendar_v1',
                    format=2,league_year=2027)
                assert replies[0]['result']==expected
                assert replies[1]['result']==compact_lifecycle_result(expected,'manual_trade')
                if attempt:assert replies==previous and trade_fixture.path.read_bytes()==unchanged
                else:unchanged=trade_fixture.path.read_bytes()
                previous=replies
            for year in (2027,2028):
                if year==2028:
                    ledger=trade_fixture.store.load_team('b')
                    trade_fixture.store.record_payment('b','native-history-pay',receipt['buyer_generation_id'],2000000,
                        expected_cash_revision=ledger.cash_snapshot()['revision'],source='synthetic earned salary',
                        payment_reference='native-buyer-base-2027',component='base:0')
                    trade_fixture.roll(2027)
                requests=[]
                for team in ('a','b'):
                    generation=trade_fixture.inputs['seller_generation_id'] if team=='a' else receipt['buyer_generation_id']
                    requests.extend([dict(protocol=1,request_id=team+'-contract',operation='contract_context',team_id=team,
                        generation_id=generation,context_format='calendar_v3',timeout_ms=5000),
                        dict(protocol=1,request_id=team+'-player',operation='player_context',team_id=team,
                            player_id='v',context_format='calendar_v3',timeout_ms=5000)])
                payload=''.join(json.dumps(request,separators=(',',':'))+'\n' for request in requests)
                unchanged=trade_fixture.path.read_bytes();previous=None
                for attempt in range(2):
                    result=subprocess.run([sys.argv[1],sys.executable,str(trade_fixture.path),'--calendar-history'],
                        input=payload,text=True,capture_output=True,timeout=30,check=True)
                    replies=[json.loads(line) for line in result.stdout.splitlines()]
                    assert len(replies)==4 and all(reply['error'] is None for reply in replies)
                    for request,reply in zip(requests,replies):
                        expected=(trade_fixture.store.calendar_contract_context(request['team_id'],request['generation_id'],context_format='calendar_v3')
                            if request['operation']=='contract_context' else trade_fixture.store.player_context(request['team_id'],'v',context_format='calendar_v3'))
                        assert reply['result']==expected
                    if attempt:assert replies==previous
                    previous=replies
                    assert trade_fixture.path.read_bytes()==unchanged
        finally:trade_fixture.doCleanups()
        print("Native Windows calendar trade transaction, full/compact receipts, v3 inspection and rollover restart verified (synthetic).")

        from dataclasses import asdict
        from tests import test_calendar_restructure_store
        amendment_fixture=test_calendar_restructure_store.CalendarRestructureStoreTests()
        amendment_fixture.setUp()
        try:
            scope=asdict(amendment_fixture.inputs['scope'])
            for field in ('amended_on','first_regular_season_game'):
                scope[field]=getattr(amendment_fixture.inputs['scope'],field).isoformat()
            scope['exclusions']=sorted(scope['exclusions'])
            request=dict(protocol=1,request_id='convert-2027',operation='manual_restructure',team_id='a',player_id='v',
                decision_mode='manual',calendar_format='calendar_v1',generation_id=amendment_fixture.gid,
                scope=scope,converted_base=amendment_fixture.inputs['converted_base'],
                expected_revision=amendment_fixture.inputs['expected_revision'],timeout_ms=5000)
            mutation_requests=[request,{**request,'receipt_format':'target_v1'}]
            contexts=[dict(protocol=1,request_id='amended-contract',operation='contract_context',team_id='a',
                generation_id=amendment_fixture.gid,context_format='calendar_v3',timeout_ms=5000),
                dict(protocol=1,request_id='amended-player',operation='player_context',team_id='a',player_id='v',
                    context_format='calendar_v3',timeout_ms=5000)]
            previous_mutations=None
            for year in (2027,2028):
                if year==2028:
                    amendment_fixture.fixture.pay('a','bonus:calendar-restructure:convert-2027',100000)
                    amendment_fixture.fixture.pay('a','base:1',1900000)
                    amendment_fixture.fixture.roll(('a',),2027)
                previous=None
                payload=''.join(json.dumps(item,separators=(',',':'))+'\n' for item in mutation_requests+contexts)
                for attempt in range(2):
                    result=subprocess.run([sys.argv[1],sys.executable,str(amendment_fixture.path),'--calendar-history'],
                        input=payload,text=True,capture_output=True,timeout=30,check=True)
                    replies=[json.loads(line) for line in result.stdout.splitlines()]
                    assert len(replies)==4 and all(reply['error'] is None for reply in replies)
                    receipt=amendment_fixture.amend()
                    expected=dict(decision_mode='manual',team_id='a',player_id='v',generation_id=amendment_fixture.gid,restructure=receipt)
                    assert replies[0]['result']==expected
                    assert replies[1]['result']==compact_lifecycle_result(expected,'manual_restructure')
                    assert replies[2]['result']==amendment_fixture.store.calendar_contract_context('a',amendment_fixture.gid,context_format='calendar_v3')
                    assert replies[3]['result']==amendment_fixture.store.player_context('a','v',context_format='calendar_v3')
                    if previous_mutations is not None:assert replies[:2]==previous_mutations
                    if attempt:assert replies==previous and amendment_fixture.path.read_bytes()==unchanged
                    else:unchanged=amendment_fixture.path.read_bytes()
                    previous=replies;previous_mutations=replies[:2]
                ledger=FranchiseStore(amendment_fixture.path).load_team('a')
                assert ledger.active_contract('v').elapsed_years==year-2026
                assert ledger.charges==((2950000,3050000) if year==2027 else (3050000,))
                assert ledger.generation_accounting(amendment_fixture.gid).original_contract.elapsed_years==0
        finally:amendment_fixture.doCleanups()
        print("Native Windows calendar amendment full/compact receipts, current contexts and later-roll restart verified (synthetic).")

        from tests import test_layered_restructure_bridge
        layered_fixture=test_layered_restructure_bridge.LayeredRestructureBridgeTests()
        layered_fixture.setUp()
        try:
            request=layered_fixture.request
            requests=[request,{**request,'receipt_format':'target_v1'}]
            payload=''.join(json.dumps(item,separators=(',',':'))+'\n' for item in requests)
            historical=None
            for phase in ('commit','expired'):
                if phase=='expired':layered_fixture.fixture.expire()
                previous=None
                for attempt in range(2):
                    result=subprocess.run([sys.argv[1],sys.executable,str(layered_fixture.fixture.path),'--calendar-history'],
                        input=payload,text=True,capture_output=True,timeout=30,check=True)
                    replies=[json.loads(line) for line in result.stdout.splitlines()]
                    assert len(replies)==2 and all(reply['error'] is None for reply in replies)
                    expected=[layered_fixture.bridge.handle(item) for item in requests]
                    assert replies==expected
                    assert replies[0]['result']['restructure']['format']==3
                    history=replies[0]['result']['restructure']['amendment_history']
                    assert len(history['prior_restructures'])==1
                    assert history==replies[1]['result']['restructure']['amendment_history']
                    if attempt:assert replies==previous and layered_fixture.fixture.path.read_bytes()==unchanged
                    else:unchanged=layered_fixture.fixture.path.read_bytes()
                    if historical is not None:assert replies==historical
                    previous=replies
                historical=previous
            ledger=FranchiseStore(layered_fixture.fixture.path).load_team('a')
            agreement=ledger.generation_accounting(layered_fixture.fixture.gid)
            assert len(agreement.prior_restructures)==1 and len(agreement.contract.bonus_layers)==2
            assert ledger.generation_calendar_view(layered_fixture.fixture.gid).authoritative_expired
            assert ledger.cash_snapshot()['unpaid_total']==0
        finally:layered_fixture.doCleanups()
        print("Native Windows repeated calendar amendment full/compact history, payroll, expiry and restart verified (synthetic).")

        from tests import test_layered_release_bridge
        release_fixture=test_layered_release_bridge.LayeredReleaseBridgeTests()
        release_fixture.setUp()
        try:
            requests=[release_fixture.request,{**release_fixture.request,'receipt_format':'target_v1'}]
            payload=''.join(json.dumps(item,separators=(',',':'))+'\n' for item in requests)
            historical=None
            for phase in ('release','closed_year','paid'):
                if phase=='closed_year':release_fixture.fixture.next_year()
                if phase=='paid':
                    for component,amount in (('bonus:calendar-layered-restructure:second-2028',200000),('base:2',1800000)):
                        ledger=release_fixture.fixture.store.load_team('a')
                        release_fixture.fixture.store.record_payment('a','native-release-'+component,'contract:v',amount,
                            expected_cash_revision=ledger.cash_snapshot()['revision'],source='synthetic retained payroll',
                            payment_reference='native-retained-'+component,component=component)
                previous=None
                for attempt in range(2):
                    result=subprocess.run([sys.argv[1],sys.executable,str(release_fixture.fixture.path),'--calendar-history'],
                        input=payload,text=True,capture_output=True,timeout=30,check=True)
                    replies=[json.loads(line) for line in result.stdout.splitlines()]
                    assert len(replies)==2 and all(reply['error'] is None for reply in replies)
                    assert replies==[release_fixture.bridge.handle(item) for item in requests]
                    receipt=replies[0]['result']['release']
                    assert receipt['format']==3 and receipt['cash']['unpaid_total']==2000000
                    assert receipt['amendment_history']==replies[1]['result']['release']['amendment_history']
                    if attempt:assert replies==previous and release_fixture.fixture.path.read_bytes()==unchanged
                    else:unchanged=release_fixture.fixture.path.read_bytes()
                    if historical is not None:assert replies==historical
                    previous=replies
                historical=previous
            ledger=FranchiseStore(release_fixture.fixture.path).load_team('a')
            agreement=ledger.generation_accounting(release_fixture.fixture.gid)
            assert agreement.status=='released' and len(agreement.prior_restructures)==1
            assert ledger.cash_snapshot()['unpaid_total']==0
            assert ledger.generation_calendar_view(release_fixture.fixture.gid).annual_charges()==()
        finally:release_fixture.doCleanups()
        print("Native Windows layered release full/compact history, retained payroll and rollover restart verified (synthetic).")

        from tests import test_layered_trade_bridge
        trade_history_fixture=test_layered_trade_bridge.LayeredTradeBridgeTests()
        trade_history_fixture.setUp()
        try:
            requests=[trade_history_fixture.request,{**trade_history_fixture.request,'receipt_format':'target_v1'}]
            payload=''.join(json.dumps(item,separators=(',',':'))+'\n' for item in requests)
            historical=None
            for phase in ('assignment','next_year','buyer_release'):
                fixture=trade_history_fixture.fixture
                if phase=='next_year':
                    fixture.fixture.pay('b','base:0',1800000);fixture.fixture.roll(('a','b'),2028)
                if phase=='buyer_release':
                    from datetime import date
                    from fractions import Fraction
                    from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
                    from franchise.guarantees import DiscountProfile
                    ledger=fixture.store.load_team('b')
                    fixture.store.release_calendar_preseason_veteran('b','native-history-buyer-release','v',
                        generation_id=ledger.contract_identity('v').generation_id,
                        scope=PreseasonReleaseScope(2029,date(2029,6,1),date(2029,9,10),EXCLUDED_LIABILITIES,
                            True,True,0,'synthetic buyer release'),discount=DiscountProfile(2029,Fraction(0),'synthetic zero'),
                        payment_year_offsets=(0,),expected_revision=ledger.revision,access_check=lambda:None)
                previous=None
                for attempt in range(2):
                    result=subprocess.run([sys.argv[1],sys.executable,str(fixture.path),'--calendar-history'],
                        input=payload,text=True,capture_output=True,timeout=30,check=True)
                    replies=[json.loads(line) for line in result.stdout.splitlines()]
                    assert len(replies)==2 and all(reply['error'] is None for reply in replies)
                    assert replies==[trade_history_fixture.bridge.handle(item) for item in requests]
                    assert replies[0]['result']['format']==3
                    assert replies[0]['result']['amendment_history']==replies[1]['result']['amendment_history']
                    if attempt:assert replies==previous and fixture.path.read_bytes()==unchanged
                    else:unchanged=fixture.path.read_bytes()
                    if historical is not None:assert replies==historical
                    previous=replies
                historical=previous
            seller=FranchiseStore(fixture.path).load_team('a');buyer=fixture.store.load_team('b')
            assert len(seller.generation_accounting(fixture.gid).prior_restructures)==1
            incoming=buyer.generation_accounting(historical[0]['result']['buyer_generation_id'])
            assert incoming.contract.bonus_layers==() and incoming.prior_restructures==()
            assert incoming.status=='released' and buyer.cash_snapshot()['nominal_total']==1800000
        finally:trade_history_fixture.doCleanups()
        print("Native Windows layered assignment full/compact history, separate buyer payroll/release and rollover restart verified (synthetic).")

        from tests import test_calendar_history_bridge
        history_read_fixture=test_calendar_history_bridge.CalendarHistoryBridgeTests()
        history_read_fixture.setUp()
        try:
            requests=[history_read_fixture.contract,history_read_fixture.player,
                {**history_read_fixture.player,'request_id':'scoped-b-history','team_id':'b'}]
            payload=''.join(json.dumps(item,separators=(',',':'))+'\n' for item in requests)
            saved_history=None
            for phase in ('active','expired'):
                if phase=='expired':history_read_fixture.fixture.expire()
                unchanged=history_read_fixture.fixture.path.read_bytes()
                previous=None
                for attempt in range(2):
                    result=subprocess.run([sys.argv[1],sys.executable,str(history_read_fixture.fixture.path),'--calendar-history'],
                        input=payload,text=True,capture_output=True,timeout=30,check=True)
                    replies=[json.loads(line) for line in result.stdout.splitlines()]
                    assert len(replies)==3 and all(reply['error'] is None for reply in replies)
                    assert replies==[history_read_fixture.bridge.handle(item) for item in requests]
                    context=replies[0]['result']
                    assert context['format']==5 and context['original_contract']['elapsed_years']==0
                    assert len(context['amendment_history']['prior_restructures'])==1
                    assert replies[1]['result']['personality']=={'money':0.8}
                    assert replies[2]['result']['calendar_contract_context'] is None
                    assert replies[2]['result']['personality'] is None
                    if phase=='active':saved_history=context['amendment_history']
                    else:
                        assert context['calendar_accounting']['status']=='expired'
                        assert context['amendment_history']==saved_history
                        assert context['economic_archive']['cash_obligation']['paid']==9000000
                    if attempt:assert replies==previous
                    previous=replies
                    assert history_read_fixture.fixture.path.read_bytes()==unchanged
        finally:history_read_fixture.doCleanups()
        print("Native Windows calendar-v4 immutable history and scoped player reads survive expiry/restart without writes (synthetic).")

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
                assert len(replies)==5
                assert replies[0]['error'] is None and replies[0]['result']['ai_enabled'] is True
                if attempt==0:
                    assert replies[1]['error'] is None and replies[1]['result']['room_after']==90
                    agreement=replies[3];context=replies[4]
                else:
                    assert replies[1]['error']=='state_rejected'
                    assert replies[3]==agreement and replies[4]==context
                assert replies[2]['error'] is None and replies[2]['result']['outcome']=='player_rejected'
                assert replies[2]['result']['decision_mode']=='proposal' and 'charges' not in replies[2]['result']
                assert replies[3]['error'] is None and replies[3]['result']['outcome']=='signed'
                assert replies[4]['error'] is None
                current=c_store.load_team('a')
                assert current.charges==(10,) and current.revision==1 and current._players=={'v'}
                assert replies[3]['result']==c_store.player_context('a','v')
            print("Native Windows plain-C host adapter, bounded response retrieval and restart verified (synthetic).")
            from franchise.inference_budget import InferenceBudget
            budget_path=Path(directory)/'C budget with spaces.sqlite'
            scope='C host 2026 "--provider offline-fixture"'
            for attempt in range(2):
                result=subprocess.run([sys.argv[2],sys.executable,str(c_path),str(budget_path),scope],
                    text=True,capture_output=True,timeout=30,check=True)
                replies=[json.loads(line) for line in result.stdout.splitlines()]
                assert len(replies)==2 and replies[0]['error']=='ai_disabled'
                assert replies[1]['error'] is None
                assert replies[1]['result']==c_store.player_context('a','v')
                assert not budget_path.exists()
            print("Native Windows request-only launch refuses live AI without token policy while manual reads remain available (synthetic).")
            import sqlite3
            from contextlib import closing
            token_path=Path(directory)/'C cumulative token budget with spaces.sqlite'
            for attempt in range(2):
                result=subprocess.run([sys.argv[2],sys.executable,str(c_path),str(token_path),scope,'token-budget'],
                    text=True,capture_output=True,timeout=30,check=True)
                replies=[json.loads(line) for line in result.stdout.splitlines()]
                assert len(replies)==2 and replies[0]['error']=='ai_disabled'
                assert replies[1]['error'] is None and replies[1]['result']==c_store.player_context('a','v')
                assert token_path.is_file()
                with closing(sqlite3.connect(token_path)) as budget_db:
                    assert budget_db.execute('SELECT scope,request_limit FROM policies').fetchall()==[(scope,2)]
                    assert budget_db.execute('SELECT scope,token_limit FROM token_policies').fetchall()==[(scope,30000)]
                status=InferenceBudget(token_path,scope=scope,request_limit=2,token_limit=30000).status()
                assert status['attempts']==0 and status['reserved_tokens']==0 and status['remaining_tokens']==30000
            print("Native Windows plain-C cumulative token launch preserves immutable policy across restart without paid inference (synthetic).")









if __name__ == "__main__":
    main()
