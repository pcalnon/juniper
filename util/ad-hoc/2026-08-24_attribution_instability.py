"""
Characterise the attribution-unstable networks: retrained, or unstable scoring?

Five networks attribute to more than one dataset at different growth stages. The handoff
offered two explanations -- either they were retrained on a second dataset (for which no
other record exists), or attribution is unstable there -- and they leave DIFFERENT
signatures:

  RETRAINED       the score VECTOR changes: one dataset's score climbs materially while
                  another's falls. Usually a wall-clock gap before the change, because a
                  second training run had to be started.

  UNSTABLE        the score vector is essentially constant and only the WINNER moves,
                  because two candidates sit within the gap rule of each other and tiny
                  differences in how far each clears its own floor decide the verdict.
                  Snapshots seconds apart, one continuous run.

The discriminator is therefore the SPREAD of each dataset's score along the trajectory,
read against the gap between the top two candidates. This script prints both, plus the
wall-clock deltas, and re-adjudicates under the shipped two-floor rule to show whether the
instability survives it.

Pure data analysis over the gitignored attribution sidecar: no cascor import, no HDF5
opens, no writes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-24
Status: ad-hoc -- investigation
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: section 3 item 4 of the 2026-08-23 handoff is closed.
Related: notes/JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import snapshot_attribute as sa  # noqa: E402

DEFAULT_SIDECAR = pathlib.Path(
    "/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots/snapshots_attribution.jsonl"
)
UNSTABLE = ("2537e0f0", "846587fb", "17de4973", "1e9e15a8", "5af596ef")
STAMP = re.compile(r"cascor_snapshot_(\d{8})_(\d{6})_")


def parse_time(name: str):
    match = STAMP.search(name or "")
    if not match:
        return None
    return dt.datetime.strptime(match.group(1) + match.group(2), "%Y%m%d%H%M%S")


def load(sidecar: pathlib.Path):
    rows = []
    with sidecar.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def describe(uuid: str, rows, cross, margin, gap, show_all: bool) -> None:
    mine = [r for r in rows if uuid in (r.get("name") or "")]
    mine.sort(key=lambda r: (parse_time(r.get("name")) or dt.datetime.min, int(r.get("hidden_units") or 0)))
    if not mine:
        print(f"{uuid}: no snapshots\n")
        return

    datasets = sorted({k for r in mine for k in (r.get("scores") or {})})
    print("=" * 100)
    print(f"NETWORK {uuid}   snapshots={len(mine)}   datasets scored: {', '.join(datasets)}")
    print("=" * 100)

    first = parse_time(mine[0].get("name"))
    last = parse_time(mine[-1].get("name"))
    if first and last:
        print(f"span: {first:%Y-%m-%d %H:%M:%S} -> {last:%H:%M:%S}   ({(last - first).total_seconds():.0f}s)")

    # Wall-clock gaps: a retrain has to be started, so it shows up as a pause.
    gaps = []
    for prev, cur in zip(mine, mine[1:]):
        a, b = parse_time(prev.get("name")), parse_time(cur.get("name"))
        if a and b:
            gaps.append((b - a).total_seconds())
    if gaps:
        print(f"inter-snapshot gaps: median {sorted(gaps)[len(gaps)//2]:.0f}s   max {max(gaps):.0f}s")

    # Score spread per dataset -- the retrained-vs-unstable discriminator. `peak@` is where
    # along the trajectory each dataset's score is highest, and `decay` is how far it has
    # fallen by the end. SEQUENTIAL training produces ORDERED peaks that each decay afterwards
    # (catastrophic forgetting as training moves on); noise produces neither.
    print("\nscore spread along the trajectory (a RETRAIN moves a dataset's score materially):")
    print(f"  {'dataset':<14} {'min':>7} {'max':>7} {'range':>7} {'peak@':>7} {'final':>7} {'decay':>7}")
    peaks = []
    for name in datasets:
        series = [(i, float(r["scores"][name])) for i, r in enumerate(mine) if name in (r.get("scores") or {})]
        if not series:
            continue
        values = [v for _, v in series]
        peak_index, peak_value = max(series, key=lambda kv: kv[1])
        final = series[-1][1]
        print(
            f"  {name:<14} {min(values):>7.3f} {peak_value:>7.3f} {peak_value-min(values):>7.3f} "
            f"{peak_index:>7} {final:>7.3f} {peak_value-final:>7.3f}"
        )
        peaks.append((peak_index, name, peak_value, peak_value - final))

    # A dataset only counts as a "phase" if it actually got high AND then gave the lead up.
    phases = [(i, n) for i, n, v, d in sorted(peaks) if v >= 0.80 and d >= 0.15]
    if len(phases) >= 2:
        print(f"\n  ** ORDERED PEAK-AND-DECAY across {len(phases)} datasets: " + " -> ".join(n for _, n in phases))
        print("     each rose above 0.80 and then fell back by >=0.15 as the next took over —")
        print("     the signature of SEQUENTIAL training, which noise does not produce.")

    def revise(row):
        scores = {k: float(v) for k, v in (row.get("scores") or {}).items()}
        if not scores:
            return None
        null = {n: {"max": 0.0, "p95": None, "n": 120} for n in scores}
        return sa.adjudicate(scores, null, margin, gap, cross_floor=sa.cross_floor_excluding(cross, row.get("name")))

    changed = [r for r in mine if r.get("verdict") == sa.ATTRIBUTED] if not show_all else mine
    print(f"\ntrajectory ({'all' if show_all else 'attributed only'}); v1 = single floor, v2 = shipped two-floor:")
    header = f"  {'time':<10} {'hid':>4} {'v1':<16} {'v2':<16}"
    header += "".join(f"{d[:8]:>9}" for d in datasets)
    print(header)
    for row in changed:
        stamp = parse_time(row.get("name"))
        cells = "".join(f"{float(row['scores'][d]):>9.3f}" if d in (row.get("scores") or {}) else f"{'-':>9}" for d in datasets)
        new = revise(row)
        v1 = f"{row.get('verdict')}:{row.get('dataset') or '-'}"
        v2 = f"{new['verdict']}:{new['dataset'] or '-'}" if new else "-"
        print(f"  {stamp:%H:%M:%S}   {int(row.get('hidden_units') or 0):>4} {v1:<16} {v2:<16}{cells}")

    # Under the shipped two-floor rule, does the instability survive?
    revised = collections.Counter()
    for row in mine:
        scores = {k: float(v) for k, v in (row.get("scores") or {}).items()}
        if not scores:
            revised["no-scores"] += 1
            continue
        null = {n: {"max": 0.0, "p95": None, "n": 120} for n in scores}
        verdict = sa.adjudicate(scores, null, margin, gap, cross_floor=sa.cross_floor_excluding(cross, row.get("name")))
        revised[f"{verdict['verdict']}:{verdict['dataset']}"] += 1
    print(f"\n  under the SHIPPED two-floor rule: {dict(revised)}")
    distinct = {k.split(':')[1] for k in revised if k.startswith("attributed:")}
    if len(distinct) > 1:
        print(f"  ** still attributes to MORE THAN ONE dataset: {sorted(distinct)}")
    elif distinct:
        print(f"  ** resolves to a single dataset: {sorted(distinct)[0]}")
    else:
        print("  ** no attribution survives; the network becomes indeterminate throughout")
    print()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--sidecar", type=pathlib.Path, default=DEFAULT_SIDECAR)
    parser.add_argument("--uuid", action="append", default=[], help="restrict to these (repeatable); default: all five")
    parser.add_argument("--all-rows", action="store_true", help="print every snapshot, not just the attributed ones")
    parser.add_argument("--margin", type=float, default=sa.DEFAULT_MARGIN)
    parser.add_argument("--gap", type=float, default=sa.DEFAULT_GAP)
    args = parser.parse_args(argv)

    rows = load(args.sidecar)
    cross = sa.build_cross_dataset_floor(rows)
    print(f"sidecar rows: {len(rows)}   cross-dataset floors: " + ", ".join(f"{k}={v['max']:.3f}" for k, v in sorted(cross.items())) + "\n")

    for uuid in args.uuid or UNSTABLE:
        describe(uuid, rows, cross, args.margin, args.gap, args.all_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
