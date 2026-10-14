from dataclasses import replace
from fractions import Fraction
from datetime import date
import unittest
from franchise.books import ActiveContract,OpeningBooks,ChargeRecord
from franchise.cap import Ledger,Offer,Rejected
from franchise.cash import CashBook,CashObligation
from franchise.salary_rules import VeteranMinimumProfile
from franchise.releases import PreseasonReleaseScope,EXCLUDED_LIABILITIES
from franchise.guarantees import DiscountProfile


class LedgerYearTransitionTests(unittest.TestCase):
    def calendar_amendment_ledger(self):
        ledger=self.ledger();old=ledger._active_contracts['v']
        guaranteed=replace(old,offer=replace(old.offer,guaranteed_salaries=(0,2000000,0)))
        ledger._active_contracts['v']=guaranteed;ledger._contracts['v']=guaranteed.offer
        ledger._generation_agreements.clear();ledger._refresh_generation_agreement('v')
        self.transition(ledger)
        return ledger

    def amendment_inputs(self,ledger,**changes):
        from franchise.restructures import PreseasonRestructureScope,EXCLUDED_RESTRUCTURE_TERMS
        inputs=dict(generation_id=ledger.contract_identity('v').generation_id,
            scope=PreseasonRestructureScope(2027,date(2027,6,1),date(2027,9,10),0,True,True,True,
                EXCLUDED_RESTRUCTURE_TERMS,ledger._veteran_minimum_profile.source,'synthetic guaranteed calendar conversion'),
            converted_base=100000,record_id='calendar-conversion',expected_revision=1)
        inputs.update(changes);return inputs

    def test_calendar_amendment_preserves_original_economics_and_cash_indices(self):
        ledger=self.calendar_amendment_ledger();gid=ledger.contract_identity('v').generation_id
        original=ledger.generation_accounting(gid);cash=ledger.cash_snapshot()
        plan=ledger.apply_calendar_preseason_restructure('v',**self.amendment_inputs(ledger))
        amended=ledger.generation_accounting(gid)
        self.assertIs(amended.original_contract,original.original_contract)
        self.assertEqual(amended.original_contract.elapsed_years,0)
        self.assertEqual(amended.restructure_calendar_year,2027)
        self.assertEqual(amended.restructure.original_contract.elapsed_years,1)
        self.assertEqual(plan.bonus_layer.original_start_index,1)
        self.assertEqual(plan.bonus_layer.allocation_years,2)
        self.assertEqual(ledger.charges,(2950011,3050013))
        self.assertEqual(ledger.cash_snapshot()['nominal_total'],cash['nominal_total'])
        self.assertEqual(ledger.cash_snapshot()['paid_total'],cash['paid_total'])
        self.assertEqual(ledger.cash_snapshot()['obligations'][0]['paid_components'],cash['obligations'][0]['paid_components'])
        view=ledger.generation_calendar_view(gid)
        self.assertEqual((view.anchor_year,view.current_contract.elapsed_years),(2027,1))
        ledger._cash.pay('contract:v',100000,ledger._cash.revision,component='bonus:calendar-conversion')
        ledger._cash.pay('contract:v',1900000,ledger._cash.revision,component='base:1')
        self.transition(ledger,from_year=2027,to_year=2028,expected_revision=2,
            next_minimum_profile=VeteranMinimumProfile(2028,(('v',(7,7),('active_inactive',)*2),)))
        self.assertEqual(ledger.charges,(3050013,))
        self.assertEqual(ledger.active_contract('v').elapsed_years,2)
        self.assertIs(ledger.generation_accounting(gid),amended)
        release=self.release_inputs(ledger,scope=PreseasonReleaseScope(2028,date(2028,7,1),date(2028,9,10),
            EXCLUDED_LIABILITIES,True,True,0,'synthetic later release'),
            discount=DiscountProfile(2028,Fraction(0),'synthetic rate'),payment_year_offsets=(0,),expected_revision=3)
        ledger.apply_calendar_preseason_release('v',**release)
        self.assertEqual(ledger.charges,(1050013,0))
        self.assertIs(ledger.generation_accounting(gid).restructure,plan)
        self.assertEqual(ledger.cash_snapshot()['nominal_total'],7000000)
        self.assertEqual(ledger.cash_snapshot()['paid_total'],7000000)

    def test_calendar_amendment_invalid_and_repeated_calls_cannot_mutate(self):
        for changes in ({'generation_id':'foreign'},{'generation_id':True},{'expected_revision':True},
                        {'converted_base':0},{'record_id':''}):
            ledger=self.calendar_amendment_ledger()
            before=(ledger.generation_snapshot(),ledger.generation_calendar_snapshot(),ledger.cash_snapshot())
            with self.subTest(changes=changes),self.assertRaises((ValueError,Rejected)):
                ledger.apply_calendar_preseason_restructure('v',**self.amendment_inputs(ledger,**changes))
            self.assertEqual((ledger.generation_snapshot(),ledger.generation_calendar_snapshot(),ledger.cash_snapshot()),before)
        ledger=self.calendar_amendment_ledger()
        with self.assertRaises(Rejected):
            ledger.apply_preseason_restructure('v',**{key:value for key,value in self.amendment_inputs(ledger).items() if key!='generation_id'})
        ledger.apply_calendar_preseason_restructure('v',**self.amendment_inputs(ledger))
        before=(ledger.generation_snapshot(),ledger.generation_calendar_snapshot(),ledger.cash_snapshot())
        with self.assertRaisesRegex(ValueError,'Repeated layered'):
            ledger.apply_calendar_preseason_restructure('v',**self.amendment_inputs(ledger,expected_revision=2,record_id='second'))
        self.assertEqual((ledger.generation_snapshot(),ledger.generation_calendar_snapshot(),ledger.cash_snapshot()),before)

    def incoming_plan(self):
        from franchise.generations import assignment_identity
        seller=self.ledger();source=seller.contract_identity('v').generation_id
        self.transition(seller)
        destination=assignment_identity('b','v','incoming-current')
        plan=seller.apply_calendar_preseason_trade_out('v',**self.calendar_trade_inputs(seller,
            buyer_cash_id=destination.cash_obligation_id))
        return plan,source,destination

    def calendar_buyer(self,*,prior_released=False):
        contract=ActiveContract(Offer('v',(2000000,)*3,3000000),'synthetic prior buyer agreement')
        buyer=Ledger.from_opening(OpeningBooks(contracts=(contract,) if prior_released else (),
            retained=(ChargeRecord('buyer-debt',(7,11,13),'synthetic prior debt'),)),
            cap=10000000,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1000000,)*3})
        records=(CashObligation('contract:v','v',9000000,3000000,'synthetic settled prior bonus',
            (('signing_bonus',3000000),)),) if prior_released else ()
        buyer._cash=CashBook(records,'synthetic buyer cash');buyer.bind_team_identity('b');buyer._league_year=2026
        if prior_released:
            buyer.apply_preseason_release('v',scope=PreseasonReleaseScope(2026,date(2026,6,1),date(2026,9,10),
                EXCLUDED_LIABILITIES,True,True,0,'synthetic prior healthy release'),
                discount=DiscountProfile(2026,Fraction(0),'synthetic rate'),payment_year_offsets=(0,1,2),
                record_id='prior-release',expected_revision=0)
        self.transition(buyer,expected_revision=buyer.revision)
        return buyer

    def receive(self,buyer,plan,source,**changes):
        inputs=dict(expected_revision=buyer.revision,assignment_request_id='incoming-current',
            assigned_from_team='a',assigned_from_generation_id=source)
        inputs.update(changes)
        return buyer.apply_calendar_preseason_trade_in(plan,**inputs)

    def test_calendar_buyer_anchors_incoming_agreement_at_actual_trade_year(self):
        plan,source,destination=self.incoming_plan();buyer=self.calendar_buyer()
        self.receive(buyer,plan,source)
        self.assertEqual(buyer.charges,(2000011,2000013))
        self.assertEqual(buyer.contract_identity('v'),destination)
        agreement=buyer.generation_accounting(destination.generation_id)
        self.assertEqual(agreement.incoming_trade,plan)
        view=buyer.generation_calendar_view(destination.generation_id)
        self.assertEqual((view.anchor_year,view.current_year,view.current_contract.elapsed_years),(2027,2027,0))
        buyer._cash.pay(destination.cash_obligation_id,2000000,buyer._cash.revision,component='base:0')
        self.transition(buyer,from_year=2027,to_year=2028,expected_revision=buyer.revision,
            next_minimum_profile=VeteranMinimumProfile(2028,(('v',(7,7),('active_inactive',)*2),)))
        self.assertEqual(buyer.active_contract('v').elapsed_years,1)
        self.assertEqual(buyer.charges,(2000013,))
        self.assertIs(buyer.generation_accounting(destination.generation_id),agreement)
        self.assertEqual(buyer.cash_snapshot()['unpaid_total'],2000000)

    def test_calendar_buyer_keeps_former_closed_agreement_cash_and_debt(self):
        plan,source,destination=self.incoming_plan();buyer=self.calendar_buyer(prior_released=True)
        old_id=buyer.contract_identity('v').generation_id
        old=buyer.generation_accounting(old_id);old_cash=buyer.generation_cash(old_id)
        self.receive(buyer,plan,source)
        self.assertIs(buyer.generation_accounting(old_id),old)
        self.assertEqual(buyer.generation_cash(old_id),old_cash)
        self.assertEqual(buyer.contract_identity('v'),destination)
        self.assertEqual(buyer.cash_snapshot()['nominal_total'],7000000)
        self.assertEqual(buyer.cash_snapshot()['paid_total'],3000000)
        self.assertEqual(buyer.charges,(2000011,2000013))

    def test_calendar_buyer_preserves_authoritatively_expired_paid_agreement(self):
        plan,source,destination=self.incoming_plan()
        contract=ActiveContract(Offer('v',(2000000,),3000000),'synthetic exhausted original term')
        buyer=Ledger.from_opening(OpeningBooks(contracts=(contract,)),cap=10000000,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'v':(1000000,)*3})
        buyer._cash=CashBook((CashObligation('contract:v','v',5000000,5000000,'synthetic fully settled',
            (('signing_bonus',3000000),('base:0',2000000))),),'synthetic coverage')
        buyer.bind_team_identity('b');buyer._league_year=2026
        old_id=buyer.contract_identity('v').generation_id;old=buyer.generation_accounting(old_id)
        self.transition(buyer,expired_generation_ids=(old_id,))
        old_view=buyer.generation_calendar_view(old_id)
        self.assertTrue(old_view.authoritative_expired)
        self.receive(buyer,plan,source)
        self.assertIs(buyer.generation_accounting(old_id),old)
        self.assertIs(buyer.generation_calendar_view(old_id),old_view)
        self.assertEqual(buyer.contract_identity('v'),destination)
        self.assertEqual(buyer.cash_snapshot()['nominal_total'],9000000)
        self.assertEqual(buyer.cash_snapshot()['paid_total'],5000000)

    def test_calendar_buyer_rejections_preserve_all_books(self):
        plan,source,_=self.incoming_plan()
        for changes in ({'expected_revision':True},{'expected_revision':0},{'assignment_request_id':''},
                        {'assigned_from_team':'b'},{'assigned_from_generation_id':'foreign'}):
            buyer=self.calendar_buyer();before=(buyer.generation_snapshot(),buyer.generation_calendar_snapshot(),buyer.cash_snapshot())
            with self.subTest(changes=changes),self.assertRaises((ValueError,Rejected)):
                self.receive(buyer,plan,source,**changes)
            self.assertEqual((buyer.generation_snapshot(),buyer.generation_calendar_snapshot(),buyer.cash_snapshot()),before)
        for kind in ('cap','floor'):
            buyer=self.calendar_buyer()
            if kind=='cap':buyer._cap=Fraction(1)
            else:buyer._veteran_minimums['v']=(3000000,3000000)
            before=(buyer.generation_snapshot(),buyer.generation_calendar_snapshot(),buyer.cash_snapshot())
            with self.subTest(kind=kind),self.assertRaises(Rejected):self.receive(buyer,plan,source)
            self.assertEqual((buyer.generation_snapshot(),buyer.generation_calendar_snapshot(),buyer.cash_snapshot()),before)
        buyer=self.calendar_buyer()
        with self.assertRaises(Rejected):
            buyer.apply_preseason_trade_in(plan,expected_revision=buyer.revision,assignment_request_id='incoming-current',
                assigned_from_team='a',assigned_from_generation_id=source)

    def calendar_trade_inputs(self,ledger,**changes):
        from franchise.trades import PreseasonTradeScope,EXCLUDED_TRADE_LIABILITIES
        inputs=dict(generation_id=ledger.contract_identity('v').generation_id,
            scope=PreseasonTradeScope(2027,date(2027,6,2),date(2027,9,10),date(2027,9,10),
                EXCLUDED_TRADE_LIABILITIES,True,0,True,True,'synthetic calendar assignment'),
            record_id='calendar-assignment',expected_revision=1)
        inputs.update(changes);return inputs

    def test_calendar_trade_out_preserves_economic_cursor_and_earned_payments(self):
        ledger=self.ledger();gid=ledger.contract_identity('v').generation_id
        original=ledger.generation_accounting(gid)
        self.transition(ledger);ledger._last_transaction_date=date(2026,6,1)
        plan=ledger.apply_calendar_preseason_trade_out('v',**self.calendar_trade_inputs(ledger))
        assigned=ledger.generation_accounting(gid)
        self.assertIs(assigned.contract,original.contract)
        self.assertIs(assigned.original_contract,original.original_contract)
        self.assertEqual(assigned.outgoing_trade_calendar_year,2027)
        self.assertEqual(plan.original_contract.elapsed_years,1)
        self.assertEqual(assigned.payment_ceilings()['base:0'],2000000)
        self.assertEqual(assigned.payment_ceilings()['base:1'],0)
        self.assertEqual(ledger.cash_snapshot()['nominal_total'],5000000)
        self.assertEqual(ledger.cash_snapshot()['paid_total'],5000000)
        self.assertEqual(plan.buyer_cash.amount,4000000)
        self.assertEqual(plan.buyer_contract.offer.salaries,(2000000,2000000))
        self.assertEqual(ledger.charges,(1000011,1000013))
        self.assertNotIn('v',ledger._players)
        snapshot=ledger.generation_snapshot()
        self.assertEqual(snapshot['agreements'][0]['outgoing_trade_calendar_year'],2027)
        self.transition(ledger,from_year=2027,to_year=2028,expected_revision=2,
            next_minimum_profile=VeteranMinimumProfile(2028,(('v',(7,7),('active_inactive',)*2),)))
        self.assertEqual(ledger.charges,(1000013,))
        self.assertEqual(ledger.generation_calendar_view(gid).annual_charges(),plan.retained_bonus.annual_charges[1:])

    def test_calendar_trade_out_rejects_stale_identity_and_legacy_path_without_mutation(self):
        for changes in ({'generation_id':'foreign'},{'generation_id':True},{'expected_revision':True},
                        {'expected_revision':0},{'record_id':''}):
            ledger=self.ledger();self.transition(ledger)
            before=(ledger.generation_snapshot(),ledger.generation_calendar_snapshot(),ledger.cash_snapshot())
            with self.subTest(changes=changes),self.assertRaises((Rejected,ValueError)):
                ledger.apply_calendar_preseason_trade_out('v',**self.calendar_trade_inputs(ledger,**changes))
            self.assertEqual((ledger.generation_snapshot(),ledger.generation_calendar_snapshot(),ledger.cash_snapshot()),before)
        ledger=self.ledger();self.transition(ledger)
        with self.assertRaises(Rejected):
            ledger.apply_preseason_trade_out('v',**{key:value for key,value in self.calendar_trade_inputs(ledger).items()
                                                  if key!='generation_id'})

    def release_inputs(self,ledger,**changes):
        inputs=dict(generation_id=ledger.contract_identity('v').generation_id,
            scope=PreseasonReleaseScope(2027,date(2027,7,1),date(2027,9,10),EXCLUDED_LIABILITIES,
                True,True,0,'synthetic verified healthy release'),
            discount=DiscountProfile(2027,Fraction(0),'synthetic discount'),payment_year_offsets=(0,1),
            record_id='calendar-release',expected_revision=1)
        inputs.update(changes);return inputs

    def test_calendar_release_uses_current_cursor_and_retained_charges_age_once(self):
        ledger=self.ledger();gid=ledger.contract_identity('v').generation_id
        economic=ledger.generation_accounting(gid)
        self.transition(ledger)
        ledger._last_transaction_date=date(2026,6,1)
        plan=ledger.apply_calendar_preseason_release('v',**self.release_inputs(ledger))
        self.assertEqual(plan.original_contract.elapsed_years,1)
        archive=ledger.generation_accounting(gid)
        self.assertIs(archive.contract,economic.contract)
        self.assertEqual(archive.release_calendar_year,2027)
        self.assertEqual(archive.payment_ceilings()['base:0'],2000000)
        self.assertEqual(ledger.charges,(Fraction(1000011),Fraction(1000013)))
        self.assertEqual(ledger.cash_snapshot()['paid_total'],5000000)
        self.assertEqual(ledger.cash_snapshot()['unpaid_total'],0)
        self.assertNotIn('v',ledger._players)
        self.transition(ledger,from_year=2027,to_year=2028,expected_revision=2,
            next_minimum_profile=VeteranMinimumProfile(2028,(('v',(7,7),('active_inactive',)*2),)))
        self.assertEqual(ledger.charges,(Fraction(1000013),))
        self.assertEqual(ledger.generation_calendar_view(gid).annual_charges(),plan.charges()[1:])

    def test_invalid_calendar_release_cannot_change_financial_or_cash_state(self):
        for changes in ({'generation_id':'foreign'},{'generation_id':True},{'expected_revision':True},
                        {'payment_year_offsets':(0,)}, {'record_id':''}):
            ledger=self.ledger();self.transition(ledger)
            before=ledger.generation_snapshot();calendar=ledger.generation_calendar_snapshot()
            with self.subTest(changes=changes),self.assertRaises((Rejected,ValueError)):
                ledger.apply_calendar_preseason_release('v',**self.release_inputs(ledger,**changes))
            self.assertEqual(ledger.generation_snapshot(),before)
            self.assertEqual(ledger.generation_calendar_snapshot(),calendar)
        ledger=self.ledger();self.transition(ledger)
        with self.assertRaises(Rejected):
            ledger.apply_preseason_release('v',**{key:value for key,value in self.release_inputs(ledger).items()
                                                if key!='generation_id'})

    def ledger(self,term=3):
        contract=ActiveContract(Offer('v',(2000000,)*term,3000000),'synthetic economic terms')
        ledger=Ledger.from_opening(OpeningBooks(contracts=(contract,),retained=(ChargeRecord('debt',(7,11,13),'synthetic retained'),)),
            cap=10000000,roster_reserve=0,max_bonus_years=5,veteran_minimums={'v':(1000000,)*term})
        ledger._cash=CashBook((CashObligation('contract:v','v',contract.nominal_cash,5000000,
            'synthetic allocated settlement',(('signing_bonus',3000000),('base:0',2000000))),),'synthetic cash')
        ledger.bind_team_identity('a');ledger._league_year=2026
        return ledger

    def transition(self,ledger,**changes):
        inputs=dict(from_year=2026,to_year=2027,expected_revision=0,next_cap=9000000,roster_reserve=500,
            next_minimum_profile=VeteranMinimumProfile(2027,(('v',(7,7,7),('active_inactive',)*3),)),
            source='synthetic verified closing exclusions and next budget',expired_generation_ids=())
        inputs.update(changes);return ledger.apply_year_transition(**inputs)

    def test_survivor_ages_preserving_all_cash_and_economic_archives(self):
        ledger=self.ledger();gid=ledger.contract_identity('v').generation_id
        agreement=ledger.generation_accounting(gid);cash=ledger.cash_snapshot();charges=ledger.charges
        result=self.transition(ledger)
        self.assertEqual(ledger.active_contract('v').elapsed_years,1)
        self.assertIs(ledger.generation_accounting(gid),agreement)
        self.assertEqual(ledger.cash_snapshot(),cash)
        self.assertEqual(ledger.charges,charges[1:]);self.assertEqual(ledger.cap,9000000)
        self.assertEqual(result['league_year'],2027);self.assertEqual(ledger.revision,1)
        self.assertEqual(ledger.generation_calendar_view(gid).payment_ceilings(),agreement.payment_ceilings())
        with self.assertRaises(Rejected):ledger.preview_offer(Offer('v',(2000000,),0),1)
        # Payment remains explicit and enables another independent year close.
        original=ledger._cash.records['contract:v']
        ledger._cash.records['contract:v']=replace(original,paid=7000000,
            paid_components=original.paid_components+(('base:1',2000000),))
        self.transition(ledger,from_year=2027,to_year=2028,expected_revision=1,
            next_minimum_profile=VeteranMinimumProfile(2028,(('v',(7,7),('active_inactive',)*2),)))
        self.assertEqual(ledger.active_contract('v').elapsed_years,2)
        self.assertEqual(ledger.charges,charges[2:])

    def test_expiry_requires_exact_eligibility_and_full_settlement(self):
        ledger=self.ledger(1);gid=ledger.contract_identity('v').generation_id
        before=ledger.financial_snapshot();cash=ledger.cash_snapshot()
        with self.assertRaises(Rejected):self.transition(ledger)
        self.assertEqual(ledger.financial_snapshot(),before);self.assertEqual(ledger.cash_snapshot(),cash)
        self.transition(ledger,expired_generation_ids=(gid,))
        self.assertEqual(ledger._players,set());self.assertEqual(ledger.charges,(Fraction(11),Fraction(13)))
        self.assertEqual(ledger.generation_accounting(gid).status,'active')
        self.assertEqual(ledger.generation_calendar_view(gid).status,'expired')
        self.assertEqual(ledger.cash_snapshot(),cash)
        with self.assertRaises(Rejected):ledger.active_contract('v')

    def test_invalid_closing_inputs_do_not_mutate(self):
        for changes in ({'from_year':True},{'to_year':2028},{'expected_revision':True},
                        {'source':''},{'expired_generation_ids':('unknown',)},
                        {'next_minimum_profile':None},{'next_cap':-1}):
            ledger=self.ledger();before=ledger.financial_snapshot();cash=ledger.cash_snapshot()
            with self.subTest(changes=changes),self.assertRaises((Rejected,ValueError)):
                self.transition(ledger,**changes)
            self.assertEqual(ledger.financial_snapshot(),before);self.assertEqual(ledger.cash_snapshot(),cash)
        ledger=self.ledger();ledger._cash.records['contract:v']=replace(ledger._cash.records['contract:v'],paid_components=None)
        with self.assertRaises(Rejected):self.transition(ledger)

    def test_closed_release_and_assignment_keep_original_payment_rights(self):
        from tests import test_releases,test_trades
        for kind,fixture in (('release',test_releases.PreseasonReleaseTests()),('trade',test_trades.PreseasonTradeTests())):
            ledger=Ledger.from_opening(OpeningBooks(contracts=(fixture.contract(),)),cap=100,roster_reserve=0,
                max_bonus_years=5,veteran_minimums={'v':(1,1,1)})
            ledger._cash=CashBook((fixture.cash(),),'synthetic cash');ledger.bind_team_identity('a');ledger._league_year=2026
            if kind=='release':
                plan=fixture.plan()
                ledger.apply_preseason_release('v',scope=plan.scope,discount=plan.discount,
                    payment_year_offsets=plan.payment_year_offsets,record_id='release',expected_revision=0)
            else:ledger.apply_preseason_trade_out('v',scope=fixture.scope(),record_id='trade',expected_revision=0)
            gid=ledger.contract_identity('v').generation_id;agreement=ledger.generation_accounting(gid)
            cash=ledger.cash_snapshot();charges=ledger.charges;ceilings=agreement.payment_ceilings()
            self.transition(ledger,expected_revision=1)
            self.assertIs(ledger.generation_accounting(gid),agreement)
            self.assertEqual(ledger.generation_calendar_view(gid).payment_ceilings(),ceilings)
            self.assertEqual(ledger.charges,charges[1:]);self.assertEqual(ledger.cash_snapshot(),cash)

    def test_layered_survivor_and_assignment_keep_original_amendment_plan(self):
        from tests.test_restructures import PreseasonRestructureTests
        ledger=self.ledger();old=ledger._active_contracts['v']
        guaranteed=replace(old,offer=replace(old.offer,guaranteed_salaries=(2000000,0,0)))
        ledger._active_contracts['v']=guaranteed;ledger._contracts['v']=guaranteed.offer
        # This fixture replaces its original source before any operation.
        ledger._generation_agreements.clear();ledger._refresh_generation_agreement('v')
        cash=ledger._cash.records['contract:v']
        ledger._cash.records['contract:v']=replace(cash,paid=3000000,paid_components=(('signing_bonus',3000000),))
        plan=ledger.apply_preseason_restructure('v',scope=PreseasonRestructureTests().scope(),converted_base=1000000,
            record_id='conversion',expected_revision=0)
        cash=ledger._cash.records['contract:v']
        ledger._cash.records['contract:v']=replace(cash,paid=5000000,
            paid_components=(('signing_bonus',3000000),('bonus:conversion',1000000),('base:0',1000000)))
        gid=ledger.contract_identity('v').generation_id;before=ledger.cash_snapshot()
        self.transition(ledger,expected_revision=1)
        self.assertEqual(ledger.active_contract('v').bonus_layers,plan.contract.bonus_layers)
        self.assertIs(ledger.generation_accounting(gid).restructure,plan)
        self.assertEqual(ledger.cash_snapshot(),before)
        assigned=ledger.apply_calendar_preseason_trade_out('v',**self.calendar_trade_inputs(ledger,expected_revision=2))
        agreement=ledger.generation_accounting(gid)
        self.assertIs(agreement.restructure,plan)
        self.assertIs(agreement.contract,plan.contract)
        self.assertEqual(assigned.original_contract.bonus_layers,plan.contract.bonus_layers)
        self.assertEqual(agreement.payment_ceilings()['base:0'],1000000)
        self.assertEqual(ledger.charges,(Fraction(4000000,3)+11,Fraction(4000000,3)+13))
        self.assertEqual(assigned.seller_cash.amount+assigned.buyer_cash.amount,9000000)
        self.assertEqual(assigned.seller_cash.paid_components,tuple(tuple(row) for row in before['obligations'][0]['paid_components']))
