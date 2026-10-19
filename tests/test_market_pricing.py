"""Price pressure, native encoding and observed-evidence boundaries."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from franchise.books import OpeningBooks, ActiveContract
from franchise.cap import Ledger, Offer, Rejected
from franchise.guest_contracts import GUEST_CONTRACT_FORMAT, SOFTDRINK_CONTRACT_FORMAT, guest_terms_for_offer
from franchise.market_pricing import build_pricebook, native_demand
from franchise.performance import Observation, PerformanceEvidence
from tools.build_local_pricebook import main


def performance(player, yards, *, games=16, mode='fast_sim', window='completed-2025', complete=True):
    return PerformanceEvidence(player,window,mode,
        (Observation('games',games,'Authored completed season'),
         Observation('receiving_yards',yards,'Authored completed season')),
        'Authored fixture',complete_window=complete).to_context()


def fixture():
    peers=[dict(player_id=f'peer-{i}',position='WR',annual_value=value,rookie=False,
                source='Authored actual annual value, not a fitted cap charge',
                performance=performance(f'peer-{i}',yards))
           for i,(value,yards) in enumerate([(10000000,600),(20000000,1000),(30000000,1600)])]
    return dict(format=1,team_id='club',league_cap=300000000,contract_format=SOFTDRINK_CONTRACT_FORMAT,
        market=dict(cap=300000000,as_of='2026-09-01',source='Authored market snapshot',comparables=peers),
        players=[dict(player_id='player',position='WR',rookie=False,minimum_salaries=[1000000]*3,
                      years=3,bonus_code=3,source='Authored annual salary floor profile')])


class MarketPricingTests(unittest.TestCase):
    def test_missing_stats_are_median_not_zero_and_no_cash_or_signing_is_authorized(self):
        data=fixture();before=copy.deepcopy(data);result=build_pricebook(data)
        self.assertEqual(data,before)
        self.assertEqual(result['report']['player']['target_annual_value'],20000000)
        self.assertEqual(result['report']['player']['basis'],'positional_median_missing_complete_performance')
        self.assertFalse(result['policy']['signing_enabled'])

    def test_star_production_commands_top_of_market_and_bad_production_lower_tier(self):
        data=fixture();data['players'][0]['performance']=performance('player',1700)
        self.assertEqual(build_pricebook(data)['report']['player']['target_annual_value'],30000000)
        data['players'][0]['performance']=performance('player',100)
        self.assertEqual(build_pricebook(data)['report']['player']['target_annual_value'],10000000)

    def test_partial_small_or_mixed_evidence_cannot_promote_or_demote(self):
        for changes in [dict(complete=False),dict(games=4),dict(mode='played'),dict(window='different-year')]:
            data=fixture();data['players'][0]['performance']=performance('player',9000,**changes)
            self.assertEqual(build_pricebook(data)['report']['player']['target_annual_value'],20000000)

    def test_own_actual_annual_price_retained_when_history_missing_not_used_as_own_peer(self):
        data=fixture();data['market']['comparables'].append(dict(player_id='player',position='WR',
            annual_value=35000000,rookie=False,source='Authored actual APY'))
        self.assertEqual(build_pricebook(data)['report']['player']['target_annual_value'],35000000)
        data['players'][0]['performance']=performance('player',100)
        self.assertEqual(build_pricebook(data)['report']['player']['matching_performance_peers'],3)

    def test_rookie_compensation_never_drags_down_veteran_market(self):
        data=fixture();data['market']['comparables'].append(dict(player_id='rookie',position='WR',
            annual_value=900000,rookie=True,source='Authored rookie deal'))
        self.assertEqual(build_pricebook(data)['report']['player']['target_annual_value'],20000000)
        rookie=copy.deepcopy(data['players'][0]);rookie.update(player_id='rookie',rookie=True);data['players'].append(rookie)
        result=build_pricebook(data);self.assertNotIn('rookie',result['policy']['quotes']);self.assertIn('unpriced',result['report']['rookie'])

    def test_cap_scale_is_proportional_and_native_terms_do_not_double_apply_four_to_one(self):
        data=fixture();data.update(league_cap=75000000,contract_format=GUEST_CONTRACT_FORMAT)
        small=build_pricebook(data);data.update(league_cap=300000000,contract_format=SOFTDRINK_CONTRACT_FORMAT)
        large=build_pricebook(data)
        a=Offer.from_dict(small['policy']['quotes']['player']['offer']);b=Offer.from_dict(large['policy']['quotes']['player']['offer'])
        self.assertEqual(b.signing_bonus,a.signing_bonus*4)
        self.assertEqual(b.salaries,tuple(x*4 for x in a.salaries))
        self.assertEqual(guest_terms_for_offer(b,contract_format=SOFTDRINK_CONTRACT_FORMAT),
                         guest_terms_for_offer(a,contract_format=GUEST_CONTRACT_FORMAT))

    def test_annual_minimum_is_preserved_after_bonus_and_rounding(self):
        offer=native_demand('player',1000000,[1500000,1600000,1700000],3,4,SOFTDRINK_CONTRACT_FORMAT)
        self.assertGreaterEqual(min(offer.salaries),1700000)
        self.assertEqual(offer,guest_terms_for_offer(offer,contract_format=SOFTDRINK_CONTRACT_FORMAT).to_offer('player',contract_format=SOFTDRINK_CONTRACT_FORMAT))
        with self.assertRaises(ValueError):native_demand('p',1000000,[1000000],1,10,GUEST_CONTRACT_FORMAT)

    def test_prices_force_cap_tradeoffs_instead_of_fitting_remaining_room(self):
        opening=OpeningBooks(contracts=tuple(ActiveContract(
            Offer(f'existing-{i}',(20000000,)*3,0),
            'Authored existing veteran contract') for i in range(10)))
        ledger=Ledger.from_opening(opening,cap=300000000,roster_reserve=20000000,
            max_bonus_years=5,veteran_minimums={**{f'p{i}':(1000000,)*3 for i in range(5)},
                **{f'existing-{i}':(1000000,)*3 for i in range(10)}})
        quotes=[]
        for i in range(5):
            data=fixture();data['players'][0]['player_id']=f'p{i}'
            # Same league cap as the market; existing contracts and roster
            # reserve, rather than a reduced cap, constrain new spending.
            quotes.append(Offer.from_dict(build_pricebook(data)['policy']['quotes'][f'p{i}']['offer']))
        for i,offer in enumerate(quotes[:4]):ledger.sign(f'sign-{i}',offer,ledger.revision)
        before=ledger.financial_snapshot()
        with self.assertRaises(Rejected):ledger.sign('one-too-many',quotes[4],ledger.revision)
        self.assertEqual(ledger.financial_snapshot(),before)
        self.assertEqual(quotes[0].salaries,quotes[4].salaries)

    def test_bad_comparables_and_wrong_player_evidence_refuse(self):
        for change in ['rating','cap_hit','duplicate','foreign','position']:
            data=fixture()
            if change=='rating':data['market']['comparables'][0]['rating']=99
            elif change=='cap_hit':data['market']['comparables'][0]['cap_hit']=100
            elif change=='duplicate':data['market']['comparables'].append(data['market']['comparables'][0])
            elif change=='foreign':data['players'][0]['performance']=performance('other',1000)
            else:data['players'][0]['position']=[]
            with self.assertRaises(ValueError):build_pricebook(data)

    def test_ties_and_input_order_do_not_reroll_prices(self):
        data=fixture();data['players'][0]['performance']=performance('player',1000)
        first=build_pricebook(data);data['market']['comparables'].reverse();second=build_pricebook(data)
        self.assertEqual(first['policy']['quotes']['player']['offer'],second['policy']['quotes']['player']['offer'])

    def test_cli_is_exclusive_and_preview_has_no_writes(self):
        import contextlib,io
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'input.json';out=root/'policy.json';source.write_text(json.dumps(fixture()))
            with contextlib.redirect_stdout(io.StringIO()):main([str(source)])
            self.assertEqual(list(root.iterdir()),[source])
            with contextlib.redirect_stdout(io.StringIO()):main([str(source),'--output',str(out)])
            before=out.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):main([str(source),'--output',str(out)])
            self.assertEqual(out.read_bytes(),before)
