#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

One-off: seed ``conf/memory_index_baseline.json``'s growth series with the single
datapoint that predates the tool.

``util/memory_index_check.py --accept`` records a sample every time it runs, but a
runway needs two. The earlier point exists only in the shared-session-memory plan's
P0 execution log (2026-08-19: 123 rows / 16,933 bytes) -- ``MEMORY.md`` has no git
history, so it cannot be recovered any other way.

It is tagged with an explicit ``source`` saying it was RECONSTRUCTED rather than
measured, and every sample the tool writes is tagged too, so the provenance of the
series is never ambiguous. Run once; after that the tool maintains the series.

Usage:
    python3 util/ad-hoc/2026-08-24_seed_memory_index_history.py [--baseline PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SEED = {
    "date": "2026-08-19",
    "rows": 123,
    "lines": 123,
    "bytes": 16933,
    "source": "plan P0 execution log (reconstructed, not measured by this tool)",
}
MEASURED = "measured by util/memory_index_check.py --accept"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", type=Path, default=Path("conf/memory_index_baseline.json"))
    args = ap.parse_args()

    if not args.baseline.is_file():
        print(f"error: no baseline at {args.baseline}; run `memory_index_check.py --accept` first", file=sys.stderr)
        return 2

    data = json.loads(args.baseline.read_text(encoding="utf-8"))
    history = [h for h in (data.get("history") or []) if h.get("date") != SEED["date"]]
    for h in history:
        h.setdefault("source", MEASURED)
    data["history"] = [SEED] + history
    args.baseline.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"seeded {args.baseline}: {len(data['history'])} samples, {len(data.get('slugs') or [])} slugs")
    for h in data["history"]:
        print(f"  {h['date']}  {h['bytes']:>6} B  {h.get('source', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
