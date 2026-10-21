from copy import deepcopy
import unittest

from tools.model_opening_cap import published_club_proxies, model_opening_cap
from tools.reconcile_week1_contracts import CLUBS


class OpeningCapModelTests(unittest.TestCase):
    def inputs(self):
        text='Authored (https://overthecap.com/salary-cap-space)\n#### Base Salary Cap: $301,200,000\n'
        text+='\n'.join(f'{name} | $1,200,000 | $1,200,000 | 80 | $290,000,000 | $20,000,000'
                        for name in CLUBS.values())
        proxies=published_club_proxies(text,season_year=2026,base_cap=301_200_000,as_of='2026-10-20')
        charges=dict(season_year=2026,league_cap=301_200_000,unresolved=0,input_sha256='a'*64,
                     teams={code:dict(roster_charge_subtotal=290_000_000) for code in CLUBS})
        return text,proxies,charges

    def build(self,charges,proxies,**kwargs):
        return model_opening_cap(charges,proxies,cutoff='2026-09-10',
                                 allow_modeled_missing_obligations=True,**kwargs)

    def test_external_budget_does_not_expand_when_roster_cost_increases(self):
        _,proxy,charges=self.inputs();before=deepcopy(proxy)
        r=self.build(charges,proxy)
        self.assertEqual(r['teams']['NYG']['modeled_cap_room_dollars'],1_200_000)
        charges['teams']['NYG']['roster_charge_subtotal']+=5_000_000
        after=self.build(charges,proxy)
        self.assertEqual(after['teams']['NYG']['modeled_cap_room_dollars'],-3_800_000)
        self.assertEqual(after['teams']['NYG']['adjusted_budget_dollars'],r['teams']['NYG']['adjusted_budget_dollars'])
        self.assertEqual(after['over_cap_clubs'],['NYG']);self.assertEqual(proxy,before)
        self.assertFalse(after['signing_authorized']);self.assertFalse(after['ready_for_franchise_test'])

    def test_known_totals_remain_fixed_even_if_they_make_room_worse(self):
        _,proxy,charges=self.inputs()
        known={'NYG':dict(source='authored dated total',as_of='2026-09-09',
                          retained_dollars=30_000_000,net_adjustment_dollars=-1_000_000)}
        r=self.build(charges,proxy,known_totals=known)['teams']['NYG']
        self.assertEqual(r['retained_dollars'],30_000_000)
        self.assertEqual(r['net_adjustment_dollars'],-1_000_000)
        self.assertEqual(r['retained_basis'],'known_complete_total')

    def test_no_automatic_authorization_and_no_partial_league(self):
        _,proxy,charges=self.inputs()
        with self.assertRaises(ValueError):model_opening_cap(charges,proxy,cutoff='2026-09-10')
        charges['teams'].pop('NYG')
        with self.assertRaises(ValueError):self.build(charges,proxy)

    def test_other_season_missing_and_duplicate_tables_are_rejected(self):
        text,_,_=self.inputs()
        for changed in [text.replace('$301,200,000','$327,000,000'),
                        '\n'.join(text.splitlines()[:-1]),text+'\nGiants | $1 | $1 | 1 | $1 | $1']:
            with self.assertRaises(ValueError):published_club_proxies(changed,
                season_year=2026,base_cap=301_200_000,as_of='2026-10-20')

    def test_known_future_and_boolean_amounts_do_not_gain_authority(self):
        _,proxy,charges=self.inputs()
        for known in [dict(source='authored',as_of='2026-09-11',retained_dollars=1),
                      dict(source='authored',retained_dollars=1),
                      dict(source='authored',as_of='2026-09-09',retained_dollars=True)]:
            with self.assertRaises(ValueError):self.build(charges,proxy,known_totals={'NYG':known})

    def test_confirmed_debt_is_inside_proxy_total_not_added_twice_or_erased(self):
        _,proxy,charges=self.inputs()
        known=dict(source='authored partial book',as_of='2026-09-09',retained_components=[
            dict(obligation_id='original-bonus',dollars=7_000_000,
                 source='authored charge',as_of='2026-09-08')])
        r=self.build(charges,proxy,known_totals={'NYG':known})['teams']['NYG']
        self.assertEqual(r['retained_dollars'],20_000_000)
        self.assertEqual(r['unallocated_retained_dollars'],13_000_000)
        known['retained_components'][0]['dollars']=22_000_000
        r=self.build(charges,proxy,known_totals={'NYG':known})['teams']['NYG']
        self.assertEqual(r['retained_dollars'],22_000_000)
        self.assertTrue(r['retained_proxy_raised_to_known_floor'])
        self.assertEqual(r['modeled_cap_room_dollars'],-800_000)
        known['retained_dollars']=21_000_000
        with self.assertRaises(ValueError):self.build(charges,proxy,known_totals={'NYG':known})
        known.pop('retained_dollars')
        known['retained_components']*=2
        with self.assertRaises(ValueError):self.build(charges,proxy,known_totals={'NYG':known})

    def test_explicit_calibration_matches_external_room_without_changing_charges(self):
        _,proxy,charges=self.inputs()
        charges['teams']['NYG']['roster_charge_subtotal']+=5_000_000
        original=deepcopy(charges)
        r=self.build(charges,proxy,calibrate_to_published_room=True)['teams']['NYG']
        self.assertEqual(r['modeled_cap_room_dollars'],1_200_000)
        self.assertEqual(r['simulation_calibration_dollars'],5_000_000)
        self.assertEqual(r['adjustment_basis'],'simulation_room_calibration')
        self.assertEqual(charges,original)
        known={'NYG':dict(source='dated known adjustment',as_of='2026-09-09',
                          net_adjustment_dollars=-1_000_000)}
        r=self.build(charges,proxy,known_totals=known,calibrate_to_published_room=True)['teams']['NYG']
        self.assertEqual(r['net_adjustment_dollars'],-1_000_000)
        self.assertNotEqual(r['room_difference_from_target_dollars'],0)
