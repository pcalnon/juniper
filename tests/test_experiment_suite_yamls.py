"""Drift gate for the shipped experiment suites (``util/experiments/suites/**/*.yaml``).

``util/`` is not pre-commit-lint-gated and no test loaded these suite files at all before
R-6, so a malformed suite — an unknown ``execution:`` key, a ``stall_second`` typo, an
``app:`` that is neither cascor nor recurrence — shipped uncaught and only surfaced when a
campaign cell failed hours into a GPU run. This unittest is the gate.

Hermetic by construction: it calls ``run_suite.load_suite``, which validates the document
structure only. Contracts that need an INHERITED value additionally resolve
``suite.base_config`` — see ``_cell_specs`` — but never require it to resolve: a sibling-repo
reference (``../../../../../juniper-cascor/...``) is unreadable in a checkout that has only
juniper-ml, which is every CI run, and is reported as ``unresolved`` so the caller declines to
judge rather than guessing. No contract here fails because the ecosystem is absent.

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

Fourth contract: ``execution.per_run_timeout_seconds`` must sit ABOVE the wall budget the
driver will enforce. That timeout is run_suite's SUBPROCESS ceiling, not a budget. When it
is at or below the driver's own budget, run_suite kills the driver from outside and records
``timed_out`` with ``exit_code: null`` (``run_suite.py:350-354``), returning BEFORE the
manifest read at ``:355`` — so the driver never writes a manifest and the honest ``timed_out``
record is destroyed rather than degraded. The rule was stated in-repo by a suite author
(``suites/p4/e-j-h2h-wide-cap64.yaml:73-75``: "the DRIVER must be what stops a run") and then
not carried to the suites that needed it. EQUAL is a loss, not a tie: the driver still has to
write its manifest after hitting its deadline, so a simultaneous subprocess kill pre-empts it.
The predicate is therefore ``timeout > budget``, not ``>=``.

Cascor only, as with the two contracts above. The recurrence path has the same defect —
``_run_recurrence`` (``run_experiment.py:1617``) resolves ``max_wall`` identically at ``:1619``
and passes it as the SOCKET timeout on the synchronous ``POST /v1/train`` (``:1697``), logging
its own honest ``timed_out`` — but retuning a recurrence timeout is a separate analysis of that
failure mode, and one of the five affected suites (``perf/pf5-recurrence-d-scaling``) is inside
the gated perf lane. Surveyed 2026-08-20 and left deliberately unfixed:
``recurrence-d-sweep`` (600/900, inverted) and ``p4/e-d``, ``p4/e-f``, ``p4/e-g``,
``perf/pf5`` (900/900, equal). See ``util/ad-hoc/2026-08-20_wall_ordering_survey.py``.

KNOWN LIMITATION — partially lifted. ``_declared_numbers`` still reads only the suite's own
``matrix`` / ``include``; ``_effective_numbers`` and ``_effective_wall_budgets`` resolve the
per-cell value the driver actually sees, so an inherited pool, cap or budget is no longer
invisible. Per-cell resolution matters in BOTH directions: a suite may inherit a large value
(the blind spot) or override an inherited one DOWNWARD — ``e-k-thread-probe-cap16`` and
``e-l-determinism-cap4`` both inherit ``max_hidden_units: 64`` and cap it at 16 and 4, so
reading the base alone would flag them as wide-cap suites they are not.
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


def _oversize_reasons(doc: dict, suite_path: "Path | None" = None) -> "list[str]":
    """Why this suite needs a raised stall window — empty when it does not.

    With ``suite_path`` the per-cell effective values are folded in, so a pool or cap
    inherited from ``base_config`` trips the contract too (the asymmetry ml#1142 left behind:
    it taught the WALL contract to read a base config and left this one matrix-only).

    Declared values are UNIONED with effective ones rather than replaced by them. A base that
    does not resolve yields no effective values at all, and in CI no sibling-repo base ever
    resolves — so reading effective values alone would silently stop this contract firing on
    every suite it currently catches. The union can only ever add reasons, never remove one.
    """
    reasons: "list[str]" = []
    pools = _declared_numbers(doc, POOL_KEY)
    caps = _declared_numbers(doc, CAP_KEY)
    if suite_path is not None:
        pools = pools + _effective_numbers(doc, suite_path, POOL_KEY)[0]
        caps = caps + _effective_numbers(doc, suite_path, CAP_KEY)[0]
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


def _run_suite_default_timeout() -> float:
    """run_suite's own ``per_run_timeout_seconds`` fallback, read from source not duplicated."""
    source = (REPO_ROOT / "util" / "experiments" / "run_suite.py").read_text(encoding="utf-8")
    match = re.search(r'per_run_timeout_seconds",\s*([0-9.]+)', source)
    if match is None:  # pragma: no cover - only if run_suite's default is restructured
        raise AssertionError("run_suite's per_run_timeout_seconds default not found")
    return float(match.group(1))


