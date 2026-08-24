"""
Aggregate the snapshot archive's disk footprint by classification cohort.

Answers the "how much is actually at stake?" half of the §6.4 retention decision:
the owner is being asked whether cohort B (truncated writes) may be deleted, and
that question is easier to answer with the byte counts beside the file counts.

Reads only the gitignored ``snapshots_classification.jsonl`` sidecar, which already
carries ``size_bytes`` per record — no filesystem walk, no HDF5 opens, no writes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-23
Status: ad-hoc -- one-off (investigation)
Retire when: the §6.4 retention policy is ratified and any retention tool reports
             its own footprint numbers.
Related: notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md
         section "6.4 Phase 4 -- Retention policy"
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

DEFAULT_SIDECAR = pathlib.Path(
    "/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots/snapshots_classification.jsonl"
)


def _human(num_bytes: int) -> str:
    """Render a byte count the way an operator reads a retention decision."""
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(value) < 1024.0 or unit == "TB":
            return f"{value:,.1f} {unit}"
        value /= 1024.0
    return f"{value:,.1f} TB"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--sidecar", type=pathlib.Path, default=DEFAULT_SIDECAR)
    parser.add_argument(
        "--axis",
        choices=("category", "health"),
        default="category",
        help="the classification frame to group on (both are valid; they differ)",
    )
    args = parser.parse_args(argv)

    if not args.sidecar.is_file():
        print(f"sidecar not found: {args.sidecar}", file=sys.stderr)
        return 1

    counts: collections.Counter[str] = collections.Counter()
    total_bytes: collections.Counter[str] = collections.Counter()
    details: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    missing_size = 0

    with args.sidecar.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            key = record.get(args.axis) or "<unset>"
            counts[key] += 1
            size = record.get("size_bytes")
            if isinstance(size, int):
                total_bytes[key] += size
            else:
                missing_size += 1
            load = record.get("load") or {}
            if load.get("status") and load.get("status") != "snapshot_ok":
                details[key][str(load.get("detail"))] += 1

    grand_files = sum(counts.values())
    grand_bytes = sum(total_bytes.values())

    print(f"sidecar: {args.sidecar}")
    print(f"axis:    {args.axis}\n")
    print(f"{'cohort':<24} {'files':>8} {'bytes':>14} {'mean/file':>12}")
    print("-" * 62)
    for key, n_files in counts.most_common():
        n_bytes = total_bytes[key]
        mean = _human(n_bytes // n_files) if n_files else "-"
        print(f"{key:<24} {n_files:>8,} {_human(n_bytes):>14} {mean:>12}")
    print("-" * 62)
    print(f"{'TOTAL':<24} {grand_files:>8,} {_human(grand_bytes):>14}")
    if missing_size:
        print(f"\n(records with no size_bytes: {missing_size})")

    for key, reasons in sorted(details.items()):
        print(f"\nload-failure signatures within '{key}':")
        for reason, n in reasons.most_common(10):
            print(f"  {n:>6,}  {reason}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
