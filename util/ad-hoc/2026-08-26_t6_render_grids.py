#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Status:      ad-hoc -- one-off (T6 re-baseline publish step)
Retire when: RETAINED (owner policy 2026-08-25 -- no retirement deadline)
Related:     HANDOFF_2026-08-25_t6-rebaseline-window-held-not-launched.md SS1 step 4;
             notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md

Render a suite run's grid as the markdown table the P4 evidence doc publishes, joining
the suite registry (outcome, wall) with each cell's ``artifacts/results/metrics_final.json``
(val / train accuracy, hidden units, epoch) and ``manifest.json`` (completion reason).

An optional ``--reference SUITE_DIR`` (repeatable) adds a "ref wall" column matched on the
cell's varied parameters -- NOT on cell_id, which is a hash of the overrides and moves when
a budget changes (E-A's wide-pool-long went 850cdc66 -> 63f4fcb9 in ml#1284). Reference
walls are context only: R-5 SS5.1 and F-P4-6 make cross-sha wall comparisons
non-attributable, so the caller labels the column accordingly.

Usage:
    python3 util/ad-hoc/2026-08-26_t6_render_grids.py SUITE_DIR [--reference DIR ...]
        [--run-root ~/.local/state/juniper-experiments] [--label-ref NAME ...]

Reads only; writes nothing.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import sys
from pathlib import Path

DEFAULT_RUN_ROOT = Path(os.path.expanduser("~/.local/state/juniper-experiments"))
META_COLS = {"cell_id", "name", "run_id", "outcome", "exit_code", "wall_seconds"}
NON_KEY_COLS = {"outputs.max_wall_seconds"}  # budgets change between runs; not part of the cell identity


def load_rows(suite_dir: Path) -> list[dict]:
    """aggregate.csv when the suite finished; registry.jsonl (no override columns) otherwise."""
    agg = suite_dir / "aggregate.csv"
    if agg.is_file():
        with agg.open(newline="") as fh:
            rows = list(csv.DictReader(fh))
        # An include cell's nested override (E-C's moon cells: dataset.params: {...}) lands in
        # the CSV as one dict-repr column; flatten it one level so both load paths agree.
        for row in rows:
            for k, v in list(row.items()):
                if isinstance(v, str) and v.startswith("{"):
                    try:
                        nested = ast.literal_eval(v)
                    except (ValueError, SyntaxError):
                        continue
                    if isinstance(nested, dict):
                        del row[k]
                        for kk, vv in nested.items():
                            # the CSV may already carry an EMPTY matrix column of the same name
                            # (E-C: dataset.params.noise is blank on the moon include rows)
                            if row.get(f"{k}.{kk}") in (None, ""):
                                row[f"{k}.{kk}"] = vv
        return rows
    reg = suite_dir / "registry.jsonl"
    rows = []
    if reg.is_file():
        for line in reg.read_text().splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            # Mirror aggregate.csv's shape: the meta columns plus one column per override,
            # nested override dicts (E-C's dataset.params) flattened one level.
            row = {k: raw.get(k) for k in ("cell_id", "name", "run_id", "outcome", "exit_code", "wall_seconds")}
            for k, v in (raw.get("overrides") or {}).items():
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        row[f"{k}.{kk}"] = vv
                else:
                    row[k] = v
            rows.append(row)
    return rows


def cell_key(row: dict) -> tuple:
    """Identity of a cell = its varied parameters (override columns) plus its include name."""
    parts = [("name", row.get("name") or "")]
    for k in sorted(row):
        if k in META_COLS or k in NON_KEY_COLS:
            continue
        v = row.get(k)
        if v in (None, ""):
            continue
        parts.append((k, str(v)))
    return tuple(parts)


def cell_metrics(run_root: Path, run_id: str) -> dict:
    out = {"val_acc": None, "train_acc": None, "hidden": None, "epoch": None, "reason": None}
    rd = run_root / run_id
    mf = rd / "artifacts" / "results" / "metrics_final.json"
    if mf.is_file():
        m = json.loads(mf.read_text())
        out.update(val_acc=m.get("val_accuracy"), train_acc=m.get("train_accuracy"), hidden=m.get("hidden_units"), epoch=m.get("epoch"))
    man = rd / "manifest.json"
    if man.is_file():
        man_d = json.loads(man.read_text())
        out["reason"] = man_d.get("completion_reason")
        if out["val_acc"] is None:
            out["val_acc"] = (man_d.get("acceptance") or {}).get("val_accuracy")
    return out


def fmt(v, nd=4):
    if v is None or v == "":
        return "—"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    try:
        f = float(v)
        return f"{f:.{nd}f}" if "." in str(v) else str(v)
    except (TypeError, ValueError):
        return str(v)


def short_param(col: str) -> str:
    return col.split(".")[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    ap.add_argument("suite_dir", type=Path)
    ap.add_argument("--reference", action="append", default=[], type=Path, help="prior suite dir; adds a ref-wall column matched on varied params")
    ap.add_argument("--label-ref", action="append", default=[], help="column label for each --reference, in order")
    ap.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = ap.parse_args()

    rows = load_rows(args.suite_dir)
    if not rows:
        print(f"no rows in {args.suite_dir}", file=sys.stderr)
        return 1
    param_cols = sorted({k for r in rows for k in r if k not in META_COLS and k not in NON_KEY_COLS and r.get(k) not in (None, "")})

    refs = []
    for i, rdir in enumerate(args.reference):
        label = args.label_ref[i] if i < len(args.label_ref) else rdir.name
        refs.append((label, {cell_key(r): r for r in load_rows(rdir)}))

    head = ["cell"] + [short_param(c) for c in param_cols] + ["outcome", "wall (s)"]
    head += [f"{lbl} wall (s)" for lbl, _ in refs]
    head += ["val acc", "train acc", "hidden", "epoch", "completion"]
    print("| " + " | ".join(head) + " |")
    print("|" + "|".join("---" for _ in head) + "|")

    total_wall = 0.0
    n_ok = 0
    unparsed_walls = 0
    for r in rows:
        met = cell_metrics(args.run_root, r.get("run_id", "")) if r.get("run_id") else {}
        wall = r.get("wall_seconds")
        if wall not in (None, ""):
            try:
                total_wall += float(wall)
            except (TypeError, ValueError):
                unparsed_walls += 1  # a not-run / malformed row: reported in the summary, never silently dropped
        if r.get("outcome") == "succeeded":
            n_ok += 1
        cells = [r.get("name") or r.get("cell_id", "")]
        cells += [fmt(r.get(c)) for c in param_cols]
        cells += [r.get("outcome", ""), fmt(wall, 1)]
        key = cell_key(r)
        for _, table in refs:
            ref = table.get(key)
            cells.append(fmt(ref.get("wall_seconds"), 1) + (f" ({ref.get('outcome')})" if ref and ref.get("outcome") != "succeeded" else "") if ref else "—")
        cells += [fmt(met.get("val_acc")), fmt(met.get("train_acc")), fmt(met.get("hidden")), fmt(met.get("epoch")), met.get("reason") or "—"]
        print("| " + " | ".join(str(c) for c in cells) + " |")
    print()
    extra = f"; unparsed walls: {unparsed_walls}" if unparsed_walls else ""
    print(f"cells: {len(rows)}; succeeded: {n_ok}; summed wall: {total_wall:.1f} s ({total_wall/3600:.2f} h){extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
