from dataclasses import replace
from datetime import date
from fractions import Fraction
import unittest
from franchise.books import ActiveContract
from franchise.cap import Offer
from franchise.cash import CashObligation
from franchise.guarantees import DiscountProfile
from franchise.releases import EXCLUDED_LIABILITIES, PreseasonReleaseScope, calculate_preseason_release


class PreseasonReleaseTests(unittest.TestCase):
    def scope(self, when=date(2026, 6, 1), year=2026):
        return PreseasonReleaseScope(year, when, date(year, 9, 10), EXCLUDED_LIABILITIES,
                                     True, True, 0, 'synthetic healthy preseason scope')

    def contract(self):
        return ActiveContract(Offer('v', (10, 20, 30), 9, (0, 20, 10)), 'synthetic contract')

    def cash(self):
        return CashObligation('contract:v', 'v', 69, 9, 'synthetic allocated payments', (('signing_bonus', 9),))

    def plan(self, **kwargs):
        inputs = dict(scope=self.scope(), discount=DiscountProfile(2026, Fraction(0), 'synthetic zero rate'),
                      payment_year_offsets=(0, 1, 2), record_id='release:v')
        inputs.update(kwargs)
        return calculate_preseason_release(inputs.pop('contract', self.contract()), inputs.pop('cash', self.cash()), **inputs)

    def test_independent_pre_and_post_june_cash_and_cap_expectations(self):
        before = self.plan()
        after = self.plan(scope=self.scope(date(2026, 6, 2)))
        self.assertEqual(before.charges(), (39,))
        self.assertEqual(after.charges(), (33, 6))
        for plan in (before, after):
            self.assertEqual(plan.cash_obligation.amount, 39)
            self.assertEqual(plan.cash_obligation.paid, 9)
            self.assertEqual(plan.cash_obligation.amount - plan.cash_obligation.paid, 30)
            self.assertEqual(plan.cash_obligation.paid_components, self.cash().paid_components)
            self.assertEqual(plan.cancelled_unearned_base, 30)
            self.assertEqual(plan.original_contract, self.contract())
            self.assertEqual(plan.original_cash, self.cash())
            self.assertIn('synthetic healthy preseason scope', plan.cash_obligation.source)
            self.assertIn('article-13', plan.retained[0].source)

    def test_discount_changes_cap_only_and_unpaid_bonus_cash_survives(self):
        cash = replace(self.cash(), paid=3, paid_components=(('signing_bonus', 3),))
        plan = self.plan(cash=cash, discount=DiscountProfile(2026, Fraction(1, 10), 'synthetic 10% rate'))
        self.assertEqual(plan.charges(), (Fraction(9) + Fraction(200, 11) + Fraction(1000, 121),))
        self.assertEqual(plan.cash_obligation.amount, 39)
        self.assertEqual(plan.cash_obligation.amount - plan.cash_obligation.paid, 36)

    def test_original_elapsed_bonus_and_paid_prior_bases_remain(self):
        contract = replace(self.contract(), elapsed_years=1)
        cash = replace(self.cash(), paid=19, paid_components=(('base:0', 10), ('signing_bonus', 9)))
        plan = self.plan(contract=contract, cash=cash, payment_year_offsets=(0, 1))
        self.assertEqual(plan.charges(), (36,))
        self.assertEqual(plan.cancelled_unearned_base, 20)
        self.assertEqual((plan.cash_obligation.amount, plan.cash_obligation.paid), (49, 19))
        with self.assertRaisesRegex(ValueError, 'Prior base'):
            self.plan(contract=contract, payment_year_offsets=(0, 1))

    def test_unknown_or_contradictory_payment_coverage_rejects(self):
        for cash in (replace(self.cash(), paid_components=None), replace(self.cash(), amount=70),
                     replace(self.cash(), player_id='other'),
                     replace(self.cash(), paid=10, paid_components=(('signing_bonus', 9), ('base:0', 1))),
                     replace(self.cash(), paid=10, paid_components=(('signing_bonus', 10),)),
                     replace(self.cash(), paid=9, paid_components=(('unknown_bonus', 9),))):
            with self.subTest(cash=cash), self.assertRaises(ValueError):
                self.plan(cash=cash)

    def test_scope_requires_affirmative_explicit_supported_facts(self):
        from dataclasses import asdict
        for missing in ('current_year_earned_base', 'covered_guarantees', 'healthy', 'exclusions'):
            values = asdict(self.scope())
            del values[missing]
            with self.subTest(missing=missing), self.assertRaises(TypeError):
                PreseasonReleaseScope(**values)
        changes = ({'covered_guarantees': False}, {'covered_guarantees': 1}, {'healthy': False},
                   {'current_year_earned_base': 1}, {'current_year_earned_base': False},
                   {'exclusions': EXCLUDED_LIABILITIES - {'injury_liability'}}, {'source': ''},
                   {'removed_on': date(2026, 9, 10)}, {'removed_on': date(2027, 1, 1)},
                   {'first_regular_season_game': date(2027, 9, 10)}, {'league_year': True})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(self.scope(), **change)
        with self.assertRaises(ValueError):
            self.plan(discount=DiscountProfile(2025, Fraction(0), 'synthetic'))
        with self.assertRaises(ValueError):
            self.plan(payment_year_offsets=(0, 1))

    def test_final_year_and_fractional_bonus_remain_exact(self):
        final = self.plan(scope=self.scope(date(2030, 6, 2), 2030),
                          discount=DiscountProfile(2030, Fraction(0), 'synthetic zero rate'))
        self.assertEqual(final.charges(), (39,))
        contract = ActiveContract(Offer('v', (1, 1, 1), 1), 'synthetic fractional bonus')
        cash = CashObligation('contract:v', 'v', 4, 0, 'synthetic allocated no payments', ())
        plan = self.plan(contract=contract, cash=cash, scope=self.scope(date(2026, 6, 2)))
        self.assertEqual(plan.charges(), (Fraction(1, 3), Fraction(2, 3)))
        self.assertEqual((plan.cash_obligation.amount, plan.cancelled_unearned_base), (1, 3))
