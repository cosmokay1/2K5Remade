from copy import deepcopy
from hashlib import sha256
import unittest

from tests import test_confirm_saved_signing as fixtures
from tools.build_week1_opening import build_opening,rookie_amendment_hold
from tools.reconcile_week1_contracts import CLUBS
from franchise.store import from_config


class OpeningBundleTests(unittest.TestCase):
    def inputs(self):
        fixture=fixtures.SavedSigningConfirmationTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        payload=bytearray(fixture.before);payload[0x917ef]=26;payload=bytes(payload)
        roster=payload[0x2e0:0x91320]
        fit=dict(output_sha256=sha256(roster).hexdigest(),game_dollar_scale=1,players={'owned':dict(
            represented_cap_dollars=[4766000,3523000],source_cap_dollars=[5000000,4000000],
            source_base_dollars=[3500000,2000000],source_nonbase_dollars=[1500000,2000000])})
        assembly=dict(bindings={'owned':0,'free':1})
        charge=dict(season_year=2026,league_cap=80500000,input_sha256='a'*64,
                    teams={c:dict(players=[]) for c in CLUBS})
        charge['teams']['SF']['players']=[dict(team='SF',gsis_id='owned',player='Synthetic Starter',roster_status='ACT',cap_dollars=5000000),
            dict(team='SF',gsis_id=None,player='Unknown One',roster_status='DEV',cap_dollars=1000000),
            dict(team='SF',gsis_id=None,player='Unknown Two',roster_status='RES',cap_dollars=2000000)]
        book=dict(calibration_policy='published_room_target',salary_input_sha256='a'*64,proxy_source={'as_of':'2026-10-20'},
            teams={c:dict(retained_dollars=0,net_adjustment_dollars=0,modeled_cap_room_dollars=80500000,
                          retained_basis='authored',adjustment_basis='authored') for c in CLUBS})
        book['teams']['SF'].update(retained_dollars=1000000,net_adjustment_dollars=500000,modeled_cap_room_dollars=72000000)
        archive=[dict(gsis_id='owned',is_active=True,season_history=[
            dict(year='2026',team='49ers',cap_number=5,base_salary=3.5,prorated_bonus=1.5),
            dict(year='2027',team='49ers',cap_number=4,base_salary=2,prorated_bonus=2)])]
        return payload,roster,fit,assembly,charge,book,archive

    def test_all_clubs_balance_and_two_unbound_obligations_are_not_collapsed(self):
        inputs=self.inputs();before=deepcopy(inputs)
        bundle,bindings,report=build_opening(*inputs,seed='authored fresh fixture')
        ledger=from_config(bundle['teams']['49ers'])
        self.assertEqual(ledger.room,72000000)
        self.assertEqual(report['teams']['49ers']['off_roster_obligations'],2)
        self.assertEqual(len(ledger._opening_books.retained),3)
        self.assertEqual(len(bundle['teams']),32)
        self.assertEqual(inputs,before)
        self.assertFalse(report['game_verified']);self.assertFalse(report['signing_authorized'])
        player=next(c.player_id for c in ledger._opening_books.legacy_contracts)
        self.assertTrue(any(r.record_id=='native-base:'+player for r in ledger._opening_books.adjustments))

    def test_original_rookie_lock_does_not_extend_to_a_replacement_deal(self):
        row=dict(gsis_id='rookie',is_active=True,team='Giants',year_signed=2025,draft_year=2025,years=4,draft_round=1)
        self.assertTrue(rookie_amendment_hold([row],'rookie','NYG',2026))
        self.assertFalse(rookie_amendment_hold([row],'rookie','NYG',2028))
        row.update(year_signed=2026,years=1)
        self.assertFalse(rookie_amendment_hold([row],'rookie','NYG',2026))

    def test_wrong_roster_membership_or_room_model_cannot_be_bound(self):
        inputs=list(self.inputs());inputs[2]['output_sha256']='b'*64
        with self.assertRaises(ValueError):build_opening(*inputs,seed='authored')
        inputs=list(self.inputs());inputs[5]['teams']['SF']['modeled_cap_room_dollars']+=1
        with self.assertRaises(ValueError):build_opening(*inputs,seed='authored')
