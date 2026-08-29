#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : cross-repo tooling (ad-hoc)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Collect the cascor#582 selection-bias measurement across a suite's cells.

Reads each cell's run dir from the suite ``registry.jsonl`` and greps that run's trainer log --
INCLUDING rotated siblings, because service run logs rotate and an analysis that reads only
``juniper_cascor.log`` silently misses records -- for the probe line emitted by the
``diag/tensor-hash-probe-572`` branch under ``JUNIPER_DIAG_VAL_SPLIT=1``:

    DIAG-VALSPLIT: RESULT n_sel=100 n_out=100 acc_selected_on=… acc_held_out=… optimism=…

Both halves come from one partition and are scored on the SAME final model; only one of them was
visible to early stopping. ``optimism = acc_selected_on - acc_held_out`` is therefore a paired
estimate of the bias that #582's X_test-as-validation promotion puts into the reported metric.

VACUITY: a cell whose log yields no RESULT line is reported as MISSING and excluded from the
statistics -- never counted as a zero. Absence of evidence is not a measurement of no effect.

Usage
-----
    2026-08-29_val_split_bias_collect.py <SUITE_DIR>

Exit: 0 if at least one cell reported; 2 on usage / no registry / zero cells reporting.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

RESULT_RE = re.compile(
    r"DIAG-VALSPLIT: RESULT n_sel=(?P<n_sel>\d+) n_out=(?P<n_out>\d+) "
    r"acc_selected_on=(?P<sel>[-\d.]+) acc_held_out=(?P<out>[-\d.]+) optimism=(?P<opt>[-+\d.]+)"
)


def find_result(run_dir: Path) -> dict | None:
    """Scan a run's trainer log and its rotated siblings; return the LAST result found."""
    found = None
    for log in sorted((run_dir / "logs").glob("juniper_cascor.log*")):
        try:
            for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
                m = RESULT_RE.search(line)
                if m:
                    found = m.groupdict()
        except OSError as exc:
            print(f"# WARNING unreadable {log.name}: {type(exc).__name__}", file=sys.stderr)
    return found


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    suite_dir = Path(argv[0])
    registry = suite_dir / "registry.jsonl"
    if not registry.is_file():
        print(f"no registry.jsonl under {suite_dir}", file=sys.stderr)
        return 2

    rows, missing = [], []
    for raw in registry.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        rec = json.loads(raw)
        run_dir = rec.get("run_dir")
        cell = rec.get("cell_id", "?")
        seed = (rec.get("overrides") or {}).get("dataset.params.seed", "?")
        if not run_dir:
            missing.append((cell, seed, "no run_dir in registry"))
            continue
        res = find_result(Path(run_dir))
        if res is None:
            missing.append((cell, seed, "no RESULT line in log"))
            continue
        rows.append(
            {
                "cell": cell,
                "seed": seed,
                "n_sel": int(res["n_sel"]),
                "n_out": int(res["n_out"]),
                "sel": float(res["sel"]),
                "out": float(res["out"]),
                "opt": float(res["opt"]),
            }
        )

    print(f"# suite: {suite_dir}")
    print(f"# cells reporting: {len(rows)}   MISSING: {len(missing)}")
    print()
    print(f"{'cell':<16} {'ds_seed':>8} {'n_sel':>6} {'n_out':>6} {'selected_on':>12} {'held_out':>10} {'optimism':>10}")
    for r in rows:
        print(f"{r['cell']:<16} {str(r['seed']):>8} {r['n_sel']:>6} {r['n_out']:>6} {r['sel']:>12.4f} {r['out']:>10.4f} {r['opt']:>+10.4f}")
    for cell, seed, why in missing:
        print(f"{cell:<16} {str(seed):>8}   MISSING -- {why}")

    if not rows:
        print("\nno cell reported a RESULT line; nothing to summarise", file=sys.stderr)
        return 2

    opts = [r["opt"] for r in rows]
    sels = [r["sel"] for r in rows]
    outs = [r["out"] for r in rows]
    n = len(opts)
    mean_opt = statistics.fmean(opts)
    sd_opt = statistics.stdev(opts) if n > 1 else float("nan")
    print()
    print(f"mean selected_on : {statistics.fmean(sels):.4f}")
    print(f"mean held_out    : {statistics.fmean(outs):.4f}")
    print(f"mean OPTIMISM    : {mean_opt:+.4f}   sd {sd_opt:.4f}   n {n}")
    if n > 1:
        se = sd_opt / (n**0.5)
        lo, hi = mean_opt - 1.96 * se, mean_opt + 1.96 * se
        print(f"95% CI (normal)  : [{lo:+.4f}, {hi:+.4f}]   se {se:.4f}")
        print(f"positive cells   : {sum(1 for o in opts if o > 0)}/{n}   zero: {sum(1 for o in opts if o == 0)}   negative: {sum(1 for o in opts if o < 0)}")
        if lo <= 0.0 <= hi:
            print("VERDICT: the interval INCLUDES zero -- this sample does not establish a nonzero bias.")
        else:
            print("VERDICT: the interval EXCLUDES zero -- a nonzero bias in the stated direction.")
    print()
    print("# Each half is ~100 rows, so a single cell's optimism is dominated by sampling noise")
    print("# between halves. The mean over independent datasets is the estimate; the sd is the noise.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
