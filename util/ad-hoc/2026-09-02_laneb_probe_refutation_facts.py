#!/usr/bin/env python
"""Lane B rig 4: re-probe the brief's ESTABLISHED FACTS, and hunt a coin-flip verdict.

Project:       Juniper
Sub-Project:   JuniperML
Application:   util/ad-hoc
Author:        Paul Calnon
Version:       0.7.1
License:       MIT License
"""

from __future__ import annotations

import numpy as np

from juniper_data.generators.gaussian.generator import GaussianGenerator
from juniper_data.generators.gaussian.params import GaussianParams
from juniper_data.generators.mackey_glass.generator import MackeyGlassGenerator
from juniper_data.generators.mackey_glass.params import MackeyGlassParams
from juniper_data.generators.spiral.generator import SpiralGenerator
from juniper_data.generators.spiral.params import SpiralParams

rng = np.random.default_rng(0)
PAIRS = [(int(a), int(b)) for a, b in rng.integers(0, 10**6, size=(60, 2))]


def frac_dependent(fn):
    dep = 0
    for a, b in PAIRS:
        if fn(a).tobytes() != fn(b).tobytes():
            dep += 1
    return dep


print("=" * 92)
print("K. RE-PROBE OF AN 'ESTABLISHED FACT': gaussian at class_std <= 1e-8")
print("=" * 92)
print("   The brief states gaussian is 'breakable to seed-invariant at class_std<=1e-8,")
print("   a broad regime'. Measured (noise=0.0, all other defaults, probing X_full):")
print()
print(f"   {'class_std':>12} | {'seed pairs reading dependent':>29} | verdict")
print("   " + "-" * 62)
for cs in (1e-4, 1e-6, 1e-7, 1e-8, 1e-9, 1e-10, 1e-12, 1e-15, 1e-20):
    d = frac_dependent(lambda s, cs=cs: GaussianGenerator.generate(GaussianParams(class_std=cs, noise=0.0, seed=s))["X_full"])
    tag = "invariant" if d == 0 else ("dependent" if d == len(PAIRS) else ">>> COIN FLIP <<<")
    print(f"   {cs:>12.0e} | {d:>26}/{len(PAIRS)} | {tag}")
g = GaussianGenerator.generate(GaussianParams(class_std=1e-8, noise=0.0, seed=1))["X_full"]
print(f"\n   (gaussian default center_radius puts points at |x| ~ {np.abs(g).max():.2f}; "
      f"float32 ulp there is ~{np.spacing(np.float32(np.abs(g).max())):.2e},")
print("    which is why 1e-8 still moves bits near the smaller coordinates.)")

print()
print("=" * 92)
print("L. HUNTING A NON-DETERMINISTIC VERDICT (the 'sample of size two' attack)")
print("=" * 92)
print("   mackey_glass, probing X_full, 60 random seed pairs per row:")
print()
print(f"   {'init_noise_std':>15} | {'pairs reading dependent':>24} | verdict")
print("   " + "-" * 60)
for std in (1e-13, 3e-14, 1e-14, 3e-15, 1e-15, 3e-16, 1e-16, 1e-17):
    d = frac_dependent(lambda s, std=std: MackeyGlassGenerator.generate(MackeyGlassParams(init_noise_std=std, seed=s, n_steps=600))["X_full"])
    tag = "invariant" if d == 0 else ("dependent" if d == len(PAIRS) else ">>> COIN FLIP <<<")
    print(f"   {std:>15.0e} | {d:>21}/{len(PAIRS)} | {tag}")

print()
print("   spiral, probing X_full (n_spirals=2, n_points=200):")
print()
print(f"   {'noise':>15} | {'pairs reading dependent':>24} | verdict")
print("   " + "-" * 60)
for nz in (1e-9, 3e-10, 1e-10, 3e-11, 1e-11, 1e-12, 1e-13):
    d = frac_dependent(lambda s, nz=nz: SpiralGenerator.generate(SpiralParams(n_spirals=2, n_points_per_spiral=200, noise=nz, seed=s))["X_full"])
    tag = "invariant" if d == 0 else ("dependent" if d == len(PAIRS) else ">>> COIN FLIP <<<")
    print(f"   {nz:>15.0e} | {d:>21}/{len(PAIRS)} | {tag}")

print()
print("=" * 92)
print("M. DO -0.0 / NaN ACTUALLY OCCUR IN GENERATOR OUTPUT?  (checking my own claim)")
print("=" * 92)
checks = {
    "spiral clockwise=True": SpiralGenerator.generate(SpiralParams(n_spirals=3, noise=0.0, seed=1, clockwise=True))["X_full"],
    "spiral clockwise=False": SpiralGenerator.generate(SpiralParams(n_spirals=3, noise=0.0, seed=1, clockwise=False))["X_full"],
    "spiral legacy_cascor": SpiralGenerator.generate(SpiralParams(noise=0.0, seed=1, algorithm="legacy_cascor"))["X_full"],
    "gaussian class_std=1e-20": GaussianGenerator.generate(GaussianParams(class_std=1e-20, noise=0.0, seed=1))["X_full"],
}
for label, arr in checks.items():
    neg_zero = int(((arr == 0.0) & np.signbit(arr)).sum())
    nans = int(np.isnan(arr).sum())
    print(f"   {label:<26} -0.0 cells: {neg_zero:>5}   NaN cells: {nans:>5}")
