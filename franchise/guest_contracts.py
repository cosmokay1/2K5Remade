"""Exact contract-format boundary for new deals; no guest writes or authority.

The game stores an amount word, bonus percentage, schedule shape and term,
not arbitrary annual salaries. Preserve its annual rounding, but reject a bonus
schedule that disagrees with modern allocation. Existing deals remain legacy.
Cap/minimum/rookie validation, identity binding and commit recovery are separate.
"""
from dataclasses import dataclass

from franchise.cap import Offer, Rejected
from franchise.legacy_contracts import original_annual_rows

GUEST_CONTRACT_FORMAT = 'original_fxg_v1'
SOFTDRINK_CONTRACT_FORMAT = 'softdrink_fxg_v1'


def guest_money_scale(contract_format):
    if contract_format == GUEST_CONTRACT_FORMAT:
        return 1
    if contract_format == SOFTDRINK_CONTRACT_FORMAT:
        return 4
    raise ValueError('Supported guest proposal contract format required')


def guest_offer_encoding(offer: Offer, *, contract_format=GUEST_CONTRACT_FORMAT):
    """Return only the mapped offer bits; applying guest memory is separate."""
    terms = guest_terms_for_offer(offer, contract_format=contract_format)
    return {'amount_word': terms.amount_word,
            'flags_word': (terms.shape_code << 29) | (terms.years << 16) | terms.bonus_code}


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

    def to_offer(self, player_id: str, *, contract_format=GUEST_CONTRACT_FORMAT) -> Offer:
        scale = guest_money_scale(contract_format)
        if self.bonus_code and self.years > 5:
            raise ValueError('Guest bonus term exceeds modern five-year allocation')
        rows = original_annual_rows(self.amount_word, self.bonus_code, self.shape_code, self.years)
        # Retain the nominal signing bonus, not a smaller invented bonus that
        # happens to fit the game's truncating annual allocation.
        offer = Offer(player_id, tuple(row['salary_dollars'] * scale for row in rows),
                      self.amount_word * self.bonus_code * 1000 * scale)
        if offer.charges(5) != tuple(row['original_game_charge_dollars'] * scale for row in rows):
            raise ValueError('Guest bonus rounding differs from modern allocation')
        return offer


def guest_terms_for_offer(offer: Offer, *, contract_format=GUEST_CONTRACT_FORMAT) -> GuestContractTerms:
    """Find an exact raw schedule, refusing rounding or lost base guarantees.

    Positive bonus fixes at most ten candidate amount words. With zero bonus,
    each shape's salaries are monotone in the amount word, so binary search
    avoids scanning the entire 16-bit domain. Compare every annual salary,
    nominal bonus and modern charge before returning a candidate.
    """
    scale = guest_money_scale(contract_format)
    unit = 1000 * scale
    if not isinstance(offer, Offer):
        raise ValueError('Typed modern offer required')
    years = len(offer.salaries)
    if years > 15 or (offer.signing_bonus and years > 5):
        raise ValueError('Modern offer term cannot use the guest contract format')
    if any(offer.guaranteed_salaries):
        raise ValueError('Guest contract format cannot preserve guaranteed base')
    if offer.signing_bonus % unit or any(salary % unit for salary in offer.salaries):
        raise ValueError('Guest annual salaries and bonuses require exact scaled whole thousands')
    shapes = (2, 1, 6, 0, 7, 3, 4, 5)
    candidates = []
    if offer.signing_bonus:
        bonus_units = offer.signing_bonus // unit
        for bonus_code in range(1, 11):
            if bonus_units % bonus_code == 0:
                amount = bonus_units // bonus_code
                if 1 <= amount <= 65535:
                    candidates.extend((amount, bonus_code, shape) for shape in shapes)
    else:
        target = sum(offer.salaries) // scale
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
            decoded = terms.to_offer(offer.player_id, contract_format=contract_format)
        except ValueError:
            continue
        if decoded.salaries == offer.salaries and decoded.signing_bonus == offer.signing_bonus:
            return terms
    raise ValueError('Modern offer has no exact guest contract schedule')


def preview_guest_offer(store, team_id, player_id, *, amount_word, flags_word, expected_revision,
                        contract_format=GUEST_CONTRACT_FORMAT):
    """Inspect exact new free-agent terms, never sign or reserve cap room.

    Format rejection is separate from authoritative ownership/minimum/cap
    rejection. Existing contracts retain their legacy schedules elsewhere.
    """
    guest_money_scale(contract_format)
    if type(amount_word) is not int or not 0 <= amount_word <= 65535:
        raise ValueError('Unsigned guest offer amount word required')
    if type(flags_word) is not int or not 0 <= flags_word <= 0xFFFFFFFF:
        raise ValueError('Unsigned guest offer flags required')
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError('Explicit nonnegative financial revision required')
    result = {'amount_word': amount_word, 'flags_word': flags_word,
              'outcome': None, 'offer': None, 'preview': None, 'reason': None,
              **({'contract_format': contract_format} if contract_format != GUEST_CONTRACT_FORMAT else {})}
    try:
        offer = GuestContractTerms.from_context(amount_word, flags_word).to_offer(player_id, contract_format=contract_format)
    except ValueError as error:
        return {**result, 'outcome': 'format_rejected', 'reason': str(error)}
    result['offer'] = offer.to_dict()
    try:
        preview = store.preview_offer(team_id, offer, expected_revision)
    except Rejected as error:
        return {**result, 'outcome': 'accounting_rejected', 'reason': str(error)}
    return {**result, 'outcome': 'eligible_preview', 'preview': preview}
