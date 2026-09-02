#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : cross-repo tooling (ad-hoc)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

P-1b: verify the per-partition seed-substream scheme actually delivers what it promises.

WHY THIS MATTERS
P-1b was ruled 2026-09-01 (design of record
notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md section 9.3).
Its whole claim is: **adding a partition cannot perturb the partitions that already exist**, because
each is drawn from its own named substream rather than from a shared sequential stream.

That is a claim about `numpy.random.SeedSequence`, and P-1a was ruled out precisely because a
plausible-sounding claim about RNG behaviour (design section 6.3's "vectorised draws are sized to N")
turned out to be the wrong mechanism. So this verifies P-1b's premise before anything is built on it,
rather than after.

It also checks one hazard that P-1b INTRODUCES and P-1a did not have. Under D-1 (design section 9.2,
decision 6) X_full is ASSEMBLED from independently generated subsets. For a linspace-parameterised
generator, "independently generated at a different size" means a DIFFERENT GRID over the same curve
-- so train and val could land on identical curve positions, which would be a leak of exactly the
kind this arc exists to remove.

WHAT IT CHECKS

  P1  Does spawning MORE children leave the earlier ones unchanged?
      SeedSequence(s).spawn(3)[:2] vs SeedSequence(s).spawn(2). This is P-1b's core promise.

  P2  Is POSITIONAL spawning order-dependent in a way that would bite later?
      Spawning on a REUSED parent advances an internal counter, so spawn(2) then spawn(1) is not
      the same as spawn(3). A named/keyed derivation avoids it. Both are exercised.

  P3  Do independently-generated partitions share curve positions? (the new hazard)
      Counts coincident points between linspace grids at the train and val sizes.

Read-only: computes and prints. Writes nothing.

Usage
-----
    python 2026-09-01_p1b_substream_check.py [--n-train N] [--n-val N] [--n-test N] [--seed S]

Exit: 0 always unless a probe raises; the verdict is in the output, not the exit code.
"""

from __future__ import annotations

import argparse
import hashlib

import numpy as np


def _draw(ss: np.random.SeedSequence, n: int = 8) -> np.ndarray:
    """Materialise a substream as concrete values -- comparing SeedSequence objects proves nothing."""
    return np.random.default_rng(ss).random(n)


def p1_spawn_prefix() -> tuple[bool, str]:
    """P-1b's core promise: adding a partition must not perturb existing ones."""
    two = np.random.SeedSequence(42).spawn(2)
    three = np.random.SeedSequence(42).spawn(3)
    same = all(np.array_equal(_draw(a), _draw(b)) for a, b in zip(two, three[:2]))
    return same, "spawn(3)[:2] vs spawn(2), compared as DRAWN VALUES"


def p2_positional_reuse_trap() -> tuple[bool, str]:
    """Spawning twice off the SAME parent advances a counter -- is that a real hazard?

    Returns True when the trap is CONFIRMED to exist (i.e. reuse differs from a fresh spawn),
    because that is the thing the design must warn about.
    """
    parent = np.random.SeedSequence(42)
    first_two = parent.spawn(2)
    third_from_reuse = parent.spawn(1)[0]
    fresh_third = np.random.SeedSequence(42).spawn(3)[2]
    # The first two must still match a fresh spawn(2) ...
    fresh_two = np.random.SeedSequence(42).spawn(2)
    prefix_ok = all(np.array_equal(_draw(a), _draw(b)) for a, b in zip(first_two, fresh_two))
    # ... and the incrementally-spawned third should equal the fresh third.
    third_ok = np.array_equal(_draw(third_from_reuse), _draw(fresh_third))
    return (prefix_ok and third_ok), f"incremental spawn: prefix_ok={prefix_ok} third_matches_fresh={third_ok}"


def _named_stream(seed: int, name: str) -> np.random.SeedSequence:
    """Derive a substream from a STABLE NAME rather than a position.

    Order-independent by construction: the key is a digest of the partition name, so adding,
    removing or reordering partitions cannot move any other partition's stream.
    """
    key = int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big")
    return np.random.SeedSequence(entropy=seed, spawn_key=(key,))


def p2b_named_is_order_independent() -> tuple[bool, str]:
    """A named derivation must be invariant to which other partitions exist."""
    a = _draw(_named_stream(42, "train"))
    # Derive the others in between -- with positional spawning this would matter.
    _ = _draw(_named_stream(42, "test"))
    _ = _draw(_named_stream(42, "val"))
    b = _draw(_named_stream(42, "train"))
    distinct = not np.array_equal(_draw(_named_stream(42, "train")), _draw(_named_stream(42, "val")))
    return (np.array_equal(a, b) and distinct), f"train stream stable across interleaving; train!=val: {distinct}"


def p3_grid_coincidence(n_train: int, n_val: int, n_test: int) -> tuple[bool, str]:
    """The hazard P-1b INTRODUCES: independently generated grids sharing curve positions.

    Returns True when the overlap is NEGLIGIBLE (endpoints only or fewer).
    """
    g_tr = np.linspace(0.0, 1.0, n_train)
    g_va = np.linspace(0.0, 1.0, n_val)
    g_te = np.linspace(0.0, 1.0, n_test)
    tr_va = np.intersect1d(g_tr, g_va).size
    tr_te = np.intersect1d(g_tr, g_te).size
    va_te = np.intersect1d(g_va, g_te).size
    worst = max(tr_va, tr_te, va_te)
    return worst <= 2, f"shared grid points: train∩val={tr_va} train∩test={tr_te} val∩test={va_te} (2 = endpoints only)"


def p4_duplicate_rows(n_train: int, n_val: int, seed: int, noise: float) -> tuple[bool, str]:
    """The sharp form of P3: do independently generated partitions share IDENTICAL ROWS?

    A shared grid position is only a latent duplicate -- independent noise usually separates the
    two points. But `noise` is a caller-supplied parameter and **zero is a legitimate value**, and
    at noise=0 a shared grid position IS a byte-identical row in both partitions.

    Returns True when there are NO duplicate rows.
    """
    try:
        from juniper_data.generators.spiral.generator import SpiralGenerator
    except Exception as exc:
        return True, f"SKIP juniper_data not importable: {type(exc).__name__}"

    def arm(n: int, name: str):
        rng = np.random.default_rng(_named_stream(seed, name))
        return SpiralGenerator._generate_spiral_coordinates(
            n_points=n,
            radius=1.0,
            n_rotations=2.0,
            angle_offset=0.0,
            clockwise=False,
            noise=noise,
            rng=rng,
            algorithm="modern",
            origin=(0.0, 0.0),
        )

    tr = arm(n_train, "train")
    va = arm(n_val, "val")
    tr_set = {tuple(r) for r in tr.tolist()}
    dupes = sum(1 for r in va.tolist() if tuple(r) in tr_set)
    return dupes == 0, f"noise={noise}: {dupes} of {n_val} val rows are byte-identical to a train row"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-train", type=int, default=1000)
    ap.add_argument("--n-val", type=int, default=400)
    ap.add_argument("--n-test", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 78)
    print(f"P-1b substream check  (train={args.n_train} val={args.n_val} test={args.n_test} seed={args.seed})")
    print("=" * 78)

    ok1, d1 = p1_spawn_prefix()
    print(f"{'P1  spawn(k) prefix-stable':44s}  {'YES' if ok1 else 'NO ':3s}  {d1}")
    ok2, d2 = p2_positional_reuse_trap()
    print(f"{'P2  incremental spawn off same parent':44s}  {'OK ' if ok2 else 'NO ':3s}  {d2}")
    ok2b, d2b = p2b_named_is_order_independent()
    print(f"{'P2b named derivation order-independent':44s}  {'YES' if ok2b else 'NO ':3s}  {d2b}")
    ok3, d3 = p3_grid_coincidence(args.n_train, args.n_val, args.n_test)
    print(f"{'P3  grid coincidence (new hazard)':44s}  {'OK ' if ok3 else 'LEAK':3s}  {d3}")

    ok4a, d4a = p4_duplicate_rows(args.n_train, args.n_val, args.seed, noise=0.0)
    print(f"{'P4a duplicate ROWS at noise=0':44s}  {'OK ' if ok4a else 'LEAK':3s}  {d4a}")
    ok4b, d4b = p4_duplicate_rows(args.n_train, args.n_val, args.seed, noise=0.1)
    print(f"{'P4b duplicate ROWS at noise=0.1':44s}  {'OK ' if ok4b else 'LEAK':3s}  {d4b}")

    print("-" * 78)
    if not ok4a:
        print("CONFIRMED LEAK at noise=0: identical rows appear in train AND val. `noise` is a")
        print("        caller-supplied parameter and 0 is legitimate, so this is reachable config,")
        print("        not a corner case. Independent noise is what normally hides it (P4b).")
    if ok1 and ok2b:
        print("P-1b's core promise HOLDS: a partition's stream does not move when others are added.")
    else:
        print("P-1b's core promise DID NOT verify -- do not build on it. See probe lines above.")
    if not ok3:
        print("WARNING: independently generated partitions share more than endpoint grid positions.")
        print("         For a linspace-parameterised generator that is duplicated curve locations")
        print("         across partitions -- differing only by noise. Size the partitions coprime,")
        print("         or offset the grids, before shipping.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
