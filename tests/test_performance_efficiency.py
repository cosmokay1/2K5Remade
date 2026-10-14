import copy
import unittest
from franchise.performance import COUNTERS, Observation, PerformanceEvidence


class ObservedEfficiencyTests(unittest.TestCase):
    def evidence(self, records=(), **changes):
        args=dict(player_id='v',window='synthetic week1',mode='played',observations=records,
                  coverage='synthetic controlled complete observation',team_id='a',complete_window=True)
        args.update(changes)
        return PerformanceEvidence(**args)

    def record(self, counter, value):
        return Observation(counter,value,'synthetic event capture: '+counter)

    def test_exact_ratios_preserve_opportunity_sample_and_both_sources(self):
        evidence=self.evidence(tuple(self.record(key,value) for key,value in (
            ('targets',4),('receptions',3),('receiving_yards',30),('pass_attempts',6),('completions',4),
            ('passing_yards',42),('rush_attempts',3),('rushing_yards',12))))
        original=copy.deepcopy(evidence.to_context())
        context=evidence.efficiency_context()
        self.assertEqual((context['player_id'],context['window'],context['mode'],context['team_id']),
                         ('v','synthetic week1','played','a'))
        self.assertTrue(context['complete_window'])
        expected={'reception_per_target':('3/4',4),'receiving_yards_per_target':('15/2',4),
            'completions_per_pass_attempt':('2/3',6),'passing_yards_per_pass_attempt':(7,6),
            'rushing_yards_per_rush_attempt':(4,3)}
        for key,(value,sample) in expected.items():
            ratio=context['efficiencies'][key]
            self.assertEqual((ratio['value'],ratio['sample_count']),(value,sample))
            self.assertIsNone(ratio['unavailable_reason'])
            self.assertEqual(ratio['numerator']['source'],'synthetic event capture: '+ratio['numerator']['counter'])
            self.assertEqual(ratio['denominator']['source'],'synthetic event capture: '+ratio['denominator']['counter'])
        self.assertEqual(evidence.to_context(),original)
        self.assertEqual(PerformanceEvidence.from_context(original).to_context(),original)

    def test_unknown_and_zero_denominators_are_unavailable_not_estimated(self):
        evidence=self.evidence((self.record('receptions',0),
            Observation('targets',None,'synthetic fastsim source','Engine did not capture targets'),
            self.record('pass_attempts',0),self.record('completions',0)))
        ratios=evidence.efficiency_context()['efficiencies']
        target=ratios['reception_per_target']
        self.assertIsNone(target['value'])
        self.assertIsNone(target['sample_count'])
        self.assertEqual(target['denominator']['source'],'synthetic fastsim source')
        self.assertIn('Engine did not capture targets',target['unavailable_reason'])
        passing=ratios['completions_per_pass_attempt']
        self.assertIsNone(passing['value'])
        self.assertEqual(passing['sample_count'],0)
        self.assertIn('zero observed opportunities',passing['unavailable_reason'])
        missing=ratios['rushing_yards_per_rush_attempt']
        self.assertIsNone(missing['numerator']['source'])
        self.assertIn('Counter not supplied',missing['unavailable_reason'])

    def test_known_opportunities_with_missing_production_keep_sample_count(self):
        ratios=self.evidence((self.record('targets',8),)).efficiency_context()['efficiencies']
        self.assertIsNone(ratios['receiving_yards_per_target']['value'])
        self.assertEqual(ratios['receiving_yards_per_target']['sample_count'],8)
        self.assertIsNone(ratios['reception_per_target']['value'])

    def test_signed_yards_and_observed_zero_production_are_exact(self):
        records=(self.record('targets',2),self.record('receptions',0),self.record('receiving_yards',-5),
                 self.record('rush_attempts',2),self.record('rushing_yards',-3))
        ratios=self.evidence(records,mode='cpu_played').efficiency_context()['efficiencies']
        self.assertEqual(ratios['reception_per_target']['value'],0)
        self.assertEqual(ratios['receiving_yards_per_target']['value'],'-5/2')
        self.assertEqual(ratios['rushing_yards_per_rush_attempt']['value'],'-3/2')

    def test_canonical_reconstruction_rejects_omitted_or_inconsistent_evidence(self):
        original=self.evidence((self.record('targets',2),self.record('receptions',1))).to_context()
        cases=[]
        changed=copy.deepcopy(original);del changed['observations']['targets']['source'];cases.append(changed)
        changed=copy.deepcopy(original);changed['missing_counters']=[];cases.append(changed)
        changed=copy.deepcopy(original);changed['observations']['receptions']['value']=3;cases.append(changed)
        changed=copy.deepcopy(original);changed['observations']['targets']['value']=True;cases.append(changed)
        changed=copy.deepcopy(original);changed['complete_window']=1;cases.append(changed)
        changed=copy.deepcopy(original);changed['mode']=[];cases.append(changed)
        changed=copy.deepcopy(original);changed['extra']=1;cases.append(changed)
        changed=copy.deepcopy(original);changed['team_id']=None;cases.append(changed)
        for case in cases:
            with self.subTest(case=case),self.assertRaises(ValueError):
                PerformanceEvidence.from_context(case)

    def test_legacy_source_context_has_no_added_derived_fields(self):
        evidence=self.evidence((),team_id=None,complete_window=None,mode='fast_sim')
        context=evidence.to_context()
        self.assertEqual(set(context),{'player_id','window','mode','coverage','observations','missing_counters'})
        self.assertEqual(context['missing_counters'],sorted(COUNTERS))
        self.assertEqual(PerformanceEvidence.from_context(context),evidence)
        self.assertNotIn('pressures_per_dropback',evidence.efficiency_context()['efficiencies'])
