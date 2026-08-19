#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/relocation_check.py`` -- gate G3 of the shared-session-memory
plan. ``util/`` is outside every pre-commit Python hook's scope, so this suite IS
the gate.

The single most important test here is
``test_identifiers_carried_but_prose_dropped_fails``. A synthesis reviewer named
that case as the one thing to check first: the source proposal's own completeness
check was token-level and *passes* on exactly that loss, because the identifiers
survive in the destination while the reasoning that explained them does not. If
G3 ships tautological, the P3 migration has **no** content-loss control at all --
the docs screen is blind to pointer-shaped deletion at any magnitude.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "util" / "relocation_check.py"

_spec = importlib.util.spec_from_file_location("relocation_check", MODULE_PATH)
assert _spec and _spec.loader
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)

_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
    "PATH": "/usr/bin:/bin",
}

# A realistic AGENTS.md bullet: identifiers plus the reasoning that explains them.
SOURCE_LINE = "- `util/editable_install_drift_check.py` -- Ambiguous canonical: " "`discover_canonical` returns `(None, [.., ..])` when two non-worktree " "checkouts share a name, and `--fix` then skips rather than picking " "`candidates[0]`, because guessing would silently re-point a deliberate checkout."


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        env={**_ENV, "HOME": str(repo)},
    )


class Fixture:
    """Throwaway repo with a source doc and a destination doc, one commit deep."""

    def __init__(self, tmp: Path, source_body: str, dest_body: str) -> None:
        self.root = tmp
        _git(self.root, "init", "-q", "-b", "main")
        self.source = self.root / "AGENTS.md"
        self.dest_dir = self.root / "docs"
        self.dest_dir.mkdir()
        self.dest = self.dest_dir / "REFERENCE.md"
        self.source.write_text(source_body, encoding="utf-8")
        self.dest.write_text(dest_body, encoding="utf-8")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "base")

    def relocate(self, source_body: str, dest_body: str) -> None:
        self.source.write_text(source_body, encoding="utf-8")
        self.dest.write_text(dest_body, encoding="utf-8")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "relocate")

    def check(self, **kw):
        params = {
            "repo": self.root,
            "base": "HEAD~1",
            "head": "HEAD",
            "source": "AGENTS.md",
            "dest": "docs/REFERENCE.md",
            "threshold": rc.DEFAULT_THRESHOLD,
            "min_chars": rc.DEFAULT_MIN_CHARS,
            "expect_removals": False,
        }
        params.update(kw)
        return rc.check(**params)


class RelocationCompletenessTest(unittest.TestCase):
    def test_verbatim_relocation_passes(self):
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            fx.relocate("# A\n\nSee the reference.\n", f"# R\n\n{SOURCE_LINE}\n")
            self.assertEqual(fx.check()["unmatched"], 0)

    def test_reworded_relocation_passes(self):
        """Relocation legitimately rewrites the lead-in; that is not a loss."""
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            reworded = "### Ambiguous canonical\n\n" "`discover_canonical` returns `(None, [.., ..])` when two non-worktree " "checkouts share a name, and `--fix` then skips rather than picking " "`candidates[0]`, because guessing would silently re-point a " "deliberate checkout.\n"
            fx.relocate("# A\n\nSee the reference.\n", f"# R\n\n{reworded}")
            self.assertEqual(fx.check()["unmatched"], 0)

    def test_identifiers_carried_but_prose_dropped_fails(self):
        """THE load-bearing test. A token-level check passes here; G3 must not.

        The destination keeps every backticked identifier from the removed line
        and drops the reasoning. The knowledge is gone; the tokens are not.
        """
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            tokens_only = "### editable_install_drift_check\n\n" "`discover_canonical`, `--fix`, `candidates[0]`\n"
            fx.relocate("# A\n\nSee the reference.\n", f"# R\n\n{tokens_only}")
            result = fx.check()
            self.assertEqual(result["unmatched"], 1, result)
            self.assertLess(result["findings"][0]["best_score"], rc.DEFAULT_THRESHOLD)

    def test_in_place_rewrite_is_not_a_loss(self):
        """An in-place reword looks identical to a relocation in the diff.

        Found by running this gate on its own PR: searching only the destination
        reported a reworded-but-retained bullet as content loss. "Lost" means gone
        from BOTH files, so the source at HEAD is part of the haystack.
        """
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            reworded = "- `util/editable_install_drift_check.py` -- Ambiguous canonical: " "`discover_canonical` returns `(None, [.., ..])` when two non-worktree " "checkouts share a name; `--fix` then skips instead of picking " "`candidates[0]`, since guessing would silently re-point a deliberate " "checkout."
            fx.relocate(f"# A\n\n{reworded}\n", "# R\n")
            self.assertEqual(fx.check()["unmatched"], 0)

    def test_outright_deletion_fails(self):
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            fx.relocate("# A\n\nSee the reference.\n", "# R\n")
            self.assertEqual(fx.check()["unmatched"], 1)

    def test_merged_into_a_longer_destination_line_passes(self):
        """Destination CONTAINS the removed line -- a merge, not a loss."""
        with TemporaryDirectory() as td:
            short = "- `--fix` re-points orphaned editable installs to their canonical repo."
            fx = Fixture(Path(td), f"# A\n\n{short}\n", "# R\n")
            merged = "Repair: `--fix` re-points orphaned editable installs to their " "canonical repo. `--dry-run` previews the plan.\n"
            fx.relocate("# A\n\nSee the reference.\n", f"# R\n\n{merged}")
            self.assertEqual(fx.check()["unmatched"], 0)


