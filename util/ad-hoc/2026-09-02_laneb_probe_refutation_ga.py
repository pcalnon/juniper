#!/usr/bin/env python
"""Lane B refutation rig 3: G-a's loop, float semantics, and which array to probe.

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

from juniper_data.generators.checkerboard.generator import CheckerboardGenerator
from juniper_data.generators.checkerboard.params import CheckerboardParams
from juniper_data.generators.circles.generator import CirclesGenerator
from juniper_data.generators.circles.params import CirclesParams
from juniper_data.generators.gaussian.generator import GaussianGenerator
from juniper_data.generators.gaussian.params import GaussianParams
from juniper_data.generators.mackey_glass.generator import MackeyGlassGenerator
from juniper_data.generators.mackey_glass.params import MackeyGlassParams
from juniper_data.generators.moon.generator import MoonGenerator
from juniper_data.generators.moon.params import MoonParams
from juniper_data.generators.spiral.generator import SpiralGenerator
from juniper_data.generators.spiral.params import SpiralParams
from juniper_data.generators.xor.generator import XorGenerator
from juniper_data.generators.xor.params import XorParams


def name_key(name):
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big")


def substream_seed(root, name):
    return int(np.random.SeedSequence(entropy=root, spawn_key=(name_key(name),)).generate_state(1, dtype=np.uint32)[0])


def flat(a):
    return np.ascontiguousarray(a.reshape(len(a), -1))


def dupe_mask(train, cand):
    s = {r.tobytes() for r in flat(train)}
    return np.array([r.tobytes() in s for r in flat(cand)])


print("=" * 92)
print("H. G-a 'de-duplicate at assembly, then top up' -- does the loop terminate?")
print("=" * 92)
print("   mackey_glass at its DEFAULT init_noise_std=0.0 (the census' 368/368 case).")
print("   G-a: drop val rows that appear in train, regenerate to top back up, repeat.")
print()

root = 12345
tr = MackeyGlassGenerator.generate(MackeyGlassParams(seed=substream_seed(root, "train"), n_steps=600))["X_full"]
target = 200
attempt_seed = substream_seed(root, "validation")
kept = np.zeros((0,) + tr.shape[1:], dtype=tr.dtype)
for it in range(1, 9):
    cand = MackeyGlassGenerator.generate(MackeyGlassParams(seed=attempt_seed + it, n_steps=600))["X_full"]
    m = dupe_mask(tr, cand)
    fresh = cand[~m]
    kept = np.concatenate([kept, fresh]) if len(fresh) else kept
    print(f"   top-up round {it}: generated {len(cand):4d} rows, {int(m.sum()):4d} were duplicates of train, "
          f"{len(fresh):3d} fresh  -> val has {len(kept)}/{target}")
    if len(kept) >= target:
        break
print("   ...the seed is inert, so every round returns the identical trajectory.")
print("   G-a either LOOPS FOREVER or emits an EMPTY validation partition.")
print("   Note: 9.3.4 ruled G-b unsound *because* it could not fix mackey_glass. Neither can G-a.")

print()
print("=" * 92)
print("I. WHICH ARRAY DO YOU PROBE?  The verdict is not a property of the run.")
print("=" * 92)
cases = [
    ("spiral noise=0 modern", lambda s: SpiralGenerator.generate(SpiralParams(noise=0.0, seed=s, algorithm="modern"))),
    ("spiral noise=0 legacy", lambda s: SpiralGenerator.generate(SpiralParams(noise=0.0, seed=s, algorithm="legacy_cascor"))),
    ("moon noise=0", lambda s: MoonGenerator.generate(MoonParams(noise=0.0, seed=s))),
    ("gaussian class_std=1e-8", lambda s: GaussianGenerator.generate(GaussianParams(class_std=1e-8, noise=0.0, seed=s))),
    ("xor noise=0", lambda s: XorGenerator.generate(XorParams(noise=0.0, seed=s))),
    ("checkerboard noise=0", lambda s: CheckerboardGenerator.generate(CheckerboardParams(noise=0.0, seed=s))),
    ("circles noise=0", lambda s: CirclesGenerator.generate(CirclesParams(noise=0.0, seed=s))),
]
print(f"   {'config':<26} | {'probe X_full':>13} | {'probe X_train':>14} | agree?")
print("   " + "-" * 74)
for label, f in cases:
    try:
        a, b = f(11), f(22)
    except Exception as exc:  # noqa: BLE001
        print(f"   {label:<26} | {type(exc).__name__}: {exc}")
        continue
    vf = "invariant" if a["X_full"].tobytes() == b["X_full"].tobytes() else "dependent"
    vt = "invariant" if a["X_train"].tobytes() == b["X_train"].tobytes() else "dependent"
    print(f"   {label:<26} | {vf:>13} | {vt:>14} | {'yes' if vf == vt else '>>> NO <<<'}")

print()
print("=" * 92)
print("J. FLOAT SEMANTICS -- tobytes() and np.array_equal disagree on real generator output")
print("=" * 92)
sp = SpiralGenerator.generate(SpiralParams(n_spirals=3, n_points_per_spiral=50, noise=0.0, seed=1))["X_full"]
print(f"   spiral(n_spirals=3, noise=0) X_full: the 3 arms all start at the origin.")
origin_rows = sp[[0, 50, 100]]
print(f"   rows 0 / 50 / 100 = {origin_rows.tolist()}")
print(f"   np.array_equal(row0, row50)          : {np.array_equal(origin_rows[0], origin_rows[1])}")
print(f"   row0.tobytes() == row50.tobytes()    : {origin_rows[0].tobytes() == origin_rows[1].tobytes()}")
print(f"   signbits row0 / row50                : "
      f"{np.signbit(origin_rows[0]).tolist()} / {np.signbit(origin_rows[1]).tolist()}")
n_unique_bytes = len({r.tobytes() for r in flat(sp)})
print(f"   distinct rows by tobytes()           : {n_unique_bytes} of {len(sp)}")
print()
print("   The two candidate implementations of 'exact duplicate row' therefore give")
print("   different duplicate counts on the SAME array. Demonstration on a minimal case:")
z = np.array([[0.0, 1.0], [-0.0, 1.0]], dtype=np.float32)
n = np.array([[np.nan, 1.0], [np.nan, 1.0]], dtype=np.float32)
print(f"     [0.0,1] vs [-0.0,1] : array_equal={np.array_equal(z[0], z[1])}  tobytes_equal={z[0].tobytes() == z[1].tobytes()}")
print(f"     [nan,1] vs [nan,1]  : array_equal={np.array_equal(n[0], n[1])}  tobytes_equal={n[0].tobytes() == n[1].tobytes()}")
print("   -> -0.0 is a duplicate under array_equal and NOT under tobytes();")
print("      NaN is a duplicate under tobytes() and NOT under array_equal.")
print("   The proposal specifies neither, and 'zero exact duplicate rows' has two answers.")
