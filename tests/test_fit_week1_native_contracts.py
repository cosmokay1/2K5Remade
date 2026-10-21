import unittest
from tools.fit_week1_native_contracts import fit_fields,source_schedule,refit_opening_franchise
from franchise.legacy_contracts import original_annual_rows


class NativeContractFitTests(unittest.TestCase):
    def test_fresh_refit_preserves_flags_and_refuses_changed_prior_terms(self):
        from hashlib import sha256
        from tests.test_build_week1_opening import OpeningBundleTests
        from tools.inspect_franchise_save import PLAYER_START
        fixture=OpeningBundleTests();self.addCleanup(fixture.doCleanups)
        payload,old,*_=fixture.inputs();saved=bytearray(payload)
        from tools.inspect_franchise_calendar import inspect_calendar
        start=inspect_calendar(payload)['scheduler_offset']
        saved[start+1]=7;saved[start+4]=4;saved[start+6]=0
        saved[PLAYER_START+36]|=0xf0
        new=bytearray(old);new[0xAFA8+10]^=1;new[0xAFA8+36]=(new[0xAFA8+36]&0xf0)|4
        new[0xAFA8+39]=(new[0xAFA8+39]&0xf0)|4
        prior=dict(output_sha256=sha256(old).hexdigest(),players={'one':dict(source_slot=0,team='SF')})
        current=dict(prior,output_sha256=sha256(new).hexdigest())
        result,proof=refit_opening_franchise(bytes(saved),old,bytes(new),prior,current)
        self.assertEqual(result[PLAYER_START+36],0xf4)
        self.assertEqual(proof['changed_players'],['one'])
        self.assertEqual(result[PLAYER_START+25:PLAYER_START+28],saved[PLAYER_START+25:PLAYER_START+28])
        saved[PLAYER_START+10]^=2
        with self.assertRaises(ValueError):
            refit_opening_franchise(bytes(saved),old,bytes(new),prior,current)

    def test_rookie_term_cannot_collapse_when_raw_archive_has_no_annual_rows(self):
        charge=dict(gsis_id='rookie',team='NYG',cap_dollars=1000000)
        archive=[dict(gsis_id='rookie',team='Giants',is_active=True,year_signed=2026,draft_year=2026,years=4,season_history=[])]
        with self.assertRaisesRegex(ValueError,'multi-year rookie'):
            source_schedule(charge,archive,2026)
        archive[0]['season_history']=[dict(year=str(2026+i),team='Giants',cap_number=1+i/10) for i in range(4)]
        self.assertEqual(source_schedule(charge,archive,2026)[0],[1000000,1100000,1200000,1300000])
        archive[0]['season_history'].pop()
        with self.assertRaisesRegex(ValueError,'truncate'):
            source_schedule(charge,archive,2026)

    def test_approved_modeled_rookie_keeps_all_years_and_nominal_total(self):
        charge=dict(gsis_id='rookie',team='NYG',cap_dollars=1000000,basis='modeled_rookie_allocation',
            nominal_total_preserved=True,signed_total_dollars=4600000,
            annual_cap_projection=[dict(year=2026+i,cap_dollars=1000000+i*100000) for i in range(4)])
        archive=[dict(gsis_id='rookie',team='Giants',is_active=True,year_signed=2026,draft_year=2026,years=4,season_history=[])]
        self.assertEqual(source_schedule(charge,archive,2026),([1000000,1100000,1200000,1300000],None,'approved_modeled_rookie_schedule'))
        charge['annual_cap_projection'].pop()
        with self.assertRaises(ValueError):source_schedule(charge,archive,2026)

    def test_positive_sourced_bonus_is_not_erased_for_an_exact_no_bonus_fit(self):
        result=fit_fields([4000000,4000000],scale=4,bonus_target=1200000)
        self.assertGreater(result['fields']['contract_bonus'],0)
        rows=original_annual_rows(result['fields']['contract_value'],result['fields']['contract_bonus'],result['fields']['contract_type'],2)
        self.assertEqual(result['represented_cap_dollars'],[r['original_game_charge_dollars']*4 for r in rows])
        self.assertEqual([a+b for a,b in zip(result['represented_cap_dollars'],result['residual_dollars'])],[4000000]*2)
        self.assertFalse(result['cash_or_guarantees_verified'])

    def test_guarantees_never_supply_bonus_and_wrong_team_future_is_not_imported(self):
        charge=dict(gsis_id='one',team='NYG',cap_dollars=1000000)
        archive=[dict(gsis_id='one',is_active=True,guaranteed=2,
            season_history=[dict(year='2026',team='Giants',cap_number=1,prorated_bonus=None),
                            dict(year='2027',team='Bears',cap_number=2)])]
        targets,bonus,basis=source_schedule(charge,archive,2026)
        self.assertEqual(targets,[1000000]);self.assertIsNone(bonus)
        archive.append(archive[0].copy())
        self.assertEqual(source_schedule(charge,archive,2026),([1000000],None,'accepted_current_charge_only'))

    def test_rounding_is_reported_and_invalid_native_inputs_are_held(self):
        result=fit_fields([1145000],scale=4)
        self.assertLessEqual(abs(result['residual_dollars'][0]),20000)
        for targets,scale,bonus in [([],4,None),([0],4,None),([1000],3,None),([1000],4,-1),([10**15],4,None)]:
            with self.assertRaises(ValueError):fit_fields(targets,scale=scale,bonus_target=bonus)
