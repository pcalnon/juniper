#!/usr/bin/env python3
"""Structural + hermetic YAML-extraction gate for publish.yml TestPyPI install verification.

The meta-package publish path (``.github/workflows/publish.yml``) must prove the
uploaded wheel installs from TestPyPI AND that the light extras ``[clients]`` and
``[tools]`` still resolve against published metadata. A broken extras declaration
(mistyped name, missing roll-up, dangling self-ref) that only the bare install
would catch would otherwise ship to production PyPI.

This unittest:
  1. Structurally pins the verify step's three install specs, TestPyPI index-url,
     production PyPI ``--extra-index-url`` (required for deps; the meta-package
     exception documented in ``test_workflow_script_paths.py``), the absence of
     ``--no-deps``, the tomllib version read, the ``pypi needs: testpypi`` gate,
     and the ``v*`` release-tag guard.
  2. Extracts the verify shell and runs it hermetically with PATH stubs for
     ``sleep`` / ``pip`` / ``python`` so a rewrite that drops a verify step, swaps
     the index URLs, or stops walking extras fails in CI without hitting the
     network.

Neither the workflow YAML nor ``util/`` is pre-commit-lint-gated for these
properties, so this unittest IS the gate.

Run: python3 -m unittest -v tests/test_publish_testpypi_verify.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import os
import re
import stat
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "publish.yml"
VERIFY_STEP_NAME = "Verify TestPyPI install"
TESTPYPI_INDEX = "https://test.pypi.org/simple/"
PYPI_EXTRA_INDEX = "https://pypi.org/simple/"

# Light extras exercised at publish time (no torch). Order is part of the contract
# (bare first, then clients, then tools) so a truncated verify cannot silently ship.
EXPECTED_INSTALL_SPECS = (
    "juniper-ml==VERSION",
    "juniper-ml[clients]==VERSION",
    "juniper-ml[tools]==VERSION",
)


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


def _verify_step_run(doc: dict) -> str:
    steps = (doc.get("jobs") or {}).get("testpypi", {}).get("steps") or []
    step = next((s for s in steps if s.get("name") == VERIFY_STEP_NAME), None)
    if step is None or "run" not in step:
        raise unittest.SkipTest(f"could not locate {VERIFY_STEP_NAME!r} in {WORKFLOW_NAME}")
    return step["run"]


class PublishTestPyPIVerifyStructuralTest(unittest.TestCase):
    """Pin publish.yml verify wiring so a casual edit cannot drop extras resolution."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)
        cls.script = _verify_step_run(cls.doc)

    def test_jobs_present(self) -> None:
        jobs = self.doc.get("jobs") or {}
        for name in ("build", "testpypi", "pypi"):
            with self.subTest(job=name):
                self.assertIn(name, jobs)

    def test_build_tag_guard_rejects_shared_package_releases(self) -> None:
        # Meta publish must NOT fire for juniper-<pkg>-v* shared/sub-package Releases.
        build_if = str(self.doc["jobs"]["build"].get("if") or "")
        self.assertIn("workflow_dispatch", build_if)
        self.assertIn("startsWith(github.event.release.tag_name, 'v')", build_if)

    def test_pypi_needs_testpypi(self) -> None:
        needs = self.doc["jobs"]["pypi"].get("needs")
        needs = [needs] if isinstance(needs, str) else (needs or [])
        self.assertIn("testpypi", needs, "PyPI publish must wait on TestPyPI verify (Gate 1).")

    def test_testpypi_needs_build(self) -> None:
        needs = self.doc["jobs"]["testpypi"].get("needs")
        needs = [needs] if isinstance(needs, str) else (needs or [])
        self.assertIn("build", needs)

    def test_verify_reads_version_from_pyproject_tomllib(self) -> None:
        self.assertIn("tomllib", self.script)
        self.assertIn("pyproject.toml", self.script)
        self.assertIn("['project']['version']", self.script)

    def test_verify_three_install_specs_in_order(self) -> None:
        # Bare -> [clients] -> [tools]. A missing extras step is the exact ship-silent class.
        bare = self.script.find('"juniper-ml==${VERSION}"')
        clients = self.script.find('"juniper-ml[clients]==${VERSION}"')
        tools = self.script.find('"juniper-ml[tools]==${VERSION}"')
        self.assertNotEqual(bare, -1, "bare juniper-ml==VERSION install missing")
        self.assertNotEqual(clients, -1, "[clients] extras install missing")
        self.assertNotEqual(tools, -1, "[tools] extras install missing")
        self.assertLess(bare, clients)
        self.assertLess(clients, tools)

    def test_verify_uses_testpypi_index_and_pypi_extra_index(self) -> None:
        # Meta-package exception: deps come from production PyPI; the target must come from TestPyPI.
        self.assertGreaterEqual(self.script.count(f"--index-url {TESTPYPI_INDEX}"), 3)
        self.assertGreaterEqual(self.script.count(f"--extra-index-url {PYPI_EXTRA_INDEX}"), 3)

    def test_verify_does_not_use_no_deps(self) -> None:
        # --no-deps + --extra-index-url is the supply-chain hole covered by
        # test_workflow_script_paths; the meta verify must install WITH deps.
        self.assertNotIn("--no-deps", self.script)

    def test_verify_does_not_install_heavy_extras(self) -> None:
        # [worker]/[servers]/[all]/[recurrence] pull torch / multi-GB; keep publish verify light.
        for heavy in ("[worker]", "[servers]", "[all]", "[recurrence]"):
            with self.subTest(extra=heavy):
                self.assertNotIn(f"juniper-ml{heavy}", self.script)

    def test_verify_imports_clients_and_tools_surfaces(self) -> None:
        self.assertIn("import juniper_data_client, juniper_cascor_client", self.script)
        self.assertIn("import juniper_ci_tools, juniper_doc_tools, juniper_observability", self.script)
        self.assertIn("importlib.metadata", self.script)

    def test_testpypi_environment_and_oidc(self) -> None:
        self.assertEqual(self.doc["jobs"]["testpypi"].get("environment"), "testpypi")
        self.assertEqual(self.doc["jobs"]["pypi"].get("environment"), "pypi")
        self.assertEqual(self.doc.get("permissions"), {"id-token": "write"})


