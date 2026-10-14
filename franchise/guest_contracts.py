"""Exact contract-format boundary for new deals; no guest writes or authority.

The game stores an amount word, bonus percentage, schedule shape and term,
not arbitrary annual salaries. Preserve its annual rounding, but reject a bonus
schedule that disagrees with modern allocation. Existing deals remain legacy.
Cap/minimum/rookie validation, identity binding and commit recovery are separate.
"""
from dataclasses import dataclass

from franchise.cap import Offer
from franchise.legacy_contracts import original_annual_rows


@dataclass(frozen=True)
class GuestContractTerms:
    amount_word: int
    bonus_code: int
    shape_code: int
    years: int

    def __post_init__(self):
        original_annual_rows(self.amount_word, self.bonus_code, self.shape_code, self.years)

    @classmethod
    def from_context(cls, amount_word: int, flags_word: int):
        if type(flags_word) is not int or not 0 <= flags_word <= 0xFFFFFFFF:
            raise ValueError('Unsigned guest context flags required')
        # 323D80 copies context+8 low nibble to player+24 bits20..23,
        # bits29..31 to bits16..18, and context+0A low nibble to both terms.
        return cls(amount_word, flags_word & 15, (flags_word >> 29) & 7,
                   (flags_word >> 16) & 15)

    def to_offer(self, player_id: str) -> Offer:
        if self.bonus_code and self.years > 5:
            raise ValueError('Guest bonus term exceeds modern five-year allocation')
        rows = original_annual_rows(self.amount_word, self.bonus_code, self.shape_code, self.years)
        # Retain the nominal signing bonus, not a smaller invented bonus that
        # happens to fit the game's truncating annual allocation.
        offer = Offer(player_id, tuple(row['salary_dollars'] for row in rows),
                      self.amount_word * self.bonus_code * 1000)
        if offer.charges(5) != tuple(row['original_game_charge_dollars'] for row in rows):
            raise ValueError('Guest bonus rounding differs from modern allocation')
        return offer


def guest_terms_for_offer(offer: Offer) -> GuestContractTerms:
    """Find an exact raw schedule, refusing rounding or lost base guarantees.

    Positive bonus fixes at most ten candidate amount words. With zero bonus,
    each shape's salaries are monotone in the amount word, so binary search
    avoids scanning the entire 16-bit domain. Compare every annual salary,
    nominal bonus and modern charge before returning a candidate.
    """
    if not isinstance(offer, Offer):
        raise ValueError('Typed modern offer required')
    years = len(offer.salaries)
    if years > 15 or (offer.signing_bonus and years > 5):
        raise ValueError('Modern offer term cannot use the guest contract format')
    if any(offer.guaranteed_salaries):
        raise ValueError('Guest contract format cannot preserve guaranteed base')
    if offer.signing_bonus % 1000 or any(salary % 1000 for salary in offer.salaries):
        raise ValueError('Guest annual salaries and bonuses require whole thousands')
    shapes = (2, 1, 6, 0, 7, 3, 4, 5)
    candidates = []
    if offer.signing_bonus:
        bonus_units = offer.signing_bonus // 1000
        for bonus_code in range(1, 11):
            if bonus_units % bonus_code == 0:
                amount = bonus_units // bonus_code
                if 1 <= amount <= 65535:
                    candidates.extend((amount, bonus_code, shape) for shape in shapes)
    else:
        target = sum(offer.salaries)
        for shape in shapes:
            low, high = 1, 65535
            while low < high:
                middle = (low + high) // 2
                total = sum(row['salary_dollars'] for row in
                            original_annual_rows(middle, 0, shape, years))
                if total < target:
                    low = middle + 1
                else:
                    high = middle
            candidates.append((low, 0, shape))
    for amount, bonus_code, shape in candidates:
        terms = GuestContractTerms(amount, bonus_code, shape, years)
        try:
            decoded = terms.to_offer(offer.player_id)
        except ValueError:
            continue
        if decoded.salaries == offer.salaries and decoded.signing_bonus == offer.signing_bonus:
            return terms
    raise ValueError('Modern offer has no exact guest contract schedule')
