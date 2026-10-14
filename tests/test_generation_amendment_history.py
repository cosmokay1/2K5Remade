from dataclasses import FrozenInstanceError,replace
from datetime import date
from fractions import Fraction
import json
import unittest
from franchise.generations import GenerationAgreement,GenerationCalendarView,legacy_identity
from franchise.restructures import calculate_layered_preseason_restructure
from tests import test_restructures as fixtures


class GenerationAmendmentHistoryTests(unittest.TestCase):
    def plans(self):
        fixture=fixtures.PreseasonRestructureTests();first=fixture.plan()
        contract=replace(first.contract,elapsed_years=3)
        cash=replace(first.cash_obligation,paid=40,paid_components=first.cash_obligation.paid_components+
            ((first.bonus_layer.cash_component,8),('base:2',2)))
        scope=replace(fixture.scope(),league_year=2027,amended_on=date(2027,6,1),
            first_regular_season_game=date(2027,9,10),source='synthetic second conversion')
        second=calculate_layered_preseason_restructure(contract,cash,scope=scope,converted_base=8,
            annual_minimums=(2,)*4,record_id='second-conversion')
        return first,second

    def agreement(self,first=None,second=None,**changes):
        if first is None:first,second=self.plans()
        values=dict(identity=legacy_identity('a','v'),original_contract=first.original_contract,
            contract=second.contract,restructure=second,restructure_calendar_year=2027,prior_restructures=(first,))
        values.update(changes)
        return GenerationAgreement(**values)

    def test_exact_paid_cash_bonus_schedules_and_immutable_birth_chain(self):
        first,second=self.plans();agreement=self.agreement(first,second)
        self.assertIs(agreement.original_contract,first.original_contract)
        self.assertEqual(agreement.prior_restructures,(first,));self.assertIs(agreement.restructure,second)
        self.assertEqual(agreement.contract.nominal_cash,180)
        self.assertEqual(agreement.annual_charges(),tuple(Fraction(n,5) for n in (88,178,218,268)))
        self.assertEqual(second.original_cash.paid,40)
        self.assertEqual(second.cash_obligation.paid_components,second.original_cash.paid_components)
        self.assertEqual(agreement.contract.bonus_layers,(first.bonus_layer,second.bonus_layer))
        with self.assertRaises(FrozenInstanceError):agreement.prior_restructures=()
        view=GenerationCalendarView(agreement,2027,2028)
        self.assertIs(view.agreement,agreement)
        self.assertEqual(view.current_contract.elapsed_years,4)
        self.assertEqual(view.annual_charges(),tuple(Fraction(n,5) for n in (178,218,268)))
        snapshot=agreement.amendment_history_snapshot()
        self.assertEqual(snapshot['format'],1);self.assertEqual(len(snapshot['prior_restructures']),1)
        self.assertEqual(snapshot['prior_restructures'][0]['scope']['league_year'],2026)
        self.assertEqual(snapshot['latest_restructure']['scope']['league_year'],2027)
        json.dumps(snapshot,allow_nan=False)
        snapshot['prior_restructures'][0]['converted_base']=999
        self.assertEqual(agreement.prior_restructures[0].converted_base,8)
        legacy=GenerationAgreement(legacy_identity('a','v'),first.original_contract,first.contract,restructure=first)
        self.assertIsNone(legacy.amendment_history_snapshot())

    def test_terms_source_cursor_year_layers_cash_and_malformed_history_reject(self):
        first,second=self.plans()
        bad_plans=(replace(second,original_contract=replace(second.original_contract,source='tampered')),
            replace(second,scope=replace(second.scope,league_year=2026,amended_on=date(2026,6,1),first_regular_season_game=date(2026,9,10))),
            replace(second,original_contract=replace(second.original_contract,elapsed_years=4)),
            replace(second,contract=replace(second.contract,bonus_layers=(second.bonus_layer,))),
            replace(second,original_cash=replace(second.original_cash,source='lost predecessor source')),
            replace(second,cash_obligation=replace(second.cash_obligation,paid=32,
                paid_components=tuple((key,value) for key,value in second.cash_obligation.paid_components if key!=first.bonus_layer.cash_component))),
            replace(second,original_cash=replace(second.original_cash,obligation_id='foreign')),
            replace(second,scope=None))
        for plan in bad_plans:
            with self.subTest(plan=plan),self.assertRaises(ValueError):
                self.agreement(first,plan,restructure_calendar_year=plan.scope.league_year if plan.scope else 2027)
        for changes in ({'prior_restructures':[first]},{'prior_restructures':(None,)},
                        {'restructure':None},{'restructure_calendar_year':None},
                        {'original_contract':replace(first.original_contract,source='tampered birth')}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.agreement(first,second,**changes)

    def test_closed_release_keeps_full_history_and_exact_remaining_bonus_debt(self):
        from franchise.releases import calculate_preseason_release
        from tests import test_releases as release_fixtures
        first,second=self.plans();agreement=self.agreement(first,second)
        scope=release_fixtures.PreseasonReleaseTests().scope()
        scope=replace(scope,league_year=2027,removed_on=date(2027,5,1),first_regular_season_game=date(2027,9,10))
        cash=replace(second.cash_obligation,paid=48,
            paid_components=second.cash_obligation.paid_components+((second.bonus_layer.cash_component,8),))
        from franchise.guarantees import DiscountProfile
        release=calculate_preseason_release(second.contract,cash,scope=scope,
            discount=DiscountProfile(2027,Fraction(0),'synthetic zero'),payment_year_offsets=(0,)*4,
            record_id='later-release')
        closed=replace(agreement,release=release,release_calendar_year=2027)
        self.assertEqual(closed.prior_restructures,agreement.prior_restructures)
        self.assertIs(closed.restructure,second)
        self.assertEqual(closed.original_contract,first.original_contract)
        # Original bonus: 4 remaining; first layer: 32/5; second layer: 8.
        self.assertEqual(release.retained[0].annual_charges,(Fraction(92,5),))
        self.assertEqual(release.cash_obligation.paid,48)
        self.assertEqual(closed.payment_ceilings()['base:3'],12)
        view=GenerationCalendarView(closed,2027,2028)
        self.assertEqual(view.annual_charges(),())
        self.assertEqual(view.payment_ceilings(),closed.payment_ceilings())
        with self.assertRaises(ValueError):
            replace(closed,release=replace(release,scope=replace(scope,league_year=2028,
                removed_on=date(2028,5,1),first_regular_season_game=date(2028,9,10))),release_calendar_year=2028)

    def test_closed_assignment_retains_chain_and_rejects_wrong_closing_year_delta(self):
        from franchise.trades import calculate_preseason_trade
        from tests import test_trades as trade_fixtures
        first,second=self.plans();agreement=self.agreement(first,second)
        scope=replace(trade_fixtures.PreseasonTradeTests().scope(),league_year=2027,
            traded_on=date(2027,5,1),seller_first_regular_season_game=date(2027,9,10),
            buyer_first_regular_season_game=date(2027,9,10))
        cash=replace(second.cash_obligation,paid=48,
            paid_components=second.cash_obligation.paid_components+((second.bonus_layer.cash_component,8),))
        trade=calculate_preseason_trade(second.contract,cash,scope=scope,record_id='later-assignment')
        closed=replace(agreement,outgoing_trade=trade,outgoing_trade_calendar_year=2027)
        self.assertEqual(closed.prior_restructures,(first,))
        self.assertEqual(closed.outgoing_trade.retained_bonus.annual_charges,(Fraction(92,5),))
        self.assertEqual((trade.seller_cash.amount,trade.buyer_cash.amount),(48,132))
        self.assertEqual(closed.payment_ceilings()['base:2'],2)
        self.assertEqual(closed.payment_ceilings()['base:3'],0)
        view=GenerationCalendarView(closed,2027,2028)
        self.assertEqual(view.status,'assigned');self.assertEqual(view.payment_ceilings(),closed.payment_ceilings())
        with self.assertRaises(ValueError):
            replace(closed,outgoing_trade=replace(trade,scope=replace(scope,league_year=2028,
                traded_on=date(2028,5,1),seller_first_regular_season_game=date(2028,9,10),
                buyer_first_regular_season_game=date(2028,9,10))),outgoing_trade_calendar_year=2028)
