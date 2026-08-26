"""Regression guard against the old ``prompts/templates/`` path in the live suite surface.

The custom-agent template library was renamed ``prompts/templates/`` ->
``prompts/agent_templates/``. The ``SKILL.md`` moved with it, but several live references
were left pointing at the now-nonexistent ``prompts/templates/`` -- most damagingly the
``prompt-validator`` subagent, which was told to read ``prompts/templates/RUBRIC.md`` and
``prompts/templates/manifest.yaml`` (neither of which exists), so it could not find its own
contract. This test asserts that no live suite file under ``.claude/agents/``,
``.claude/skills/``, or ``prompts/agent_templates/`` contains the stale literal
``prompts/templates/``, so the rename cannot silently regress.

``.claude/**`` is git-tracked via the PR-1 ``.gitignore`` negation and ``prompts/**`` is
git-tracked too, but both are excluded from every pre-commit hook except markdownlint, so
this unittest -- wired into ``ci.yml`` -- is the gate.

Note: the new path ``prompts/agent_templates/`` does NOT contain the substring
``prompts/templates/`` (``agent_`` separates the segments), so a plain substring scan is the
correct, false-positive-free check.

Location-agnostic: discovers the repo root by walking up for ``.github/workflows/``.
"""

from __future__ import annotations

import unittest
from pathlib import Path

# The stale path literal that must not survive anywhere in the live suite surface.
_STALE = "prompts/" + "templates/"

# Live suite directories (relative to repo root) that must be clean.
_SCAN_DIRS = (
    Path(".claude") / "agents",
    Path(".claude") / "skills",
    Path("prompts") / "agent_templates",
)


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


class AgentSuitePathDriftTest(unittest.TestCase):
    """No live suite file may reference the pre-rename ``prompts/templates/`` path."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.scan_dirs = [cls.repo_root / d for d in _SCAN_DIRS]
        cls.scanned_files = [p for d in cls.scan_dirs if d.is_dir() for p in sorted(d.rglob("*")) if p.is_file()]

    def test_scan_dirs_present(self):
        present = [d for d in self.scan_dirs if d.is_dir()]
        self.assertTrue(
            present,
            f"expected at least one live suite dir to exist under {self.repo_root}: {self.scan_dirs}",
        )

    def test_scanned_at_least_one_file(self):
        # Guards against a vacuous pass if the suite directories are empty/missing.
        self.assertTrue(self.scanned_files, "expected at least one live suite file to scan")

    def test_no_stale_template_path(self):
        offenders = []
        for path in self.scanned_files:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if _STALE in text:
                rel = path.relative_to(self.repo_root)
                for lineno, line in enumerate(text.splitlines(), start=1):
                    if _STALE in line:
                        offenders.append(f"{rel}:{lineno}: {line.strip()}")
        self.assertEqual(
            offenders,
            [],
            "live suite files must not reference the pre-rename path " f"'{_STALE}' (use 'prompts/agent_templates/'):\n" + "\n".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
