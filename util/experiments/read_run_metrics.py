#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   experiments
# File Name:     read_run_metrics.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Canonical reader for the perf lane's two RATIFIED gate inputs (P2 item 0.4). Promoted from
#   util/ad-hoc/2026-09-02_pf1_drive_extract.py, which produced the P3 measurements.
#
#   Two traps sit between a reader and a run's real numbers, and this module exists so neither has
#   to be re-discovered:
#
#   1. `aggregate.csv` carries `wall_seconds` ONLY, and the lane DE-RATIFIED `wall_seconds` -- it
#      absorbs plot rendering and stack bring-up. Anyone who opens the aggregate is analysing the
#      wrong quantity with nothing flagging it.
#   2. `timings.drive` is QUANTIZED to the driver's status-poll interval (DEFAULT_POLL_INTERVAL =
#      5.0 in run_experiment.py; the drive loop breaks only on a poll), so
#      drive ~= (polls - 1) * 5.0 + HTTP overhead. Measured 2026-09-02: at 20 s cells it UNDERSTATED
#      real spread by 25x-182x, and at a poll boundary it OVERSTATED by 5x. It is not a conservative
#      approximation in either direction, so it cannot even serve as an upper bound on noise.
#
#   The resolving instrument is the cascor step-duration histogram, sampled DIRECTLY from the
#   service by the driver's own poll loop into artifacts/results/metrics_series.csv. It is
#   poll-independent AND Prometheus-independent: a run reporting `scrape_confirmed: false` still
#   carries a complete histogram, because that flag describes the PROMETHEUS scrape, not the data.
#
#   THE GATE IS SPLIT (owner decision, 2026-09-02), and these are its two halves:
#     * WORK  -- step_count. Deterministic for a seed-fixed config, and CONTENTION-IMMUNE: measured
#                identical across 21 cells spanning a 3x range of step duration. Gateable exactly --
#                but the determinism holds only WITHIN a termination branch (completion_reason).
#                Corpus census 2026-09-04: 29 of 79 repeated configs diverge across branches, zero
#                within one. Comparing across branches is what produced the ml#1710 false FAIL.
#     * SPEED -- mean_step_seconds (= step_sum / step_count). Carries a 13-20.5% host drift floor
#                and is NOT gated; it is reported.
#####################################################################################################################################################################################################
"""Read the ratified perf metrics for a run, a suite, or a headroom sweep.

Usage:
    python util/experiments/read_run_metrics.py SUITE_DIR [SUITE_DIR ...]
    python util/experiments/read_run_metrics.py --run RUN_DIR
    python util/experiments/read_run_metrics.py --sweep SWEEP_DIR
    python util/experiments/read_run_metrics.py SUITE_DIR --json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml

STEP_SUM_COLUMN = "juniper_cascor_training_step_duration_seconds_sum"
STEP_COUNT_COLUMN = "juniper_cascor_training_step_duration_seconds_count"

SERIES_RELPATH = "artifacts/results/metrics_series.csv"
MANIFEST_RELPATH = "manifest.json"

# Terminal states that stop the DRIVER rather than the workload, so the step-duration histogram is
# cut short and its count measures the budget, not the code. Never gate on one.
TRUNCATING_TERMINATIONS = frozenset({"timed_out", "torn_down_early", "stalled"})


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def step_totals(run_dir: Path) -> Tuple[Optional[float], Optional[float]]:
    """Final ``(sum, count)`` of the step-duration histogram, or ``(None, None)``.

    Read from the LAST sampled row that carries the pair. The drive loop samples ``/metrics``
    BEFORE it tests for termination (run_experiment.py: poll -> sample -> write row -> break on
    terminal FSM), so the final row is always taken after training completed. That is what makes
    the count exact rather than approximately exact, and therefore safe to gate at zero tolerance.
    """
    series = run_dir / SERIES_RELPATH
    if not series.is_file():
        return None, None
    try:
        with series.open(encoding="utf-8", newline="") as handle:
            rows = [row for row in csv.DictReader(handle) if row.get(STEP_SUM_COLUMN)]
    except OSError:
        return None, None
    if not rows:
        return None, None
    last = rows[-1]
    try:
        return float(last[STEP_SUM_COLUMN]), float(last[STEP_COUNT_COLUMN])
    except (TypeError, ValueError, KeyError):
        return None, None


def _recurrence_fields(run_dir: Path, timings: Mapping[str, Any]) -> Dict[str, Any]:
    """Speed and the (absent) work counter for a recurrence run.

    RECURRENCE HAS NO WORK COUNTER, and that is a finding rather than an omission here.
    Surveyed across 36 runs on 2026-09-04:

    * ``n_epochs`` takes exactly TWO values -- 1 (28 runs, "converged") and 200 (2 runs,
      "max_epochs") -- because it tracks the READOUT TYPE: closed-form readouts converge in one
      epoch. It is invariant to ``d`` and ``n_steps``, the two dimensions PF-5 and PF-6 exist to
      vary, so gating on it would be VACUOUS exactly where it is needed.
    * ``dataset.n_windows`` does vary (349 / 1346 / 1574 / 3149) but is INPUT SIZE, fixed by the
      config. A code change that does redundant work does not move it. cascor's ``step_count``
      measures work DONE; this measures work ASKED FOR.

    So the split gate's WORK half has no recurrence equivalent, and a recurrence run can be
    reported but not gated. ``work_countable`` says so explicitly so callers refuse rather than
    quietly compare something that cannot regress.
    """
    train = _load_json(run_dir / "artifacts/results/train_response.json")
    dataset = train.get("dataset") or {}
    return {
        "kind": "recurrence",
        "work_countable": False,
        "work_uncountable_reason": "recurrence exposes no work-done counter: n_epochs is 1-or-200 by readout type and invariant to d/n_steps; n_windows is input size, fixed by config",
        "train_seconds": timings.get("train"),
        "crossval_seconds": timings.get("crossval"),
        "n_epochs": train.get("n_epochs"),
        "stopped_reason": train.get("stopped_reason"),
        "n_windows": dataset.get("n_windows"),
    }


def read_run(run_dir: Path) -> Dict[str, Any]:
    """Both gate inputs plus provenance for one run directory.

    Handles both apps. cascor yields a countable ``step_count``; recurrence does not (see
    ``_recurrence_fields``), and says so via ``work_countable`` rather than reporting a zero or a
    ``None`` a caller might read as "matches".
    """
    run_dir = Path(run_dir)
    manifest = _load_json(run_dir / MANIFEST_RELPATH)
    timings = manifest.get("timings") or {}
    drive_loop = manifest.get("drive_loop") or {}
    scraped = manifest.get("metrics_scraped")
    # Tri-state (ml#1550): True scraped, False did not, None == COULD NOT ASK (Prometheus
    # unreachable). Never collapse None into False -- that is the false-negative the tri-state
    # replaced.
    confirmed = scraped.get("scrape_confirmed") if isinstance(scraped, dict) else None
    step_sum, step_count = step_totals(run_dir)
    row: Dict[str, Any] = {
        "run_dir": str(run_dir),
        "run_id": manifest.get("run_id"),
        "outcome": manifest.get("outcome"),
        "kind": "cascor",
        "work_countable": True,
        # TERMINATION BRANCH -- part of the comparison precondition, not decoration.
        #
        # `step_count` is deterministic for a seed-fixed config ONLY GIVEN the branch that ended
        # training. Censused over the whole corpus 2026-09-04
        # (util/ad-hoc/2026-09-04_step_count_determinism_census.py): 333 runs, 153 distinct configs,
        # 79 repeated, of which **29 diverge in step_count** -- and **all 29 are fully explained by
        # completion_reason**, with ZERO still divergent once grouped by it.
        #
        # So a differing reason means a different trajectory, and comparing across it produces a
        # FALSE FAIL. The observed case: identical config_sha256 and seeds gave 6496
        # (early_stopped) / 6095 (below_threshold) / 6496 (early_stopped).
        "completion_reason": manifest.get("completion_reason"),
        "drive_seconds": timings.get("drive"),
        "polls": drive_loop.get("polls"),
        "step_sum_seconds": step_sum,
        "step_count": step_count,
        "mean_step_seconds": (step_sum / step_count) if step_sum is not None and step_count else None,
        "scrape_confirmed": confirmed,
    }
    # `drive` identifies a cascor run (a polled training loop); `train` identifies recurrence,
    # whose POST /v1/train is SYNCHRONOUS -- the response IS completion, so there is no poll loop
    # and its duration carries none of `drive`'s 5 s quantization.
    if "drive" not in timings and "train" in timings:
        row.update(_recurrence_fields(run_dir, timings))
    return row


# Fields that identify a cell to a HUMAN but do not affect the computation. Stripping them is what
# turns a per-cell hash into a WORKLOAD identity. `experiment.seed` is deliberately NOT here: it
# changes the computation and two runs at different seeds are different workloads.
COSMETIC_EXPERIMENT_KEYS = ("description", "name")


def workload_fingerprint(suite_dir: Path, cell_id: str) -> Optional[str]:
    """Identity of the WORKLOAD a cell ran, stable across repeats of it.

    Why not ``registry.jsonl``'s ``config_sha256``: that hashes the whole materialised cell YAML,
    including ``experiment.description``. PF-1's five repeats differ only by "repeat 1".."repeat 5",
    so their ``config_sha256`` values are all DIFFERENT -- using it as a "same workload" test would
    refuse every legitimate comparison, including a suite against its own baseline.

    This hashes the same YAML with the cosmetic keys removed. Measured 2026-09-03: identical across
    all five PF-1 repeats, and different between the pre- and post-cascor#618 workloads (which set
    ``output_epochs`` and re-calibrated the epoch budget) -- so it detects the "figures before and
    after are not comparable" boundary mechanically instead of by memory.
    """
    cell_yaml = Path(suite_dir) / "cells" / cell_id / "experiment.yaml"
    if not cell_yaml.is_file():
        return None
    try:
        config = yaml.safe_load(cell_yaml.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None  # unreadable cell -> "unknown identity", which callers must treat as a refusal
    if not isinstance(config, dict):
        return None
    experiment = config.get("experiment")
    if isinstance(experiment, dict):
        for key in COSMETIC_EXPERIMENT_KEYS:
            experiment.pop(key, None)
    try:
        blob = json.dumps(config, sort_keys=True)
    except (TypeError, ValueError):
        # `safe_load` produces four types `json.dumps` refuses -- date, datetime, bytes,
        # set -- plus three shapes no `default=` can rescue, because `default=` is consulted
        # for VALUES only: a non-str mapping key, mixed-type keys under `sort_keys=True`
        # (`< not supported between str and int`), and a recursive anchor (`ValueError:
        # Circular reference detected`, which `safe_load` builds happily).
        #
        # The tempting repair is `default=str`. It is WRONG here, and measurably so:
        # `str()` of a set embeds Python's randomised string hash, so one config yields a
        # DIFFERENT fingerprint in every process. `compare_baseline` matches the persisted
        # fingerprint by exact string, and baselines are never rewritten -- so that turns a
        # loud crash into "different workload, so this is an INVALID comparison", blaming a
        # config that never changed. `str()` on a tz-aware datetime is additionally
        # PyYAML-version-dependent (3.13 normalised to naive UTC, 6.x keeps the offset), and
        # no PyYAML floor is declared for this tooling.
        #
        # An unhashable config is genuinely an UNKNOWN identity, so say so. Callers already
        # treat None as a refusal -- and `summarise` counts unknowns rather than filtering
        # them, so one bad cell cannot be dropped into a vacuous "single workload".
        return None
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def read_suite(suite_dir: Path) -> List[Dict[str, Any]]:
    """One row per cell, in registry order. Empty list when the registry is absent."""
    registry = Path(suite_dir) / "registry.jsonl"
    if not registry.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    for line in registry.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        row = read_run(Path(entry.get("run_dir", "")))
        row["cell_id"] = entry.get("cell_id")
        row["overrides"] = entry.get("overrides")
        row["grafana_bridge"] = entry.get("grafana_bridge")
        row["config_sha256"] = entry.get("config_sha256")
        row["workload_fingerprint"] = workload_fingerprint(Path(suite_dir), str(entry.get("cell_id"))) if entry.get("cell_id") else None
        rows.append(row)
    return rows


def _spread(values: Sequence[float]) -> Dict[str, float]:
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if len(values) >= 2 else 0.0
    return {
        "n": len(values),
        "median": statistics.median(values),
        "mean": mean,
        "sd": sd,
        "sd_pct": (100 * sd / mean) if mean else 0.0,
        "min": min(values),
        "max": max(values),
        "spread_pct": (100 * (max(values) - min(values)) / min(values)) if min(values) else 0.0,
    }


def summarise(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Aggregate a suite's rows into the two gate halves.

    ``work_invariant`` is the load-bearing field: True when every cell reports the SAME
    ``step_count``. A suite of repeats that fails it is not a set of repeats.
    """
    drives = [r["drive_seconds"] for r in rows if isinstance(r.get("drive_seconds"), (int, float))]
    sums = [r["step_sum_seconds"] for r in rows if isinstance(r.get("step_sum_seconds"), (int, float))]
    counts = [r["step_count"] for r in rows if isinstance(r.get("step_count"), (int, float))]
    means = [r["mean_step_seconds"] for r in rows if isinstance(r.get("mean_step_seconds"), (int, float))]

    fingerprints = sorted({r["workload_fingerprint"] for r in rows if r.get("workload_fingerprint")})
    identified = sum(1 for r in rows if r.get("workload_fingerprint"))
    # A suite whose runs expose no work counter cannot satisfy the work invariant -- not because it
    # failed, but because the question does not apply. Kept as a THIRD state so a caller never reads
    # "not countable" as "counted, and they matched".
    countable = all(r.get("work_countable", True) for r in rows) if rows else False
    # DO NOT filter out null reasons before taking uniqueness. The first version of this line was
    # `... for r in rows if r.get("completion_reason")`, which dropped unknown-branch cells and made
    # `4x early_stopped + 1x None` read as a SINGLE branch -- fail-open on exactly the mixed case the
    # guard exists for. Unknown is a distinct value, and `has_unknown_reason` below makes an all-
    # unknown suite refuse too rather than look uniform.
    reasons = sorted({str(r.get("completion_reason")) for r in rows}) if rows else []
    has_unknown_reason = any(not r.get("completion_reason") for r in rows)
    out: Dict[str, Any] = {
        "cells": len(rows),
        "kinds": sorted({str(r.get("kind", "cascor")) for r in rows}),
        "work_countable": countable,
        # Cells that ended on DIFFERENT branches are not repeats of each other, even at one config.
        "completion_reasons": reasons,
        "has_unknown_completion_reason": has_unknown_reason,
        "single_completion_reason": len(reasons) == 1 and not has_unknown_reason,
        # These end the run before the workload does, so the histogram is truncated by construction
        # and its count is a fact about the budget rather than about the code.
        # READ `outcome`, NOT `completion_reason`. The first version matched these against
        # `completion_reason` and could therefore NEVER FIRE: across 370 manifests
        # `completion_reason` is only {early_stopped, no_candidate, below_threshold, max_iterations,
        # None}, while timed_out / torn_down_early / stalled are `outcome` values -- and all 15
        # driver-stopped runs carry `completion_reason=None`. The accompanying test passed only
        # because its fixture wrote the string into the reason field, which production never does.
        "truncated_terminations": sorted({str(r.get("outcome")) for r in rows if r.get("outcome") in TRUNCATING_TERMINATIONS}),
        "step_counts": sorted(set(counts)),
        # `len(counts) == len(rows)` is load-bearing: `counts` keeps only cells whose step_count
        # is numeric, so without it the invariant is a statement about the cells that ANSWERED
        # rather than about the suite. Measured on `main` before this line: two cells, one with
        # no step_count, reported `step_counts=[100]` and `work_invariant=True`.
        "work_invariant": countable and len(counts) == len(rows) and len(set(counts)) == 1 and bool(counts),
        # A suite whose cells ran DIFFERENT workloads is not a set of repeats either, and its
        # step_count spread would be a fact about the configs rather than about the host or the
        # code. Recorded separately from work_invariant so the two failures stay distinguishable.
        "workload_fingerprints": fingerprints,
        # `identified == len(rows)` is the same guard for identity. `fingerprints` DROPS cells with
        # no fingerprint, so `len(fingerprints) == 1` alone reads True for "one known + one
        # unknown" -- the exact fail-open the `reasons` comment above warns about, left in place on
        # the sibling field. Measured on `main` before this line: True.
        "single_workload": identified == len(rows) and len(fingerprints) == 1,
    }
    if drives:
        out["drive"] = _spread(drives)
    if sums:
        out["step_sum"] = _spread(sums)
    if means:
        out["mean_step"] = _spread(means)
    if drives and sums and out["drive"]["sd_pct"]:
        out["drive_sd_ratio"] = out["step_sum"]["sd_pct"] / out["drive"]["sd_pct"]
    return out


