#!/usr/bin/env python3
"""
Project     : Juniper - Cascade Correlation Neural Network Research Platform
Sub-Project : juniper-ml
Application : E2E canopy validation arc - Phase 1 row-coverage mapper
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Ad-hoc helper for the canopy E2E validation arc (plan
notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md).

Answers "which matrix rows still need a verdict?" by diffing the row-id
inventory of the click-by-click matrix against every accumulated verdict
record (the run TSVs plus the inherited rowlog from the superseded
arc/canopy-e2e-phase1-results run).

Handles the compressed range notation the run records use
("M-TOPOLOGY-01..06,09..18", "W1-01..11", "W14-01..11").

Usage:
    python util/ad-hoc/e2e_row_coverage.py [--repo-root P] [--json]
                                           [--verdict-file F]...

Exit 0 always (report-only).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

MATRIX = "notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md"

# A matrix row id: leading token of a markdown table row, e.g. C2.1-01,
# M-NETWORK-EDITOR-05, W13-01. Trailing lane-arm suffixes (-L / -D) are
# stripped so live/demo arms fold onto their matrix row.
ROW_ID_RE = re.compile(r"^\|\s*([A-Z][A-Za-z0-9.]*(?:-[A-Z0-9]+)*-\d+)\s*\|")
# A verdict token, anywhere in a record line: base prefix + numeric range set.
VERDICT_RE = re.compile(r"\b([A-Z][A-Za-z0-9.]*(?:-[A-Z]+)*)-(\d+(?:\.\.\d+)?(?:,\d+(?:\.\.\d+)?)*)\b")

LANE_SUFFIX_RE = re.compile(r"-(?:L|D)$")


def strip_lane(row_id: str) -> str:
    return LANE_SUFFIX_RE.sub("", row_id)


def matrix_rows(repo_root: Path) -> list[str]:
    """Ordered, de-duplicated row ids declared in the matrix tables."""
    path = repo_root / MATRIX
    seen: dict[str, None] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ROW_ID_RE.match(line)
        if m:
            seen.setdefault(strip_lane(m.group(1)), None)
    return list(seen)


def expand(prefix: str, spec: str, width: int) -> set[str]:
    """Expand "01..06,09" into a set of zero-padded row ids."""
    out: set[str] = set()
    for part in spec.split(","):
        if ".." in part:
            lo_s, hi_s = part.split("..", 1)
            pad = max(width, len(lo_s), len(hi_s))
            for n in range(int(lo_s), int(hi_s) + 1):
                out.add(f"{prefix}-{n:0{pad}d}")
        else:
            pad = max(width, len(part))
            out.add(f"{prefix}-{int(part):0{pad}d}")
    return out


def verdicted(paths: list[Path], known: set[str]) -> tuple[set[str], set[str]]:
    """
    Row ids carrying a verdict, plus tokens that matched no matrix row.

    Only the first field of a TSV line and explicit range tokens are trusted
    as verdict subjects; prose row references elsewhere on the line would
    otherwise credit rows that were merely mentioned.
    """
    hit: set[str] = set()
    unknown: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # TSV: first column. Markdown rowlog: first cell after the pipe.
            head = line.split("\t", 1)[0]
            if head.startswith("|"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                head = cells[0] if cells else ""
            if not head or head in {"row_id", "row"}:
                continue
            for m in VERDICT_RE.finditer(head):
                prefix, spec = m.group(1), m.group(2)
                width = len(spec.split("..")[0].split(",")[0])
                ids = expand(strip_lane(prefix), spec, width)
                for rid in ids:
                    (hit if rid in known else unknown).add(rid)
    return hit, unknown


def group(rows: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        out[r.rsplit("-", 1)[0]].append(r)
    return dict(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".", type=Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verdict-file", action="append", default=[], type=Path)
    args = ap.parse_args()

    root = args.repo_root.resolve()
    rows = matrix_rows(root)
    known = set(rows)

    files = args.verdict_file or sorted(
        list((root / "reports" / "e2e").glob("*/statuses.tsv"))
        + list((root / "reports" / "e2e").glob("*/rowlog.md"))
    )
    done, unknown = verdicted([Path(f) for f in files], known)
    remaining = [r for r in rows if r not in done]

    if args.json:
        print(json.dumps({
            "matrix_rows": len(rows), "verdicted": len(done),
            "remaining": len(remaining), "remaining_rows": remaining,
            "unmatched_tokens": sorted(unknown),
            "verdict_files": [str(f) for f in files],
        }, indent=2))
        return 0

    print(f"matrix rows : {len(rows)}")
    print(f"verdicted   : {len(done)}")
    print(f"remaining   : {len(remaining)}")
    print(f"sources     : {len(files)} verdict file(s)")
    if unknown:
        print(f"\nunmatched verdict tokens ({len(unknown)}): {', '.join(sorted(unknown))}")
    print("\nremaining by group:")
    for g, members in sorted(group(remaining).items()):
        print(f"  {g:<24} {len(members):>3}  {', '.join(m.rsplit('-', 1)[1] for m in members)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
