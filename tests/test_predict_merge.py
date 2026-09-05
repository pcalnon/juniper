"""Hermetic tests for ``util/fleet_triage/predict_merge.py`` (Stage-0 supervisor script layer).

Drives the deterministic predicted-merge engine over synthetic bare-origin + branch
fixture repos (the ``tests/test_worktree_cleanup.py`` fixture idiom) -- no network, no
``gh``, no ``pre-commit`` (the fast-gate battery is injected or env-skipped). Covers:

* the four verdict classes -- MERGE-CLEAN, NEEDS-UPDATE-BRANCH, DAMAGED-FIX-FIRST
  (symbol-loss AND docs-deletion AND injected gate-fail), and CONFLICT;
* the #895 ``_ast_symbol_screen`` fail-soft arms (non-screenable short-circuit, missing /
  exit-2 / empty / non-JSON checker -> ``skip``, WARN-only not mapped, ``skip`` ≠ DAMAGED);
* the TRUE-delta-vs-stale-file-list discrimination (delta from the merge RESULT, so a
  main-owned file the branch is merely stale on is excluded -- the #729 class);
* the docs deletion-magnitude screen delegation (same #895 subprocess pattern): a deleted
  heading / >=N-run FAIL -> DAMAGED, a small in-place swap WARN -> MERGE-CLEAN (the
  August-storm false-DAMAGED class), the ``Allow-Docs-Rewrite`` trailer waiver, and the
  matching missing / exit-2 / empty / non-JSON -> ``skip`` fail-soft arms;
* the fast-gate battery skip when the TRUE delta has no ``.py`` files;
* the ``--batch`` cluster map + suggested merge order (heal PRs first -- a fix|heal|hotfix
  head branch or a fix(/fix:/heal title -- then ascending same-file-cluster membership),
  including a fake-``gh`` end-to-end batch;
* ``triage_pr`` / ``_gh_json`` / CLI ``--pr`` hard-fail on gh nonzero / non-JSON;
* ``triage_batch`` soft-ERROR continue (one unresolvable ``headRefName`` must not abort
  the rest of the open-PR set) + ``suggest_order`` empty-``true_delta`` ERROR contention;
* deleted-``.py`` paths stay in ``true_delta`` but are filtered out of the gate battery;
* ``JUNIPER_FLEET_SKIP_PRECOMMIT`` forces skip_all when the default gate runner would run;
* the detached-clone-never-mutates-source contract (a ``git clone`` under the system
  tempdir, never a ``git worktree`` of -- and never a write to -- the invoking checkout);
* CLI exit codes (0 always-report / 2 usage / 2 non-git ``--repo-root`` / ``--pr``).

``util/`` is not pre-commit-lint-gated (flake8/black scope to ``scripts``+``tests``), so
this unittest -- wired into ``ci.yml`` + AGENTS.md's run-all -- is the gate. Imported via
the ``sys.path.insert`` idiom; ``RedactedEnv`` builds every subprocess env mapping.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from fleet_triage import predict_merge as pm  # noqa: E402  (path-invoked util import)

SCRIPT_PATH = REPO_ROOT / "util" / "fleet_triage" / "predict_merge.py"
GIT_TIMEOUT = 60


# --------------------------------------------------------------------------- #
# fixture helpers (git repos with main + origin/main + local/remote branches)
# --------------------------------------------------------------------------- #


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    cp = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
    )
    if check and cp.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed ({cp.returncode}): {cp.stderr.strip()}")
    return cp


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "tests@example.invalid")
    _git(path, "config", "user.name", "Fleet Tests")
    _git(path, "config", "commit.gpgsign", "false")
    _git(path, "config", "tag.gpgsign", "false")


def _write(repo: Path, rel: str, content: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _commit(repo: Path, msg: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _publish_main(repo: Path) -> None:
    """Point ``origin/main`` at the current ``main`` tip (the predicted-merge base)."""
    _git(repo, "update-ref", "refs/remotes/origin/main", "refs/heads/main")


def _publish_branch(repo: Path, name: str) -> None:
    """Point ``origin/<name>`` at the local branch tip (so ``origin/<name>`` resolves for the gh path)."""
    _git(repo, "update-ref", f"refs/remotes/origin/{name}", f"refs/heads/{name}")


def _for_each_ref(repo: Path) -> str:
    return _git(repo, "for-each-ref", "--format=%(objectname) %(refname)").stdout


def _worktree_count(repo: Path) -> int:
    out = _git(repo, "worktree", "list", "--porcelain").stdout
    return sum(1 for ln in out.splitlines() if ln.startswith("worktree "))


class _RepoCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="fleet-triage-test-"))
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)], check=False))
        self.repo = self.tmp / "repo"
        _init_repo(self.repo)


# --------------------------------------------------------------------------- #
# the four verdict classes + true-delta discrimination
# --------------------------------------------------------------------------- #


class VerdictTest(_RepoCase):
    def test_merge_clean(self):
        _write(self.repo, "fileA.txt", "A0\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "clean")
        _write(self.repo, "fileD.txt", "D\n")
        _commit(self.repo, "add D on branch")

        v = pm.simulate_merge(self.repo, "clean", run_gates=False)
        self.assertEqual(v["verdict"], "MERGE-CLEAN")
        self.assertTrue(v["mergeable"])
        self.assertFalse(v["behind_main"])
        self.assertEqual(v["true_delta"], ["fileD.txt"])
        self.assertEqual(v["gates"]["merge"], "clean")

    def test_needs_update_branch_and_true_delta_discrimination(self):
        # main advances a file the branch never touches -> branch behind; the stale
        # main-owned file must NOT appear in the RESULT-computed true delta (#729 class).
        _write(self.repo, "fileA.txt", "A0\n")
        _write(self.repo, "fileB.txt", "B0\n")
        _commit(self.repo, "c0")
        _git(self.repo, "branch", "feat")  # feat forks at c0
        _git(self.repo, "checkout", "-q", "feat")
        _write(self.repo, "fileA.txt", "A1\n")  # branch edits A
        _write(self.repo, "fileC.txt", "C1\n")  # branch adds C
        _commit(self.repo, "feat work")
        _git(self.repo, "checkout", "-q", "main")
        _write(self.repo, "fileB.txt", "B1\n")  # main edits B (branch is now stale on B)
        _commit(self.repo, "main work")
        _publish_main(self.repo)

        v = pm.simulate_merge(self.repo, "feat", run_gates=False)
        self.assertEqual(v["verdict"], "NEEDS-UPDATE-BRANCH")
        self.assertTrue(v["mergeable"])
        self.assertTrue(v["behind_main"])
        # TRUE delta = what the MERGE changes vs current main: A (edited) + C (added).
        self.assertEqual(v["true_delta"], ["fileA.txt", "fileC.txt"])
        # discrimination: fileB is main-owned churn, not a change this PR lands.
        self.assertNotIn("fileB.txt", v["true_delta"])

    def test_conflict(self):
        _write(self.repo, "fileX.txt", "line1\nline2\n")
        _commit(self.repo, "c0")
        _git(self.repo, "branch", "conf")
        _git(self.repo, "checkout", "-q", "conf")
        _write(self.repo, "fileX.txt", "line1\nBRANCH\n")
        _commit(self.repo, "branch edit")
        _git(self.repo, "checkout", "-q", "main")
        _write(self.repo, "fileX.txt", "line1\nMAIN\n")
        _commit(self.repo, "main edit")
        _publish_main(self.repo)

        v = pm.simulate_merge(self.repo, "conf", run_gates=False)
        self.assertEqual(v["verdict"], "CONFLICT")
        self.assertFalse(v["mergeable"])
        self.assertEqual(v["gates"]["merge"], "conflict")
        self.assertIn("fileX.txt", v["conflicted_files"])

    def test_damaged_symbol_loss(self):
        # An in-scope util/*.py loses a symbol in the fused result: flake8/mypy still pass,
        # but the AST screen flags it -> DAMAGED-FIX-FIRST (#738/#755 class).
        _write(self.repo, "util/mod.py", "def foo():\n    return 1\n\n\ndef bar():\n    return 2\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "dmg")
        _write(self.repo, "util/mod.py", "def bar():\n    return 2\n")  # foo deleted
        _commit(self.repo, "drop foo")

        v = pm.simulate_merge(self.repo, "dmg", run_gates=False)
        self.assertEqual(v["verdict"], "DAMAGED-FIX-FIRST")
        self.assertTrue(v["mergeable"])
        self.assertIn("util/mod.py", v["true_delta"])
        lost = v["gates"]["ast_symbol_screen"]["lost"]
        self.assertEqual(v["gates"]["ast_symbol_screen"]["status"], "fail")
        self.assertTrue(any(item["symbol"] == "func:foo" for item in lost), lost)

    def test_symbol_loss_waived_by_allow_trailer(self):
        # Same deletion as test_damaged_symbol_loss, but the branch commit carries an
        # ``Allow-Symbol-Loss`` trailer -> the sequence-safety screen WAIVES it, so the
        # per-PR verdict is MERGE-CLEAN. predict_merge now delegates to the SAME
        # juniper-symbol-loss-check console script (juniper-ci-tools) as the push:main
        # ``main-verify`` gate, so an author-declared intentional removal is honored identically.
        _write(self.repo, "util/mod.py", "def foo():\n    return 1\n\n\ndef bar():\n    return 2\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "waived")
        _write(self.repo, "util/mod.py", "def bar():\n    return 2\n")  # foo intentionally removed
        _commit(self.repo, "drop foo (intentional)\n\nAllow-Symbol-Loss: func:foo")

        v = pm.simulate_merge(self.repo, "waived", run_gates=False)
        self.assertEqual(v["gates"]["ast_symbol_screen"]["status"], "pass")
        self.assertEqual(v["gates"]["ast_symbol_screen"]["lost"], [])
        self.assertEqual(v["verdict"], "MERGE-CLEAN")

    def test_damaged_docs_deletion(self):
        # A deleted Markdown heading is a module FAIL (net section removal, #801/#803) ->
        # DAMAGED-FIX-FIRST. predict_merge now delegates to the SAME
        # juniper-docs-additions-check console script (juniper-ci-tools) thresholds as the
        # push:main main-verify gate (heading-deletion / >=N-run FAIL; a small swap is WARN).
        _write(self.repo, "notes.md", "# Title\n\n## Section One\n\nbody\n\n## Section Two\n\nkeep\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "docdel")
        _write(self.repo, "notes.md", "# Title\n\n## Section Two\n\nkeep\n")  # Section One heading dropped
        _commit(self.repo, "drop Section One")

        v = pm.simulate_merge(self.repo, "docdel", run_gates=False)
        self.assertEqual(v["verdict"], "DAMAGED-FIX-FIRST")
        screen = v["gates"]["docs_additions_only"]
        self.assertEqual(screen["status"], "fail")
        dels = screen["deletions"]
        self.assertTrue(dels and dels[0]["file"] == "notes.md", dels)
        self.assertEqual(dels[0]["reason"], "heading-deletion")
        self.assertEqual(screen.get("waived"), [])

    def test_small_docs_deletion_is_not_damaged(self):
        # The storm-validated fix: a small in-place docs swap (a couple of removed lines
        # bracketed by additions, no heading, below the >=5-run threshold) is a module WARN,
        # NOT a FAIL -- so it is MERGE-CLEAN, not DAMAGED-FIX-FIRST. The old inline
        # any-removed-line rule painted exactly this class DAMAGED (12 ml + 14 cascor false
        # verdicts hand-adjudicated across the two August storm triages).
        _write(self.repo, "notes.md", "# Title\n\nold line one\nold line two\ntail\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "docswap")
        _write(self.repo, "notes.md", "# Title\n\nnew line one\nnew line two\ntail\n")  # in-place swap
        _commit(self.repo, "reword two docs lines")

        v = pm.simulate_merge(self.repo, "docswap", run_gates=False)
        screen = v["gates"]["docs_additions_only"]
        self.assertEqual(screen["status"], "pass", screen)
        self.assertEqual(screen["deletions"], [])
        self.assertEqual(v["verdict"], "MERGE-CLEAN")

    def test_docs_deletion_waived_by_allow_trailer(self):
        # A heading deletion (a real module FAIL) that the branch commit declares with
        # ``Allow-Docs-Rewrite: notes.md`` -- the same escape hatch the
        # juniper-docs-additions-check console script honors. Without trailer parity the
        # fleet screen would forever DAMAGED an intentional rewrite that main-verify
        # would WAIVE (the symbol screen already has this parity via #895).
        _write(self.repo, "notes.md", "# Title\n\n## Section One\n\nbody\n\n## Section Two\n\nkeep\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "docwaive")
        _write(self.repo, "notes.md", "# Title\n\n## Section Two\n\nkeep\n")
        _commit(self.repo, "rewrite notes (intentional)\n\nAllow-Docs-Rewrite: notes.md")

        v = pm.simulate_merge(self.repo, "docwaive", run_gates=False)
        screen = v["gates"]["docs_additions_only"]
        self.assertEqual(screen["status"], "pass")
        self.assertEqual(screen["deletions"], [])
        self.assertTrue(
            screen.get("waived") and screen["waived"][0]["file"] == "notes.md",
            screen.get("waived"),
        )
        self.assertEqual(v["verdict"], "MERGE-CLEAN")

    def test_docs_deletion_wildcard_trailer_waives_all(self):
        _write(self.repo, "notes/a.md", "# A\n\n## Sec A\n\nbody\n")
        _write(self.repo, "docs/b.md", "# B\n\n## Sec B\n\nbody\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "wild")
        _write(self.repo, "notes/a.md", "# A\n")  # drop the ## Sec A heading (real FAIL)
        _write(self.repo, "docs/b.md", "# B\n")  # drop the ## Sec B heading (real FAIL)
        _commit(self.repo, "trim both docs\n\nAllow-Docs-Rewrite: *")

        v = pm.simulate_merge(self.repo, "wild", run_gates=False)
        screen = v["gates"]["docs_additions_only"]
        self.assertEqual(screen["status"], "pass")
        self.assertEqual(screen["deletions"], [])
        waived_files = {item["file"] for item in screen.get("waived", [])}
        self.assertEqual(waived_files, {"notes/a.md", "docs/b.md"})
        self.assertEqual(v["verdict"], "MERGE-CLEAN")

    def test_docs_deletion_trailer_wrong_path_still_damaged(self):
        # A trailer for a DIFFERENT path must NOT silence an unwaived heading deletion.
        _write(self.repo, "notes.md", "# Title\n\n## Section One\n\nbody\n\n## Section Two\n\nkeep\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "wrongpath")
        _write(self.repo, "notes.md", "# Title\n\n## Section Two\n\nkeep\n")
        _commit(self.repo, "drop Section One\n\nAllow-Docs-Rewrite: other.md")

        v = pm.simulate_merge(self.repo, "wrongpath", run_gates=False)
        self.assertEqual(v["verdict"], "DAMAGED-FIX-FIRST")
        self.assertEqual(v["gates"]["docs_additions_only"]["status"], "fail")
        self.assertEqual(v["gates"]["docs_additions_only"].get("waived"), [])

    def test_docs_additions_only_markdown_is_merge_clean(self):
        # Pure docs additions must NOT trip docs_additions_only (no `-` content lines).
        # Regression class: counting unified-diff `---`/`+++` headers as removals would
        # falsely DAMAGED every new `.md` file and stall the fleet merge order.
        _write(self.repo, "notes/keep.md", "# keep\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "docadd")
        _write(self.repo, "notes/new.md", "# new section\n\nbody\n")
        _commit(self.repo, "add notes/new.md")

        v = pm.simulate_merge(self.repo, "docadd", run_gates=False)
        self.assertEqual(v["gates"]["docs_additions_only"]["status"], "pass")
        self.assertEqual(v["gates"]["docs_additions_only"]["deletions"], [])
        self.assertEqual(v["verdict"], "MERGE-CLEAN")

    def test_non_markdown_deletion_does_not_trip_docs_screen(self):
        # docs_additions_only is intentionally `.md`-scoped; a .txt deletion alone must
        # not produce DAMAGED-FIX-FIRST via that gate (symbol/gate battery own .py).
        _write(self.repo, "plain.txt", "a\nb\nc\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "txtdel")
        _write(self.repo, "plain.txt", "a\nc\n")  # drop b
        _commit(self.repo, "drop a txt line")

        v = pm.simulate_merge(self.repo, "txtdel", run_gates=False)
        self.assertEqual(v["gates"]["docs_additions_only"]["status"], "pass")
        self.assertEqual(v["gates"]["docs_additions_only"]["deletions"], [])
        self.assertEqual(v["verdict"], "MERGE-CLEAN")

    def test_gate_battery_skips_when_delta_has_no_py(self):
        # Docs-only TRUE delta must skip every pre-commit hook (never invoke the runner).
        # Without this, a mis-wired battery could fail-closed on empty `--files` or
        # invent flake8 damage for PRs that touch no Python.
        _write(self.repo, "notes/seed.md", "seed\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "mdonly")
        _write(self.repo, "notes/extra.md", "extra\n")
        _commit(self.repo, "add notes/extra.md")

        calls = []

        def tracking_runner(clone, hook, files):
            calls.append((hook, list(files)))
            return ("fail", "must not run")

        v = pm.simulate_merge(self.repo, "mdonly", gate_runner=tracking_runner)
        self.assertEqual(calls, [], "gate_runner must not run when the delta has no .py")
        for hook in pm.PRECOMMIT_HOOKS:
            self.assertEqual(v["gates"][hook]["status"], "skip")
            self.assertIn("no .py", v["gates"][hook]["detail"])
        self.assertEqual(v["verdict"], "MERGE-CLEAN")

    def test_damaged_injected_gate_failure(self):
        # A clean, additions-only .py PR (no symbol loss) with an injected failing gate.
        _write(self.repo, "util/keep.py", "x = 1\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "addpy")
        _write(self.repo, "util/new.py", "def baz():\n    return 3\n")
        _commit(self.repo, "add util/new.py")

        def failing_runner(clone, hook, files):
            return ("fail", "synthetic flake8 failure") if hook == "flake8" else ("pass", "")

        v = pm.simulate_merge(self.repo, "addpy", gate_runner=failing_runner)
        self.assertEqual(v["verdict"], "DAMAGED-FIX-FIRST")
        self.assertEqual(v["gates"]["flake8"]["status"], "fail")
        self.assertEqual(v["gates"]["black"]["status"], "pass")

    def test_deleted_py_not_passed_to_gate_battery(self):
        # A deleted ``.py`` stays in ``true_delta`` but must NOT be handed to
        # ``pre-commit --files`` (the path is gone on the merge HEAD). Filtering via
        # ``_blob(HEAD) is not None`` is the only guard against a false DAMAGED
        # from hooks that cannot open a deleted path.
        _write(self.repo, "util/keep.py", "x = 1\n")
        _write(self.repo, "util/doomed.py", "def doomed():\n    return 0\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "rmpy")
        _git(self.repo, "rm", "-q", "util/doomed.py")
        _write(self.repo, "notes/README.md", "docs only addition\n")
        _commit(self.repo, "delete doomed.py + docs")

        seen: list = []

        def recording_runner(clone, hook, files):
            seen.append((hook, list(files)))
            return ("pass", "")

        v = pm.simulate_merge(self.repo, "rmpy", gate_runner=recording_runner)
        self.assertIn("util/doomed.py", v["true_delta"])
        # Gate battery must skip entirely (no remaining .py in changed_existing) —
        # never invoke the runner with the deleted path. Symbol-loss DAMAGED from
        # the deleted def is honest (#908 screen); the regression class is a false
        # DAMAGED from pre-commit opening a path that no longer exists on HEAD.
        self.assertEqual(seen, [], f"gate_runner must not run when delta's only .py is deleted; got {seen}")
        for hook in pm.PRECOMMIT_HOOKS:
            self.assertEqual(v["gates"][hook]["status"], "skip")
            self.assertIn("no .py", v["gates"][hook]["detail"])
        self.assertEqual(v["gates"]["ast_symbol_screen"]["status"], "fail")
        self.assertEqual(v["verdict"], "DAMAGED-FIX-FIRST")

    def test_env_skip_precommit_disables_default_gate_runner(self):
        # ``JUNIPER_FLEET_SKIP_PRECOMMIT`` is the hermetic escape when ``gate_runner``
        # is unset. Ignoring it would invoke real pre-commit (hang/flake); always
        # skipping would silence live fleet gates.
        _write(self.repo, "util/keep.py", "x = 1\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "addpy")
        _write(self.repo, "util/new.py", "def baz():\n    return 3\n")
        _commit(self.repo, "add util/new.py")

        with mock.patch.dict(os.environ, {"JUNIPER_FLEET_SKIP_PRECOMMIT": "1"}):
            v = pm.simulate_merge(self.repo, "addpy", run_gates=True, gate_runner=None)
        for hook in pm.PRECOMMIT_HOOKS:
            self.assertEqual(v["gates"][hook]["status"], "skip", hook)
            self.assertIn("gates disabled", v["gates"][hook]["detail"])
        self.assertEqual(v["verdict"], "MERGE-CLEAN")


# --------------------------------------------------------------------------- #
# detached-clone-never-mutates-source
# --------------------------------------------------------------------------- #


class NoMutationTest(_RepoCase):
    def test_source_untouched_and_scratch_is_a_clone_not_a_worktree(self):
        _write(self.repo, "fileA.txt", "A0\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "clean")
        _write(self.repo, "fileD.txt", "D\n")
        _commit(self.repo, "add D")

        refs_before = _for_each_ref(self.repo)
        wt_before = _worktree_count(self.repo)
        scratch_parent = self.tmp / "scratch-parent"
        scratch_parent.mkdir()

        v = pm.simulate_merge(self.repo, "clean", run_gates=False, keep_scratch=True, scratch_parent=scratch_parent)
        self.assertEqual(v["verdict"], "MERGE-CLEAN")

        # source repo: refs and worktree registry are byte-for-byte unchanged.
        self.assertEqual(_for_each_ref(self.repo), refs_before)
        self.assertEqual(_worktree_count(self.repo), wt_before)
        self.assertEqual(_worktree_count(self.repo), 1, "predict_merge must NOT register a worktree on the source")

        # the scratch lived under the parent we passed (system tempdir), NOT under the repo,
        # and is a real clone (its .git is a directory), not a linked-worktree pointer file.
        clones = list(scratch_parent.glob("fleet-triage-*/clone"))
        self.assertEqual(len(clones), 1, f"expected one kept scratch clone under {scratch_parent}, got {clones}")
        clone = clones[0]
        self.assertFalse(str(clone).startswith(str(self.repo)), "scratch clone must not live inside the source repo")
        self.assertTrue((clone / ".git").is_dir(), "scratch must be a git clone (.git dir), not a worktree pointer")


# --------------------------------------------------------------------------- #
# batch cluster map + suggested merge order (pure) + fake-gh end-to-end
# --------------------------------------------------------------------------- #


class ClusterOrderTest(unittest.TestCase):
    def test_clusters_and_heal_first_least_colliding_order(self):
        verdicts = [
            # PR #1 is a heal via its fix/ HEAD branch (the new _is_heal rule: a
            # fix|heal|hotfix branch prefix, not an arbitrary "restore"/"heal" substring).
            {"pr": 1, "title": "restore deleted block", "branch": "fix/restore-x", "true_delta": ["A.md"]},
            {"pr": 2, "title": "feat two", "branch": "cursor/two", "true_delta": ["HOT.py"]},
            {"pr": 3, "title": "feat three", "branch": "cursor/three", "true_delta": ["HOT.py"]},
            {"pr": 4, "title": "feat four", "branch": "cursor/four", "true_delta": ["HOT.py"]},
            {"pr": 5, "title": "feat five", "branch": "cursor/five", "true_delta": ["SOLO.py"]},
        ]
        clusters = pm.build_clusters(verdicts)
        self.assertEqual(clusters["HOT.py"], [2, 3, 4])
        self.assertEqual(clusters["SOLO.py"], [5])
        self.assertEqual(clusters["A.md"], [1])

        order = pm.suggest_order(verdicts, clusters)
        # heal PR #1 first; then least-colliding (#5 SOLO, contention 1) before the HOT cluster.
        self.assertEqual(order[0], 1)
        self.assertEqual(order, [1, 5, 2, 3, 4])

    def test_no_heal_pr_still_orders_by_contention(self):
        verdicts = [
            {"pr": 10, "title": "big", "branch": "cursor/big", "true_delta": ["X.py"]},
            {"pr": 11, "title": "big2", "branch": "cursor/big2", "true_delta": ["X.py"]},
            {"pr": 12, "title": "small", "branch": "cursor/small", "true_delta": ["Y.py"]},
        ]
        clusters = pm.build_clusters(verdicts)
        order = pm.suggest_order(verdicts, clusters)
        self.assertEqual(order[0], 12, "the singleton-cluster PR should lead when no heal PR exists")

    def test_suggest_order_error_empty_delta_has_zero_contention(self):
        # soft-ERROR rows carry ``true_delta=[]`` (predict_merge.py triage_batch catch).
        # ``suggest_order`` contention is ``max(len(cluster[path]))`` over true_delta, so an
        # empty delta sorts as least-colliding (contention 0) — after heals, ahead of busy
        # feat clusters. Pin that so a future demotion/promotion of ERROR cannot silently
        # reorder the supervisor merge plan.
        verdicts = [
            {"pr": 1, "title": "heal canopy", "branch": "cursor/heal-x", "true_delta": ["A.md"]},
            {"pr": 2, "title": "gone branch", "branch": "cursor/gone", "true_delta": [], "verdict": "ERROR"},
            {"pr": 3, "title": "feat hot", "branch": "cursor/hot", "true_delta": ["HOT.py"]},
            {"pr": 4, "title": "feat hot2", "branch": "cursor/hot2", "true_delta": ["HOT.py"]},
        ]
        clusters = pm.build_clusters(verdicts)
        self.assertNotIn("", clusters)  # empty paths must not invent a cluster key
        order = pm.suggest_order(verdicts, clusters)
        self.assertEqual(order[0], 1, "heal still leads (title ^heal)")
        self.assertEqual(order[1], 2, "ERROR empty-delta (contention 0) before HOT cluster")
        self.assertEqual(order[2:], [3, 4], order)

    def test_is_heal_requires_branch_or_title_prefix(self):
        # Tightened rule (#910 wave-1 mis-sort fix): heal-first fires ONLY on a
        # fix|heal|hotfix HEAD-branch prefix or a fix(/fix:/heal TITLE prefix -- never a
        # bare substring anywhere in the title/branch.
        # promotes:
        self.assertTrue(pm._is_heal({"title": "heal canopy WS", "branch": "cursor/y"}))  # title ^heal
        self.assertTrue(pm._is_heal({"title": "fix: restore gate", "branch": "cursor/x"}))  # title ^fix:
        self.assertTrue(pm._is_heal({"title": "fix(triage): sort", "branch": "cursor/z"}))  # title ^fix(
        self.assertTrue(pm._is_heal({"title": "feat", "branch": "fix/broken-gate"}))  # branch ^fix/
        self.assertTrue(pm._is_heal({"title": "feat", "branch": "origin/hotfix/urgent"}))  # origin-qualified ^hotfix/
        # does NOT promote (the arbitrary-substring false positives the old rule hit):
        self.assertFalse(pm._is_heal({"title": "repair broken gate", "branch": "cursor/x"}))  # "repair" dropped
        self.assertFalse(pm._is_heal({"title": "feat", "branch": "cursor/fix-first-docs"}))  # not a fix/ path segment
        self.assertFalse(pm._is_heal({"title": "test(fleet): + heal tokens", "branch": "cursor/t"}))  # "heal" mid-title

        self.assertFalse(pm._is_heal({"title": "feat docs", "branch": "cursor/docs-sync"}))

        verdicts = [
            {"pr": 20, "title": "feat hot", "branch": "cursor/hot", "true_delta": ["HOT.py"]},
            {"pr": 21, "title": "fix: repair symbol screen", "branch": "cursor/repair-x", "true_delta": ["A.md"]},
            {"pr": 22, "title": "feat solo", "branch": "cursor/solo", "true_delta": ["SOLO.py"]},
            {"pr": 23, "title": "nudge", "branch": "hotfix/y", "true_delta": ["B.md"]},
        ]
        clusters = pm.build_clusters(verdicts)
        order = pm.suggest_order(verdicts, clusters)
        # Both heal PRs lead (#21 fix: title + #23 hotfix/ branch); remaining ties break
        # by PR number via _pr_key (20 before 22), not by title.
        self.assertEqual(order[:2], [21, 23], order)
        self.assertEqual(order[2:], [20, 22], order)


# --------------------------------------------------------------------------- #
# docs deletion-magnitude screen delegation — fail-soft arms + verdict mapping
# --------------------------------------------------------------------------- #


class DocsAdditionsScreenDegradeTest(unittest.TestCase):
    """Pin the fail-soft contract of the docs deletion-magnitude screen delegation.

    Mirrors ``AstSymbolScreenDegradeTest``: predict_merge shells out to the
    ``juniper-docs-additions-check`` console script (juniper-ci-tools; the same subprocess
    pattern), so a missing (package not installed) / broken / non-JSON checker must ``skip``
    (never crash triage), ``skip`` must
    never become ``DAMAGED-FIX-FIRST`` (only ``status == "fail"`` drives that verdict), and
    a WARN-only (small in-place swap) finding must not be mapped into ``deletions``. FAIL
    findings map into ``deletions`` and WAIVED findings into ``waived``.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="fleet-docs-degrade-"))
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)], check=False))

    def _screen_with_run(self, cp: subprocess.CompletedProcess, changed=None):
        # The console script juniper-docs-additions-check is "available" -> shutil.which returns a
        # truthy path; _run is stubbed to return the canned CompletedProcess (no real subprocess).
        # Console-script analogue of the pre-W3 "_DOCS_ADDITIONS_CHECK on-disk path + _run stub".
        with mock.patch.object(pm.shutil, "which", return_value="/usr/bin/juniper-docs-additions-check"):
            with mock.patch.object(pm, "_run", return_value=cp) as run_mock:
                out = pm._docs_additions_only_screen(Path("/clone"), "base", "head", changed or ["notes.md"])
        return out, run_mock

    def test_non_screenable_delta_short_circuits_without_subprocess(self):
        with mock.patch.object(pm, "_run") as run_mock:
            out = pm._docs_additions_only_screen(Path("/unused"), "base", "head", ["util/mod.py", "README.txt"])
        self.assertEqual(out, {"status": "pass", "deletions": [], "waived": []})
        run_mock.assert_not_called()

    def test_missing_checker_degrades_to_skip(self):
        # juniper-ci-tools not installed -> the console script is not on PATH -> shutil.which
        # returns None -> skip, and the subprocess is never spawned.
        with mock.patch.object(pm.shutil, "which", return_value=None):
            with mock.patch.object(pm, "_run") as run_mock:
                out = pm._docs_additions_only_screen(Path("/unused"), "base", "head", ["notes.md"])
        self.assertEqual(out["status"], "skip")
        self.assertEqual(out["deletions"], [])
        self.assertIn("unavailable", out["detail"])
        run_mock.assert_not_called()

    def test_checker_exit_2_degrades_to_skip(self):
        cp = subprocess.CompletedProcess(args=["docs_additions_check"], returncode=2, stdout="", stderr="fatal: bad revision 'base'\n")
        out, run_mock = self._screen_with_run(cp)
        self.assertEqual(out["status"], "skip")
        self.assertEqual(out["deletions"], [])
        self.assertIn("bad revision", out["detail"])
        run_mock.assert_called_once()

    def test_empty_stdout_degrades_to_skip(self):
        cp = subprocess.CompletedProcess(args=[], returncode=0, stdout="   \n", stderr="")
        out, _ = self._screen_with_run(cp)
        self.assertEqual(out["status"], "skip")
        self.assertEqual(out["deletions"], [])
        self.assertIn("docs-deletion screen error", out["detail"])

    def test_non_json_stdout_degrades_to_skip(self):
        cp = subprocess.CompletedProcess(args=[], returncode=0, stdout="not-json{\n", stderr="")
        out, _ = self._screen_with_run(cp)
        self.assertEqual(out["status"], "skip")
        self.assertEqual(out["deletions"], [])
        self.assertEqual(out["detail"], "docs-deletion screen returned non-JSON")

    def test_warn_only_finding_is_not_mapped_into_deletions(self):
        report = {"findings": [{"path": "notes.md", "reason": "small-deletion", "severity": "WARN", "detail": {"deleted": 1, "added": 1}}]}
        cp = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(report), stderr="")
        out, _ = self._screen_with_run(cp)
        self.assertEqual(out["status"], "pass")
        self.assertEqual(out["deletions"], [])
        self.assertEqual(out["waived"], [])

    def test_fail_and_waived_findings_map_shape_and_status(self):
        report = {
            "findings": [
                {"path": "notes.md", "reason": "heading-deletion", "severity": "FAIL", "detail": {"deleted": 4, "added": 0}},
                {"path": "docs/x.md", "reason": "deletion-run", "severity": "WAIVED", "detail": {"deleted": 7}},
                {"path": "docs/y.md", "reason": "small-deletion", "severity": "WARN", "detail": {"deleted": 1}},
            ]
        }
        cp = subprocess.CompletedProcess(args=[], returncode=1, stdout=json.dumps(report), stderr="")
        out, _ = self._screen_with_run(cp)
        self.assertEqual(out["status"], "fail")
        self.assertEqual(out["deletions"], [{"file": "notes.md", "reason": "heading-deletion", "removed_lines": 4}])
        self.assertEqual(
            out["waived"],
            [{"file": "docs/x.md", "reason": "deletion-run", "removed_lines": 7, "waived_by": "Allow-Docs-Rewrite trailer"}],
        )

    def test_skip_status_does_not_damage_merge_verdict(self):
        # End-to-end: a .md-touching PR whose docs checker is unavailable must stay
        # MERGE-CLEAN (skip ≠ fail). Regression class: treating skip as damaged would
        # block every fleet triage batch when juniper-ci-tools is temporarily absent.
        repo = self.tmp / "repo"
        _init_repo(repo)
        _write(repo, "notes/seed.md", "# seed\n")
        _commit(repo, "c0")
        _publish_main(repo)
        _git(repo, "checkout", "-q", "-b", "adddoc")
        _write(repo, "notes/new.md", "# new\n\nbody\n")
        _commit(repo, "add notes/new.md")

        # shutil.which -> None models juniper-ci-tools not installed; shutil.rmtree (used by
        # simulate_merge's clone cleanup) is a different attribute and stays live.
        with mock.patch.object(pm.shutil, "which", return_value=None):
            v = pm.simulate_merge(repo, "adddoc", run_gates=False)
        self.assertEqual(v["gates"]["docs_additions_only"]["status"], "skip")
        self.assertEqual(v["verdict"], "MERGE-CLEAN")


