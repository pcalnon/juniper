#!/usr/bin/env python3
"""Is ``step_count`` deterministic under identical config+seed? Census the whole corpus.

Project: Juniper
Sub-Project: juniper-ml
Application: perf lane (P2 item 1.5 / gate premise)
Author: Paul Calnon
License: MIT

WHY: the work gate compares ``step_count`` EXACTLY, on the premise that it is deterministic for a
seed-fixed config. Adversarial validation (2026-09-04) produced a counterexample -- identical
``config_sha256``, identical seeds, all ``succeeded``, and step_count 6496 / 6095 / 6496. This
settles the question over the whole corpus rather than one cell, and tests whether requiring
``completion_reason`` to MATCH would remove the divergences.

Usage:  python3 util/ad-hoc/2026-09-04_step_count_determinism_census.py
"""

from __future__ import annotations

import collections
import csv
import json
import pathlib

STATE = pathlib.Path.home() / ".local/state/juniper-experiments"
COUNT_COL = "juniper_cascor_training_step_duration_seconds_count"


def step_count(run_dir: pathlib.Path):
    series = run_dir / "artifacts/results/metrics_series.csv"
    if not series.is_file():
        return None
    try:
        with series.open(encoding="utf-8", newline="") as handle:
            rows = [r for r in csv.DictReader(handle) if r.get(COUNT_COL)]
    except OSError:
        return None
    try:
        return float(rows[-1][COUNT_COL]) if rows else None
    except (ValueError, KeyError):
        return None


def main() -> int:
    runs = []
    for manifest_path in sorted(STATE.glob("*/manifest.json")):
        try:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cfg = m.get("config_sha256")
        if not cfg:
            continue
        count = step_count(manifest_path.parent)
        if count is None:
            continue
        runs.append(
            {
                "run": manifest_path.parent.name,
                "cfg": cfg,
                "count": count,
                "reason": m.get("completion_reason"),
                "outcome": m.get("outcome"),
                "seeds": json.dumps(m.get("seeds"), sort_keys=True),
            }
        )

    by_cfg = collections.defaultdict(list)
    for r in runs:
        by_cfg[r["cfg"]].append(r)
    repeated = {c: v for c, v in by_cfg.items() if len(v) > 1}

    diverged = {c: v for c, v in repeated.items() if len({r["count"] for r in v}) > 1}

    print(f"runs with a config_sha256 and a step_count : {len(runs)}")
    print(f"distinct configs                           : {len(by_cfg)}")
    print(f"configs seen more than once                : {len(repeated)}")
    print(f"  of those, DIVERGENT step_count           : {len(diverged)}")
    print()

    # Does requiring completion_reason to match remove the divergence? If every divergent config
    # becomes invariant once grouped by (cfg, reason), then reason is the discriminator and a
    # comparator that also matches on it would never emit the false FAIL.
    still_divergent, explained = [], []
    for cfg, group in diverged.items():
        by_reason = collections.defaultdict(set)
        for r in group:
            by_reason[r["reason"]].add(r["count"])
        if all(len(counts) == 1 for counts in by_reason.values()):
            explained.append((cfg, {k: sorted(v)[0] for k, v in by_reason.items()}))
        else:
            still_divergent.append((cfg, dict(by_reason)))

    print(f"divergent configs EXPLAINED by completion_reason : {len(explained)}")
    print(f"divergent configs STILL divergent within a reason: {len(still_divergent)}")
    print()

    if still_divergent:
        print("--- STILL DIVERGENT within one completion_reason (a reason guard would NOT fix these):")
        for cfg, by_reason in still_divergent[:10]:
            detail = "; ".join(f"{k}={sorted(v)}" for k, v in by_reason.items())
            print(f"  {cfg[:12]}  {detail}")
        print()

    print("--- reason distribution over ALL runs counted:")
    for reason, n in collections.Counter(r["reason"] for r in runs).most_common():
        print(f"  {str(reason):<20} {n}")

    # Terminal states whose step_count is truncated by construction: the histogram stops when the
    # driver stops, so these are never a fair comparison regardless of config identity.
    print()
    unsafe = {"timed_out", "torn_down_early", "stalled"}
    n_unsafe = sum(1 for r in runs if r["reason"] in unsafe)
    print(f"runs whose reason implies a TRUNCATED histogram ({'/'.join(sorted(unsafe))}): {n_unsafe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
