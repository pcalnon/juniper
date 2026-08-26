"""Lint test: ``AGENTS.md`` Repository-Structure tree completeness (gap G-3).

Catches the *indented-tree* drift that the grep-based path-drift guard
(``test_agent_suite_path_drift.py``) cannot: a real top-level directory that is
absent from the fenced Repository-Structure tree in ``AGENTS.md``. This is the
exact class that let ``prompts/agent_templates/`` show as a stale ``templates/``
and left ``conf/`` / ``papers/`` and the six published sub-package directories
out of the tree entirely.

Contract: every tracked, non-hidden top-level directory (the ``ls -d */``
surface, sourced from ``git ls-tree`` so build artifacts never cause a false
failure) must appear as a node in the tree. Hidden dirs (``.github`` etc.) and
files are out of scope -- matching ``ls -d */``.

Portable / self-locating like the other AGENTS.md lints
(``test_agents_md_header_schema.py``): walks up for an ``AGENTS.md`` sibling to
``.github/``, so it drops into any Juniper repo's ``tests/`` unchanged.
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path
from typing import ClassVar


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "AGENTS.md").is_file() and (parent / ".github").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (AGENTS.md + .github/) from {here}")


# A top-level tree node: connector at column 0, then the entry name. Directory
# nodes are written with a trailing slash (``├── conf/``); files are not.
_TOP_NODE_RE = re.compile(r"^[├└]──\s+(?P<name>\S+)")
# The fenced block holding the tree (the one containing the ``util/`` leaf).
_FENCE_RE = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.DOTALL)


def tree_block(agents_md_text: str) -> str:
    """Return the fenced Repository-Structure tree block (raises if absent)."""
    for body in _FENCE_RE.findall(agents_md_text):
        if "└── util/" in body or "├── AGENTS.md" in body:
            return body
    raise AssertionError("AGENTS.md Repository-Structure tree block not found")


def top_level_dir_nodes(tree_text: str) -> set[str]:
    """Set of top-level *directory* node names (trailing slash) in the tree."""
    nodes: set[str] = set()
    for line in tree_text.splitlines():
        m = _TOP_NODE_RE.match(line)
        if m and m.group("name").endswith("/"):
            nodes.add(m.group("name").rstrip("/"))
    return nodes


def missing_dirs(dirs: list[str], tree_text: str) -> list[str]:
    """Subset of ``dirs`` that does not appear as a top-level node in the tree."""
    nodes = top_level_dir_nodes(tree_text)
    return [d for d in dirs if d not in nodes]


def _tracked_top_level_dirs(repo_root: Path) -> "list[str] | None":
    """Tracked, non-hidden top-level directories via ``git ls-tree`` (None if git
    is unavailable -- the caller skips rather than fails)."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "ls-tree", "-d", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return sorted(name for name in out.splitlines() if name and not name.startswith("."))


class AgentsMdTreeDriftTest(unittest.TestCase):
    tree: ClassVar[str]
    repo: ClassVar[Path]

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = _repo_root()
        cls.tree = tree_block((cls.repo / "AGENTS.md").read_text(encoding="utf-8"))

    def test_every_tracked_top_level_dir_is_in_the_tree(self) -> None:
        dirs = _tracked_top_level_dirs(self.repo)
        if dirs is None:
            self.skipTest("git unavailable")
        absent = missing_dirs(dirs, self.tree)
        self.assertEqual(
            absent,
            [],
            f"AGENTS.md Repository-Structure tree is missing top-level dir(s): {absent}. " "Add each as a `├── <name>/` node (this is the G-3 drift guard).",
        )

    def test_known_packaged_subdirs_present(self) -> None:
        # The six published sub-package dirs were the headline G-3 omission.
        for pkg in ("juniper-ci-tools", "juniper-doc-tools", "juniper-observability", "juniper-service-core"):
            self.assertIn(pkg, top_level_dir_nodes(self.tree), f"{pkg}/ missing from the tree")

    def test_checker_flags_a_missing_dir(self) -> None:
        # Synthetic negative: a dir absent from the tree must be reported, while a
        # present one (conf/, added by G-3) must not -- proving the guard bites.
        self.assertEqual(missing_dirs(["conf", "zzz_not_a_real_dir"], self.tree), ["zzz_not_a_real_dir"])

    def test_prompts_uses_agent_templates_not_stale_templates(self) -> None:
        # G-3 rename: the tree must cite the real prompts/agent_templates/ dir.
        self.assertIn("agent_templates/", self.tree)


if __name__ == "__main__":
    unittest.main()
