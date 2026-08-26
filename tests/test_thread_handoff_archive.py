"""Drift tests for archived thread-handoff prompt filenames and references.

The handoff archive is documentation, but stale or non-canonical names make
future handoff prompts hard to locate and easy to reference incorrectly.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_HANDOFF_DIR = _REPO_ROOT / "prompts" / "thread-handoff_automated-prompts"
_CANONICAL_NAME = re.compile(r"^HANDOFF_\d{4}-\d{2}-\d{2}_[A-Za-z0-9][A-Za-z0-9._-]*\.md$")
_CANONICAL_REFERENCE = re.compile(r"\b(HANDOFF_\d{4}-\d{2}-\d{2}_[A-Za-z0-9][A-Za-z0-9._-]*\.md)\b")


class ThreadHandoffArchiveTest(unittest.TestCase):
    def test_archived_thread_handoff_filenames_are_canonical(self):
        names = sorted(path.name for path in _HANDOFF_DIR.glob("*.md"))
        self.assertGreater(names, [], "thread-handoff archive should contain prompt files")

        bad_names = []
        for name in names:
            try:
                name.encode("ascii")
            except UnicodeEncodeError:
                bad_names.append(name)
                continue
            if not _CANONICAL_NAME.fullmatch(name):
                bad_names.append(name)

        self.assertEqual(
            bad_names,
            [],
            "Archive filenames must follow HANDOFF_YYYY-MM-DD_subject.md with ASCII subject text",
        )

    def test_top_level_note_references_to_thread_handoffs_resolve(self):
        references = {}
        for path in sorted((_REPO_ROOT / "notes").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for match in _CANONICAL_REFERENCE.finditer(text):
                references.setdefault(match.group(1), []).append(path.relative_to(_REPO_ROOT).as_posix())

        self.assertTrue(references, "expected at least one top-level note to reference an archived handoff")

        missing = {name: sources for name, sources in sorted(references.items()) if not (_HANDOFF_DIR / name).is_file()}

        self.assertEqual(missing, {}, "top-level note handoff references must resolve to archived prompt files")


if __name__ == "__main__":
    unittest.main()