class NoiseFilterTest(unittest.TestCase):
    def test_markup_only_removals_are_ignored(self):
        with TemporaryDirectory() as td:
            body = "# A\n\n| a | b |\n| --- | --- |\n\n```\ncode\n```\n\n## Heading\n"
            fx = Fixture(Path(td), body, "# R\n")
            fx.relocate("# A\n", "# R\n")
            self.assertEqual(fx.check()["unmatched"], 0)

    def test_short_lines_below_min_chars_are_ignored(self):
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), "# A\n\n- tiny note\n", "# R\n")
            fx.relocate("# A\n", "# R\n")
            self.assertEqual(fx.check()["removed_substantive"], 0)

    def test_is_substantive_predicate(self):
        self.assertFalse(rc.is_substantive("", 40))
        self.assertFalse(rc.is_substantive("### Heading", 40))
        self.assertFalse(rc.is_substantive("| --- | --- |", 40))
        self.assertFalse(rc.is_substantive("```bash", 40))
        self.assertTrue(rc.is_substantive(SOURCE_LINE, 40))


class MachineryNegativeControlTest(unittest.TestCase):
    """A gate that cannot fail is not a gate."""

    def test_missing_destination_at_head_is_a_hard_failure(self):
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            with self.assertRaises(rc.RelocationError):
                fx.check(dest="docs/DOES_NOT_EXIST.md")

    def test_missing_source_at_head_is_a_hard_failure(self):
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            with self.assertRaises(rc.RelocationError):
                fx.check(source="NOPE.md")

    def test_expect_removals_refuses_a_vacuous_pass(self):
        """The caller asserted a relocation; a diff with no removals means the
        check would have passed on an empty input."""
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), "# A\n", "# R\n")
            fx.relocate("# A\n", "# R\n\nsomething new and quite long enough here\n")
            with self.assertRaises(rc.RelocationError):
                fx.check(expect_removals=True)

    def test_bad_ref_is_a_hard_failure(self):
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            with self.assertRaises(rc.RelocationError):
                fx.check(base="no-such-ref")


class ContainmentAsymmetryTest(unittest.TestCase):
    """The asymmetry is the anti-tautology property; pin it directly."""

    def test_needle_inside_candidate_is_a_full_match(self):
        self.assertEqual(rc.best_match("alpha beta", ["x alpha beta y"]), 1.0)

    def test_candidate_inside_needle_is_not_a_full_match(self):
        score = rc.best_match(
            "the fix flag skips rather than picking candidates 0 when ambiguous",
            ["candidates 0"],
        )
        self.assertLess(score, 1.0)
        self.assertLess(score, rc.DEFAULT_THRESHOLD)


class CliTest(unittest.TestCase):
    def _run(self, fx: Fixture, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MODULE_PATH), "--repo-root", str(fx.root), "--base", "HEAD~1", "--head", "HEAD", *extra],
            capture_output=True,
            text=True,
        )

    def test_exit_one_on_loss(self):
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            fx.relocate("# A\n", "# R\n")
            res = self._run(fx)
            self.assertEqual(res.returncode, 1)
            self.assertIn("[LOST]", res.stdout)

    def test_exit_zero_when_complete(self):
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            fx.relocate("# A\n", f"# R\n\n{SOURCE_LINE}\n")
            self.assertEqual(self._run(fx).returncode, 0)

    def test_advisory_reports_but_exits_zero(self):
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            fx.relocate("# A\n", "# R\n")
            res = self._run(fx, "--advisory")
            self.assertEqual(res.returncode, 0)
            self.assertIn("ADVISORY", res.stdout)
            self.assertIn("[LOST]", res.stdout)

    def test_exit_two_on_broken_machinery(self):
        with TemporaryDirectory() as td:
            fx = Fixture(Path(td), f"# A\n\n{SOURCE_LINE}\n", "# R\n")
            self.assertEqual(self._run(fx, "--source", "NOPE.md").returncode, 2)


if __name__ == "__main__":
    unittest.main()
