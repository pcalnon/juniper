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

That contract triggered on pool size alone, which is not where the class ends. A WIDE-CAP
suite at a modest pool reaches the same failure through a different door: the candidate
phase gets slower every iteration as the cascade widens the input each candidate sees, so
a healthy late-growth cell reads ``stalled`` — "the ml#1069 class, arriving through width
instead of through pool size" (``suites/p4/e-i-cascor-cap-ceiling.yaml:46-50``). The gate
therefore triggers on ``max_hidden_units`` as well.

Third contract: a wide-cap suite must also PIN ITS WALL BUDGET, by either mechanism —
``execution.max_wall_seconds`` or a dotted ``outputs.max_wall_seconds`` override. An
unpinned cell inherits ``base_config``'s value (3600 s for ``spiral-baseline``) with no
signal at all. Measured on the E-I cap sweep at fixed pool 8 (suite run
``20260814T091542Z``): cap 32 → 1497.4 s, cap 64 → 2907.1 s, cap 128 → **4243.6 s**. Only
the last exceeds the inherited default, but 64 clears it by just 693 s, so 64 is the first
cap that cannot be assumed safe under the defaults.

KNOWN LIMITATION — inherited values are invisible here. ``_declared_numbers`` reads only
the suite's own ``matrix`` / ``include``, so a pool or cap coming from ``suite.base_config``
does not trip either contract. That is deliberate: resolving ``base_config`` reaches into
the sibling repos and would turn this structural gate into one that skips whenever the
ecosystem is not checked out (see the paragraph above on ``expand_cells``). A suite that
inherits a large budget shape must declare its own window regardless.
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
# The cap at which WIDTH reaches the same class. Measured on the E-I cap sweep at fixed pool 8
# (suite run 20260814T091542Z): cap 32 -> 1497.4 s, cap 64 -> 2907.1 s, cap 128 -> 4243.6 s
# against a 3600 s inherited driver budget. 32 is demonstrated-safe; 64 clears the budget by
# only 693 s; 128 exceeds it outright. 64 is the first cap that cannot be assumed safe.
LARGE_CAP_THRESHOLD = 64
POOL_KEY = "training.params.candidate_pool_size"
CAP_KEY = "training.params.max_hidden_units"
WALL_OVERRIDE_KEY = "outputs.max_wall_seconds"


def _suite_files() -> "list[Path]":
    return sorted(p for p in SUITES_ROOT.rglob("*.yaml") if p.is_file())


