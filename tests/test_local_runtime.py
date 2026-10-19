"""Authored offline local-runtime integration and persistence checks."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from franchise.books import OpeningBooks
from franchise.bridge import Bridge
from franchise.cap import Ledger, Offer
from franchise.control import AccessDisabled
from franchise.guest_contracts import GuestContractTerms
from franchise.local_runtime import LocalRulesRuntime, saved_calendar_tick
from franchise.performance import Observation, PerformanceEvidence
from franchise.store import FranchiseStore


class LocalRuntimeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.path = self.root / 'local.json'
        self.config = dict(format=1, enabled=True, signing_enabled=False, team_id='club',
                           quotes={'p': dict(offer=Offer('p', (100,), 0).to_dict(),
                                             source='Authored baseline, current money scale')})
        self.path.write_text(json.dumps(self.config))
        self.tick = 4
        self.store = FranchiseStore(self.root / 'ledger.sqlite')
        self.store.create_team('club', Ledger.from_opening(OpeningBooks(), cap=1000,
            roster_reserve=0, max_bonus_years=5, veteran_minimums={'p': (1,)}))

    def runtime(self):
        return LocalRulesRuntime(self.path, clock=lambda: self.tick)

    def bridge(self):
        runtime = self.runtime()
        return Bridge(self.store, provider=runtime, access_check=runtime.check)

    def request(self, **changes):
        return {**dict(protocol=1, request_id='one', operation='negotiate_proposal', team_id='club',
            offer=Offer('p', (100,), 0).to_dict(), expected_revision=0, timeout_ms=1000,
            personality={'money': .5, 'patience': .5}, performance={},
            relationships={'trust': .5, 'respect': .5}), **changes}

    def send(self, bridge=None, **changes):
        reply = (bridge or self.bridge()).handle(self.request(**changes))
        self.assertIsNone(reply['error'], reply)
        return reply['result']

    def write_config(self):
        self.path.write_text(json.dumps(self.config))

    def test_handshake_is_explicit_local_and_reports_ai_off(self):
        reply = self.bridge().handle(dict(protocol=1, request_id='hello', operation='hello'))
        self.assertIsNone(reply['error'])
        self.assertFalse(reply['result']['ai_enabled'])
        self.assertTrue(reply['result']['negotiation_enabled'])
        self.assertEqual(reply['result']['decision_mode'], 'local-rules')
        self.assertIn('negotiate_proposal', reply['result']['operations'])

    def test_acceptance_records_price_without_signing_or_cloud(self):
        with patch('franchise.vertex_provider.VertexProvider.__init__', side_effect=AssertionError('No SDK construction')):
            result = self.send()
        self.assertEqual(result['outcome'], 'accepted_proposal')
        self.assertEqual(result['local_rules']['asking_offer'], self.config['quotes']['p']['offer'])
        self.assertEqual(self.store.load_team('club').charges, (0,))
        self.assertEqual(self.store.negotiation_history('club', 'p'), [result])

    def test_lowball_survives_restart_and_only_saved_progress_reopens(self):
        low = self.send(offer=Offer('p', (50,), 0).to_dict())
        self.assertEqual(low['reaction'], 'offended')
        original = self.store.player_context('club', 'p')['relationships']['respect']
        retry = self.send(offer=Offer('p', (50,), 0).to_dict())
        self.assertEqual(low, retry)
        self.assertEqual(original, self.store.player_context('club', 'p')['relationships']['respect'])
        for tick in (4, 5):
            self.tick = tick
            self.assertEqual(self.send(request_id=f'next-{tick}')['outcome'], 'player_rejected')
        self.tick = 6
        result = self.send(request_id='new-window')
        self.assertEqual(result['outcome'], 'accepted_proposal')
        self.assertEqual(result['local_rules']['history_start'], 3)
        self.tick = 5
        self.assertEqual(self.bridge().handle(self.request(request_id='rollback'))['error'], 'state_rejected')

    def test_patience_cannot_be_reset_by_restarting_or_changing_policy(self):
        for i in range(3):
            result = self.send(request_id=str(i), offer=Offer('p', (80,), 0).to_dict())
            self.assertEqual(result['outcome'], 'counteroffer')
        self.config['quotes']['p']['source'] += ' amended'
        self.write_config()
        result = self.send(request_id='four')
        self.assertEqual(result['outcome'], 'player_rejected')
        self.tick += 2
        self.assertEqual(self.send(request_id='later')['outcome'], 'accepted_proposal')

    def test_signing_is_explicit_and_financial_receipt_replays_once(self):
        self.assertEqual(self.bridge().handle(self.request(operation='negotiate'))['error'], 'ai_disabled')
        self.config['signing_enabled'] = True
        self.write_config()
        result = self.send(operation='negotiate')
        self.assertEqual(result['outcome'], 'signed')
        self.assertEqual(self.send(operation='negotiate'), result)
        self.assertEqual(self.store.load_team('club').charges, (100,))
        reopened = FranchiseStore(self.store.path)
        self.assertEqual(reopened.negotiation_history('club', 'p'), [result])
        self.assertEqual(reopened.load_team('club').charges, (100,))

    def test_local_agreement_never_overrides_cap(self):
        self.config['quotes']['p']['offer'] = Offer('p', (1100,), 0).to_dict()
        self.config['signing_enabled'] = True
        self.write_config()
        result = self.send(operation='negotiate', offer=Offer('p', (1100,), 0).to_dict())
        self.assertEqual(result['action'], 'accept')
        self.assertEqual(result['outcome'], 'accounting_rejected')
        self.assertEqual(self.store.load_team('club').charges, (0,))

    def test_missing_quote_other_team_and_client_history_cursor_reject(self):
        for change in (dict(team_id='other'), dict(offer=Offer('unknown', (100,), 0).to_dict()),
                       dict(history_start=100), dict(local_rules={'tick': 100})):
            reply = self.bridge().handle({**self.request(), **change})
            self.assertIsNotNone(reply['error'])
        self.assertEqual(self.store.negotiation_history('club', 'p'), [])

    def test_disable_delete_or_edit_revokes_existing_service(self):
        for mutation in ('disable', 'edit', 'delete'):
            self.write_config()
            bridge = self.bridge()
            if mutation == 'disable':
                data = copy.deepcopy(self.config); data['enabled'] = False
                self.path.write_text(json.dumps(data))
            elif mutation == 'edit': self.path.write_text(self.path.read_text() + '\n')
            else: self.path.unlink()
            self.assertEqual(bridge.handle(self.request())['error'], 'ai_disabled')
        self.assertEqual(self.store.negotiation_history('club', 'p'), [])

    def test_clock_change_mid_decision_prevents_persistence(self):
        runtime = self.runtime()
        original = LocalRulesRuntime.evaluate
        def change_clock(session, context):
            reply = original(session, context)
            self.tick += 1
            return reply
        with patch.object(LocalRulesRuntime, 'evaluate', change_clock):
            reply = Bridge(self.store, provider=runtime, access_check=runtime.check).handle(self.request())
        self.assertEqual(reply['error'], 'state_rejected')
        self.assertEqual(self.store.negotiation_history('club', 'p'), [])

    def performance(self, yards=1000, games=10, complete=True):
        return PerformanceEvidence('p', 'last-completed-season', 'fast_sim',
            (Observation('games', games, 'Authored complete season'),
             Observation('receiving_yards', yards, 'Authored complete season')),
            'Authored fixture', complete_window=complete).to_context()

    def price_config(self, **changes):
        self.config['quotes']['p'].update(performance=self.performance(**changes),
            adjustment=dict(counter='receiving_yards', reference_per_game=80, minimum_games=8))
        self.write_config()

    def test_server_performance_drives_bounded_price_not_client_stats(self):
        self.price_config()
        result = self.send()
        self.assertEqual(result['counter']['salaries'], [125])
        self.assertEqual(result['local_rules']['performance_factor'], [5, 4])
        self.assertEqual(result['local_rules']['performance'], self.performance())
        self.tick += 2
        result = self.send(request_id='client-cannot-reprice', performance=self.performance(yards=0))
        self.assertEqual(result['counter']['salaries'], [125])

    def test_missing_or_small_samples_use_anchor_and_partial_season_is_rejected(self):
        self.price_config(games=7)
        result = self.send()
        self.assertEqual(result['local_rules']['performance_factor'], [1, 1])
        self.price_config(complete=False)
        with self.assertRaises(ValueError): self.runtime()

    def test_guest_pricing_decodes_exact_scaled_salary_and_bonus(self):
        terms = GuestContractTerms(1200, 4, 2, 3)
        self.config['quotes']['p']['offer'] = terms.to_offer('p', contract_format='softdrink_fxg_v1').to_dict()
        self.price_config()
        runtime = self.runtime().for_team('club')
        from tests.test_local_negotiation import LocalNegotiationTests
        context = LocalNegotiationTests().context(terms.to_offer('p', contract_format='softdrink_fxg_v1'),
                                                contract_format='softdrink_fxg_v1')
        _, evidence = runtime.evaluate(context)
        expected = GuestContractTerms(1500, 4, 2, 3).to_offer('p', contract_format='softdrink_fxg_v1')
        self.assertEqual(evidence['asking_offer'], expected.to_dict())

    def test_saved_clock_validates_phase_horizon_and_never_uses_wall_time(self):
        calendar = dict(season_index=2, phase_01_raw=8, step_04_raw=18, step_05_raw=3)
        with patch('tools.inspect_franchise_calendar.inspect_calendar', return_value=calendar):
            self.assertEqual(saved_calendar_tick(lambda: b'fixture'), 71)
            for changes in (dict(phase_01_raw=0), dict(step_04_raw=17), dict(step_05_raw=19)):
                with patch('tools.inspect_franchise_calendar.inspect_calendar', return_value={**calendar, **changes}):
                    with self.assertRaises(ValueError): saved_calendar_tick(lambda: b'fixture')

    def test_sidecar_cli_constructs_local_mode_without_google_or_budget(self):
        from franchise.sidecar import main
        fake_payload = b'authored'
        captured = []
        def serve(bridge, _reader, _writer):
            captured.append(bridge.handle(dict(protocol=1, operation='hello', request_id='hello')))
        bindings = self.root / 'bindings.json'; bindings.write_text('{}')
        argv = ['sidecar', '--database', str(self.store.path), '--provider', 'local-rules',
                '--local-config', str(self.path), '--guest-save', 'fixture', '--guest-bindings', str(bindings)]
        with patch('sys.argv', argv), patch('franchise.sidecar.read_guest_save', return_value=fake_payload), \
             patch('tools.franchise_snapshot_bindings.resolve_bindings'), \
             patch('franchise.local_runtime.saved_calendar_tick', return_value=4), \
             patch('franchise.sidecar.serve', serve), \
             patch('franchise.vertex_provider.VertexProvider.__init__', side_effect=AssertionError('No Google SDK')), \
             patch('franchise.runtime_budget.runtime_request_budget', side_effect=AssertionError('No budget')):
            main()
        self.assertEqual(captured[0]['result']['decision_mode'], 'local-rules')
        self.assertFalse(captured[0]['result']['ai_enabled'])
        with patch('sys.argv', argv + ['--ai-request-limit', '1']), patch('sys.stderr', io.StringIO()):
            with self.assertRaises(SystemExit) as error: main()
        self.assertEqual(error.exception.code, 2)

    def test_local_proposal_journal_settlement_and_reload_with_authored_save(self):
        import hashlib
        from franchise.cash import CashObligation
        from franchise.books import ActiveContract
        from tools.inspect_franchise_save import TEAMS
        from tools.franchise_finance_state import saved_finance_state
        from tools.franchise_identity_state import saved_identity_state
        from tests.test_guest_signing_journal import GuestSigningJournalTests
        fixture = GuestSigningJournalTests(); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        store = FranchiseStore(self.root / 'journal.sqlite')
        owned = fixture.bindings['players'][0]['player_id']
        opening = GuestContractTerms(829, 4, 1, 2).to_offer(owned)
        for team in TEAMS:
            contracts = (ActiveContract(opening, 'Authored opening contract'),) if team == '49ers' else ()
            floors = {owned: (1000,) * 15, fixture.player: (1000,) * 15} if team == '49ers' else {}
            store.create_team(team, Ledger.from_opening(OpeningBooks(contracts=contracts),
                cap=80500000, roster_reserve=0, max_bonus_years=5, veteran_minimums=floors))
            cash = (CashObligation('contract:' + owned, owned,
                sum(opening.salaries) + opening.signing_bonus, 0, 'Authored unpaid cash'),) if team == '49ers' else ()
            store.initialize_cash(team, cash, source='Authored complete inventory')
        revision = store.load_team('49ers').revision
        self.config.update(team_id='49ers', signing_enabled=True,
            quotes={fixture.player: dict(offer=fixture.offer.to_dict(), source='Authored asking contract')})
        self.write_config()
        runtime = self.runtime()
        current = fixture.before
        bridge = Bridge(store, provider=runtime, access_check=runtime.check,
            guest_snapshot=(fixture.bindings, fixture.before), guest_signing_reader=lambda: current)
        proposal = bridge.handle({**self.request(), 'team_id': '49ers', 'request_id': 'proposal',
            'offer': fixture.offer.to_dict(), 'contract_format': 'original_fxg_v1',
            'expected_revision': revision})
        self.assertIsNone(proposal['error'], proposal)
        self.assertEqual(proposal['result']['outcome'], 'accepted_proposal')
        before = store.load_team('49ers').financial_snapshot()
        digest = lambda data: hashlib.sha256(data).hexdigest()
        prepare = dict(protocol=1, request_id='journal', operation='guest_signing_prepare', timeout_ms=5000,
            team_id='49ers', proposal_request_id='proposal', guest_offer=fixture.raw,
            expected_revision=revision, expected_before_sha256=digest(current),
            live_finance_sha256=digest(saved_finance_state(current)),
            live_identity_sha256=digest(saved_identity_state(current)))
        response = bridge.handle(prepare)
        self.assertIsNone(response['error'], response)
        self.assertFalse(response['result']['write_authorized'])
        self.assertEqual(store.load_team('49ers').financial_snapshot(), before)
        current = fixture.after  # Authored after-save, never a game save write.
        confirm = dict(protocol=1, request_id='confirm', operation='guest_signing_confirm',
                       timeout_ms=5000, journal_request_id='journal', expected_after_sha256=digest(current))
        response = bridge.handle(confirm)
        self.assertIsNone(response['error'], response)
        self.assertEqual(response['result']['charges'], [4766000, 3523000])
        self.assertEqual(bridge.handle(confirm), response)
        reopened = FranchiseStore(store.path)
        self.assertEqual(reopened.load_team('49ers').revision, revision + 1)
        history = reopened.negotiation_history('49ers', fixture.player)
        self.assertIn('local_rules', history[0])
        self.assertEqual(history[-1]['local_rules'], history[0]['local_rules'])
        self.assertEqual(history[-1]['outcome'], 'signed')

    def test_local_active_contract_keeps_earned_salary_and_old_bonus(self):
        from fractions import Fraction
        from franchise.legacy_amendments import RULE, InSeasonAmendmentScope
        from tests.test_earned_amendment import EarnedAmendmentTests
        store = FranchiseStore(self.root / 'amendment.sqlite')
        store.create_franchise({'Giants': EarnedAmendmentTests().ledger()}, seed='local-earned-fixture')
        offer = Offer('dart', (1000000, 2000000), 2000000)
        self.config.update(team_id='Giants', signing_enabled=True,
            quotes={'dart': dict(offer=offer.to_dict(), source='Authored asking contract')})
        self.write_config()
        runtime = self.runtime()
        bridge = Bridge(store, provider=runtime, access_check=runtime.check)
        actor = store.player_context('Giants', 'dart')
        scope = InSeasonAmendmentScope(2026, 8, 17, 'Authored salary clock')
        reply = bridge.handle({**self.request(), 'team_id': 'Giants', 'offer': offer.to_dict(),
            'amendment_rule': RULE, 'amendment_scope': scope.to_dict(),
            'personality': actor['personality'], 'relationships': actor['relationships']})
        self.assertIsNone(reply['error'], reply)
        self.assertEqual(reply['result']['outcome'], 'accepted_amendment_proposal')
        self.assertEqual(store.load_team('Giants').revision, 0)
        receipt = store.commit_accepted_amendment('Giants', 'one', 'agreement', 0,
            scope=scope, access_check=lambda: runtime.check(signing=True))
        expected = Fraction(1544000 * 8 + 1000000 * 9, 17) + 3320000
        reopened = FranchiseStore(store.path)
        self.assertEqual(reopened.load_team('Giants').charges[0], expected)
        self.assertEqual(reopened.load_team('Giants').revision, 1)
        self.assertEqual(store.commit_accepted_amendment('Giants', 'one', 'agreement', 0,
            scope=scope, access_check=lambda: runtime.check(signing=True)), receipt)