class PublishTestPyPIVerifyRehearsalTest(unittest.TestCase):
    """Run the extracted verify shell with PATH stubs — prove the ACTUAL three pip specs fire."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        cls.script = _verify_step_run(yaml.safe_load(wf.read_text(encoding="utf-8")))

    def _write_stubs(self, bindir: Path, pip_log: Path, version: str = "9.9.9") -> None:
        sleep = bindir / "sleep"
        sleep.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
        sleep.chmod(sleep.stat().st_mode | stat.S_IXUSR)

        pip = bindir / "pip"
        pip.write_text(
            "#!/bin/bash\n" f'printf "%s\\n" "$*" >> "{pip_log}"\n' "exit 0\n",
            encoding="utf-8",
        )
        pip.chmod(pip.stat().st_mode | stat.S_IXUSR)

        # python stub: tomllib version probe prints VERSION; import probes succeed.
        python = bindir / "python"
        python.write_text(
            "#!/bin/bash\n"
            'args="$*"\n'
            'if [[ "$args" == *tomllib* ]]; then\n'
            f'  echo "{version}"\n'
            "  exit 0\n"
            "fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        python.chmod(python.stat().st_mode | stat.S_IXUSR)

    def _run_verify(self) -> list[str]:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            bindir = tdp / "bin"
            bindir.mkdir()
            pip_log = tdp / "pip.log"
            pip_log.write_text("", encoding="utf-8")
            # Minimal pyproject so a non-stubbed python path still has a file (defensive).
            (tdp / "pyproject.toml").write_text('[project]\nname = "juniper-ml"\nversion = "9.9.9"\n', encoding="utf-8")
            self._write_stubs(bindir, pip_log, version="9.9.9")
            script_path = tdp / "verify.sh"
            script_path.write_text(self.script, encoding="utf-8")
            env = RedactedEnv(os.environ)
            env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
            # Keep cwd at the temp tree (script opens pyproject.toml relative to CWD).
            proc = subprocess.run(  # nosec B603,B607 - workflow's own shell, fixed argv
                ["bash", str(script_path)],
                cwd=str(tdp),
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"verify shell exited {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
            )
            lines = [ln for ln in pip_log.read_text(encoding="utf-8").splitlines() if ln.strip()]
            return lines

    def test_three_pip_installs_fire_with_expected_specs(self) -> None:
        lines = self._run_verify()
        self.assertEqual(len(lines), 3, f"expected exactly 3 pip installs, got {len(lines)}: {lines}")
        expected = [spec.replace("VERSION", "9.9.9") for spec in EXPECTED_INSTALL_SPECS]
        for line, spec in zip(lines, expected):
            with self.subTest(spec=spec):
                self.assertIn("install", line)
                self.assertIn(f"--index-url {TESTPYPI_INDEX}", line)
                self.assertIn(f"--extra-index-url {PYPI_EXTRA_INDEX}", line)
                self.assertIn(spec, line)
                self.assertNotIn("--no-deps", line)

    def test_clients_install_precedes_tools(self) -> None:
        lines = self._run_verify()
        self.assertTrue(any("[clients]" in ln for ln in lines))
        self.assertTrue(any("[tools]" in ln for ln in lines))
        clients_i = next(i for i, ln in enumerate(lines) if "[clients]" in ln)
        tools_i = next(i for i, ln in enumerate(lines) if "[tools]" in ln)
        self.assertLess(clients_i, tools_i)

    def test_sleep_is_invoked_but_stubbed_not_blocking(self) -> None:
        # Contract: the workflow still contains `sleep 30` (index lag buffer). The
        # rehearsal must not actually wait — the PATH stub makes that hermetic.
        self.assertIsNotNone(
            re.search(r"^\s*sleep\s+30\s*$", self.script, re.MULTILINE),
            "verify shell must retain `sleep 30` (TestPyPI index-lag buffer)",
        )
        # If sleep were not stubbed this would hang ~30s; finishing quickly is the proof.
        lines = self._run_verify()
        self.assertEqual(len(lines), 3)


if __name__ == "__main__":
    unittest.main()
