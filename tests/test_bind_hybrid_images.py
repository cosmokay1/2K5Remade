from copy import deepcopy
from hashlib import sha256
import struct
import unittest

from tests import test_plan_hybrid_roster as fixtures
from tools.bind_hybrid_images import bind_club_images


class ClubImageBindingTests(unittest.TestCase):
    def inputs(self):
        payload=bytes(fixtures.HybridPlanTests().roster())
        report=dict(native_sha256=sha256(payload).hexdigest(),source_sha256=sha256(payload).hexdigest(),
            source_free_agents_included=False,matched=[dict(gsis_id='authored',source_slot=0,native_slot=0,
            preserve_native_photo_id=struct.unpack_from('<H',payload,0xAFA8+6)[0])],unresolved_source=[])
        return payload,report

    def test_only_verified_club_photo_bytes_change_and_free_agent_bytes_stay_intact(self):
        payload,report=self.inputs()
        output,receipt=bind_club_images(payload,payload,report,dict(bindings=[],slots=[]),{})
        self.assertEqual(output,payload)
        self.assertTrue(receipt['all_club_images_bound'])
        self.assertFalse(receipt['ready_for_franchise_test'])
        self.assertFalse(receipt['game_dispatch_verified'])
        self.assertFalse(receipt['signing_authorized'])

    def test_missing_official_photo_binds_only_after_asset_hash_and_source_slot_match(self):
        payload,report=self.inputs()
        report['unresolved_source']=[dict(gsis_id='authored',reason='no_verified_native_image_record',
                                         player=dict(source_slot=0))];report['matched']=[]
        _,missing=bind_club_images(payload,payload,report,dict(bindings=[],slots=[]),{})
        self.assertFalse(missing['all_club_images_bound'])
        data=b'authored native cache bytes'
        asset=dict(gsis_id='authored',source_slot=0,photo_id=50000,
                   source_url='https://static.www.nfl.com/authored')
        manifest=dict(bindings=[asset],slots=[dict(name='50000',size=len(data),sha256=sha256(data).hexdigest())])
        output,receipt=bind_club_images(payload,payload,report,manifest,{'50000':data})
        self.assertEqual(struct.unpack_from('<H',output,0xAFA8+6)[0],50000)
        self.assertEqual(output[:0xAFA8+6],payload[:0xAFA8+6])
        self.assertEqual(output[0xAFA8+8:],payload[0xAFA8+8:])
        self.assertTrue(receipt['all_club_images_bound'])
        for bad in [b'corrupt',None]:
            with self.assertRaises(ValueError):bind_club_images(payload,payload,report,manifest,{'50000':bad})
        manifest['bindings'][0]['source_slot']=1
        with self.assertRaises(ValueError):bind_club_images(payload,payload,report,manifest,{'50000':data})

    def test_wrong_roster_missing_identity_duplicate_and_out_of_range_are_rejected(self):
        payload,report=self.inputs()
        for transform in [lambda r:r.update(source_free_agents_included=True),
                          lambda r:r.update(source_sha256='a'*64),
                          lambda r:r.update(matched=[]),
                          lambda r:r['matched'].append(deepcopy(r['matched'][0])),
                          lambda r:r['matched'][0].update(native_slot=-1)]:
            bad=deepcopy(report);transform(bad)
            with self.assertRaises(ValueError):bind_club_images(payload,payload,bad,dict(bindings=[],slots=[]),{})
