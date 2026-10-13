"""Explicit nominal compensation and payments; independent of cap proration."""
from dataclasses import asdict, dataclass
from franchise.cap import money, Rejected


@dataclass(frozen=True)
class CashObligation:
    obligation_id: str
    player_id: str
    amount: int
    paid: int
    source: str
    paid_components: tuple[tuple[str, int], ...] | None = None

    def __post_init__(self):
        for value in (self.obligation_id, self.player_id, self.source):
            if type(value) is not str or not value.strip():
                raise ValueError("Cash records require stable identity and provenance")
        if money(self.paid) > money(self.amount):
            raise ValueError("Paid cash exceeds nominal obligation")
        if self.paid_components is not None:
            if type(self.paid_components) is not tuple:
                raise ValueError("Immutable payment allocations required")
            seen, total = set(), 0
            for record in self.paid_components:
                if type(record) is not tuple or len(record) != 2:
                    raise ValueError("Component and paid amount required")
                key, amount = record
                if type(key) is not str or not key.strip() or key in seen:
                    raise ValueError("Unique payment components required")
                seen.add(key)
                total += money(amount)
            if total != self.paid:
                raise ValueError("Payment allocations disagree with total paid")

    def to_dict(self):
        record = asdict(self)
        if self.paid_components is None:
            del record["paid_components"]
        else:
            record["paid_components"] = [list(item) for item in self.paid_components]
        return record

    @classmethod
    def from_dict(cls, record):
        record = dict(record)
        if record.get("paid_components") is not None:
            record["paid_components"] = tuple(tuple(item) for item in record["paid_components"])
        return cls(**record)


class CashBook:
    def __init__(self, records: tuple[CashObligation, ...], source: str):
        if type(records) is not tuple or any(not isinstance(item, CashObligation) for item in records):
            raise ValueError("Typed opening cash records required")
        if type(source) is not str or not source.strip():
            raise ValueError("Cash coverage source required")
        self.source = source
        self.records = {record.obligation_id: record for record in records}
        if len(self.records) != len(records):
            raise ValueError("Duplicate cash obligations")
        self.revision = 0

    def add_contract(self, offer, source, *, track_components=True):
        key = "contract:" + offer.player_id
        if key in self.records:
            raise Rejected("Contract cash already registered")
        self.records[key] = CashObligation(key, offer.player_id, sum(offer.salaries) + offer.signing_bonus, 0, source, () if track_components else None)
        self.revision += 1

    def pay(self, obligation_id, amount, expected_revision, *, component=None):
        amount = money(amount)
        if type(expected_revision) is not int or expected_revision != self.revision:
            raise Rejected("Payment is based on stale cash state")
        if amount == 0 or obligation_id not in self.records:
            raise Rejected("Positive payment against known obligation required")
        record = self.records[obligation_id]
        if record.paid + amount > record.amount:
            raise Rejected("Payment exceeds outstanding cash obligation")
        allocations = None
        if record.paid_components is not None:
            if type(component) is not str or not component.strip():
                raise Rejected("Payment component required for allocated cash history")
            values = dict(record.paid_components)
            values[component] = values.get(component, 0) + amount
            allocations = tuple(sorted(values.items()))
        elif component is not None:
            raise Rejected("Historical payment allocation is unavailable; explicit reconciliation required")
        self.records[obligation_id] = CashObligation(record.obligation_id, record.player_id,
            record.amount, record.paid + amount, record.source, allocations)
        self.revision += 1

    def snapshot(self):
        records = [self.records[key].to_dict() for key in sorted(self.records)]
        return {"revision": self.revision, "source": self.source, "obligations": records,
                "nominal_total": sum(record.amount for record in self.records.values()),
                "paid_total": sum(record.paid for record in self.records.values()),
                "unpaid_total": sum(record.amount - record.paid for record in self.records.values())}
