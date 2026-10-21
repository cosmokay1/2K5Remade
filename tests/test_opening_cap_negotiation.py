from hashlib import sha256
import json
from pathlib import Path
import struct
import unittest

from franchise import opening_native,guest_application,guest_signing
from franchise.books import OpeningBooks,ChargeRecord
from franchise.bridge import Bridge
from franchise.cap import Ledger,Rejected
from franchise.saved_checkpoint import projection,verify
from franchise.store import FranchiseStore
from tests import test_retained_guest_cap as fixtures
from tests import test_follow_on_guest_amendment as native_fixture
from tools.inspect_franchise_save import TEAMS


class OpeningNegotiationTests(unittest.TestCase):
    def test_imported_salary_bonus_and_room_survive_real_journal_settlement_and_reopen(self):
        helper=fixtures.RetainedGuestCapTests();self.addCleanup(helper.doCleanups)
        s=helper.sample();ledgers={}
        for team in TEAMS:
            old=s.store.load_team(team);books=old._opening_books
            extra=(ChargeRecord('native-base:'+s.player,(100000,)*2,'authored source base'),
                   ChargeRecord('native-nonbase:'+s.player,(-20000,)*2,'authored source nonbase')) if team=='49ers' else ()
            ledgers[team]=Ledger.from_opening(OpeningBooks(legacy_contracts=books.legacy_contracts,
                retained=books.retained,adjustments=books.adjustments+extra),cap=old.cap,
                roster_reserve=old.roster_reserve,max_bonus_years=5,veteran_minimums=old._veteran_minimums,
                observed_player_ids=old._observed_player_ids,observed_player_source=old._observed_player_source)
        path=Path(s.store.path).with_name('opening.sqlite');s.store=FranchiseStore(path)
        s.store.create_franchise(ledgers,seed=s.bindings['personality_seed'])
        for team,ledger in ledgers.items():s.store.initialize_cash(team,(),source='authored imported cash unknown',
            unknown_legacy_players=tuple(ledger._legacy_contracts))
        s.before,proof=opening_native.build(s.store,s.bindings,s.before,source={'fixture':'authored full league'})
        opening_native.register(s.store,proof,s.before);s.current=s.before
        def live():
            _,finance,identity=projection(s.current)
            return dict(finance=sha256(finance).hexdigest(),identity=sha256(identity).hexdigest())
        s.projection=live;s.observation['team']['payroll_raw']=struct.unpack_from('<I',s.before,0x44a8+0x124)[0]
        from franchise.salary_clock import bind_salary_clock
        s.scope=bind_salary_clock(s.bindings,s.before,s.observation,s.clock)
        s.revision=s.store.load_team('49ers').revision
        s.bridge=Bridge(s.store,provider=lambda _:json.dumps(dict(action='accept',reason='Authored consent.',salaries=None,signing_bonus=None)),
            access_check=lambda:True,guest_snapshot=(s.bindings,s.before),guest_signing_reader=lambda:s.current)
        context=s.store.player_context('49ers',s.player)
        reply=s.bridge.handle(dict(protocol=1,request_id='proposal',operation='negotiate_proposal',team_id='49ers',
            offer=s.offer.to_dict(),expected_revision=s.revision,timeout_ms=5000,
            personality=context['personality'],relationships=context['relationships'],performance={},
            contract_format='original_fxg_v1',amendment_rule='legacy_bonus_carry_v1',amendment_scope=s.scope.to_dict()))
        self.assertIsNone(reply['error'],reply)
        s.prepare()
        plan=guest_application.authorize(s.store,'issue','journal',s.before,access_check=lambda:True,
            live_projection=s.projection())['application_plan']
        self.assertEqual(plan['enforced_payroll_raw'],8638)
        s.current=native_fixture.FollowOnAmendmentTests().apply(s.before,s.offer_raw,plan)
        guest_signing.settle(s.store,'journal',s.current,access_check=lambda:True)
        reopened=FranchiseStore(path)
        self.assertEqual(reopened.load_team('49ers').charges[0],8638000)
        with reopened._connection() as db:
            self.assertTrue(verify(reopened,db,s.current))
            with self.assertRaises(Rejected):verify(reopened,db,s.before)
        # Replay the persisted consent and source correction, not an aggregate refill.
        self.assertEqual(reopened.load_team('49ers').financial_snapshot(),s.store.load_team('49ers').financial_snapshot())
