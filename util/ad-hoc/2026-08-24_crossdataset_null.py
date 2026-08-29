"""
Re-adjudicate attributed snapshots against a CROSS-DATASET EMPIRICAL null.

The two synthetic nulls in this series both answer "what does a network with no learned
structure score?" -- one by drawing fresh weights at the initialisation scale, one by
permuting a trained network's own weights. Neither answers the question the archive
actually poses, which is:

    what does a network that WAS trained -- just not on THIS dataset -- score here?

That null needs no simulation at all, because the attribution sidecar already stores every
snapshot's score against every shape-compatible dataset. So for target dataset D, the
reference class is the snapshots confidently attributed to some OTHER dataset: real
networks, at real capacities, carrying real trained weights, that we have positive
evidence were trained on something that is not D.

This is the strictest of the three nulls and the only one built from trained networks.
A score that clears it is evidence about what the snapshot learned; a score that does not
is explained by "a trained network of this size scores about this well on D regardless".

Pure data analysis: reads one gitignored sidecar, imports no cascor, opens no snapshot,
writes nothing.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-24
Status: ad-hoc -- investigation
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the chosen null ships inside util/snapshot_attribute.py.
Related: section 3 item 2 of HANDOFF_2026-08-23_snapshot-retention-and-arc-closeout.md
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

DEFAULT_SIDECAR = pathlib.Path(
    "/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots/snapshots_attribution.jsonl"
)
DEFAULT_MARGIN = 0.05
DEFAULT_GAP = 0.05


def percentile(values, q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    position = q / 100.0 * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def load_attributed(sidecar: pathlib.Path):
    rows = []
    with sidecar.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("verdict") == "attributed" and record.get("scores"):
                rows.append(record)
    return rows


def build_reference_null(rows, target: str, band: int | None, capacity: int | None):
    """Scores on ``target`` from snapshots attributed to some dataset OTHER than target.

    ``band`` optionally restricts the reference class to snapshots whose hidden-unit count
    is within +/- band of ``capacity``, so the floor is capacity-comparable as well as
    trained. Returns the raw sample; the caller picks the statistic.
    """
    sample = []
    for record in rows:
        if record.get("dataset") == target:
            continue
        score = (record.get("scores") or {}).get(target)
        if score is None:
            continue
        if band is not None and capacity is not None:
            if abs(int(record.get("hidden_units") or 0) - capacity) > band:
                continue
        sample.append(float(score))
    return sample


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--sidecar", type=pathlib.Path, default=DEFAULT_SIDECAR)
    parser.add_argument("--margin", type=float, default=DEFAULT_MARGIN)
    parser.add_argument("--gap", type=float, default=DEFAULT_GAP)
    parser.add_argument("--band", type=int, default=None, help="restrict the reference class to +/- this many hidden units")
    parser.add_argument("--statistic", choices=("max", "p95", "p99"), default="max", help="floor statistic (the shipped tool uses max)")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="SUBSTR",
        help="drop snapshots whose name contains SUBSTR from the REFERENCE CLASS (repeatable). "
        "Sensitivity handle: a 'max' floor can rest on a single outlier, and if that outlier is "
        "itself of contested attribution the floor it sets is not trustworthy.",
    )
    parser.add_argument("--json-out", type=pathlib.Path, default=None)
    args = parser.parse_args(argv)

    rows = load_attributed(args.sidecar)
    if args.exclude:
        before = len(rows)
        excluded = [r for r in rows if any(s in (r.get("name") or "") for s in args.exclude)]
        rows = [r for r in rows if not any(s in (r.get("name") or "") for s in args.exclude)]
        print(f"excluded {before - len(rows)} snapshot(s) from BOTH cohort and reference class:", file=sys.stderr)
        for record in excluded:
            print(f"  {record.get('name')} (attributed={record.get('dataset')}, hidden={record.get('hidden_units')})", file=sys.stderr)
    print(f"attributed rows: {len(rows)}\n", file=sys.stderr)

    datasets = sorted({r["dataset"] for r in rows if r.get("dataset")})

    # Global (un-banded) floors, for the summary table.
    print("cross-dataset empirical floors (reference = snapshots attributed elsewhere)\n")
    print(f"{'dataset':<14} {'ref n':>6} {'ref max':>9} {'ref p95':>9} {'old floor':>10}")
    print("-" * 54)
    global_floor = {}
    for dataset in datasets:
        sample = build_reference_null(rows, dataset, None, None)
        if not sample:
            continue
        global_floor[dataset] = {"max": max(sample), "p95": percentile(sample, 95), "p99": percentile(sample, 99), "n": len(sample)}
        old = None
        for record in rows:
            if record.get("dataset") == dataset and record.get("lift") is not None:
                old = round(float(record["scores"][dataset]) - float(record["lift"]), 3)
                break
        print(f"{dataset:<14} {len(sample):>6} {max(sample):>9.3f} {percentile(sample, 95):>9.3f} {old if old is not None else float('nan'):>10.3f}")

    survivors: collections.Counter = collections.Counter()
    lost: collections.Counter = collections.Counter()
    reasons: collections.Counter = collections.Counter()
    detail = []

    for record in rows:
        target = record["dataset"]
        capacity = int(record.get("hidden_units") or 0)
        scores = {k: float(v) for k, v in record["scores"].items()}

        floors = {}
        for name in scores:
            sample = build_reference_null(rows, name, args.band, capacity)
            if not sample:
                floors[name] = 1.0  # no reference class -> cannot be attributed to (conservative)
                continue
            floors[name] = max(sample) if args.statistic == "max" else percentile(sample, 95 if args.statistic == "p95" else 99)

        lifts = {name: scores[name] - floors[name] for name in scores}
        ordered = sorted(lifts.items(), key=lambda kv: -kv[1])
        best, best_lift = ordered[0]
        runner = ordered[1][1] if len(ordered) > 1 else float("-inf")
        separation = best_lift - runner

        if best_lift < args.margin:
            verdict, chosen = "indeterminate", None
            reasons["below floor"] += 1
        elif separation < args.gap:
            verdict, chosen = "ambiguous", None
            reasons["ambiguous"] += 1
        else:
            verdict, chosen = "attributed", best

        if verdict == "attributed" and chosen == target:
            survivors[target] += 1
        else:
            lost[target] += 1
        detail.append(
            {
                "name": record.get("name"),
                "hidden_units": capacity,
                "old_dataset": target,
                "new_verdict": verdict,
                "new_dataset": chosen,
                "new_lift": round(best_lift, 4),
                "floor_used": round(floors.get(target, float("nan")), 4),
                "score_on_target": round(scores.get(target, float("nan")), 4),
            }
        )

    band_note = f"+/-{args.band} hidden units" if args.band is not None else "un-banded"
    print("\n" + "=" * 74)
    print("CROSS-DATASET EMPIRICAL RE-ADJUDICATION")
    print("=" * 74)
    print(f"floor statistic: {args.statistic}   reference class: {band_note}   margin: {args.margin}   gap: {args.gap}\n")
    print(f"{'dataset':<14} {'was':>6} {'survives':>9} {'lost':>6}")
    print("-" * 40)
    for dataset in sorted(set(list(survivors) + list(lost)), key=lambda d: -(survivors[d] + lost[d])):
        print(f"{dataset:<14} {survivors[dataset] + lost[dataset]:>6} {survivors[dataset]:>9} {lost[dataset]:>6}")
    print("-" * 40)
    print(f"{'TOTAL':<14} {sum(survivors.values()) + sum(lost.values()):>6} {sum(survivors.values()):>9} {sum(lost.values()):>6}")

    if args.json_out:
        args.json_out.write_text(json.dumps({"detail": detail, "floors": global_floor}, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
