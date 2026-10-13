"""Read-only binary comparison for controlled NFL 2K5 save experiments.

Offsets are candidates for investigation, never inferred contract fields.
Accepts raw SAVEGAME.DAT files, not ZIPs or signed container metadata.
"""
import argparse
import hashlib
import json
from pathlib import Path


def compare(before: bytes, after: bytes) -> dict:
    if not before or not after:
        raise ValueError("Both inputs must contain data")
    if before.startswith(b"PK\x03\x04") or after.startswith(b"PK\x03\x04"):
        raise ValueError("Extract SAVEGAME.DAT first; ZIP containers are unsupported")
    if len(before) != len(after):
        raise ValueError("Save lengths differ; use matching raw save formats")
    spans = []
    start = None
    for offset, (old, new) in enumerate(zip(before, after)):
        if old != new and start is None:
            start = offset
        if old == new and start is not None:
            spans.append((start, offset))
            start = None
    if start is not None:
        spans.append((start, len(before)))
    return {
        "before_sha256": hashlib.sha256(before).hexdigest(),
        "after_sha256": hashlib.sha256(after).hexdigest(),
        "size_bytes": len(before),
        "changed_bytes": sum(end - start for start, end in spans),
        "spans": [
            {
                "offset": start,
                "offset_hex": hex(start),
                "length": end - start,
                "before_hex": before[start:end].hex(),
                "after_hex": after[start:end].hex(),
            }
            for start, end in spans
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args()
    try:
        report = compare(args.before.read_bytes(), args.after.read_bytes())
    except (OSError, ValueError) as exc:
        parser.exit(2, f"save_diff: {exc}\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
