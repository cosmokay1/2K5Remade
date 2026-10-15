"""Authored full-league journal/crash tests; no retail assets or provider calls."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from franchise import guest_signing
from franchise.books import ActiveContract, OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger, Rejected
from franchise.cash import CashObligation
from franchise.control import AccessDisabled
from franchise.guest_contracts import GuestContractTerms
from franchise.store import FranchiseStore
from tools.inspect_franchise_save import TEAMS
import test_confirm_saved_signing as saved_fixtures


class GuestSigningJournalTests(unittest.TestCase):
    def setUp(self):
        sample=saved_fixtures.SavedSigningConfirmationTests();sample.setUp()
        self.before,self.after,self.bindings=sample.before,sample.after,sample.bindings
        self.player,self.offer,self.raw=sample.player,sample.offer,sample.raw
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'journal.sqlite';self.store=FranchiseStore(self.path)
        owned=self.bindings['players'][0]['player_id']
        opening=GuestContractTerms(829,4,1,2).to_offer(owned)
        for team in TEAMS:
            contracts=(ActiveContract(opening,'Authored known original contract'),) if team=='49ers' else ()
            floors={owned:(1000,)*15,self.player:(1000,)*15} if team=='49ers' else {}
            self.store.create_team(team,Ledger.from_opening(OpeningBooks(contracts=contracts),
                cap=80500000,roster_reserve=0,max_bonus_years=5,veteran_minimums=floors))
            records=(CashObligation('contract:'+owned,owned,sum(opening.salaries)+opening.signing_bonus,
                                    0,'Authored explicit unpaid cash'),) if team=='49ers' else ()
            self.store.initialize_cash(team,records,source='Authored complete cash inventory')
        self.revision=self.store.load_team('49ers').revision
        self.calls=0
        def provider(_):
            self.calls+=1
            return json.dumps(dict(action='accept',reason='Authored accepted deal',salaries=None,signing_bonus=None))
        reply=Bridge(self.store,provider=provider,access_check=lambda:None).handle(dict(
            protocol=1,request_id='proposal',operation='negotiate_proposal',team_id='49ers',
            offer=self.offer.to_dict(),contract_format='original_fxg_v1',expected_revision=self.revision,
            timeout_ms=1000,personality={},performance={'games':16},relationships={}))
        self.assertIsNone(reply['error'],reply)
        self.initial=self.store.load_team('49ers').financial_snapshot()

    def prepare(self,store=None,**changes):
        args=dict(bindings=self.bindings,before_payload=self.before,guest_offer=self.raw,
            expected_before_sha256=hashlib.sha256(self.before).hexdigest(),expected_revision=self.revision,
            access_check=lambda:None)
        args.update(changes)
        return guest_signing.prepare(store or self.store,'49ers','proposal','journal',**args)

    def settle(self,store=None,**changes):
        return guest_signing.settle(store or self.store,'journal',changes.get('after',self.after),
                                    access_check=changes.get('access_check',lambda:None))

    def test_prepare_restart_freeze_confirm_and_exactly_once_settlement(self):
        prepared=self.prepare();reopened=FranchiseStore(self.path)
        self.assertFalse(prepared['write_authorized'])
        self.assertEqual(self.prepare(reopened),prepared)
        self.assertEqual(guest_signing.inspect(reopened,'journal',self.before)['save_position'],'before')
        candidate=guest_signing.inspect(reopened,'journal',self.after)
        self.assertEqual(candidate['save_position'],'candidate_after')
        self.assertFalse(candidate['write_authorized'])
        self.assertEqual(candidate['before_payload'],self.before)
        self.assertEqual(reopened.load_team('49ers').financial_snapshot(),self.initial)
        with self.assertRaisesRegex(Rejected,'awaits confirmation'):
            reopened.commit_accepted_proposal('49ers','proposal','bypass',self.revision,access_check=lambda:None)
        with self.assertRaisesRegex(Rejected,'awaits confirmation'):
            reopened.bind_actor('49ers',self.player,{}, {},access_check=lambda:None)
        with self.assertRaisesRegex(Rejected,'awaits confirmation'):
            reopened.initialize_cash('Bears',(),source='Competing club operation')
        receipt=self.settle(reopened)
        self.assertEqual(receipt.charges,(4766000,3523000))
        self.assertEqual(self.settle(FranchiseStore(self.path)),receipt)
        status=guest_signing.inspect(reopened,'journal',self.after)
        self.assertEqual((status['state'],status['save_position']),('settled','confirmed_after'))
        self.assertEqual(status['before_payload'],self.before)
        self.assertEqual(status['after_payload'],self.after)
        self.assertEqual(reopened.load_team('49ers').revision,self.revision+1)
        self.assertEqual(reopened.load_team('49ers').cash_snapshot()['nominal_total'],
                         2*(sum(self.offer.salaries)+self.offer.signing_bonus))
        self.assertEqual(len(reopened.negotiation_history('49ers',self.player)),2)
        self.assertEqual(self.calls,1)
        with self.assertRaises(Rejected): self.settle(after=self.before)
        with self.assertRaises(Rejected): self.prepare()
        # The old save after a committed settlement is detected, never rolled back implicitly.
        status=guest_signing.inspect(reopened,'journal',self.before)
        self.assertEqual(status['save_position'],'before')
        self.assertEqual(status['after_payload'],self.after)

    def test_concurrent_settlement_retries_share_one_saved_and_financial_result(self):
        self.prepare()
        with ThreadPoolExecutor(max_workers=2) as pool:
            receipts=list(pool.map(lambda _:self.settle(FranchiseStore(self.path)),range(2)))
        self.assertEqual(receipts[0],receipts[1])
        self.assertEqual(self.store.load_team('49ers').revision,self.revision+1)
        self.assertEqual(len(self.store.negotiation_history('49ers',self.player)),2)
        self.assertEqual(guest_signing.inspect(self.store,'journal',self.after)['state'],'settled')

    def test_game_restarting_during_cancellation_does_not_release_the_pending_lock(self):
        self.prepare();checks=0
        def stopped():
            nonlocal checks
            checks+=1
            return checks==1
        with self.assertRaises(Rejected):
            guest_signing.cancel(self.store,'journal',self.before,game_stopped_check=stopped)
        self.assertEqual(checks,2)
        self.assertEqual(guest_signing.inspect(self.store,'journal',self.before)['state'],'prepared')
        with self.assertRaisesRegex(Rejected,'awaits confirmation'):
            self.store.initialize_cash('Bears',(),source='Still held')

    def test_only_one_pending_signing_and_no_changed_preparation_retry(self):
        self.prepare()
        with self.assertRaises(Rejected): self.prepare(guest_offer={**self.raw,'amount_word':828})
        with self.assertRaisesRegex(Rejected,'Another guest signing'):
            guest_signing.prepare(self.store,'49ers','proposal','another',bindings=self.bindings,
                before_payload=self.before,guest_offer=self.raw,expected_before_sha256=hashlib.sha256(self.before).hexdigest(),
                expected_revision=self.revision,access_check=lambda:None)

    def test_prepare_shutdown_rolls_back_reservation(self):
        checks=0
        def disable():
            nonlocal checks
            checks+=1
            if checks==2: raise AccessDisabled('Disabled before preparation commit')
        with self.assertRaises(AccessDisabled): self.prepare(access_check=disable)
        with self.assertRaises(Rejected): guest_signing.inspect(self.store,'journal',self.before)
        self.assertEqual(self.store.load_team('49ers').financial_snapshot(),self.initial)
        self.prepare()

    def test_settlement_shutdown_rolls_back_journal_and_all_finances(self):
        self.prepare();checks=0
        def disable():
            nonlocal checks
            checks+=1
            if checks==3: raise AccessDisabled('Disabled after financial inserts')
        with self.assertRaises(AccessDisabled): self.settle(access_check=disable)
        self.assertEqual(checks,3)
        reopened=FranchiseStore(self.path)
        status=guest_signing.inspect(reopened,'journal',self.after)
        self.assertEqual((status['state'],status['save_position']),('prepared','candidate_after'))
        self.assertIsNone(status['after_payload'])
        self.assertEqual(reopened.load_team('49ers').financial_snapshot(),self.initial)
        self.assertEqual(len(reopened.negotiation_history('49ers',self.player)),1)
        self.settle(reopened)

    def test_abrupt_process_exit_keeps_original_backup_and_unsettled_state(self):
        self.prepare()
        after_path=self.path.with_suffix('.after');after_path.write_bytes(self.after)
        code='''import os,sys
from pathlib import Path
from franchise.store import FranchiseStore
from franchise.guest_signing import settle
checks=0
def terminate():
 global checks
 checks+=1
 if checks==3: os._exit(73)
settle(FranchiseStore(sys.argv[1]),'journal',Path(sys.argv[2]).read_bytes(),access_check=terminate)
'''
        child=subprocess.run([sys.executable,'-c',code,str(self.path),str(after_path)],timeout=15)
        self.assertEqual(child.returncode,73)
        reopened=FranchiseStore(self.path)
        status=guest_signing.inspect(reopened,'journal',self.after)
        self.assertEqual(status['state'],'prepared')
        self.assertEqual(status['before_payload'],self.before)
        self.assertEqual(reopened.load_team('49ers').financial_snapshot(),self.initial)
        self.settle(reopened)
        self.assertEqual(self.calls,1)

    def test_cancel_requires_stopped_game_and_original_save_without_enabling_ai(self):
        self.prepare()
        with self.assertRaises(Rejected): guest_signing.cancel(self.store,'journal',self.before,game_stopped_check=lambda:False)
        with self.assertRaises(Rejected): guest_signing.cancel(self.store,'journal',self.after,game_stopped_check=lambda:None)
        with self.assertRaises(ValueError): guest_signing.cancel(self.store,'journal',self.before,game_stopped_check=None)
        self.assertEqual(guest_signing.cancel(self.store,'journal',self.before,game_stopped_check=lambda:None)['state'],'cancelled')
        self.assertEqual(self.store.load_team('49ers').financial_snapshot(),self.initial)
        with self.assertRaises(Rejected): self.settle()
        self.store.bind_actor('49ers',self.player,{}, {},access_check=lambda:None) # Ordinary writes resume.
        with self.assertRaises(Rejected): self.prepare()

    def test_disabled_control_preserves_readable_recovery_and_pending_lock(self):
        self.prepare()
        def disabled(): raise AccessDisabled('Disabled')
        with self.assertRaises(AccessDisabled): self.settle(access_check=disabled)
        status=guest_signing.inspect(FranchiseStore(self.path),'journal',self.after)
        self.assertEqual(status['save_position'],'candidate_after')
        self.assertFalse(status['write_authorized'])
        self.assertEqual(self.store.load_team('49ers').financial_snapshot(),self.initial)

    def test_invalid_after_save_does_not_release_pending_work(self):
        self.prepare()
        for payload in (self.before,b'unsupported'):
            with self.assertRaises(ValueError): self.settle(after=payload)
        self.assertEqual(guest_signing.inspect(self.store,'journal',b'unsupported')['save_position'],'unrecognized')
        self.assertEqual(self.store.load_team('49ers').financial_snapshot(),self.initial)

    def test_missing_cash_or_incomplete_league_cannot_prepare(self):
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("DELETE FROM events WHERE team_id='Vikings'")
        with self.assertRaisesRegex(Rejected,'cash obligations'): self.prepare()
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("DELETE FROM teams WHERE id='Vikings'")
        with self.assertRaisesRegex(Rejected,'league books'): self.prepare()

    def test_corrupt_backup_or_confirmation_is_not_returned_as_recovery_evidence(self):
        self.prepare()
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("UPDATE guest_signings SET before_payload=? WHERE request_id='journal'",(b'changed',))
        with self.assertRaises(ValueError): guest_signing.inspect(self.store,'journal',self.before)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("UPDATE guest_signings SET before_payload=? WHERE request_id='journal'",(self.before,))
        self.settle()
        with closing(sqlite3.connect(self.path)) as db,db:
            proof=json.loads(db.execute("SELECT confirmation FROM guest_signings").fetchone()[0])
            proof['after_roster_payroll']+=1
            db.execute('UPDATE guest_signings SET confirmation=?',(json.dumps(proof),))
        with self.assertRaises(ValueError): guest_signing.inspect(self.store,'journal',self.after)
