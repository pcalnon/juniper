#!/usr/bin/env python
"""Measure juniper-data's Class B (external-fetch) generators, cold and warm.

Project:     Juniper
Sub-Project: juniper-ml
Application: APD-DATA-018 step 1 -- measure the precondition
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Status:      ad-hoc (single-use measurement)

Step 1 of section 4 of
``notes/JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md``:
the primer's test for whether an async job pattern is warranted is "does the work
outlive a sensible request timeout". That document argued it near-certainly does
for Class B; this measures it instead of asserting it.

**Politeness.** ``equities`` fans out over 503 bundled S&P constituents by
default and each SEC call is throttled to >=0.12 s. Measuring the default would
mean ~1000 requests to SEC for a number that extrapolates from three. So this
measures a SMALL sample and reports the per-symbol cost plus the arithmetic
extrapolation, and states clearly that the extrapolation is arithmetic rather
than observed. juniper-data's own compliant User-Agent and throttle are used
unchanged.

Cold vs warm is controlled by pointing the generator's cache at a fresh temp
directory (cold) and then re-running against the now-populated one (warm).

Usage::

    python util/ad-hoc/2026-09-02_measure_class_b_generators.py            # all
    python util/ad-hoc/2026-09-02_measure_class_b_generators.py equities   # one
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

DATA_ROOT = Path("/home/pcalnon/Development/python/Juniper/juniper-data")
CLIENT_BUDGET_SEC = 30.0  # juniper-data-client default; see analysis section 1.3


def _timed(fn: Callable[[], Any]) -> tuple[float, str]:
    """Run ``fn``; return (seconds, outcome). Never raises."""
    start = time.perf_counter()
    try:
        fn()
        return time.perf_counter() - start, "ok"
    except Exception as exc:  # noqa: BLE001 - a failed generator is a result, not a crash
        return time.perf_counter() - start, f"{type(exc).__name__}: {str(exc)[:120]}"


def measure_equities(sample: int = 3) -> dict[str, Any]:
    """Cold/warm for a small symbol sample, plus the arithmetic default-scale floor."""
    from juniper_data.generators.equities.generator import _SEC_MIN_INTERVAL, EquitiesGenerator
    from juniper_data.generators.equities.params import EquitiesParams

    constituents = DATA_ROOT / "juniper_data/generators/equities/sp500_constituents.csv"
    n_constituents = sum(1 for _ in constituents.open()) - 1  # minus header

    cache_dir = Path(tempfile.mkdtemp(prefix="equities-cold-"))
    os.environ["JUNIPER_DATA_EQUITIES_CACHE_DIR"] = str(cache_dir)
    # The module read the env var at import time, so point the module constant too.
    import juniper_data.generators.equities.generator as eq

    eq._CACHE_DIR = cache_dir

    params = EquitiesParams(max_symbols=sample)
    cold, cold_outcome = _timed(lambda: EquitiesGenerator.generate(params))
    warm, warm_outcome = _timed(lambda: EquitiesGenerator.generate(params))
    shutil.rmtree(cache_dir, ignore_errors=True)

    per_symbol = cold / sample if sample else float("nan")
    return {
        "generator": "equities",
        "sample_symbols": sample,
        "cold_sec": round(cold, 2),
        "warm_sec": round(warm, 2),
        "cold_outcome": cold_outcome,
        "warm_outcome": warm_outcome,
        "per_symbol_sec": round(per_symbol, 3),
        "default_symbols": n_constituents,
        # Arithmetic, NOT observed: the SEC throttle alone imposes this floor at
        # default scale, independent of network conditions.
        "default_throttle_floor_sec": round(n_constituents * _SEC_MIN_INTERVAL, 1),
        "default_extrapolated_sec": round(per_symbol * n_constituents, 1),
        "sec_min_interval": _SEC_MIN_INTERVAL,
    }


def measure_arc_agi() -> dict[str, Any]:
    from juniper_data.generators.arc_agi.generator import ArcAgiGenerator
    from juniper_data.generators.arc_agi.params import ArcAgiParams

    params = ArcAgiParams()
    cold, cold_outcome = _timed(lambda: ArcAgiGenerator.generate(params))
    warm, warm_outcome = _timed(lambda: ArcAgiGenerator.generate(params))
    return {
        "generator": "arc_agi",
        "cold_sec": round(cold, 2),
        "warm_sec": round(warm, 2),
        "cold_outcome": cold_outcome,
        "warm_outcome": warm_outcome,
    }


def measure_mnist() -> dict[str, Any]:
    from juniper_data.generators.mnist.generator import MnistGenerator
    from juniper_data.generators.mnist.params import MnistParams

    params = MnistParams()
    cold, cold_outcome = _timed(lambda: MnistGenerator.generate(params))
    warm, warm_outcome = _timed(lambda: MnistGenerator.generate(params))
    return {
        "generator": "mnist",
        "cold_sec": round(cold, 2),
        "warm_sec": round(warm, 2),
        "cold_outcome": cold_outcome,
        "warm_outcome": warm_outcome,
        "note": "cold is only cold if the HF cache was empty; see hf_cache_present",
        "hf_cache_present": (Path.home() / ".cache" / "huggingface").exists(),
    }


MEASURERS: dict[str, Callable[[], dict[str, Any]]] = {
    "equities": measure_equities,
    "arc_agi": measure_arc_agi,
    "mnist": measure_mnist,
}


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(DATA_ROOT))
    wanted = argv[1:] or list(MEASURERS)
    results = []
    for name in wanted:
        if name not in MEASURERS:
            print(f"unknown generator: {name}", file=sys.stderr)
            return 2
        print(f"--- measuring {name} ---", flush=True)
        results.append(MEASURERS[name]())
        print(json.dumps(results[-1], indent=2), flush=True)

    print("\n=== SUMMARY (client budget %.0fs) ===" % CLIENT_BUDGET_SEC)
    for r in results:
        cold = r.get("cold_sec")
        verdict = "OVER BUDGET" if isinstance(cold, float) and cold > CLIENT_BUDGET_SEC else "within budget"
        print("%-10s cold=%-8s warm=%-8s %s" % (r["generator"], cold, r.get("warm_sec"), verdict))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
