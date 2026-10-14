"""Authored synthetic layout fixtures only; no retail asset fixtures."""
import contextlib
import io
from pathlib import Path
import struct
import tempfile
import unittest
from tools.inspect_franchise_save import inspect_save,main,SIZE,PLAYER_START,PLAYER_STRIDE,STRING_START


class InspectFranchiseSaveTests(unittest.TestCase):
    def fixture(self):
        data=bytearray(SIZE);data[:4]=b'\x04\0\0\0';data[0x917EF]=26
        def pointer(location,target):struct.pack_into('<i',data,location,target-location+1)
        pointer(0x35C,0x1000);struct.pack_into('<H',data,0x358,1)
        data[0x45C4]=1;pointer(0x44A8,PLAYER_START);pointer(0x1000,PLAYER_START+PLAYER_STRIDE)
        cursor=STRING_START
        for slot,names in enumerate((('Synthetic','Starter'),('Authored','Freeagent'))):
            for field,name in zip((0x10,0x14),names):
                pointer(PLAYER_START+slot*PLAYER_STRIDE+field,cursor)
                value=(name+'\0').encode('utf-16le');data[cursor:cursor+len(value)]=value;cursor+=len(value)
        return data

    def test_read_only_membership_and_source_slots(self):
        data=self.fixture();before=bytes(data);result=inspect_save(before)
        self.assertEqual(result['year'],2026);self.assertEqual(result['size_bytes'],SIZE)
        self.assertEqual(len(result['teams']),32);self.assertEqual(result['membership_count'],2)
        self.assertEqual(result['teams']['49ers'][0],{'source_slot':0,'first_name':'Synthetic','last_name':'Starter'})
        self.assertEqual(result['free_agents'][0]['source_slot'],1)
        self.assertEqual(bytes(data),before)
        self.assertNotIn('salary',str(result));self.assertNotIn('ratings',str(result))

    def test_controlled_roster_transfer_changes_membership_without_financial_inference(self):
        data=self.fixture();before=inspect_save(bytes(data))
        data[0x45C4]=2;struct.pack_into('<i',data,0x44AC,PLAYER_START+PLAYER_STRIDE-0x44AC+1)
        struct.pack_into('<H',data,0x358,0)
        after=inspect_save(bytes(data))
        self.assertEqual(after['teams']['49ers'],before['teams']['49ers']+before['free_agents'])
        self.assertEqual(after['free_agents'],[]);self.assertEqual(after['membership_count'],2)
        self.assertNotEqual(after['payload_sha256'],before['payload_sha256'])

    def test_malformed_and_duplicate_roster_references_fail_closed(self):
        for scenario in range(6):
            with self.subTest(scenario=scenario):
                data=self.fixture()
                if scenario==0:struct.pack_into('<i',data,0x44A8,-0x44A8)
                if scenario==1:struct.pack_into('<i',data,0x44A8,PLAYER_START-0x44A8+2)
                if scenario==2:struct.pack_into('<i',data,0x1000,PLAYER_START-0x1000+1)
                if scenario==3:data[0x45C4]=72
                if scenario==4:struct.pack_into('<H',data,0x358,65535)
                if scenario==5:struct.pack_into('<i',data,0x35C,0x1001-0x35C+1)
                with self.assertRaises(ValueError):inspect_save(bytes(data))

    def test_invalid_name_pointer_encoding_and_missing_terminator_reject(self):
        for scenario in range(4):
            with self.subTest(scenario=scenario):
                data=self.fixture()
                if scenario==0:struct.pack_into('<i',data,PLAYER_START+0x10,1)
                if scenario==1:struct.pack_into('<i',data,PLAYER_START+0x10,STRING_START+1-(PLAYER_START+0x10)+1)
                if scenario==2:data[STRING_START:STRING_START+100]=b'A\0'*50
                if scenario==3:data[STRING_START:STRING_START+4]=b'\x00\xd8\0\0'
                with self.assertRaises(ValueError):inspect_save(bytes(data))

    def test_unsupported_format_and_cli_preserves_file(self):
        for data in (b'',b'ROST'+bytes(SIZE-4),bytes(SIZE),bytes(SIZE+1)):
            with self.assertRaises(ValueError):inspect_save(data)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'SAVEGAME.DAT';path.write_bytes(self.fixture());before=path.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()) as output:main([str(path)])
            self.assertIn('snapshot record locator',output.getvalue());self.assertEqual(path.read_bytes(),before)