def _dotted_get(config: dict, dotted: str) -> object:
    """Read a dotted path out of a resolved config, or None if any segment is missing."""
    node: object = config
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _cell_specs(doc: dict, suite_path: Path) -> "tuple[list[tuple[dict, dict]], list[str]]":
    """``(base config, overrides)`` for every cell this suite expands to.

    Pairs each cell with the base config it will actually be materialised from, exactly as
    ``run_suite.materialise_cell`` does — so an inherited value becomes visible and a
    per-cell override is applied on top of the right base. Bases that do not resolve are
    returned as ``unresolved`` rather than guessed, mirroring ``_inherited_wall_budgets``.

    ``expand_cells`` does not raise on an unresolvable reference — ``_resolve_base_config``
    returns the non-existent literal path — so this stays decidable-or-declined, never fatal.
    """
    try:
        cells = run_suite.expand_cells(doc, suite_path)
    except Exception as exc:  # noqa: BLE001 - a malformed suite is the load contract's job
        return [], [f"{suite_path.name}: expand_cells failed: {exc}"]

    loaded: "dict[Path, dict | None]" = {}
    specs: "list[tuple[dict, dict]]" = []
    unresolved: "list[str]" = []
    for cell in cells:
        path = Path(cell["config_path"])
        if path not in loaded:
            try:
                base = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
            except (OSError, yaml.YAMLError):
                base = None
            loaded[path] = base if isinstance(base, dict) else None
        base = loaded[path]
        if base is None:
            if str(path) not in unresolved:
                unresolved.append(str(path))
            continue
        specs.append((base, cell["overrides"]))
    return specs, unresolved