def _install_fake_gh(bin_dir: Path, payload_dir: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    gh = bin_dir / "gh"
    # Optional GH_FAKE_{LIST,VIEW}_{RC,BODY} overrides let individual arms force
    # nonzero exit / non-JSON stdout without rewriting the stub.
    gh.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ "${1:-}" == "pr" && "${2:-}" == "list" ]]; then\n'
        '  if [[ -n "${GH_FAKE_LIST_RC:-}" ]]; then echo "${GH_FAKE_LIST_BODY:-gh list fail}" >&2; exit "$GH_FAKE_LIST_RC"; fi\n'
        '  if [[ -n "${GH_FAKE_LIST_BODY:-}" ]]; then printf "%s" "$GH_FAKE_LIST_BODY"; exit 0; fi\n'
        '  cat "$GH_FAKE_DIR/list.json"; exit 0\n'
        "fi\n"
        'if [[ "${1:-}" == "pr" && "${2:-}" == "view" ]]; then\n'
        '  if [[ -n "${GH_FAKE_VIEW_RC:-}" ]]; then echo "${GH_FAKE_VIEW_BODY:-gh view fail}" >&2; exit "$GH_FAKE_VIEW_RC"; fi\n'
        '  if [[ -n "${GH_FAKE_VIEW_BODY:-}" ]]; then printf "%s" "$GH_FAKE_VIEW_BODY"; exit 0; fi\n'
        '  cat "$GH_FAKE_DIR/view.json"; exit 0\n'
        "fi\n"
        'echo "unexpected gh invocation: $*" >&2\n'
        "exit 99\n"
    )
    gh.chmod(gh.stat().st_mode | stat.S_IXUSR)


