"""
Re-adjudicate attributed snapshots against a WEIGHT-PERMUTATION null.

The companion script ``2026-08-24_capacity_matched_null.py`` fixes the capacity defect
by drawing fresh random weights at the initialisation scale. That is a strict improvement
over the zero-hidden-unit null, but it still assumes a *scale*: trained weights grow, and
small weights hold a sigmoid in its near-linear regime, which produces simpler decision
boundaries than a trained network of the same architecture. A null that is too smooth is
too lenient, and lenient is the direction that manufactures attributions.

This null removes that assumption. For each snapshot it permutes the entries WITHIN each
parameter tensor. Capacity, weight scale, and the exact weight multiset are all preserved
by construction; the only thing destroyed is the ARRANGEMENT of the weights -- which is
precisely what training produces. If a snapshot's score survives a floor built this way,
the score is evidence about what it learned rather than about how big its weights are.

Read-only: opens each snapshot, never writes one. ``JUNIPER_CASCOR_SNAPSHOTS_DIR`` is
redirected before any cascor import so probing cannot grow the archive being measured.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-24
Status: ad-hoc -- investigation
Retire when: the chosen null ships inside util/snapshot_attribute.py.
Related: section 3 item 2 of HANDOFF_2026-08-23_snapshot-retention-and-arc-closeout.md
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import sys
import tempfile

_PROBE_SNAPSHOT_DIR = pathlib.Path(tempfile.mkdtemp(prefix="permnull-probe-"))
os.environ["JUNIPER_CASCOR_SNAPSHOTS_DIR"] = str(_PROBE_SNAPSHOT_DIR)
os.environ.setdefault("CASCOR_NUM_PROCESSES", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import snapshot_attribute as sa  # noqa: E402 - deliberate: env must be set before this import chain

DEFAULT_SIDECAR = pathlib.Path(
    "/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots/snapshots_attribution.jsonl"
)


def _permute_tensor(tensor, torch):
    """Shuffle a tensor's entries in place-equivalent fashion, preserving its multiset."""
    flat = tensor.detach().reshape(-1)
    order = torch.randperm(flat.numel())
    return flat[order].reshape(tensor.shape).clone()


def permutation_null_for(network, datasets, size, torch, seed_base):
    """Score ``size`` weight-permuted clones of ``network``.

    The clone shares the architecture and the exact weight multiset; only the arrangement
    differs. Returns the {dataset: {p50,p95,max,n}} shape ``adjudicate`` expects.
    """
    original_units = [(unit, unit["weights"], unit["bias"]) for unit in network.hidden_units]
    original_ow = network.output_weights
    original_ob = network.output_bias

    samples = {name: [] for name in datasets}
    try:
        for offset in range(size):
            torch.manual_seed(seed_base + offset)
            for unit, weights, bias in original_units:
                unit["weights"] = _permute_tensor(weights, torch)
                unit["bias"] = _permute_tensor(bias, torch)
            network.output_weights = _permute_tensor(original_ow, torch)
            network.output_bias = _permute_tensor(original_ob, torch)
            for name, scored in sa.score_network(network, datasets, torch).items():
                samples[name].append(scored)
    finally:
        # Restore, so the in-memory network still matches the file it came from.
        for unit, weights, bias in original_units:
            unit["weights"] = weights
            unit["bias"] = bias
        network.output_weights = original_ow
        network.output_bias = original_ob

    built = {}
    for name, values in samples.items():
        if values:
            built[name] = {"p50": sa.percentile(values, 50), "p95": sa.percentile(values, 95), "max": max(values), "n": len(values)}
        else:
            built[name] = {"p50": None, "p95": None, "max": None, "n": 0}
    return built


