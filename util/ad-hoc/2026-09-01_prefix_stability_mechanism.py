#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : cross-repo tooling (ad-hoc)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

P-1: WHY are juniper-data generators not prefix-stable? Decomposes V-1's finding.

WHY THIS MATTERS
The 2026-08-31 D-1 ruling (design section 9.2, decision 6) wants a shared seed to permit dataset
comparison across snapshots. D-2 (decision 8) makes adding the third partition an ask for N+M rows
instead of N. V-1 measured that all six cascor-relevant generators return DIFFERENT rows in that
case, so the ruling's own goal is unreachable as things stand (design section 9.3).

Two ways out are on the table and NEITHER IS RULED:

  P-1a  prefix-stable generation -- guarantee generate(N+M)[:N] == generate(N). Preserves the
        existing corpus.
  P-1b  per-partition seed substreams -- each partition drawn from its own named stream, so adding
        one cannot perturb the others. Structural, but does NOT preserve the corpus.

**P-1a's feasibility is an empirical question, and it is the question this script answers.**
Design section 6.3 named two mechanisms for V-1's result: (1) `shuffle_and_split` permutes the full
set, and (2) "the raw generation itself is not prefix-stable ... vectorised draws are sized to N".
Mechanism 2 as stated would make P-1a require changing the NUMERICS of every generator. But there
is a third candidate the design did not separate out: the generators are STRATIFIED -- spiral
vstacks per-arm blocks, gaussian per-class blocks -- so changing N changes every stratum's size AND
the concatenation layout, which would break the prefix even if every draw were perfectly
prefix-stable.

Those two diagnoses imply very different costs, so this separates them.

WHAT IT MEASURES -- four independent probes, each falsifiable on its own

  Q1  Is numpy itself prefix-stable? fresh rng, `normal(size=N+M)[:N]` vs `normal(size=N)`.
      If FALSE, P-1a is blocked at the numerics layer and nothing above matters.

  Q2  Is ONE stratum prefix-stable? A single spiral arm at n=small vs n=large, each with a FRESH
      rng, comparing the first `small` rows. Isolates per-stratum generation from layout.

  Q3  Does the shared RNG couple the strata? Arm 0 drawn at `large` then arm 1, vs arm 0 at `small`
      then arm 1 -- compare arm 1's prefix. This is the sequential-stream-shift mechanism.

  Q4  Does the stratified LAYOUT break the prefix on its own? Compare X_full[:small*n_arms] against
      the small run, given what Q2/Q3 established.

READING THE RESULT
  Q1 TRUE, Q2 TRUE  -> the numerics are fine; the breakage is layout/coupling, so P-1a is a
                       RESTRUCTURING (fixed per-stratum sizes + independent substreams + append),
                       not a rewrite of the draws. Note that such a restructuring is essentially
                       P-1b applied per stratum.
  Q1 FALSE or Q2 FALSE -> P-1a needs the draws themselves changed. Expensive; P-1b is the
                       pragmatic choice.

This script is READ-ONLY: it imports generators and compares arrays. It writes nothing.

Usage
-----
    /opt/miniforge3/envs/JuniperData/bin/python 2026-09-01_prefix_stability_mechanism.py \
        [--small N] [--large N] [--seed S]

Exit: 0 if every probe returned a verdict; 2 if the generators could not be imported.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np


def _eq(a: np.ndarray, b: np.ndarray) -> bool:
    return a.shape == b.shape and bool(np.array_equal(a, b))


def q1_numpy_prefix(small: int, large: int, seed: int) -> tuple[bool, str]:
    """Is a plain vectorised numpy draw prefix-stable across sizes?"""
    if large <= small:
        return False, "VACUOUS: large <= small"
    a = np.random.default_rng(seed).normal(size=large)[:small]
    b = np.random.default_rng(seed).normal(size=small)
    ok = _eq(a, b)
    # Guard against a vacuous TRUE from two identical-size draws.
    detail = f"normal(size={large})[:{small}] vs normal(size={small})"
    return ok, detail


def q1b_numpy_prefix_uniform(small: int, large: int, seed: int) -> tuple[bool, str]:
    """Same question for `uniform`/`random`, which some generators use instead."""
    a = np.random.default_rng(seed).random(size=large)[:small]
    b = np.random.default_rng(seed).random(size=small)
    return _eq(a, b), f"random(size={large})[:{small}] vs random(size={small})"


