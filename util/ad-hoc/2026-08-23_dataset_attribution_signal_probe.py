#!/usr/bin/env python3
"""Does a snapshot's accuracy actually IDENTIFY the dataset it was trained on?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-23
Status: ad-hoc — feasibility probe for handoff item 2 (the inference pass)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the signal is characterised and util/snapshot_attribute.py exists (or the
             approach is abandoned because the signal is not there).
Related: notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_SNAPSHOT-CLASSIFICATION-STAGE-1-FINDINGS.md,
         handoff 2026-08-22 §3.2 (owner's dataset-inference design)

WHY PROBE BEFORE BUILDING
    The owner's design (§3.2) is: inference is cheap, so score every snapshot against every
    2-in -> 2-out cascor dataset; better-than-chance is a strong-but-not-definitive
    indicator, and with multiple hits pick the largest margin over chance.

    That is only worth industrialising over 27.6k snapshots if the signal EXISTS and
    SEPARATES. Two failure modes would sink it, and neither is visible from reasoning:

      (a) everything scores ~chance  -> the networks do not discriminate at all;
      (b) everything scores high on several datasets -> six 2-D binary problems are similar
          enough that above-chance is not evidence of provenance.

    (b) is the real risk. Spiral / moons / circles are all "2-D points, two interleaved
    classes"; a network that separates one may well beat chance on another by accident.

WHAT IT REPORTS
    Per snapshot: accuracy on all six datasets, the majority-class baseline for each (the
    honest chance line -- a constant predictor achieves it), the margin over that, the best
    dataset, and the GAP to the runner-up. The gap is the decisiveness signal: a large
    margin that is not separated from second place identifies nothing.

READ-ONLY. Loads snapshots through cascor's own loader and writes nothing.
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
CASCOR_SRC = JUNIPER / "juniper-cascor" / "src"
DATA_ROOT = JUNIPER / "juniper-data"
SIDECAR = JUNIPER / "juniper-cascor" / "cascor-snapshots" / "snapshots_classification.jsonl"

#: The 2-D binary-classification family from juniper-data's GENERATOR_REGISTRY. Excludes
#: csv_import (arbitrary shape), equities*, the four regression synthetics, mnist (784->10)
#: and arc_agi.
GENERATORS = ("spiral", "xor", "gaussian", "circles", "moon", "checkerboard")


@contextlib.contextmanager
def muffled():
    """cascor logs every load to stdout; keep the report readable."""
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


def build_datasets():
    """Generate one canonical instance of each generator at its declared defaults."""
    sys.path.insert(0, str(DATA_ROOT))
    import numpy as np

    datasets = {}
    for name in GENERATORS:
        module = __import__(f"juniper_data.generators.{name}", fromlist=["x"])
        generator = getattr(module, f"{name.capitalize()}Generator", None) or getattr(module, f"{name.title()}Generator")
        params_cls = getattr(module, f"{name.capitalize()}Params", None) or getattr(module, f"{name.title()}Params")
        produced = generator.generate(params_cls())
        X, y = produced["X_full"], produced["y_full"]
        if X.shape[1] != 2 or y.shape[1] != 2:
            print(f"  skip {name}: shape ({X.shape[1]} in, {y.shape[1]} out) is not 2->2")
            continue
        labels = np.argmax(y, axis=1)
        # The honest chance line: what a constant predictor gets. Using a flat 0.5 would
        # overstate the margin on any generator whose classes are not balanced.
        counts = np.bincount(labels, minlength=y.shape[1])
        datasets[name] = {"X": X, "labels": labels, "baseline": float(counts.max() / len(labels)), "n": len(labels)}
    return datasets


def score(network, dataset, torch, np):
    """Accuracy UP TO A PERMUTATION OF THE CLASS LABELS.

    ⚠ Raw accuracy is the wrong metric here, and the first cut of this probe used it.

    One-hot column order is an arbitrary convention of whichever generator run produced the
    training set. A network that learned a dataset perfectly but with the two columns
    swapped scores ``1 - p``, so raw accuracy reports it as far BELOW chance -- and a
    below-chance score reads as "did not learn this", which is the exact opposite of the
    truth. Measured on the first probe run: several snapshots scored **0.010 / 0.030 /
    0.060** on gaussian. Those are not failures; they are 0.990 / 0.970 / 0.940 accuracy
    with the labels inverted, and they beat every raw-accuracy "winner" on the same row.

    Using raw accuracy would therefore have mis-attributed exactly the snapshots the signal
    is strongest for. For a binary problem the permutation-invariant score is
    ``max(p, 1 - p)``.
    """
    with contextlib.suppress(Exception):
        with muffled():
            output = network.forward(torch.tensor(dataset["X"], dtype=torch.float32))
        predicted = output.argmax(dim=1).cpu().numpy()
        raw = float((predicted == dataset["labels"]).mean())
        return max(raw, 1.0 - raw), raw
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sample", type=int, default=15, help="How many snapshots to probe")
    parser.add_argument("--min-hidden", type=int, default=1, help="Only probe snapshots with at least this many hidden units")
    parser.add_argument("--seed", type=int, default=20260823)
    args = parser.parse_args()

    print("building datasets …")
    datasets = build_datasets()
    import numpy as np

    for name, data in datasets.items():
        print(f"  {name:<13} n={data['n']:>5}  majority-class baseline={data['baseline']:.3f}")
    if not datasets:
        print("no usable 2->2 datasets; nothing to probe")
        return 2

    sys.path.insert(0, str(CASCOR_SRC))
    import torch

    from snapshots.snapshot_serializer import CascadeHDF5Serializer

    rows = [json.loads(line) for line in SIDECAR.open() if line.strip()]
    loadable = [r for r in rows if (r.get("load") or {}).get("status") == "ok" and (r.get("iterations_lower_bound") or 0) >= args.min_hidden]
    print(f"\nloadable with >={args.min_hidden} hidden unit(s): {len(loadable)}")
    sample = random.Random(args.seed).sample(loadable, min(args.sample, len(loadable)))

    serializer = CascadeHDF5Serializer()
    header = f"{'snapshot':<26} {'hid':>4} " + " ".join(f"{n[:9]:>9}" for n in datasets) + f"  {'best':>13} {'margin':>7} {'gap':>7}"
    print("\n(scores are permutation-corrected: max(p, 1-p) — see score())")
    print("\n" + header)
    print("-" * len(header))

    decisive = 0
    examined = 0
    for row in sample:
        with muffled():
            network = serializer.load_network(row["path"], restore_multiprocessing=False)
        if network is None:
            continue
        if getattr(network, "input_size", None) != 2 or getattr(network, "output_size", None) != 2:
            continue
        margins = {}
        accuracies = {}
        raw_accuracies = {}
        for name, data in datasets.items():
            scored = score(network, data, torch, np)
            if scored is None:
                continue
            corrected, raw = scored
            accuracies[name] = corrected
            raw_accuracies[name] = raw
            margins[name] = corrected - data["baseline"]
        if not margins:
            continue
        examined += 1
        ordered = sorted(margins.items(), key=lambda kv: -kv[1])
        best, best_margin = ordered[0]
        gap = best_margin - ordered[1][1] if len(ordered) > 1 else float("nan")
        if best_margin > 0.10 and gap > 0.05:
            decisive += 1
        cells = " ".join(f"{accuracies.get(n, float('nan')):>9.3f}" for n in datasets)
        print(f"{row['name'][17:43]:<26} {row.get('iterations_lower_bound', 0):>4} {cells}  {best:>13} {best_margin:>+7.3f} {gap:>+7.3f}")

    print(f"\nexamined {examined}; {decisive} had a decisive pick (margin > 0.10 AND gap to runner-up > 0.05)")
    print("\nA large margin with a SMALL gap identifies nothing: it means the network beats")
    print("chance on several of these 2-D binary problems, which is exactly what makes")
    print("above-chance a weak provenance signal on its own.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
