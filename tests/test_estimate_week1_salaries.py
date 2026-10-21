from copy import deepcopy
import unittest

from tools.estimate_week1_salaries import estimate_opening_charges
from tools.reconcile_week1_contracts import CLUBS


class OpeningEstimateTests(unittest.TestCase):
    def inputs(self):
        weekly, contracts = [], []
        for code, name in CLUBS.items():
            gsis='authored-'+code
            weekly.append(dict(season=2026,week=1,game_type='REG',team=code,status='ACT',
                               full_name=gsis,gsis_id=gsis,years_exp=4,position='LS'))
            contracts.append(dict(gsis_id=gsis,is_active=True,
                                  season_history=[dict(year=2026,team=name,cap_number=1)]))
        for i in range(3):
            self.add(weekly,contracts,'peer'+str(i),cap=2*(i+1),apy=4*(i+1))
        return weekly,contracts

    def add(self,weekly,contracts,name,cap=None,apy=None,status='ACT',position='WR'):
        weekly.append(dict(season=2026,week=1,game_type='REG',team='NYG',status=status,
                           full_name=name,gsis_id=name,years_exp=4,position=position))
        if apy is not None:
            contracts.append(dict(gsis_id=name,is_active=True,year_signed=2026,years=3,
                value=apy*3,apy=apy,contract_history=[dict(status='Active',team='Giants',
                year_signed=2026,yrs=3,total=apy*3,contract_type='UFA')],
                season_history=[] if cap is None else [dict(year=2026,team='Giants',cap_number=cap)]))

    def run_model(self,w,c,reports=(),cap=301_200_000):
        return estimate_opening_charges(w,c,reports,season_year=2026,league_cap=cap)

    def player(self,r,name):
        return next(p for p in r['teams']['NYG']['players'] if p['player']==name)

    def test_existing_charges_are_preserved_and_prices_do_not_depend_on_team_budget(self):
        w,c=self.inputs();self.add(w,c,'target',apy=20);before=deepcopy((w,c))
        result=self.run_model(w,c);other=self.run_model(w,c,cap=1)
        self.assertEqual((w,c),before)
        self.assertEqual(self.player(result,'target')['cap_dollars'],10_000_000)
        self.assertEqual(self.player(result,'peer0')['cap_dollars'],2_000_000)
        self.assertEqual(self.player(result,'target'),self.player(other,'target'))
        self.assertIsNone(result['teams']['NYG']['cap_room'])
        self.assertFalse(result['ready_for_franchise_test'])

    def test_positive_one_year_deal_with_zero_annual_placeholder_is_not_free(self):
        w,c=self.inputs();self.add(w,c,'placeholder',cap=0,apy=2)
        row=c[-1];row.update(years=1,value=2)
        row['contract_history'][0].update(yrs=1,total=2)
        before=deepcopy(c)
        entry=self.player(self.run_model(w,c),'placeholder')
        self.assertEqual(entry['cap_dollars'],2000000)
        self.assertEqual(entry['basis'],'modeled_one_year_nominal_charge')
        self.assertEqual(entry['archived_zero_cap_placeholder_dollars'],0)
        self.assertEqual(c,before)

    def test_published_comparison_is_labeled_as_estimated_not_historical(self):
        w,c=self.inputs();c[-1]['season_history'][0]['historical_annual_schedule_verified']=False
        p=self.player(self.run_model(w,c),'peer2')
        self.assertEqual(p['basis'],'published_matching_contract_estimate')
        self.assertFalse(p['paid_cash_verified'])

    def test_practice_and_specialist_fallbacks_do_not_use_active_star_prices(self):
        w,c=self.inputs()
        for i in range(3):self.add(w,c,'ps'+str(i),cap=0.2475,apy=0.2475,status='DEV',position='RB')
        self.add(w,c,'practice-punter',status='DEV',position='P')
        self.add(w,c,'reserve-snapper',status='RES',position='LS')
        r=self.run_model(w,c)
        self.assertEqual(self.player(r,'practice-punter')['cap_dollars'],248_000)
        self.assertEqual(self.player(r,'practice-punter')['fallback'],'practice_experience_tier')
        self.assertEqual(self.player(r,'reserve-snapper')['fallback'],'reserve_full_salary_projection')

    def test_rookie_projection_preserves_nominal_total_and_nearest_slots(self):
        w,c=self.inputs();self.add(w,c,'rookie',apy=2)
        row=c[-1];row.update(years=4,value=8,draft_year=2026,draft_overall=10,otc_id=10)
        row['contract_history'][0].update(yrs=4,total=8,contract_type='Drafted')
        reports=[]
        for slot in (1,8,9,11,12,200):
            c.append(dict(otc_id=slot,draft_overall=slot))
            reports.append(dict(otc_id=slot,contract_type='Drafted',annual=[
                dict(year=2026+i,cap_dollars=n) for i,n in enumerate([1_000_000,2_000_000,2_000_000,3_000_000])]))
        p=self.player(self.run_model(w,c,reports),'rookie')
        self.assertEqual(p['comparable_otc_ids'],[8,9,11,12])
        self.assertEqual(sum(r['cap_dollars'] for r in p['annual_cap_projection']),8_000_000)
        self.assertNotIn('signing_bonus',p)
        self.assertFalse(p['paid_cash_verified'])
        with self.assertRaises(ValueError):self.run_model(w,c,reports+reports[:1])
        reports[0]['annual'][0]['cap_dollars']=0
        with self.assertRaises(ValueError):self.run_model(w,c,reports)

    def test_off_roster_rookie_is_kept_for_rights_review_not_added_to_a_club(self):
        w,c=self.inputs()
        c.append(dict(player='off-roster',gsis_id='off-roster',team='Giants',
                      draft_year=2026,year_signed=2026))
        r=self.run_model(w,c)
        self.assertEqual(r['club_members'],35)
        self.assertTrue(r['rookie_contracts_without_week1_owner'][0]['rights_review_required'])

    def test_insufficient_peers_unknown_experience_and_duplicate_owner_cannot_hide(self):
        w,c=self.inputs();self.add(w,c,'unknown',position='UNKNOWN')
        r=self.run_model(w,c)
        self.assertEqual(r['unresolved'],1)
        self.assertIsNone(r['teams']['NYG']['roster_charge_subtotal'])
        w[-1]['years_exp']=None
        with self.assertRaises(ValueError):self.run_model(w,c)
        w[-1]['years_exp']=4;w.append({**w[-1],'team':'NYJ'})
        with self.assertRaises(ValueError):self.run_model(w,c)
