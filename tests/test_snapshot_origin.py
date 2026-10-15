"""Durable namespace association without changing saves, actors or journal intents."""
import contextlib
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from franchise import guest_signing
from franchise.cap import Rejected
from franchise.snapshot_origin import bind, verify, KEY
from franchise.store import FranchiseStore
from tools.bind_franchise_snapshot import main
from tools.check_native_saved_signing import fixture


class SnapshotOriginTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.root=Path(directory.name);self.data=fixture(self.root)
        self.store=self.data['store'];sample=self.data['sample']
        self.bindings=sample.bindings;self.before=sample.before;self.after=sample.after

    def metadata(self):
        with contextlib.closing(sqlite3.connect(self.store.path)) as db:
            row=db.execute('SELECT value FROM franchise_metadata WHERE key=?',(KEY,)).fetchone()
        return None if row is None else json.loads(row[0])

    def prepare(self,bindings=None):
        return guest_signing.prepare(self.store,'49ers','native-captured','journal',
            bindings=bindings or self.bindings,before_payload=self.before,guest_offer=self.data['sample'].raw,
            expected_before_sha256=hashlib.sha256(self.before).hexdigest(),expected_revision=1,access_check=lambda:None)

    def test_registration_restart_and_representation_conversion_preserve_state(self):
        before={team:self.store.load_team(team).financial_snapshot() for team in ('49ers','Bears')}
        actors=self.store.player_context('49ers',self.data['sample'].player)
        history=self.store.negotiation_history('49ers',self.data['sample'].player)
        payload=bytes(self.before);original=copy.deepcopy(self.bindings)
        association=bind(self.store,self.bindings,self.before)
        old=copy.deepcopy(self.bindings);old.pop('game_context');old['version']='original-save-bindings-v1'
        self.assertEqual(bind(FranchiseStore(self.store.path),old,self.before),association)
        changed=copy.deepcopy(self.bindings);changed['players'].reverse()
        changed['game_context'].update(source_image_sha256='b'*64,loaded_image_sha256='c'*64)
        self.assertEqual(verify(self.store,changed,self.before),association)
        self.assertEqual(actors,self.store.player_context('49ers',self.data['sample'].player))
        self.assertEqual(history,self.store.negotiation_history('49ers',self.data['sample'].player))
        self.assertEqual(before,{team:self.store.load_team(team).financial_snapshot() for team in before})
        self.assertEqual(self.bindings,original);self.assertEqual(self.before,payload)

    def test_missing_or_different_namespace_requires_explicit_registration(self):
        with self.assertRaises(Rejected):verify(self.store,self.bindings,self.before)
        bind(self.store,self.bindings,self.before)
        for key,value in (('franchise_id','0'*32),('baseline_payload_sha256','1'*64)):
            changed=copy.deepcopy(self.bindings);changed[key]=value
            for operation in (bind,verify):
                with self.subTest(key=key,operation=operation),self.assertRaises(Rejected):
                    operation(self.store,changed,self.before)
        self.assertEqual(self.metadata()['franchise_id'],self.bindings['franchise_id'])

    def test_wrong_seed_and_rerolled_player_ids_cannot_claim_database(self):
        for change in ('seed','player'):
            registry=copy.deepcopy(self.bindings)
            if change=='seed':registry['personality_seed']='different valid authored seed'
            else:registry['players'][1]['player_id']='f'*32
            with self.subTest(change=change),self.assertRaises(Rejected):bind(self.store,registry,self.before)
            self.assertIsNone(self.metadata())

    def test_actor_origin_corruption_cannot_be_registered(self):
        with contextlib.closing(sqlite3.connect(self.store.path)) as db:
            event_id,serialized=db.execute("SELECT id,payload FROM events WHERE kind='actor' LIMIT 1").fetchone()
            event=json.loads(serialized);event['actor']['relationships']['trust']=0.9
            db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(event),event_id));db.commit()
        with self.assertRaisesRegex(Rejected,'personality origin'):bind(self.store,self.bindings,self.before)
        self.assertIsNone(self.metadata())

    def test_bootstrap_changes_require_explicit_migration(self):
        bind(self.store,self.bindings,self.before)
        with contextlib.closing(sqlite3.connect(self.store.path)) as db:
            config=json.loads(db.execute("SELECT config FROM teams WHERE id='Bears'").fetchone()[0])
            config['cap']+=1000
            db.execute("UPDATE teams SET config=? WHERE id='Bears'",(json.dumps(config),));db.commit()
        with self.assertRaises(Rejected):verify(self.store,self.bindings,self.before)

    def test_initial_registration_requires_matching_ownership(self):
        with self.assertRaisesRegex(Rejected,'ownership'):bind(self.store,self.bindings,self.after)
        self.assertIsNone(self.metadata())

    def test_pending_work_blocks_registration_but_not_existing_namespace_recovery(self):
        self.prepare()
        with self.assertRaisesRegex(Rejected,'awaits confirmation'):bind(self.store,self.bindings,self.before)
        self.assertIsNone(self.metadata())

    def test_legacy_journal_stays_exact_through_association_verification_and_settlement(self):
        association=bind(self.store,self.bindings,self.before)
        old=copy.deepcopy(self.bindings);old.pop('game_context');old['version']='original-save-bindings-v1'
        self.prepare(old)
        with contextlib.closing(sqlite3.connect(self.store.path)) as db:
            intent=db.execute('SELECT intent FROM guest_signings').fetchone()[0]
        self.assertEqual(verify(self.store,self.bindings,self.after),association)
        guest_signing.settle(self.store,'journal',self.after,access_check=lambda:None)
        self.assertEqual(verify(FranchiseStore(self.store.path),self.bindings,self.after),association)
        with contextlib.closing(sqlite3.connect(self.store.path)) as db:
            self.assertEqual(db.execute('SELECT intent FROM guest_signings').fetchone()[0],intent)
        self.assertEqual(json.loads(intent)['bindings']['version'],'original-save-bindings-v1')
        self.assertEqual(guest_signing.inspect(self.store,'journal',self.after)['save_position'],'confirmed_after')

    def test_corrupt_record_is_rejected_without_repair_or_overwrite(self):
        bind(self.store,self.bindings,self.before)
        corrupt=self.metadata();corrupt['format']=True
        with contextlib.closing(sqlite3.connect(self.store.path)) as db:
            db.execute('UPDATE franchise_metadata SET value=? WHERE key=?',(json.dumps(corrupt),KEY));db.commit()
        for operation in (bind,verify):
            with self.assertRaises(Rejected):operation(self.store,self.bindings,self.before)
        self.assertIs(self.metadata()['format'],True)

    def test_competing_namespaces_cannot_both_register(self):
        other=copy.deepcopy(self.bindings);other['franchise_id']='e'*32
        def register(registry):
            try: return bind(FranchiseStore(self.store.path),registry,self.before)['franchise_id']
            except Rejected: return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(register,(self.bindings,other)))
        self.assertEqual(sum(value is not None for value in results),1)
        self.assertIn(self.metadata()['franchise_id'],results)

    def test_cli_does_not_create_missing_database_or_modify_input_files(self):
        missing=self.root/'missing.sqlite'
        paths=self.data['paths'];save=paths['save'];registry=paths['bindings']
        before=(save.read_bytes(),registry.read_bytes())
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
            main([str(missing),str(save),str(registry)])
        self.assertFalse(missing.exists())
        with contextlib.redirect_stdout(io.StringIO()) as output:
            main([self.store.path,str(save),str(registry)])
        self.assertFalse(json.loads(output.getvalue())['write_authorized'])
        self.assertEqual((save.read_bytes(),registry.read_bytes()),before)
