"""Regression tests for util/validate_claude_yaml_access.bash.

Covers the happy path plus the three failure modes the script detects:
  L2  dangerous trigger (pull_request_target / workflow_run)
  L3a missing if-guard on the claude: job
  L3b if-guard does not reference the '@claude' literal

Also covers the no-arg ``default_targets`` path: ``JUNIPER_ROOT`` sibling-repo
scan (canonical 8 repos) and the empty-scan warning exit-0 arm.

Additionally pins the live juniper-ml ``.github/workflows/claude.yml``
``on:`` event matrix, per-event ``if:`` gates, and exact job ``permissions``
(the L2/L3 bash validator does not cover those).

The test bodies invoke the bash script via subprocess and assert on its
exit code + stderr/stdout. The script lives at the canonical location
util/validate_claude_yaml_access.bash relative to this file.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

import yaml

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "util" / "validate_claude_yaml_access.bash"
CLAUDE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "claude.yml"

# Live claude.yml contract (public-repo ANTHROPIC_API_KEY surface).
_EXPECTED_ON_EVENTS = frozenset(
    {
        "issue_comment",
        "pull_request_review_comment",
        "issues",
        "pull_request_review",
    }
)
_EXPECTED_PERMISSIONS = {
    "contents": "write",
    "pull-requests": "write",
    "issues": "write",
    "id-token": "write",
    "actions": "read",
}


GOOD_YAML = dedent("""\
    name: Claude Code

    on:
      issue_comment:
        types: [created]
      pull_request_review_comment:
        types: [created]
      issues:
        types: [opened, assigned]
      pull_request_review:
        types: [submitted]

    jobs:
      claude:
        if: |
          (github.event_name == 'issue_comment'
            && contains(github.event.comment.body, '@claude'))
        runs-on: ubuntu-latest
        steps:
          - run: echo hi
    """)

BAD_TRIGGER_YAML = dedent("""\
    name: Claude Code
    on:
      pull_request_target:
        types: [opened]
    jobs:
      claude:
        if: contains(github.event.pull_request.body, '@claude')
        runs-on: ubuntu-latest
        steps:
          - run: echo hi
    """)

NO_IF_YAML = dedent("""\
    name: Claude Code
    on:
      issue_comment:
        types: [created]
    jobs:
      claude:
        runs-on: ubuntu-latest
        steps:
          - run: echo hi
    """)

WRONG_TOKEN_YAML = dedent("""\
    name: Claude Code
    on:
      issue_comment:
        types: [created]
    jobs:
      claude:
        if: contains(github.event.comment.body, 'claude')
        runs-on: ubuntu-latest
        steps:
          - run: echo hi
    """)


def _run_validator(target_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), str(target_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def _run_validator_no_args(*, juniper_root: Path | None) -> subprocess.CompletedProcess:
    """Drive the no-arg default_targets path with an optional JUNIPER_ROOT override."""
    env = RedactedEnv(os.environ)
    if juniper_root is None:
        env.pop("JUNIPER_ROOT", None)
    else:
        env["JUNIPER_ROOT"] = str(juniper_root)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=60,
    )


def _write_sibling_claude(juniper_root: Path, repo_name: str, body: str) -> Path:
    wf = juniper_root / repo_name / ".github" / "workflows"
    wf.mkdir(parents=True)
    target = wf / "claude.yml"
    target.write_text(body)
    return target


class ScriptShapeTests(unittest.TestCase):
    def test_script_exists_and_is_executable(self) -> None:
        self.assertTrue(SCRIPT_PATH.is_file(), f"missing: {SCRIPT_PATH}")
        # x-bit on the file (we explicitly chmod +x at install time).
        # subprocess invocation goes through `bash` regardless, so this
        # is hygiene only.
        self.assertTrue(
            SCRIPT_PATH.stat().st_mode & 0o111,
            f"not executable: {SCRIPT_PATH}",
        )


class ValidatorBehaviorTests(unittest.TestCase):
    def test_happy_path_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "claude.yml"
            f.write_text(GOOD_YAML)
            result = _run_validator(f)
            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn("OK", result.stdout)
            self.assertIn("passed L2/L3 validation", result.stdout)

    def test_dangerous_trigger_fails_l2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "claude.yml"
            f.write_text(BAD_TRIGGER_YAML)
            result = _run_validator(f)
            self.assertEqual(result.returncode, 1)
            self.assertIn("L2 dangerous trigger present", result.stdout)
            self.assertIn("FAIL", result.stdout)

    def test_workflow_run_trigger_fails_l2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "claude.yml"
            # Same shape as BAD_TRIGGER_YAML but using workflow_run instead.
            f.write_text(BAD_TRIGGER_YAML.replace("pull_request_target", "workflow_run"))
            result = _run_validator(f)
            self.assertEqual(result.returncode, 1)
            self.assertIn("L2 dangerous trigger present", result.stdout)

    def test_missing_if_guard_fails_l3a(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "claude.yml"
            f.write_text(NO_IF_YAML)
            result = _run_validator(f)
            self.assertEqual(result.returncode, 1)
            self.assertIn("L3a claude job has no if-guard", result.stdout)

    def test_wrong_token_fails_l3b(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "claude.yml"
            f.write_text(WRONG_TOKEN_YAML)
            result = _run_validator(f)
            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "L3b if-guard does not reference '@claude' literal",
                result.stdout,
            )

    def test_directory_argument_resolves_canonical_path(self) -> None:
        # Mirror real layout: <repo>/.github/workflows/claude.yml
        with tempfile.TemporaryDirectory() as tmp:
            wf_dir = Path(tmp) / ".github" / "workflows"
            wf_dir.mkdir(parents=True)
            (wf_dir / "claude.yml").write_text(GOOD_YAML)
            result = _run_validator(Path(tmp))
            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn("OK", result.stdout)

    def test_nonexistent_argument_exits_two(self) -> None:
        # /no/such/path is not a file or dir; script should exit 2 (usage).
        bogus = Path("/no/such/path/that/exists")
        result = _run_validator(bogus)
        self.assertEqual(result.returncode, 2)
        self.assertIn("input does not exist", result.stderr)

    def test_directory_without_claude_yml_skips_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty_repo"
            empty.mkdir()
            result = _run_validator(empty)
            self.assertEqual(result.returncode, 0, msg=f"stdout={result.stdout!r} stderr={result.stderr!r}")
            self.assertIn("no claude.yml under", result.stderr)
            self.assertIn("nothing to do", result.stdout)


class DefaultTargetsTests(unittest.TestCase):
    """No-arg default_targets: JUNIPER_ROOT sibling scan + empty-scan warning."""

    def test_juniper_root_scans_canonical_siblings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Canonical names from DEFAULT_REPOS; a non-canonical dir must be ignored.
            _write_sibling_claude(root, "juniper-ml", GOOD_YAML)
            _write_sibling_claude(root, "juniper-canopy", GOOD_YAML)
            _write_sibling_claude(root, "not-a-juniper-repo", BAD_TRIGGER_YAML)
            result = _run_validator_no_args(juniper_root=root)
            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn("OK", result.stdout)
            self.assertIn("passed L2/L3 validation", result.stdout)
            # Must not have audited the non-canonical sibling (would FAIL L2).
            self.assertNotIn("FAIL", result.stdout)
            self.assertNotIn("not-a-juniper-repo", result.stdout)

    def test_juniper_root_aggregates_sibling_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_sibling_claude(root, "juniper-ml", GOOD_YAML)
            _write_sibling_claude(root, "juniper-data", BAD_TRIGGER_YAML)
            result = _run_validator_no_args(juniper_root=root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("FAIL", result.stdout)
            self.assertIn("L2 dangerous trigger present", result.stdout)
            self.assertIn("1 claude.yml file(s) failed validation", result.stdout)

    def test_juniper_root_with_no_claude_yml_warns_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Empty sibling dirs — JUNIPER_ROOT is set but nothing to audit.
            (root / "juniper-ml").mkdir()
            (root / "juniper-canopy").mkdir()
            result = _run_validator_no_args(juniper_root=root)
            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn("contains no claude.yml under the canonical Juniper repos", result.stderr)
            self.assertIn("nothing to do", result.stdout)


class LiveClaudeWorkflowContractTests(unittest.TestCase):
    """Pin juniper-ml's live claude.yml event matrix + permissions (secret surface).

    The bash validator only checks L2 dangerous triggers + L3a/L3b ``@claude``
    presence. It does not notice a dropped ``on:`` event, an ungated event in
    ``if:``, or a permissions widen/narrow — all of which change who can spend
    ``ANTHROPIC_API_KEY`` on a public repo.
    """

    raw: str
    doc: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = CLAUDE_WORKFLOW.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)

    def test_on_events_match_canonical_matrix(self) -> None:
        # PyYAML may parse the ``on:`` key as boolean True.
        on_block = self.doc.get("on") or self.doc.get(True)
        self.assertIsInstance(on_block, dict, msg="claude.yml must declare an on: mapping")
        self.assertEqual(
            frozenset(on_block.keys()),
            _EXPECTED_ON_EVENTS,
            msg=(f"on: event drift: missing={sorted(_EXPECTED_ON_EVENTS - frozenset(on_block))} " f"extra={sorted(frozenset(on_block) - _EXPECTED_ON_EVENTS)}"),
        )

    def test_job_if_gates_every_on_event(self) -> None:
        """Every on: event must appear in the claude job if: (drive-by hatch)."""
        job = self.doc["jobs"]["claude"]
        if_expr = job.get("if")
        self.assertIsInstance(if_expr, str)
        self.assertIn("@claude", if_expr)
        for event in _EXPECTED_ON_EVENTS:
            self.assertIn(
                f"github.event_name == '{event}'",
                if_expr,
                msg=f"claude job if: does not gate on: event {event!r}",
            )

    def test_job_permissions_exact(self) -> None:
        job = self.doc["jobs"]["claude"]
        perms = job.get("permissions")
        self.assertEqual(
            perms,
            _EXPECTED_PERMISSIONS,
            msg=f"claude job permissions drift: got={perms!r}",
        )


if __name__ == "__main__":
    unittest.main()
