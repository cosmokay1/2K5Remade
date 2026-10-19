"""Adapter scope: actual APY and explicitly preserved rookie/special-deal gaps."""
import json
import unittest
from unittest.mock import patch
from franchise.salary_rules import VeteranMinimumProfile
from tools.export_local_market import export_market
from tools.inspect_franchise_save import PLAYER_START,PLAYER_STRIDE


class MarketExportTests(unittest.TestCase):
    def run_export(self, *, kind='UFA', fit_total=999999999, year=2026, special_years=None):
        members={i:dict(player_id=f'p{i}',team='Giants' if i==0 else 'Other') for i in range(4)}
        members[4]=dict(player_id='free',team='free_agents')
        payload=bytearray(PLAYER_START+5*PLAYER_STRIDE)
        for i in members:payload[PLAYER_START+i*PLAYER_STRIDE+0x35]=3
        audit=dict(ledger=[dict(name=f'N{i}',headline_dollars={'apy':20000000+i*1000000},
            year_signed=2024,contract_history=[dict(status='Active',year_signed=2024,contract_type=kind if i==0 else 'UFA')],
            source='Authored annual contract',fit=dict(contract_total=fit_total)) for i in range(4)])
        if special_years is not None:
            audit['ledger'][0]['source_years']=special_years
            audit['ledger'][0]['contract_history'][0]['yrs']=special_years
        report=dict(start_year=year,as_of='2026-09-01',audit_sha256='a'*64,
            teams={'Giants':dict(matched=[dict(player_id='p0',name='N0')],unresolved=[]),
                   'Other':dict(matched=[dict(player_id=f'p{i}',name=f'N{i}') for i in range(1,4)],unresolved=[])})
        profile=VeteranMinimumProfile(2026,tuple((p['player_id'],(5,6,7),('active_inactive',)*3) for p in members.values()))
        with patch('tools.export_local_market.reconcile_source',return_value=report),\
             patch('tools.export_local_market.migrate_context',return_value={'game_context':{'league_cap_raw':75300,'money_scale':4}}),\
             patch('tools.export_local_market.resolve_bindings',return_value=members),\
             patch('tools.export_local_market.salary_inputs',return_value=({'profile':profile.to_dict(),'source':'Authored salary inputs'},{})):
            return export_market({},bytes(payload),json.dumps(audit).encode(),team_id='Giants')

    def test_actual_annual_price_is_used_instead_of_fitted_cap_total(self):
        a=self.run_export(fit_total=999999999);b=self.run_export(fit_total=1)
        self.assertEqual(a['pricebook']['policy'],b['pricebook']['policy'])
        self.assertEqual(a['pricebook']['report']['p0']['target_annual_value'],20000000)
        self.assertFalse(a['pricebook']['policy']['signing_enabled'])
        self.assertIn('free',a['pricebook']['policy']['quotes'])

    def test_existing_rookie_deal_not_reclassified_by_salary_minimum_inputs(self):
        result=self.run_export(kind='Drafted')
        self.assertNotIn('p0',result['pricebook']['policy']['quotes'])
        self.assertIn('p0',result['excluded'])
        self.assertIn('free',result['pricebook']['policy']['quotes'])

    def test_special_tender_and_unsupported_source_year_not_claimed_as_market(self):
        self.assertNotIn('p0',self.run_export(kind='Franchise')['pricebook']['policy']['quotes'])
        with self.assertRaises(ValueError):self.run_export(year=2027)

    def test_multi_year_tag_acquisition_label_is_not_a_one_year_tender(self):
        result=self.run_export(kind='Franchise',special_years=5)
        self.assertEqual(result['pricebook']['report']['p0']['target_annual_value'],20000000)
        self.assertNotIn('p0',self.run_export(kind='Franchise',special_years=1)['pricebook']['policy']['quotes'])
