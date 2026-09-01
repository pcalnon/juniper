#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : cross-repo tooling (ad-hoc)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Which CLASS-1 generators actually leak under P-1b? Sizes the G-a / G-b / G-c guard choice.

WHY THIS MATTERS
Section 9.3.2 of the design of record
(notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md) records that P-1b
reintroduces a leak: independently generating partitions at different sizes gives a different grid
over the same curve, and grids can coincide. Measured on `spiral`, that was 4 of 400 val rows
byte-identical to a train row at noise=0.

Three guards are specified there and NONE is ruled:

  G-a  de-duplicate at assembly     -- generator-independent; costs an exact-match pass
  G-b  offset the grid per partition -- cheap and exact, but PER-GENERATOR and only helps
                                        the mechanism-A (linspace-parameterised) generators
  G-c  constrain sizes to be pairwise coprime -- cheapest, still leaves the endpoints

**The choice turns on how many class-1 generators actually leak**, and that was never measured:
section 9.3.1 classified only 3 of 17 by reading source, and the class-1 list in section 9.3.3 is
by EXCLUSION. If only `spiral` and `moon` leak, G-b is viable. If the leak is broader -- or shows
up in a generator that is not linspace-parameterised at all -- then G-b is unsound and G-a is
required.

Inferring this from `grep linspace` is exactly the mistake this arc keeps making: checking an
artifact ADJACENT to the one that could falsify the claim. So this generates and compares actual
rows.

WHAT IT DOES
For each class-1 generator: generate a `train` partition and a `val` partition INDEPENDENTLY, each
from its own name-keyed seed substream (the P-1b scheme from section 9.3.2), at different sizes, and
count how many val rows are byte-identical to a train row. Repeated at noise=0 (where independent
noise cannot mask a shared position) and at the generator's default noise.

A generator is reported LEAKS when any duplicate appears at either noise setting.

VACUITY GUARDS -- the V-1 instrument shipped a vacuous PREFIX-STABLE verdict for exactly this
reason, so:
  * refuses to report a verdict when the two runs produced the same row count (the size kwarg was
    silently ignored -- juniper-data params models accept unknown fields);
  * refuses to report CLEAN when a partition came back empty;
  * reports the row counts it actually compared, so a reader can see the comparison was real.

Read-only: generates in memory and compares. Writes nothing.

Usage
-----
    /opt/miniforge3/envs/JuniperData/bin/python 2026-09-01_class1_duplicate_census.py \
        [--n-train N] [--n-val N] [--seed S]

Exit: 0 if every generator returned a verdict; 2 if none could be probed.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import sys

import numpy as np

# Class-1 (synthesised) generators per section 9.3.3, with their size kwarg and noise kwarg.
# `noise=None` means the generator exposes no noise knob -- only the noise=0 column applies.
CLASS1 = [
    ("spiral", "SpiralParams", "SpiralGenerator", "n_points_per_spiral", "noise"),
    ("moon", "MoonParams", "MoonGenerator", "n_samples", "noise"),
    ("gaussian", "GaussianParams", "GaussianGenerator", "n_samples_per_class", "noise"),
    ("xor", "XorParams", "XorGenerator", "n_points_per_quadrant", "noise"),
    ("circles", "CirclesParams", "CirclesGenerator", "n_samples", "noise"),
    ("checkerboard", "CheckerboardParams", "CheckerboardGenerator", "n_samples", "noise"),
    # The five synthetic SEQUENCE generators. In the deferred tier (Chunk 3b), but they are
    # class-1 and probing them is what turns "6 of 11" into a complete class-1 census.
    # They size by `n_steps` and share SyntheticSequenceParams.
    ("ar_p", "ArPParams", "ArPGenerator", "n_steps", None),
    ("delay_product", "DelayProductParams", "DelayProductGenerator", "n_steps", None),
    ("irregular_sine", "IrregularSineParams", "IrregularSineGenerator", "n_steps", None),
    ("mackey_glass", "MackeyGlassParams", "MackeyGlassGenerator", "n_steps", None),
    ("multi_sine", "MultiSineParams", "MultiSineGenerator", "n_steps", None),
]


def named_seed(seed: int, name: str) -> int:
    """The P-1b derivation (section 9.3.2), reduced to a plain int seed.

    The generators take an int `seed`, not a SeedSequence, so the name-keyed SeedSequence is
    materialised into one. Order-independence is preserved -- the key derives from the NAME.
    """
    key = int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big")
    ss = np.random.SeedSequence(entropy=seed, spawn_key=(key,))
    return int(ss.generate_state(1, dtype=np.uint32)[0])


