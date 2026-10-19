"""Native cap projection preserves real liabilities and tolerates no mystery debt."""
from fractions import Fraction
import copy
import unittest
from franchise.cap import Offer
from franchise.legacy_amendments import InSeasonAmendmentScope
from franchise.native_cap import amendment_payroll_projection
from tests import test_legacy_amendment


class NativeAmendmentCapTests(unittest.TestCase):
    def setUp(self):
        self.ledger=test_legacy_amendment.LegacyAmendmentTests().ledger()
        self.offer=Offer('dart',(1000000,)*3,3000000)
        self.comparison=self.ledger.preview_legacy_amendment(self.offer,0)
        self.arguments=dict(native_payroll_before_raw=966,native_old_charge=3864000,native_new_charge=2000000,
            native_old_unamortized_bonus=6960000,native_accumulator_before_raw=0,
            native_accumulator_after_raw=0,team_adjustment_applies=True,game_dollar_scale=4)

    def project(self,**changes):
        return amendment_payroll_projection(self.comparison,**(self.arguments|changes))

    def test_retained_bonus_is_charged_without_changing_league_ceiling(self):
        p=self.project()
        self.assertEqual(p['league_cap_raw'],75300)
        self.assertEqual(p['native_payroll_after_raw'],500)
        self.assertEqual(p['enforced_payroll_raw'],1330) # 2M new + 2.32M retained + 1M reserve
        self.assertEqual(p['native_room_after'],295880000)
        self.assertEqual(p['exact_room_after'],self.comparison['room_after'])
        self.assertEqual(p['rounding_charge'],0);self.assertFalse(p['write_authorized'])

    def test_native_acceleration_is_offset_once_and_prior_debt_is_preserved(self):
        # Native accelerated bonus exceeds this tiny team's payroll; cannot
        # represent it by a negative payroll. Never erase the old accumulator.
        with self.assertRaisesRegex(ValueError,'not representable'):
            self.project(native_accumulator_after_raw=1740)
        self.comparison['annual_team_charges_before'][0]+=10000000
        self.comparison['annual_team_charges_after'][0]+=10000000
        self.comparison['room_before']-=10000000;self.comparison['room_after']-=10000000
        self.arguments['native_payroll_before_raw']+=2500
        p=self.project(native_accumulator_before_raw=20,native_accumulator_after_raw=1760)
        self.assertEqual(p['enforced_payroll_raw'],2090)
        self.assertEqual(p['exact_room_after'],self.comparison['room_after']-80000)
        self.assertEqual(p['native_room_after'],p['exact_room_after'])
        self.assertEqual(p['baseline_accumulator_raw'],20)
        self.assertEqual(p['league_cap_raw'],75300)

    def test_earned_pay_requires_a_signed_correction_not_just_adding_bonus(self):
        self.offer=Offer('dart',(12000000,),0)
        self.comparison=self.ledger.preview_legacy_amendment(self.offer,0,
            scope=InSeasonAmendmentScope(2026,8,17,'authored period proof'))
        p=self.project(native_new_charge=12000000)
        self.assertLess(p['enforced_payroll_raw'],p['native_payroll_after_raw'])
        self.assertGreaterEqual(Fraction(p['rounding_charge']),0)
        self.assertLess(Fraction(p['rounding_charge']),4000)
        self.assertLessEqual(Fraction(p['native_room_after']),Fraction(p['exact_room_after']))
        self.assertEqual(Fraction(p['native_room_after'])+Fraction(p['rounding_charge']),Fraction(p['exact_room_after']))

    def test_rounding_cannot_make_an_exactly_affordable_offer_spend_extra_raw_units(self):
        self.offer=Offer('dart',(1004000,)*3,3000000)
        self.comparison=self.ledger.preview_legacy_amendment(self.offer,0,
            scope=InSeasonAmendmentScope(2026,8,17,'authored period proof'))
        self.comparison['cap']=Fraction(self.comparison['annual_team_charges_after'][0])+1000000
        # Native league caps are whole raw units; a fractional cap is invalid.
        from franchise.cap import json_amount
        self.comparison['cap']=json_amount(self.comparison['cap'])
        self.comparison['room_before']=json_amount(Fraction(self.comparison['cap'])-Fraction(self.comparison['annual_team_charges_before'][0])-1000000)
        self.comparison['room_after']=0
        with self.assertRaises(ValueError):self.project()

    def test_previously_recorded_accumulator_is_not_an_extra_cap_charge(self):
        # A prior signed amendment already carried this old bonus in the
        # ledger. Unrelated native debt remains charged by the default path.
        self.comparison['annual_team_charges_before'][0]+=10000000
        self.comparison['annual_team_charges_after'][0]+=10000000
        self.comparison['room_before']-=10000000;self.comparison['room_after']-=10000000
        self.arguments['native_payroll_before_raw']+=2500
        a=self.project(native_accumulator_before_raw=20,native_accumulator_after_raw=1760)
        b=self.project(native_accumulator_before_raw=20,native_accumulator_after_raw=1760,
            accounted_accumulator_before_raw=20)
        self.assertEqual(b['exact_room_after'],self.comparison['room_after'])
        self.assertEqual(b['exact_room_after']-a['exact_room_after'],80000)
        self.assertEqual(a['enforced_payroll_raw']-b['enforced_payroll_raw'],20)
        for value in (True,-1,21):
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.project(native_accumulator_before_raw=20,accounted_accumulator_before_raw=value)

    def test_accessor_branch_accumulator_overflow_and_unexplained_changes_hold(self):
        for changes in (dict(native_accumulator_before_raw=2,native_accumulator_after_raw=1),
                        dict(native_accumulator_after_raw=1),dict(native_accumulator_after_raw=65536),
                        dict(native_accumulator_after_raw=1740,team_adjustment_applies=False),
                        dict(game_dollar_scale=True),dict(native_payroll_before_raw=True),
                        dict(native_new_charge=2000001)):
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.project(**changes)

    def test_over_cap_retains_negative_room_and_never_authorizes_writes(self):
        self.ledger=test_legacy_amendment.LegacyAmendmentTests().ledger(cap=5000000)
        self.comparison=self.ledger.preview_legacy_amendment(self.offer,0)
        p=self.project();self.assertFalse(p['within_cap']);self.assertLess(p['native_room_after'],0)
        self.assertFalse(p['write_authorized'])

    def test_tampered_team_posting_room_and_affordability_reject(self):
        original=copy.deepcopy(self.comparison)
        for field in ('room_after','room_before','annual_team_charges_after','within_modeled_cap'):
            self.comparison=copy.deepcopy(original)
            if field=='within_modeled_cap':self.comparison[field]=False
            elif field=='annual_team_charges_after':self.comparison[field][0]+=1
            else:self.comparison[field]+=1
            with self.subTest(field=field),self.assertRaises(ValueError):self.project()