def _fmt(value: Any, spec: str = "9.3f") -> str:
    return format(value, spec) if isinstance(value, (int, float)) else " " * int(spec.split(".")[0])


def render(suite_dir: Path, rows: Sequence[Mapping[str, Any]], summary: Mapping[str, Any]) -> str:
    lines = [f"\n=== {Path(suite_dir).name}  ({summary['cells']} cells) ==="]
    lines.append(f"{'cell':<16} {'polls':>5} {'drive':>9} {'step_sum':>9} {'steps':>7} {'mean_ms':>8}  scrape")
    for row in rows:
        mean_ms = row.get("mean_step_seconds")
        lines.append(
            f"{str(row.get('cell_id') or '?'):<16} {str(row.get('polls')):>5} "
            f"{_fmt(row.get('drive_seconds'))} {_fmt(row.get('step_sum_seconds'))} "
            f"{_fmt(row.get('step_count'), '7.0f')} "
            f"{_fmt(mean_ms * 1000 if isinstance(mean_ms, float) else None, '8.3f')}  {row.get('scrape_confirmed')}"
        )
    for key, label in (("drive", "drive   "), ("step_sum", "step_sum")):
        block = summary.get(key)
        if block:
            lines.append(
                f"  {label}: median={block['median']:.3f} mean={block['mean']:.3f} "
                f"sd={block['sd']:.4f} ({block['sd_pct']:.3f}%) spread={block['spread_pct']:.2f}%"
            )
    if summary["work_invariant"]:
        lines.append(f"  WORK INVARIANT HOLDS -- step_count identical across all {summary['cells']} cells ({summary['step_counts'][0]:.0f})")
    elif summary["step_counts"]:
        lines.append(f"  WORK INVARIANT BROKEN -- step_counts differ: {[int(c) for c in summary['step_counts']]}")
    ratio = summary.get("drive_sd_ratio")
    if ratio is not None:
        verb = "UNDERSTATES" if ratio >= 1 else "OVERSTATES"
        shown = ratio if ratio >= 1 else (1 / ratio if ratio else 0)
        lines.append(f"  drive {verb} the real spread by {shown:.1f}x")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Read the ratified perf metrics for runs and suites.")
    parser.add_argument("suite_dirs", nargs="*", help="suite directories (containing registry.jsonl)")
    parser.add_argument("--run", action="append", default=[], help="a single RUN_DIR (repeatable)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of the table")
    args = parser.parse_args(argv)

    if not args.suite_dirs and not args.run:
        parser.error("give at least one SUITE_DIR or --run RUN_DIR")

    payload: Dict[str, Any] = {"runs": [], "suites": []}
    for run_dir in args.run:
        payload["runs"].append(read_run(Path(run_dir)))
    for suite_dir in args.suite_dirs:
        rows = read_suite(Path(suite_dir))
        payload["suites"].append({"suite_dir": str(suite_dir), "rows": rows, "summary": summarise(rows)})

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for run in payload["runs"]:
        print(json.dumps(run, indent=2, sort_keys=True))
    for suite in payload["suites"]:
        if not suite["rows"]:
            print(f"\n=== {Path(suite['suite_dir']).name}: no registry.jsonl ===")
            continue
        print(render(Path(suite["suite_dir"]), suite["rows"], suite["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
