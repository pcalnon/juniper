"""Hermetic tests for ``util/fleet_triage/predict_merge.py`` (Stage-0 supervisor script layer).

Drives the deterministic predicted-merge engine over synthetic bare-origin + branch
fixture repos (the ``tests/test_worktree_cleanup.py`` fixture idiom) -- no network, no
``gh``, no ``pre-commit`` (the fast-gate battery is injected or env-skipped). Covers:

* the four verdict classes -- MERGE-CLEAN, NEEDS-UPDATE-BRANCH, DAMAGED-FIX-FIRST
  (symbol-loss AND docs-deletion AND injected gate-fail), and CONFLICT;
* the TRUE-delta-vs-stale-file-list discrimination (delta from the merge RESULT, so a
  main-owned file the branch is merely stale on is excluded -- the #729 class);
* the docs additions-only screen edges (``_removed_content_lines`` ``---`` header
  exclusion; additions-only ``.md`` pass; non-``.md`` deletions ignored);
* the fast-gate battery skip when the TRUE delta has no ``.py`` files;
* the ``--batch`` cluster map + suggested merge order (restore/heal/repair/fix-first
  first, then ascending same-file-cluster membership), including a fake-``gh``
  end-to-end batch;
* the detached-clone-never-mutates-source contract (a ``git clone`` under the system
  tempdir, never a ``git worktree`` of -- and never a write to -- the invoking checkout);
* CLI exit codes (0 always-report / 2 usage / 2 non-git ``--repo-root``).

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
        # util/sequence_safety/symbol_loss_check.py CLI as the push:main ``main-verify``
        # gate, so an author-declared intentional removal is honored identically.
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
        _write(self.repo, "notes.md", "line1\nline2\nline3\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "docdel")
        _write(self.repo, "notes.md", "line1\nline3\n")  # line2 removed
        _commit(self.repo, "drop a docs line")

        v = pm.simulate_merge(self.repo, "docdel", run_gates=False)
        self.assertEqual(v["verdict"], "DAMAGED-FIX-FIRST")
        dels = v["gates"]["docs_additions_only"]["deletions"]
        self.assertEqual(v["gates"]["docs_additions_only"]["status"], "fail")
        self.assertTrue(dels and dels[0]["file"] == "notes.md", dels)

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
            {"pr": 1, "title": "restore deleted block", "branch": "cursor/restore-x", "true_delta": ["A.md"]},
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

    def test_is_heal_recognizes_repair_and_fix_first_tokens(self):
        # suggest_order only auto-leads on restore/heal today in the cluster test; the
        # other documented tokens must also promote, or a repair/fix-first PR sits
        # behind colliding feat work and the supervisor merge order is wrong.
        self.assertTrue(pm._is_heal({"title": "repair broken gate", "branch": "cursor/x"}))
        self.assertTrue(pm._is_heal({"title": "feat", "branch": "cursor/fix-first-docs"}))
        self.assertTrue(pm._is_heal({"title": "heal canopy WS", "branch": "cursor/y"}))
        self.assertFalse(pm._is_heal({"title": "feat docs", "branch": "cursor/docs-sync"}))

        verdicts = [
            {"pr": 20, "title": "feat hot", "branch": "cursor/hot", "true_delta": ["HOT.py"]},
            {"pr": 21, "title": "repair symbol screen", "branch": "cursor/repair-x", "true_delta": ["A.md"]},
            {"pr": 22, "title": "feat solo", "branch": "cursor/solo", "true_delta": ["SOLO.py"]},
            {"pr": 23, "title": "nudge", "branch": "cursor/fix-first-y", "true_delta": ["B.md"]},
        ]
        clusters = pm.build_clusters(verdicts)
        order = pm.suggest_order(verdicts, clusters)
        # Both heal PRs lead (repair title + fix-first branch); remaining ties break
        # by PR number via _pr_key (20 before 22), not by title.
        self.assertEqual(order[:2], [21, 23], order)
        self.assertEqual(order[2:], [20, 22], order)


# --------------------------------------------------------------------------- #
# docs additions-only screen — pure unit + wiring edges
# --------------------------------------------------------------------------- #


class DocsAdditionsScreenUnitTest(unittest.TestCase):
    """Pin ``_removed_content_lines`` so unified-diff headers never inflate deletions."""

    def test_removed_content_lines_ignores_file_headers(self):
        # A real unified diff always opens with `---` / `+++` headers. Those must not
        # count as content removals — otherwise every touched `.md` (even pure adds)
        # reports removed_lines >= 1 and the PR is falsely DAMAGED-FIX-FIRST.
        diff = (
            "diff --git a/notes/x.md b/notes/x.md\n"
            "index 111..222 100644\n"
            "--- a/notes/x.md\n"
            "+++ b/notes/x.md\n"
            "@@ -1,3 +1,3 @@\n"
            " keep\n"
            "-gone\n"
            "+added\n"
            " keep2\n"
        )
        self.assertEqual(pm._removed_content_lines(diff), 1)

    def test_removed_content_lines_pure_add_is_zero(self):
        diff = (
            "diff --git a/notes/new.md b/notes/new.md\n"
            "new file mode 100644\n"
            "index 000..abc\n"
            "--- /dev/null\n"
            "+++ b/notes/new.md\n"
            "@@ -0,0 +1,2 @@\n"
            "+# title\n"
            "+body\n"
        )
        self.assertEqual(pm._removed_content_lines(diff), 0)

    def test_removed_content_lines_empty_diff_is_zero(self):
        self.assertEqual(pm._removed_content_lines(""), 0)


def _install_fake_gh(bin_dir: Path, payload_dir: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text("#!/usr/bin/env bash\n" 'if [[ "${1:-}" == "pr" && "${2:-}" == "list" ]]; then cat "$GH_FAKE_DIR/list.json"; exit 0; fi\n' 'if [[ "${1:-}" == "pr" && "${2:-}" == "view" ]]; then cat "$GH_FAKE_DIR/view.json"; exit 0; fi\n' 'echo "unexpected gh invocation: $*" >&2\nexit 99\n')
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


if __name__ == "__main__":
    unittest.main()
