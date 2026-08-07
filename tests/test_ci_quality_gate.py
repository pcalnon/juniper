#!/usr/bin/env python3
"""Structural + YAML-extraction rehearsal for ci.yml Quality Gate advisory exclusion.

Flood-remediation P2 / soak convention: ``sequence-safety``, ``fleet-pr-lint``, and
``release-train-archive-guard`` MUST stay ABSENT from ``required-checks.needs``.
Those jobs skip on ``push:main`` (or are PR-only); the Quality Gate is
``if: always()`` and treats any non-success need as fatal — folding an advisory
job into ``needs:`` paints every push red.

Security is soft-fail: ``needs.security.result == failure`` errors, but
``skipped`` stays green (intentional when the security job is gated off).

This unittest parses ``ci.yml`` with PyYAML and extracts the Quality Gate shell
(substituting ``${{ needs.*.result }}``) — the same "run the real thing" idiom
as ``tests/test_release_train_workflow_guard.py``.

Run: python3 -m unittest -v tests/test_ci_quality_gate.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import os
import re
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "ci.yml"
QG_JOB = "required-checks"
QG_STEP_NAME = "Check Quality Gate Status"

# Jobs that must NEVER appear in the Quality Gate needs: (advisory / PR-only soak).
ADVISORY_EXCLUDED = frozenset(
    {
        "sequence-safety",
        "fleet-pr-lint",
        "release-train-archive-guard",
    }
)

# Required hard needs (the QG must keep these).
REQUIRED_NEEDS = (
    "pre-commit",
    "tests",
    "build",
    "docs",
    "security",
    "claude-yaml-audit",
    "dependency-docs",
)


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


def _materialize(script: str, results: dict[str, str]) -> str:
    """Replace GitHub Actions ``${{ needs.<job>.result }}`` expressions with concrete values."""
    out = script
    for job, result in results.items():
        out = out.replace("${{ needs." + job + ".result }}", result)
    leftover = re.findall(r"\$\{\{\s*needs\.([A-Za-z0-9_-]+)\.result\s*\}\}", out)
    if leftover:
        raise AssertionError(f"unsubstituted needs.*.result expressions: {leftover}")
    return out


class QualityGateStructuralTest(unittest.TestCase):
    """Pin QG needs membership + security soft-fail predicate text."""

    repo_root: Path
    workflow_path: Path
    raw: str
    doc: dict
    qg: dict
    script: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)
        cls.qg = cls.doc["jobs"][QG_JOB]
        steps = cls.qg.get("steps") or []
        step = next((s for s in steps if s.get("name") == QG_STEP_NAME), None)
        if step is None or "run" not in step:
            raise unittest.SkipTest(f"could not locate {QG_STEP_NAME!r} in {WORKFLOW_NAME}")
        cls.script = step["run"]

    def test_quality_gate_if_always(self) -> None:
        self.assertEqual(str(self.qg.get("if", "")), "always()")

    def test_required_needs_exact_membership(self) -> None:
        needs = self.qg.get("needs") or []
        if isinstance(needs, str):
            needs = [needs]
        self.assertEqual(
            list(needs),
            list(REQUIRED_NEEDS),
            "Quality Gate needs: must stay the hard-required set (order-sensitive for operator logs).",
        )

    def test_advisory_jobs_absent_from_needs(self) -> None:
        needs = self.qg.get("needs") or []
        if isinstance(needs, str):
            needs = [needs]
        present = ADVISORY_EXCLUDED.intersection(needs)
        self.assertEqual(
            present,
            set(),
            f"advisory/PR-only jobs must stay ABSENT from Quality Gate needs: (got {sorted(present)}). " "Folding them in fails every push:main because those jobs skip on push.",
        )

    def test_advisory_jobs_still_defined(self) -> None:
        """Exclusion is meaningful only while the advisory jobs exist."""
        jobs = self.doc.get("jobs") or {}
        for name in ADVISORY_EXCLUDED:
            with self.subTest(job=name):
                self.assertIn(name, jobs, f"{name} job missing from ci.yml — update ADVISORY_EXCLUDED if retired")

    def test_security_soft_fail_predicate_in_shell(self) -> None:
        # Soft-fail: only == failure trips the gate (skipped must remain OK).
        self.assertRegex(
            self.script,
            r'needs\.security\.result.*"failure"',
            "security must soft-fail on == failure (not != success)",
        )
        # Must NOT use the hard != success form for security.
        hard = re.search(
            r'needs\.security\.result.*"success"',
            self.script,
        )
        self.assertIsNone(
            hard,
            "security must not use != success — that turns intentional skips into gate failures",
        )

    def test_hard_jobs_use_success_predicate(self) -> None:
        for job in ("pre-commit", "tests", "build", "docs", "claude-yaml-audit", "dependency-docs"):
            with self.subTest(job=job):
                self.assertRegex(
                    self.script,
                    rf'needs\.{re.escape(job)}\.result.*"success"',
                    f"{job} must hard-require success",
                )


class QualityGateRehearsalTest(unittest.TestCase):
    """Run the extracted QG shell over a result matrix (security soft-fail + hard fails)."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        steps = doc["jobs"][QG_JOB].get("steps") or []
        step = next((s for s in steps if s.get("name") == QG_STEP_NAME), None)
        if step is None or "run" not in step:
            raise unittest.SkipTest(f"could not locate {QG_STEP_NAME!r}")
        cls.script = step["run"]

    def _all_success(self) -> dict[str, str]:
        return dict.fromkeys(REQUIRED_NEEDS, "success")

    def _run(self, results: dict[str, str]) -> subprocess.CompletedProcess:
        materialized = _materialize(self.script, results)
        with tempfile.TemporaryDirectory() as td:
            script_path = Path(td) / "qg.sh"
            script_path.write_text(materialized, encoding="utf-8")
            env = RedactedEnv(os.environ)
            return subprocess.run(  # nosec B603,B607 - workflow shell, fixed argv
                ["bash", str(script_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=15,
            )

    def test_all_success_passes(self) -> None:
        proc = self._run(self._all_success())
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Quality Gate PASSED", proc.stdout + proc.stderr)

    def test_security_skipped_still_passes(self) -> None:
        results = self._all_success()
        results["security"] = "skipped"
        proc = self._run(results)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Quality Gate PASSED", proc.stdout + proc.stderr)

    def test_security_failure_fails_gate(self) -> None:
        results = self._all_success()
        results["security"] = "failure"
        proc = self._run(results)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Security scan failed", proc.stdout + proc.stderr)

    def test_tests_failure_fails_gate(self) -> None:
        results = self._all_success()
        results["tests"] = "failure"
        proc = self._run(results)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Regression tests failed", proc.stdout + proc.stderr)

    def test_tests_skipped_fails_gate(self) -> None:
        """Hard jobs treat skipped as failure (!= success)."""
        results = self._all_success()
        results["tests"] = "skipped"
        proc = self._run(results)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
