#!/usr/bin/env python
"""Lane B refutation rig: the seed-perturbation probe on a finite-pool generator.

Project:       Juniper
Sub-Project:   JuniperML
Application:   util/ad-hoc
Author:        Paul Calnon
Version:       0.7.1
License:       MIT License

Builds a synthetic local ARC-AGI task pool (no network) and runs the PROPOSED
gate exactly as specified:

  probe(params) -> generate twice with two different seeds, compare X_full;
                   identical => "invariant" (refuse INDEPENDENT_SUBSTREAM)
                   differing => "dependent" (honour it)

then measures what INDEPENDENT_SUBSTREAM actually produces.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from juniper_data.generators.arc_agi.generator import ArcAgiGenerator
from juniper_data.generators.arc_agi.params import ArcAgiParams

# --------------------------------------------------------------------------- #
# The proposed mechanism, implemented faithfully.
# --------------------------------------------------------------------------- #


def name_key(name: str) -> int:
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big")


def substream_seed(root_seed: int, name: str) -> int:
    ss = np.random.SeedSequence(entropy=root_seed, spawn_key=(name_key(name),))
    return int(ss.generate_state(1, dtype=np.uint32)[0])


def probe_seed_sensitivity(make, base_kwargs, key="X_full", seed_a=11, seed_b=22):
    """Step 2 of the proposal: two seeds, assert X_full differs."""
    a = make({**base_kwargs, "seed": seed_a})[key]
    b = make({**base_kwargs, "seed": seed_b})[key]
    same_shape = a.shape == b.shape
    identical = same_shape and a.tobytes() == b.tobytes()
    return ("invariant" if identical else "dependent"), a, b


def exact_dupe_rows(A: np.ndarray, B: np.ndarray) -> int:
    """G-a's discriminator: count rows of B that appear byte-identically in A."""
    if A.size == 0 or B.size == 0:
        return 0
    sa = {r.tobytes() for r in np.ascontiguousarray(A)}
    return sum(1 for r in np.ascontiguousarray(B) if r.tobytes() in sa)


# --------------------------------------------------------------------------- #
# Synthetic ARC pool (offline).
# --------------------------------------------------------------------------- #


def build_pool(root: Path, n_tasks: int, rng: np.random.Generator) -> None:
    d = root / "training"
    d.mkdir(parents=True, exist_ok=True)
    for i in range(n_tasks):
        g_in = rng.integers(0, 10, size=(3, 3)).tolist()
        g_out = rng.integers(0, 10, size=(3, 3)).tolist()
        json.dump({"train": [{"input": g_in, "output": g_out}], "test": []}, (d / f"t{i:03d}.json").open("w"))


def gen(kwargs):
    return ArcAgiGenerator.generate(ArcAgiParams(**kwargs))


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="laneb_arc_"))
    try:
        pool = tmp / "pool"
        build_pool(pool, n_tasks=40, rng=np.random.default_rng(7))

        base = {"source": "local", "local_path": str(pool), "subset": "training", "pad_to": 30}

        print("=" * 78)
        print("A. FINITE POOL, n_tasks == pool size  (arc_agi: replace=False is per-partition)")
        print("=" * 78)
        kw = {**base, "n_tasks": 40}
        verdict, a, b = probe_seed_sensitivity(gen, kw)
        print(f"   pool size                     : 40 tasks")
        print(f"   X_full shape                  : {a.shape}")
        print(f"   PROBE VERDICT (X_full, 11/22) : {verdict}   <-- gate honours INDEPENDENT_SUBSTREAM")
        print(f"   X_full rows AS A SET identical: {sorted(r.tobytes() for r in a) == sorted(r.tobytes() for r in b)}")

        # Now do what the gate just authorised: independent per-partition substreams.
        root = 12345
        parts = {}
        for nm in ("train", "validation", "test"):
            parts[nm] = gen({**kw, "seed": substream_seed(root, nm)})["X_full"]
        tr, va, te = parts["train"], parts["validation"], parts["test"]
        print(f"   partition sizes               : train={len(tr)} val={len(va)} test={len(te)}")
        print(f"   EXACT duplicate rows val<-train: {exact_dupe_rows(tr, va)} / {len(va)}  "
              f"({100.0 * exact_dupe_rows(tr, va) / max(len(va), 1):.1f}%)")
        print(f"   EXACT duplicate rows test<-train: {exact_dupe_rows(tr, te)} / {len(te)}")

        print()
        print("=" * 78)
        print("B. FINITE POOL, n_tasks < pool size (the 'expected overlap' regime)")
        print("=" * 78)
        for n in (30, 20, 10):
            kw2 = {**base, "n_tasks": n}
            v, _, _ = probe_seed_sensitivity(gen, kw2)
            p = {nm: gen({**kw2, "seed": substream_seed(root, nm)})["X_full"] for nm in ("train", "validation")}
            d = exact_dupe_rows(p["train"], p["validation"])
            print(f"   n_tasks={n:3d}/40  probe={v:<10s}  val rows duplicated from train: "
                  f"{d}/{len(p['validation'])} ({100.0 * d / max(len(p['validation']), 1):.1f}%)")

        print()
        print("=" * 78)
        print("C. seed IS A CONTROL-FLOW SWITCH -- the probe cannot reach the run's branch")
        print("=" * 78)
        kw3 = {**base, "n_tasks": 10}
        v, _, _ = probe_seed_sensitivity(gen, kw3)
        # The RUN, as configured by the caller (seed omitted => default None):
        run_none_1 = gen({**kw3})["X_full"]
        run_none_2 = gen({**kw3})["X_full"]
        print(f"   caller's params contain seed=None (ArcAgiParams default).")
        print(f"   PROBE (substitutes seeds 11/22) : {v}")
        print(f"   ACTUAL run with seed=None, twice: identical = {run_none_1.tobytes() == run_none_2.tobytes()}")
        print(f"   -> generator.py:129-135  `if params.seed is None: tasks = tasks[:n]`")
        print(f"      The probe, by setting a seed, ALWAYS takes the `else: rng.choice(...)` branch.")
        print(f"      It reports on code the run does not execute.")

        print()
        print("=" * 78)
        print("D. EMPTY DATASET -- every gate is vacuously green")
        print("=" * 78)
        empty = tmp / "empty"
        (empty / "training").mkdir(parents=True)
        kwe = {"source": "local", "local_path": str(empty), "subset": "training", "pad_to": 30, "n_tasks": 10}
        ve, ea, eb = probe_seed_sensitivity(gen, kwe)
        print(f"   X_full shape                   : {ea.shape}   (matches the reported (0, 900))")
        print(f"   PROBE VERDICT                  : {ve}")
        print(f"   G-a duplicate rows val<-train  : {exact_dupe_rows(ea, eb)}   (0 duplicates => G-a PASSES)")
        print(f"   -> 'invariant' here is a fact about an EMPTY ARRAY, not about the generator.")
        print(f"      Same config with a non-empty pool probes as: "
              f"{probe_seed_sensitivity(gen, {**base, 'n_tasks': 10})[0]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
