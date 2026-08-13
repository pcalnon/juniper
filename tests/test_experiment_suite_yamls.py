"""Drift gate for the shipped experiment suites (``util/experiments/suites/**/*.yaml``).

``util/`` is not pre-commit-lint-gated and no test loaded these suite files at all before
R-6, so a malformed suite — an unknown ``execution:`` key, a ``stall_second`` typo, an
``app:`` that is neither cascor nor recurrence — shipped uncaught and only surfaced when a
campaign cell failed hours into a GPU run. This unittest is the gate.

Hermetic by construction: it calls ``run_suite.load_suite``, which validates the document
structure only. It deliberately does NOT call ``expand_cells``, because that resolves
``suite.base_config`` into the sibling repos (``../../../../../juniper-cascor/...``) and
would turn a structural gate into one that skips whenever the ecosystem is not checked out.

Second contract (R-6, ml#1069): a cascor suite that trains a large candidate pool must
declare its own stall window. The driver's Q-2 stall detector watches ``current_epoch``,
which advances only during OUTPUT-layer training — nothing is reported while the CANDIDATE
pool trains — so every ``candidate_pool_size >= 16`` cell reads as ``stalled`` at ~130 s
against the 120 s default while perfectly healthy. The P4 E-A grid lost its pool-16 cells
to exactly that and had to be re-run behind an ad-hoc ``JUNIPER_SUITE_DRIVER`` shim.
"""

from __future__ import annotations

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SUITES_ROOT = REPO_ROOT / "util" / "experiments" / "suites"
DRIVER_PATH = REPO_ROOT / "util" / "experiments" / "run_experiment.py"

spec = importlib.util.spec_from_file_location("run_suite", REPO_ROOT / "util" / "experiments" / "run_suite.py")
run_suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_suite)

# The pool size at which the candidate phase reliably outruns the driver default. Measured on
# the P4 E-A grid: pool 4 / 8 cells complete inside the window; every pool >= 16 cell stalled.
LARGE_POOL_THRESHOLD = 16
POOL_KEY = "training.params.candidate_pool_size"


def _suite_files() -> "list[Path]":
    return sorted(p for p in SUITES_ROOT.rglob("*.yaml") if p.is_file())


def _driver_default_stall_seconds() -> float:
    """Read DEFAULT_STALL_SECONDS out of the driver source rather than importing it.

    Importing ``run_experiment`` pulls its whole module-level surface; the constant is the
    only thing needed here, and reading it keeps this gate honest if the Q-2 default moves.
    """
    match = re.search(r"^DEFAULT_STALL_SECONDS\s*=\s*([0-9.]+)", DRIVER_PATH.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:  # pragma: no cover - only if the driver constant is renamed
        raise AssertionError(f"DEFAULT_STALL_SECONDS not found in {DRIVER_PATH}")
    return float(match.group(1))


def _declared_pool_sizes(doc: dict) -> "list[int]":
    """Every candidate_pool_size this suite's own YAML can produce (matrix + include)."""
    sizes: "list[int]" = []
    matrix_values = (doc.get("matrix") or {}).get(POOL_KEY)
    if isinstance(matrix_values, list):
        sizes.extend(v for v in matrix_values if isinstance(v, int))
    for item in doc.get("include") or []:
        if not isinstance(item, dict):
            continue
        value = (item.get("overrides") or {}).get(POOL_KEY)
        if isinstance(value, int):
            sizes.append(value)
    return sizes


class SuiteYamlLoadTest(unittest.TestCase):
    """Every shipped suite must survive the validator it will be run through."""

    def test_suite_files_are_discovered(self) -> None:
        files = _suite_files()
        self.assertTrue(files, f"no suite YAMLs found under {SUITES_ROOT} — the gate would pass vacuously")

    def test_every_suite_loads(self) -> None:
        for path in _suite_files():
            with self.subTest(suite=path.relative_to(REPO_ROOT).as_posix()):
                try:
                    doc = run_suite.load_suite(path)
                except run_suite.SuiteError as exc:
                    self.fail(f"{path.relative_to(REPO_ROOT)} failed suite validation: {exc}")
                self.assertEqual(doc.get("schema_version"), 1)
                self.assertIn(doc["suite"]["app"], ("cascor", "recurrence"))

    def test_a_malformed_suite_is_actually_rejected(self) -> None:
        """Negative control — proves the gate bites rather than passing vacuously."""
        good = yaml.safe_load((SUITES_ROOT / "p4" / "e-a-cascor-budget-sweep.yaml").read_text(encoding="utf-8"))
        good["execution"]["stall_second"] = 900  # the typo class this gate exists to catch
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.yaml"
            bad.write_text(yaml.safe_dump(good), encoding="utf-8")
            with self.assertRaises(run_suite.SuiteError):
                run_suite.load_suite(bad)


class StallSecondsContractTest(unittest.TestCase):
    """R-6 / ml#1069: large candidate pools must carry their own stall window."""

    def test_large_pool_cascor_suites_declare_stall_seconds(self) -> None:
        default = _driver_default_stall_seconds()
        checked = 0
        for path in _suite_files():
            doc = run_suite.load_suite(path)
            if doc["suite"]["app"] != "cascor":
                continue  # the recurrence train call is synchronous — no poll loop, no stall detector
            pools = _declared_pool_sizes(doc)
            if not any(size >= LARGE_POOL_THRESHOLD for size in pools):
                continue
            checked += 1
            with self.subTest(suite=path.relative_to(REPO_ROOT).as_posix()):
                declared = (doc.get("execution") or {}).get("stall_seconds")
                self.assertIsNotNone(
                    declared,
                    f"{path.name} sweeps candidate_pool_size up to {max(pools)} but declares no execution.stall_seconds; " f"its pool >= {LARGE_POOL_THRESHOLD} cells will be recorded as 'stalled' at the {default}s driver default while healthy",
                )
                self.assertGreater(float(declared), default, f"{path.name} declares stall_seconds={declared}, at or below the {default}s driver default — no effect")
        self.assertGreater(checked, 0, "no large-pool cascor suite was checked — the contract would pass vacuously")


class StallShimRetirementTest(unittest.TestCase):
    """Anti-resurrection: the ad-hoc driver shim R-6 replaced must not come back."""

    def test_the_ad_hoc_stall_shim_is_gone(self) -> None:
        shim = REPO_ROOT / "util" / "ad-hoc" / "2026-08-10_driver_stall_shim.py"
        self.assertFalse(
            shim.exists(),
            f"{shim.relative_to(REPO_ROOT)} is back — execution.stall_seconds (ml#1069) is the supported mechanism; " "a JUNIPER_SUITE_DRIVER shim silently applies one window to every cell of every suite",
        )


if __name__ == "__main__":
    unittest.main()
