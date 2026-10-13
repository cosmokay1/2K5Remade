from dataclasses import asdict, replace
from datetime import date
from fractions import Fraction
import unittest
from franchise.books import ActiveContract
from franchise.cap import Offer
from franchise.cash import CashObligation
from franchise.trades import EXCLUDED_TRADE_LIABILITIES, PreseasonTradeScope, calculate_preseason_trade


class PreseasonTradeTests(unittest.TestCase):
    def scope(self, when=date(2026, 6, 1), year=2026):
        return PreseasonTradeScope(year, when, date(year, 9, 10), date(year, 9, 11),
            EXCLUDED_TRADE_LIABILITIES, True, 0, True, True, 'synthetic healthy preseason assignment')

    def contract(self):
        return ActiveContract(Offer('v', (10, 20, 30), 9, (0, 20, 10)), 'synthetic original contract')

    def cash(self):
        return CashObligation('contract:v', 'v', 69, 9, 'synthetic allocated cash', (('signing_bonus', 9),))

    def plan(self, contract=None, cash=None, scope=None):
        return calculate_preseason_trade(contract or self.contract(), cash or self.cash(),
            scope=scope or self.scope(), record_id='trade:v')

    def test_independent_june_boundary_expectations_and_cash_conservation(self):
        for when, charges in ((date(2026, 6, 1), (9,)), (date(2026, 6, 2), (3, 6))):
            with self.subTest(when=when):
                plan = self.plan(scope=self.scope(when))
                self.assertEqual(plan.retained_bonus.annual_charges, charges)
                self.assertEqual(plan.buyer_contract.charges(), (10, 20, 30))
                self.assertEqual(plan.buyer_contract.offer.guaranteed_salaries, (0, 20, 10))
                self.assertEqual(plan.buyer_contract.offer.signing_bonus, 0)
                self.assertEqual((plan.seller_cash.amount, plan.seller_cash.paid), (9, 9))
                self.assertEqual((plan.buyer_cash.amount, plan.buyer_cash.paid), (60, 0))
                self.assertEqual(plan.buyer_cash.paid_components, ())
                self.assertEqual(plan.seller_cash.paid_components, self.cash().paid_components)
                self.assertEqual(plan.assigned_base, 60)
                self.assertEqual(plan.original_contract, self.contract())
                self.assertEqual(plan.original_cash, self.cash())
                self.assertIn('synthetic healthy preseason assignment', plan.buyer_contract.source)

    def test_elapsed_contract_preserves_history_and_assigns_remaining_guarantees(self):
        contract = replace(self.contract(), elapsed_years=1)
        cash = replace(self.cash(), paid=19, paid_components=(('base:0', 10), ('signing_bonus', 9)))
        plan = self.plan(contract, cash, self.scope(date(2026, 6, 2)))
        self.assertEqual(plan.retained_bonus.annual_charges, (3, 3))
        self.assertEqual(plan.buyer_contract.offer.salaries, (20, 30))
        self.assertEqual(plan.buyer_contract.offer.guaranteed_salaries, (20, 10))
        self.assertEqual(plan.buyer_contract.elapsed_years, 0)
        self.assertEqual((plan.seller_cash.amount, plan.buyer_cash.amount), (19, 50))
        with self.assertRaisesRegex(ValueError, 'prior base'):
            self.plan(contract, self.cash())

    def test_unknown_unpaid_bonus_and_future_payments_are_not_assumed_away(self):
        for cash in (replace(self.cash(), paid_components=None),
                     replace(self.cash(), paid=3, paid_components=(('signing_bonus', 3),)),
                     replace(self.cash(), paid=10, paid_components=(('signing_bonus', 9), ('base:1', 1))),
                     replace(self.cash(), amount=70), replace(self.cash(), player_id='other'),
                     replace(self.cash(), paid_components=(('other_bonus', 9),))):
            with self.subTest(cash=cash), self.assertRaises(ValueError):
                self.plan(cash=cash)

    def test_scope_requires_explicit_assent_and_supported_liabilities(self):
        changes = ({'healthy': False}, {'assignment_consent': False}, {'assignment_consent': 1},
                   {'transaction_eligible': False}, {'current_year_earned_base': False},
                   {'current_year_earned_base': 1}, {'source': ''},
                   {'exclusions': EXCLUDED_TRADE_LIABILITIES - {'seller_retained_guarantees'}},
                   {'traded_on': date(2026, 9, 10)}, {'buyer_first_regular_season_game': date(2026, 5, 31)},
                   {'seller_first_regular_season_game': date(2027, 9, 10)}, {'league_year': True})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(self.scope(), **change)
        for field in ('assignment_consent', 'transaction_eligible', 'healthy', 'current_year_earned_base', 'exclusions'):
            values = asdict(self.scope())
            del values[field]
            with self.subTest(missing=field), self.assertRaises(TypeError):
                PreseasonTradeScope(**values)

    def test_final_year_and_fractional_bonus_are_exact(self):
        plan = self.plan(scope=self.scope(date(2030, 6, 2), 2030))
        self.assertEqual(plan.retained_bonus.annual_charges, (9,))
        contract = ActiveContract(Offer('v', (1, 1, 1), 1), 'synthetic fractional contract')
        cash = CashObligation('contract:v', 'v', 4, 1, 'synthetic paid bonus', (('signing_bonus', 1),))
        plan = self.plan(contract, cash, self.scope(date(2026, 6, 2)))
        self.assertEqual(plan.retained_bonus.annual_charges, (Fraction(1, 3), Fraction(2, 3)))
        self.assertEqual(plan.buyer_contract.offer.guaranteed_salaries, ())
        self.assertEqual((plan.seller_cash.amount, plan.buyer_cash.amount), (1, 3))
