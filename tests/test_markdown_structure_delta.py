#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Hermetic tests for ``util/markdown_structure_delta.py`` -- the CI gate that fails a PR which
BREAKS markdown structure without demanding a clean tree first.

``util/`` draws "(no files to check) Skipped" from every pre-commit Python hook, so this
unittest **is** the gate for that module.

The three things a gate like this gets wrong, each pinned here:

* **Red on arrival.** ``main`` carries 104 structural problems across 23 files, most in
  ``notes/legacy/`` and ``notes/code-review/``. A gate demanding zero is unmergeable from the
  first commit, so the comparison must be per-file and per-PR: a file the PR does not touch is
  not the PR's problem, and a file it touches must not come out worse than it went in.
* **Vacuous pass.** The underlying screen silently skips anything not ending ``.md``. A bad glob,
  a wrong base ref, or a sanitised temp filename examines nothing and reports success -- a
  correct predicate over an empty site enumeration. Examining zero of N touched files must be an
  error, not a pass.
* **A new file graded on a curve.** A file the PR ADDS has no "before", and defaulting its
  baseline to anything but zero would let a PR introduce a broken table in new prose.

Every fixture is a synthetic git repository under a temp dir. Nothing reads the live tree.
"""

from __future__ import annotations

import importlib.util
import subprocess  # nosec B404 - fixed argv git, no shell
import unittest
import unittest.mock
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "markdown_structure_delta.py"

_spec = importlib.util.spec_from_file_location("markdown_structure_delta", MODULE_PATH)
assert _spec and _spec.loader
msd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(msd)

CLEAN_TABLE = "# Doc\n\n| Symptom | Fix |\n|---------|-----|\n| a | b |\n"
BROKEN_TABLE = "# Doc\n\n| Symptom | Fix |\n| a | b |\n"
CLEAN_FENCE = "# Doc\n\n```bash\necho hi\n```\n\n## After\n\ntext\n"
BROKEN_FENCE = "# Doc\n\n```bash\necho hi\n\n## After\n\ntext\n"


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=120, check=False)


def _repo(root: Path) -> None:
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Test")


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "--no-verify", "-m", message)
    return _git(root, "rev-parse", "HEAD").stdout.strip()


class DeltaGateTest(unittest.TestCase):
    """`run(before, after)` drives the module against a synthetic two-commit history."""

    def run_gate(self, before: dict[str, str], after: dict[str, str]) -> tuple[int, str]:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            for name, text in before.items():
                (root / name).write_text(text, encoding="utf-8")
            (root / "seed.txt").write_text("seed\n", encoding="utf-8")
            base = _commit(root, "base")
            for name, text in after.items():
                (root / name).write_text(text, encoding="utf-8")
            _commit(root, "head")

            # The module resolves paths against its own REPO_ROOT; point that at the fixture.
            with unittest.mock.patch.object(msd, "REPO_ROOT", root):
                from contextlib import redirect_stdout
                from io import StringIO

                buf = StringIO()
                with redirect_stdout(buf):
                    code = msd.main(["--base", base, "--head", "HEAD"])
                return code, buf.getvalue()

    def test_untouched_broken_file_does_not_fail_the_pr(self):
        # The whole reason the gate can ship today: `main` carries 104 problems and a PR that
        # does not touch them is not the PR's problem.
        code, out = self.run_gate(
            {"legacy.md": BROKEN_TABLE, "touched.md": CLEAN_TABLE},
            {"touched.md": CLEAN_TABLE + "\n| c | d |\n"},
        )
        self.assertEqual(code, 0)
        self.assertNotIn("legacy.md", out, "an untouched file must not even be examined")

    def test_a_file_the_pr_breaks_FAILS(self):
        code, out = self.run_gate({"doc.md": CLEAN_TABLE}, {"doc.md": CLEAN_TABLE + "\n| X | Y |\n| p | q |\n"})
        self.assertEqual(code, 1)
        self.assertIn("doc.md", out)

    def test_a_touched_file_that_stays_equally_broken_PASSES(self):
        # Inherited damage is invisible; only an INCREASE is the PR's doing. A gate keyed on the
        # count rather than the delta fails here, which is what makes it unshippable.
        code, out = self.run_gate({"doc.md": BROKEN_TABLE}, {"doc.md": BROKEN_TABLE + "\nmore prose\n"})
        self.assertEqual(code, 0)
        self.assertIn("1 -> 1", out)

    def test_a_touched_file_that_gets_BETTER_passes(self):
        code, _ = self.run_gate({"doc.md": BROKEN_TABLE}, {"doc.md": CLEAN_TABLE})
        self.assertEqual(code, 0)

    def test_a_NEW_broken_file_fails_even_though_it_has_no_before(self):
        # No "before" must mean zero, not "unknown, therefore fine".
        code, out = self.run_gate({"other.md": CLEAN_TABLE}, {"added.md": BROKEN_TABLE})
        self.assertEqual(code, 1)
        self.assertIn("added", out)

    def test_an_unbalanced_fence_is_caught_as_well_as_a_table(self):
        # The fence is the one markdownlint and the link validator both miss: it does not go
        # "missing", it silently absorbs every heading after it.
        code, out = self.run_gate({"doc.md": CLEAN_FENCE}, {"doc.md": BROKEN_FENCE})
        self.assertEqual(code, 1)
        self.assertIn("doc.md", out)

    def test_a_pr_touching_no_markdown_is_not_an_error(self):
        code, out = self.run_gate({"doc.md": CLEAN_TABLE}, {"code.py": "x = 1\n"})
        self.assertEqual(code, 0)
        self.assertIn("no markdown touched", out)

    def test_a_deleted_file_is_not_compared(self):
        # A deletion has no head state; comparing it would read the screen's "cannot open" as
        # zero problems and quietly pass, or crash. Neither is a verdict.
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / "gone.md").write_text(BROKEN_TABLE, encoding="utf-8")
            (root / "stay.md").write_text(CLEAN_TABLE, encoding="utf-8")
            base = _commit(root, "base")
            (root / "gone.md").unlink()
            _commit(root, "head")
            with unittest.mock.patch.object(msd, "REPO_ROOT", root):
                self.assertEqual(msd.touched_markdown(base, "HEAD"), [])


class VacuousExaminationTest(unittest.TestCase):
    """Examining zero of N touched files must be an ERROR, never a pass."""

    def test_examining_none_of_the_touched_files_exits_2(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / "doc.md").write_text(CLEAN_TABLE, encoding="utf-8")
            base = _commit(root, "base")
            (root / "doc.md").write_text(CLEAN_TABLE + "\ntext\n", encoding="utf-8")
            _commit(root, "head")
            with unittest.mock.patch.object(msd, "REPO_ROOT", root):
                # Every `git show` fails -> nothing is examined. Without the guard the loop
                # completes with 0 regressions and reports success over an EMPTY site set.
                with unittest.mock.patch.object(msd, "problems_at", return_value=None):
                    self.assertEqual(msd.main(["--base", base, "--head", "HEAD"]), 2)

    def test_the_screen_only_reads_dot_md_so_the_temp_name_keeps_the_suffix(self):
        # `problems_at` materialises the blob under the ORIGINAL basename. A sanitised temp name
        # would be skipped by the screen and score 0 for every file -- vacuous, and green.
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn("Path(td) / Path(rel).name", source)


class RefResolutionTest(unittest.TestCase):
    def test_an_unresolvable_base_exits_2_rather_than_comparing_nothing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / "doc.md").write_text(CLEAN_TABLE, encoding="utf-8")
            _commit(root, "base")
            with unittest.mock.patch.object(msd, "REPO_ROOT", root):
                self.assertEqual(msd.main(["--base", "refs/heads/nope", "--head", "HEAD"]), 2)


if __name__ == "__main__":
    unittest.main()
