"""Explicit opening obligations; no guessed game fields or hidden player ratings.

Existing contract charges derive from original terms and elapsed years. Retained
charges and adjustments are explicit imported records until their lifecycle
operations exist. These records do not establish that import values are truthful.
"""
from dataclasses import asdict, dataclass
from fractions import Fraction
from franchise.cap import Offer, json_amount, money


@dataclass(frozen=True)
class ActiveContract:
    offer: Offer
    source: str
    elapsed_years: int = 0
    bonus_years: int = 5

    def __post_init__(self):
        if type(self.source) is not str or not self.source.strip():
            raise ValueError("Contract requires source/provenance")
        if type(self.elapsed_years) is not int or not 0 <= self.elapsed_years < len(self.offer.salaries):
            raise ValueError("Active contract must have remaining years")
        self.offer.charges(self.bonus_years)

    def charges(self):
        return self.offer.charges(self.bonus_years)[self.elapsed_years:]


@dataclass(frozen=True)
class ChargeRecord:
    record_id: str
    annual_charges: tuple[int | Fraction, ...]
    source: str

    def __post_init__(self):
        if type(self.record_id) is not str or not self.record_id.strip():
            raise ValueError("Charge record requires a stable ID")
        if type(self.source) is not str or not self.source.strip():
            raise ValueError("Charge record requires source/provenance")
        if type(self.annual_charges) is not tuple or not self.annual_charges:
            raise ValueError("Charge record requires annual amounts")
        for value in self.annual_charges:
            if type(value) is not int and not isinstance(value, Fraction):
                raise ValueError("Charge record amounts must be exact")


@dataclass(frozen=True)
class RookieTender:
    player_id: str
    amount: int

    def __post_init__(self):
        if type(self.player_id) is not str or not self.player_id.strip() or money(self.amount) == 0:
            raise ValueError("Rookie tender requires player ID and positive amount")


def parse_amount(value):
    if type(value) is int:
        return Fraction(value)
    if type(value) is str and "/" in value:
        try:
            amount = Fraction(value)
        except (ValueError, ZeroDivisionError):
            raise ValueError("Invalid exact amount") from None
        if str(amount) == value:
            return amount
    raise ValueError("Amount must be an integer or canonical rational string")


@dataclass(frozen=True)
class OpeningBooks:
    contracts: tuple[ActiveContract, ...] = ()
    retained: tuple[ChargeRecord, ...] = ()
    adjustments: tuple[ChargeRecord, ...] = ()
    tenders: tuple[RookieTender, ...] = ()

    def __post_init__(self):
        for records, expected in ((self.contracts, ActiveContract), (self.retained, ChargeRecord),
                                  (self.adjustments, ChargeRecord), (self.tenders, RookieTender)):
            if type(records) is not tuple or any(not isinstance(item, expected) for item in records):
                raise ValueError("Opening records must be immutable typed tuples")
        players = [item.offer.player_id for item in self.contracts]
        tenders = [item.player_id for item in self.tenders]
        ids = [item.record_id for item in (*self.retained, *self.adjustments)]
        if len(players) != len(set(players)) or len(tenders) != len(set(tenders)) or len(ids) != len(set(ids)):
            raise ValueError("Duplicate opening obligation")
        if set(players) & set(tenders):
            raise ValueError("Player cannot have an active contract and unsigned tender")
        if any(value < 0 for item in self.retained for value in item.annual_charges):
            raise ValueError("Retained obligations cannot be negative")
        if any(value < 0 for value in self.charges()):
            raise ValueError("Opening credits exceed modeled obligations")

    def charges(self) -> tuple[Fraction, ...]:
        rows = [item.charges() for item in self.contracts]
        rows.extend(item.annual_charges for item in (*self.retained, *self.adjustments))
        rows.extend((item.amount,) for item in self.tenders)
        years = max((len(row) for row in rows), default=1)
        return tuple(sum((Fraction(row[i]) for row in rows if i < len(row)), Fraction(0))
                     for i in range(years))

    def to_dict(self):
        return {"contracts": [{**asdict(item), "offer": item.offer.to_dict()} for item in self.contracts],
                "retained": [{**asdict(item), "annual_charges": [json_amount(value) for value in item.annual_charges]} for item in self.retained],
                "adjustments": [{**asdict(item), "annual_charges": [json_amount(value) for value in item.annual_charges]} for item in self.adjustments],
                "tenders": [asdict(item) for item in self.tenders]}

    @classmethod
    def from_dict(cls, data):
        if type(data) is not dict or set(data) != {"contracts", "retained", "adjustments", "tenders"}:
            raise ValueError("Unexpected opening book fields")
        contracts = []
        for item in data["contracts"]:
            offer = item["offer"]
            contracts.append(ActiveContract(Offer.from_dict(offer),
                                            item["source"], item["elapsed_years"], item["bonus_years"]))
        def records(key):
            return tuple(ChargeRecord(item["record_id"], tuple(parse_amount(value) for value in item["annual_charges"]), item["source"])
                         for item in data[key])
        return cls(tuple(contracts), records("retained"), records("adjustments"),
                   tuple(RookieTender(**item) for item in data["tenders"]))
