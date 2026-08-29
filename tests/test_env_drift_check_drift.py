"""Structural drift gate for the ``juniper-env-drift-check`` console script
(test-suite audit §10.1; the env floor-drift guard shipped in juniper-ml#579).

THE INCIDENT THIS GATES (``juniper-ci-tools`` 0.5.0). #579 added the
``juniper-env-drift-check`` console script; #580 (the coverage-gap mapper),
merged after #579, **replaced** the ``[project.scripts]`` block instead of
appending -- a semantic (non-textual) merge conflict that silently dropped the
``juniper-env-drift-check`` entry point and reverted the description. The 0.5.0
wheel therefore shipped the *module* but not the *console script*
(``juniper-env-drift-check`` -> exit 127). It slipped because the behavioural
dogfood (``tests/test_env_drift_check.py``) invokes
``python -m juniper_ci_tools.cli_env_drift_check`` -- which still works when the
entry point is gone -- and the only entry-point exercise was the build smoke,
not an always-on pytest assertion. This STRUCTURAL gate (modelled on
``test_coverage_gap_mapper_drift.py``) runs in the always-on pytest job, so the
clobber can't recur silently. Fixed in 0.5.1.

Asserts:
1. ``juniper-env-drift-check`` is registered in ``juniper-ci-tools/pyproject.toml``
   ``[project.scripts]`` -> ``juniper_ci_tools.cli_env_drift_check:main``.
2. Both module halves ship (``env_drift_check.py`` + ``cli_env_drift_check.py``).
3. Version coherence: ``_version.py`` __version__ == pyproject ``[project].version``.
4. Pin coherence: juniper-ml's own workflows admit the current ci-tools version.
5. CLASS GUARD (the durable fix): **every** ``juniper_ci_tools/cli*.py`` module has a
   corresponding ``[project.scripts]`` entry -- so a future concurrent-merge clobber
   that drops *any* tool's console script fails loudly here, not silently at publish.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

# Pin-range pattern, identical to test_ci_tools_drift.py / test_coverage_gap_mapper_drift.py.
_PIN_PATTERN = re.compile(r"juniper-ci-tools\s*>=\s*([0-9]+(?:\.[0-9]+)+)\s*,\s*<\s*([0-9]+(?:\.[0-9]+)+)")

# The console-script entry #579 registers (whitespace-forgiving).
_SCRIPT_PATTERN = re.compile(r"""juniper-env-drift-check\s*=\s*["']juniper_ci_tools\.cli_env_drift_check:main["']""")

_ML_OWN_WORKFLOWS = (
    ".github/workflows/ci.yml",
    ".github/workflows/lockfile-update.yml",
    ".github/workflows/docs-full-check.yml",
)

# The two module halves of the tool (logic-module + thin-CLI-wrapper pattern).
_TOOL_MODULES = (
    "juniper-ci-tools/juniper_ci_tools/env_drift_check.py",
    "juniper-ci-tools/juniper_ci_tools/cli_env_drift_check.py",
)


def _parse_version(value: str) -> tuple[int, ...]:
    """Convert "0.5.1" -> (0, 5, 1). Ignores any pre-release/build tags."""
    return tuple(int(part.split("-")[0].split("+")[0]) for part in value.split("."))


def _read_pyproject_version(pyproject: Path) -> str | None:
    if not pyproject.exists():
        return None
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        match = re.match(r'^version\s*=\s*"([^"]+)"\s*$', line.strip())
        if match:
            return match.group(1)
    return None


def _read_dunder_version(version_py: Path) -> str | None:
    if not version_py.exists():
        return None
    match = re.search(r'__version__\s*=\s*"([^"]+)"', version_py.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def _extract_pins(yaml_text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _PIN_PATTERN.finditer(yaml_text)]


def _scripts_block(pyproject_text: str) -> str:
    """Return the body of the ``[project.scripts]`` table (up to the next table)."""
    out: list[str] = []
    in_block = False
    for line in pyproject_text.splitlines():
        stripped = line.strip()
        if stripped == "[project.scripts]":
            in_block = True
            continue
        if in_block:
            if stripped.startswith("[") and stripped.endswith("]"):
                break
            out.append(line)
    return "\n".join(out)


class EnvDriftCheckDriftTest(unittest.TestCase):
    """Structural dogfood gate for the §10.1 ``juniper-env-drift-check`` script."""

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

    def test_current_version_is_readable(self) -> None:
        self.assertIsNotNone(self.current_version, "Could not read juniper-ci-tools [project].version from juniper-ci-tools/pyproject.toml")

    def test_console_script_registered(self) -> None:
        """The juniper-env-drift-check console script is registered -- the exact
        assertion that would have caught the 0.5.0 #580 clobber."""
        self.assertTrue(self.pyproject.exists(), "juniper-ci-tools/pyproject.toml is missing")
        text = self.pyproject.read_text(encoding="utf-8")
        self.assertIn("[project.scripts]", text, "juniper-ci-tools/pyproject.toml has no [project.scripts] table")
        self.assertRegex(
            text,
            _SCRIPT_PATTERN,
            'juniper-env-drift-check = "juniper_ci_tools.cli_env_drift_check:main" is NOT registered in [project.scripts] -- the env floor-drift console script is unwired (the 0.5.0 #580 clobber regression).',
        )

    def test_tool_modules_exist(self) -> None:
        for rel in _TOOL_MODULES:
            with self.subTest(module=rel):
                self.assertTrue((self.juniper_ml_root / rel).is_file(), f"{rel} is missing")

    def test_version_dunder_matches_pyproject(self) -> None:
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

    def test_every_cli_module_has_a_console_script(self) -> None:
        """CLASS GUARD (the durable fix). Every ``juniper_ci_tools/cli*.py`` module
        is wired to a ``[project.scripts]`` entry. A concurrent-merge clobber that
        drops ANY tool's entry point (not just env-drift-check) fails here, in the
        always-on pytest job -- closing the 0.5.0 incident class. If a future
        ``cli*.py`` is intentionally NOT an entry point, allowlist it below."""
        pkg = self.ci_tools_root / "juniper_ci_tools"
        block = _scripts_block(self.pyproject.read_text(encoding="utf-8"))
        cli_modules = sorted(p.stem for p in pkg.glob("cli*.py"))
        self.assertTrue(cli_modules, "no juniper_ci_tools/cli*.py modules found -- glob/path wrong?")
        for stem in cli_modules:
            with self.subTest(module=stem):
                self.assertIn(
                    f"juniper_ci_tools.{stem}:main",
                    block,
                    f'juniper_ci_tools/{stem}.py ships a CLI but has NO [project.scripts] entry pointing at "juniper_ci_tools.{stem}:main" -- a console-script entry point was dropped (the 0.5.0 #580 class). Add the entry, or allowlist {stem} here if it is intentionally not a console script.',
                )


class HelperTest(unittest.TestCase):
    """Direct unit tests for the helpers (so they are not solely covered by the
    integration assertions)."""

    def test_parse_version(self) -> None:
        self.assertEqual(_parse_version("0.5.1"), (0, 5, 1))
        self.assertEqual(_parse_version("0.5.1-rc1"), (0, 5, 1))
        self.assertEqual(_parse_version("0.10.0"), (0, 10, 0))

    def test_extract_pins(self) -> None:
        self.assertEqual(_extract_pins('pip install "juniper-ci-tools>=0.1.0,<0.6.0"'), [("0.1.0", "0.6.0")])
        self.assertEqual(_extract_pins("nothing here"), [])

    def test_scripts_block_isolates_table(self) -> None:
        sample = '[project]\nx = 1\n[project.scripts]\nfoo = "juniper_ci_tools.cli_foo:main"\n[project.urls]\ny = 2\n'
        block = _scripts_block(sample)
        self.assertIn("cli_foo:main", block)
        self.assertNotIn("y = 2", block)

    def test_script_pattern_matches_canonical_entry(self) -> None:
        self.assertRegex('juniper-env-drift-check = "juniper_ci_tools.cli_env_drift_check:main"', _SCRIPT_PATTERN)
        self.assertNotRegex('juniper-coverage-gap-map = "juniper_ci_tools.cli_coverage_gap_mapper:main"', _SCRIPT_PATTERN)


if __name__ == "__main__":
    unittest.main()
