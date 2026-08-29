"""Static lint for the service-smoke Skill (custom-agent suite E-1 Stage 1/2).

The Skill (``.claude/skills/service-smoke/SKILL.md``) is a runtime diagnostician
(HTTP + opt-in UI smoke): it boots a Juniper service in its conda env, probes
``/v1/health``, tails the boot log, reports a live traceback as ``file:line`` (the
"green tests / dead app" catch), and -- when invoked with ``--ui`` (Stage 2) --
drives the live dashboard via the ``playwright`` MCP and reports client-side
failures. Its live behaviour needs conda + the real service (and the UI smoke a real
browser MCP), so it cannot run in ubuntu CI -- correctness of the live path is
covered by a documented manual smoke-verify, not by CI.

This unittest is the *structural* gate for the Skill surface:
  * frontmatter shape -- the suite's ``opus`` + ``max`` defaults, user-only
    invocation, and the base tool set ``{Read, Grep, Glob, Bash}``;
  * the **Stage-2 boundary** -- the frontmatter MUST now declare a browser MCP
    (``mcp__playwright`` / ``chrome-devtools``) for the opt-in ``--ui`` smoke (the
    inverse of Stage 1's "no browser MCP"); ``Agent`` is still forbidden (the Skill
    never delegates live-process management to a subagent);
  * wiring to the real teardown utilities (each referenced path exists on disk);
  * an explicit teardown step -- close the browser, then the spike's two gotchas
    (SIGTERM->SIGKILL escalation, poll-to-down, finally-style reap);
  * the opt-in UI smoke documented (``--ui``, the ``/dashboard`` target, console-error
    collection, the no-commit guard for the tracked ``.playwright-mcp/`` dir);
  * named terminal states (incl. ``UI_UNHEALTHY_REPORTED``) and bounded behaviour.

``.claude/**`` is git-tracked via the PR-1 ``.gitignore`` negation but excluded from
every pre-commit hook except markdownlint, so this unittest -- wired into ``ci.yml``
-- is the gate.

Design-of-record: ``notes/JUNIPER_2026-06-27_JUNIPER-ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS-PLAN.md`` (S6.9).
Spike record: ``notes/JUNIPER_2026-06-29_JUNIPER-ML_E1-SERVICE-SMOKE-STAGE0-SPIKE.md``.
Location-agnostic: discovers the repo root by walking up for ``.github/workflows/``.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

# The base tool grant the Skill must pre-approve.
_REQUIRED_TOOLS = {"Read", "Grep", "Glob", "Bash"}
# `Agent` is still forbidden: the Skill manages its own live processes and never
# delegates to a subagent -- that boundary survives Stage 2. (A browser MCP, by
# contrast, is now REQUIRED for the opt-in --ui smoke; see _is_browser_mcp.)
_FORBIDDEN_TOOLS = {"Agent"}

# Teardown utilities the Skill must wire to by literal path -- each must appear in
# the body AND exist on disk (no dangling wiring). Reused, never reinvented.
_REFERENCED_PATHS = [
    "util/reap_pytest_orphans.bash",
    "util/kill_all_pythons.bash",
]
_TERMINAL_STATES = (
    "HEALTHY",
    "UNHEALTHY_REPORTED",
    "UI_UNHEALTHY_REPORTED",
    "BOOT_FAILED",
    "TEARDOWN_ESCALATED",
)


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


def _split_frontmatter(text: str):
    """Return (front_dict, front_raw, body). front_raw is the YAML text between the
    first two ``---`` fences so the Stage-1 boundary can be checked on the frontmatter
    alone (the body legitimately names the Stage-2 browser MCPs)."""
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
    """True if ``tool`` names a browser MCP server (the Stage-2 UI-smoke driver).

    Accepts a server-wildcard grant (``mcp__playwright`` / ``mcp__chrome-devtools``)
    or a specific tool (``mcp__playwright__browser_navigate``), plus the bare server
    names for tolerance."""
    t = str(tool).strip().lower()
    return t.startswith("mcp__playwright") or t.startswith("mcp__chrome-devtools") or t in {"playwright", "chrome-devtools"}


class ServiceSmokeSkillLintTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.skill_path = cls.repo_root / ".claude" / "skills" / "service-smoke" / "SKILL.md"
        cls.text = cls.skill_path.read_text(encoding="utf-8") if cls.skill_path.exists() else None
        cls.front, cls.front_raw, cls.body = _split_frontmatter(cls.text) if cls.text else (None, "", "")

    def setUp(self):
        if self.text is None:
            self.skipTest(f"service-smoke Skill absent at {self.skill_path}")

    def test_skill_file_exists(self):
        self.assertTrue(self.skill_path.exists(), f"missing Skill at {self.skill_path}")

    def test_frontmatter_parses(self):
        self.assertIsNotNone(self.front, "SKILL.md has no parseable YAML frontmatter")

    def test_name_matches_filename_stem(self):
        self.assertEqual(self.front.get("name"), "service-smoke", "name must equal the Skill dir/file stem")

    def test_description_substantive(self):
        desc = self.front.get("description", "")
        self.assertIsInstance(desc, str)
        self.assertGreaterEqual(len(desc), 60, "description should describe what it boots/probes and the opt-in UI smoke")

    def test_argument_hint_present(self):
        self.assertTrue(str(self.front.get("argument-hint", "")).strip(), "argument-hint should be set")

    def test_allowed_tools_include_required(self):
        tools = _as_tool_set(self.front.get("allowed-tools"))
        missing = sorted(_REQUIRED_TOOLS - tools)
        self.assertEqual(missing, [], f"allowed-tools missing the base tool set {missing}")

    def test_stage2_boundary_browser_declared_no_agent(self):
        """Stage 2 adds the opt-in browser UI smoke, so the frontmatter MUST declare a
        browser MCP (playwright / chrome-devtools) -- the inverse of Stage 1's "no
        browser MCP" boundary. `Agent` stays forbidden: the Skill never delegates its
        live-process management to a subagent."""
        tools = _as_tool_set(self.front.get("allowed-tools"))
        self.assertTrue(
            any(_is_browser_mcp(t) for t in tools),
            f"Stage-2 Skill must declare a browser MCP (e.g. mcp__playwright) in allowed-tools; got {sorted(tools)}",
        )
        granted_forbidden = sorted(t for t in tools if t in _FORBIDDEN_TOOLS)
        self.assertEqual(granted_forbidden, [], f"Skill must not grant {granted_forbidden} (no subagent delegation, even in Stage 2)")

    def test_model_pinned_to_opus(self):
        base = str(self.front.get("model", "")).split(":")[0].strip().lower()
        self.assertTrue(base == "opus" or base.startswith("claude-opus"), f"suite default model is Opus; got {self.front.get('model')!r}")

    def test_effort_is_max(self):
        self.assertEqual(str(self.front.get("effort", "")).strip().lower(), "max", "suite default effort is 'max'")

    def test_user_only_invocation(self):
        self.assertIs(self.front.get("disable-model-invocation"), True, "Skill is user-only (it manages live processes)")

    def test_referenced_paths_exist(self):
        for rel in _REFERENCED_PATHS:
            self.assertIn(rel, self.body, f"SKILL.md should reference {rel}")
            self.assertTrue((self.repo_root / rel).exists(), f"SKILL.md references {rel} but it does not exist on disk")

    def test_probes_health_endpoint(self):
        self.assertIn("/v1/health", self.body, "Skill must probe the /v1/health endpoint")

    def test_explicit_teardown_step(self):
        """Teardown is mandatory and now also closes the UI-smoke browser: close the
        browser, then a SIGTERM->SIGKILL escalation, poll-to-down (not
        assert-down-immediately), and a finally-style reap."""
        self.assertIn("SIGTERM", self.body, "teardown must escalate from SIGTERM")
        self.assertIn("SIGKILL", self.body, "teardown must escalate to SIGKILL after the timeout")
        self.assertRegex(self.body, r"finally", "teardown must run in a finally-style path")
        self.assertRegex(self.body, r"poll-to-down|poll for connection", "teardown must poll-to-down, not assert down immediately")
        self.assertRegex(self.body, r"browser_close|close the browser", "teardown must close the UI-smoke browser, not orphan it")

    def test_bounded_behaviour_documented(self):
        low = self.body.lower()
        self.assertIn("bounded", low, "Skill must document bounded waits")
        self.assertIn("timeout", low, "Skill must document a bounded timeout (no unbounded wait-until-ready)")

    def test_terminal_states_documented(self):
        for state in _TERMINAL_STATES:
            self.assertIn(state, self.body, f"Skill must document terminal state {state}")

    def test_ui_smoke_documented(self):
        """The Stage-2 surface must document the opt-in UI smoke: the --ui flag, the
        dashboard navigation target, console-error collection, and the no-commit guard
        for the tracked .playwright-mcp/ artifact dir."""
        self.assertIn("--ui", self.body, "Skill must document the opt-in --ui flag")
        self.assertIn("/dashboard", self.body, "Skill must navigate the dashboard mount (/dashboard), not assume /")
        self.assertIn("console", self.body.lower(), "UI smoke must collect console errors")
        self.assertIn(".playwright-mcp", self.body, "Skill must guard against committing .playwright-mcp/ artifacts")


if __name__ == "__main__":
    unittest.main()