def _spiral_arm(n_points: int, seed: int, angle_offset: float = 0.0):
    """One spiral arm with a FRESH rng -- isolates per-stratum generation."""
    from juniper_data.generators.spiral.generator import SpiralGenerator

    rng = np.random.default_rng(seed)
    return SpiralGenerator._generate_spiral_coordinates(
        n_points=n_points,
        radius=1.0,
        n_rotations=2.0,
        angle_offset=angle_offset,
        clockwise=False,
        noise=0.1,
        rng=rng,
        algorithm="modern",
        origin=(0.0, 0.0),
    )


def q2_single_stratum(small: int, large: int, seed: int) -> tuple[bool, str]:
    """Is ONE spiral arm prefix-stable when each run gets its own fresh rng?"""
    a = _spiral_arm(large, seed)[:small]
    b = _spiral_arm(small, seed)
    if a.shape != b.shape:
        return False, f"shape mismatch {a.shape} vs {b.shape}"
    return _eq(a, b), f"arm(n={large})[:{small}] vs arm(n={small}), fresh rng each"


def q3_shared_rng_coupling(small: int, large: int, seed: int) -> tuple[bool, str]:
    """Does arm 0's size shift arm 1's stream, when the rng is SHARED across arms?

    Mirrors the real generator: one rng threaded through every arm in sequence.
    """
    from juniper_data.generators.spiral.generator import SpiralGenerator

    def two_arms(n: int):
        rng = np.random.default_rng(seed)
        arms = []
        for i in range(2):
            arms.append(
                SpiralGenerator._generate_spiral_coordinates(
                    n_points=n,
                    radius=1.0,
                    n_rotations=2.0,
                    angle_offset=2 * np.pi * i / 2,
                    clockwise=False,
                    noise=0.1,
                    rng=rng,
                    algorithm="modern",
                    origin=(0.0, 0.0),
                )
            )
        return arms

    big = two_arms(large)
    lil = two_arms(small)
    arm1_stable = _eq(big[1][:small], lil[1])
    # Report the INDEPENDENT question: is arm 1 still prefix-stable once arm 0 grew?
    return arm1_stable, f"arm1 prefix under shared rng, arm0 at {large} vs {small}"


def q4_layout(small: int, large: int, seed: int) -> tuple[bool, str]:
    """Does the vstack layout break the prefix at the X_full level?"""
    from juniper_data.generators.spiral.generator import SpiralGenerator
    from juniper_data.generators.spiral.params import SpiralParams

    d_small = SpiralGenerator.generate(SpiralParams(n_points_per_spiral=small, seed=seed))
    d_large = SpiralGenerator.generate(SpiralParams(n_points_per_spiral=large, seed=seed))
    xs, xl = d_small["X_full"], d_large["X_full"]
    if xs.shape[0] == xl.shape[0]:
        return False, f"VACUOUS: both runs produced {xs.shape[0]} rows -- size kwarg had no effect"
    ok = _eq(xl[: xs.shape[0]], xs)
    return ok, f"X_full[:{xs.shape[0]}] of n_per_spiral={large} vs n_per_spiral={small}"


def q5_algorithm_discriminator(small: int, large: int, seed: int) -> tuple[bool, str]:
    """Is prefix-stability ALGORITHM-dependent within a single generator?

    spiral's `modern` path builds geometry with `np.linspace(0, radius, n_points)` -- a
    DETERMINISTIC function of n_points, so a larger N resamples the whole curve more densely and
    shares no prefix. Its `legacy_cascor` path instead draws `sqrt(rng.random(n_points))`, a pure
    vectorised RNG draw, which Q1b shows IS prefix-stable.

    If this comes back STABLE, the obstacle is not "generation" in general -- it is specifically
    parametric-curve sampling, and the fix is per-generator rather than fleet-wide.
    """
    from juniper_data.generators.spiral.generator import SpiralGenerator

    def arm(n: int):
        rng = np.random.default_rng(seed)
        return SpiralGenerator._generate_spiral_coordinates(
            n_points=n,
            radius=1.0,
            n_rotations=2.0,
            angle_offset=0.0,
            clockwise=False,
            noise=0.1,
            rng=rng,
            algorithm="legacy_cascor",
            origin=(0.0, 0.0),
        )

    a = arm(large)[:small]
    b = arm(small)
    return _eq(a, b), f"legacy_cascor arm(n={large})[:{small}] vs arm(n={small})"


def q6_linspace_isolation(small: int, large: int, seed: int) -> tuple[bool, str]:
    """Mechanism A in one line, with no juniper-data code involved."""
    a = np.linspace(0.0, 1.0, large)[:small]
    b = np.linspace(0.0, 1.0, small)
    return _eq(a, b), f"linspace(0,1,{large})[:{small}] vs linspace(0,1,{small})"