def load_rows(sidecar: pathlib.Path, verdicts):
    rows = []
    with sidecar.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("verdict") in verdicts and record.get("scores"):
                rows.append(record)
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--sidecar", type=pathlib.Path, default=DEFAULT_SIDECAR)
    parser.add_argument("--null-size", type=int, default=120, help="weight permutations per snapshot")
    parser.add_argument("--margin", type=float, default=sa.DEFAULT_MARGIN)
    parser.add_argument("--gap", type=float, default=sa.DEFAULT_GAP)
    parser.add_argument("--cascor-src", type=pathlib.Path, default=None)
    parser.add_argument("--data-root", type=pathlib.Path, default=None)
    parser.add_argument("--seed", type=int, default=20260824)
    parser.add_argument("--verdicts", default="attributed")
    parser.add_argument("--limit", type=int, default=None, help="only the first N snapshots (smoke test)")
    parser.add_argument("--json-out", type=pathlib.Path, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    cascor_src = args.cascor_src or sa.default_cascor_src()
    data_root = args.data_root or sa.default_data_root()
    verdicts = tuple(v.strip() for v in args.verdicts.split(",") if v.strip())

    datasets = sa.load_datasets(data_root)
    print(f"datasets loaded: {', '.join(sorted(datasets))}", file=sys.stderr)

    rows = load_rows(args.sidecar, verdicts)
    if args.limit:
        rows = rows[: args.limit]
    print(f"snapshots to re-adjudicate: {len(rows)}", file=sys.stderr)

    sys.path.insert(0, str(cascor_src))
    import torch

    from snapshots.snapshot_serializer import CascadeHDF5Serializer

    serializer = CascadeHDF5Serializer()

    survivors: collections.Counter = collections.Counter()
    lost: collections.Counter = collections.Counter()
    unloadable = 0
    transitions: collections.Counter = collections.Counter()
    detail = []

    with sa._muffle_stdout(not args.verbose):
        for index, record in enumerate(rows, start=1):
            path = record.get("path")
            old_dataset = record.get("dataset")
            try:
                network = serializer.load_network(str(path), restore_multiprocessing=False)
            except Exception:  # noqa: BLE001 - an unloadable snapshot is a finding, not a crash
                network = None
            if network is None:
                unloadable += 1
                continue

            null = permutation_null_for(network, datasets, args.null_size, torch, seed_base=args.seed + index * 1000)
            scores = {k: float(v) for k, v in (record.get("scores") or {}).items()}
            new = sa.adjudicate(scores, null, args.margin, args.gap)

            transitions[(old_dataset, new["verdict"], new["dataset"])] += 1
            if new["verdict"] == sa.ATTRIBUTED and new["dataset"] == old_dataset:
                survivors[old_dataset] += 1
            else:
                lost[old_dataset] += 1
            detail.append(
                {
                    "name": record.get("name"),
                    "hidden_units": record.get("hidden_units"),
                    "old": {"dataset": old_dataset, "lift": record.get("lift")},
                    "new": {"verdict": new["verdict"], "dataset": new["dataset"], "lift": new.get("lift")},
                    "floor": {k: (v.get("max") if v else None) for k, v in null.items()},
                }
            )
            if index % 10 == 0:
                print(f"  [{index}/{len(rows)}] permutation nulls built", file=sys.stderr)

    print("\n" + "=" * 74)
    print("WEIGHT-PERMUTATION RE-ADJUDICATION")
    print("=" * 74)
    print(f"permutations per snapshot: {args.null_size}   margin: {args.margin}   gap: {args.gap}")
    if unloadable:
        print(f"unloadable snapshots skipped: {unloadable}")
    print()
    print(f"{'dataset':<14} {'was':>6} {'survives':>9} {'lost':>6}")
    print("-" * 40)
    for dataset in sorted(set(list(survivors) + list(lost)), key=lambda d: -(survivors[d] + lost[d])):
        total = survivors[dataset] + lost[dataset]
        print(f"{dataset or '<none>':<14} {total:>6} {survivors[dataset]:>9} {lost[dataset]:>6}")
    print("-" * 40)
    print(f"{'TOTAL':<14} {sum(survivors.values()) + sum(lost.values()):>6} {sum(survivors.values()):>9} {sum(lost.values()):>6}")

    print("\nverdict transitions (was -> new):")
    for (od, nv, nd), count in transitions.most_common():
        print(f"  {count:>4}  {od} -> {nv}:{nd}")

    if args.json_out:
        args.json_out.write_text(json.dumps({"detail": detail, "null_size": args.null_size}, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json_out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
