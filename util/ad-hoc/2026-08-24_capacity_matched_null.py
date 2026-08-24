"""
Re-adjudicate the attributed snapshot cohort against a CAPACITY-MATCHED null.

The null in ``util/snapshot_attribute.py`` is keyed on ``(input_size, output_size)``
and every null network is freshly constructed -- therefore ZERO hidden units. Measured:
**0 of the 129 attributed snapshots have zero hidden units** (they run 1..103), so that
floor is capacity-correct for none of them. A grown network partitions the input plane
more finely, and permutation-corrected argmax accuracy rises with that capacity for
reasons unrelated to having learned the dataset -- so the floor is too low and every
lift is inflated by an unknown amount.

This script rebuilds the floor at the RIGHT capacity and replays the *unmodified*
``adjudicate`` over the *stored* scores, so the null is the only thing that changes.

The null network reproduces the real cascade wiring rather than a flat hidden layer:
``_compute_hidden_outputs`` feeds unit ``i`` from ``buffer[:, :input_size + i]``, so
unit ``i``'s weight vector has shape ``(input_size + i,)`` and the output layer is
``(input_size + n_hidden, output_size)``. A flat-layer approximation would understate
the floor, which is the direction that manufactures attributions.

Read-only with respect to the archive: it opens no snapshot and writes no sidecar.
``JUNIPER_CASCOR_SNAPSHOTS_DIR`` is redirected before any cascor import so that
constructing probe networks cannot grow the archive being measured.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-24
Status: ad-hoc -- investigation
Retire when: the capacity-matched null ships inside util/snapshot_attribute.py.
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

# MUST precede any cascor import: constants_hdf5.py reads this at module-import time, and
# `train_output_layer` calls `create_snapshot()` unconditionally. Without this a probe grows
# the very archive it is measuring.
_PROBE_SNAPSHOT_DIR = pathlib.Path(tempfile.mkdtemp(prefix="capnull-probe-"))
os.environ["JUNIPER_CASCOR_SNAPSHOTS_DIR"] = str(_PROBE_SNAPSHOT_DIR)
os.environ.setdefault("CASCOR_NUM_PROCESSES", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import snapshot_attribute as sa  # noqa: E402 - deliberate: env must be set before this import chain

DEFAULT_SIDECAR = pathlib.Path(
    "/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots/snapshots_attribution.jsonl"
)


def build_capacity_matched_null(datasets, shape, n_hidden, size, cascor_src, seed_base, verbose=False):
    """Score ``size`` random networks that have ``n_hidden`` units wired as a real cascade.

    Returns the same {dataset: {p50,p95,max,n}} shape as ``snapshot_attribute.build_null`` so
    it is a drop-in replacement for the floor lookup in ``adjudicate``.
    """
    sys.path.insert(0, str(cascor_src))
    import torch

    from cascade_correlation.cascade_correlation import CascadeCorrelationNetwork
    from cascade_correlation.cascade_correlation_config.cascade_correlation_config import CascadeCorrelationConfig

    input_size, output_size = shape
    samples = {name: [] for name in datasets}

    with sa._muffle_stdout(not verbose):
        for offset in range(size):
            seed = seed_base + offset
            torch.manual_seed(seed)
            network = CascadeCorrelationNetwork(config=CascadeCorrelationConfig(input_size=input_size, output_size=output_size, random_seed=seed))
            scale = float(getattr(network, "random_value_scale", 1.0) or 1.0)
            activation = _resolve_activation(network)

            # Faithful cascade wiring: unit i reads input_size + i features.
            network.hidden_units = [
                {
                    "activation_fn": activation,
                    "weights": torch.randn(input_size + index) * scale,
                    "bias": torch.randn(1) * scale,
                }
                for index in range(n_hidden)
            ]
            network.output_weights = torch.randn(input_size + n_hidden, output_size) * scale
            network.output_bias = torch.randn(output_size) * scale

            for name, scored in sa.score_network(network, datasets, torch).items():
                samples[name].append(scored)

    built = {}
    for name, values in samples.items():
        if values:
            built[name] = {"p50": sa.percentile(values, 50), "p95": sa.percentile(values, 95), "max": max(values), "n": len(values)}
        else:
            built[name] = {"p50": None, "p95": None, "max": None, "n": 0}
    return built


def _resolve_activation(network):
    """The activation the serializer would install on a restored unit.

    Mirrors ``snapshot_serializer.py:1333-1335`` so a null unit computes exactly what a
    loaded unit computes; a bare callable and a wrapped one differ in this codebase.
    """
    from utils.activation import ActivationWithDerivative

    fn = getattr(network, "activation_fn", None)
    if isinstance(fn, ActivationWithDerivative):
        return fn
    return ActivationWithDerivative(fn)


def load_attributed(sidecar: pathlib.Path, verdicts):
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
    parser.add_argument("--null-size", type=int, default=120, help="random networks per (shape, hidden) architecture")
    parser.add_argument("--margin", type=float, default=sa.DEFAULT_MARGIN)
    parser.add_argument("--gap", type=float, default=sa.DEFAULT_GAP)
    parser.add_argument("--cascor-src", type=pathlib.Path, default=None)
    parser.add_argument("--data-root", type=pathlib.Path, default=None)
    parser.add_argument("--seed", type=int, default=20260824)
    parser.add_argument("--verdicts", default="attributed", help="comma-separated verdicts to re-adjudicate")
    parser.add_argument("--limit-arch", type=int, default=None, help="only build nulls for the N smallest architectures (smoke test)")
    parser.add_argument("--json-out", type=pathlib.Path, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    cascor_src = args.cascor_src or sa.default_cascor_src()
    data_root = args.data_root or sa.default_data_root()
    verdicts = tuple(v.strip() for v in args.verdicts.split(",") if v.strip())

    datasets = sa.load_datasets(data_root)
    print(f"datasets loaded: {', '.join(sorted(datasets))}", file=sys.stderr)

    rows = load_attributed(args.sidecar, verdicts)
    print(f"rows to re-adjudicate: {len(rows)} (verdicts={verdicts})", file=sys.stderr)

    architectures = sorted({(tuple(r.get("shape") or ()), int(r.get("hidden_units") or 0)) for r in rows}, key=lambda a: (a[1], a[0]))
    if args.limit_arch:
        architectures = architectures[: args.limit_arch]
        keep = set(architectures)
        rows = [r for r in rows if (tuple(r.get("shape") or ()), int(r.get("hidden_units") or 0)) in keep]
        print(f"LIMITED to {len(architectures)} architectures / {len(rows)} rows (smoke)", file=sys.stderr)
    print(f"architectures needing a capacity-matched null: {len(architectures)}", file=sys.stderr)

    nulls = {}
    for index, (shape, hidden) in enumerate(architectures, start=1):
        nulls[(shape, hidden)] = build_capacity_matched_null(
            datasets, shape, hidden, args.null_size, cascor_src, seed_base=args.seed + hidden * 1000, verbose=args.verbose
        )
        print(f"  [{index}/{len(architectures)}] shape={shape} hidden={hidden} null built", file=sys.stderr)

    transitions = collections.Counter()
    survivors = collections.Counter()
    lost = collections.Counter()
    detail = []

    for record in rows:
        shape = tuple(record.get("shape") or ())
        hidden = int(record.get("hidden_units") or 0)
        scores = {k: float(v) for k, v in (record.get("scores") or {}).items()}
        old_verdict = record.get("verdict")
        old_dataset = record.get("dataset")

        new = sa.adjudicate(scores, nulls[(shape, hidden)], args.margin, args.gap)
        transitions[(old_verdict, old_dataset, new["verdict"], new["dataset"])] += 1
        if new["verdict"] == sa.ATTRIBUTED and new["dataset"] == old_dataset:
            survivors[old_dataset] += 1
        else:
            lost[old_dataset] += 1
        detail.append(
            {
                "name": record.get("name"),
                "shape": list(shape),
                "hidden_units": hidden,
                "old": {"verdict": old_verdict, "dataset": old_dataset, "lift": record.get("lift")},
                "new": {"verdict": new["verdict"], "dataset": new["dataset"], "lift": new.get("lift"), "gap": new.get("gap")},
            }
        )

    print("\n" + "=" * 74)
    print("CAPACITY-MATCHED RE-ADJUDICATION")
    print("=" * 74)
    print(f"null size per architecture: {args.null_size}   margin: {args.margin}   gap: {args.gap}\n")
    print(f"{'dataset':<14} {'was':>6} {'survives':>9} {'lost':>6}")
    print("-" * 40)
    for dataset in sorted(set(list(survivors) + list(lost)), key=lambda d: -(survivors[d] + lost[d])):
        total = survivors[dataset] + lost[dataset]
        print(f"{dataset or '<none>':<14} {total:>6} {survivors[dataset]:>9} {lost[dataset]:>6}")
    print("-" * 40)
    print(f"{'TOTAL':<14} {sum(survivors.values()) + sum(lost.values()):>6} {sum(survivors.values()):>9} {sum(lost.values()):>6}")

    print("\nverdict transitions (old -> new):")
    for (ov, od, nv, nd), count in transitions.most_common():
        arrow = f"{ov}:{od} -> {nv}:{nd}"
        print(f"  {count:>4}  {arrow}")

    if args.json_out:
        args.json_out.write_text(json.dumps({"detail": detail, "null_size": args.null_size}, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json_out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
