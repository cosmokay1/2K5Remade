import unittest
from franchise.cap import Ledger, Offer, Rejected
from franchise.draft import Prospect, comparison_context
from franchise.performance import Observation, PerformanceEvidence
from franchise.rookie import RookieScale


class DraftComparisonTests(unittest.TestCase):
    def ledger(self):
        return Ledger(cap=20, roster_reserve=0, max_bonus_years=5, veteran_minimums={}, existing_charges=(0,)*4, rookies={p: RookieScale(2, (10,)*4, 10, 30, 100) for p in ('a', 'b')}, rookie_year_one_allocation=25, rookie_total_allocation=100)

    def prospect(self, player, salary):
        evidence = PerformanceEvidence(player, 'synthetic college season', 'cpu_played', (
            Observation('receptions', 50, 'synthetic fixture'),
            Observation('targets', None, 'synthetic fixture', 'engine did not record opportunities'),
            Observation('pressures', None, 'synthetic fixture', 'not applicable/observed'),
        ), 'generated fixture, not actual college records')
        return Prospect(player, 'WR', 'slot receiver', 'synthetic college conference', 'fixture roster',
                        (evidence,), {'priorities': ['early playing time']}, 'fixture interview',
                        Offer(player, (salary,)*4, 0), 'synthetic slot estimate')

    def context(self, ledger, prospects, revision=0):
        return comparison_context(ledger, expected_revision=revision, draft_round=2, overall_pick=40,
            prospects=prospects, team_needs=[{'position':'WR', 'role':'slot', 'reason':'returning slot player departed', 'source':'fixture roster history'}])

    def test_cap_checks_and_unknown_opportunities_do_not_change_money(self):
        ledger = self.ledger()
        before = ledger.financial_snapshot()
        context = self.context(ledger, (self.prospect('a', 10), self.prospect('b', 21)))
        self.assertEqual([p['contract_validation']['status'] for p in context['prospects']], ['eligible', 'ineligible'])
        evidence = context['prospects'][0]['performance'][0]
        self.assertIsNone(evidence['observations']['targets']['value'])
        self.assertIn('snaps', evidence['missing_counters'])
        self.assertEqual(ledger.financial_snapshot(), before)

    def test_hidden_ratings_identity_and_stale_revision_reject(self):
        ledger = self.ledger()
        prospect = self.prospect('a', 10)
        prospect.personality['catching'] = 99
        with self.assertRaisesRegex(ValueError, 'hidden game ratings'):
            self.context(ledger, (prospect,))
        with self.assertRaises(Rejected):
            self.context(ledger, (self.prospect('a', 10),), revision=1)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.context(ledger, (self.prospect('a', 10), self.prospect('a', 10)))

    def test_rookie_pool_limits_independent_of_team_cap(self):
        ledger = self.ledger()
        ledger.update_budget(cap=100, roster_reserve=0, expected_revision=0)
        context = self.context(ledger, (self.prospect('a', 26),), revision=1)
        self.assertEqual(context['prospects'][0]['contract_validation']['status'], 'ineligible')
        self.assertEqual(ledger.revision, 1)

    def test_duplicate_prospect_windows_reject_before_inference(self):
        from dataclasses import replace
        from franchise.draft import DraftScouting
        ledger=self.ledger()
        prospect=self.prospect('a',10)
        repeated=replace(prospect,evidence=prospect.evidence+prospect.evidence)
        calls=[]
        before=ledger.financial_snapshot()
        with self.assertRaisesRegex(ValueError,'Duplicate prospect observation'):
            DraftScouting(ledger,access_check=lambda:None).recommend('duplicate',lambda context:calls.append(context),
                expected_revision=0,draft_round=2,overall_pick=40,prospects=(repeated,),team_needs=[])
        self.assertEqual(calls,[])
        self.assertEqual(ledger.financial_snapshot(),before)
        # Separate simulation modes remain explicit observations, not a summed total.
        other=replace(prospect.evidence[0],mode='played')
        context=replace(prospect,evidence=prospect.evidence+(other,)).to_context()
        self.assertEqual([e['mode'] for e in context['performance']],['cpu_played','played'])

    def test_concurrent_budget_change_invalidates_comparison(self):
        ledger = self.ledger()
        class ChangedAfterPreview:
            def validate_scouting_personality(self, player, personality):
                return ledger.validate_scouting_personality(player, personality)
            def scouting_history(self):
                return []
            def management_context(self):
                return ledger.management_context()
            def negotiation_context(self, player):
                return ledger.negotiation_context(player)
            def preview_draft_offer(self, offer, revision):
                result = ledger.preview_offer(offer, revision)
                ledger.update_budget(cap=100, roster_reserve=0, expected_revision=revision)
                return result
        with self.assertRaisesRegex(Rejected, 'stale'):
            self.context(ChangedAfterPreview(), (self.prospect('a', 10),))

    def test_scouting_guarded_choice_cache_and_financial_rejections(self):
        from franchise.draft import DraftScouting
        from franchise.control import AccessDisabled
        import json
        ledger = self.ledger()
        enabled, calls = True, []
        def check():
            if not enabled:
                raise AccessDisabled('synthetic shutdown')
        session = DraftScouting(ledger, access_check=check)
        inputs = dict(expected_revision=0, draft_round=2, overall_pick=40,
                      prospects=(self.prospect('a', 10), self.prospect('b', 21)), team_needs=[])
        def provider(context):
            calls.append(context)
            return json.dumps({'action':'recommend', 'player_id':'a', 'reason':'Observed production fits the slot role',
                               'uncertainty':'Targets were not recorded; efficiency is unknown'})
        before = ledger.financial_snapshot()
        reply = session.recommend('first', provider, **inputs)
        self.assertFalse(reply['pick_exercised'])
        self.assertEqual(session.recommend('first', provider, **inputs), reply)
        self.assertEqual(len(calls), 1)
        self.assertEqual(ledger.financial_snapshot(), before)
        bad = lambda _: json.dumps({'action':'recommend', 'player_id':'b', 'reason':'Pick b', 'uncertainty':'Unknown'})
        with self.assertRaises(Rejected):
            session.recommend('bad', bad, **inputs)
        enabled = False
        with self.assertRaises(AccessDisabled):
            session.recommend('first', provider, **inputs)

    def test_shutdown_and_budget_changes_during_scouting_discard_model_choice(self):
        from franchise.draft import DraftScouting
        from franchise.control import AccessDisabled
        import json
        ledger = self.ledger()
        enabled = True
        def check():
            if not enabled:
                raise AccessDisabled('synthetic shutdown')
        session = DraftScouting(ledger, access_check=check)
        inputs = dict(expected_revision=0, draft_round=2, overall_pick=40,
                      prospects=(self.prospect('a', 10),), team_needs=[])
        choice = json.dumps({'action':'recommend', 'player_id':'a', 'reason':'Production', 'uncertainty':'Small sample'})
        def shutdown(_):
            nonlocal enabled
            enabled = False
            return choice
        with self.assertRaises(AccessDisabled):
            session.recommend('first', shutdown, **inputs)
        enabled = True
        def changed_budget(_):
            ledger.update_budget(cap=100, roster_reserve=0, expected_revision=0)
            return choice
        with self.assertRaises(Rejected):
            session.recommend('first', changed_budget, **inputs)
        self.assertEqual(ledger.financial_snapshot()['signed_players'], [])

    def test_scouting_defers_without_paid_call_when_no_estimate_fits(self):
        from franchise.draft import DraftScouting
        ledger = self.ledger()
        session = DraftScouting(ledger, access_check=lambda: None)
        def forbidden(_):
            raise AssertionError('No eligible prospect should require inference')
        reply = session.recommend('defer', forbidden, expected_revision=0, draft_round=2, overall_pick=40,
                                  prospects=(self.prospect('a', 21),), team_needs=[])
        self.assertEqual(reply['decision']['action'], 'defer')
        self.assertIsNone(reply['decision']['player_id'])
        self.assertEqual(ledger.revision, 0)

    def durable_scouting(self, directory):
        from pathlib import Path
        from franchise.books import OpeningBooks
        from franchise.store import FranchiseStore, StoredLedger
        store = FranchiseStore(Path(directory) / 'state.sqlite')
        store.create_team('a', Ledger.from_opening(OpeningBooks(), cap=20, roster_reserve=0,
            max_bonus_years=5, veteran_minimums={}, rookies=self.ledger()._rookies,
            rookie_year_one_allocation=25, rookie_total_allocation=100))
        inputs = dict(expected_revision=0, draft_round=2, overall_pick=40,
                      prospects=(self.prospect('a', 10),), team_needs=[])
        return store, StoredLedger(store, 'a'), inputs

    def test_durable_scouting_restart_recall_and_story_history(self):
        import json, tempfile
        from franchise.draft import DraftScouting
        from franchise.store import FranchiseStore, StoredLedger
        with tempfile.TemporaryDirectory() as directory:
            store, ledger, inputs = self.durable_scouting(directory)
            choice = lambda _: json.dumps({'action':'recommend', 'player_id':'a', 'reason':'Observed production', 'uncertainty':'Targets unknown'})
            first = DraftScouting(ledger, access_check=lambda: None).recommend('first', choice, **inputs)
            reopened = StoredLedger(FranchiseStore(store.path), 'a')
            def forbidden(_):
                raise AssertionError('Restart retry must not regenerate advice')
            session = DraftScouting(reopened, access_check=lambda: None)
            self.assertEqual(session.recommend('first', forbidden, **inputs), first)
            seen = []
            def next_choice(context):
                seen.append(context)
                return choice(context)
            session.recommend('second', next_choice, **inputs)
            self.assertEqual(seen[0]['history'][0]['request_id'], 'first')
            self.assertEqual([item['request_id'] for item in reopened.scouting_history()], ['first', 'second'])
            self.assertEqual(store.load_team('a').revision, 0)
            self.assertEqual(store.load_team('a').financial_snapshot()['signed_players'], [])

    def test_concurrent_scouting_history_and_tampered_revision_reject(self):
        import json, sqlite3, tempfile
        from franchise.draft import DraftScouting
        with tempfile.TemporaryDirectory() as directory:
            store, ledger, inputs = self.durable_scouting(directory)
            choice = lambda _: json.dumps({'action':'defer', 'player_id':None, 'reason':'Need more evidence', 'uncertainty':'Targets unknown'})
            session = DraftScouting(ledger, access_check=lambda: None)
            def concurrent(context):
                DraftScouting(ledger, access_check=lambda: None).recommend('other', choice, **inputs)
                return choice(context)
            with self.assertRaisesRegex(Rejected, 'evidence changed'):
                session.recommend('stale', concurrent, **inputs)
            self.assertEqual([item['request_id'] for item in ledger.scouting_history()], ['other'])
            from contextlib import closing
            with closing(sqlite3.connect(store.path)) as db:
                row = db.execute("SELECT id,payload FROM events WHERE kind='draft_scouting'").fetchone()
                payload = json.loads(row[1])
                payload['event']['evidence']['financial_revision'] = 99
                db.execute('UPDATE events SET payload=? WHERE id=?', (json.dumps(payload), row[0]))
                db.commit()
            with self.assertRaises(Rejected):
                store.load_team('a')

    def test_recorded_scouting_evidence_revalidates_on_database_replay(self):
        import json,sqlite3,tempfile
        from contextlib import closing
        from franchise.draft import DraftScouting
        for scenario in ('duplicate','foreign','opportunities','missing_counters'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                store,ledger,inputs=self.durable_scouting(directory)
                DraftScouting(ledger,access_check=lambda:None).recommend('advice',lambda _:json.dumps(
                    {'action':'recommend','player_id':'a','reason':'Observed production','uncertainty':'Targets unknown'}),**inputs)
                with closing(sqlite3.connect(store.path)) as db:
                    row=db.execute("SELECT id,payload FROM events WHERE kind='draft_scouting'").fetchone()
                    payload=json.loads(row[1])
                    windows=payload['event']['evidence']['prospects'][0]['performance']
                    if scenario == 'duplicate': windows.append(windows[0])
                    if scenario == 'foreign': windows[0]['player_id']='b'
                    if scenario == 'opportunities':
                        windows[0]['observations']['targets']={'value':1,'source':'fixture','unavailable_reason':None}
                    if scenario == 'missing_counters': windows[0]['missing_counters']=[]
                    db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),row[0]))
                    db.commit()
                with self.assertRaises(ValueError): store.load_team('a')

    def test_initialized_draft_personality_stays_consistent_with_franchise(self):
        import tempfile,json
        from pathlib import Path
        from dataclasses import replace
        from franchise.books import OpeningBooks
        from franchise.store import FranchiseStore,StoredLedger
        from franchise.draft import DraftScouting
        with tempfile.TemporaryDirectory() as directory:
            store=FranchiseStore(Path(directory)/'state.sqlite')
            store.create_franchise({'a':Ledger.from_opening(OpeningBooks(),cap=20,roster_reserve=0,
                max_bonus_years=5,veteran_minimums={},rookies=self.ledger()._rookies,
                rookie_year_one_allocation=25,rookie_total_allocation=100)},seed='draft personality fixture')
            ledger=StoredLedger(store,'a')
            original=store.player_context('a','a')['personality']
            prospect=replace(self.prospect('a',10),personality=original,personality_source=original['source'])
            inputs=dict(expected_revision=0,draft_round=2,overall_pick=40,prospects=(prospect,),team_needs=[])
            choice=lambda _:json.dumps({'action':'recommend','player_id':'a','reason':'Production and saved priorities',
                                       'uncertainty':'Targets unknown'})
            reply=DraftScouting(ledger,access_check=lambda:None).recommend('saved',choice,**inputs)
            self.assertEqual(reply['evidence']['prospects'][0]['personality'],original)
            changed=replace(prospect,personality={**original,'money':0.01})
            calls=[]
            with self.assertRaisesRegex(Rejected,'saved player personality'):
                DraftScouting(ledger,access_check=lambda:None).recommend('changed',lambda c:calls.append(c),
                    **{**inputs,'prospects':(changed,)})
            self.assertEqual(calls,[])
            reopened=FranchiseStore(store.path)
            self.assertEqual(reopened.player_context('a','a')['personality'],original)
            self.assertEqual(reopened.load_team('a').revision,0)
            import sqlite3
            from contextlib import closing
            with closing(sqlite3.connect(store.path)) as db:
                row=db.execute("SELECT id,payload FROM events WHERE kind='draft_scouting'").fetchone()
                payload=json.loads(row[1])
                payload['event']['evidence']['prospects'][0]['personality']['money']=0.01
                db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(payload),row[0]))
                db.commit()
            with self.assertRaisesRegex(Rejected,'saved player personality'):
                reopened.load_team('a')

    def test_legacy_scouting_before_actor_binding_replays_chronologically(self):
        import tempfile,json
        from franchise.draft import DraftScouting
        from franchise.store import FranchiseStore
        with tempfile.TemporaryDirectory() as directory:
            store,ledger,inputs=self.durable_scouting(directory)
            reply=DraftScouting(ledger,access_check=lambda:None).recommend('legacy',lambda _:json.dumps(
                {'action':'defer','player_id':None,'reason':'More evidence needed','uncertainty':'Targets unknown'}),**inputs)
            store.bind_actor('a','a',{'money':0.8},{'trust':0.5},access_check=lambda:None)
            reopened=FranchiseStore(store.path)
            self.assertEqual(reopened.recalled_scouting('a','legacy'),reply)
            self.assertEqual(reopened.player_context('a','a')['personality'],{'money':0.8})
