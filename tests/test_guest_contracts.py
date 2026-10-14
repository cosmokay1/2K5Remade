"""Guest format compatibility must not loosen the modern financial validator."""
import unittest

from franchise.cap import Ledger, Offer, Rejected
from franchise.guest_contracts import GuestContractTerms, guest_terms_for_offer


class GuestContractsTests(unittest.TestCase):
    def test_calibrated_descending_terms_retain_each_charge_and_rounding(self):
        terms = GuestContractTerms(829, 4, 1, 2)
        offer = terms.to_offer('player')
        self.assertEqual(offer.salaries, (3108000, 1865000))
        self.assertEqual(offer.signing_bonus, 3316000)
        self.assertEqual(offer.charges(5), (4766000, 3523000))
        self.assertEqual(sum(offer.salaries) + offer.signing_bonus, 8289000)
        self.assertEqual(guest_terms_for_offer(offer).to_offer('player'), offer)

    def test_bonus_rounding_and_long_horizon_cannot_be_modernized_silently(self):
        with self.assertRaisesRegex(ValueError, 'rounding'):
            GuestContractTerms(500, 4, 2, 3).to_offer('p')
        with self.assertRaisesRegex(ValueError, 'five-year'):
            GuestContractTerms(1949, 4, 2, 6).to_offer('p')
        with self.assertRaises(ValueError):
            guest_terms_for_offer(Offer('p', (1000000,)*6, 600000))

    def test_format_fit_does_not_authorize_over_cap_or_below_minimum(self):
        offer = GuestContractTerms(829, 4, 1, 2).to_offer('p')
        ledger = Ledger(cap=4765999, existing_charges=(0, 0), roster_reserve=0,
            max_bonus_years=5, veteran_minimums={'p': (300000, 300000)})
        before = ledger.financial_snapshot()
        with self.assertRaises(Rejected): ledger.sign('over', offer, 0)
        self.assertEqual(ledger.financial_snapshot(), before)
        cheap = GuestContractTerms(10, 0, 2, 1).to_offer('p')
        self.assertEqual(guest_terms_for_offer(cheap).to_offer('p'), cheap)
        with self.assertRaises(Rejected): ledger.sign('below', cheap, 0)
        self.assertEqual(ledger.financial_snapshot(), before)

    def test_unrepresentable_guarantees_units_and_salary_vectors_refuse(self):
        for offer in (Offer('p', (1000000,), 0, (1,)),
                      Offer('p', (1000001,), 0),
                      Offer('p', (1000000,), 1),
                      Offer('p', (1000000, 900000, 1300000), 0),
                      Offer('p', (1000000,)*16, 0)):
            with self.assertRaises(ValueError): guest_terms_for_offer(offer)

    def test_zero_bonus_round_trips_every_shape_and_supported_term(self):
        for years in range(1, 16):
            for shape in range(8):
                for amount in (1, 829, 65535):
                    with self.subTest(years=years, shape=shape, amount=amount):
                        offer = GuestContractTerms(amount, 0, shape, years).to_offer('p')
                        self.assertEqual(guest_terms_for_offer(offer).to_offer('p'), offer)

    def test_positive_bonus_round_trips_exact_allocations(self):
        for years in range(1, 6):
            for bonus_code in range(1, 11):
                for shape in range(8):
                    offer = GuestContractTerms(1000 * years, bonus_code, shape, years).to_offer('p')
                    self.assertEqual(guest_terms_for_offer(offer).to_offer('p'), offer)

    def test_context_extracts_only_contract_bits_and_checks_field_bounds(self):
        self.assertEqual(GuestContractTerms.from_context(1949, 0x4D060004),
                         GuestContractTerms(1949, 4, 2, 6))
        for flags in (True, -1, 0x100000000):
            with self.assertRaises(ValueError): GuestContractTerms.from_context(829, flags)
        for args in ((True, 4, 1, 2), (65536, 4, 1, 2), (829, 11, 1, 2),
                     (829, 4, 8, 2), (829, 4, 1, 0)):
            with self.assertRaises(ValueError): GuestContractTerms(*args)
