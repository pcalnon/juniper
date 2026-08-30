#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : cross-repo tooling (ad-hoc)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

V-1: does asking a juniper-data generator for N+M points preserve the first N?

WHY THIS MATTERS
The train/validation/test partition design
(notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md section 6.3)
records the owner's decision that the requested TRAINING count is honoured literally and the
validation/test partitions are generated as ADDITIONAL points -- e.g. train/val/test 100/40/30 at
N=1000 yields 1000/400/300. Its stated benefit is that `train` does not shrink, so **existing
baselines are preserved**: the only behavioural change would be that early stopping gains a
partition to consult.

That benefit holds only if a generator asked for N+M produces the SAME first N rows as one asked
for N. A purely sequential generator would. One that shuffles, normalises or class-balances over
the full requested set will not -- and then every existing baseline moves anyway, which changes
the migration story completely.

V-1 was raised as an explicit verification item rather than assumed. This script answers it.

WHAT IT COMPARES
For each generator: build params at a small N and a larger N with the SAME seed, generate both,
and compare the smaller run's arrays against the corresponding prefix of the larger run's. Reports
per-key equality for X_train/y_train and for X_full/y_full -- the full set can be prefix-stable
while the split is not, and that distinction is the whole point.

Usage
-----
    2026-08-30_v1_generator_prefix_check.py [--small N] [--large N]

Exit: 0 if every generator probed reported a verdict; 2 if none could be probed.
"""

from __future__ import annotations

import argparse
import importlib
import sys

import numpy as np

# (module path, params class, generator class, point-count kwarg, extra kwargs)
GENERATORS = [
    ("juniper_data.generators.spiral", "SpiralParams", "SpiralGenerator", "n_points_per_spiral", {}),
    ("juniper_data.generators.moon", "MoonParams", "MoonGenerator", "n_samples", {}),
    ("juniper_data.generators.xor", "XorParams", "XorGenerator", "n_points_per_quadrant", {}),
    ("juniper_data.generators.circles", "CirclesParams", "CirclesGenerator", "n_samples", {}),
    ("juniper_data.generators.checkerboard", "CheckerboardParams", "CheckerboardGenerator", "n_samples", {}),
    ("juniper_data.generators.gaussian", "GaussianParams", "GaussianGenerator", "n_samples_per_class", {}),
]

# The size kwarg differs per generator and the params models do NOT reject an unknown field --
# passing `n_samples` to xor or gaussian is silently ignored, both runs come out at the default
# size, and the comparison then reports PREFIX-STABLE from two IDENTICAL generations. That is a
# vacuous pass, and it is why `probe` below asserts the two runs actually differ in size before
# trusting a stable verdict.


def probe(mod_path: str, params_name: str, gen_name: str, count_kw: str, extra: dict, small: int, large: int) -> str:
    try:
        mod = importlib.import_module(mod_path)
    except Exception as exc:
        return f"SKIP import failed: {type(exc).__name__}: {exc}"
    params_cls = getattr(mod, params_name, None) or getattr(importlib.import_module(mod_path + ".params"), params_name, None)
    gen_cls = getattr(mod, gen_name, None) or getattr(importlib.import_module(mod_path + ".generator"), gen_name, None)
    if params_cls is None or gen_cls is None:
        return f"SKIP could not resolve {params_name}/{gen_name}"

    try:
        p_small = params_cls(**{count_kw: small, "seed": 42, **extra})
        p_large = params_cls(**{count_kw: large, "seed": 42, **extra})
        d_small = gen_cls.generate(p_small)
        d_large = gen_cls.generate(p_large)
    except Exception as exc:
        return f"SKIP generate failed: {type(exc).__name__}: {exc}"

    verdicts = []
    for key in ("X_full", "X_train"):
        a, b = d_small.get(key), d_large.get(key)
        if a is None or b is None:
            verdicts.append(f"{key}=absent")
            continue
        n = a.shape[0]
        if b.shape[0] < n:
            verdicts.append(f"{key}=larger-run-is-smaller({b.shape[0]}<{n})")
            continue
        if b.shape[0] == n:
            # The two runs produced the SAME size, so the size kwarg did not take effect and
            # this comparison is between two identical generations. Report it as untested rather
            # than as stability -- a pass that could not have failed is not evidence.
            verdicts.append(f"{key}=VACUOUS-same-size({n}); size kwarg had no effect")
            continue
        same = bool(np.array_equal(a, b[:n]))
        verdicts.append(f"{key}={'PREFIX-STABLE' if same else 'DIFFERS'}({n} vs {b.shape[0]})")
    return "  ".join(verdicts)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--small", type=int, default=500)
    ap.add_argument("--large", type=int, default=850)
    args = ap.parse_args(argv)

    print("# V-1: does generating the LARGER set preserve the smaller set's first N rows?")
    print(f"# small={args.small} large={args.large} seed=42 (same seed both runs)")
    print("# X_full  = the raw generated set before splitting")
    print("# X_train = the post-split training partition -- the one section 6.3's claim is about")
    print()
    probed = 0
    for mod_path, params_name, gen_name, count_kw, extra in GENERATORS:
        result = probe(mod_path, params_name, gen_name, count_kw, extra, args.small, args.large)
        if not result.startswith("SKIP"):
            probed += 1
        print(f"{mod_path.rsplit('.', 1)[-1]:<14} {result}")
    print()
    if probed == 0:
        print("no generator could be probed -- verdict is UNKNOWN, not 'stable'", file=sys.stderr)
        return 2
    print(f"# generators probed: {probed}/{len(GENERATORS)}")
    print("# A DIFFERS on X_train means section 6.3's 'train does not shrink, so baselines are")
    print("# preserved' does NOT hold for that generator: the rows change even at the same count.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
