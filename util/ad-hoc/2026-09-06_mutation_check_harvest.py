#!/usr/bin/env python3
"""
Break each guard a harvested test claims to pin, and require the test to notice.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#1625 / #1735 harvest; `2026-09-06_harvest_methods.py`

A harvested test that passes on first run has proved nothing yet. It may be pinning a real
guard, or it may be an OR whose easy half is always true -- `assertIn("cpu_count", reasons +
json.dumps(result["host"]))` reads the field name straight out of the echoed host dict whether
or not the field is in the blocking set.

So break the guard and require the test to notice. Each entry names a production edit and the
tests that MUST go red under it; a test that stays green under its own mutation is reported,
because that is the vacuous case.

Mutations are applied to a COPY under a temp directory -- never to the tree -- and the suite is
re-run in a subprocess so stale bytecode cannot answer for the mutant.

Usage:
    2026-09-06_mutation_check_harvest.py

Exit: 0 when every test named below dies under its mutation; 1 when any survives.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 -- fixed argv python invocations, no shell
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# (label, file under util/, old text, new text, tests that must fail)
MUTATIONS = [
    (
        "cpu_count leaves the blocking host set",
        "experiments/compare_baseline.py",
        '"cpu_count"',
        '"cpu_count_DISABLED"',
        ["test_cpu_count_mismatch_is_refused"],
    ),
    (
        "the candidate's fingerprints are first-matched instead of set-compared",
        "experiments/compare_baseline.py",
        'if not summary["single_workload"]:',
        "if False:",
        ["test_mixed_fingerprints_in_candidate_are_REFUSED_not_first_matched"],
    ),
    (
        "make_baseline stops gating on the termination branch",
        "experiments/make_baseline.py",
        'if not summary.get("single_completion_reason", True) and summary.get("completion_reasons"):',
        "if False:",
        ["test_refuses_a_suite_whose_cells_mix_a_KNOWN_and_a_MISSING_branch"],
    ),
    (
        "the pre-#1776 falsy filter is re-introduced into completion_reasons",
        "experiments/read_run_metrics.py",
        'reasons = sorted({str(r.get("completion_reason")) for r in rows}) if rows else []',
        'reasons = sorted({str(r.get("completion_reason")) for r in rows if r.get("completion_reason")}) if rows else []',
        ["test_completion_reasons_KEEPS_the_unknown_member_rather_than_filtering_it"],
    ),
    (
        "a zero baseline speed is treated as present",
        "experiments/compare_baseline.py",
        "if base_speed and cand_speed",
        "if base_speed is not None and cand_speed is not None",
        ["test_zero_baseline_speed_is_n_a_and_still_passes"],
    ),
]


def run(tmp: Path, names: list[str], suite: str) -> dict[str, bool]:
    """`{test: passed}` for each named test, run against the mutated copy."""
    out: dict[str, bool] = {}
    for name in names:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "-k", name, suite],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        ran = "Ran 0 tests" not in proc.stderr
        out[name] = proc.returncode == 0 and ran
        if not ran:
            print(f"    !! {name} matched NO test under -k -- the name is wrong, not the guard")
    return out


def main() -> int:
    worst = 0
    for label, rel, old, new, names in MUTATIONS:
        suite = {"make_baseline": "tests.test_make_baseline", "read_run_metrics": "tests.test_read_run_metrics"}.get(Path(rel).stem, "tests.test_compare_baseline")
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "repo"
            # Copy ONLY what the suite imports. A whole-tree copy dies on the dangling
            # symlinks under notes/legacy/, and copying them is not the point anyway.
            tmp.mkdir(parents=True)
            for sub in ("util", "tests"):
                shutil.copytree(REPO / sub, tmp / sub, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"), symlinks=True)
            target = tmp / "util" / rel
            text = target.read_text(encoding="utf-8")
            if old not in text:
                print(f"[SKIP] {label}: anchor {old!r} not in util/{rel}")
                worst = 1
                continue
            target.write_text(text.replace(old, new, 1), encoding="utf-8")
            results = run(tmp, names, suite)
        survivors = [n for n, passed in results.items() if passed]
        status = "OK  " if not survivors else "VACUOUS"
        print(f"[{status}] {label}")
        for name in names:
            print(f"    {'SURVIVED (vacuous)' if results[name] else 'died (good)'}: {name}")
        if survivors:
            worst = 1
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
