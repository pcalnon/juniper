#!/usr/bin/env python
"""Lane B rig 7: xor's degenerate config, and G-a's unsatisfiable invariant.

Project:       Juniper
Sub-Project:   JuniperML
Application:   util/ad-hoc
Author:        Paul Calnon
Version:       0.7.1
License:       MIT License
"""

from __future__ import annotations

import hashlib

import numpy as np

import importlib
import os
import pathlib
import tempfile

# Load-bearing side effect, NOT an unused import. `juniper_data.generators.csv_import`
# cannot be imported directly -- it hits a circular import:
#   csv_import/__init__ -> ... -> api.routes.datasets -> api.routes.generators
#   -> csv_import (partially initialised) -> ImportError on VERSION.
# Importing the routes module first completes that cycle. Expressed as an explicit
# import_module() call rather than a bare `import ... # noqa: F401`, because the noqa
# hid it from flake8 but not from CodeQL, which correctly flagged an unused NAME.
importlib.import_module("juniper_data.api.routes.generators")

from juniper_data.generators.csv_import import CsvImportGenerator, CsvImportParams  # noqa: E402
from juniper_data.generators.xor.generator import XorGenerator
from juniper_data.generators.xor.params import XorParams


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
print("P. xor IS BREAKABLE TO FULLY SEED-INVARIANT AT A SCHEMA-VALID CONFIG")
print("=" * 96)
print("   XorParams.margin has `ge=MIN_MARGIN` and no constraint tying it to x_range/y_range,")
print("   so margin == x_range == y_range makes every rng.uniform(a, a) draw a constant.")
print()
print(f"   {'config':<38} | {'probe':>10} | {'distinct rows':>14} | {'G-a dupes val<-train':>21}")
print("   " + "-" * 92)
root = 12345
for label, kw in [
    ("default (margin=0.1, x_range=1.0)", {}),
    ("margin=1.0, x_range=1.0, y_range=1.0", {"margin": 1.0, "x_range": 1.0, "y_range": 1.0}),
    ("...same, noise=0.0 explicit", {"margin": 1.0, "x_range": 1.0, "y_range": 1.0, "noise": 0.0}),
]:
    a = XorGenerator.generate(XorParams(seed=11, **kw))["X_full"]
    b = XorGenerator.generate(XorParams(seed=22, **kw))["X_full"]
    v = "invariant" if a.tobytes() == b.tobytes() else "dependent"
    tr = XorGenerator.generate(XorParams(seed=substream_seed(root, "train"), **kw))["X_full"]
    va = XorGenerator.generate(XorParams(seed=substream_seed(root, "validation"), **kw))["X_full"]
    d = exact_dupes(tr, va)
    print(f"   {label:<38} | {v:>10} | {len({r.tobytes() for r in flat(a)}):>5} of {len(a):<5} | {d:>17}/{len(va)}")

print()
print("=" * 96)
print("Q. G-a's INVARIANT IS UNSATISFIABLE WHEN THE SOURCE HAS LEGITIMATE DUPLICATE ROWS")
print("=" * 96)
# Self-contained fixture: 6 records, 3 distinct feature vectors, multiplicities [2,2,2].
# Coinciding feature vectors are the NORMAL case for low-cardinality / categorical data,
# which is the whole point of this section. Written to a temp dir that
# JUNIPER_DATA_IMPORT_DIR points at, so the rig reproduces with no external setup.
_tmpdir = tempfile.mkdtemp(prefix="juniper_unsat_rig_")
pathlib.Path(_tmpdir, "d.csv").write_text("f0,f1,label\n1,1,0\n1,1,0\n2,2,1\n2,2,1\n3,3,0\n3,3,0\n", encoding="utf-8")
os.environ["JUNIPER_DATA_IMPORT_DIR"] = _tmpdir

out = CsvImportGenerator.generate(CsvImportParams(file_path="d.csv", target_column="label", seed=3))
X = np.ascontiguousarray(out["X_full"])
print(f"   csv_import pool (6 records, 3 distinct feature vectors):")
print(f"{X}")
uniq, counts = np.unique(flat(X), axis=0, return_counts=True)
print(f"   distinct feature rows: {len(uniq)} of {len(X)}; multiplicities {counts.tolist()}")
print()
print("   G-a requires 'zero exact duplicate rows between train and val/test'. Enumerating")
print("   every contiguous 4/1/1 partition of this pool:")
viol = 0
total = 0
for perm_seed in range(8):
    p = np.random.default_rng(perm_seed).permutation(len(X))
    tr, va, te = X[p[:4]], X[p[4:5]], X[p[5:6]]
    bad = exact_dupes(tr, va) + exact_dupes(tr, te)
    total += 1
    viol += bad > 0
    print(f"     shuffle seed {perm_seed}: duplicate rows in val/test that appear in train = {bad}")
print(f"   -> {viol}/{total} partitions violate G-a. The rows are genuinely distinct RECORDS;")
print("      only their feature vectors coincide. G-a would delete valid data (biasing the")
print("      sample) or refuse to assemble. Low-cardinality / categorical tabular data is the")
print("      normal case, not a corner case.")

print()
print("=" * 96)
print("R. THE ORDERING DEFECT -- the probe needs the artifact the strategy produces")
print("=" * 96)
print("   Design decision 6 (already ruled) makes X_full = concat(train, val, test), i.e.")
print("   X_full is a PRODUCT of the partition strategy. The proposal probes X_full to CHOOSE")
print("   the partition strategy. Concretely:")
print("     - probing 'X_full as the pre-P-1b single-call array'  measures a code path that,")
print("       once P-1b ships, no longer exists;")
print("     - probing 'X_full as concat(partitions)' requires running INDEPENDENT_SUBSTREAM")
print("       first, i.e. doing the thing the gate exists to authorise.")
print("   Section I of rig 3 shows the two readings already disagree for spiral and moon.")
