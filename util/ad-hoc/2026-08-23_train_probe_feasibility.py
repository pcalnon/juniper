#!/usr/bin/env python3
"""Feasibility probe for handoff item 3 — the training probe over the zero-node cohort.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-23
Status: ad-hoc — cost/behaviour probe before building the item-3 pass
Retire when: util/snapshot_train_probe.py exists, or the approach is abandoned.
Related: handoff 2026-08-22 §2.3 / §3.3,
         notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_SNAPSHOT-CLASSIFICATION-STAGE-1-FINDINGS.md

WHAT ITEM 3 ASKS
    §2.3: "load the no-hidden-node snapshots and initiate standard training. [...] A snapshot
    that then fails to train belongs to a different subset -- dysfunctional networks."

    That splits the archive's **15,927 zero-hidden-unit snapshots** into category 3
    (*formerly broken* -- reloads without hidden nodes but CAN train) and category 2
    (*fails to train* -- dysfunctional).

WHY PROBE FIRST
    Item 2 taught the lesson twice: cascor's shipped training defaults are enormous
    (candidate_pool_size=40, candidate_epochs=400, output_epochs=10000, max_iterations=1e6),
    so a naive `fit()` per snapshot is measured in minutes, and 15,927 x minutes is weeks.

    Two things must be known before designing the pass:
      1. the per-snapshot cost of the SMALLEST training run that still answers the question;
      2. whether a cheap STRUCTURAL screen (non-finite or degenerate weights) already
         separates the dysfunctional ones, in which case most of the cohort never needs
         training at all.

    (2) is the interesting one: a structural screen is ~30 ms/snapshot, so if it finds the
    dysfunctional set, item 3 collapses from weeks to minutes.

SAFETY
    ``train_output_layer`` calls ``create_snapshot()`` unconditionally, so
    ``JUNIPER_CASCOR_SNAPSHOTS_DIR`` is redirected to a scratch dir BEFORE any cascor import.
    Without that this probe would write into the archive it is measuring.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import random
import sys
import tempfile
import time
from pathlib import Path

_SCRATCH = tempfile.mkdtemp(prefix="train-probe-")
os.environ["JUNIPER_CASCOR_SNAPSHOTS_DIR"] = _SCRATCH

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
CASCOR_SRC = JUNIPER / "juniper-cascor" / "src"
DATA_ROOT = JUNIPER / "juniper-data"
SIDECAR = JUNIPER / "juniper-cascor" / "cascor-snapshots" / "snapshots_classification.jsonl"


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


def structural_verdict(network, torch) -> str:
    """Cheap pathology screen -- no training. Does the network even hold usable numbers?

    A network whose weights are non-finite, or whose output layer is identically zero, cannot
    train meaningfully and does not need a training run to establish that.
    """
    weights = getattr(network, "output_weights", None)
    bias = getattr(network, "output_bias", None)
    if weights is None or bias is None:
        return "no_output_layer"
    try:
        if not bool(torch.isfinite(weights.detach()).all()) or not bool(torch.isfinite(bias.detach()).all()):
            return "non_finite_weights"
        if float(weights.detach().abs().sum()) == 0.0 and float(bias.detach().abs().sum()) == 0.0:
            return "all_zero_output_layer"
    except Exception as exc:  # noqa: BLE001 - an unusable tensor is itself the finding
        return f"unusable_tensors:{type(exc).__name__}"
    return "structurally_ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--screen", type=int, default=400, help="How many zero-node snapshots to structurally screen")
    parser.add_argument("--train", type=int, default=6, help="How many to actually train (cost measurement)")
    parser.add_argument("--pool", type=int, default=3)
    parser.add_argument("--candidate-epochs", type=int, default=30)
    parser.add_argument("--output-epochs", type=int, default=60)
    parser.add_argument("--seed", type=int, default=20260823)
    parser.add_argument("--verbose-rows", action="store_true", help="Print a line per trained snapshot (noisy over a large sample)")
    args = parser.parse_args()

    sys.path.insert(0, str(DATA_ROOT))
    sys.path.insert(0, str(CASCOR_SRC))
    import torch

    from snapshots.snapshot_serializer import CascadeHDF5Serializer

    rows = [json.loads(line) for line in SIDECAR.open() if line.strip()]
    zero_node = [r for r in rows if (r.get("load") or {}).get("status") == "ok" and (r.get("iterations_lower_bound") or 0) == 0]
    print(f"zero-node loadable cohort: {len(zero_node)}\n")

    serializer = CascadeHDF5Serializer()
    sample = random.Random(args.seed).sample(zero_node, min(args.screen, len(zero_node)))

    print(f"=== STAGE 1: structural screen ({len(sample)} snapshots, no training) ===")
    verdicts: dict[str, int] = {}
    ok_rows = []
    started = time.time()
    for record in sample:
        with muffled():
            network = serializer.load_network(record["path"], restore_multiprocessing=False)
        verdict = "load_failed" if network is None else structural_verdict(network, torch)
        verdicts[verdict] = verdicts.get(verdict, 0) + 1
        if verdict == "structurally_ok":
            ok_rows.append(record)
    elapsed = time.time() - started
    for name, count in sorted(verdicts.items(), key=lambda kv: -kv[1]):
        print(f"  {name:<26} {count:>5}  ({count / len(sample):.1%})")
    print(f"  screen cost: {elapsed / len(sample) * 1000:.0f} ms/snapshot -> {elapsed / len(sample) * len(zero_node) / 60:.0f} min for all {len(zero_node)}")

    if not ok_rows:
        print("\nnothing structurally OK to train; the screen alone answers item 3")
        return 0

    print(f"\n=== STAGE 2: training cost ({args.train} snapshots) ===")
    from cascade_correlation.cascade_correlation_config.cascade_correlation_config import CascadeCorrelationConfig  # noqa: F401

    module = __import__("juniper_data.generators.xor", fromlist=["x"])
    produced = module.XorGenerator.generate(module.XorParams())
    X = torch.tensor(produced["X_full"], dtype=torch.float32)
    y = torch.tensor(produced["y_full"], dtype=torch.float32)

    tally = {"formerly_broken": 0, "fails_to_train": 0}
    failures = []
    print(f"{'snapshot':<30} {'grew':>5} {'acc_before':>11} {'acc_after':>10} {'secs':>7}  outcome")
    for record in ok_rows[: args.train]:
        with muffled():
            network = serializer.load_network(record["path"], restore_multiprocessing=False)
        if network is None or network.input_size != 2 or network.output_size != 2:
            continue
        with muffled():
            before = float((network.forward(X).argmax(dim=1) == y.argmax(dim=1)).float().mean())
        # Pin every epoch knob: max_epochs alone is NOT enough -- later output passes read
        # output_epochs, which falls back to 10000.
        for field, value in (("candidate_pool_size", args.pool), ("candidate_epochs", args.candidate_epochs), ("output_epochs", args.output_epochs), ("max_iterations", 1), ("max_hidden_units", 2)):
            with contextlib.suppress(Exception):
                setattr(network, field, value)
                setattr(network.config, field, value)
        started = time.time()
        outcome = "trained"
        try:
            with muffled():
                network.fit(X, y, max_epochs=args.output_epochs, max_iterations=1)
        except Exception as exc:  # noqa: BLE001 - a training failure IS the category-2 signal
            outcome = f"FAILED {type(exc).__name__}: {str(exc)[:40]}"
        seconds = time.time() - started
        with muffled():
            after = float((network.forward(X).argmax(dim=1) == y.argmax(dim=1)).float().mean())
        grew = len(getattr(network, "hidden_units", []) or [])
        # "Can it train?" is a question about the PROCESS, not the outcome: fit() completed and
        # the cascade actually installed a unit. One sampled snapshot went 0.490 -> 0.460 --
        # worse accuracy, but it grew and trained, so it is category 3 (formerly broken), not
        # category 2. Conflating "trained badly" with "cannot train" would file healthy
        # networks as dysfunctional.
        trained = outcome == "trained" and grew > 0
        tally["formerly_broken" if trained else "fails_to_train"] += 1
        if not trained:
            failures.append((record["name"][17:47], outcome, grew))
        if args.verbose_rows:
            print(f"{record['name'][17:47]:<30} {grew:>5} {before:>11.3f} {after:>10.3f} {seconds:>7.1f}  {outcome}")

    total = sum(tally.values())
    if total:
        print(f"\n=== ITEM 3 SPLIT (n={total}) ===")
        for name, count in tally.items():
            print(f"  {name:<18} {count:>5}  ({count / total:.1%})")
        if failures:
            print("  failures:")
            for name, why, grew in failures[:10]:
                print(f"    {name}  grew={grew}  {why}")
        else:
            print("  (no failures in this sample)")
    print(f"\nscratch snapshots written (NOT the archive): {len(list(Path(_SCRATCH).glob('*.h5')))} in {_SCRATCH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
