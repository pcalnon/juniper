"""
Characterise the snapshot archive for the S-2 retention question. Read-only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-22
Status: ad-hoc — investigation (evidence for S-2: "is the March–April 2026 cohort of
        retained research value?")
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: S-2 is decided and any retention policy lands under design §6.4.
Related: notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md
         (§6.2 index, §6.4 retention), util/snapshot_index.py

WHAT IT ANSWERS
    S-2 cannot be answered by provenance: D-C applies going forward, and the whole
    Mar–Apr cohort predates it, so every one of those files is unattributed. The only
    evidence available is what is INSIDE them plus whatever run dirs survive.

    So this asks what the files themselves say: how many distinct networks, how much
    training each represents, what architectures, what the size and time distribution
    look like, and how much of the archive is plausibly one campaign versus incidental.

WHY IT READS THE INDEX, NOT THE FILES
    The §6.2 index already holds every field this needs, so a full characterisation is
    a second of JSON parsing instead of ~3.5 minutes of HDF5 opens. It also means this
    script cannot damage a snapshot -- it never opens one.

METHOD NOTE (the trap this arc already paid for)
    `created` is the authoritative timestamp, NOT mtime: a copy reset every mtime in
    this archive, so anything date-derived must come from the internal attribute. The
    filename's date agrees with `created` and is used only as a cross-check.

    Equally, one file is not a cohort. Everything here is reported as a DISTRIBUTION
    with counts, so a headline claim can be checked against the spread that produced it.

USAGE
    python util/ad-hoc/2026-08-22_s2_cohort_characterisation.py [--index PATH] [--json]
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_INDEX = Path("/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots/snapshots_index.jsonl")

#: The cohort S-2 asks about.
COHORT_MONTHS = ("2026-03", "2026-04")


def load(index_path: Path) -> List[dict]:
    rows = []
    for line in index_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def month_of(row: dict) -> str:
    """Month from the internal ``created`` attribute — never from mtime."""
    created = row.get("created") or ""
    return created[:7] if len(created) >= 7 else "unknown"


def human(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unit == "GiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0
    return str(n)


def describe(rows: List[dict], label: str) -> Dict[str, Any]:
    sizes = [r.get("size_bytes", 0) for r in rows]
    epochs = [r.get("current_epoch") for r in rows if isinstance(r.get("current_epoch"), int)]
    uuids = Counter(r.get("uuid") for r in rows if r.get("uuid"))
    archs = Counter(
        (
            (r.get("arch") or {}).get("input_size"),
            (r.get("arch") or {}).get("output_size"),
            (r.get("arch") or {}).get("num_hidden_units"),
        )
        for r in rows
    )
    hidden = Counter((r.get("arch") or {}).get("num_hidden_units") for r in rows)
    per_uuid = Counter(uuids.values())

    return {
        "label": label,
        "snapshots": len(rows),
        "bytes": sum(sizes),
        "bytes_human": human(sum(sizes)),
        "distinct_networks_by_uuid": len(uuids),
        "snapshots_per_network": {
            "median": statistics.median(uuids.values()) if uuids else 0,
            "max": max(uuids.values()) if uuids else 0,
            "singletons": per_uuid.get(1, 0),
        },
        "size": {
            "median": human(int(statistics.median(sizes))) if sizes else "-",
            "max": human(max(sizes)) if sizes else "-",
        },
        "current_epoch": {
            "zero": sum(1 for e in epochs if e == 0),
            "nonzero": sum(1 for e in epochs if e > 0),
            "max": max(epochs) if epochs else None,
            "median_nonzero": statistics.median([e for e in epochs if e > 0]) if any(e > 0 for e in epochs) else None,
        },
        "hidden_units": dict(sorted(((k, v) for k, v in hidden.items() if k is not None), key=lambda kv: -kv[1])[:8]),
        "top_architectures": [{"in_out_hidden": list(k), "count": v} for k, v in archs.most_common(6)],
        "writer_versions": dict(Counter(r.get("juniper_version") for r in rows).most_common()),
        "unreadable": sum(1 for r in rows if not r.get("readable")),
        "attributed": sum(1 for r in rows if r.get("provenance")),
    }


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if not args.index.is_file():
        print(f"ERROR: no index at {args.index} — run util/snapshot_index.py --scan first")
        return 2

    rows = load(args.index)
    by_month: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        by_month[month_of(row)].append(row)

    cohort = [r for r in rows if month_of(r) in COHORT_MONTHS]
    rest = [r for r in rows if month_of(r) not in COHORT_MONTHS]

    report = {
        "index": str(args.index),
        "by_month": {m: {"snapshots": len(v), "bytes_human": human(sum(x.get("size_bytes", 0) for x in v))} for m, v in sorted(by_month.items())},
        "whole_archive": describe(rows, "whole archive"),
        "cohort_2026_03_04": describe(cohort, "Mar–Apr 2026 cohort"),
        "outside_cohort": describe(rest, "outside the cohort"),
    }

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return 0

    print(f"index: {args.index}\n")
    print("=== snapshots by month (from the internal `created` attr, not mtime) ===")
    for month, stats in report["by_month"].items():
        print(f"  {month:<10} {stats['snapshots']:>7}   {stats['bytes_human']:>10}")
    for key in ("whole_archive", "cohort_2026_03_04", "outside_cohort"):
        block = report[key]
        print(f"\n=== {block['label']} ===")
        print(f"  snapshots            : {block['snapshots']}")
        print(f"  bytes                : {block['bytes_human']}")
        print(f"  distinct networks    : {block['distinct_networks_by_uuid']}  (by meta.uuid)")
        print(f"  snapshots/network    : median {block['snapshots_per_network']['median']}, max {block['snapshots_per_network']['max']}, singletons {block['snapshots_per_network']['singletons']}")
        print(f"  size                 : median {block['size']['median']}, max {block['size']['max']}")
        print(f"  current_epoch        : zero {block['current_epoch']['zero']}, non-zero {block['current_epoch']['nonzero']}, max {block['current_epoch']['max']}, median non-zero {block['current_epoch']['median_nonzero']}")
        print(f"  hidden-unit counts   : {block['hidden_units']}")
        print(f"  writer versions      : {block['writer_versions']}")
        print(f"  unreadable/attributed: {block['unreadable']} / {block['attributed']}")
        print("  top architectures (input, output, hidden):")
        for entry in block["top_architectures"]:
            print(f"      {tuple(entry['in_out_hidden'])!s:<20} {entry['count']:>7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
