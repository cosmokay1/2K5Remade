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

    def test_concurrent_budget_change_invalidates_comparison(self):
        ledger = self.ledger()
        class ChangedAfterPreview:
            def management_context(self):
                return ledger.management_context()
            def negotiation_context(self, player):
                return ledger.negotiation_context(player)
            def preview_offer(self, offer, revision):
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
