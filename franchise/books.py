"""Explicit opening obligations; no guessed game fields or hidden player ratings.

Existing contract charges derive from original terms and elapsed years. Retained
charges and adjustments are explicit imported records until their lifecycle
operations exist. These records do not establish that import values are truthful.
"""
from dataclasses import asdict, dataclass
from fractions import Fraction
from franchise.cap import Offer, json_amount, money


@dataclass(frozen=True)
class BonusLayer:
    record_id: str
    amount: int
    original_start_index: int
    allocation_years: int
    source: str

    @property
    def cash_component(self):
        return 'bonus:' + self.record_id

    def __post_init__(self):
        if any(type(value) is not str or not value.strip() for value in (self.record_id, self.source)):
            raise ValueError('Bonus layer requires identity and provenance')
        if money(self.amount) == 0:
            raise ValueError('Additional bonus layer must be positive')
        if type(self.original_start_index) is not int or self.original_start_index < 0:
            raise ValueError('Original-year bonus start index required')
        if type(self.allocation_years) is not int or not 1 <= self.allocation_years <= 5:
            raise ValueError('Bonus layer allocation must be one through five years')

    @classmethod
    def from_dict(cls, record):
        if type(record) is not dict or set(record) != {'record_id','amount','original_start_index','allocation_years','source'}:
            raise ValueError('Unexpected bonus layer fields')
        return cls(**record)


@dataclass(frozen=True)
class ActiveContract:
    offer: Offer
    source: str
    elapsed_years: int = 0
    bonus_years: int = 5
    bonus_layers: tuple[BonusLayer, ...] = ()

    def __post_init__(self):
        if type(self.source) is not str or not self.source.strip():
            raise ValueError("Contract requires source/provenance")
        if type(self.elapsed_years) is not int or not 0 <= self.elapsed_years < len(self.offer.salaries):
            raise ValueError("Active contract must have remaining years")
        self.offer.charges(self.bonus_years)
        if type(self.bonus_layers) is not tuple or any(not isinstance(layer, BonusLayer) for layer in self.bonus_layers):
            raise ValueError('Immutable typed bonus layers required')
        if len({layer.record_id for layer in self.bonus_layers}) != len(self.bonus_layers):
            raise ValueError('Duplicate bonus layer identity')
        if any(layer.original_start_index + layer.allocation_years > len(self.offer.salaries) for layer in self.bonus_layers):
            raise ValueError('Bonus allocation cannot exceed original contract term')

    def compensation_components(self):
        """Nominal payable components; their allocation never implies payment."""
        return {'signing_bonus': self.offer.signing_bonus,
                **{'base:' + str(i): amount for i, amount in enumerate(self.offer.salaries)},
                **{layer.cash_component: layer.amount for layer in self.bonus_layers}}

    @property
    def nominal_cash(self):
        return sum(self.compensation_components().values())

    def charges(self):
        original = self.offer.charges(self.bonus_years)
        return tuple(value + sum((Fraction(layer.amount, layer.allocation_years) for layer in self.bonus_layers
            if layer.original_start_index <= i < layer.original_start_index + layer.allocation_years), Fraction(0))
            for i, value in enumerate(original) if i >= self.elapsed_years)

    def to_dict(self):
        return {'offer': self.offer.to_dict(), 'source': self.source, 'elapsed_years': self.elapsed_years,
                'bonus_years': self.bonus_years,
                **({'bonus_layers': [asdict(layer) for layer in self.bonus_layers]} if self.bonus_layers else {})}

    @classmethod
    def from_dict(cls, record):
        keys = {'offer', 'source', 'elapsed_years', 'bonus_years'}
        if type(record) is not dict or set(record) not in (keys, keys | {'bonus_layers'}):
            raise ValueError('Unexpected active contract fields')
        layers = record.get('bonus_layers', [])
        if type(layers) is not list or any(type(layer) is not dict for layer in layers):
            raise ValueError('Serialized bonus layer objects required')
        return cls(Offer.from_dict(record['offer']), record['source'], record['elapsed_years'], record['bonus_years'],
                   tuple(BonusLayer.from_dict(layer) for layer in layers))


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
        return {"contracts": [item.to_dict() for item in self.contracts],
                "retained": [{**asdict(item), "annual_charges": [json_amount(value) for value in item.annual_charges]} for item in self.retained],
                "adjustments": [{**asdict(item), "annual_charges": [json_amount(value) for value in item.annual_charges]} for item in self.adjustments],
                "tenders": [asdict(item) for item in self.tenders]}

    @classmethod
    def from_dict(cls, data):
        if type(data) is not dict or set(data) != {"contracts", "retained", "adjustments", "tenders"}:
            raise ValueError("Unexpected opening book fields")
        contracts = []
        for item in data["contracts"]:
            contracts.append(ActiveContract.from_dict(item))
        def records(key):
            return tuple(ChargeRecord(item["record_id"], tuple(parse_amount(value) for value in item["annual_charges"]), item["source"])
                         for item in data[key])
        return cls(tuple(contracts), records("retained"), records("adjustments"),
                   tuple(RookieTender(**item) for item in data["tenders"]))
