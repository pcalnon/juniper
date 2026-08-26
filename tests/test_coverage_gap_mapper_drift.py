"""Dogfood / drift gate for the ``juniper-coverage-gap-map`` console script
(enhancement E-4, plan
``notes/JUNIPER_2026-06-27_JUNIPER-ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS-PLAN.md`` §6.7,
Phase-2 PR-6).

The advisory per-file coverage-gap mapper is hosted in the
``juniper-ci-tools`` sub-package (its own pytest suite is the behavioural
gate, run by ``.github/workflows/ci-ci-tools.yml``). This juniper-ml-side
test is the **structural** dogfood gate, modelled on
``tests/test_ci_tools_drift.py``. It asserts:

1. The ``juniper-coverage-gap-map`` console script is registered in
   ``juniper-ci-tools/pyproject.toml`` ``[project.scripts]`` and points at
   ``juniper_ci_tools.cli_coverage_gap_mapper:main``.
2. Both halves of the tool ship: the logic module
   (``coverage_gap_mapper.py``) and the CLI wrapper
   (``cli_coverage_gap_mapper.py``).
3. The version is coherent: ``juniper_ci_tools/_version.py``'s
   ``__version__`` equals ``pyproject.toml`` ``[project].version``.
4. The pin is coherent: juniper-ml's own workflows
   (``ci.yml`` / ``lockfile-update.yml`` / ``docs-full-check.yml``) pin a
   ``juniper-ci-tools>=X,<Y`` range that still admits the current version --
   so bumping ci-tools to ship E-4 without widening the pin ceiling fails
   loudly here (the same coupling ``test_ci_tools_drift.py`` enforces).
5. The **C-0 enforcing mode** is wired and behaves: the opt-in ``--enforce``
   flag (plus ``--fail-under-file`` / ``--fail-under-submodule`` / ``--omit``)
   is declared in the CLI, AND an end-to-end invocation of the shipped entry
   point over a synthetic ``coverage.json`` exits ``1`` on a gap, ``0`` when
   clean, ``0`` on ``--help``, and ``0`` for the advisory default (no
   ``--enforce``). Work-unit C-0 of
   ``notes/JUNIPER_2026-06-30_JUNIPER-ECOSYSTEM_PER-FILE-COVERAGE-ROLLOUT-SCOPING.md``.

Why this is (mostly) a STRUCTURAL gate (the manual-verify note)
--------------------------------------------------------------
The mapper's *point* is to run coverage over a target repo and map the
per-file gaps. That cross-repo coverage RUN **cannot execute in juniper-ml
CI**: juniper-ml is a meta-package with no application package to measure,
and the target repos (cascor-model, canopy, ...) are not checked out in the
per-PR ubuntu runner. So the run-coverage half is structural only -- it proves
the tool is *shipped and wired*, not that a live coverage run behaves. What
this gate DOES exercise end-to-end is the **primary JSON-parsing path**: the
C-0 checks (item 5) write a synthetic ``coverage.json`` and invoke the shipped
console entry (``python -m juniper_ci_tools.cli_coverage_gap_mapper``) with the
ci-tools subdir on ``PYTHONPATH`` -- no real coverage run, no target repo, so
it is deterministic in the ubuntu runner. The full behavioural matrix lives in
``juniper-ci-tools/tests/test_coverage_gap_mapper.py`` (synthetic
``coverage.json`` fixtures); the CROSS-REPO real coverage run remains a
documented **manual-verify** invocation an operator runs against a real repo::

    # From a target repo with a real test command (e.g. juniper-cascor's
    # cascor-model package, whose CI has no per-file coverage gate):
    cd <target-repo>
    pip install "juniper-ci-tools>=0.6.0,<0.7.0"
    juniper-coverage-gap-map --repo-root . --package <pkg> \\
        --test-command "python -m pytest"
    # -> prints the per-file distribution, the files below 90%, and each
    #    sub-module's average vs the 95% bar; exits 0 regardless (advisory).

    # Or against a pre-generated coverage.json (the primary path):
    juniper-coverage-gap-map --coverage-json coverage.json --json

    # C-0 enforcing gate (opt-in): exit 1 on a per-file statement gap or a
    # sub-module pooled gap; --omit drops thin shims before gating.
    juniper-coverage-gap-map --coverage-json coverage.json --enforce \\
        --fail-under-file 90 --fail-under-submodule 95 --omit '*/__main__.py'

Skip semantics mirror ``test_ci_tools_drift.py``: there is no consumer-repo
pin for this brand-new script yet, so there is no cross-repo sibling
assertion to run; the structural checks above are all juniper-ml-local and
run unconditionally. ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`` is honoured only by
the informational environment probe, for parity with the sibling drift tests.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

# Pin-range pattern, identical to test_ci_tools_drift.py:
#   pip install "juniper-ci-tools>=0.1.0,<0.6.0"
_PIN_PATTERN = re.compile(r"juniper-ci-tools\s*>=\s*([0-9]+(?:\.[0-9]+)+)\s*,\s*<\s*([0-9]+(?:\.[0-9]+)+)")

# The console-script entry E-4 registers (whitespace-forgiving).
_SCRIPT_PATTERN = re.compile(r"""juniper-coverage-gap-map\s*=\s*["']juniper_ci_tools\.cli_coverage_gap_mapper:main["']""")

# juniper-ml's own workflows that pin juniper-ci-tools (same set as
# test_ci_tools_drift.py's _ML_OWN_WORKFLOWS).
_ML_OWN_WORKFLOWS = (
    ".github/workflows/ci.yml",
    ".github/workflows/lockfile-update.yml",
    ".github/workflows/docs-full-check.yml",
)

# Blocking per-file workflow gates must be paired with the coverage JSON they
# consume and an enforcing-capable ci-tools install.
_COVERAGE_GATE_INVOCATION = "juniper-coverage-gap-map --coverage-json coverage.json --enforce"
_COVERAGE_JSON_REPORT_FLAG = "--cov-report=json:coverage.json"
_COVERAGE_GATE_MIN_VERSION = "0.6.0"

# The two module halves of the tool (the logic-module + thin-CLI-wrapper
# pattern mirrored from lint_agents_md_version.py / cli_lint_agents_md_version.py).
_TOOL_MODULES = (
    "juniper-ci-tools/juniper_ci_tools/coverage_gap_mapper.py",
    "juniper-ci-tools/juniper_ci_tools/cli_coverage_gap_mapper.py",
)


def _parse_version(value: str) -> tuple[int, ...]:
    """Convert "0.5.0" -> (0, 5, 0). Ignores any pre-release tags."""
    return tuple(int(part.split("-")[0].split("+")[0]) for part in value.split("."))


def _read_pyproject_version(pyproject: Path) -> str | None:
    """Read ``[project].version`` from the ci-tools pyproject (regex, like the
    sibling drift test -- no tomllib dependency)."""
    if not pyproject.exists():
        return None
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        match = re.match(r'^version\s*=\s*"([^"]+)"\s*$', line.strip())
        if match:
            return match.group(1)
    return None


def _read_dunder_version(version_py: Path) -> str | None:
    """Read ``__version__`` from ``_version.py``."""
    if not version_py.exists():
        return None
    match = re.search(r'__version__\s*=\s*"([^"]+)"', version_py.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def _extract_pins(yaml_text: str) -> list[tuple[str, str]]:
    """Every ``juniper-ci-tools>=X,<Y`` (lower, upper) pair in the text."""
    return [(m.group(1), m.group(2)) for m in _PIN_PATTERN.finditer(yaml_text)]


def _has_admitting_gate_pin(yaml_text: str, current_version: str) -> bool:
    """Return true when a workflow installs a ci-tools range suitable for the
    blocking per-file gate.

    The lower bound must be at least 0.6.0, the release that introduced the
    enforcing coverage gate used by these workflows; the upper bound must still
    admit the in-tree ci-tools version.
    """
    current = _parse_version(current_version)
    minimum = _parse_version(_COVERAGE_GATE_MIN_VERSION)
    return any(minimum <= _parse_version(lower) <= current < _parse_version(upper) for lower, upper in _extract_pins(yaml_text))


class CoverageGapMapperDriftTest(unittest.TestCase):
    """Structural dogfood gate for the E-4 ``juniper-coverage-gap-map`` script."""

    # Declared so the annotated method bodies type-check (the attributes are
    # populated in setUpClass; mypy checks annotated bodies under this config).
    juniper_ml_root: Path
    ci_tools_root: Path
    pyproject: Path
    version_py: Path
    current_version: str | None

    @classmethod
    def setUpClass(cls) -> None:
        cls.juniper_ml_root = Path(__file__).resolve().parent.parent
        cls.ci_tools_root = cls.juniper_ml_root / "juniper-ci-tools"
        cls.pyproject = cls.ci_tools_root / "pyproject.toml"
        cls.version_py = cls.ci_tools_root / "juniper_ci_tools" / "_version.py"
        cls.current_version = _read_pyproject_version(cls.pyproject)

    def test_environment_note(self) -> None:
        """Informational: state plainly that the cross-repo coverage run is a
        documented manual-verify step, not a CI assertion (so an operator
        reading CI logs is not confused). Mirrors test_ci_tools_drift.py's
        environment sanity probe."""
        forced = os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL")
        print("INFO: coverage-gap-mapper drift gate is STRUCTURAL -- the real per-file " "coverage run is a manual-verify step (see module docstring); juniper-ml CI " f"cannot run it (meta-package; no target repo checked out). FORCE_LOCAL={forced!r}")

    def test_current_version_is_readable(self) -> None:
        self.assertIsNotNone(
            self.current_version,
            "Could not read juniper-ci-tools [project].version from juniper-ci-tools/pyproject.toml; the drift gate depends on it as the source of truth for 'current'.",
        )

    def test_console_script_registered(self) -> None:
        """The juniper-coverage-gap-map console script is registered and points
        at the CLI wrapper's ``:main``."""
        self.assertTrue(self.pyproject.exists(), "juniper-ci-tools/pyproject.toml is missing")
        text = self.pyproject.read_text(encoding="utf-8")
        self.assertIn("[project.scripts]", text, "juniper-ci-tools/pyproject.toml has no [project.scripts] table")
        self.assertRegex(
            text,
            _SCRIPT_PATTERN,
            'juniper-coverage-gap-map = "juniper_ci_tools.cli_coverage_gap_mapper:main" is not registered in [project.scripts] -- E-4 console script unwired.',
        )

    def test_tool_modules_exist(self) -> None:
        """Both the logic module and the thin CLI wrapper ship."""
        for rel in _TOOL_MODULES:
            with self.subTest(module=rel):
                self.assertTrue((self.juniper_ml_root / rel).is_file(), f"{rel} is missing -- E-4 module not shipped")

    def test_version_dunder_matches_pyproject(self) -> None:
        """``_version.py`` __version__ mirrors pyproject [project].version."""
        if self.current_version is None:
            self.skipTest("no current version available")
        dunder = _read_dunder_version(self.version_py)
        self.assertIsNotNone(dunder, "juniper_ci_tools/_version.py has no __version__")
        self.assertEqual(
            dunder,
            self.current_version,
            f"_version.py __version__ ({dunder}) != pyproject [project].version ({self.current_version}); bump both in the same PR.",
        )

    def test_ml_own_workflow_pins_admit_current(self) -> None:
        """juniper-ml's own workflow pins must admit the current ci-tools
        version. Shipping E-4 as a minor bump (0.4.0 -> 0.5.0) without widening
        the ``<X.Y.0`` ceiling here fails loudly -- the exact coupling this and
        test_ci_tools_drift.py exist to catch."""
        if self.current_version is None:
            self.skipTest("no current version available")
        current = _parse_version(self.current_version)
        for rel in _ML_OWN_WORKFLOWS:
            with self.subTest(workflow=rel):
                workflow = self.juniper_ml_root / rel
                if not workflow.exists():
                    self.skipTest(f"{rel} not present in this checkout")
                pins = _extract_pins(workflow.read_text(encoding="utf-8"))
                self.assertGreater(len(pins), 0, f"{rel} no longer pins juniper-ci-tools")
                for lower, upper in pins:
                    self.assertLessEqual(_parse_version(lower), current, f"{rel} pin lower bound {lower} is ahead of current {self.current_version}")
                    self.assertLess(current, _parse_version(upper), f"{rel} pin upper bound {upper} excludes current {self.current_version} -- widen the ceiling in the same PR as the ci-tools bump.")

    def test_enforce_flags_are_wired(self) -> None:
        """C-0 STRUCTURAL: the CLI declares the opt-in enforcing flags. Guards
        against the enforcing mode silently regressing to advisory-only (e.g. a
        concurrent-merge clobber of the argparse block)."""
        cli = self.ci_tools_root / "juniper_ci_tools" / "cli_coverage_gap_mapper.py"
        self.assertTrue(cli.is_file(), f"{cli} is missing")
        text = cli.read_text(encoding="utf-8")
        for flag in ('"--enforce"', '"--fail-under-file"', '"--fail-under-submodule"', '"--omit"'):
            with self.subTest(flag=flag):
                self.assertIn(flag, text, f"cli_coverage_gap_mapper.py does not declare {flag} -- the C-0 enforcing mode is unwired.")

    def test_blocking_workflow_gates_have_json_input_and_current_ci_tools(self) -> None:
        """Every blocking workflow gate must have the coverage.json producer and
        install an enforcing-capable ``juniper-ci-tools`` range.

        This catches the high-blast-radius failure mode where a workflow wires
        ``juniper-coverage-gap-map --coverage-json coverage.json --enforce`` but
        later drops ``--cov-report=json:coverage.json`` or relaxes the ci-tools
        pin below the release that ships the enforcing mode.
        """
        if self.current_version is None:
            self.skipTest("no current version available")

        workflows_dir = self.juniper_ml_root / ".github" / "workflows"
        gated_workflows: list[Path] = []
        missing_json: list[Path] = []
        bad_pin: list[Path] = []

        for workflow in sorted(workflows_dir.glob("*.yml")) + sorted(workflows_dir.glob("*.yaml")):
            text = workflow.read_text(encoding="utf-8")
            if _COVERAGE_GATE_INVOCATION not in text:
                continue
            gated_workflows.append(workflow)
            if _COVERAGE_JSON_REPORT_FLAG not in text:
                missing_json.append(workflow)
            if not _has_admitting_gate_pin(text, self.current_version):
                bad_pin.append(workflow)

        self.assertGreater(len(gated_workflows), 0, "No blocking per-file coverage workflow gates found; the rollout gate may have been removed.")
        self.assertEqual(
            missing_json,
            [],
            "Blocking per-file coverage gate workflow(s) do not produce coverage.json via " f"{_COVERAGE_JSON_REPORT_FLAG}: " + ", ".join(str(p.relative_to(self.juniper_ml_root)) for p in missing_json),
        )
        self.assertEqual(
            bad_pin,
            [],
            "Blocking per-file coverage gate workflow(s) do not install a juniper-ci-tools range with lower bound >= " f"{_COVERAGE_GATE_MIN_VERSION} that admits current {self.current_version}: " + ", ".join(str(p.relative_to(self.juniper_ml_root)) for p in bad_pin),
        )


class CoverageGapMapperEnforceEndToEndTest(unittest.TestCase):
    """C-0 END-TO-END: invoke the shipped console entry over a synthetic
    ``coverage.json`` and assert the ``--enforce`` exit-code contract.

    Deterministic in the ubuntu runner -- this exercises only the primary
    JSON-parsing path (no real coverage run, no target repo checked out). Since
    ``juniper_ci_tools`` is not pip-installed in juniper-ml CI, the ci-tools
    subdir is put on ``PYTHONPATH`` for the child process (juniper-ml CI installs
    the package's import-time deps, PyYAML + packaging, in the tests job).
    """

    juniper_ml_root: Path
    ci_tools_root: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.juniper_ml_root = Path(__file__).resolve().parent.parent
        cls.ci_tools_root = cls.juniper_ml_root / "juniper-ci-tools"

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        """Invoke the shipped module-form entry with the ci-tools subdir on PYTHONPATH."""
        env = RedactedEnv(os.environ)
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(self.ci_tools_root) + (os.pathsep + existing if existing else "")
        cmd = [sys.executable, "-m", "juniper_ci_tools.cli_coverage_gap_mapper", *args]
        return subprocess.run(cmd, capture_output=True, text=True, env=env)

    @staticmethod
    def _write_cov(tmp: Path, files: dict, name: str = "coverage.json") -> Path:
        """Write a synthetic coverage.json from ``path -> (num_statements, covered)``."""
        out: dict = {"files": {}}
        for path, (num, covered) in files.items():
            pct = 100.0 if num == 0 else 100.0 * covered / num
            out["files"][path] = {"summary": {"num_statements": num, "covered_lines": covered, "missing_lines": max(num - covered, 0), "percent_covered": pct}}
        dest = tmp / name
        dest.write_text(json.dumps(out), encoding="utf-8")
        return dest

    def test_help_exits_zero_and_lists_enforce(self) -> None:
        proc = self._run("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--enforce", proc.stdout)

    def test_enforce_exits_one_on_gap_naming_the_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gap = self._write_cov(Path(td), {"pkg/low.py": (10, 1), "pkg/ok.py": (10, 10)})
            proc = self._run("--coverage-json", str(gap), "--enforce")
            self.assertEqual(proc.returncode, 1, f"expected exit 1 on a gap; stdout={proc.stdout!r} stderr={proc.stderr!r}")
            self.assertIn("pkg/low.py", proc.stdout)
            self.assertIn("FAIL", proc.stdout)

    def test_enforce_exits_zero_when_clean(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            clean = self._write_cov(Path(td), {"pkg/ok.py": (10, 10), "pkg/also.py": (20, 20)})
            proc = self._run("--coverage-json", str(clean), "--enforce")
            self.assertEqual(proc.returncode, 0, f"expected exit 0 when clean; stdout={proc.stdout!r} stderr={proc.stderr!r}")

    def test_advisory_default_exits_zero_on_gap(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gap = self._write_cov(Path(td), {"pkg/dead.py": (20, 0)})
            proc = self._run("--coverage-json", str(gap))
            self.assertEqual(proc.returncode, 0, f"advisory default must exit 0; stdout={proc.stdout!r} stderr={proc.stderr!r}")
            self.assertNotIn("Enforcing gate", proc.stdout)

    def test_omit_excludes_offender_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gap = self._write_cov(Path(td), {"pkg/main.py": (10, 10), "pkg/__main__.py": (4, 0)})
            self.assertEqual(self._run("--coverage-json", str(gap), "--enforce").returncode, 1)
            proc = self._run("--coverage-json", str(gap), "--enforce", "--omit", "*/__main__.py")
            self.assertEqual(proc.returncode, 0, f"--omit should exclude the shim -> clean -> exit 0; stdout={proc.stdout!r} stderr={proc.stderr!r}")


class PinHelperTest(unittest.TestCase):
    """Direct unit tests for the helpers so they are not solely reliant on the
    integration assertions for coverage."""

    def test_parse_version(self) -> None:
        self.assertEqual(_parse_version("0.5.0"), (0, 5, 0))
        self.assertEqual(_parse_version("0.5.0-rc1"), (0, 5, 0))
        self.assertEqual(_parse_version("0.10.0"), (0, 10, 0))

    def test_extract_pins(self) -> None:
        self.assertEqual(_extract_pins('pip install "juniper-ci-tools>=0.1.0,<0.6.0"'), [("0.1.0", "0.6.0")])
        self.assertEqual(_extract_pins("nothing here"), [])

    def test_gate_pin_helper_requires_enforcing_capable_lower_bound(self) -> None:
        self.assertTrue(_has_admitting_gate_pin('pip install "juniper-ci-tools>=0.6.0,<0.7.0"', "0.6.0"))
        self.assertFalse(_has_admitting_gate_pin('pip install "juniper-ci-tools>=0.1.0,<0.7.0"', "0.6.0"))

    def test_gate_pin_helper_rejects_current_version_excluded_by_upper_bound(self) -> None:
        self.assertFalse(_has_admitting_gate_pin('pip install "juniper-ci-tools>=0.6.0,<0.6.1"', "0.6.1"))

    def test_script_pattern_matches_canonical_entry(self) -> None:
        self.assertRegex('juniper-coverage-gap-map = "juniper_ci_tools.cli_coverage_gap_mapper:main"', _SCRIPT_PATTERN)
        self.assertNotRegex('juniper-lint-workflow-paths = "juniper_ci_tools.cli_lint_workflow_paths:main"', _SCRIPT_PATTERN)


if __name__ == "__main__":
    unittest.main()
