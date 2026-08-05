#!/usr/bin/env python3
"""Structural + hermetic YAML-extraction gate for security-scan.yml.

The weekly ``.github/workflows/security-scan.yml`` is the ecosystem's
scheduled dependency vulnerability screen. Unlike the per-PR ``ci.yml``
``security`` job (which deliberately omits ``--strict`` because editable
skips count as findings), the scheduled scan MUST run:

  ``pip-audit --strict --desc on``

after ``pip install -e .`` so a known CVSS finding fails the run. Neither
the workflow YAML nor ``util/`` is otherwise lint-gated for this contract,
so this unittest IS the gate.

Distinct from open #937 (Quality Gate soft-fail wiring for the *per-PR*
security job) — this file pins the *scheduled* workflow's audit flags.

Run: python3 -m unittest -v tests/test_security_scan_workflow.py

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

WORKFLOW_NAME = "security-scan.yml"
JOB_NAME = "security-scan"
INSTALL_STEP = "Install dependencies"
AUDIT_STEP = "Run pip-audit (Dependency Vulnerabilities)"
STRICT_AUDIT = "pip-audit --strict --desc on"


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


def _step_run(job: dict, name: str) -> str:
    steps = job.get("steps") or []
    step = next((s for s in steps if s.get("name") == name), None)
    if step is None or "run" not in step:
        raise unittest.SkipTest(f"could not locate step {name!r} in {WORKFLOW_NAME}")
    return step["run"]


class SecurityScanStructuralTest(unittest.TestCase):
    """Pin security-scan.yml so a casual edit cannot drop --strict or widen perms."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)
        cls.job = (cls.doc.get("jobs") or {}).get(JOB_NAME)
        if cls.job is None:
            raise unittest.SkipTest(f"{WORKFLOW_NAME} has no {JOB_NAME} job")
        cls.install_script = _step_run(cls.job, INSTALL_STEP)
        cls.audit_script = _step_run(cls.job, AUDIT_STEP)

    def test_schedule_and_dispatch_triggers(self) -> None:
        on = self.doc.get("on") or self.doc.get(True) or {}
        self.assertIn("workflow_dispatch", on)
        schedule = on.get("schedule") or []
        crons = [s.get("cron") for s in schedule if isinstance(s, dict)]
        self.assertTrue(any(crons), "scheduled security scan must keep a cron trigger")

    def test_permissions_are_contents_read_only(self) -> None:
        perms = self.doc.get("permissions") or {}
        self.assertEqual(perms, {"contents": "read"})

    def test_installs_editable_before_audit(self) -> None:
        # Bare ``pip-audit`` without the package installed audits nothing useful.
        self.assertIn("pip install pip-audit", self.install_script)
        self.assertIn("pip install -e .", self.install_script)

    def test_audit_uses_strict_and_desc(self) -> None:
        # --strict is the load-bearing flag: without it findings are soft.
        # Distinct from ci.yml's per-PR job which intentionally omits --strict.
        self.assertIn(STRICT_AUDIT, self.audit_script)
        self.assertNotIn("--skip-editable", self.audit_script)
        # Single audit invocation — no soft follow-up that swallows the exit.
        invocations = re.findall(r"^\s*pip-audit\b.*$", self.audit_script, re.MULTILINE)
        self.assertEqual(len(invocations), 1, msg=invocations)
        self.assertIn("--strict", invocations[0])
        self.assertIn("--desc on", invocations[0])

    def test_python_version_is_pinned(self) -> None:
        steps = self.job.get("steps") or []
        setup = next(
            (
                s
                for s in steps
                if isinstance(s.get("uses"), str) and "actions/setup-python@" in s["uses"]
            ),
            None,
        )
        self.assertIsNotNone(setup)
        self.assertEqual((setup.get("with") or {}).get("python-version"), "3.12")


class SecurityScanRehearsalTest(unittest.TestCase):
    """Run the extracted install + audit shells with PATH stubs — prove --strict fires."""

    install_script: str
    audit_script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        job = yaml.safe_load(wf.read_text(encoding="utf-8"))["jobs"][JOB_NAME]
        cls.install_script = _step_run(job, INSTALL_STEP)
        cls.audit_script = _step_run(job, AUDIT_STEP)

    def _write_stubs(self, bindir: Path, pip_log: Path, audit_log: Path) -> None:
        # Avoid f-strings that embed bash `${…}` expansions (3.12 parse hazards).
        python = bindir / "python"
        python.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'if [ "${1-}" = "-m" ] && [ "${2-}" = "pip" ]; then\n'
            '  printf "python-m-pip %s\\n" "${*:3}" >> "' + str(pip_log) + '"\n'
            "  exit 0\n"
            "fi\n"
            'echo "unexpected python argv: $*" >&2\n'
            "exit 2\n",
            encoding="utf-8",
        )
        python.chmod(python.stat().st_mode | stat.S_IXUSR)

        pip = bindir / "pip"
        pip.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'printf "pip %s\\n" "$*" >> "' + str(pip_log) + '"\n'
            "exit 0\n",
            encoding="utf-8",
        )
        pip.chmod(pip.stat().st_mode | stat.S_IXUSR)

        audit = bindir / "pip-audit"
        audit.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'printf "%s\\n" "$*" >> "' + str(audit_log) + '"\n'
            "exit 0\n",
            encoding="utf-8",
        )
        audit.chmod(audit.stat().st_mode | stat.S_IXUSR)

    def test_install_then_strict_audit_argv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            bindir = td_path / "bin"
            bindir.mkdir()
            pip_log = td_path / "pip.log"
            audit_log = td_path / "audit.log"
            pip_log.write_text("", encoding="utf-8")
            audit_log.write_text("", encoding="utf-8")
            self._write_stubs(bindir, pip_log, audit_log)

            env = RedactedEnv(os.environ)
            env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")

            install = td_path / "install.sh"
            install.write_text(self.install_script, encoding="utf-8")
            audit = td_path / "audit.sh"
            audit.write_text(self.audit_script, encoding="utf-8")

            for script in (install, audit):
                proc = subprocess.run(  # nosec B603,B607 - workflow shell, fixed argv
                    ["bash", str(script)],
                    cwd=td_path,
                    capture_output=True,
                    text=True,
                    env=env,
                    check=False,
                    timeout=15,
                )
                self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)

            pip_lines = pip_log.read_text(encoding="utf-8")
            self.assertIn("pip-audit", pip_lines)
            self.assertRegex(pip_lines, r"(^|\n)(pip |python-m-pip ).*-e \.")

            audit_argv = audit_log.read_text(encoding="utf-8").strip()
            self.assertEqual(audit_argv, "--strict --desc on")


if __name__ == "__main__":
    unittest.main()