def _effective_numbers(doc: dict, suite_path: Path, key: str) -> "tuple[list[float], list[str]]":
    """Every value ``key`` actually takes across this suite's cells: override, else inherited.

    The per-cell resolution is the point. Taking the union of suite and base values instead
    would flag ``e-k-thread-probe-cap16`` and ``e-l-determinism-cap4`` as sweeping the cap 64
    they inherit and then override down to 16 and 4 — a false positive on two shipped suites.
    """
    specs, unresolved = _cell_specs(doc, suite_path)
    values: "list[float]" = []
    for base, overrides in specs:
        value = overrides[key] if key in overrides else _dotted_get(base, key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values.append(float(value))
    return values, unresolved


def _effective_wall_budgets(doc: dict, suite_path: Path) -> "tuple[list[float], list[str]]":
    """The wall budget the DRIVER will enforce on each cell, by the driver's own precedence.

    ``run_experiment.py:1883`` documents it: ``CLI > YAML outputs.max_wall_seconds > default``.
    A suite that sets ``execution.max_wall_seconds`` has run_suite forward
    ``--max-wall-seconds``, which wins outright for every cell — so that short-circuits, and a
    matrix override underneath it would never be read. Otherwise each cell resolves its own
    override, then its base config, then the driver default; a cell that pins nothing anywhere
    still HAS a budget, and that default is exactly what makes the inherited case bite.
    """
    declared = (doc.get("execution") or {}).get("max_wall_seconds")
    if isinstance(declared, (int, float)) and not isinstance(declared, bool):
        return [float(declared)], []
    default = _driver_default("DEFAULT_MAX_WALL_SECONDS")
    specs, unresolved = _cell_specs(doc, suite_path)
    budgets: "list[float]" = []
    for base, overrides in specs:
        value = overrides[WALL_OVERRIDE_KEY] if WALL_OVERRIDE_KEY in overrides else _dotted_get(base, WALL_OVERRIDE_KEY)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            budgets.append(float(value))
        else:
            budgets.append(default)
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
            reasons = _oversize_reasons(doc, path)
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

    def test_a_pool_inherited_from_a_base_config_is_caught(self) -> None:
        """The blind spot ml#1142 left behind, and the reason it had to close.

        ``e-l-determinism-cap4`` declares only ``max_hidden_units``; its
        ``candidate_pool_size: 8`` comes from ``util/ad-hoc/2026-08-16_h2h_wide_nrot3.yaml``
        and was invisible to this contract. Pool 8 is under the threshold so nothing tripped —
        a suite inheriting pool 32 the same way would have slipped straight through.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text("training:\n  params:\n    candidate_pool_size: 32\n", encoding="utf-8")
            doc = {"suite": {"app": "cascor", "base_config": ["base.yaml"]}}
            self.assertEqual(_oversize_reasons(doc), [], "precondition: invisible without a suite_path")
            self.assertEqual(_oversize_reasons(doc, root / "suite.yaml"), ["candidate_pool_size up to 32"])

    def test_a_downward_override_of_an_inherited_cap_does_not_trip(self) -> None:
        """The false-positive class the per-cell resolution exists to avoid.

        ``e-k-thread-probe-cap16`` and ``e-l-determinism-cap4`` inherit ``max_hidden_units:
        64`` — exactly the threshold — from the shared base and override it DOWN to 16 and 4.
        Reading the base alone would flag both as wide-cap suites they are not.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text("training:\n  params:\n    max_hidden_units: 64\n", encoding="utf-8")
            doc = {"suite": {"app": "cascor", "base_config": ["base.yaml"]}, "matrix": {CAP_KEY: [4]}}
            self.assertEqual(_oversize_reasons(doc, root / "suite.yaml"), [])

    def test_an_unresolvable_base_never_weakens_the_contract(self) -> None:
        """A declared value must still fire when the base config cannot be read — the CI case.

        Every sibling-repo base is unreadable in CI. Resolving effective values INSTEAD of
        declared ones would have silently stopped this contract firing on every suite it
        already catches; the union is what prevents that.
        """
        with tempfile.TemporaryDirectory() as tmp:
            doc = {
                "suite": {"app": "cascor", "base_config": ["../../../../../juniper-cascor/conf/experiments/nope.yaml"]},
                "matrix": {POOL_KEY: [32]},
            }
            self.assertEqual(_oversize_reasons(doc, Path(tmp) / "suite.yaml"), ["candidate_pool_size up to 32"])


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
            # Was ``_declared_wall_budgets(doc) + _inherited_wall_budgets(doc, path)[0]``, which
            # unioned values that are ALTERNATIVES, not co-existing constraints, and then took
            # their min. E-I overrides its base's 3600 to 14400 in the matrix, so the driver only
            # ever sees 14400 — but the union produced [14400, 3600] and min() flunked a correctly
            # budgeted suite. CI never saw it: there the sibling base is unresolvable, so the
            # union was [14400] and passed. Resolving per-cell, override-beats-base, is the fix.
            effective, unresolved = _effective_wall_budgets(doc, path)
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

    def test_an_override_beats_the_base_it_replaces(self) -> None:
        """E-I's real shape: a matrix override raising a base's budget must not read as the base.

        ``e-i-cascor-cap-ceiling`` inherits ``outputs.max_wall_seconds: 3600`` from
        ``spiral-baseline`` and overrides it to 14400 in its matrix, so every cell runs at
        14400 — its measured cap-128 cell took 4243.6 s, which only 14400 permits. Unioning
        the two and taking the min reported 3600 and failed the suite. The failure was
        invisible in CI, where the sibling base does not resolve and the union is [14400]:
        a contract that passes for the wrong reason wherever it runs.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text("outputs:\n  max_wall_seconds: 3600\n", encoding="utf-8")
            doc = {"suite": {"app": "cascor", "base_config": ["base.yaml"]}, "matrix": {WALL_OVERRIDE_KEY: [14400]}}
            self.assertEqual(_effective_wall_budgets(doc, root / "suite.yaml"), ([14400.0], []))
            legacy = _declared_wall_budgets(doc) + _inherited_wall_budgets(doc, root / "suite.yaml")[0]
            self.assertEqual(min(legacy), 3600.0, "precondition: the union-and-min arithmetic this replaced")

    def test_either_budget_mechanism_satisfies_the_contract(self) -> None:
        """execution.max_wall_seconds and the dotted outputs override are equivalent."""
        via_execution = {"execution": {"max_wall_seconds": 14400}}
        via_override = {"matrix": {WALL_OVERRIDE_KEY: [14400]}}
        self.assertEqual(_declared_wall_budgets(via_execution), [14400.0])
        self.assertEqual(_declared_wall_budgets(via_override), [14400.0])
        self.assertEqual(_declared_wall_budgets({"execution": {}}), [])


class TimeoutOrderingContractTest(unittest.TestCase):
    """The DRIVER must be what stops a run — never run_suite's subprocess timeout."""

    def test_cascor_suites_time_out_after_the_driver_stops(self) -> None:
        """``per_run_timeout_seconds`` must sit strictly above the effective wall budget.

        Below or equal, run_suite's ``subprocess.run(timeout=...)`` fires first and returns at
        ``run_suite.py:354`` before the manifest read at ``:355``: the row is recorded
        ``timed_out`` with ``exit_code: null`` and the driver's own manifest is never written.
        The evidence is destroyed, not degraded — which is why this is fatal where ml#1152's
        inert-stall-window check is advisory: there the run itself stays valid.

        Survey of 2026-08-20 (``util/ad-hoc/2026-08-20_wall_ordering_survey.py``, full
        ecosystem checked out): 3 inverted, 6 equal, 14 correct. The four cascor offenders are
        fixed in the PR that added this gate; the five recurrence ones are deliberately out of
        scope per the module docstring.
        """
        default_timeout = _run_suite_default_timeout()
        checked = 0
        undecidable: "list[str]" = []
        for path in _suite_files():
            doc = run_suite.load_suite(path)
            if doc["suite"]["app"] != "cascor":
                continue
            raw = (doc.get("execution") or {}).get("per_run_timeout_seconds")
            timeout = float(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool) else default_timeout
            budgets, unresolved = _effective_wall_budgets(doc, path)
            if not budgets:
                # Every cell's base config is a sibling repo this checkout cannot read, so the
                # budget is unknowable. Declining is the honest outcome — the same call
                # _inherited_wall_budgets made, and the reason CI judges 7 suites of 23.
                undecidable.append(f"{path.name} (unreadable base_config: {', '.join(unresolved)})")
                continue
            checked += 1
            with self.subTest(suite=path.relative_to(REPO_ROOT).as_posix()):
                worst = max(budgets)
                self.assertGreater(
                    timeout,
                    worst,
                    f"{path.name} sets per_run_timeout_seconds={timeout:g} against an effective wall budget of {worst:g}s, " f"so run_suite's subprocess kill pre-empts the driver: the cell is recorded 'timed_out' with exit_code null " f"and NO manifest is written. Raise per_run_timeout_seconds above {worst:g}, or lower the budget via " "execution.max_wall_seconds — the driver must be what stops a run (suites/p4/e-j-h2h-wide-cap64.yaml:73-75)",
                )
        self.assertGreater(checked, 0, f"no cascor suite was decidable — the contract would pass vacuously (undecidable: {undecidable})")

    def test_an_inverted_ordering_is_caught(self) -> None:
        """Negative control: a timeout below an inherited budget must be visible here."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text("outputs:\n  max_wall_seconds: 14400\n", encoding="utf-8")
            doc = {"suite": {"app": "cascor", "base_config": ["base.yaml"]}, "execution": {"per_run_timeout_seconds": 3600}}
            budgets, unresolved = _effective_wall_budgets(doc, root / "suite.yaml")
            self.assertEqual((budgets, unresolved), ([14400.0], []))
            self.assertLess(3600, max(budgets), "the shape e-k and e-l shipped with")

    def test_an_equal_ordering_is_caught_too(self) -> None:
        """EQUAL is a loss, not a tie — hence ``assertGreater`` rather than ``assertGreaterEqual``.

        Six shipped suites sat exactly here. The driver has to survive its own deadline long
        enough to write a manifest; a subprocess kill at the same instant pre-empts that.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text("outputs:\n  max_wall_seconds: 3600\n", encoding="utf-8")
            doc = {"suite": {"app": "cascor", "base_config": ["base.yaml"]}, "execution": {"per_run_timeout_seconds": 3600}}
            budgets, _ = _effective_wall_budgets(doc, root / "suite.yaml")
            self.assertFalse(3600 > max(budgets), "an equal ordering must NOT satisfy the contract")

    def test_a_correct_ordering_passes(self) -> None:
        """Positive control: the e-j convention (15600 over 14400) must not be flagged."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text("outputs:\n  max_wall_seconds: 14400\n", encoding="utf-8")
            doc = {"suite": {"app": "cascor", "base_config": ["base.yaml"]}, "execution": {"per_run_timeout_seconds": 15600}}
            budgets, _ = _effective_wall_budgets(doc, root / "suite.yaml")
            self.assertGreater(15600, max(budgets))

    def test_a_cell_pinning_no_budget_anywhere_still_has_one(self) -> None:
        """The inherited case that bites: no budget in suite or base means the driver default.

        Reporting no budget here would let a suite whose base pins nothing pass by default,
        which is precisely the ``cascor-budget-sweep`` / ``e-c`` shape against 3600.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text("outputs:\n  plots: []\n", encoding="utf-8")
            doc = {"suite": {"app": "cascor", "base_config": ["base.yaml"]}}
            budgets, unresolved = _effective_wall_budgets(doc, root / "suite.yaml")
            self.assertEqual(budgets, [_driver_default("DEFAULT_MAX_WALL_SECONDS")])
            self.assertEqual(unresolved, [])

    def test_execution_max_wall_seconds_wins_over_the_base_config(self) -> None:
        """CLI precedence: the forwarded flag overrides whatever the resolved config says.

        ``run_experiment.py:1883`` — ``CLI > YAML outputs.max_wall_seconds > default``. Reading
        the base here would compare the timeout against a budget the driver will never enforce.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text("outputs:\n  max_wall_seconds: 14400\n", encoding="utf-8")
            doc = {"suite": {"app": "cascor", "base_config": ["base.yaml"]}, "execution": {"max_wall_seconds": 2000}}
            self.assertEqual(_effective_wall_budgets(doc, root / "suite.yaml"), ([2000.0], []))

    def test_an_unreadable_base_config_is_declined_not_guessed(self) -> None:
        """A sibling-repo base that is not checked out must yield no verdict — the CI case."""
        with tempfile.TemporaryDirectory() as tmp:
            doc = {"suite": {"app": "cascor", "base_config": ["../../../../../juniper-cascor/conf/experiments/nope.yaml"]}}
            budgets, unresolved = _effective_wall_budgets(doc, Path(tmp) / "suite.yaml")
            self.assertEqual(budgets, [])
            self.assertEqual(len(unresolved), 1)


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
