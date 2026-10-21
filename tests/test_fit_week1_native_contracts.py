import unittest
from tools.fit_week1_native_contracts import fit_fields,source_schedule
from franchise.legacy_contracts import original_annual_rows


class NativeContractFitTests(unittest.TestCase):
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