def q7_sequential_draw_offset(small: int, large: int, seed: int) -> tuple[bool, str]:
    """Mechanism B in one line: the SECOND of two N-sized draws off one rng.

    Q5 refuted the guess that spiral's RNG-drawn `legacy_cascor` path would be prefix-stable.
    This isolates why: a generator that makes k draws each sized N has draw #2 begin at stream
    position N, so changing N moves it. Draw #1 is prefix-stable (Q1b); draw #2 is not.

    This is independent of Mechanism A -- it bites even with no linspace anywhere.
    """
    def second_draw(n: int):
        rng = np.random.default_rng(seed)
        rng.random(n)  # draw #1 -- consumes n values
        return rng.random(n)  # draw #2 -- starts at stream position n

    a = second_draw(large)[:small]
    b = second_draw(small)
    return _eq(a, b), f"2nd of two random(n) draws, n={large} vs {small}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--small", type=int, default=500)
    ap.add_argument("--large", type=int, default=850)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    try:
        import juniper_data  # noqa: F401
    except Exception as exc:
        print(f"juniper_data not importable: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("run with /opt/miniforge3/envs/JuniperData/bin/python", file=sys.stderr)
        return 2

    print("=" * 78)
    print(f"P-1 prefix-stability mechanism  (small={args.small} large={args.large} seed={args.seed})")
    print("=" * 78)

    probes = [
        ("Q1  numpy normal() prefix-stable?", q1_numpy_prefix),
        ("Q1b numpy random() prefix-stable?", q1b_numpy_prefix_uniform),
        ("Q2  ONE spiral arm, fresh rng", q2_single_stratum),
        ("Q3  arm1 prefix under SHARED rng", q3_shared_rng_coupling),
        ("Q4  X_full under stratified vstack", q4_layout),
        ("Q5  spiral legacy_cascor (RNG-drawn)", q5_algorithm_discriminator),
        ("Q6  bare np.linspace [mech A]", q6_linspace_isolation),
        ("Q7  2nd of two n-sized draws [mech B]", q7_sequential_draw_offset),
    ]

    results = {}
    for label, fn in probes:
        try:
            ok, detail = fn(args.small, args.large, args.seed)
        except Exception as exc:
            print(f"{label:38s}  ERROR  {type(exc).__name__}: {exc}")
            results[label] = None
            continue
        verdict = "STABLE " if ok else "DIFFERS"
        print(f"{label:38s}  {verdict}  {detail}")
        results[label] = ok

    print("-" * 78)
    q1 = results.get("Q1  numpy normal() prefix-stable?")
    q1b = results.get("Q1b numpy random() prefix-stable?")
    q6 = results.get("Q6  bare np.linspace [mech A]")
    q7 = results.get("Q7  2nd of two n-sized draws [mech B]")

    if None in (q1, q1b, q6, q7):
        print("READING: inconclusive -- a probe errored. Do not rule on this output.")
        return 0

    if q1 and q1b and not q6 and not q7:
        print("READING: numpy is NOT the problem. TWO INDEPENDENT mechanisms are, and both bite.")
        print()
        print("  Mechanism A -- parametric-curve sampling (Q6, and Q2 in situ).")
        print("    `np.linspace(0,r,N)` spacing is a function of N, so a larger N RESAMPLES the")
        print("    whole curve more densely rather than extending it. spiral's default `modern`")
        print("    path is built on it. NOT FIXABLE without redefining the dataset: making")
        print("    arm(N+M)[:N] == arm(N) needs FIXED-DENSITY sampling, so the extra points extend")
        print("    the curve -- a LONGER spiral, i.e. a different dataset, not the same one.")
        print()
        print("  Mechanism B -- sequential multi-draw offset (Q7, and Q5 in situ).")
        print("    A generator making k draws each sized N has draw #2 begin at stream position N,")
        print("    so changing N moves it. Draw #1 is prefix-stable; draw #2 is not. This is why")
        print("    spiral's pure-RNG `legacy_cascor` path ALSO differs (Q5) -- it draws distance,")
        print("    then x-noise, then y-noise off one rng. Fixable in principle (per-draw")
        print("    substreams, or one max-sized draw), but that is surgery on every generator.")
        print()
        print("CONSEQUENCE FOR THE P-1a / P-1b RULING:")
        print("  P-1a is blocked. Mechanism B is merely expensive; Mechanism A is SEMANTIC -- for")
        print("  every linspace-parameterised generator, 'the same dataset with more rows' is not")
        print("  a thing that exists. P-1b (per-partition seed substreams) sidesteps both, because")
        print("  each partition is generated at its own size and never claims to be a prefix of")
        print("  another. It does not preserve the existing corpus -- but per V-1 nothing does.")
    else:
        print("READING: mixed result -- see the per-probe lines above and do not summarise from")
        print("         this banner alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
