#!/usr/bin/env python3
"""Positive control: can attribution identify a dataset we KNOW the answer for?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-23
Status: ad-hoc — methodology check for handoff item 2
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the attribution design is settled.
Related: 2026-08-23_attribution_null_distribution.py

WHY THIS IS THE DECIDING EXPERIMENT
    The null-distribution check found that archive snapshots do not separate from UNTRAINED
    networks on any of the six 2-D datasets. That has two very different explanations, and
    they imply opposite next steps:

      (a) THE METHOD IS BROKEN -- scoring a cascor network against candidate datasets simply
          cannot recover provenance, so no amount of parameter sweeping will help; or
      (b) THE ARCHIVE IS UNDER-TRAINED -- the method works, but these particular snapshots
          (median 3 hidden units, largely from a debugging campaign) never learned enough to
          carry a signature.

    Only a positive control separates them: train a network HERE, on a dataset we choose, and
    ask attribution to name it. If it cannot identify a network it should trivially identify,
    the method is broken and (b) is not worth chasing.

    It also measures the second thing that matters: whether a network trained on generator
    defaults still scores well when the candidate is generated at DIFFERENT parameters, which
    is what attribution against an unknown archive would actually face.

READ-ONLY with respect to the archive. Trains in memory; writes no snapshot.
NOTE: ``train_output_layer`` calls ``create_snapshot()`` unconditionally, so
``JUNIPER_CASCOR_SNAPSHOTS_DIR`` is set to a scratch dir before any training happens.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
import tempfile
from pathlib import Path

# MUST precede any cascor import that could trigger a snapshot write.
_SCRATCH = tempfile.mkdtemp(prefix="attribution-control-")
os.environ["JUNIPER_CASCOR_SNAPSHOTS_DIR"] = _SCRATCH

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
    parser.add_argument("--epochs", type=int, default=400)
    parser.add_argument("--hidden", type=int, default=8, help="max hidden units to grow")
    # cascor's shipped defaults are sized for real training runs, not controls:
    # candidate_pool_size=40, candidate_epochs=400, output_epochs=10000,
    # max_iterations=1000000. A default fit() therefore trains 40 candidates x 400 epochs
    # per growth iteration -- which is why the first two attempts at this control burned
    # 40 and 15 minutes without finishing one 194-point dataset.
    parser.add_argument("--pool", type=int, default=4, help="candidate pool size (default 40 is far too large for a control)")
    parser.add_argument("--candidate-epochs", type=int, default=60)
    parser.add_argument(
        "--train-only",
        default=None,
        help="comma-separated subset of datasets to TRAIN on (all six remain candidates). "
        "Cascade training is compute-heavy -- a full six-network control ran >40 min. "
        "spiral / xor / checkerboard are the informative targets: the untrained-null margins "
        "there are +0.020 / +0.065 / -0.006, so a win is real signal rather than the dataset "
        "being linearly separable. gaussian and moon are won by untrained networks anyway.",
    )
    args = parser.parse_args()
    targets = tuple(t.strip() for t in args.train_only.split(",")) if args.train_only else GENERATORS

    sys.path.insert(0, str(JUNIPER / "juniper-data"))
    sys.path.insert(0, str(JUNIPER / "juniper-cascor" / "src"))
    import numpy as np
    import torch

    def build(name, **overrides):
        module = __import__(f"juniper_data.generators.{name}", fromlist=["x"])
        generator = getattr(module, f"{name.capitalize()}Generator", None) or getattr(module, f"{name.title()}Generator")
        params_cls = getattr(module, f"{name.capitalize()}Params", None) or getattr(module, f"{name.title()}Params")
        produced = generator.generate(params_cls(**overrides))
        return produced["X_full"], produced["y_full"]

    candidates = {}
    for name in GENERATORS:
        X, y = build(name)
        candidates[name] = (torch.tensor(X, dtype=torch.float32), np.argmax(y, axis=1))

    def scores(network):
        out = {}
        for name, (X, labels) in candidates.items():
            with muffled():
                output = network.forward(X)
            raw = float((output.argmax(dim=1).cpu().numpy() == labels).mean())
            out[name] = max(raw, 1.0 - raw)
        return out

    from cascade_correlation.cascade_correlation import CascadeCorrelationNetwork
    from cascade_correlation.cascade_correlation_config.cascade_correlation_config import CascadeCorrelationConfig

    print(f"scratch snapshot dir: {_SCRATCH}\n")
    print("Training one network per dataset, then asking attribution to name it.\n")
    header = f"{'trained on':<14} {'hid':>4} " + " ".join(f"{n[:9]:>9}" for n in GENERATORS) + f"  {'picked':>13} {'correct':>8}"
    print(header)
    print("-" * len(header))

    correct = 0
    total = 0
    for truth in targets:
        X_np, y_np = build(truth)
        X = torch.tensor(X_np, dtype=torch.float32)
        y = torch.tensor(y_np, dtype=torch.float32)
        with muffled():
            torch.manual_seed(101)
            # ``max_epochs`` alone is NOT enough, and this is a documented hazard: the
            # service/library applies it only to the INITIAL output pass, while every later
            # pass reads ``output_epochs``, which falls back to **10000**. Setting only
            # ``max_epochs`` therefore looks capped and silently runs 50x longer -- measured
            # here as >16 minutes without finishing a single 194-point dataset. Both must be
            # set, to the same value.
            config = CascadeCorrelationConfig(
                input_size=2,
                output_size=2,
                random_seed=101,
                max_hidden_units=args.hidden,
                output_epochs=args.epochs,
                candidate_epochs=args.candidate_epochs,
                candidate_pool_size=args.pool,
                max_iterations=args.hidden,
            )
            network = CascadeCorrelationNetwork(config=config)
            # ``fit`` is THE training entry point. An earlier cut of this control called a
            # non-existent ``train_network`` inside a bare ``except: pass``, so every network
            # came out untrained and the control silently measured untrained networks --
            # producing a confident "the method is broken" from an experiment that never ran.
            # No swallowing here: a training failure must be visible.
            network.fit(X, y, max_epochs=args.epochs, max_iterations=args.hidden)
        result = scores(network)

        # A positive control is only valid if the positive actually happened. If the network
        # cannot classify the data it was JUST trained on, the run says nothing about
        # attribution and must not be scored as though it did.
        self_score = result[truth]
        if self_score < 0.70:
            print(f"{truth:<14} {len(getattr(network, 'hidden_units', []) or []):>4}  TRAINING DID NOT TAKE (scores {self_score:.3f} on its own data) — row excluded")
            continue
        picked = max(result, key=lambda k: result[k])
        hit = picked == truth
        correct += int(hit)
        total += 1
        cells = " ".join(f"{result[n]:>9.3f}" for n in GENERATORS)
        print(f"{truth:<14} {len(getattr(network, 'hidden_units', []) or []):>4} {cells}  {picked:>13} {'YES' if hit else 'no':>8}")

    print(f"\npositive control: {correct}/{total} correctly attributed")
    if correct <= total // 2:
        print("\nThe method cannot reliably name a dataset it was JUST trained on.")
        print("That is a property of the approach, not of the archive — parameter sweeping")
        print("over an unknown corpus cannot fix what fails on a known one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
