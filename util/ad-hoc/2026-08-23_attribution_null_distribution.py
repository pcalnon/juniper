#!/usr/bin/env python3
"""Do TRAINED snapshots separate from UNTRAINED networks, per dataset?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-23
Status: ad-hoc — methodology check for handoff item 2
Retire when: the attribution design is settled.
Related: 2026-08-23_dataset_attribution_signal_probe.py,
         2026-08-23_attribution_untrained_control.py

THE PROBLEM THIS MEASURES
    The owner's design (§3.2) scores each snapshot against every 2-in -> 2-out dataset and
    treats better-than-chance as evidence of provenance, picking the largest margin over
    chance. The untrained control showed that cannot work as stated: a network that has
    NEVER been trained already beats chance on ``gaussian`` by **+0.408 on average, up to
    +0.500 (perfect)**, because gaussian blobs are linearly separable and a random linear
    boundary separates them -- especially once accuracy is made permutation-invariant.

    So "beats chance" is not the right test. The right test is "beats what an UNTRAINED
    network of the same shape already gets on this dataset".

    This script builds that null distribution per dataset and reports how far the trained
    population separates from it. Where the two distributions overlap, the dataset carries
    no provenance information at all and must be excluded from attribution rather than
    silently winning it.

READ-ONLY.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import random
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
SIDECAR = JUNIPER / "juniper-cascor" / "cascor-snapshots" / "snapshots_classification.jsonl"
GENERATORS = ("spiral", "xor", "gaussian", "circles", "moon", "checkerboard")


@contextlib.contextmanager
def muffled():
    sys.stdout.flush()
    saved, devnull = os.dup(1), os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 1)
        yield
    finally:
        sys.stdout.flush()
        os.dup2(saved, 1)
        os.close(devnull)
        os.close(saved)


def percentile(values, q):
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    index = min(len(ordered) - 1, max(0, int(round(q / 100.0 * (len(ordered) - 1)))))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trained", type=int, default=120)
    parser.add_argument("--untrained", type=int, default=120)
    parser.add_argument("--min-hidden", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260823)
    args = parser.parse_args()

    sys.path.insert(0, str(JUNIPER / "juniper-data"))
    sys.path.insert(0, str(JUNIPER / "juniper-cascor" / "src"))
    import numpy as np
    import torch

    datasets = {}
    for name in GENERATORS:
        module = __import__(f"juniper_data.generators.{name}", fromlist=["x"])
        generator = getattr(module, f"{name.capitalize()}Generator", None) or getattr(module, f"{name.title()}Generator")
        params_cls = getattr(module, f"{name.capitalize()}Params", None) or getattr(module, f"{name.title()}Params")
        produced = generator.generate(params_cls())
        X, y = produced["X_full"], produced["y_full"]
        datasets[name] = (torch.tensor(X, dtype=torch.float32), np.argmax(y, axis=1))

    def scores(network):
        result = {}
        for name, (X, labels) in datasets.items():
            with muffled():
                output = network.forward(X)
            raw = float((output.argmax(dim=1).cpu().numpy() == labels).mean())
            result[name] = max(raw, 1.0 - raw)
        return result

    from cascade_correlation.cascade_correlation import CascadeCorrelationNetwork
    from cascade_correlation.cascade_correlation_config.cascade_correlation_config import CascadeCorrelationConfig
    from snapshots.snapshot_serializer import CascadeHDF5Serializer

    print(f"building null from {args.untrained} untrained networks …")
    null = {name: [] for name in GENERATORS}
    for seed in range(args.untrained):
        with muffled():
            torch.manual_seed(seed)
            network = CascadeCorrelationNetwork(config=CascadeCorrelationConfig(input_size=2, output_size=2, random_seed=seed))
        for name, value in scores(network).items():
            null[name].append(value)

    print(f"scoring {args.trained} trained snapshots …")
    rows = [json.loads(line) for line in SIDECAR.open() if line.strip()]
    loadable = [r for r in rows if (r.get("load") or {}).get("status") == "ok" and (r.get("iterations_lower_bound") or 0) >= args.min_hidden]
    sample = random.Random(args.seed).sample(loadable, min(args.trained, len(loadable)))

    serializer = CascadeHDF5Serializer()
    trained = {name: [] for name in GENERATORS}
    for row in sample:
        with muffled():
            network = serializer.load_network(row["path"], restore_multiprocessing=False)
        if network is None or getattr(network, "input_size", None) != 2 or getattr(network, "output_size", None) != 2:
            continue
        for name, value in scores(network).items():
            trained[name].append(value)

    print(f"\npermutation-corrected accuracy — UNTRAINED null vs TRAINED (n_trained={len(trained[GENERATORS[0]])})\n")
    header = f"{'dataset':<14} {'null p50':>9} {'null p95':>9} {'null max':>9} | {'train p50':>9} {'train p95':>9} | {'p50 lift':>9} {'>null p95':>10}"
    print(header)
    print("-" * len(header))
    verdicts = {}
    for name in GENERATORS:
        n50, n95, nmax = percentile(null[name], 50), percentile(null[name], 95), max(null[name])
        t50, t95 = percentile(trained[name], 50), percentile(trained[name], 95)
        above = sum(1 for v in trained[name] if v > n95) / max(len(trained[name]), 1)
        lift = t50 - n50
        verdicts[name] = (lift, above)
        print(f"{name:<14} {n50:>9.3f} {n95:>9.3f} {nmax:>9.3f} | {t50:>9.3f} {t95:>9.3f} | {lift:>+9.3f} {above:>9.1%}")

    print("\nINTERPRETATION")
    print("  'p50 lift'  = how much the median trained snapshot beats the median untrained one.")
    print("  '>null p95' = share of trained snapshots exceeding the 95th percentile of the null;")
    print("                5% is what pure chance produces, so anything near 5% carries NO signal.")
    print()
    for name, (lift, above) in sorted(verdicts.items(), key=lambda kv: -kv[1][0]):
        if lift > 0.10 and above > 0.30:
            verdict = "USABLE — trained networks clearly separate from the null"
        elif above <= 0.10:
            verdict = "UNUSABLE — indistinguishable from an untrained network"
        else:
            verdict = "WEAK — partial separation; not sufficient alone"
        print(f"  {name:<14} {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
