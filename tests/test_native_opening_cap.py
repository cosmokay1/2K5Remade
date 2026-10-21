from copy import deepcopy
from hashlib import sha256
import struct
import unittest

from franchise import opening_native,guest_application
from franchise.cap import Rejected
from franchise.saved_checkpoint import projection,verify
from tests import test_retained_guest_cap as fixtures
from franchise.books import ChargeRecord


class NativeOpeningCapTests(unittest.TestCase):
    def sample(self):
        helper=fixtures.RetainedGuestCapTests();self.addCleanup(helper.doCleanups)
        return helper.sample(adjustments=(ChargeRecord('opening-calibration',(-1000000,), 'Authored explicit cap adjustment'),))

    def test_all_team_budgets_persist_restore_and_never_grant_signing(self):
        s=self.sample();before=s.before
        after,proof=opening_native.build(s.store,s.bindings,before,source={'fixture':'sha256:authored'})
        self.assertEqual(before,s.before)
        self.assertFalse(proof['signing_authorized'])
        self.assertEqual(struct.unpack_from('<I',after,0x44a8+0x124)[0],8766)
        opening_native.register(s.store,proof,after)
        with s.store._connection() as db:self.assertTrue(verify(s.store,db,after))
        finance,identity=projection(after)[1:]
        result=guest_application.restore_cap(s.store,'restore',after,source_epoch=7,
            loaded_payload_sha256=sha256(after).hexdigest(),
            live_projection={'finance':sha256(finance).hexdigest(),'identity':sha256(identity).hexdigest()},
            finance_payrolls=[struct.unpack_from('<I',finance,48+12*i)[0] for i in range(32)],
            connection_check=lambda:True)
        plans=[result['cap_plan']]+result['additional_cap_plans']
        self.assertEqual([p['team_index'] for p in plans],list(range(32)))
        self.assertEqual(plans[0]['native_payroll_raw'],4766)
        self.assertEqual(plans[0]['enforced_payroll_raw'],8766)
        with self.assertRaises(Rejected):opening_native.register(s.store,proof,after)

    def test_tampering_or_uncounted_ledger_credit_is_held(self):
        s=self.sample();after,proof=opening_native.build(s.store,s.bindings,s.before,source={'fixture':'authored'})
        opening_native.register(s.store,proof,after)
        for at in (0x44a8+0x124,):
            corrupt=bytearray(after);corrupt[at]^=1
            with s.store._connection() as db, self.assertRaises(Rejected):verify(s.store,db,bytes(corrupt))
        changed=deepcopy(proof);changed['opening_obligations']['49ers']-=1
        with s.store._connection() as db,self.assertRaises(Rejected):opening_native.verify(s.store,db,after,proof=changed)

    def test_no_source_and_unrecorded_projection_have_no_authority(self):
        s=self.sample()
        with self.assertRaises(ValueError):opening_native.build(s.store,s.bindings,s.before,source={})
        after,proof=opening_native.build(s.store,s.bindings,s.before,source={'fixture':'authored'})
        with s.store._connection() as db,self.assertRaises(Rejected):verify(s.store,db,after)
