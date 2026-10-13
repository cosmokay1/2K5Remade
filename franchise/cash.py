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

    def __post_init__(self):
        for value in (self.obligation_id, self.player_id, self.source):
            if type(value) is not str or not value.strip():
                raise ValueError("Cash records require stable identity and provenance")
        if money(self.paid) > money(self.amount):
            raise ValueError("Paid cash exceeds nominal obligation")


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

    def add_contract(self, offer, source):
        key = "contract:" + offer.player_id
        if key in self.records:
            raise Rejected("Contract cash already registered")
        self.records[key] = CashObligation(key, offer.player_id, sum(offer.salaries) + offer.signing_bonus, 0, source)
        self.revision += 1

    def pay(self, obligation_id, amount, expected_revision):
        amount = money(amount)
        if type(expected_revision) is not int or expected_revision != self.revision:
            raise Rejected("Payment is based on stale cash state")
        if amount == 0 or obligation_id not in self.records:
            raise Rejected("Positive payment against known obligation required")
        record = self.records[obligation_id]
        if record.paid + amount > record.amount:
            raise Rejected("Payment exceeds outstanding cash obligation")
        self.records[obligation_id] = CashObligation(record.obligation_id, record.player_id,
            record.amount, record.paid + amount, record.source)
        self.revision += 1

    def snapshot(self):
        records = [asdict(self.records[key]) for key in sorted(self.records)]
        return {"revision": self.revision, "source": self.source, "obligations": records,
                "nominal_total": sum(record.amount for record in self.records.values()),
                "paid_total": sum(record.paid for record in self.records.values()),
                "unpaid_total": sum(record.amount - record.paid for record in self.records.values())}
