#!/usr/bin/env python3
"""YAML-extraction rehearsal for ci.yml sequence-safety label hatch → ``--advisory``.

Flood-remediation P2 SF5: owner-applied ``allow-symbol-loss`` / ``docs-rewrite`` PR
labels demote THAT screen's FAIL to WARN-only for the run (``--advisory``: exit 0
with findings still printed). Labels are read live via ``gh pr view`` so
apply-label + re-run takes effect with no push. ``merge_group`` has no PR object →
queued merges stay strict (no label downgrade). Exact-match ``grep -qx`` prevents
near-miss labels from silencing a FAIL.

The CLI ``--advisory`` arms are covered in ``tests/test_symbol_loss_check.py`` /
``tests/test_docs_additions_check.py``; this unittest pins the *workflow wiring*
that maps labels → argv and aggregates exit codes — the seam those module tests
cannot see.

Extracts the workflow's OWN ``Run sequence-safety screens`` shell and drives it
over a hermetic stub ``gh`` / ``git`` / ``python3`` (same idiom as
``tests/test_pr_budget_alarm.py`` / ``tests/test_ci_precommit_g4.py``).

Neither the workflow YAML nor this shell is otherwise lint-gated for the hatch,
so this unittest IS the gate.

Run: python3 -m unittest -v tests/test_ci_sequence_safety_hatch.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "ci.yml"
STEP_NAME = "Run sequence-safety screens (symbol + docs)"
JOB_NAME = "sequence-safety"


def _find_repo_root(start: Path) -> Path:
    cur = start
    for _ in range(8):
        if (cur / ".github" / "workflows").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise AssertionError(f"could not locate repo root with .github/workflows from {start}")


class SequenceSafetyHatchStructuralTest(unittest.TestCase):
    """Pin the hatch surface so a refactor cannot drop exact-match or widen merge_group."""

    workflow_path: Path
    raw: str
    doc: dict
    job: dict
    step: dict | None
    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)
        job = cls.doc.get("jobs", {}).get(JOB_NAME)
        if job is None:
            raise unittest.SkipTest(f"{WORKFLOW_NAME} has no {JOB_NAME} job")
        cls.job = job
        steps = job.get("steps", [])
        cls.step = next((s for s in steps if s.get("name") == STEP_NAME), None)
        if cls.step is None or "run" not in cls.step:
            raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step in {WORKFLOW_NAME}")
        cls.script = cls.step["run"]

    def test_job_is_pr_or_merge_group_only(self) -> None:
        self.assertEqual(
            self.job.get("if"),
            "github.event_name == 'pull_request' || github.event_name == 'merge_group'",
        )

    def test_permissions_include_pull_requests_read(self) -> None:
        perms = self.job.get("permissions") or {}
        self.assertEqual(perms.get("contents"), "read")
        self.assertEqual(perms.get("pull-requests"), "read")

    def test_script_uses_exact_grep_qx_and_advisory_tokens(self) -> None:
        script = self.script
        self.assertIn("grep -qx 'allow-symbol-loss'", script)
        self.assertIn("grep -qx 'docs-rewrite'", script)
        self.assertIn('sym_adv="--advisory"', script)
        self.assertIn('docs_adv="--advisory"', script)
        # Label hatch only on pull_request (merge_group stays strict).
        self.assertIn('"$EVENT_NAME" = "pull_request"', script)
        self.assertIn("gh pr view", script)
        # Exit aggregation: invocation error (≥2) vs finding (≥1).
        self.assertIn("-ge 2", script)
        self.assertIn("-ge 1", script)


class SequenceSafetyHatchRehearsalTest(unittest.TestCase):
    """Extract and run the real screen shell over the label / event / exit matrix."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        steps = doc.get("jobs", {}).get(JOB_NAME, {}).get("steps", [])
        step = next((s for s in steps if s.get("name") == STEP_NAME), None)
        if step is None or "run" not in step:
            raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step in {WORKFLOW_NAME}")
        cls.script = step["run"]

    def _run_screens(
        self,
        *,
        event_name: str,
        labels: list[str] | None = None,
        pr_number: str = "42",
        pr_base: str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        mg_base: str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        symbol_exit: int = 0,
        docs_exit: int = 0,
        empty_base: bool = False,
    ) -> tuple[int, str, list[str]]:
        """Return (exit_code, combined_output, python3 argv log lines)."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            script_path = td_path / "screens.sh"
            script_path.write_text(self.script, encoding="utf-8")
            py_log = td_path / "python.log"
            stub_bin = td_path / "bin"
            stub_bin.mkdir()

            # Stub python3: log full argv; honour --json by writing {}; return configured exit.
            # First non-json call for each module sets the human-screen exit; --json always 0
            # (workflow uses ``|| true`` on the json arm, but a clean stub keeps the log tidy).
            py = stub_bin / "python3"
            py.write_text(
                "#!/usr/bin/env bash\n" "set -euo pipefail\n" f'printf "%s\\n" "$*" >>"{py_log}"\n' 'args="$*"\n' 'if [[ "$args" == *"--json"* ]]; then\n' '  printf "%s\\n" "{}"\n' "  exit 0\n" "fi\n" 'if [[ "$args" == *"symbol_loss_check.py"* ]]; then\n' f"  exit {int(symbol_exit)}\n" "fi\n" 'if [[ "$args" == *"docs_additions_check.py"* ]]; then\n' f"  exit {int(docs_exit)}\n" "fi\n" 'echo "unexpected python3 argv: $*" >&2\n' "exit 99\n",
                encoding="utf-8",
            )
            py.chmod(0o755)

            # One label per line (mirrors ``gh pr view --jq '.labels[].name'``).
            labels_file = td_path / "labels.txt"
            labels_file.write_text("".join(f"{name}\n" for name in (labels or [])), encoding="utf-8")
            gh = stub_bin / "gh"
            gh.write_text(
                "#!/usr/bin/env bash\n" "set -euo pipefail\n" 'if [ "${1:-}" = "pr" ] && [ "${2:-}" = "view" ]; then\n' f'  cat "{labels_file}"\n' "  exit 0\n" "fi\n" 'echo "unexpected gh argv: $*" >&2\n' "exit 99\n",
                encoding="utf-8",
            )
            gh.chmod(0o755)

            git = stub_bin / "git"
            git.write_text(
                "#!/usr/bin/env bash\n" "set -euo pipefail\n" 'if [ "${1:-}" = "cat-file" ]; then exit 0; fi\n' 'if [ "${1:-}" = "fetch" ]; then exit 0; fi\n' 'echo "unexpected git argv: $*" >&2\n' "exit 99\n",
                encoding="utf-8",
            )
            git.chmod(0o755)

            env = RedactedEnv(os.environ)
            env["PATH"] = str(stub_bin) + os.pathsep + env.get("PATH", "")
            env["GH_TOKEN"] = "unused"  # nosec B105 - dummy token for the PATH-stubbed gh, never a real credential
            env["EVENT_NAME"] = event_name
            env["PR_NUMBER"] = pr_number
            env["PR_BASE_SHA"] = "" if empty_base and event_name == "pull_request" else pr_base
            env["MG_BASE_SHA"] = "" if empty_base and event_name == "merge_group" else mg_base

            proc = subprocess.run(  # nosec B603,B607 - workflow shell, fixed argv
                ["bash", str(script_path)],
                cwd=td_path,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=30,
            )
            combined = proc.stdout + proc.stderr
            log_lines = py_log.read_text(encoding="utf-8").splitlines() if py_log.is_file() else []
            return proc.returncode, combined, log_lines

    @staticmethod
    def _human_invocations(log: list[str]) -> list[str]:
        """Drop the ``--json`` artifact arms; keep the human-screen invocations."""
        return [line for line in log if "--json" not in line]

    def test_no_labels_runs_strict(self) -> None:
        rc, out, log = self._run_screens(event_name="pull_request", labels=[])
        self.assertEqual(rc, 0, msg=out)
        human = self._human_invocations(log)
        self.assertEqual(len(human), 2)
        self.assertTrue(human[0].endswith("symbol_loss_check.py --base aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --head HEAD"))
        self.assertTrue(human[1].endswith("docs_additions_check.py --base aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --head HEAD"))
        self.assertNotIn("--advisory", human[0])
        self.assertNotIn("--advisory", human[1])
        self.assertNotIn("ADVISORY", out)

    def test_allow_symbol_loss_label_advisories_symbol_only(self) -> None:
        rc, out, log = self._run_screens(event_name="pull_request", labels=["allow-symbol-loss"])
        self.assertEqual(rc, 0, msg=out)
        human = self._human_invocations(log)
        self.assertIn("--advisory", human[0])
        self.assertNotIn("--advisory", human[1])
        self.assertIn("label allow-symbol-loss -> symbol screen ADVISORY", out)

    def test_docs_rewrite_label_advisories_docs_only(self) -> None:
        rc, out, log = self._run_screens(event_name="pull_request", labels=["docs-rewrite"])
        self.assertEqual(rc, 0, msg=out)
        human = self._human_invocations(log)
        self.assertNotIn("--advisory", human[0])
        self.assertIn("--advisory", human[1])
        self.assertIn("label docs-rewrite -> docs screen ADVISORY", out)

    def test_both_labels_advisory_both_screens(self) -> None:
        rc, out, log = self._run_screens(
            event_name="pull_request",
            labels=["allow-symbol-loss", "docs-rewrite", "unrelated"],
        )
        self.assertEqual(rc, 0, msg=out)
        human = self._human_invocations(log)
        self.assertIn("--advisory", human[0])
        self.assertIn("--advisory", human[1])

    def test_near_miss_label_does_not_advisory(self) -> None:
        """``grep -qx`` must reject substrings / prefixes (e.g. allow-symbol-loss-please)."""
        rc, out, log = self._run_screens(
            event_name="pull_request",
            labels=["allow-symbol-loss-please", "docs-rewrite-now", "symbol-loss"],
        )
        self.assertEqual(rc, 0, msg=out)
        human = self._human_invocations(log)
        self.assertNotIn("--advisory", human[0])
        self.assertNotIn("--advisory", human[1])
        self.assertNotIn("ADVISORY", out)

    def test_merge_group_stays_strict_even_if_labels_present(self) -> None:
        """merge_group has no PR object — hatch block must not run (no gh, no --advisory)."""
        rc, out, log = self._run_screens(
            event_name="merge_group",
            labels=["allow-symbol-loss", "docs-rewrite"],
            # PR_NUMBER set but EVENT_NAME=merge_group must still skip the hatch.
        )
        self.assertEqual(rc, 0, msg=out)
        human = self._human_invocations(log)
        self.assertEqual(len(human), 2)
        # Uses MG base, never PR base.
        self.assertIn("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", human[0])
        self.assertNotIn("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", human[0])
        self.assertNotIn("--advisory", human[0])
        self.assertNotIn("--advisory", human[1])
        self.assertNotIn("ADVISORY", out)

    def test_finding_exit_1_fails_step(self) -> None:
        rc, out, _log = self._run_screens(
            event_name="pull_request",
            labels=[],
            symbol_exit=1,
            docs_exit=0,
        )
        self.assertEqual(rc, 1, msg=out)
        self.assertIn("per-PR compositional-loss finding", out)

    def test_invocation_error_exit_2(self) -> None:
        rc, out, _log = self._run_screens(
            event_name="pull_request",
            labels=[],
            symbol_exit=0,
            docs_exit=2,
        )
        self.assertEqual(rc, 2, msg=out)
        self.assertIn("invocation error", out)

    def test_empty_base_sha_exits_2(self) -> None:
        rc, out, log = self._run_screens(event_name="pull_request", empty_base=True)
        self.assertEqual(rc, 2, msg=out)
        self.assertIn("could not resolve a base sha", out)
        # Must not invoke the screens with an empty base.
        self.assertEqual(log, [])


if __name__ == "__main__":
    unittest.main()
