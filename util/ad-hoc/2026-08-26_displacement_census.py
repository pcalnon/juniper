"""
Census displaced attributions in an existing sidecar, without re-running attribution.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/snapshot_attribute.py SS DISPLACEMENT in adjudicate();
         notes/JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md SS3.2

WHY THIS EXISTS
    `adjudicate()` now marks an ATTRIBUTED row `displaced` when the winner (highest LIFT) is not
    the highest RAW scorer. Rows already in the sidecar predate the field, and re-running
    attribution over 28k snapshots to populate it is expensive.

    Every sidecar row already stores its full `scores` vector, so displacement is recomputable
    offline and exactly: `max(scores) != dataset`. That is the same comparison `adjudicate` makes,
    so this both CENSUSES the existing corpus and CHECKS the new flag against real data.

READ-ONLY. Opens the sidecar for reading and writes nothing.

USAGE
    python util/ad-hoc/2026-08-26_displacement_census.py \
        ~/Development/python/Juniper/juniper-cascor/cascor-snapshots/snapshots_attribution.jsonl
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from typing import Any, Dict, List

ATTRIBUTED = "attributed"


def load_rows(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    rows = load_rows(sys.argv[1])
    attributed = [r for r in rows if r.get("verdict") == ATTRIBUTED]
    print(f"sidecar rows: {len(rows)}")
    print(f"attributed:   {len(attributed)}")

    displaced: List[Dict[str, Any]] = []
    by_dataset: Counter = Counter()
    pairs: Counter = Counter()

    for row in attributed:
        scores = row.get("scores") or {}
        if not scores:
            continue
        raw_best = max(scores, key=lambda name: scores[name])
        winner = row.get("dataset")
        by_dataset[winner] += 1
        if raw_best != winner:
            displaced.append(row)
            pairs[(winner, raw_best)] += 1

    print(f"displaced:    {len(displaced)} of {len(attributed)}")
    print()
    print("attributed by dataset:")
    for name, count in by_dataset.most_common():
        print(f"   {name:<14} {count}")
    print()
    print("displacement pairs (winner <- outscored by):")
    for (winner, raw_best), count in pairs.most_common():
        print(f"   {winner:<14} <- {raw_best:<14} x{count}")

    print()
    print("displaced rows:")
    for row in displaced:
        scores = row["scores"]
        raw_best = max(scores, key=lambda name: scores[name])
        winner = row["dataset"]
        print(
            f"   {str(row.get('name', ''))[:52]:<52} {str(row.get('hidden_units', '-')):>4}u  "
            f"{winner} {scores[winner]:.3f} (lift {row.get('lift', 0):+.3f})  "
            f"< {raw_best} {scores[raw_best]:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
