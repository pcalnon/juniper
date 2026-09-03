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


def measure_csv_import(row_counts: tuple[int, ...] = (10_000, 100_000, 500_000, 1_000_000), n_features: int = 20) -> dict[str, Any]:
    """Scaling curve for the Class C generator, and the row count that crosses the budget.

    ``csv_import`` is neither fan-out-bound (Option 6) nor a fixed decode
    (Option 1): its cost tracks the size of a caller-supplied file, and nothing
    caps that. ``CsvImportParams`` has no row or byte limit, the only settings-level
    control is ``import_dir`` (a traversal guard), and ``_load_csv`` materialises
    the whole file into a ``list[dict]`` before conversion. So the question is not
    "is it slow" but "where does it cross 30 s, and is that reachable".

    Measured cold only: there is no fetch to warm, and the OS page cache makes a
    second read of the same file unrepresentative of a real first import.
    """
    import csv as _csv
    import random

    from juniper_data.api.settings import get_settings

    import_dir = Path(tempfile.mkdtemp(prefix="csv-import-"))
    os.environ["JUNIPER_DATA_IMPORT_DIR"] = str(import_dir)
    get_settings.cache_clear()  # settings are cached; the env var must take effect

    from juniper_data.generators.csv_import.generator import CsvImportGenerator
    from juniper_data.generators.csv_import.params import CsvImportParams

    rng = random.Random(7)
    rows: list[dict[str, Any]] = []
    header = [f"f{i}" for i in range(n_features)] + ["label"]
    written = 0
    results: list[dict[str, Any]] = []

    for target in row_counts:
        name = f"import_{target}.csv"
        path = import_dir / name
        # Append rather than regenerate, so each larger file reuses the prior rows.
        mode = "a" if path.exists() else "w"
        with path.open(mode, newline="", encoding="utf-8") as handle:
            writer = _csv.writer(handle)
            if mode == "w":
                writer.writerow(header)
                for prior in rows:
                    writer.writerow([prior[c] for c in header])
            while written < target:
                row = {c: round(rng.random(), 6) for c in header[:-1]}
                row["label"] = rng.randint(0, 1)
                rows.append(row)
                writer.writerow([row[c] for c in header])
                written += 1

        size_mb = path.stat().st_size / (1024 * 1024)
        params = CsvImportParams(file_path=name, label_column="label", seed=42)
        elapsed, outcome = _timed(lambda p=params: CsvImportGenerator.generate(p))
        results.append(
            {
                "rows": target,
                "size_mb": round(size_mb, 1),
                "sec": round(elapsed, 2),
                "outcome": outcome,
                "over_budget": elapsed > CLIENT_BUDGET_SEC,
            }
        )
        print("    %9d rows | %7.1f MB | %8.2f s%s" % (target, size_mb, elapsed, "  OVER BUDGET" if elapsed > CLIENT_BUDGET_SEC else ""), flush=True)

    shutil.rmtree(import_dir, ignore_errors=True)

    ok = [r for r in results if r["outcome"] == "ok" and r["sec"] > 0]
    per_row_ms = (ok[-1]["sec"] / ok[-1]["rows"] * 1000) if ok else float("nan")
    crossover = int(CLIENT_BUDGET_SEC / (per_row_ms / 1000)) if ok and per_row_ms > 0 else None
    return {
        "generator": "csv_import",
        "n_features": n_features,
        "points": results,
        "per_row_ms": round(per_row_ms, 6),
        "budget_crossover_rows": crossover,
        "cold_sec": ok[-1]["sec"] if ok else None,
        "warm_sec": None,
    }


MEASURERS: dict[str, Callable[[], dict[str, Any]]] = {
    "equities": measure_equities,
    "arc_agi": measure_arc_agi,
    "mnist": measure_mnist,
    "csv_import": measure_csv_import,
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
