"""
Profile the architectures of the attributed snapshot cohort.

Answers "how many capacity-matched nulls would we have to build, and over what
capacity range?" before any are built. The existing null in
``util/snapshot_attribute.py`` is keyed on ``(input_size, output_size)`` alone and
is always constructed with ZERO hidden units, so it is the correct floor only for
the zero-node majority and is too lenient for every grown network.

Reads only the gitignored attribution sidecar. No cascor import, no HDF5 opens,
no writes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-24
Status: ad-hoc -- one-off (investigation)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the capacity-matched null ships in util/snapshot_attribute.py.
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


def _print_implied_floors(rows) -> int:
    """The floor each attribution was judged against, recovered as ``score - lift``.

    This is the number the capacity-matched null has to beat. Every one of these was
    produced by a network with ZERO hidden units, against snapshots that have 1..103.
    """
    floors: dict[str, set] = collections.defaultdict(set)
    for record in rows:
        dataset = record.get("dataset")
        lift = record.get("lift")
        score = (record.get("scores") or {}).get(dataset)
        if dataset is None or lift is None or score is None:
            continue
        floors[dataset].add(round(float(score) - float(lift), 4))

    print("zero-hidden-unit floor actually used, recovered as score - lift\n")
    print(f"{'dataset':<14} {'floor(s)':<28} {'distinct':>9}")
    print("-" * 54)
    for dataset in sorted(floors):
        values = sorted(floors[dataset])
        shown = ", ".join(f"{v:.3f}" for v in values[:4])
        if len(values) > 4:
            shown += ", ..."
        print(f"{dataset:<14} {shown:<28} {len(values):>9}")
    return 0


def _print_curve(rows, dataset: str) -> int:
    """Raw score on ``dataset`` against hidden-unit count, for rows attributed to it.

    The point of the plot is the SHAPE, not the level. A floor that is too low inflates
    every score by roughly the same amount, so it shifts the curve without bending it;
    a rising curve therefore survives a floor correction, while a flat cluster sitting
    just above the floor does not.
    """
    points = []
    for record in rows:
        if record.get("dataset") != dataset:
            continue
        score = (record.get("scores") or {}).get(dataset)
        if score is None:
            continue
        points.append((int(record.get("hidden_units") or 0), float(score)))

    if not points:
        print(f"no rows attributed to {dataset!r} with a recorded score")
        return 0

    points.sort()
    print(f"score on {dataset!r} vs capacity  (n={len(points)})\n")
    print(f"{'hidden':>7}  {'score':>7}  {'':<52}")
    print("-" * 70)
    for hidden, score in points:
        bar_start = max(0, min(50, int((score - 0.5) * 100)))
        bar = " " * bar_start + "#"
        print(f"{hidden:>7}  {score:>7.3f}  {bar:<52}")

    lo = [s for h, s in points if h <= 10]
    hi = [s for h, s in points if h >= 50]
    print("-" * 70)
    if lo and hi:
        print(f"mean score at <=10 hidden units: {sum(lo)/len(lo):.3f}  (n={len(lo)})")
        print(f"mean score at >=50 hidden units: {sum(hi)/len(hi):.3f}  (n={len(hi)})")
        print(f"capacity effect: {sum(hi)/len(hi) - sum(lo)/len(lo):+.3f}")
    else:
        print("not enough spread in capacity to compare low vs high")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--sidecar", type=pathlib.Path, default=DEFAULT_SIDECAR)
    parser.add_argument("--verdict", default="attributed", help="cohort to profile")
    parser.add_argument(
        "--floors",
        action="store_true",
        help="recover the ZERO-HIDDEN-UNIT floor each attribution was actually judged against, "
        "as floor = score - lift. Exact, and free: no null is rebuilt.",
    )
    parser.add_argument(
        "--curve",
        metavar="DATASET",
        default=None,
        help="instead of the profile, print raw score vs hidden-unit count for this dataset. "
        "A score that RISES monotonically with capacity is a learning curve, which a "
        "scoring artifact does not produce -- the independent ground the xor cluster is "
        "claimed to survive on.",
    )
    args = parser.parse_args(argv)

    if not args.sidecar.is_file():
        print(f"sidecar not found: {args.sidecar}", file=sys.stderr)
        return 1

    rows = []
    with args.sidecar.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("verdict") == args.verdict:
                rows.append(record)

    if not rows:
        print(f"no rows with verdict={args.verdict!r}")
        return 0

    if args.curve:
        return _print_curve(rows, args.curve)

    if args.floors:
        return _print_implied_floors(rows)

    by_dataset: collections.Counter[str] = collections.Counter()
    by_arch: collections.Counter[tuple] = collections.Counter()
    hidden_by_dataset: dict[str, list[int]] = collections.defaultdict(list)
    lift_by_dataset: dict[str, list[float]] = collections.defaultdict(list)

    for record in rows:
        dataset = record.get("dataset") or "<none>"
        hidden = int(record.get("hidden_units") or 0)
        shape = tuple(record.get("shape") or ())
        by_dataset[dataset] += 1
        by_arch[(shape, hidden)] += 1
        hidden_by_dataset[dataset].append(hidden)
        if record.get("lift") is not None:
            lift_by_dataset[dataset].append(float(record["lift"]))

    print(f"cohort: verdict={args.verdict!r}  n={len(rows)}\n")

    print(f"{'dataset':<14} {'n':>5} {'hidden min':>11} {'hidden max':>11} {'hidden med':>11} {'lift min':>9} {'lift med':>9}")
    print("-" * 78)
    for dataset, n in by_dataset.most_common():
        hidden = sorted(hidden_by_dataset[dataset])
        lifts = sorted(lift_by_dataset[dataset])
        med_h = hidden[len(hidden) // 2]
        med_l = lifts[len(lifts) // 2] if lifts else float("nan")
        min_l = lifts[0] if lifts else float("nan")
        print(f"{dataset:<14} {n:>5} {hidden[0]:>11} {hidden[-1]:>11} {med_h:>11} {min_l:>9.3f} {med_l:>9.3f}")

    print(f"\ndistinct (shape, hidden_units) architectures needing a null: {len(by_arch)}")
    all_hidden = sorted(h for _, h in by_arch)
    print(f"hidden-unit range across the cohort: {all_hidden[0]} .. {all_hidden[-1]}")
    zero = sum(n for (_, h), n in by_arch.items() if h == 0)
    print(f"rows whose CURRENT null is already capacity-correct (hidden_units == 0): {zero} / {len(rows)}")

    print("\nmost common architectures:")
    for (shape, hidden), n in by_arch.most_common(12):
        print(f"  shape={shape} hidden={hidden:<4} n={n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
