#!/usr/bin/env python
"""Lane B rig 5: the degenerate-gaussian case, and NaN reachability via csv_import.

Project:       Juniper
Sub-Project:   JuniperML
Application:   util/ad-hoc
Author:        Paul Calnon
Version:       0.7.1
License:       MIT License
"""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

import numpy as np

from juniper_data.generators.gaussian.generator import GaussianGenerator
from juniper_data.generators.gaussian.params import GaussianParams


def name_key(name):
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big")


def substream_seed(root, name):
    return int(np.random.SeedSequence(entropy=root, spawn_key=(name_key(name),)).generate_state(1, dtype=np.uint32)[0])


def flat(a):
    return np.ascontiguousarray(a.reshape(len(a), -1))


def exact_dupes(A, B):
    s = {r.tobytes() for r in flat(A)}
    return sum(1 for r in flat(B) if r.tobytes() in s)


print("=" * 96)
print("N. DEGENERATE GAUSSIAN -- probe 'dependent', G-a 0 duplicates, and train == val as a DATASET")
print("=" * 96)
root = 12345
print(f"   {'class_std':>10} | {'probe':>10} | {'G-a dupes':>10} | {'distinct rows in X_full':>23} | "
      f"{'worst val row nn-dist to train':>30}")
print("   " + "-" * 96)
for cs in (1.0, 1e-3, 1e-8, 1e-20):
    a = GaussianGenerator.generate(GaussianParams(class_std=cs, noise=0.0, seed=11))["X_full"]
    b = GaussianGenerator.generate(GaussianParams(class_std=cs, noise=0.0, seed=22))["X_full"]
    verdict = "invariant" if a.tobytes() == b.tobytes() else "dependent"
    tr = GaussianGenerator.generate(GaussianParams(class_std=cs, noise=0.0, seed=substream_seed(root, "train")))["X_full"]
    va = GaussianGenerator.generate(GaussianParams(class_std=cs, noise=0.0, seed=substream_seed(root, "validation")))["X_full"]
    d = exact_dupes(tr, va)
    distinct = len({r.tobytes() for r in flat(tr)})
    nn = np.array([np.abs(tr.astype(np.float64) - v).max(axis=1).min() for v in va.astype(np.float64)])
    print(f"   {cs:>10.0e} | {verdict:>10} | {d:>7}/{len(va):<3} | {distinct:>7} of {len(tr):<12} | {nn.max():.3e}")

print()
print("   At class_std=1e-20 the dataset is n_classes constant points repeated n_samples_per_class")
print("   times. Every validation row sits at ~1e-20 from a training row -- a 100% leak by any")
print("   sane definition -- and BOTH gates read green, because ONE center coordinate is exactly")
print("   0.0 (centers[i,1] = center_radius*sin(0)), where a 1e-20 perturbation is a representable")
print("   float32 subnormal. The whole verdict rests on that single cell.")
g = GaussianGenerator.generate(GaussianParams(class_std=1e-20, noise=0.0, seed=11))["X_full"]
h = GaussianGenerator.generate(GaussianParams(class_std=1e-20, noise=0.0, seed=22))["X_full"]
diff = (g != h)
print(f"   cells differing between the probe's two seeds: {int(diff.sum())} of {g.size}  "
      f"(columns hit: {sorted(set(np.nonzero(diff)[1].tolist()))})")
print(f"   max |difference| across the whole array      : {np.abs(g.astype(np.float64) - h.astype(np.float64)).max():.3e}")

print()
print("=" * 96)
print("O. NaN IS REACHABLE -- csv_import on a CSV with an empty cell")
print("=" * 96)
tmp = Path(tempfile.mkdtemp(prefix="laneb_csv_"))
try:
    p = tmp / "d.csv"
    p.write_text("a,b,label\n1.0,,0\n1.0,,0\n2.0,3.0,1\n4.0,5.0,1\n2.0,3.0,1\n4.0,5.0,0\n")
    from juniper_data.generators.csv_import.generator import CsvImportGenerator
    from juniper_data.generators.csv_import.params import CsvImportParams

    out = CsvImportGenerator.generate(CsvImportParams(file_path=str(p), target_column="label", seed=3))
    X = out["X_full"]
    print(f"   X_full =\n{X}")
    print(f"   NaN cells in X_full: {int(np.isnan(X).sum())}")
    r0, r1 = flat(X)[0], flat(X)[1]
    print(f"   rows 0 and 1 are the same source record shape [1.0, NaN]:")
    print(f"     np.array_equal(r0, r1)        : {np.array_equal(r0, r1)}      <- 'not duplicates'")
    print(f"     r0.tobytes() == r1.tobytes()  : {r0.tobytes() == r1.tobytes()}      <- 'duplicates'")
    print("   -> On real data the two candidate implementations of G-a disagree about whether")
    print("      a leaked row is a leak. The proposal does not say which one it means.")
except Exception as exc:  # noqa: BLE001
    print(f"   csv_import unavailable in this env: {type(exc).__name__}: {exc}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
