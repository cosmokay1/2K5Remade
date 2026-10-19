"""Retained opening liabilities survive real saved-amendment coordination."""
from fractions import Fraction
import struct
import unittest

from franchise.books import ChargeRecord, OpeningBooks
from franchise.cap import Ledger, Rejected
from franchise.guest_contracts import GuestContractTerms
from franchise import guest_application, guest_signing
from franchise.store import FranchiseStore
from tools.inspect_franchise_save import PLAYER_START
from tools.reconcile_signing_context import reconcile_signing_context
from tests import test_guest_amendment_application as fixtures


class RetainedGuestCapTests(unittest.TestCase):
    def sample(self, *, retained=None, adjustments=(), team_flag=0, two_players=False):
        sample=fixtures.GuestAmendmentApplicationTests()
        sample.opening_team_flag=team_flag
        sample.two_players=two_players
        sample.opening_retained=retained if retained is not None else (
            ChargeRecord('prior-release',(5000000,2000000),'Authored retained bonus schedule'),)
        sample.opening_adjustments=adjustments
        self.addCleanup(sample.doCleanups)
        sample.setUp()
        return sample

    def test_retained_debt_reaches_native_cap_and_survives_saved_settlement_and_reopen(self):
        s=self.sample();before=s.store.load_team('49ers').financial_snapshot()
        self.assertEqual(s.reply['result']['amendment_basis']['annual_team_charges_before'],[9766000,5523000])
        self.assertFalse(s.prepare()['write_authorized'])
        issued=guest_application.authorize(s.store,'issuance','journal',s.before,
            access_check=lambda:True,live_projection=s.projection())
        plan=issued['application_plan']
        self.assertEqual(plan['enforced_payroll_raw'],8658)
        self.assertEqual(plan['native_payroll_raw'],2000)
        self.assertEqual(before,s.store.load_team('49ers').financial_snapshot())
        with self.assertRaises(Rejected):
            guest_application.authorize(s.store,'again','journal',s.before,
                access_check=lambda:True,live_projection=s.projection())
        after=bytearray(s.before);terms=GuestContractTerms.from_context(**s.offer_raw)
        after[PLAYER_START+8]&=0xf7
        struct.pack_into('<H',after,PLAYER_START+10,terms.amount_word)
        flags=struct.unpack_from('<I',after,PLAYER_START+36)[0]
        flags=(flags&~0x0ff7000f)|(terms.years<<24)|(terms.shape_code<<16)|(terms.bonus_code<<20)|terms.years
        struct.pack_into('<I',after,PLAYER_START+36,flags)
        struct.pack_into('<I',after,0x44a8+0x124,plan['enforced_payroll_raw'])
        after=bytes(after)
        receipt=guest_signing.settle(s.store,'journal',after,access_check=lambda:True)
        self.assertEqual(receipt.charges,(3658000,3658000,2000000))
        reopened=FranchiseStore(s.store.path)
        self.assertEqual(reopened.load_team('49ers').charges,(8658000,5658000,2000000))
        self.assertEqual(reopened.load_team('49ers').cap,80500000)
        self.assertEqual(reopened.load_team('49ers')._opening_books.retained,s.opening_retained)
        self.assertEqual(guest_signing.inspect(reopened,'journal',after)['save_position'],'confirmed_after')
        self.assertEqual(guest_signing.settle(reopened,'journal',after,access_check=lambda:True).charges,receipt.charges)

    def test_retained_debt_can_make_native_roster_affordable_but_actual_offer_illegal(self):
        s=self.sample();source=s.store.load_team('49ers')
        books=OpeningBooks(legacy_contracts=tuple(source._legacy_contracts.values()),
            retained=(ChargeRecord('prior-release',(77000000,),'Authored prior obligation'),))
        ledger=Ledger.from_opening(books,cap=80500000,roster_reserve=0,max_bonus_years=5,
            veteran_minimums={s.player:(1000000,)*7})
        before=ledger.financial_snapshot()
        comparison=ledger.preview_legacy_amendment(s.offer,0,scope=s.scope)
        self.assertFalse(comparison['within_modeled_cap'])
        self.assertEqual(comparison['room_after'],-158000)
        with self.assertRaisesRegex(Rejected,'cap room'):
            ledger.apply_legacy_amendment('illegal',s.offer,0,proposal_request_id='p',source='authored',scope=s.scope)
        self.assertEqual(ledger.financial_snapshot(),before)

    def test_fractional_retained_debt_rounds_up_only_at_native_total(self):
        s=self.sample(retained=(ChargeRecord('prior-release',(Fraction(10000001,2),),'Authored exact retained amount'),))
        s.prepare();intent=s.intent();_,_,cap=guest_application.amendment_target(intent,s.before)
        self.assertEqual(cap['enforced_payroll_raw'],8659)
        self.assertEqual(Fraction(cap['rounding_charge']),Fraction(1999,2))
        self.assertLessEqual(Fraction(cap['native_room_after']),Fraction(cap['exact_room_after']))

    def test_free_agent_path_cannot_bypass_missing_supplemental_cap_adapter(self):
        s=self.sample();free=s.bindings['players'][1]['player_id']
        offer=GuestContractTerms.from_context(**s.offer_raw).to_offer(free)
        before=s.store.load_team('49ers').financial_snapshot()
        with s.store._connection() as db, self.assertRaisesRegex(Rejected,'roster charges'):
            guest_signing._before_books(s.store,db,s.bindings,s.before,offer,s.offer_raw,'49ers')
        self.assertEqual(s.store.load_team('49ers').financial_snapshot(),before)

    def test_saved_payroll_cannot_drop_retained_charge_before_settlement(self):
        s=self.sample();s.prepare()
        guest_application.authorize(s.store,'issuance','journal',s.before,
            access_check=lambda:True,live_projection=s.projection())
        before=s.store.load_team('49ers').financial_snapshot()
        # Even a one-unit reduction in the required saved payroll is refused.
        wrong=bytearray(s.before);struct.pack_into('<I',wrong,0x44a8+0x124,8657)
        with self.assertRaisesRegex(ValueError,'payroll'):
            guest_signing.settle(s.store,'journal',bytes(wrong),access_check=lambda:True)
        self.assertEqual(s.store.load_team('49ers').financial_snapshot(),before)
        with s.store._connection() as db:
            self.assertEqual(db.execute('SELECT state FROM guest_signings').fetchone()[0],'prepared')

    def test_unexplained_credit_is_not_treated_as_retained_debt(self):
        # An adjustment remains outside this adapter. In particular, the new
        # retained-debt support must never whitelist a cap-inflating credit.
        s=self.sample(adjustments=(ChargeRecord('credit',(-1000000,),'Unverified source credit'),))
        with self.assertRaisesRegex(ValueError,'checkpoint'):
            reconcile_signing_context(s.bindings,s.before,s.observation,s.store,
                expected_revision=s.revision,guest_offer=s.offer_raw,amendment_scope=s.scope)
        with self.assertRaises(ValueError):s.prepare()
        with s.store._connection() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM guest_signings').fetchone()[0],0)
