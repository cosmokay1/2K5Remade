from copy import deepcopy
import unittest

from tools.rookie_contract_sources import (reconcile_rookie_page, apply_rookie_schedules,
                                         reconcile_rookie_sources)


class RookieSourceTests(unittest.TestCase):
    def inputs(self, practice=False):
        kind, years, total = ('Practice',1,0.001) if practice else ('Drafted',4,0.0044)
        archived = dict(player='Authored Player',otc_id=123,gsis_id='authored',
            draft_year=2026,draft_round=3,draft_overall=75,year_signed=2026,
            years=years,is_active=True,value=total,season_history=[{'year':None,'cap_number':None}],
            contract_history=[dict(team='Giants',contract_type=kind,status='Active',
                                   year_signed=2026,yrs=years,total=total)])
        annual = '\n'.join(f'L{i}: {year}  | $1,000 | '+('' if practice else '$100')+
            ' | $900 | $'+('1,000' if practice else '1,100')
            for i,year in enumerate(range(2026,2026+years),10))
        text = f'''Authored (https://overthecap.com/player/authored-player/123/)
L1: ### Authored Player
L2: Entry: 2026 Draft, Round 3, #75 overall (Giants)
L0: 2026 Salary Cap Charge: ${'1,000' if practice else '1,100'}
L3: #### Current Contract
L4: ##### ({kind}, signed 2026)
L5: Year  | Base Salary | Prorated Signing Bonus | Guaranteed Salary | Cap
L6: Number | Cap %
{annual}
L20: #### Contract History
L21: Team | Contract Type | Status | Year Signed | Yrs | Total
L22: Giants | {kind} | Active | 2026 | {years} | ${int(total*1_000_000):,}
'''
        return text, archived

    def parse(self,text,archived):
        return reconcile_rookie_page(text,archived,season_year=2026)

    def test_matching_schedule_fills_source_gaps_without_inventing_paid_cash(self):
        text,archived=self.inputs();before=deepcopy(archived)
        report=self.parse(text,archived);updated=apply_rookie_schedules([archived],[report])
        self.assertEqual(archived,before)
        self.assertEqual(report['annual'][0]['allocated_bonus_dollars'],100)
        self.assertEqual(report['annual'][0]['guaranteed_salary_dollars'],900)
        self.assertEqual(updated[0]['season_history'][1]['cap_number'],'0.0011')
        self.assertIsNone(updated[0]['season_history'][1]['cash_paid'])
        self.assertFalse(report['paid_cash_verified']);self.assertFalse(report['signing_authorized'])

    def test_source_reference_cannot_swallow_the_identity_heading(self):
        text,archived=self.inputs()
        text=text.replace('L1:', 'citesourceview0\nL1:').replace(
            'L2: Entry:', 'L0: cite1†Position\nL2: Entry:')
        self.assertEqual(self.parse(text,archived)['gsis_id'],'authored')

    def test_replacement_practice_contract_is_not_restored_to_four_years(self):
        text,archived=self.inputs(practice=True);report=self.parse(text,archived)
        self.assertEqual(report['contract_type'],'Practice')
        self.assertEqual(len(report['annual']),1)
        self.assertIsNone(report['annual'][0]['allocated_bonus_dollars'])
        archived['years']=4
        with self.assertRaises(ValueError):self.parse(text,archived)

    def test_undrafted_three_year_and_replacement_sfa_keep_their_lineage(self):
        text,archived=self.inputs()
        text=text.replace('2026 Draft, Round 3, #75 overall', '2026 Undrafted Free Agent')
        line=next(l for l in text.splitlines() if '2029  |' in l)
        text=text.replace(line+'\n','').replace('Drafted','UDFA').replace(
            '| 4 | $4,400','| 3 | $3,300')
        archived.update(draft_round=None,draft_overall=None,years=3,value=0.0033)
        archived['contract_history'][0].update(contract_type='UDFA',yrs=3,total=0.0033)
        report=self.parse(text,archived)
        self.assertEqual(report['contract_type'],'UDFA')
        self.assertEqual(len(report['annual']),3)
        self.assertFalse(report['historical_annual_schedule_verified'])
        text,archived=self.inputs(practice=True)
        text=text.replace('Practice','SFA')
        archived['contract_history'][0]['contract_type']='SFA'
        self.assertEqual(self.parse(text,archived)['contract_type'],'SFA')

    def test_published_cap_match_does_not_turn_conflicting_components_into_cash(self):
        text,archived=self.inputs();text=text.replace('$1,000','$950')
        report=self.parse(text,archived)
        self.assertFalse(report['published_components_reconcile'])
        result=apply_rookie_schedules([archived],[report])
        annual=result[0]['season_history'][1]
        self.assertIsNone(annual['cash_paid'])
        self.assertNotIn('base_salary',annual)
        self.assertFalse(annual['historical_annual_schedule_verified'])

    def test_first_year_summary_and_changed_archive_are_rejected(self):
        text,archived=self.inputs()
        with self.assertRaises(ValueError):
            self.parse(text.replace('Cap Charge: $1,100','Cap Charge: $1,200'),archived)
        report=self.parse(text,archived)
        archived['contract_history'][0]['team']='Jets'
        with self.assertRaises(ValueError):apply_rookie_schedules([archived],[report])

    def test_wrong_year_slot_identity_term_owner_and_total_are_rejected(self):
        for old,new in [('signed 2026','signed 2027'),('#75','#76'),
                        ('player/123/','player/124/'),('Giants | Drafted','Jets | Drafted'),
                        ('$4,400','$4,500'),('### Authored Player','### Someone Else')]:
            text,archived=self.inputs()
            with self.subTest(change=old),self.assertRaises(ValueError):
                self.parse(text.replace(old,new),archived)

    def test_incomplete_duplicate_and_unexplained_cap_rows_are_rejected(self):
        for change in ('missing','duplicate','cap'):
            text,archived=self.inputs()
            line=next(x for x in text.splitlines() if '2028  |' in x)
            text=text.replace(line,'' if change=='missing' else line+'\n'+line if change=='duplicate'
                              else line.replace('$1,100','$1,101'))
            with self.subTest(change=change),self.assertRaises(ValueError):self.parse(text,archived)

    def test_conflicting_archive_is_not_overwritten_and_matching_evidence_is_preserved(self):
        text,archived=self.inputs();report=self.parse(text,archived)
        archived['season_history']=[dict(year='2026',team='Giants',cap_number='0.0012')]
        with self.assertRaises(ValueError):apply_rookie_schedules([archived],[report])
        archived['season_history'][0].update(cap_number='0.0011',cash_paid='0.0005')
        result=apply_rookie_schedules([archived],[report])
        self.assertEqual(result[0]['season_history'][0]['cash_paid'],'0.0005')
        with self.assertRaises(ValueError):apply_rookie_schedules([archived],[report,report])

    def test_batch_keeps_missing_identity_and_conflicting_source_gaps(self):
        text,archived=self.inputs()
        missing=deepcopy(archived);missing.update(otc_id=124,player='Missing Player')
        report=reconcile_rookie_sources([archived,missing],[text],season_year=2026)
        self.assertEqual(report['requested'],2)
        self.assertEqual(report['matched_published_schedules'],1)
        self.assertEqual(report['unresolved'][0]['reasons'],['Source page unavailable'])
        changed=text.replace('2027  | $1,000 | $100 | $900 | $1,100',
                             '2027  | $1,000 | $100 | $900 | $1,200').replace(
                             '2028  | $1,000 | $100 | $900 | $1,100',
                             '2028  | $1,000 | $100 | $900 | $1,000')
        report=reconcile_rookie_sources([archived],[text,changed],season_year=2026)
        self.assertEqual(report['matched_published_schedules'],0)
        self.assertIn('Conflicting published schedules',report['unresolved'][0]['reasons'])
        report=reconcile_rookie_sources([archived,archived],[text],season_year=2026)
        self.assertEqual(report['matched_published_schedules'],0)
        self.assertIn('Duplicate archived OTC identity',report['unresolved'][0]['reasons'])
