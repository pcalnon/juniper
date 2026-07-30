"""Tests for util/sequence_safety/docs_additions_check.py -- the docs deletion screen.

Hermetic: every case builds a throwaway git repo under a tempdir (``git -C``, never
``cd``) with a BASE and a HEAD commit, then drives the CLI as a subprocess and asserts
the finding reasons + exit code. Mirrors ``tests/test_worktree_cleanup.py``. No custom
subprocess env is needed (the fixtures pin git identity + ``commit.gpgsign`` locally and
the module only reads git), so the RedactedEnv house rule -- which applies to raw
``os.environ`` mappings -- has nothing to wrap here.

Coverage: additions-only clean pass, heading-deletion FAIL, the >=N consecutive-deletion
FAIL, small-deletion / small-swap WARN, heading-retitle WARN (delete + add a heading),
scope (AGENTS.md + notes/ in, a non-.md file out), the ``Allow-Docs-Rewrite`` trailer
escape (enumerated + wildcard), the tunable ``--min-run`` threshold, and exit codes
0/1/2.

util/ is not a package; the module is importlib-loaded for direct helper unit tests.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_TIMEOUT = 30


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_SCRIPT = _REPO_ROOT / "util" / "sequence_safety" / "docs_additions_check.py"


def _load():
    spec = importlib.util.spec_from_file_location("docs_additions_check", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so the module's @dataclass annotations (stringized by
    # ``from __future__ import annotations``) resolve via sys.modules[spec.name].
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_DAC = _load()


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
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


def _run_cli(root: Path, *extra: str, base: str = "HEAD~1", head: str = "HEAD") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--base", base, "--head", head, "--repo-root", str(root), *extra],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT,
    )


def _report(cp: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(cp.stdout)


def _reasons(report: dict) -> dict:
    return {f["path"]: f for f in report["findings"]}


_SECTIONED = "# Title\n\n## Section One\n\nbody a\nbody b\n\n## Section Two\n\nkeep me\n"


class DocsDeletionBehaviourTest(unittest.TestCase):
    def test_additions_only_is_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n\n## New Section\n\nmore\n")
            _commit(root, "add a section")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertEqual(_report(cp)["stats"]["fail_count"], 0)

    def test_heading_deletion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "drop Section One")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 1, msg=cp.stderr)
            f = _reasons(_report(cp))["docs/REFERENCE.md"]
            self.assertEqual((f["reason"], f["severity"]), ("heading-deletion", "FAIL"))

    def test_long_deletion_run_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n\nl1\nl2\nl3\nl4\nl5\nl6\n\noutro\n")
            _commit(root, "base")
            # Remove 6 consecutive body lines, no heading, no additions -> deletion-run.
            _write(root, "docs/REFERENCE.md", "# Title\n\nintro\n\noutro\n")
            _commit(root, "gut the body block")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 1, msg=cp.stderr)
            f = _reasons(_report(cp))["docs/REFERENCE.md"]
            self.assertEqual((f["reason"], f["severity"]), ("deletion-run", "FAIL"))

    def test_small_deletion_is_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nkeep\nl1\nl2\ntail\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\nkeep\ntail\n")
            _commit(root, "drop two lines")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            f = _reasons(_report(cp))["docs/REFERENCE.md"]
            self.assertEqual((f["reason"], f["severity"]), ("small-deletion", "WARN"))

    def test_in_place_swap_is_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nold line one\nold line two\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\nnew line one\nnew line two\n")
            _commit(root, "swap two lines")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertEqual(_reasons(_report(cp))["docs/REFERENCE.md"]["severity"], "WARN")

    def test_heading_retitle_is_warn_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Old Name\n\nbody\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## New Name\n\nbody\n")
            _commit(root, "rename a section heading")
            cp = _run_cli(root, "--json")
            # A heading deleted AND a heading added in the same hunk is a retitle -> WARN.
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertEqual(_reasons(_report(cp))["docs/REFERENCE.md"]["severity"], "WARN")

    def test_agents_md_and_notes_are_in_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "AGENTS.md", "# Agents\n\n## Kept\n\nx\n\n## Doomed\n\ny\n")
            _write(root, "notes/JUNIPER_2026-07-28_JUNIPER-ML_DEMO.md", "# Note\n\n## Runbook\n\nsteps\n")
            _commit(root, "base")
            _write(root, "AGENTS.md", "# Agents\n\n## Kept\n\nx\n")
            _write(root, "notes/JUNIPER_2026-07-28_JUNIPER-ML_DEMO.md", "# Note\n\nsteps\n")
            _commit(root, "drop headings in both")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 1, msg=cp.stderr)
            paths = _reasons(_report(cp))
            self.assertEqual(paths["AGENTS.md"]["reason"], "heading-deletion")
            self.assertEqual(paths["notes/JUNIPER_2026-07-28_JUNIPER-ML_DEMO.md"]["reason"], "heading-deletion")

    def test_non_markdown_file_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/tool.py", "# many\n# comment\n# lines\n# here\n# to\n# delete\nx = 1\n")
            _commit(root, "base")
            _write(root, "util/tool.py", "x = 1\n")
            _commit(root, "trim a py file")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertEqual(_report(cp)["stats"]["files_screened"], 0)


class DocsDeletionThresholdAndEscapeTest(unittest.TestCase):
    def test_min_run_threshold_is_tunable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n\nkeep\nd1\nd2\nd3\ntail\n")
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\nkeep\ntail\n")
            _commit(root, "drop three lines")
            default = _run_cli(root, "--json")  # 3 deletions < default 5 -> WARN
            self.assertEqual(default.returncode, 0, msg=default.stderr)
            self.assertEqual(_reasons(_report(default))["docs/REFERENCE.md"]["severity"], "WARN")
            tightened = _run_cli(root, "--min-run", "3", "--json")  # now 3 >= 3 -> FAIL
            self.assertEqual(tightened.returncode, 1, msg=tightened.stderr)
            self.assertEqual(_reasons(_report(tightened))["docs/REFERENCE.md"]["reason"], "deletion-run")

    def test_trailer_waives_enumerated_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "rewrite reference\n\nAllow-Docs-Rewrite: docs/REFERENCE.md")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertEqual(_reasons(_report(cp))["docs/REFERENCE.md"]["severity"], "WAIVED")

    def test_wildcard_trailer_waives_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", _SECTIONED)
            _commit(root, "base")
            _write(root, "docs/REFERENCE.md", "# Title\n\n## Section Two\n\nkeep me\n")
            _commit(root, "bulk docs rewrite\n\nAllow-Docs-Rewrite: *")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            report = _report(cp)
            self.assertTrue(report["stats"]["wildcard_waiver"])
            self.assertEqual(_reasons(report)["docs/REFERENCE.md"]["severity"], "WAIVED")


class DocsDeletionCliContractTest(unittest.TestCase):
    def test_missing_base_is_usage_error(self) -> None:
        cp = subprocess.run([sys.executable, str(_SCRIPT), "--head", "HEAD"], capture_output=True, text=True, timeout=_TIMEOUT)
        self.assertEqual(cp.returncode, 2)

    def test_unresolvable_ref_is_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n")
            _commit(root, "base")
            cp = _run_cli(root, base="nope", head="HEAD")
            self.assertEqual(cp.returncode, 2)
            self.assertIn("could not resolve ref", cp.stderr)

    def test_bad_min_run_is_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "docs/REFERENCE.md", "# Title\n")
            _commit(root, "base")
            cp = _run_cli(root, "--min-run", "0")
            self.assertEqual(cp.returncode, 2)


class DocsDeletionHelperUnitTest(unittest.TestCase):
    def test_in_docs_scope(self) -> None:
        self.assertTrue(_DAC.in_docs_scope("AGENTS.md"))
        self.assertTrue(_DAC.in_docs_scope("CLAUDE.md"))
        self.assertTrue(_DAC.in_docs_scope("docs/REFERENCE.md"))
        self.assertTrue(_DAC.in_docs_scope("notes/JUNIPER_x.md"))
        self.assertFalse(_DAC.in_docs_scope("README.md"))
        self.assertFalse(_DAC.in_docs_scope("util/x.py"))
        self.assertFalse(_DAC.in_docs_scope("docs/diagram.png"))

    def test_parse_hunks_splits_and_counts(self) -> None:
        diff = "diff --git a/x.md b/x.md\n--- a/x.md\n+++ b/x.md\n@@ -1,2 +1,0 @@\n-gone one\n-gone two\n@@ -5,0 +4,1 @@\n+added\n"
        hunks = _DAC.parse_hunks(diff)
        self.assertEqual(len(hunks), 2)
        self.assertEqual(hunks[0].deleted, ["gone one", "gone two"])
        self.assertEqual(hunks[0].added, [])
        self.assertEqual(hunks[1].added, ["added"])

    def test_classify_heading_and_run(self) -> None:
        heading = _DAC.classify_file("docs/x.md", [_DAC.Hunk(deleted=["## Section"], added=[])], 5)
        self.assertEqual((heading[0].reason, heading[0].severity), ("heading-deletion", "FAIL"))
        run = _DAC.classify_file("docs/x.md", [_DAC.Hunk(deleted=["a", "b", "c", "d", "e"], added=[])], 5)
        self.assertEqual((run[0].reason, run[0].severity), ("deletion-run", "FAIL"))
        swap = _DAC.classify_file("docs/x.md", [_DAC.Hunk(deleted=["a", "b"], added=["c", "d"])], 5)
        self.assertEqual((swap[0].reason, swap[0].severity), ("small-deletion", "WARN"))

    def test_parse_allow_trailers(self) -> None:
        allowed, wildcard = _DAC.parse_allow_trailers("fix\n\nAllow-Docs-Rewrite: docs/REFERENCE.md, AGENTS.md\n")
        self.assertEqual(allowed, {"docs/REFERENCE.md", "AGENTS.md"})
        self.assertFalse(wildcard)
        allowed2, wildcard2 = _DAC.parse_allow_trailers("Allow-Docs-Rewrite: *\n")
        self.assertTrue(wildcard2)
        self.assertEqual(allowed2, set())


if __name__ == "__main__":
    unittest.main()
