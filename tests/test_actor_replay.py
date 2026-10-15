"""Actor replay preserves chronological financial/identity checks without repeated work."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger, Offer, Rejected
from franchise.initialization import initial_actor
from franchise.store import FranchiseStore


class ActorReplayTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'state.sqlite';self.store=FranchiseStore(self.path)
        self.store.create_franchise({team:Ledger.from_opening(OpeningBooks(),cap=100,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'p':(1,),'q':(1,),'r':(1,)}) for team in ('a','b')},seed='replay-world')

    def test_every_actor_posting_is_checked_even_late_in_unchanged_block(self):
        with closing(sqlite3.connect(self.path)) as db:
            event_id,serialized=db.execute("SELECT id,payload FROM events WHERE team_id='a' AND request_key='actor:r'").fetchone()
            event=json.loads(serialized);event['posting']['cap']=101
            db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(event),event_id));db.commit()
        with self.assertRaisesRegex(ValueError,'financial posting'):self.store.load_team('a')

    def test_interleaved_financial_event_changes_the_following_actor_posting(self):
        self.store.sign('a','sign',Offer('p',(10,),0),0)
        after=self.store.load_team('a').financial_snapshot()
        # Same valid actor initialization occurs after the financial event.
        with closing(sqlite3.connect(self.path)) as db:
            serialized=db.execute("SELECT payload FROM events WHERE team_id='a' AND request_key='actor:r'").fetchone()[0]
            event=json.loads(serialized);event['posting']=after
            db.execute("DELETE FROM events WHERE team_id='a' AND request_key='actor:r'")
            db.execute("INSERT INTO events(team_id,request_key,kind,payload) VALUES ('a','actor:r','actor',?)",(json.dumps(event),));db.commit()
        ledger=self.store.load_team('a')
        self.assertEqual(ledger.financial_snapshot(),after)
        self.assertEqual(ledger._actors['r'],initial_actor('replay-world','r'))
        with closing(sqlite3.connect(self.path)) as db:
            event['posting']['charges']=[0]
            db.execute("UPDATE events SET payload=? WHERE team_id='a' AND request_key='actor:r'",(json.dumps(event),));db.commit()
        with self.assertRaisesRegex(ValueError,'financial posting'):self.store.load_team('a')

    def test_expected_origins_are_not_mutable_live_actor_objects_or_cross_read_cache(self):
        provider=lambda _:json.dumps(dict(action='accept',reason='Authored decision',salaries=None,signing_bonus=None))
        bridge=Bridge(self.store,provider=provider,access_check=lambda:None)
        reply=bridge.handle(dict(protocol=1,request_id='proposal',operation='negotiate_proposal',team_id='a',
            offer=dict(player_id='q',salaries=[10],signing_bonus=0),expected_revision=0,timeout_ms=1000,
            personality={},relationships={},performance={}))
        self.assertIsNone(reply['error'])
        self.store.update_relationship('a','consequence','q','trust',0.1,source_request_id='proposal',expected_revision=0)
        with self.store._connection() as db:
            teams=self.store._load_teams(db,('a','b'))
        self.assertEqual(teams['a']._actors['q']['relationships']['trust'],0.6)
        self.assertEqual(teams['b']._actors['q'],initial_actor('replay-world','q'))
        # A later read must validate persisted origins afresh.
        with closing(sqlite3.connect(self.path)) as db:
            serialized=db.execute("SELECT payload FROM events WHERE team_id='b' AND request_key='actor:r'").fetchone()[0]
            event=json.loads(serialized);event['actor']['relationships']['respect']=0.9
            db.execute("UPDATE events SET payload=? WHERE team_id='b' AND request_key='actor:r'",(json.dumps(event),));db.commit()
        with self.assertRaisesRegex(ValueError,'franchise origin'):self.store.load_team('b')

    def test_unknown_actor_is_rejected_within_a_cached_classification_block(self):
        with closing(sqlite3.connect(self.path)) as db:
            serialized=db.execute("SELECT payload FROM events WHERE team_id='a' AND request_key='actor:r'").fetchone()[0]
            event=json.loads(serialized);event['player_id']='unregistered'
            event['actor']=initial_actor('replay-world','unregistered')
            db.execute("UPDATE events SET payload=? WHERE team_id='a' AND request_key='actor:r'",(json.dumps(event),));db.commit()
        with self.assertRaisesRegex(Rejected,'unknown'):self.store.load_team('a')
