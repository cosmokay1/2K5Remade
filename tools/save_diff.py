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
    spans = _span_ranges(old != new for old, new in zip(before, after))
    return {
        "before_sha256": hashlib.sha256(before).hexdigest(),
        "after_sha256": hashlib.sha256(after).hexdigest(),
        "size_bytes": len(before),
        "changed_bytes": sum(end - start for start, end in spans),
        "spans": _describe_spans(spans, before, after),
    }


def _span_ranges(changes):
    spans = []
    start = None
    size = 0
    for offset, changed in enumerate(changes):
        size = offset + 1
        if changed and start is None:
            start = offset
        if not changed and start is not None:
            spans.append((start, offset))
            start = None
    if start is not None:
        spans.append((start, size))
    return spans


def _describe_spans(spans, before, after, control_after=None):
    return [
            {
                "offset": start,
                "offset_hex": hex(start),
                "length": end - start,
                "before_hex": before[start:end].hex(),
                "after_hex": after[start:end].hex(),
                **({'control_after_hex': control_after[start:end].hex()} if control_after is not None else {}),
            }
            for start, end in spans
        ]


def compare_controlled(before: bytes, after: bytes, control_after: bytes) -> dict:
    """Preserve all changes and partition transaction offsets by control overlap.

The control is a separate no-transaction save from the same baseline. Stable
control bytes do not prove a contract field; overlapping changes remain visible.
In control_spans, after_hex describes the control save, not the transaction save.
"""
    transaction = compare(before, after)
    control = compare(before, control_after)  # Same raw size/format validation.
    only = _span_ranges(old != new and old == other
        for old, new, other in zip(before, after, control_after))
    overlap = _span_ranges(old != new and old != other
        for old, new, other in zip(before, after, control_after))
    return {**transaction, 'control_after_sha256': control['after_sha256'],
        'control_changed_bytes': control['changed_bytes'], 'control_spans': control['spans'],
        'transaction_only_changed_bytes': sum(end-start for start,end in only),
        'transaction_only_spans': _describe_spans(only,before,after,control_after),
        'control_overlap_changed_bytes': sum(end-start for start,end in overlap),
        'control_overlap_spans': _describe_spans(overlap,before,after,control_after)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument('--control-after',type=Path,
                        help='Independent no-transaction raw save from the same baseline')
    args = parser.parse_args()
    try:
        before, after = args.before.read_bytes(), args.after.read_bytes()
        report = compare_controlled(before,after,args.control_after.read_bytes()) if args.control_after else compare(before,after)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"save_diff: {exc}\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