class TriageBatchGhTest(_RepoCase):
    def _two_branch_repo(self) -> None:
        _write(self.repo, "seed.txt", "seed\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        for name, extra in (("b1", "fileP.txt"), ("b2", "fileQ.txt")):
            _git(self.repo, "checkout", "-q", "main")
            _git(self.repo, "checkout", "-q", "-b", name)
            _write(self.repo, extra, "x\n")
            _write(self.repo, "shared.txt", f"from-{name}\n")  # both touch a shared file
            _commit(self.repo, f"{name} work")
            _publish_branch(self.repo, name)

    def test_triage_batch_builds_cluster_and_order(self):
        self._two_branch_repo()
        payload = self.tmp / "gh"
        payload.mkdir()
        (payload / "list.json").write_text(
            json.dumps(
                [
                    {"number": 1, "title": "b1", "headRefName": "b1", "mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN"},
                    {"number": 2, "title": "b2", "headRefName": "b2", "mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN"},
                ]
            )
        )
        bindir = self.tmp / "bin"
        _install_fake_gh(bindir, payload)
        env = {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}", "GH_FAKE_DIR": str(payload)}

        with mock.patch.dict(os.environ, env):
            report = pm.triage_batch(self.repo, run_gates=False)

        self.assertEqual(report["open_pr_count"], 2)
        self.assertIn("shared.txt", report["clusters"])
        self.assertEqual(report["clusters"]["shared.txt"], [1, 2])
        self.assertCountEqual(report["merge_order"], [1, 2])
        for v in report["prs"]:
            self.assertIn(v["verdict"], pm.SCRIPT_VERDICTS)

    def test_triage_batch_soft_error_continues_on_unresolvable_branch(self):
        # One open PR whose headRefName does not resolve as origin/<name> must surface as
        # verdict=ERROR and MUST NOT abort the rest of the batch. Without the soft-catch
        # around simulate_merge, a single deleted/renamed remote branch turns the whole
        # fleet-supervisor report into a hard failure and stalls merge ordering.
        self._two_branch_repo()
        payload = self.tmp / "gh"
        payload.mkdir()
        (payload / "list.json").write_text(
            json.dumps(
                [
                    {"number": 1, "title": "b1 ok", "headRefName": "b1", "mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN"},
                    {
                        "number": 99,
                        "title": "stale head",
                        "headRefName": "does-not-exist",
                        "mergeable": "UNKNOWN",
                        "mergeStateStatus": "DIRTY",
                    },
                    {"number": 2, "title": "b2 ok", "headRefName": "b2", "mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN"},
                ]
            )
        )
        bindir = self.tmp / "bin"
        _install_fake_gh(bindir, payload)
        env = {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}", "GH_FAKE_DIR": str(payload)}

        with mock.patch.dict(os.environ, env):
            report = pm.triage_batch(self.repo, run_gates=False)

        self.assertEqual(report["open_pr_count"], 3)
        by_pr = {v["pr"]: v for v in report["prs"]}
        self.assertEqual(by_pr[99]["verdict"], "ERROR")
        self.assertIn("does not resolve", by_pr[99].get("error", ""))
        self.assertEqual(by_pr[99]["true_delta"], [])
        self.assertEqual(by_pr[99]["title"], "stale head")
        # Healthy PRs still get real script verdicts and contribute to clusters/order.
        self.assertIn(by_pr[1]["verdict"], pm.SCRIPT_VERDICTS)
        self.assertIn(by_pr[2]["verdict"], pm.SCRIPT_VERDICTS)
        self.assertIn("shared.txt", report["clusters"])
        self.assertCountEqual(report["merge_order"], [1, 2, 99])


# --------------------------------------------------------------------------- #
# _ast_symbol_screen degrade arms (delegates to the juniper-symbol-loss-check console script)
# --------------------------------------------------------------------------- #


class AstSymbolScreenDegradeTest(unittest.TestCase):
    """Pin the fail-soft contract of the #895 subprocess screen.

    A missing / broken / non-JSON checker must ``skip`` (never crash triage), and
    ``skip`` must never become ``DAMAGED-FIX-FIRST`` -- only ``status == \"fail\"``
    drives that verdict. WARN-only findings must not be mapped into ``lost``.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="fleet-ast-degrade-"))
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)], check=False))

    def _screen_with_run(self, cp: subprocess.CompletedProcess, changed=None):
        # The console script juniper-symbol-loss-check is "available" -> shutil.which returns a
        # truthy path; _run is stubbed to return the canned CompletedProcess (no real subprocess).
        # This is the console-script analogue of the pre-W3 "_SYMBOL_LOSS_CHECK on-disk path +
        # _run stub" pattern (the module now lives in the installed juniper-ci-tools package).
        with mock.patch.object(pm.shutil, "which", return_value="/usr/bin/juniper-symbol-loss-check"):
            with mock.patch.object(pm, "_run", return_value=cp) as run_mock:
                out = pm._ast_symbol_screen(Path("/clone"), "base", "head", changed or ["util/mod.py"])
        return out, run_mock

    def test_non_screenable_delta_short_circuits_without_subprocess(self):
        with mock.patch.object(pm, "_run") as run_mock:
            out = pm._ast_symbol_screen(Path("/unused"), "base", "head", ["notes.md", "README.txt"])
        self.assertEqual(out, {"status": "pass", "lost": []})
        run_mock.assert_not_called()

    def test_missing_checker_degrades_to_skip(self):
        # juniper-ci-tools not installed -> the console script is not on PATH -> shutil.which
        # returns None -> skip, and the subprocess is never spawned.
        with mock.patch.object(pm.shutil, "which", return_value=None):
            with mock.patch.object(pm, "_run") as run_mock:
                out = pm._ast_symbol_screen(Path("/unused"), "base", "head", ["util/mod.py"])
        self.assertEqual(out["status"], "skip")
        self.assertEqual(out["lost"], [])
        self.assertIn("unavailable", out["detail"])
        run_mock.assert_not_called()

    def test_checker_exit_2_degrades_to_skip(self):
        cp = subprocess.CompletedProcess(
            args=["symbol_loss_check"],
            returncode=2,
            stdout="",
            stderr="fatal: bad revision 'base'\n",
        )
        out, run_mock = self._screen_with_run(cp)
        self.assertEqual(out["status"], "skip")
        self.assertEqual(out["lost"], [])
        self.assertIn("bad revision", out["detail"])
        run_mock.assert_called_once()

    def test_empty_stdout_degrades_to_skip(self):
        cp = subprocess.CompletedProcess(args=[], returncode=0, stdout="   \n", stderr="")
        out, _ = self._screen_with_run(cp)
        self.assertEqual(out["status"], "skip")
        self.assertEqual(out["lost"], [])
        self.assertIn("symbol-loss screen error", out["detail"])

    def test_non_json_stdout_degrades_to_skip(self):
        cp = subprocess.CompletedProcess(args=[], returncode=0, stdout="not-json{\n", stderr="")
        out, _ = self._screen_with_run(cp)
        self.assertEqual(out["status"], "skip")
        self.assertEqual(out["lost"], [])
        self.assertEqual(out["detail"], "symbol-loss screen returned non-JSON")

    def test_warn_only_findings_are_not_mapped_into_lost(self):
        report = {
            "findings": [
                {"path": "util/mod.py", "symbol": "func:foo", "verdict": "RELOCATED", "severity": "WARN"},
            ]
        }
        cp = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(report), stderr="")
        out, _ = self._screen_with_run(cp)
        self.assertEqual(out["status"], "pass")
        self.assertEqual(out["lost"], [])

    def test_fail_findings_map_shape_and_status(self):
        report = {
            "findings": [
                {"path": "util/mod.py", "symbol": "func:foo", "verdict": "LOST", "severity": "FAIL"},
                {"path": "util/mod.py", "symbol": "func:bar", "verdict": "WEAKENED", "severity": "WARN"},
            ]
        }
        cp = subprocess.CompletedProcess(args=[], returncode=1, stdout=json.dumps(report), stderr="")
        out, _ = self._screen_with_run(cp)
        self.assertEqual(out["status"], "fail")
        self.assertEqual(
            out["lost"],
            [{"file": "util/mod.py", "symbol": "func:foo", "kind": "lost"}],
        )

    def test_skip_status_does_not_damage_merge_verdict(self):
        # End-to-end: a .py-touching PR whose checker is unavailable must stay MERGE-CLEAN
        # (skip ≠ fail). Regression class: treating skip as damaged would block every
        # fleet triage batch when juniper-ci-tools is temporarily absent.
        repo = self.tmp / "repo"
        _init_repo(repo)
        _write(repo, "util/keep.py", "x = 1\n")
        _commit(repo, "c0")
        _publish_main(repo)
        _git(repo, "checkout", "-q", "-b", "addpy")
        _write(repo, "util/new.py", "def baz():\n    return 3\n")
        _commit(repo, "add util/new.py")

        # shutil.which -> None models juniper-ci-tools not installed; shutil.rmtree (used by
        # simulate_merge's clone cleanup) is a different attribute and stays live.
        with mock.patch.object(pm.shutil, "which", return_value=None):
            v = pm.simulate_merge(repo, "addpy", run_gates=False)
        self.assertEqual(v["gates"]["ast_symbol_screen"]["status"], "skip")
        self.assertEqual(v["verdict"], "MERGE-CLEAN")


# --------------------------------------------------------------------------- #
# triage_pr / _gh_json / CLI --pr (hard-fail; batch soft-ERROR is #930)
# --------------------------------------------------------------------------- #


class TriagePrGhTest(_RepoCase):
    def _one_branch_repo(self) -> None:
        _write(self.repo, "seed.txt", "seed\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "feat")
        _write(self.repo, "fileD.txt", "D\n")
        _commit(self.repo, "add D")
        _publish_branch(self.repo, "feat")

    def _fake_gh_env(self, payload: Path, **extra) -> dict:
        bindir = self.tmp / "bin"
        _install_fake_gh(bindir, payload)
        env = {
            "PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}",
            "GH_FAKE_DIR": str(payload),
        }
        env.update(extra)
        return env

    def test_triage_pr_enriches_title_and_gh_fields(self):
        self._one_branch_repo()
        payload = self.tmp / "gh"
        payload.mkdir()
        (payload / "view.json").write_text(
            json.dumps(
                {
                    "number": 42,
                    "title": "feat: land D",
                    "headRefName": "feat",
                    "mergeable": "MERGEABLE",
                    "mergeStateStatus": "CLEAN",
                }
            )
        )
        with mock.patch.dict(os.environ, self._fake_gh_env(payload)):
            v = pm.triage_pr(self.repo, 42, run_gates=False)
        self.assertEqual(v["pr"], 42)
        self.assertEqual(v["title"], "feat: land D")
        self.assertEqual(v["gh_mergeable"], "MERGEABLE")
        self.assertEqual(v["gh_merge_state"], "CLEAN")
        self.assertEqual(v["verdict"], "MERGE-CLEAN")
        self.assertEqual(v["true_delta"], ["fileD.txt"])

    def test_triage_pr_gh_nonzero_raises(self):
        self._one_branch_repo()
        payload = self.tmp / "gh"
        payload.mkdir()
        with mock.patch.dict(os.environ, self._fake_gh_env(payload, GH_FAKE_VIEW_RC="1", GH_FAKE_VIEW_BODY="not found")):
            with self.assertRaises(pm.PredictMergeError) as ctx:
                pm.triage_pr(self.repo, 99, run_gates=False)
        self.assertIn("gh pr view", str(ctx.exception))

    def test_triage_pr_non_json_raises(self):
        self._one_branch_repo()
        payload = self.tmp / "gh"
        payload.mkdir()
        with mock.patch.dict(os.environ, self._fake_gh_env(payload, GH_FAKE_VIEW_BODY="not-json{{{")):
            with self.assertRaises(pm.PredictMergeError) as ctx:
                pm.triage_pr(self.repo, 7, run_gates=False)
        self.assertIn("non-JSON", str(ctx.exception))


# --------------------------------------------------------------------------- #
# CLI exit codes
# --------------------------------------------------------------------------- #


class CliExitCodeTest(_RepoCase):
    def _run_cli(self, *args: str, env_overrides=None) -> subprocess.CompletedProcess:
        env = RedactedEnv(os.environ, JUNIPER_FLEET_SKIP_PRECOMMIT="1", **(env_overrides or {}))
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
            env=env,
        )

    def test_no_mode_is_usage_error(self):
        cp = self._run_cli()  # neither --pr nor --batch
        self.assertEqual(cp.returncode, 2)

    def test_non_git_repo_root_exits_2(self):
        nongit = self.tmp / "nongit"
        nongit.mkdir()
        cp = self._run_cli("--batch", "--repo-root", str(nongit))
        self.assertEqual(cp.returncode, 2)
        self.assertIn("not inside a git repository", cp.stderr)

    def test_empty_batch_reports_and_exits_0(self):
        _write(self.repo, "seed.txt", "seed\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        payload = self.tmp / "gh"
        payload.mkdir()
        (payload / "list.json").write_text("[]")
        bindir = self.tmp / "bin"
        _install_fake_gh(bindir, payload)
        cp = self._run_cli(
            "--batch",
            "--repo-root",
            str(self.repo),
            "--json",
            env_overrides={"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}", "GH_FAKE_DIR": str(payload)},
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        report = json.loads(cp.stdout)
        self.assertEqual(report["open_pr_count"], 0)
        self.assertEqual(report["merge_order"], [])

    def test_pr_mode_json_exits_0(self):
        _write(self.repo, "seed.txt", "seed\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "feat")
        _write(self.repo, "fileD.txt", "D\n")
        _commit(self.repo, "add D")
        _publish_branch(self.repo, "feat")
        payload = self.tmp / "gh"
        payload.mkdir()
        (payload / "view.json").write_text(
            json.dumps(
                {
                    "number": 3,
                    "title": "single",
                    "headRefName": "feat",
                    "mergeable": "MERGEABLE",
                    "mergeStateStatus": "CLEAN",
                }
            )
        )
        bindir = self.tmp / "bin"
        _install_fake_gh(bindir, payload)
        cp = self._run_cli(
            "--pr",
            "3",
            "--repo-root",
            str(self.repo),
            "--json",
            env_overrides={"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}", "GH_FAKE_DIR": str(payload)},
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        verdict = json.loads(cp.stdout)
        self.assertEqual(verdict["pr"], 3)
        self.assertEqual(verdict["title"], "single")
        self.assertEqual(verdict["verdict"], "MERGE-CLEAN")

    def test_pr_mode_gh_failure_exits_2(self):
        _write(self.repo, "seed.txt", "seed\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        payload = self.tmp / "gh"
        payload.mkdir()
        bindir = self.tmp / "bin"
        _install_fake_gh(bindir, payload)
        cp = self._run_cli(
            "--pr",
            "404",
            "--repo-root",
            str(self.repo),
            env_overrides={
                "PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}",
                "GH_FAKE_DIR": str(payload),
                "GH_FAKE_VIEW_RC": "1",
                "GH_FAKE_VIEW_BODY": "GraphQL: Could not resolve",
            },
        )
        self.assertEqual(cp.returncode, 2)
        self.assertIn("error:", cp.stderr)


class MissingHookIsSkipNotFailTest(unittest.TestCase):
    """A hook the TARGET repo does not define must degrade to ``skip``, never ``fail``.

    Regression for the 2026-09-05 finding: ``PRECOMMIT_HOOKS`` was hardcoded to
    juniper-ml's black/isort/flake8 battery, but juniper-data lints with ``ruff`` and
    defines none of them. pre-commit answers ``No hook with id `black` in stage
    `pre-commit``` and exits non-zero, which the runner scored as a gate FAILURE --
    making all 6 evaluated juniper-data PRs ``DAMAGED-FIX-FIRST`` for a property of the
    instrument, not of the PR. The mirror risk was worse: ``ruff`` was in no repo's
    battery, so a juniper-data PR could be reported MERGE-CLEAN while CI failed it on
    the only linter that repo actually runs.
    """

    def test_missing_hook_message_maps_to_skip(self):
        calls: list = []

        def fake_run(cmd, cwd=None):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 1, stdout="No hook with id `black` in stage `pre-commit`\n", stderr="")

        with mock.patch.object(pm, "_run", fake_run):
            status, detail = pm._default_gate_runner(Path("/nonexistent"), "black", ["a.py"])
        self.assertEqual(status, "skip")
        self.assertIn("not configured", detail)
        self.assertTrue(calls, "the runner must actually invoke pre-commit")

    def test_a_real_hook_failure_is_still_fail(self):
        # Negative control. If this ever returns "skip", the screen has been disarmed and
        # every genuinely unformatted PR would read clean.
        def fake_run(cmd, cwd=None):
            return subprocess.CompletedProcess(cmd, 1, stdout="reformatted x.py\n", stderr="")

        with mock.patch.object(pm, "_run", fake_run):
            status, detail = pm._default_gate_runner(Path("/nonexistent"), "black", ["a.py"])
        self.assertEqual(status, "fail")
        self.assertIn("reformatted", detail)

    def test_ruff_is_in_the_battery(self):
        # The blind spot itself: before this fix `ruff` was never run against any repo.
        self.assertIn("ruff", pm.PRECOMMIT_HOOKS)
        self.assertIn("ruff-format", pm.PRECOMMIT_HOOKS)


class ScreenCoverageTest(unittest.TestCase):
    """``screen_coverage`` must make a SKIP legible as "nothing examined this PR".

    Regression for the reporting defect that produced a false all-clear on 2026-09-05:
    both loss screens hard-code ``skip`` on a merge conflict, so a reader who counts only
    ``fail`` concludes "0 docs deletions across all N" when the honest statement is "0
    across the subset that was screened". On juniper-ml that was 43 of 99 PRs unscreened,
    and the unscreened set is exactly the CONFLICT set.
    """

    @staticmethod
    def _verdicts():
        def _v(pr, verdict, sym, docs):
            return {
                "pr": pr,
                "verdict": verdict,
                "mergeable": verdict != "CONFLICT",
                "behind_main": False,
                "true_delta": [],
                "conflicted_files": [],
                "gates": {
                    "ast_symbol_screen": {"status": sym},
                    "docs_additions_only": {"status": docs},
                },
            }

        return [
            _v(1, "MERGE-CLEAN", "pass", "pass"),
            _v(2, "CONFLICT", "skip", "skip"),
            _v(3, "DAMAGED-FIX-FIRST", "fail", "pass"),
        ]

    def test_skips_are_excluded_from_the_denominator(self):
        cov = pm.screen_coverage(self._verdicts())
        docs = cov["per_gate"]["docs_additions_only"]
        self.assertEqual(docs["pass"], 2)
        self.assertEqual(docs["fail"], 0)
        self.assertEqual(docs["skip"], 1)
        # The load-bearing assertion: 2 of 3, NOT 3 of 3. A rate over the full set is the
        # vacuous one this test exists to forbid.
        self.assertEqual(docs["evaluated"], 2)
        self.assertAlmostEqual(docs["screened_fraction"], 0.667, places=3)

    def test_unscreened_prs_are_named(self):
        cov = pm.screen_coverage(self._verdicts())
        self.assertEqual(cov["unscreened"], [2])
        self.assertEqual(cov["unscreened_count"], 1)

    def test_all_screened_reports_empty_unscreened(self):
        # Negative control: the field must be able to be empty, or it proves nothing.
        cov = pm.screen_coverage([self._verdicts()[0]])
        self.assertEqual(cov["unscreened"], [])
        self.assertEqual(cov["per_gate"]["docs_additions_only"]["screened_fraction"], 1.0)

    def test_batch_render_surfaces_the_unscreened_set(self):
        report = {
            "open_pr_count": 3,
            "base_ref": "origin/main",
            "base_sha": "deadbeefcafe",
            "prs": self._verdicts(),
            "clusters": {},
            "merge_order": [1, 3],
            "screen_coverage": pm.screen_coverage(self._verdicts()),
        }
        text = pm._render_batch(report)
        self.assertIn("UNSCREENED", text)
        self.assertIn("read by hand", text)


if __name__ == "__main__":
    unittest.main()