def _driver_default(constant: str) -> float:
    """Read a Q-2 default out of the driver source rather than importing it.

    Importing ``run_experiment`` pulls its whole module-level surface; the constants are the
    only thing needed here, and reading them keeps this gate honest if a default moves.
    """
    match = re.search(rf"^{constant}\s*=\s*([0-9.]+)", DRIVER_PATH.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:  # pragma: no cover - only if the driver constant is renamed
        raise AssertionError(f"{constant} not found in {DRIVER_PATH}")
    return float(match.group(1))


def _declared_numbers(doc: dict, key: str) -> "list[float]":
    """Every value this suite's own YAML can produce for ``key`` (matrix + include).

    Inherited ``suite.base_config`` values are invisible by design — see the module
    docstring's KNOWN LIMITATION note.
    """
    values: "list[float]" = []

    def _accept(value: object) -> None:
        # bool is an int subclass; a YAML ``true`` is never a budget.
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values.append(float(value))

    matrix_values = (doc.get("matrix") or {}).get(key)
    if isinstance(matrix_values, list):
        for value in matrix_values:
            _accept(value)
    for item in doc.get("include") or []:
        if isinstance(item, dict):
            _accept((item.get("overrides") or {}).get(key))
    return values


def _oversize_reasons(doc: dict) -> "list[str]":
    """Why this suite needs a raised stall window — empty when it does not."""
    reasons: "list[str]" = []
    pools = _declared_numbers(doc, POOL_KEY)
    caps = _declared_numbers(doc, CAP_KEY)
    if any(p >= LARGE_POOL_THRESHOLD for p in pools):
        reasons.append(f"candidate_pool_size up to {int(max(pools))}")
    if any(c >= LARGE_CAP_THRESHOLD for c in caps):
        reasons.append(f"max_hidden_units up to {int(max(caps))}")
    return reasons


def _declared_wall_budgets(doc: dict) -> "list[float]":
    """Wall budgets the suite pins itself, by either supported mechanism.

    ``execution.max_wall_seconds`` forwards ``--max-wall-seconds`` to the driver; a dotted
    ``outputs.max_wall_seconds`` override rewrites the resolved cell config. E-I uses the
    latter, so accepting only the former would fail a correctly-budgeted suite.
    """
    budgets: "list[float]" = []
    declared = (doc.get("execution") or {}).get("max_wall_seconds")
    if isinstance(declared, (int, float)) and not isinstance(declared, bool):
        budgets.append(float(declared))
    budgets.extend(_declared_numbers(doc, WALL_OVERRIDE_KEY))
    return budgets


def _inherited_wall_budgets(doc: dict, suite_path: Path) -> "tuple[list[float], list[str]]":
    """Wall budgets pinned in the suite's base configs, when those resolve locally.

    THIRD mechanism, and the one that makes the wall contract honest. A budget may
    legitimately live in ``base_config`` rather than the suite — ``e-j-h2h-wide-cap128``
    pins ``outputs.max_wall_seconds: 14400`` in ``util/ad-hoc/2026-08-16_h2h_wide_nrot3.yaml``
    and is correctly budgeted, which a suite-only check flunks. That is the module
    docstring's KNOWN LIMITATION biting in the FALSE-POSITIVE direction: a blind spot that
    merely hides problems is tolerable, one that fails correct configs is not.

    Resolution reuses ``run_suite._resolve_base_config`` so this cannot drift from the real
    resolver. In-repo base configs (``util/ad-hoc/...``) always resolve; sibling-repo ones
    (``../../../../../juniper-cascor/...``) do not when the ecosystem is not checked out,
    and are returned as ``unresolved`` so the caller can decline to judge rather than guess.
    """
    budgets: "list[float]" = []
    unresolved: "list[str]" = []
    for rel in (doc.get("suite") or {}).get("base_config") or []:
        if not isinstance(rel, str):
            continue
        try:
            path = run_suite._resolve_base_config(suite_path, rel)
            base = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
        except (OSError, yaml.YAMLError):
            base = None
        if not isinstance(base, dict):
            unresolved.append(rel)
            continue
        value = (base.get("outputs") or {}).get("max_wall_seconds")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            budgets.append(float(value))
    return budgets, unresolved


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
    """R-6 / ml#1069: large pools OR wide caps must carry their own stall window."""

    def test_oversize_cascor_suites_declare_stall_seconds(self) -> None:
        default = _driver_default("DEFAULT_STALL_SECONDS")
        checked = 0
        for path in _suite_files():
            doc = run_suite.load_suite(path)
            if doc["suite"]["app"] != "cascor":
                continue  # the recurrence train call is synchronous — no poll loop, no stall detector
            reasons = _oversize_reasons(doc)
            if not reasons:
                continue
            checked += 1
            with self.subTest(suite=path.relative_to(REPO_ROOT).as_posix()):
                declared = (doc.get("execution") or {}).get("stall_seconds")
                self.assertIsNotNone(
                    declared,
                    f"{path.name} sweeps {' and '.join(reasons)} but declares no execution.stall_seconds; " f"those cells will be recorded as 'stalled' at the {default}s driver default while healthy",
                )
                self.assertGreater(float(declared), default, f"{path.name} declares stall_seconds={declared}, at or below the {default}s driver default — no effect")
        self.assertGreater(checked, 0, "no oversize cascor suite was checked — the contract would pass vacuously")

    def test_a_wide_cap_suite_at_a_small_pool_is_caught(self) -> None:
        """Negative control for the widening: pool 8 + cap 128 must NOT slip through.

        This is the exact shape that passed the pool-only gate and then lost its 128-unit
        cells to a false ``stalled`` hours into a campaign.
        """
        doc = {
            "suite": {"app": "cascor"},
            "execution": {},
            "matrix": {POOL_KEY: [8], CAP_KEY: [32, 64, 128]},
        }
        self.assertEqual(_oversize_reasons(doc), ["max_hidden_units up to 128"])

    def test_a_small_suite_does_not_trip_the_contract(self) -> None:
        """The widening must not fire on budgets demonstrated safe under the defaults."""
        doc = {"suite": {"app": "cascor"}, "matrix": {POOL_KEY: [4, 8], CAP_KEY: [4, 8, 16, 32]}}
        self.assertEqual(_oversize_reasons(doc), [])


class WallBudgetContractTest(unittest.TestCase):
    """A wide-cap suite must pin its own Q-2 wall budget rather than inherit one."""

    def test_wide_cap_cascor_suites_pin_a_wall_budget(self) -> None:
        default = _driver_default("DEFAULT_MAX_WALL_SECONDS")
        checked = 0
        undecidable: "list[str]" = []
        for path in _suite_files():
            doc = run_suite.load_suite(path)
            if doc["suite"]["app"] != "cascor":
                continue
            caps = _declared_numbers(doc, CAP_KEY)
            if not any(cap >= LARGE_CAP_THRESHOLD for cap in caps):
                continue
            own = _declared_wall_budgets(doc)
            inherited, unresolved = _inherited_wall_budgets(doc, path)
            effective = own + inherited
            if not effective and unresolved:
                # The budget can only be in a base config this checkout cannot read.
                # Declining to judge is the honest outcome — asserting here would fail a
                # correctly-budgeted suite purely because the siblings are not cloned.
                undecidable.append(f"{path.name} (unreadable base_config: {', '.join(unresolved)})")
                continue
            checked += 1
            with self.subTest(suite=path.relative_to(REPO_ROOT).as_posix()):
                self.assertTrue(
                    effective,
                    f"{path.name} sweeps max_hidden_units up to {int(max(caps))} but no wall budget is pinned in the suite OR its base config, " f"so its cells fall back to the driver's {default}s default with no signal — " "set execution.max_wall_seconds, override outputs.max_wall_seconds, or pin it in the base config",
                )
                self.assertGreater(min(effective), default, f"{path.name} pins wall budget {min(effective)}s, at or below the driver's {default}s default — no effect")
        self.assertGreater(checked, 0, f"no wide-cap cascor suite was decidable — the contract would pass vacuously (undecidable: {undecidable})")

    def test_a_budget_pinned_only_in_base_config_counts(self) -> None:
        """The false-positive class this contract shipped with, caught in CI on day one.

        ``e-j-h2h-wide-cap128`` pins ``outputs.max_wall_seconds: 14400`` in its base config
        (``util/ad-hoc/2026-08-16_h2h_wide_nrot3.yaml``) and nowhere in the suite. A
        suite-only check flunked it as "pins no wall budget" while its cells had provably
        run 5166.7 s and 5016.9 s to ``succeeded`` — i.e. correctly budgeted all along.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text("outputs:\n  max_wall_seconds: 14400\n", encoding="utf-8")
            doc = {"suite": {"base_config": ["base.yaml"]}}
            budgets, unresolved = _inherited_wall_budgets(doc, root / "suite.yaml")
            self.assertEqual(budgets, [14400.0])
            self.assertEqual(unresolved, [])

    def test_an_unreadable_base_config_is_reported_not_guessed(self) -> None:
        """A sibling-repo base config that is not checked out must be declined, not failed."""
        with tempfile.TemporaryDirectory() as tmp:
            doc = {"suite": {"base_config": ["../../../../../juniper-cascor/conf/experiments/nope.yaml"]}}
            budgets, unresolved = _inherited_wall_budgets(doc, Path(tmp) / "suite.yaml")
            self.assertEqual(budgets, [])
            self.assertEqual(len(unresolved), 1)

    def test_a_base_config_without_a_budget_contributes_nothing(self) -> None:
        """Readable but budget-less: no phantom value, and not counted as unresolved."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text("outputs:\n  plots: []\n", encoding="utf-8")
            doc = {"suite": {"base_config": ["base.yaml"]}}
            budgets, unresolved = _inherited_wall_budgets(doc, root / "suite.yaml")
            self.assertEqual(budgets, [])
            self.assertEqual(unresolved, [])

    def test_either_budget_mechanism_satisfies_the_contract(self) -> None:
        """execution.max_wall_seconds and the dotted outputs override are equivalent."""
        via_execution = {"execution": {"max_wall_seconds": 14400}}
        via_override = {"matrix": {WALL_OVERRIDE_KEY: [14400]}}
        self.assertEqual(_declared_wall_budgets(via_execution), [14400.0])
        self.assertEqual(_declared_wall_budgets(via_override), [14400.0])
        self.assertEqual(_declared_wall_budgets({"execution": {}}), [])


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
