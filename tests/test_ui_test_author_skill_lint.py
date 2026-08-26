"""Static lint for the ui-test-author Skill (custom-agent suite E-6).

The Skill (``.claude/skills/ui-test-author/SKILL.md``) is the click-through test
author: it boots the target app, drives its live dashboard via the ``playwright``
MCP to observe a real control + outcome, then writes a ``@pytest.mark.ui``
pytest-playwright test -- modeled on canopy's ``src/tests/ui/`` harness -- into the
**target** repo's ``src/tests/ui/`` (uncommitted) for human review. It never
commits/PRs/merges the test, and the generated test runs in the *target* repo's CI,
not juniper-ml's. Its live behaviour needs conda + the app + a browser MCP, so it
cannot run in ubuntu CI -- correctness of the live path is a documented manual
smoke-verify.

This unittest is the *structural* gate for the Skill surface:
  * frontmatter shape -- the suite's ``opus`` + ``max`` defaults, user-only
    invocation, and the tool set ``{Read, Grep, Glob, Bash, Write}`` PLUS a declared
    browser MCP (``mcp__playwright``) for the live drive; ``Agent`` forbidden;
  * wiring to the real teardown utilities (each referenced path exists on disk);
  * an explicit teardown step (close the browser, then SIGTERM->SIGKILL poll-to-down,
    finally-style reap) -- inherited from the ``service-smoke`` discipline;
  * modelling on the real harness (``src/tests/ui/``, the ``dashboard_page`` fixture,
    ``@pytest.mark.ui``, the ``/dashboard`` mount);
  * the ``dbc.Input(type=number)`` wall documented (assert via a button / ``/api/state``
    read-back, never a numeric DOM fill);
  * the reviewed-never-auto-merged contract (write uncommitted; never commit/PR/merge);
  * named terminal states and bounded behaviour.

``.claude/**`` is git-tracked via the PR-1 ``.gitignore`` negation but excluded from
every pre-commit hook except markdownlint, so this unittest -- wired into ``ci.yml``
-- is the gate.

Design-of-record: ``notes/JUNIPER_2026-06-27_JUNIPER-ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS-PLAN.md`` (S6.10).
Location-agnostic: discovers the repo root by walking up for ``.github/workflows/``.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

# The base tool grant the Skill must pre-approve. Write is needed to emit the drafted
# test into the target repo's src/tests/ui/; the browser MCP (below) drives the app.
_REQUIRED_TOOLS = {"Read", "Grep", "Glob", "Bash", "Write"}
# `Agent` is forbidden: this Skill does its own observing + authoring, never delegates.
_FORBIDDEN_TOOLS = {"Agent"}

# Teardown utilities the Skill must wire to by literal path -- each must appear in the
# body AND exist on disk in juniper-ml (no dangling wiring). Reused from service-smoke.
_REFERENCED_PATHS = [
    "util/reap_pytest_orphans.bash",
    "util/kill_all_pythons.bash",
]
_TERMINAL_STATES = ("TEST_DRAFTED", "NO_OBSERVABLE_OUTCOME", "BOOT_FAILED", "TEARDOWN_ESCALATED")


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


def _split_frontmatter(text: str):
    if not text.startswith("---"):
        return None, "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "", text
    front = yaml.safe_load(parts[1])
    return (front if isinstance(front, dict) else None), parts[1], parts[2]


def _as_tool_set(value):
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(v).strip() for v in value if str(v).strip()}
    return {tok.strip() for tok in re.split(r"[,\s]+", str(value)) if tok.strip()}


def _is_browser_mcp(tool):
    """True if ``tool`` names a browser MCP server (the live-UI-drive driver)."""
    t = str(tool).strip().lower()
    return t.startswith("mcp__playwright") or t.startswith("mcp__chrome-devtools") or t in {"playwright", "chrome-devtools"}


class UiTestAuthorSkillLintTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.skill_path = cls.repo_root / ".claude" / "skills" / "ui-test-author" / "SKILL.md"
        cls.text = cls.skill_path.read_text(encoding="utf-8") if cls.skill_path.exists() else None
        cls.front, cls.front_raw, cls.body = _split_frontmatter(cls.text) if cls.text else (None, "", "")

    def setUp(self):
        if self.text is None:
            self.skipTest(f"ui-test-author Skill absent at {self.skill_path}")

    def test_skill_file_exists(self):
        self.assertTrue(self.skill_path.exists(), f"missing Skill at {self.skill_path}")

    def test_frontmatter_parses(self):
        self.assertIsNotNone(self.front, "SKILL.md has no parseable YAML frontmatter")

    def test_name_matches_filename_stem(self):
        self.assertEqual(self.front.get("name"), "ui-test-author", "name must equal the Skill dir/file stem")

    def test_description_substantive(self):
        desc = self.front.get("description", "")
        self.assertIsInstance(desc, str)
        self.assertGreaterEqual(len(desc), 60, "description should describe what it authors and that it is reviewed/never-merged")

    def test_argument_hint_present(self):
        self.assertTrue(str(self.front.get("argument-hint", "")).strip(), "argument-hint should be set")

    def test_allowed_tools_include_required(self):
        tools = _as_tool_set(self.front.get("allowed-tools"))
        missing = sorted(_REQUIRED_TOOLS - tools)
        self.assertEqual(missing, [], f"allowed-tools missing {missing} (Write emits the test; Read/Grep/Glob/Bash boot+model)")

    def test_browser_mcp_declared_no_agent(self):
        """E-6 drives the live app, so the frontmatter MUST declare a browser MCP
        (playwright / chrome-devtools). `Agent` is forbidden: the Skill authors the
        test itself and never delegates."""
        tools = _as_tool_set(self.front.get("allowed-tools"))
        self.assertTrue(
            any(_is_browser_mcp(t) for t in tools),
            f"ui-test-author must declare a browser MCP (e.g. mcp__playwright) in allowed-tools; got {sorted(tools)}",
        )
        granted_forbidden = sorted(t for t in tools if t in _FORBIDDEN_TOOLS)
        self.assertEqual(granted_forbidden, [], f"Skill must not grant {granted_forbidden} (no subagent delegation)")

    def test_model_pinned_to_opus(self):
        base = str(self.front.get("model", "")).split(":")[0].strip().lower()
        self.assertTrue(base == "opus" or base.startswith("claude-opus"), f"suite default model is Opus; got {self.front.get('model')!r}")

    def test_effort_is_max(self):
        self.assertEqual(str(self.front.get("effort", "")).strip().lower(), "max", "suite default effort is 'max'")

    def test_user_only_invocation(self):
        self.assertIs(self.front.get("disable-model-invocation"), True, "Skill is user-only (it boots live processes)")

    def test_referenced_paths_exist(self):
        for rel in _REFERENCED_PATHS:
            self.assertIn(rel, self.body, f"SKILL.md should reference {rel}")
            self.assertTrue((self.repo_root / rel).exists(), f"SKILL.md references {rel} but it does not exist on disk")

    def test_models_on_real_harness(self):
        """The Skill must model on canopy's real UI harness, not invent one."""
        self.assertIn("src/tests/ui/", self.body, "Skill must model on the src/tests/ui/ harness")
        self.assertIn("dashboard_page", self.body, "Skill must reuse the dashboard_page fixture")
        self.assertIn("@pytest.mark.ui", self.body, "Skill must reuse the @pytest.mark.ui marker")
        self.assertIn("/dashboard", self.body, "Skill must navigate the /dashboard mount")

    def test_dbc_input_wall_documented(self):
        """The Playwright dbc.Input(type=number) wall must be encoded so the Skill
        never emits a numeric-fill test that reads null; assert via button / /api/state."""
        self.assertIn("dbc.Input", self.body, "Skill must document the dbc.Input(type=number) wall")
        self.assertIn("/api/state", self.body, "Skill must offer the /api/state read-back as the workaround")

    def test_reviewed_never_auto_merged(self):
        low = self.body.lower()
        self.assertIn("never", low, "Skill must state the never-auto-merged contract")
        self.assertRegex(self.body, r"commit|merge", "Skill must say it never commits/merges the test")
        self.assertRegex(low, r"review|uncommitted", "Skill must write the test uncommitted for review")

    def test_explicit_teardown_step(self):
        self.assertIn("SIGTERM", self.body, "teardown must escalate from SIGTERM")
        self.assertIn("SIGKILL", self.body, "teardown must escalate to SIGKILL after the timeout")
        self.assertRegex(self.body, r"finally", "teardown must run in a finally-style path")
        self.assertRegex(self.body, r"poll-to-down|poll for connection", "teardown must poll-to-down, not assert down immediately")
        self.assertRegex(self.body, r"browser_close|close the browser", "teardown must close the live-drive browser")

    def test_bounded_behaviour_documented(self):
        low = self.body.lower()
        self.assertIn("bounded", low, "Skill must document bounded waits")
        self.assertIn("timeout", low, "Skill must document a bounded timeout")

    def test_terminal_states_documented(self):
        for state in _TERMINAL_STATES:
            self.assertIn(state, self.body, f"Skill must document terminal state {state}")


if __name__ == "__main__":
    unittest.main()
