"""Tests for the docs deletion-magnitude screen (``docs_additions_check`` + its CLI).

Migrated from juniper-ml's ``tests/test_docs_additions_check.py`` (Wave 0 of the
sequence-safety rollout) and converted from importlib path-loading of the util
script to package imports + in-process CLI invocation (``cli_main(argv)`` with
``redirect_stdout`` -- the ci-tools house idiom, so the ``--enforce`` per-file
coverage gate measures the modules); a single ``python -m`` ``--help`` smoke
proves the module-form entry.

Hermetic: every case builds a throwaway git repo under a tempdir (``git -C``,
never ``cd``) with a BASE and a HEAD commit. The fixtures pin git identity +
``commit.gpgsign`` locally and the module only reads git, so no custom subprocess
``env=`` mapping is needed (the RedactedEnv house rule has nothing to wrap here).

Coverage: additions-only clean pass, heading-deletion FAIL, the >=N
consecutive-deletion FAIL, small-deletion / small-swap WARN, heading-retitle
WARN, scope (AGENTS.md + notes/ in, a non-.md file out), the ``Allow-Docs-Rewrite``
trailer escape (enumerated + basename + wildcard), the tunable ``--min-run``, the
``--advisory`` downgrade, human + JSON output, exit codes 0/1/2, and the new
``--scope`` glob parameterization (default==universal predicate; a glob screens
its surface; the extension gate still applies; ``--files`` still bypasses scope)
+ ``_match_scope``.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

import juniper_ci_tools.docs_additions_check as dac
from juniper_ci_tools.cli_docs_additions_check import main as cli_main

_TIMEOUT = 30
_CI_TOOLS_ROOT = Path(__file__).resolve().parent.parent

_SECTIONED = "# Title\n\n## Section One\n\nbody a\nbody b\n\n## Section Two\n\nkeep me\n"


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=check, timeout=_TIMEOUT)


def _init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "tests@example.invalid")
    _git(root, "config", "user.name", "Test User")
    _git(root, "config", "commit.gpgsign", "false")


def _write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _commit(root: Path, msg: str) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", msg)


def _invoke(root: Path, *extra: str, base: str = "HEAD~1", head: str = "HEAD") -> tuple[int, str, str]:
    """Drive the CLI in-process; return (exit_code, stdout, stderr)."""
    argv = ["--base", base, "--head", head, "--repo-root", str(root), *extra]
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cli_main(argv)
    return rc, out.getvalue(), err.getvalue()


def _run_json(root: Path, *extra: str, base: str = "HEAD~1", head: str = "HEAD") -> tuple[int, dict, str]:
    rc, out, err = _invoke(root, "--json", *extra, base=base, head=head)
    return rc, json.loads(out), err


def _reasons(report: dict) -> dict:
    return {f["path"]: f for f in report["findings"]}


class DocsDeletionBehaviourTest(unittest.TestCase):
    def test_additions_only_is_clean(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n\n## New Section\n\nmore\n")
            _commit(root, "add a section")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(report["stats"]["fail_count"], 0)

    def test_heading_deletion_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "drop Section One")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 1, msg=err)
            f = _reasons(report)["docs/REFERENCE.md"]
            self.assertEqual((f["reason"], f["severity"]), ("heading-deletion", "FAIL"))

    def test_long_deletion_run_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n\nl1\nl2\nl3\nl4\nl5\nl6\n\noutro\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n\noutro\n")
            _commit(root, "gut the body block")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 1, msg=err)
            f = _reasons(report)["docs/REFERENCE.md"]
            self.assertEqual((f["reason"], f["severity"]), ("deletion-run", "FAIL"))

    def test_small_deletion_is_warn(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nkeep\nl1\nl2\ntail\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\nkeep\ntail\n")
            _commit(root, "drop two lines")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            f = _reasons(report)["docs/REFERENCE.md"]
            self.assertEqual((f["reason"], f["severity"]), ("small-deletion", "WARN"))

    def test_in_place_swap_is_warn(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nold line one\nold line two\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\nnew line one\nnew line two\n")
            _commit(root, "swap two lines")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(_reasons(report)["docs/REFERENCE.md"]["severity"], "WARN")

    def test_heading_retitle_is_warn_not_fail(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Old Name\n\nbody\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## New Name\n\nbody\n")
            _commit(root, "rename a section heading")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(_reasons(report)["docs/REFERENCE.md"]["severity"], "WARN")

    def test_agents_md_and_notes_are_in_scope(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "AGENTS.md", "# Agents\n\n## Kept\n\nx\n\n## Doomed\n\ny\n")
            _write(root, "notes/JUNIPER_2026-07-28_JUNIPER-ML_DEMO.md", "# Note\n\n## Runbook\n\nsteps\n")
            _commit(root, "base")
            _write(root, "AGENTS.md", "# Agents\n\n## Kept\n\nx\n")
            _write(root, "notes/JUNIPER_2026-07-28_JUNIPER-ML_DEMO.md", "# Note\n\nsteps\n")
            _commit(root, "drop headings in both")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 1, msg=err)
            paths = _reasons(report)
            self.assertEqual(paths["AGENTS.md"]["reason"], "heading-deletion")
            self.assertEqual(paths["notes/JUNIPER_2026-07-28_JUNIPER-ML_DEMO.md"]["reason"], "heading-deletion")

    def test_non_markdown_file_is_ignored(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/tool.py", "# many\n# comment\n# lines\n# here\n# to\n# delete\nx = 1\n")
            _commit(root, "base")
            _write(root, "util/tool.py", "x = 1\n")
            _commit(root, "trim a py file")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(report["stats"]["files_screened"], 0)


class DocsDeletionScopeTest(unittest.TestCase):
    """The new --scope glob parameterization + the universal default."""

    def test_default_scope_ignores_out_of_cluster_markdown(self) -> None:
        """With no --scope, a heading deletion in a markdown file OUTSIDE the universal
        cluster (e.g. guides/) is not screened -- the universal predicate is preserved."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "guides/HOWTO.md", "# Title\n\n## Doomed\n\nbody\n")
            _commit(root, "base")
            _write(root, "guides/HOWTO.md", "# Title\n\nbody\n")
            _commit(root, "drop a heading outside the cluster")
            rc, report, err = _run_json(root)  # no --scope
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(report["stats"]["files_screened"], 0)

    def test_scope_glob_screens_matched_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "guides/HOWTO.md", "# Title\n\n## Doomed\n\nbody\n")
            _commit(root, "base")
            _write(root, "guides/HOWTO.md", "# Title\n\nbody\n")
            _commit(root, "drop a heading under guides/")
            rc, report, err = _run_json(root, "--scope", "guides/**/*.md")
            self.assertEqual(rc, 1, msg=err)
            self.assertEqual(_reasons(report)["guides/HOWTO.md"]["reason"], "heading-deletion")

    def test_scope_extension_gate_still_applies(self) -> None:
        """A path matching the glob but not ending .md is not screened."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "guides/notes.txt", "# heading-ish\nl1\nl2\nl3\nl4\nl5\nl6\n")
            _write(root, "guides/HOWTO.md", "# Title\n\n## Doomed\n\nbody\n")
            _commit(root, "base")
            _write(root, "guides/notes.txt", "# heading-ish\n")
            _write(root, "guides/HOWTO.md", "# Title\n\nbody\n")
            _commit(root, "trim txt + drop md heading")
            rc, report, err = _run_json(root, "--scope", "guides/**")
            self.assertEqual(rc, 1, msg=err)
            self.assertIn("guides/HOWTO.md", _reasons(report))
            self.assertIn("guides/notes.txt", report["stats"]["skipped_out_of_scope"])


class DocsDeletionThresholdAndEscapeTest(unittest.TestCase):
    def test_min_run_threshold_is_tunable(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nkeep\nd1\nd2\nd3\ntail\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\nkeep\ntail\n")
            _commit(root, "drop three lines")
            rc_default, report_default, err_default = _run_json(root)  # 3 < default 5 -> WARN
            self.assertEqual(rc_default, 0, msg=err_default)
            self.assertEqual(_reasons(report_default)["docs/REFERENCE.md"]["severity"], "WARN")
            rc_tight, report_tight, err_tight = _run_json(root, "--min-run", "3")  # 3 >= 3 -> FAIL
            self.assertEqual(rc_tight, 1, msg=err_tight)
            self.assertEqual(_reasons(report_tight)["docs/REFERENCE.md"]["reason"], "deletion-run")

    def test_trailer_waives_enumerated_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "rewrite reference\n\nAllow-Docs-Rewrite: docs/REFERENCE.md")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(_reasons(report)["docs/REFERENCE.md"]["severity"], "WAIVED")

    def test_trailer_waives_by_basename(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "rewrite\n\nAllow-Docs-Rewrite: REFERENCE.md")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(_reasons(report)["docs/REFERENCE.md"]["severity"], "WAIVED")

    def test_wildcard_trailer_waives_all(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "bulk docs rewrite\n\nAllow-Docs-Rewrite: *")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertTrue(report["stats"]["wildcard_waiver"])
            self.assertEqual(_reasons(report)["docs/REFERENCE.md"]["severity"], "WAIVED")


class DocsDeletionHumanOutputTest(unittest.TestCase):
    """The non-JSON human reporter (``_print_human``) branches."""

    def test_human_clean_prints_ok(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n\n## New\n\nmore\n")
            _commit(root, "add")
            rc, out, err = _invoke(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertIn("OK: no unwaived docs-deletion findings", out)

    def test_human_fail_lists_findings(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "drop Section One")
            rc, out, err = _invoke(root)
            self.assertEqual(rc, 1, msg=err)
            self.assertIn("[FAIL/heading-deletion]", out)
            self.assertIn("FAIL: 1 unwaived docs-deletion finding", out)

    def test_human_waived_note(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "rewrite\n\nAllow-Docs-Rewrite: docs/REFERENCE.md")
            rc, out, err = _invoke(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertIn("waived (Allow-Docs-Rewrite): docs/REFERENCE.md", out)

    def test_human_wildcard_waiver_note(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "rewrite\n\nAllow-Docs-Rewrite: *")
            rc, out, err = _invoke(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertIn("waived (Allow-Docs-Rewrite): *", out)


class DocsDeletionCliContractTest(unittest.TestCase):
    def test_missing_base_is_usage_error(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            cli_main(["--head", "HEAD"])
        self.assertEqual(ctx.exception.code, 2)

    def test_unresolvable_ref_is_exit_2(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n")
            _commit(root, "base")
            rc, out, err = _invoke(root, base="nope", head="HEAD")
            self.assertEqual(rc, 2)
            self.assertIn("could not resolve ref", err)

    def test_bad_min_run_is_exit_2(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n")
            _commit(root, "base")
            rc, out, err = _invoke(root, "--min-run", "0")
            self.assertEqual(rc, 2)
            self.assertIn("--min-run must be >= 1", err)

    def test_explicit_files_bypasses_scope_filter(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            # a README.md is out of the universal cluster; --files targets it directly.
            _write(root, "README.md", "# Title\n\n## Doomed\n\nbody\n")
            _commit(root, "base")
            _write(root, "README.md", "# Title\n\nbody\n")
            _commit(root, "drop a heading in README")
            rc_auto, report_auto, err_auto = _run_json(root)
            self.assertEqual(rc_auto, 0, msg=err_auto)  # README.md not in the cluster
            rc_x, report_x, err_x = _run_json(root, "--files", "README.md")
            self.assertEqual(rc_x, 1, msg=err_x)
            self.assertEqual(_reasons(report_x)["README.md"]["reason"], "heading-deletion")

    def test_module_form_help_smoke(self) -> None:
        """`python -m juniper_ci_tools.cli_docs_additions_check --help` resolves and shows
        --scope + --min-run. cwd is the ci-tools root so it works with or without install."""
        cp = subprocess.run(
            [sys.executable, "-m", "juniper_ci_tools.cli_docs_additions_check", "--help"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
            cwd=str(_CI_TOOLS_ROOT),
        )
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
        self.assertIn("--scope", cp.stdout)
        self.assertIn("--min-run", cp.stdout)


class DocsDeletionAdvisoryTest(unittest.TestCase):
    """The --advisory (per-PR docs-rewrite label hatch) exit-0 downgrade."""

    def test_advisory_downgrades_fail_to_exit_0_but_keeps_findings(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "drop Section One")
            rc_strict, report_strict, err_strict = _run_json(root)
            self.assertEqual(rc_strict, 1, msg=err_strict)
            rc_adv, report_adv, err_adv = _run_json(root, "--advisory")
            self.assertEqual(rc_adv, 0, msg=err_adv)
            self.assertTrue(report_adv["advisory"])
            f = _reasons(report_adv)["docs/REFERENCE.md"]
            self.assertEqual((f["reason"], f["severity"]), ("heading-deletion", "FAIL"))
            self.assertEqual(report_adv["stats"]["fail_count"], 1)

    def test_advisory_human_output_prints_downgrade_note(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "drop Section One")
            rc, out, err = _invoke(root, "--advisory")
            self.assertEqual(rc, 0, msg=err)
            self.assertIn("ADVISORY", out)

    def test_advisory_clean_diff_is_still_exit_0(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n\n## New Section\n\nmore\n")
            _commit(root, "add a section")
            rc, report, err = _run_json(root, "--advisory")
            self.assertEqual(rc, 0, msg=err)
            self.assertTrue(report["advisory"])
            self.assertEqual(report["stats"]["fail_count"], 0)

    def test_advisory_does_not_mask_invocation_error_exit_2(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n")
            _commit(root, "base")
            rc, out, err = _invoke(root, "--advisory", base="nope", head="HEAD")
            self.assertEqual(rc, 2, msg=out)


class DocsDeletionHelperUnitTest(unittest.TestCase):
    def test_in_docs_scope(self) -> None:
        self.assertTrue(dac.in_docs_scope("AGENTS.md"))
        self.assertTrue(dac.in_docs_scope("CLAUDE.md"))
        self.assertTrue(dac.in_docs_scope("docs/REFERENCE.md"))
        self.assertTrue(dac.in_docs_scope("notes/JUNIPER_x.md"))
        self.assertFalse(dac.in_docs_scope("README.md"))
        self.assertFalse(dac.in_docs_scope("util/x.py"))
        self.assertFalse(dac.in_docs_scope("docs/diagram.png"))

    def test_match_scope(self) -> None:
        self.assertTrue(dac._match_scope("docs/a.md", ["docs/**/*.md"]))
        self.assertTrue(dac._match_scope("docs/sub/a.md", ["docs/**/*.md"]))
        self.assertFalse(dac._match_scope("notes/a.md", ["docs/**/*.md"]))
        self.assertTrue(dac._match_scope("guides/x.md", ["guides/**"]))
        self.assertTrue(dac._match_scope("AGENTS.md", ["AGENTS.md"]))
        self.assertFalse(dac._match_scope("docs/a.md", []))

    def test_parse_hunks_splits_and_counts(self) -> None:
        diff = "diff --git a/x.md b/x.md\n--- a/x.md\n+++ b/x.md\n@@ -1,2 +1,0 @@\n-gone one\n-gone two\n@@ -5,0 +4,1 @@\n+added\n"
        hunks = dac.parse_hunks(diff)
        self.assertEqual(len(hunks), 2)
        self.assertEqual(hunks[0].deleted, ["gone one", "gone two"])
        self.assertEqual(hunks[0].added, [])
        self.assertEqual(hunks[1].added, ["added"])

    def test_classify_heading_and_run(self) -> None:
        heading = dac.classify_file("docs/x.md", [dac.Hunk(deleted=["## Section"], added=[])], 5)
        self.assertEqual((heading[0].reason, heading[0].severity), ("heading-deletion", "FAIL"))
        run = dac.classify_file("docs/x.md", [dac.Hunk(deleted=["a", "b", "c", "d", "e"], added=[])], 5)
        self.assertEqual((run[0].reason, run[0].severity), ("deletion-run", "FAIL"))
        swap = dac.classify_file("docs/x.md", [dac.Hunk(deleted=["a", "b"], added=["c", "d"])], 5)
        self.assertEqual((swap[0].reason, swap[0].severity), ("small-deletion", "WARN"))

    def test_parse_allow_trailers(self) -> None:
        allowed, wildcard = dac.parse_allow_trailers("fix\n\nAllow-Docs-Rewrite: docs/REFERENCE.md, AGENTS.md\n")
        self.assertEqual(allowed, {"docs/REFERENCE.md", "AGENTS.md"})
        self.assertFalse(wildcard)
        allowed2, wildcard2 = dac.parse_allow_trailers("Allow-Docs-Rewrite: *\n")
        self.assertTrue(wildcard2)
        self.assertEqual(allowed2, set())


if __name__ == "__main__":
    unittest.main()
