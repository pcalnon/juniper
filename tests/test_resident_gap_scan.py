#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

Pin ``util/ad-hoc/2026-08-28_resident_gap_scan.py`` -- the FINDER the
resident-gap triage imports.

Failure class this pins
-----------------------
A census that can certify a multiplied or inflated result as a real inventory.

The 2026-08-31 run of this script reported 23,120 files / 15,285 candidates
because the default ``*/**/*.py`` glob walked ~60 copies under
``.claude/worktrees``. ``#1697`` pins the ``worktrees/`` name.
``.claude`` is a second skip -- session copies that are *not* named
worktrees still multiply the census if that entry drops. Scoped to real
source the same repo is 419 / 294. That is not a large result, it is one
result multiplied -- the sort of number a reader trusts because it is big.

A first IDENT version accepted any backtick span up to 60 chars. Comments
quote whole clauses in backticks, so ``names:`` filled with fragments
like ``), and the verbatim rejection detail (``. Those are unmatchable
against AGENTS.md by construction, which inflates every candidate and
buries the real ones.

``#1663`` / ``tests/test_hazard_triage.py`` pins the AGENTS.md finder.
``#1697`` / ``tests/test_resident_gap_triage.py`` pins severity scoring
and the ``worktrees/`` skip via the triage wrapper. This suite pins the
leftover those tests cannot see: the scan's own IDENT / SKIP_DIRS /
comment-join / CLI fail-closed surface.

Hermetic: TemporaryDirectory repos only. ``gh api`` is never called.
``util/`` is outside every pre-commit Python hook, so this suite is the gate.
"""

from __future__ import annotations

import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-08-28_resident_gap_scan.py"

# Long enough for --min-len 60, carries a MARKER, and names a unique snake_case token.
_GAP = "CRITICAL: never silently drop alpha_hazard_token when the finder walks " "this file and the comment is long enough to clear min-len"
_GAP_COMMENT = "# " + _GAP + "\n"

# Same shape, more distinctive identifiers -- ranks first under identifier-count sort.
_GAP_RICH = "CRITICAL: never silently drop bravo_hazard_token or CHARLIE_HAZARD_TOKEN " "or delta_hazard_token when the finder ranks by identifier count"
_GAP_RICH_COMMENT = "# " + _GAP_RICH + "\n"


def _load():
    spec = importlib.util.spec_from_file_location("resident_gap_scan", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()


def _write_repo(root: Path, agents: str | None, files: dict[str, str]) -> Path:
    if agents is not None:
        (root / "AGENTS.md").write_text(agents, encoding="utf-8")
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _scan(root: Path, extra: list[str] | None = None) -> tuple[int, str]:
    buf = io.StringIO()
    argv = [str(root), *(extra or [])]
    with redirect_stdout(buf):
        rc = mod.main(argv)
    return rc, buf.getvalue()


class IdentifiersTest(unittest.TestCase):
    def test_prose_backticks_are_not_identifiers(self):
        """First IDENT version accepted any `...` span; fragments inflate every candidate."""
        text = "CRITICAL: do not accept `), and the verbatim rejection detail (` " "as a name, it silently inflates every candidate"
        found = mod.identifiers(text)
        self.assertEqual(found, set(), f"prose backtick leaked into identifiers: {found}")
        for tok in found:
            self.assertNotIn(")", tok)
            self.assertNotIn(",", tok)

    def test_code_backtick_is_an_identifier(self):
        text = "CRITICAL: never silently skip `unique_token_zzz` when scoring the gap"
        self.assertIn("unique_token_zzz", mod.identifiers(text))

    def test_snake_and_constant_are_harvested(self):
        text = "CRITICAL: never silently alias OUTPUT_EPOCHS_SPLIT onto " "output_epochs_alias in this path"
        found = mod.identifiers(text)
        self.assertIn("output_epochs_alias", found)
        self.assertIn("OUTPUT_EPOCHS_SPLIT", found)

    def test_stop_drops_no_update(self):
        """``no_update`` is the I-1 starvation name and is deliberately not a gap key."""
        text = "CRITICAL: never silently treat no_update as an identifier in this " "comment block about the Dash execution model"
        found = mod.identifiers(text)
        self.assertNotIn("no_update", found)
        self.assertEqual(found, set(), f"STOP leak or unexpected harvest: {found}")


class CommentBlocksTest(unittest.TestCase):
    def test_contiguous_hash_lines_join(self):
        """A per-line split fails --min-len. The join is what makes a split directive one candidate."""
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.py"
            path.write_text(
                "# never silently\n" "# drop this_unique_token when the lines are split\n",
                encoding="utf-8",
            )
            blocks = mod.comment_blocks(path)
        self.assertEqual(len(blocks), 1, blocks)
        start, text = blocks[0]
        self.assertEqual(start, 1)
        self.assertIn("never silently", text)
        self.assertIn("this_unique_token", text)
        self.assertGreaterEqual(len(text), 60)

    def test_blank_line_splits_blocks(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.py"
            path.write_text("# first block here\n\n# second block here\n", encoding="utf-8")
            blocks = mod.comment_blocks(path)
        self.assertEqual([t for _, t in blocks], ["first block here", "second block here"])

    def test_unreadable_path_returns_empty(self):
        self.assertEqual(mod.comment_blocks(Path("/no/such/resident_gap_scan.py")), [])


class SkipDirsTest(unittest.TestCase):
    def test_dot_claude_copy_is_skipped_without_a_worktrees_segment(self):
        """#1697 pins ``worktrees/``. ``.claude`` is a second skip: session copies
        that are not named worktrees still multiply the census if this entry drops."""
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty resident file\n",
                files={".claude/session-copy/src/mod.py": _GAP_COMMENT},
            )
            rc, out = _scan(root)
        self.assertEqual(rc, 0, out)
        self.assertIn("CANDIDATES: 0", out)
        self.assertNotIn("alpha_hazard_token", out)
        self.assertNotIn(".claude/session-copy", out)

    def test_legacy_copy_is_skipped(self):
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty resident file\n",
                files={"legacy/src/mod.py": _GAP_COMMENT},
            )
            rc, out = _scan(root)
        self.assertEqual(rc, 0, out)
        self.assertIn("CANDIDATES: 0", out)
        self.assertNotIn("alpha_hazard_token", out)

    def test_real_src_hit_is_a_candidate(self):
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty resident file\n",
                files={"src/mod.py": _GAP_COMMENT},
            )
            rc, out = _scan(root)
        self.assertEqual(rc, 0, out)
        self.assertIn("CANDIDATES: 1", out)
        self.assertIn("src/mod.py", out)
        self.assertIn("alpha_hazard_token", out)


class ScanMainTest(unittest.TestCase):
    def test_missing_agents_md_is_exit_2(self):
        """Triage returns []. The scan is the operator surface and fail-closes."""
        with TemporaryDirectory() as tmp:
            root = _write_repo(Path(tmp), agents=None, files={"src/mod.py": _GAP_COMMENT})
            rc, out = _scan(root)
        self.assertEqual(rc, 2, out)
        self.assertIn("no AGENTS.md", out)
        self.assertNotIn("CANDIDATES:", out)

    def test_identifier_already_in_agents_is_not_a_candidate(self):
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="resident mention of alpha_hazard_token lives here\n",
                files={"src/mod.py": _GAP_COMMENT},
            )
            rc, out = _scan(root)
        self.assertEqual(rc, 0, out)
        self.assertIn("CANDIDATES: 0", out)
        self.assertNotIn("src/mod.py", out)

    def test_ranks_by_identifier_count(self):
        """Identifier count is a distinctiveness proxy, not severity -- why the triage exists."""
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty resident file\n",
                files={
                    "src/a_few.py": _GAP_COMMENT,
                    "src/z_many.py": _GAP_RICH_COMMENT,
                },
            )
            rc, out = _scan(root)
        self.assertEqual(rc, 0, out)
        self.assertIn("CANDIDATES: 2", out)
        pos_many = out.find("src/z_many.py")
        pos_few = out.find("src/a_few.py")
        self.assertNotEqual(pos_many, -1, out)
        self.assertNotEqual(pos_few, -1, out)
        self.assertLess(pos_many, pos_few, f"identifier-count rank inverted:\n{out}")

    def test_test_filename_is_skipped(self):
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty resident file\n",
                files={"src/test_hidden.py": _GAP_COMMENT},
            )
            rc, out = _scan(root)
        self.assertEqual(rc, 0, out)
        self.assertIn("CANDIDATES: 0", out)

    def test_short_block_is_skipped(self):
        short = "# NEVER silently delete this.\n"
        self.assertLess(len(short.lstrip("# ").strip()), 60)
        with TemporaryDirectory() as tmp:
            root = _write_repo(Path(tmp), agents="# empty resident file\n", files={"src/mod.py": short})
            rc, out = _scan(root)
        self.assertEqual(rc, 0, out)
        self.assertIn("CANDIDATES: 0", out)


if __name__ == "__main__":
    unittest.main()
