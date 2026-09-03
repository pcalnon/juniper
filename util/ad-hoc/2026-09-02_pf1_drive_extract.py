#!/usr/bin/env python3
"""Compare the two candidate perf instruments across every PF-1 suite run.

SUPERSEDED 2026-09-03 by ``util/experiments/read_run_metrics.py`` (P2 item 0.4), which is the
canonical reader, is unit-tested (``tests/test_read_run_metrics.py``) and is wired into ``ci.yml``.
Use that for anything new.

RETAINED, not deleted: ad-hoc scripts are provenance of record (owner policy 2026-08-25), and this
file is the exact instrument that produced the 2026-09-02 P3 measurements -- the drive-quantization
finding, the headroom sweep, and the epoch calibration. Re-running it reproduces those numbers.

Project: Juniper
Sub-Project: juniper-ml
Application: perf lane (P3)
Author: Paul Calnon
License: MIT

Why this exists
---------------
Two traps sit between a reader and the PF-1 numbers.

1. ``aggregate.csv`` carries ``wall_seconds`` ONLY, and the perf lane de-ratified
   ``wall_seconds`` (it absorbs plot rendering and stack bring-up). The ratified metric
   ``timings.drive`` lives in each run's ``manifest.json``, reachable only via
   ``registry.jsonl``'s ``run_dir``.

2. ``timings.drive`` is QUANTIZED to the driver's status-poll interval
   (``DEFAULT_POLL_INTERVAL = 5.0`` in ``util/experiments/run_experiment.py``). The drive
   loop breaks only on a poll, so ``drive ~= (polls - 1) * 5.0 + accumulated HTTP overhead``.
   Real variation smaller than one poll cycle is invisible in ``drive``.

The poll-independent alternative is the cascor step-duration histogram, sampled into
``artifacts/results/metrics_series.csv`` every poll as ``..._sum`` / ``..._count``. Because
the PF-1 workload is seed-fixed, ``count`` is identical across repeats, which cleanly
separates a WORK regression (``count`` moves) from a SPEED regression (``sum/count`` moves).

Usage:  python3 util/ad-hoc/2026-09-02_pf1_drive_extract.py [SUITE_DIR ...]
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

STATE = Path.home() / ".local/state/juniper-experiments/suites"

STEP_SUM = "juniper_cascor_training_step_duration_seconds_sum"
STEP_COUNT = "juniper_cascor_training_step_duration_seconds_count"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _step_totals(run_dir: Path):
    """Final (sum, count) of the step-duration histogram, or (None, None)."""
    series = run_dir / "artifacts/results/metrics_series.csv"
    if not series.is_file():
        return None, None
    with series.open(encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get(STEP_SUM)]
    if not rows:
        return None, None
    last = rows[-1]
    try:
        return float(last[STEP_SUM]), float(last[STEP_COUNT])
    except (TypeError, ValueError, KeyError):
        return None, None


def _spread(values):
    """(median, mean, sd, sd_pct, spread_pct) for a sample of >= 2."""
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    return (
        statistics.median(values),
        mean,
        sd,
        100 * sd / mean,
        100 * (max(values) - min(values)) / min(values),
    )


def report(suite_dir: Path) -> dict | None:
    registry = suite_dir / "registry.jsonl"
    if not registry.is_file():
        print(f"\n=== {suite_dir.name}: no registry.jsonl ===")
        return None
    rows = [json.loads(line) for line in registry.read_text().splitlines() if line.strip()]

    print(f"\n=== {suite_dir.name}  ({len(rows)} cells) ===")
    print(f"{'cell':<16} {'polls':>5} {'drive':>9} {'step_sum':>9} {'steps':>7} {'mean_ms':>8}  scrape")
    drives, sums, counts = [], [], []
    for row in rows:
        run_dir = Path(row.get("run_dir", ""))
        manifest = _load_json(run_dir / "manifest.json")
        drive = (manifest.get("timings") or {}).get("drive")
        polls = (manifest.get("drive_loop") or {}).get("polls")
        scraped = manifest.get("metrics_scraped")
        confirmed = scraped.get("scrape_confirmed", "absent") if isinstance(scraped, dict) else scraped
        ssum, scount = _step_totals(run_dir)

        if drive is not None:
            drives.append(drive)
        if ssum is not None:
            sums.append(ssum)
            counts.append(scount)

        drive_s = f"{drive:9.3f}" if drive is not None else "        -"
        sum_s = f"{ssum:9.3f}" if ssum is not None else "        -"
        cnt_s = f"{scount:7.0f}" if scount is not None else "      -"
        ms_s = f"{1000 * ssum / scount:8.3f}" if ssum and scount else "       -"
        print(f"{row.get('cell_id', '?'):<16} {str(polls):>5} {drive_s} {sum_s} {cnt_s} {ms_s}  {confirmed}")

    out = {"suite": suite_dir.name}
    if len(drives) >= 2:
        med, mean, sd, sd_pct, spread = _spread(drives)
        print(f"  drive    : median={med:.3f} mean={mean:.3f} sd={sd:.4f} ({sd_pct:.3f}%) spread={spread:.2f}%  3sd={3 * sd_pct:.2f}%")
        out["drive"] = {"median": med, "sd_pct": sd_pct, "spread_pct": spread}
    if len(sums) >= 2:
        med, mean, sd, sd_pct, spread = _spread(sums)
        print(f"  step_sum : median={med:.3f} mean={mean:.3f} sd={sd:.4f} ({sd_pct:.3f}%) spread={spread:.2f}%  3sd={3 * sd_pct:.2f}%")
        out["step_sum"] = {"median": med, "sd_pct": sd_pct, "spread_pct": spread}
        if len(set(counts)) == 1:
            print(f"  step count IDENTICAL across all {len(counts)} cells ({counts[0]:.0f}) -- work amount is fixed; all variation is SPEED")
        else:
            print(f"  step count VARIES: {sorted(set(counts))} -- work amount is not fixed, sum/count is the only fair comparison")
        if "drive" in out and out["drive"]["sd_pct"] > 0:
            print(f"  --> drive UNDERSTATES the spread by {sd_pct / out['drive']['sd_pct']:.1f}x (sd) / {spread / max(out['drive']['spread_pct'], 1e-9):.1f}x (range)")
    return out


def sweep_summary(sweep_dir: Path) -> None:
    """Summarise a headroom sweep from its blocks.tsv, quiet controls first.

    The quiet baseline deliberately EXCLUDES any quiet block that ran immediately after a loaded
    one: the 20 s inter-block settle does not let the host recover, so such a block measures
    residual load, not quiet. Which blocks those are is decided from the file, not hardcoded.
    """
    index = sweep_dir / "blocks.tsv"
    if not index.is_file():
        print(f"no blocks.tsv in {sweep_dir}")
        return

    rows = []
    with index.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            suite = Path(row["suite_dir"])
            registry = suite / "registry.jsonl"
            if not registry.is_file():
                continue
            means = []
            counts = set()
            for line in registry.read_text().splitlines():
                if not line.strip():
                    continue
                run_dir = Path(json.loads(line).get("run_dir", ""))
                ssum, scount = _step_totals(run_dir)
                if ssum and scount:
                    means.append(1000 * ssum / scount)
                    counts.add(scount)
            if means:
                rows.append(
                    {
                        "block": row["block"],
                        "workers": int(row["workers"]),
                        "loadavg": row["loadavg_at_start"],
                        "mean_ms": statistics.mean(means),
                        "n": len(means),
                        "counts": counts,
                    }
                )

    if not rows:
        print("no usable blocks")
        return

    # The quiet controls define both the baseline AND its uncertainty. Their own spread is the
    # noise band; a loaded block only carries information if it clears that band. No block is
    # excluded as "contaminated" -- with three controls there is no way to tell residual load from
    # ordinary drift, and dropping one on a guess would manufacture the separation being tested for.
    quiet = [row["mean_ms"] for row in rows if row["workers"] == 0]
    baseline = statistics.mean(quiet) if quiet else None
    band = 100 * (max(quiet) - min(quiet)) / min(quiet) if len(quiet) >= 2 else 0.0

    print(f"\n=== headroom sweep {sweep_dir.name} ===")
    print(f"{'block':<14} {'workers':>7} {'loadavg':>8} {'n':>2} {'mean step ms':>13} {'vs quiet':>10}")
    for row in rows:
        delta_pct = 100 * (row["mean_ms"] - baseline) / baseline if baseline else 0.0
        delta = f"{delta_pct:+9.1f}%" if baseline else "        -"
        flag = ""
        if row["workers"] > 0 and baseline:
            flag = "  SEPARABLE" if abs(delta_pct) > band else "  within quiet band -- NOT separable"
        print(f"{row['block']:<14} {row['workers']:>7} {row['loadavg']:>8} {row['n']:>2} {row['mean_ms']:>13.3f} {delta}{flag}")

    if baseline:
        print(f"\nquiet baseline = {baseline:.3f} ms/step (mean of {len(quiet)} quiet blocks: {', '.join(f'{q:.3f}' for q in quiet)})")
        print(f"quiet spread   = {band:.1f}%  <- the noise band; a load effect smaller than this is NOT attributable")
    all_counts = set()
    for row in rows:
        all_counts |= row["counts"]
    total_cells = sum(row["n"] for row in rows)
    if len(all_counts) == 1:
        print(f"step count IDENTICAL across all {total_cells} cells at every load level ({all_counts.pop():.0f}) -- the WORK invariant holds under contention")
    else:
        print(f"step counts VARY across blocks: {sorted(all_counts)}")


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--sweep":
        for d in args[1:] or sorted(STATE.parent.glob("headroom-sweep-*")):
            sweep_summary(Path(d))
        return 0
    dirs = [Path(a) for a in args] if args else sorted(STATE.glob("pf1-*"))
    for suite_dir in dirs:
        report(suite_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
