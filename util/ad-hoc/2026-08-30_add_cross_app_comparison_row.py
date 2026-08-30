#!/usr/bin/env python3
"""
Add the §12.2-item-3 cross-app comparison row to the Juniper Experiments dashboard.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-30
Status: ad-hoc -- one-off (CLI-experimentation plan §12.2 item 3)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md (§4, the
         item); plan §12.2 item 3 ("No cross-app comparison surface"); juniper-deploy#167 (the
         dashboard this edits), #171 (the PF row it is inserted before)

Why a script rather than a hand edit
------------------------------------
The dashboard is a 29 KB generated-looking JSON whose panels carry absolute ``gridPos.y``
coordinates. Inserting a row in the MIDDLE means shifting every subsequent panel, which is
exactly the kind of arithmetic a hand edit gets wrong silently -- an overlapping panel still
renders, just wrongly. This also makes the change reproducible against a moved upstream file.

What it adds, and the honest limits of each panel
-------------------------------------------------
The plan asks for "a single Grafana row comparing cascor and recurrence run durations across
run_ids". The two apps expose DISJOINT metric families and cascor has no run-duration metric at
all (its closest is a per-step histogram), so there is no single native series to compare. The
row therefore carries both kinds of panel and says which is which:

* **Like-for-like** (wall-clock, CPU seconds) -- from ``process_*`` collectors, which every
  service exposes with identical semantics. These are the real comparison.
* **Native** (table) -- each app's own training-time metric side by side, with the semantic
  difference stated in the panel description rather than left for the reader to trip over.

Verified against the live Prometheus on :9090 before writing: ``process_start_time_seconds``
and ``process_cpu_seconds_total`` both carry ``run_id`` / ``service`` / ``experiment`` under
``environment="host-experiment"``.

Idempotent: re-running detects the row by title and makes no change.

Usage
-----
    python3 util/ad-hoc/2026-08-30_add_cross_app_comparison_row.py --in DASH.json --out DASH.json
    python3 util/ad-hoc/2026-08-30_add_cross_app_comparison_row.py --in DASH.json --check

Exit 0 = written (or already present, or --check found it); 1 = --check and the row is absent;
2 = the input is unusable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROW_TITLE = "Cross-App Comparison — cascor vs recurrence"
ANCHOR_ROW_TITLE = "HTTP (host-experiment targets)"
SELECTOR = 'environment="host-experiment", run_id=~"$run_id", service=~"$service"'
DS = {"type": "prometheus", "uid": "prometheus"}

# row (h=1) + one 8-high pair + one 8-high table
ROW_HEIGHT = 17


def build_panels(base_id: int, row_y: int) -> list[dict]:
    """The row header plus its three panels, laid out from ``row_y``."""
    return [
        {
            "id": base_id,
            "type": "row",
            "title": ROW_TITLE,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": row_y},
            "collapsed": False,
        },
        {
            "id": base_id + 1,
            "type": "timeseries",
            "title": "Run Wall-Clock by Service",
            "description": (
                "time() - process_start_time_seconds — LIKE-FOR-LIKE across apps: every service "
                "exposes this with identical semantics, so cascor and recurrence are directly "
                "comparable here. Caveat: it measures the run's SERVICE lifetime, not training "
                "time alone. The experiment stack is brought up and torn down per run, so the two "
                "are close, but a slow import or a long teardown lands in this number."
            ),
            "datasource": DS,
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": row_y + 1},
            "targets": [
                {
                    "refId": "A",
                    "expr": f"time() - process_start_time_seconds{{{SELECTOR}}}",
                    "legendFormat": "{{service}} — {{run_id}}",
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "unit": "s",
                    "min": 0,
                    "custom": {"drawStyle": "line", "lineInterpolation": "stepAfter", "fillOpacity": 0},
                }
            },
            "options": {
                "legend": {"displayMode": "table", "placement": "bottom", "calcs": ["last", "max"]},
                "tooltip": {"mode": "multi"},
            },
        },
        {
            "id": base_id + 2,
            "type": "timeseries",
            "title": "Run CPU Seconds by Service",
            "description": (
                "process_cpu_seconds_total — LIKE-FOR-LIKE across apps, identical semantics. "
                "Cumulative CPU seconds consumed by each run's service. Use this rather than "
                "wall-clock when comparing runs that shared the host with other work: wall-clock "
                "absorbs contention (a concurrent clamscan measured +6.8% on one cell), CPU "
                "seconds largely does not."
            ),
            "datasource": DS,
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": row_y + 1},
            "targets": [
                {
                    "refId": "A",
                    "expr": f"process_cpu_seconds_total{{{SELECTOR}}}",
                    "legendFormat": "{{service}} — {{run_id}}",
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "unit": "s",
                    "min": 0,
                    "custom": {"drawStyle": "line", "lineInterpolation": "linear", "fillOpacity": 0},
                }
            },
            "options": {
                "legend": {"displayMode": "table", "placement": "bottom", "calcs": ["last", "max"]},
                "tooltip": {"mode": "multi"},
            },
        },
        {
            "id": base_id + 3,
            "type": "table",
            "title": "Native Training Time — cascor vs recurrence",
            "description": (
                "Each app's OWN training-time metric, side by side. These are NOT like-for-like and "
                "must not be subtracted or ratioed: cascor's is the histogram _sum, i.e. cumulative "
                "seconds spent inside training steps (monotonic, excludes non-step overhead); "
                "recurrence's is a gauge holding the wall duration of the MOST RECENT training run "
                "(it resets each run). Both are seconds over different denominators. For a strict "
                "cross-app comparison use the wall-clock or CPU-seconds panels above. cascor has no "
                "run-duration metric — plan §12.2 item 1 option (b) proposed one and it was not built."
            ),
            "datasource": DS,
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": row_y + 9},
            "targets": [
                {
                    "refId": "A",
                    "expr": (
                        "sum by (run_id, service, experiment) "
                        f"(juniper_cascor_training_step_duration_seconds_sum{{{SELECTOR}}})"
                    ),
                    "legendFormat": "cascor cumulative step seconds",
                    "instant": True,
                    "format": "table",
                },
                {
                    "refId": "B",
                    "expr": (
                        "sum by (run_id, service, experiment) "
                        f"(juniper_recurrence_train_last_duration_seconds{{{SELECTOR}}})"
                    ),
                    "legendFormat": "recurrence last train wall seconds",
                    "instant": True,
                    "format": "table",
                },
            ],
            "fieldConfig": {"defaults": {"unit": "s", "min": 0}},
            "options": {"showHeader": True},
        },
    ]


def insert_row(doc: dict) -> tuple[dict, str]:
    """Insert the row before the anchor row, shifting everything below it down."""
    panels = doc.get("panels")
    if not isinstance(panels, list) or not panels:
        raise ValueError("dashboard has no panels list")

    if any(p.get("title") == ROW_TITLE for p in panels):
        return doc, "already present"

    anchor = next((p for p in panels if p.get("type") == "row" and p.get("title") == ANCHOR_ROW_TITLE), None)
    if anchor is None:
        raise ValueError(f"anchor row not found: {ANCHOR_ROW_TITLE!r}")

    row_y = anchor["gridPos"]["y"]
    base_id = max(int(p.get("id", 0)) for p in panels) + 1

    # Shift every panel at or below the anchor. Absolute coordinates mean an unshifted panel
    # silently OVERLAPS the new row rather than erroring.
    for p in panels:
        if p.get("gridPos", {}).get("y", -1) >= row_y:
            p["gridPos"]["y"] += ROW_HEIGHT

    anchor_idx = panels.index(anchor)
    new_panels = build_panels(base_id, row_y)
    doc["panels"] = panels[:anchor_idx] + new_panels + panels[anchor_idx:]
    return doc, f"inserted {len(new_panels)} panels at y={row_y} (ids {base_id}..{base_id + 3})"


def validate(doc: dict) -> list[str]:
    """Structural checks that a bad edit would otherwise ship silently."""
    problems: list[str] = []
    panels = doc["panels"]

    ids = [p.get("id") for p in panels]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        problems.append(f"duplicate panel ids: {dupes}")

    # Occupancy check: no two panels may claim the same grid cell.
    seen: dict[tuple[int, int], int] = {}
    for p in panels:
        g = p.get("gridPos", {})
        for yy in range(g.get("y", 0), g.get("y", 0) + g.get("h", 0)):
            for xx in range(g.get("x", 0), g.get("x", 0) + g.get("w", 0)):
                if (xx, yy) in seen:
                    problems.append(f"panel {p.get('id')} overlaps panel {seen[(xx, yy)]} at x={xx} y={yy}")
                    return problems
                seen[(xx, yy)] = p.get("id")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", type=Path, required=True)
    ap.add_argument("--out", dest="dst", type=Path)
    ap.add_argument("--check", action="store_true", help="report whether the row is present; write nothing")
    args = ap.parse_args(argv)

    try:
        doc = json.loads(args.src.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - operator-facing message beats a traceback
        print(f"unusable input {args.src}: {exc}", file=sys.stderr)
        return 2

    if args.check:
        present = any(p.get("title") == ROW_TITLE for p in doc.get("panels", []))
        print(f"{ROW_TITLE!r}: {'present' if present else 'ABSENT'}")
        return 0 if present else 1

    try:
        doc, note = insert_row(doc)
    except ValueError as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2

    problems = validate(doc)
    if problems:
        for p in problems:
            print(f"VALIDATION FAILED: {p}", file=sys.stderr)
        return 2

    if note == "already present":
        print("unchanged — row already present")
        return 0

    dst = args.dst or args.src
    # ensure_ascii=True is NOT the default-by-accident: it is what the upstream file uses, and
    # `json.dumps(json.loads(f)) == f` is byte-exact only with it. Flipping it to False rewrites
    # every \uXXXX escape in the file and turns a 4-panel insert into a whole-file diff.
    dst.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"{note}; wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