def _resolve(mod_path: str, params_name: str, gen_name: str):
    base = f"juniper_data.generators.{mod_path}"
    params_cls = getattr(importlib.import_module(base + ".params"), params_name, None)
    gen_cls = getattr(importlib.import_module(base + ".generator"), gen_name, None)
    return params_cls, gen_cls


def probe(mod_path, params_name, gen_name, size_kw, noise_kw, n_train, n_val, seed, noise):
    try:
        params_cls, gen_cls = _resolve(mod_path, params_name, gen_name)
    except Exception as exc:
        return None, f"SKIP import: {type(exc).__name__}: {exc}"
    if params_cls is None or gen_cls is None:
        return None, f"SKIP unresolved {params_name}/{gen_name}"

    def gen(n: int, partition: str):
        kw = {size_kw: n, "seed": named_seed(seed, partition)}
        if noise_kw is not None and noise is not None:
            kw[noise_kw] = noise
        return gen_cls.generate(params_cls(**kw))

    try:
        d_tr = gen(n_train, "train")
        d_va = gen(n_val, "val")
    except Exception as exc:
        return None, f"SKIP generate: {type(exc).__name__}: {exc}"

    tr, va = d_tr.get("X_full"), d_va.get("X_full")
    if tr is None or va is None:
        return None, "SKIP no X_full"
    if tr.shape[0] == 0 or va.shape[0] == 0:
        return None, f"SKIP empty partition (train={tr.shape[0]} val={va.shape[0]})"
    if tr.shape[0] == va.shape[0]:
        # The size kwarg was silently ignored -- comparing two same-size runs proves nothing.
        return None, f"VACUOUS: both runs produced {tr.shape[0]} rows; size kwarg '{size_kw}' had no effect"

    tr_set = {r.tobytes() for r in tr}
    dupes = sum(1 for r in va if r.tobytes() in tr_set)
    return dupes, f"train={tr.shape[0]} val={va.shape[0]} dupes={dupes}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-train", type=int, default=1000)
    ap.add_argument("--n-val", type=int, default=400)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    try:
        import juniper_data  # noqa: F401
    except Exception as exc:
        print(f"juniper_data not importable: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("run with /opt/miniforge3/envs/JuniperData/bin/python", file=sys.stderr)
        return 2

    print("=" * 92)
    print(f"Class-1 duplicate census under P-1b  (train={args.n_train} val={args.n_val} seed={args.seed})")
    print("Each partition generated INDEPENDENTLY from its own name-keyed substream (section 9.3.2).")
    print("=" * 92)
    print(f"{'generator':16s}  {'noise=0':>34s}  {'default noise':>34s}")
    print("-" * 92)

    leaked, clean, skipped = [], [], []
    for mod_path, params_name, gen_name, size_kw, noise_kw in CLASS1:
        d0, s0 = probe(mod_path, params_name, gen_name, size_kw, noise_kw, args.n_train, args.n_val, args.seed, noise=0.0)
        dd, sd = probe(mod_path, params_name, gen_name, size_kw, noise_kw, args.n_train, args.n_val, args.seed, noise=None)
        print(f"{mod_path:16s}  {s0:>34s}  {sd:>34s}")
        if d0 is None and dd is None:
            skipped.append(mod_path)
        elif (d0 or 0) > 0 or (dd or 0) > 0:
            leaked.append(mod_path)
        else:
            clean.append(mod_path)

    print("-" * 92)
    print(f"LEAKS   : {', '.join(leaked) if leaked else '(none)'}")
    print(f"CLEAN   : {', '.join(clean) if clean else '(none)'}")
    print(f"SKIPPED : {', '.join(skipped) if skipped else '(none)'}")
    print()
    if skipped:
        print("NOTE: a skipped generator is UNKNOWN, not clean. Do not rule on a partial census.")
    if leaked and not skipped:
        only_mechanism_a = set(leaked) <= {"spiral", "moon"}
        if only_mechanism_a:
            print("READING: the leak is confined to the linspace-parameterised generators, so G-b")
            print("         (per-partition grid offset) is sufficient AND targeted. G-a still buys")
            print("         generator-independence for the unclassified tail.")
        else:
            print("READING: the leak reaches a generator that is NOT linspace-parameterised, so G-b")
            print("         is UNSOUND as a complete remedy -- it fixes only mechanism A. G-a")
            print("         (de-duplicate at assembly) is required.")
    elif not leaked and not skipped:
        print("READING: no class-1 generator leaked at these sizes. That does NOT clear the class --")
        print("         section 9.3.2 measured spiral leaking at 1000/400. Re-check the sizes before")
        print("         concluding anything; a clean sweep here most likely means a vacuity guard")
        print("         silently narrowed what was compared.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
