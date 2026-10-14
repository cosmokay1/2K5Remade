import json
import unittest
from franchise.cap import Ledger,Offer
from franchise.negotiation import Negotiation
from franchise.performance import Observation,PerformanceEvidence


class NegotiationEfficiencyTests(unittest.TestCase):
    def evidence(self):
        return PerformanceEvidence('p','observed game','played',(
            Observation('receptions',2,'synthetic outcome counter'),
            Observation('targets',3,'synthetic opportunities'),
            Observation('pressures',None,'synthetic capture','not recorded'),
        ),'single sourced game')

    def session(self,performance):
        ledger=Ledger(cap=100,existing_charges=(0,),roster_reserve=0,max_bonus_years=5,
            veteran_minimums={'p':(1,)})
        return Negotiation(ledger,player_id='p',personality={},performance=performance,
            relationships={},access_check=lambda:None)

    def test_typed_and_wire_context_deliver_same_exact_rates_with_samples(self):
        for evidence in (self.evidence(),self.evidence().to_context()):
            session=self.session(evidence)
            def provider(context):
                derived=context['observed_efficiency']
                self.assertEqual(derived['efficiencies']['reception_per_target']['value'],'2/3')
                self.assertEqual(derived['efficiencies']['reception_per_target']['sample_count'],3)
                self.assertEqual(derived['mode'],'played')
                context['observed_efficiency']['efficiencies']['reception_per_target']['value']=1
                return json.dumps({'action':'reject','reason':'Small observed sample','salaries':None,'signing_bonus':None})
            event=session.respond('proposal',Offer('p',(10,),0),provider)
            self.assertEqual(event['evidence']['observed_efficiency'],self.evidence().efficiency_context())
            self.assertEqual(session.ledger.revision,0)

    def test_legacy_descriptive_data_does_not_invent_rates(self):
        session=self.session({'yards':100})
        def provider(context):
            self.assertNotIn('observed_efficiency',context)
            return json.dumps({'action':'reject','reason':'Opportunities unavailable','salaries':None,'signing_bonus':None})
        self.assertNotIn('observed_efficiency',session.respond('proposal',Offer('p',(10,),0),provider)['evidence'])

    def test_inconsistent_wire_metadata_rejects_before_provider(self):
        performance=self.evidence().to_context()
        performance['missing_counters']=[]
        with self.assertRaises(ValueError):self.session(performance)
