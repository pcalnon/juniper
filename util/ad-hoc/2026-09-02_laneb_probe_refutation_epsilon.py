#!/usr/bin/env python
"""Lane B refutation rig 2: the exact-byte discriminator is a knife-edge.

Project:       Juniper
Sub-Project:   JuniperML
Application:   util/ad-hoc
Author:        Paul Calnon
Version:       0.7.1
License:       MIT License

Shows that (a) the probe's verdict is a function of the two seed constants it
happens to use, and (b) an arbitrarily small, schema-valid noise value flips the
probe to "dependent" and G-a to "0 duplicates" while leaving the leak intact.
"""

from __future__ import annotations

import hashlib

import numpy as np

from juniper_data.generators.mackey_glass.generator import MackeyGlassGenerator
from juniper_data.generators.mackey_glass.params import MackeyGlassParams
from juniper_data.generators.spiral.generator import SpiralGenerator
from juniper_data.generators.spiral.params import SpiralParams


def name_key(name: str) -> int:
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big")


def substream_seed(root_seed: int, name: str) -> int:
    ss = np.random.SeedSequence(entropy=root_seed, spawn_key=(name_key(name),))
    return int(ss.generate_state(1, dtype=np.uint32)[0])


def exact_dupes(A, B):
    if A.size == 0 or B.size == 0:
        return 0
    sa = {r.tobytes() for r in np.ascontiguousarray(A.reshape(len(A), -1))}
    return sum(1 for r in np.ascontiguousarray(B.reshape(len(B), -1)) if r.tobytes() in sa)


def nn_distance(A, B):
    """Max-over-B of the min-over-A Chebyshev distance -- i.e. how far the WORST
    validation row is from its nearest training row. Small => every val row has a
    near-twin in train."""
    Af = A.reshape(len(A), -1).astype(np.float64)
    Bf = B.reshape(len(B), -1).astype(np.float64)
    out = np.empty(len(Bf))
    for i, b in enumerate(Bf):
        out[i] = np.abs(Af - b).max(axis=1).min()
    return out


def spiral_full(noise, seed, n=200):
    return SpiralGenerator.generate(SpiralParams(n_spirals=2, n_points_per_spiral=n, noise=noise, seed=seed))["X_full"]


def mg_full(std, seed, n_steps=600):
    return MackeyGlassGenerator.generate(MackeyGlassParams(init_noise_std=std, seed=seed, n_steps=n_steps))["X_full"]


print("=" * 90)
print("E. THE PROBE'S VERDICT DEPENDS ON WHICH TWO SEEDS IT PICKS")
print("=" * 90)
print("   spiral(n_spirals=2, n_points=200, noise=eps)  -- probing X_full, 40 random seed pairs")
print()
print(f"   {'noise':>12} | {'pairs reading dependent':>24} | verdict is")
print("   " + "-" * 62)
rng = np.random.default_rng(0)
pairs = [(int(a), int(b)) for a, b in rng.integers(0, 10**6, size=(40, 2))]
for noise in (0.0, 1e-9, 3e-9, 1e-8, 3e-8, 1e-7, 1e-6):
    dep = 0
    for a, b in pairs:
        if spiral_full(noise, a).tobytes() != spiral_full(noise, b).tobytes():
            dep += 1
    label = "STABLE (invariant)" if dep == 0 else ("STABLE (dependent)" if dep == len(pairs) else ">>> A COIN FLIP <<<")
    print(f"   {noise:>12.0e} | {dep:>21}/40 | {label}")

print()
print("=" * 90)
print("F. AN EPSILON DEFEATS BOTH THE PROBE AND G-a WHILE THE LEAK SURVIVES")
print("=" * 90)
print("   spiral: train and val generated from independent name-keyed substreams (P-1b)")
print()
print(f"   {'noise':>10} | {'probe':>10} | {'G-a exact dupes':>16} | {'val rows within 1e-4 of a train row':>36}")
print("   " + "-" * 84)
root = 12345
for noise in (0.0, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 0.1):
    verdict = "invariant" if spiral_full(noise, 11).tobytes() == spiral_full(noise, 22).tobytes() else "dependent"
    tr = spiral_full(noise, substream_seed(root, "train"), n=200)
    va = spiral_full(noise, substream_seed(root, "validation"), n=80)
    d = exact_dupes(tr, va)
    nn = nn_distance(tr, va)
    near = int((nn < 1e-4).sum())
    print(f"   {noise:>10.0e} | {verdict:>10} | {d:>13}/{len(va):<3} | {near:>8}/{len(va)}   (min nn dist {nn.min():.2e})")

print()
print("=" * 90)
print("G. MACKEY_GLASS -- the generator that DECIDED the G-a ruling")
print("=" * 90)
print("   init_noise_std has `ge=0` and NO positive lower bound (params.py:33).")
print()
print(f"   {'init_noise_std':>15} | {'probe':>10} | {'G-a exact dupes (val<-train)':>29} | {'worst val row nn-dist to train':>31}")
print("   " + "-" * 96)
for std in (0.0, 1e-12, 1e-10, 1e-9, 1e-8, 1e-6, 1e-3):
    verdict = "invariant" if mg_full(std, 11).tobytes() == mg_full(std, 22).tobytes() else "dependent"
    tr = mg_full(std, substream_seed(root, "train"))
    va = mg_full(std, substream_seed(root, "validation"))
    d = exact_dupes(tr, va)
    nn = nn_distance(tr, va)
    print(f"   {std:>15.0e} | {verdict:>10} | {d:>25}/{len(va):<3} | {nn.max():.3e}")

print()
print("   For scale: the signal itself spans")
sig = mg_full(0.0, 0)
print(f"     X_full range = [{sig.min():.4f}, {sig.max():.4f}]  (span {sig.max() - sig.min():.4f})")
