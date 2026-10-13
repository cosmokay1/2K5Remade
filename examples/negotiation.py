"""Synthetic accepted offers illustrating mandatory cap enforcement.

Run from the workspace root: python3 -m examples.negotiation
The proposed terms stand in for negotiation output; no LLM is connected.
"""
from franchise.cap import Ledger, Offer, Rejected


def main():
    ledger = Ledger(cap=100_000_000, existing_charges=(90_000_000, 80_000_000),
                    roster_reserve=2_000_000, max_bonus_years=3)
    print(f"Available room after roster reserve: ${ledger.room:,}")
    for request_id, offer in [
        ("initial", Offer("receiver-01", (7_000_000,) * 3, 6_000_000)),
        ("counter", Offer("receiver-01", (6_000_000,) * 3, 6_000_000)),
    ]:
        try:
            receipt = ledger.sign(request_id, offer, ledger.revision)
            print(f"{request_id}: signed; annual cap charges {receipt.charges}")
        except Rejected as exc:
            print(f"{request_id}: rejected; {exc}")
    print(f"Remaining current cap room: ${ledger.room:,}")


if __name__ == "__main__":
    main()
