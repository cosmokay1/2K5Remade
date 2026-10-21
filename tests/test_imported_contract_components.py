from fractions import Fraction
import unittest

from franchise.books import OpeningBooks,ChargeRecord
from franchise.cap import Ledger,Offer
from franchise.legacy_contracts import LegacyContract
from franchise.legacy_amendments import InSeasonAmendmentScope
from franchise.saved_checkpoint import charges


class ImportedContractComponentsTests(unittest.TestCase):
    def ledger(self,nonbase=-20000):
        original=LegacyContract('player',348,5,6,3,3,'authored native approximation',4)
        books=OpeningBooks(legacy_contracts=(original,),adjustments=(
            ChargeRecord('native-base:player',(100000,)*3,'authored exact source base'),
            ChargeRecord('native-nonbase:player',(nonbase,)*3,'authored exact source nonbase'),
            ChargeRecord('club-adjustment',(500000,),'authored independent club charge')))
        return Ledger.from_opening(books,cap=301200000,roster_reserve=0,max_bonus_years=5,
            veteran_minimums={'player':(1000000,)*5}),original

    def test_source_salary_is_earned_and_source_nonbase_is_carried(self):
        ledger,original=self.ledger();scope=InSeasonAmendmentScope(2026,4,17,'authored clock')
        offer=Offer('player',(2000000,),0)
        preview=ledger.preview_legacy_amendment(offer,0,scope=scope)
        self.assertEqual(preview['current_charges'][0],3944000)
        self.assertEqual(preview['carried_bonus_charges'],[2300000]*3)
        self.assertEqual(Fraction(preview['earned_pay']['earned_base_obligation']),Fraction(1644000*4,17))
        ledger.apply_legacy_amendment('one',offer,0,proposal_request_id='proposal',source='authored consent',scope=scope)
        self.assertEqual(list(ledger.charges),charges(ledger,[original],include_opening_adjustments=True))
        ledger.apply_legacy_amendment('two',Offer('player',(1500000,),0),1,
            proposal_request_id='second',source='authored second consent',scope=scope)
        self.assertEqual(list(ledger.charges),charges(ledger,[original],include_opening_adjustments=True))
        self.assertEqual(ledger._legacy_amendments['player'].carried_bonus_charges,(2300000,)*3)

    def test_old_contract_credit_cannot_subsidize_the_replacement(self):
        ledger,_=self.ledger(nonbase=-3000000)
        preview=ledger.preview_legacy_amendment(Offer('player',(1000000,),0),0)
        self.assertEqual(preview['carried_bonus_charges'],[0,0,0])
        self.assertEqual(preview['combined_player_charges'],[1000000,0,0])

    def test_negative_imported_salary_is_rejected_at_bootstrap(self):
        original=LegacyContract('player',348,5,6,3,3,'authored native approximation',4)
        books=OpeningBooks(legacy_contracts=(original,),adjustments=(
            ChargeRecord('native-base:player',(-2000000,)*3,'authored invalid salary'),))
        with self.assertRaises(ValueError):Ledger.from_opening(books,cap=301200000,
            roster_reserve=0,max_bonus_years=5,veteran_minimums={'player':(1000000,)*5})
