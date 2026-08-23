#!/usr/bin/env python3
"""Control for the dataset-attribution probe: what do UNTRAINED networks score?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-23
Status: ad-hoc — control experiment for handoff item 2
Retire when: the attribution design is settled.
Related: util/ad-hoc/2026-08-23_dataset_attribution_signal_probe.py

WHY THIS EXISTS
    The signal probe found that permutation-corrected accuracy picks ``gaussian`` for 9 of
    14 sampled snapshots, with margins around +0.45. That looks like strong provenance
    evidence -- but it has an innocent explanation that would invalidate the whole approach:
    **gaussian blobs are linearly separable**, so ANY network with a sane linear decision
    boundary scores ~0.95 on them regardless of what it was trained on.

    If that were the cause, "gaussian" would be the default answer for every half-trained
    network in the archive and would mean nothing.

    The control that separates the two: score networks that have NEVER BEEN TRAINED. A fresh
    network's output layer is random, so any dataset it "wins" is won by the dataset's own
    easiness, not by anything the network learned. Whatever the untrained baseline picks --
    and by what margin -- is the floor that a real attribution has to clear.

READ-ONLY. Constructs networks in memory; touches no snapshot and writes nothing.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--networks", type=int, default=12, help="How many fresh networks to score")
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
        labels = np.argmax(y, axis=1)
        baseline = float(np.bincount(labels, minlength=2).max() / len(labels))
        datasets[name] = (X, labels, baseline)

    from cascade_correlation.cascade_correlation import CascadeCorrelationNetwork
    from cascade_correlation.cascade_correlation_config.cascade_correlation_config import CascadeCorrelationConfig

    print("CONTROL — freshly initialised, NEVER trained (permutation-corrected scores)\n")
    header = f"{'seed':>5} " + " ".join(f"{n[:9]:>9}" for n in GENERATORS) + f"  {'best':>13} {'margin':>7}"
    print(header)
    print("-" * len(header))

    wins: dict[str, int] = {}
    margins_by_dataset: dict[str, list] = {name: [] for name in GENERATORS}
    for seed in range(args.networks):
        with muffled():
            torch.manual_seed(seed)
            network = CascadeCorrelationNetwork(config=CascadeCorrelationConfig(input_size=2, output_size=2, random_seed=seed))
        accuracies = {}
        for name, (X, labels, _) in datasets.items():
            with muffled():
                output = network.forward(torch.tensor(X, dtype=torch.float32))
            raw = float((output.argmax(dim=1).cpu().numpy() == labels).mean())
            accuracies[name] = max(raw, 1.0 - raw)
        for name in GENERATORS:
            margins_by_dataset[name].append(accuracies[name] - datasets[name][2])
        best = max(accuracies, key=lambda k: accuracies[k] - datasets[k][2])
        margin = accuracies[best] - datasets[best][2]
        wins[best] = wins.get(best, 0) + 1
        print(f"{seed:>5} " + " ".join(f"{accuracies[n]:>9.3f}" for n in GENERATORS) + f"  {best:>13} {margin:>+7.3f}")

    print(f"\nuntrained winners: {wins}")
    print("\nper-dataset margin an UNTRAINED network already achieves (the floor to clear):")
    for name in GENERATORS:
        values = margins_by_dataset[name]
        print(f"  {name:<13} mean={sum(values) / len(values):>+7.3f}  max={max(values):>+7.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
