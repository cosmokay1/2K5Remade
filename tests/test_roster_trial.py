"""Authored save fixtures, no mod or retail asset in the test suite."""
import hashlib
import hmac
from pathlib import Path
import struct
import tempfile
import unittest
from tests import test_inspect_franchise_save as fixture_source
from tools.inspect_franchise_save import inspect_save
from tools.inspect_roster_save import inspect_roster
from tools.prepare_roster_trial import prepare_roster


def fixture():
    return bytearray(fixture_source.InspectFranchiseSaveTests().fixture()[0x2E0:0x2E0+0x91040])


class RosterTrialTests(unittest.TestCase):
    def test_membership_preserved_without_calendar_or_cap_claim(self):
        b=bytes(fixture());r=inspect_roster(b)
        self.assertEqual(r['teams']['49ers'][0]['last_name'],'Starter')
        self.assertEqual(r['membership_count'],2)
        self.assertEqual(r['nonstandard_name_pointers'],[])
        self.assertNotIn('year',r)
        self.assertNotIn('cap',r)
        with self.assertRaises(ValueError):inspect_save(b)

    def test_auxiliary_name_reported_but_record_bank_or_unterminated_name_rejected(self):
        data=fixture();field=0xAFA8+0x10;aux=0x749CC
        struct.pack_into('<i',data,field,aux-field+1)
        data[aux:aux+10]='Other'.encode('utf-16le')
        data[aux+10:aux+12]=b'\0\0'
        r=inspect_roster(bytes(data));self.assertEqual(r['teams']['49ers'][0]['first_name'],'Other')
        self.assertEqual(r['nonstandard_name_pointers'],[{'pointer_offset':field,'string_offset':aux}])
        for target in (0xAFA8, len(data)+4, 0x9103E):
            bad=bytearray(data);struct.pack_into('<i',bad,field,target-field+1)
            if target==0x9103E:bad[target:target+2]=b'A\0'
            with self.assertRaises(ValueError):inspect_roster(bytes(bad))

    def test_duplicate_members_and_invalid_bank_rejected(self):
        for mutate in (lambda d:struct.pack_into('<I',d,0x40,0),
                       lambda d:struct.pack_into('<i',d,0xD20,0xAFA8-0xD20+1)):
            d=fixture();mutate(d)
            with self.assertRaises(ValueError):inspect_roster(bytes(d))

    def test_packaging_preserves_native_container_and_refuses_unsafe_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'source.dat';data=bytes(fixture());src.write_bytes(data)
            sha=hashlib.sha256(data).hexdigest();dest=root/'trial'
            native=root/'reference';native.mkdir();reference=native/'SAVEGAME.DAT'
            # A different signed body, with unchanged layout, makes substitution visible.
            reference_data=bytearray(data);reference_data[0x100]^=1;reference_data=bytes(reference_data)
            reference.write_bytes(reference_data)
            typ='ROS\0'.encode('utf-16le');meta=b'\xff\xfe'+'Name=NATIVE\r\n'.encode('utf-16le')
            (native/'TYPE').write_bytes(typ);(native/'SaveMeta.xbx').write_bytes(meta)
            manifest=b'format=1\ncontainer=123456ABCDEF\ntype=ROS\nname=NATIVE\n'
            (native/'.nfl2k5-save.ini').write_bytes(manifest)
            (native/'EXTRA').write_bytes(hmac.digest(bytes(16),reference_data,'sha1'))
            args=dict(expected_sha256=sha,source_url='https://example.test/creator',native_template=reference)
            report=prepare_roster(src,dest,**args)
            for folder in ('rosters/NATIVE','UDATA/53450030/123456ABCDEF'):
                out=dest/'saves'/folder
                self.assertEqual((out/'SAVEGAME.DAT').read_bytes(),data)
                self.assertEqual((out/'EXTRA').read_bytes(),hmac.digest(bytes(16),data,'sha1'))
                self.assertEqual((out/'TYPE').read_bytes(),typ)
                self.assertEqual((out/'SaveMeta.xbx').read_bytes(),meta)
            self.assertEqual((dest/'saves/rosters/NATIVE/.nfl2k5-save.ini').read_bytes(),manifest)
            self.assertEqual(reference.read_bytes(),reference_data);self.assertEqual(src.read_bytes(),data)
            self.assertTrue(report['native_container_metadata_preserved'])
            self.assertFalse(report['game_load_verified']);self.assertFalse(report['cap_reconciled'])
            with self.assertRaises(FileExistsError):prepare_roster(src,dest,**args)
            with self.assertRaises(ValueError):prepare_roster(src,root/'bad',**{**args,'expected_sha256':'0'*64})
            self.assertFalse((root/'bad').exists())
            (native/'EXTRA').write_bytes(bytes(20))
            with self.assertRaises(ValueError):prepare_roster(src,root/'bad-ref',**args)
            self.assertFalse((root/'bad-ref').exists())

    def test_metadata_mismatch_cannot_become_a_new_container(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'source.dat';data=bytes(fixture());src.write_bytes(data)
            ref=root/'ref';ref.mkdir();(ref/'SAVEGAME.DAT').write_bytes(data)
            (ref/'TYPE').write_bytes('ROS\0'.encode('utf-16le'))
            (ref/'EXTRA').write_bytes(hmac.digest(bytes(16),data,'sha1'))
            (ref/'SaveMeta.xbx').write_bytes(b'\xff\xfe'+'Name=OTHER\r\n'.encode('utf-16le'))
            (ref/'.nfl2k5-save.ini').write_text('format=1\ncontainer=123456ABCDEF\ntype=ROS\nname=NATIVE\n')
            with self.assertRaises(ValueError):prepare_roster(src,root/'trial',expected_sha256=hashlib.sha256(data).hexdigest(),source_url='https://example.test/creator',native_template=ref/'SAVEGAME.DAT')
            self.assertFalse((root/'trial').exists())


if __name__=='__main__':unittest.main()
