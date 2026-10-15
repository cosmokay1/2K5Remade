"""No source or retail assets: authored schedules and source receipts only."""
import hashlib
import json
import struct
import unittest
from unittest.mock import patch

from franchise.books import OpeningBooks, ChargeRecord
from franchise.cap import Ledger, Offer, Rejected
from tools import reconcile_pack_contract_source as source_tool
from tools.franchise_snapshot_bindings import resolve_bindings, create_bindings
from tools.inspect_franchise_save import PLAYER_START, PLAYER_STRIDE
from tools.export_legacy_contracts import legacy_contracts
import test_softdrink_snapshot as snapshot_fixtures


class PackContractSourceTests(unittest.TestCase):
    def setUp(self):
        fixture=snapshot_fixtures.SoftdrinkSnapshotTests();fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.payload=bytes(fixture.payload);self.bindings=fixture.create();self.xbe=fixture.xbe
        self.player=resolve_bindings(self.bindings,self.payload)[0]
        self.row={'name':'Synthetic Starter','team_name':'49ers','source_team':'49ers',
            'source':'https://example.invalid/authored-source','otc_id':123,
            'schedule_kind':'observed','fallback':None,
            'fit':{'fields':{'contract_value':829,'contract_type':1,'contract_bonus':4,
                'contract_length':2,'contract_remaining':2},
                'source_cap_dollars':[19060000,15000000],
                'represented_cap_dollars':[19064000,14092000]}}

    def report(self,rows=None):
        raw=json.dumps({'ledger':[self.row] if rows is None else rows,
            'source_receipt':{'asset_updated_at':'2026-09-24T12:40:52Z'}}).encode()
        with patch.object(source_tool,'AUDIT_SHA256',hashlib.sha256(raw).hexdigest()):
            return source_tool.reconcile_source(self.bindings,self.payload,raw)

    def test_deltas_reconstruct_source_without_replacing_raw_legacy_contract(self):
        report=self.report();entry=report['teams']['49ers']['matched'][0]
        correction=entry['opening_adjustment']
        self.assertEqual(correction['annual_charges'],[-4000,908000])
        self.assertIn('2026-09-24',correction['source'])
        legacy=legacy_contracts(self.bindings,self.payload)['49ers']
        books=OpeningBooks(legacy_contracts=legacy,adjustments=(ChargeRecord(
            correction['record_id'],tuple(correction['annual_charges']),correction['source']),))
        self.assertEqual(books.charges(),(19060000,15000000))
        self.assertEqual(OpeningBooks.from_dict(books.to_dict()),books)
        ledger=Ledger.from_opening(books,cap=19061000,roster_reserve=0,
            max_bonus_years=5,veteran_minimums={'free':(1,)})
        with self.assertRaises(Rejected):ledger.sign('too-much',Offer('free',(1001,),0),0)
        ledger.sign('fits',Offer('free',(1000,),0),0)
        self.assertEqual(ledger.charges,(19061000,15000000))
        self.assertFalse(report['complete_opening_books']);self.assertFalse(report['write_authorized'])

    def test_absent_ambiguous_changed_estimated_or_transferred_records_are_unresolved(self):
        for case in range(5):
            with self.subTest(case=case):
                rows=[self.row]
                if case==0:rows=[]
                if case==1:rows=[self.row,self.row]
                if case==2:self.row['fit']['fields']['contract_value']=828
                if case==3:self.row['schedule_kind']='modeled'
                if case==4:self.row['source_team']='Vikings'
                report=self.report(rows)
                self.assertEqual(report['matched_contracts'],0)
                self.assertEqual(report['unresolved_contracts'],1)
                # Restore fields changed by a prior case.
                self.row['fit']['fields']['contract_value']=829
                self.row['schedule_kind']='observed';self.row['source_team']='49ers'

    def test_duplicate_snapshot_names_do_not_share_a_source_obligation(self):
        payload=bytearray(self.payload)
        for field in (0x10,0x14):
            target=PLAYER_START+field+struct.unpack_from('<i',payload,PLAYER_START+field)[0]-1
            location=PLAYER_START+PLAYER_STRIDE+field
            struct.pack_into('<i',payload,location,target-location+1)
        self.payload=bytes(payload)
        self.bindings=create_bindings(self.payload,game_xbe=self.xbe)
        report=self.report()
        self.assertEqual(report['matched_contracts'],0)
        self.assertIn('ambiguous',report['teams']['49ers']['unresolved'][0]['reason'])

    def test_source_schedule_disagreement_and_unknown_source_file_reject(self):
        for source in (b'{}',b'',bytearray(b'{}')):
            with self.assertRaises(ValueError):
                source_tool.reconcile_source(self.bindings,self.payload,source)
        for values in ([19064001,14092000],[19064000],[-1,14092000],[True,14092000]):
            with self.subTest(values=values):
                if values==[19064001,14092000]:
                    self.row['fit']['represented_cap_dollars']=values
                else:self.row['fit']['source_cap_dollars']=values
                with self.assertRaises(ValueError):self.report()
                self.row['fit']['represented_cap_dollars']=[19064000,14092000]
