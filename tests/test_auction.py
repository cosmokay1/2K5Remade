"""Offline bidding rounds: no wall clock, inference, game assets or game writes."""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from franchise.auction import LocalAuction
from franchise.books import OpeningBooks
from franchise.bridge import Bridge, ResponseTooLarge
from franchise.cap import Ledger, Offer, Rejected
from franchise.control import AccessDisabled
from franchise.local_runtime import LocalRulesRuntime
from franchise.promises import PromiseGoal
from franchise.store import FranchiseStore


class AuctionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.store = FranchiseStore(self.root / 'league.sqlite')
        self.store.create_franchise({team: Ledger.from_opening(OpeningBooks(), cap=300,
            roster_reserve=0, max_bonus_years=5, veteran_minimums={'p': (1,) * 5, 'q': (1,) * 5})
            for team in ('a', 'b')}, seed='auction-test')
        self.config = dict(format=1, enabled=True, signing_enabled=False, team_id='a',
            quotes={p: dict(offer=Offer(p, (100,), 0).to_dict(), source='Authored current-scale asking terms') for p in ('p', 'q')},
            auction=dict(id='year-one-fa', opens_at=4, closes_at=7, player_ids=['p', 'q'], source='Authored verified round clock'))
        self.path = self.root / 'local.json'; self.write_config()
        self.tick = 4
        self.book = self.reopen()

    def write_config(self):
        self.path.write_text(json.dumps(self.config))

    def runtime(self):
        return LocalRulesRuntime(self.path, clock=lambda: self.tick)

    def reopen(self):
        return LocalAuction(FranchiseStore(self.store.path), self.runtime())

    def bid(self, team='a', request='bid', player='p', amount=100, **kwargs):
        return self.book.bid(team, request, Offer(player, (amount,), 0), self.store.load_team(team).revision, **kwargs)

    def test_bid_waits_until_closing_then_records_consent_without_signing(self):
        before = self.store.load_team('a').financial_snapshot()
        result = self.bid()
        self.assertEqual(result['state'], 'pending')
        self.assertFalse(result['write_authorized'])
        self.assertEqual(self.store.negotiation_history('a', 'p'), [])
        with self.assertRaises(Rejected): self.book.resolve()
        self.assertEqual(self.book.status('a')['earmarked_cap'], 100)
        self.tick = 7
        result = self.book.resolve()
        self.assertEqual(result['outcomes']['p']['team_id'], 'a')
        self.assertFalse(result['outcomes']['p']['write_authorized'])
        self.assertEqual(self.store.load_team('a').financial_snapshot(), before)
        history = self.store.negotiation_history('a', 'p')
        self.assertEqual(history[-1]['outcome'], 'accepted_proposal')
        self.assertEqual(history[-1]['auction']['bid_request_id'], 'bid')

    def test_real_competing_bids_choose_value_and_loser_earmark_is_released(self):
        self.bid('a', 'a-bid')
        self.bid('b', 'b-bid', amount=120)
        self.assertEqual(self.book.status('a')['bids']['p']['state'], 'pending')
        self.tick = 7
        result = self.book.resolve()
        self.assertEqual(result['outcomes']['p']['team_id'], 'b')
        self.assertEqual(self.book.status('a')['bids']['p']['state'], 'not_selected')
        self.assertEqual(self.book.status('a')['earmarked_cap'], 0)
        self.assertEqual(self.book.status('b')['earmarked_cap'], 120)
        self.assertEqual(self.store.load_team('b').charges, (0,))

    def test_security_breaks_equal_annual_value_ties(self):
        self.bid('a', 'early')
        self.book.bid('b', 'secure', Offer('p', (80,), 20), 0)
        self.tick = 7
        self.assertEqual(self.book.resolve()['outcomes']['p']['team_id'], 'b')

    def test_exact_tie_prefers_first_recorded_bid_not_client_request_id(self):
        self.bid('a', 'z-earlier')
        self.bid('b', 'a-later')
        self.tick = 7
        self.assertEqual(self.book.resolve()['outcomes']['p']['team_id'], 'a')

    def test_retries_restart_and_resolution_are_idempotent(self):
        first = self.bid()
        self.book = self.reopen()
        self.assertEqual(self.bid(), first)
        self.tick = 7
        selected = self.book.resolve()
        self.book = self.reopen()
        self.assertEqual(self.book.resolve(), selected)
        self.assertEqual(len(self.store.negotiation_history('a', 'p')), 1)
        self.assertEqual(self.bid(), first)  # Original pending receipt, no new bid.
        with self.assertRaises(Rejected): self.bid(amount=110)

    def test_pending_bids_earmark_combined_room_and_withdrawal_releases_it(self):
        self.store.update_budget('a', cap=150, roster_reserve=0, expected_revision=0)
        self.bid(request='p')
        with self.assertRaises(Rejected): self.bid(request='q', player='q')
        result = self.book.withdraw('a', 'p', 'withdraw')
        self.assertEqual(result['state'], 'withdrawn')
        self.assertEqual(self.book.withdraw('a', 'p', 'withdraw'), result)
        self.assertEqual(self.bid(request='q', player='q')['state'], 'pending')
        self.assertEqual(self.store.load_team('a').charges, (0,))
        self.tick = 7
        self.assertEqual(self.book.resolve()['outcomes']['p']['state'], 'unsigned')

    def test_lowball_revokes_pending_bid_and_improved_offer_cannot_erase_it(self):
        self.bid(request='strong')
        result = self.bid(request='insult', amount=50)
        self.assertEqual(result['reaction'], 'offended')
        respect = self.store.player_context('a', 'p')['relationships']['respect']
        self.assertEqual(self.bid(request='insult', amount=50), result)
        self.assertEqual(self.store.player_context('a', 'p')['relationships']['respect'], respect)
        self.book = self.reopen()
        self.assertEqual(self.bid(request='improved', amount=150)['state'], 'player_rejected')
        self.assertEqual(self.book.status('a')['earmarked_cap'], 0)
        self.tick = 7
        self.assertEqual(self.book.resolve()['outcomes']['p']['state'], 'unsigned')
        self.assertEqual(len(self.store.negotiation_history('a', 'p')), 1)

    def test_patience_counts_submissions_across_restarts(self):
        patience = self.store.player_context('a', 'p')['personality']['patience']
        rounds = 2 + int(patience >= 1/3) + int(patience >= 2/3)
        for i in range(rounds):
            self.assertEqual(self.bid(request=str(i), amount=80)['state'], 'counteroffer')
            self.book = self.reopen()
        self.assertEqual(self.bid(request='one-too-many', amount=100)['state'], 'player_rejected')

    def test_changed_money_or_ownership_is_rechecked_at_resolution(self):
        self.bid()
        self.store.update_budget('a', cap=80, roster_reserve=0, expected_revision=0)
        self.tick = 7
        self.assertEqual(self.book.resolve()['outcomes']['p']['state'], 'unsigned')
        self.assertEqual(self.store.load_team('a').charges, (0,))

    def test_resolution_selects_only_affordable_subset_after_spending(self):
        self.bid(request='p')
        self.bid(request='q', player='q')
        self.store.update_budget('a', cap=150, roster_reserve=0, expected_revision=0)
        self.tick = 7
        result = self.book.resolve()
        self.assertEqual(result['outcomes']['p']['state'], 'selected')
        self.assertEqual(result['outcomes']['q']['state'], 'unsigned')
        self.assertEqual(self.book.status('a')['earmarked_cap'], 100)

    def test_clock_and_deadline_cannot_be_reset_by_restarting_or_rewriting_policy(self):
        self.bid()
        self.tick = 7
        with self.assertRaises(Rejected): self.bid(request='too-late')
        with self.assertRaises(Rejected): self.book.withdraw('a', 'p', 'late-withdraw')
        self.book.resolve()
        self.tick = 6
        with self.assertRaises(Rejected): self.book.resolve()
        self.config['auction']['closes_at'] = 10
        self.write_config()
        with self.assertRaises(Rejected): self.reopen()

    def test_explicit_signing_enablement_does_not_reset_auction(self):
        self.bid()
        self.tick = 7
        chosen = self.book.resolve()['outcomes']['p']['proposal_request_id']
        with self.assertRaises(AccessDisabled):
            self.store.commit_accepted_proposal('a', chosen, 'sign', 0,
                access_check=lambda: self.book.runtime.check(signing=True))
        self.config['signing_enabled'] = True; self.write_config(); self.book = self.reopen()
        receipt = self.store.commit_accepted_proposal('a', chosen, 'sign', 0,
            access_check=lambda: self.book.runtime.check(signing=True))
        self.assertEqual(receipt.charges, (100,))
        self.assertEqual(self.store.load_team('a').charges, (100,))
        self.assertEqual(self.book.status('a')['earmarked_cap'], 0)
        self.assertEqual(self.store.commit_accepted_proposal('a', chosen, 'sign', 0,
            access_check=lambda: self.book.runtime.check(signing=True)), receipt)

    def test_receipt_failure_and_disconnect_roll_back_decisions_and_reactions(self):
        def fail(_): raise ResponseTooLarge()
        with self.assertRaises(ResponseTooLarge):
            self.book.bid('a', 'insult', Offer('p', (50,), 0), 0, receipt_check=fail)
        self.assertEqual(self.store.negotiation_history('a', 'p'), [])
        self.bid()
        self.tick = 7
        with self.assertRaises(ResponseTooLarge): self.book.resolve(receipt_check=fail)
        self.assertEqual(self.store.negotiation_history('a', 'p'), [])
        self.assertEqual(self.book.status('a')['state'], 'awaiting_resolution')
        self.book.access_check = lambda: False
        with self.assertRaises(AccessDisabled): self.book.resolve()
        self.assertEqual(self.store.negotiation_history('a', 'p'), [])

    def test_policy_revocation_or_clock_change_during_resolution_rolls_back(self):
        self.bid()
        self.tick = 7
        original = self.book._story
        def change(*args, **kwargs):
            result = original(*args, **kwargs)
            self.tick = 8
            return result
        with patch.object(self.book, '_story', change):
            with self.assertRaises(Rejected): self.book.resolve()
        self.assertEqual(self.store.negotiation_history('a', 'p'), [])
        self.config['enabled'] = False; self.write_config()
        with self.assertRaises(AccessDisabled): self.book.resolve()

    def test_simultaneous_bids_cannot_overcommit_earmarks(self):
        self.store.update_budget('a', cap=150, roster_reserve=0, expected_revision=0)
        def bid(player):
            try: return self.bid(request=player, player=player)['state']
            except Rejected: return 'rejected'
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(bid, ('p', 'q'))), ['pending', 'rejected'])
        self.assertEqual(self.book.status('a')['earmarked_cap'], 100)

    def test_promises_survive_pending_bid_and_selected_proposal(self):
        goal = PromiseGoal('starts', 'starts', 10, 80, 'next-season', 'Authored proposal')
        self.bid(promise_goals=(goal,))
        self.tick = 7
        chosen = self.book.resolve()['outcomes']['p']['proposal_request_id']
        event = self.store.negotiation_history('a', 'p')[-1]
        self.assertEqual(event['request_id'], chosen)
        self.assertEqual(event['promise_goals'][0]['goal_id'], 'starts')

    def test_bridge_advertises_auction_and_blocks_instant_negotiation_bypass(self):
        runtime = self.runtime()
        bridge = Bridge(self.store, provider=runtime, access_check=runtime.check)
        hello = bridge.handle(dict(protocol=1, operation='hello', request_id='hello'))
        self.assertIn('auction_bid', hello['result']['operations'])
        request = dict(protocol=1, operation='auction_bid', request_id='bid', team_id='a',
                       offer=Offer('p', (100,), 0).to_dict(), expected_revision=0)
        self.assertEqual(bridge.handle(request)['result']['state'], 'pending')
        self.assertEqual(bridge.handle({**request, 'closes_at': 4})['error'], 'invalid_request')
        self.assertEqual(bridge.handle({**request, 'team_id': 'b'})['error'], 'state_rejected')
        normal = dict(protocol=1, operation='negotiate_proposal', request_id='bypass', team_id='a',
                      offer=request['offer'], expected_revision=0, timeout_ms=1000,
                      personality={}, relationships={}, performance={})
        self.assertEqual(bridge.handle(normal)['error'], 'state_rejected')
        resolve = dict(protocol=1, operation='auction_resolve', request_id='resolve')
        self.assertEqual(bridge.handle(resolve)['error'], 'state_rejected')
        self.tick = 7
        self.assertEqual(bridge.handle(resolve)['result']['state'], 'resolved')

    def test_native_encoded_winner_uses_existing_saved_signing_and_reload(self):
        import hashlib
        from franchise import guest_signing
        from franchise.books import ActiveContract
        from franchise.cash import CashObligation
        from franchise.guest_contracts import GuestContractTerms
        from tools.inspect_franchise_save import TEAMS
        from tools.franchise_finance_state import saved_finance_state
        from tools.franchise_identity_state import saved_identity_state
        from tests.test_guest_signing_journal import GuestSigningJournalTests
        fixture = GuestSigningJournalTests(); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        store = FranchiseStore(self.root / 'native-journal.sqlite')
        owned = fixture.bindings['players'][0]['player_id']
        opening = GuestContractTerms(829, 4, 1, 2).to_offer(owned)
        for team in TEAMS:
            contracts = (ActiveContract(opening, 'Authored opening contract'),) if team == '49ers' else ()
            floors = {owned: (1000,) * 15, fixture.player: (1000,) * 15} if team == '49ers' else {}
            store.create_team(team, Ledger.from_opening(OpeningBooks(contracts=contracts),
                cap=80500000, roster_reserve=0, max_bonus_years=5, veteran_minimums=floors))
            cash = (CashObligation('contract:' + owned, owned, sum(opening.salaries) + opening.signing_bonus,
                                   0, 'Authored unpaid cash'),) if team == '49ers' else ()
            store.initialize_cash(team, cash, source='Authored complete inventory')
        store.bind_actor('49ers', fixture.player, {'patience': .5, 'security': .5},
                         {'respect': .5, 'trust': .5}, access_check=lambda: None)
        self.config.update(team_id='49ers', signing_enabled=True,
            quotes={fixture.player: dict(offer=fixture.offer.to_dict(), source='Authored native asking terms')})
        self.config['auction']['player_ids'] = [fixture.player]
        self.write_config()
        book = LocalAuction(store, self.runtime())
        revision = store.load_team('49ers').revision
        book.bid('49ers', 'native-bid', fixture.offer, revision, contract_format='original_fxg_v1')
        self.tick = 7
        choice = book.resolve()['outcomes'][fixture.player]['proposal_request_id']
        before = store.load_team('49ers').financial_snapshot()
        digest = lambda b: hashlib.sha256(b).hexdigest()
        prepared = guest_signing.prepare(store, '49ers', choice, 'native-journal', bindings=fixture.bindings,
            before_payload=fixture.before, guest_offer=fixture.raw, expected_revision=revision,
            expected_before_sha256=digest(fixture.before), access_check=lambda: book.runtime.check(signing=True),
            live_projection={'finance': digest(saved_finance_state(fixture.before)),
                             'identity': digest(saved_identity_state(fixture.before))})
        self.assertFalse(prepared['write_authorized'])
        self.assertEqual(store.load_team('49ers').financial_snapshot(), before)
        receipt = guest_signing.settle(store, 'native-journal', fixture.after,
                                      access_check=lambda: book.runtime.check(signing=True))
        self.assertEqual(receipt.charges, (4766000, 3523000))
        reopened = FranchiseStore(store.path)
        self.assertEqual(reopened.load_team('49ers').revision, revision + 1)
        self.assertEqual(guest_signing.settle(reopened, 'native-journal', fixture.after,
            access_check=lambda: book.runtime.check(signing=True)), receipt)
        self.assertEqual(book.status('49ers')['earmarked_cap'], 0)

    def test_invalid_format_or_revision_does_not_leave_a_poisoned_bid(self):
        for fmt in ('', False, 'unsupported'):
            with self.assertRaises(ValueError):
                self.bid(contract_format=fmt)
        with self.assertRaises(ValueError):
            self.book.bid('a', 'bad-revision', Offer('p', (100,), 0), True)
        self.assertEqual(self.book.status('a')['bids'], {})

    def test_later_nonoverlapping_round_preserves_respect_but_allows_new_talks(self):
        self.bid(request='insult', amount=50)
        respect = self.store.player_context('a', 'p')['relationships']['respect']
        self.tick = 7; self.book.resolve()
        self.config['auction'].update(id='next-round', opens_at=8, closes_at=10)
        self.write_config(); self.tick = 8; self.book = self.reopen()
        self.assertEqual(self.bid(request='new-round')['state'], 'pending')
        self.assertEqual(self.store.player_context('a', 'p')['relationships']['respect'], respect)

    def test_adjacent_round_does_not_clear_a_recent_lowball(self):
        self.tick = 6
        self.bid(request='late-insult', amount=50)
        self.tick = 7; self.book.resolve()
        self.config['auction'].update(id='adjacent-round', opens_at=7, closes_at=9)
        self.write_config(); self.book = self.reopen()
        self.assertEqual(self.bid(request='too-soon', amount=150)['state'], 'player_rejected')

    def test_revocation_at_final_receipt_rolls_back_selected_proposal(self):
        self.bid(); self.tick = 7
        def revoke(_):
            self.config['enabled'] = False
            self.write_config()
        with self.assertRaises(AccessDisabled): self.book.resolve(receipt_check=revoke)
        self.assertEqual(self.store.negotiation_history('a', 'p'), [])
        self.assertEqual(self.store.load_team('a').charges, (0,))
