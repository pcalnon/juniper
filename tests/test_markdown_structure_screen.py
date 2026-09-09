#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Hermetic tests for ``util/ad-hoc/2026-09-05_markdown_structure_check.py`` -- the SCREEN that
``util/markdown_structure_delta.py`` (the CI gate) imports and calls per file.

The screen's ``check()`` was already exercised indirectly through the delta gate's suite.
Its ``main()`` was not, and that is where it under-reported: the file-selection predicate was

    if not p.is_file() or p.suffix.lower() != ".md":
        continue

``Path.is_file()`` FOLLOWS SYMLINKS, so a **dangling** symlink answers ``False`` and was
skipped -- silently, without being counted. ``main`` carries ten such links (nine under
``notes/legacy/`` pointing at a ``regressions/`` directory that is not on ``main``, one under
``notes/development/``), so a whole-tree run examined 1024 of 1034 paths while printing a
total that read as though it had covered all of them. The ten scored clean by never being
looked at.

That is the same **vacuous pass** shape the delta gate already guards -- a correct predicate
run over an incomplete site enumeration -- turned on the screen itself. Three behaviours are
pinned here:

* a markdown path that cannot be read is COUNTED and exits ``2``, never silently skipped;
* examining ZERO paths exits ``2``, so a run that filtered everything away cannot report
  success;
* a genuinely clean file still exits ``0``, and a file with a real structural problem still
  exits ``1`` -- the fix must not turn the screen into a permanent refusal.

Every fixture is a temp dir. Nothing reads the live tree.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "ad-hoc" / "2026-09-05_markdown_structure_check.py"

_spec = importlib.util.spec_from_file_location("markdown_structure_check", MODULE_PATH)
assert _spec and _spec.loader
screen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(screen)


CLEAN = "# Title\n\nSome prose.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
BROKEN_TABLE = "# Title\n\nprose\n\n| a | b |\n| 1 | 2 |\n"


def run(argv):
    """Call main(argv), returning (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = screen.main(argv)
    return code, out.getvalue(), err.getvalue()


class ScreenExitCodeTest(unittest.TestCase):
    def test_a_clean_markdown_file_exits_zero(self):
        with TemporaryDirectory() as td:
            p = Path(td, "clean.md")
            p.write_text(CLEAN)
            code, out, _err = run([str(p)])
        self.assertEqual(code, 0)
        self.assertIn("examined 1 of 1", out)

    def test_a_structural_problem_still_exits_one(self):
        # The vacuity guard must not swallow the finding the screen exists for.
        with TemporaryDirectory() as td:
            p = Path(td, "broken.md")
            p.write_text(BROKEN_TABLE)
            code, out, _err = run([str(p)])
        self.assertEqual(code, 1)
        self.assertIn("has no separator row", out)

    def test_no_arguments_exits_two(self):
        code, _out, _err = run([])
        self.assertEqual(code, 2)


class DanglingSymlinkTest(unittest.TestCase):
    """The ten links on `main` that used to score clean by never being read."""

    def _dangling(self, td):
        link = Path(td, "dangling.md")
        link.symlink_to(Path(td, "regressions", "gone.md"))
        return link

    def test_a_dangling_symlink_is_counted_and_refuses(self):
        with TemporaryDirectory() as td:
            link = self._dangling(td)
            self.assertFalse(link.is_file(), "fixture must be a dangling link")
            code, _out, err = run([str(link)])
        self.assertEqual(code, 2, "a markdown path that cannot be read must not pass")
        self.assertIn("could not read 1 markdown path", err)
        self.assertIn("refusing to report on a partial examination", err)

    def test_one_dangling_link_beside_nine_readable_files_still_refuses(self):
        # The precise regression: skipping without counting meant nine readable files
        # reported success and said nothing about the tenth.
        with TemporaryDirectory() as td:
            paths = []
            for i in range(9):
                p = Path(td, f"ok{i}.md")
                p.write_text(CLEAN)
                paths.append(str(p))
            paths.append(str(self._dangling(td)))
            code, out, err = run(paths)
        self.assertEqual(code, 2)
        self.assertIn("examined 9 of 10", out)
        self.assertIn("could not read 1", err)

    def test_a_symlink_that_RESOLVES_is_examined_normally(self):
        # Not every symlink is broken -- the fix must not refuse the working ones.
        with TemporaryDirectory() as td:
            real = Path(td, "real.md")
            real.write_text(CLEAN)
            link = Path(td, "link.md")
            link.symlink_to(real)
            code, out, _err = run([str(link)])
        self.assertEqual(code, 0)
        self.assertIn("examined 1 of 1", out)


class VacuousExaminationTest(unittest.TestCase):
    def test_all_paths_filtered_as_non_markdown_exits_two(self):
        with TemporaryDirectory() as td:
            a, b = Path(td, "setup.py"), Path(td, "conf.toml")
            a.write_text("x = 1\n")
            b.write_text("k = 1\n")
            code, _out, err = run([str(a), str(b)])
        self.assertEqual(code, 2, "examining nothing must not report success")
        self.assertIn("examined 0 of 2", err)

    def test_a_non_markdown_path_beside_a_real_one_is_reported_not_fatal(self):
        # Mixed globs are the normal calling convention; filtering is legitimate as long
        # as it is COUNTED and at least one file was actually examined.
        with TemporaryDirectory() as td:
            md = Path(td, "clean.md")
            md.write_text(CLEAN)
            other = Path(td, "notes.txt")
            other.write_text("hello\n")
            code, out, _err = run([str(md), str(other)])
        self.assertEqual(code, 0)
        self.assertIn("skipped 1 non-markdown", out)


class DeltaGateStillLoadsTheScreenTest(unittest.TestCase):
    """`util/markdown_structure_delta.py` imports this module by path and calls `check()`.

    The vacuity fix touched `main()` only, but the gate is a required CI check, so the
    import contract is pinned here rather than discovered on `main`.
    """

    def test_the_gate_can_load_the_screen_and_call_check(self):
        gate_path = REPO_ROOT / "util" / "markdown_structure_delta.py"
        spec = importlib.util.spec_from_file_location("markdown_structure_delta", gate_path)
        assert spec and spec.loader
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        loaded = gate._load_screen()
        self.assertTrue(hasattr(loaded, "check"), "the gate depends on check()")
        with TemporaryDirectory() as td:
            p = Path(td, "x.md")
            p.write_text(BROKEN_TABLE)
            self.assertEqual(len(loaded.check(p)), 1)


if __name__ == "__main__":
    unittest.main()
