"""Behavioural tests for util/prompt_discovery/ (custom-agent suite PR 4).

Covers the design's CI-objective acceptance for the discovery helpers (S5.6, S8): the
grounding-bundle schema, the provenance envelope, the per-probe graceful degradation, and
-- the dominant grounding hazard -- the ``test_status`` ``cold_cache``/empty distinction
(so "no failures" can never masquerade as fact when the truth is "not measured").

``util/`` is not a package, so the probes are imported via the house ``sys.path.insert``
idiom (matching tests/test_editable_install_drift_check.py). Location-agnostic: the repo
root is discovered by walking up for ``.github/workflows/``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


def _git_init_repo(path: str, commit_epoch: "int | None" = None) -> None:
    """Init a throwaway git repo at ``path`` with one empty commit (identity via env and signing
    disabled in-repo, so the user's global config -- e.g. ``commit.gpgsign=true`` + a pinentry
    prompt -- never leaks in). When ``commit_epoch`` is given the commit is dated to it -- deterministic
    for the D-1 freshness cases; otherwise the current time is used (the E-3 ``--target-repo`` cases
    just need a real sibling HEAD). Unifies the two helpers that PR-1 (D-1) and PR-4 (E-3) each added
    to this file independently -- both signatures are served by the optional ``commit_epoch``."""
    env = RedactedEnv(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    if commit_epoch is not None:
        env["GIT_AUTHOR_DATE"] = f"{commit_epoch} +0000"
        env["GIT_COMMITTER_DATE"] = f"{commit_epoch} +0000"
    subprocess.run(["git", "-C", path, "init", "-q"], check=True, env=env, timeout=30)
    subprocess.run(["git", "-C", path, "config", "commit.gpgsign", "false"], check=True, env=env, timeout=30)
    subprocess.run(["git", "-C", path, "commit", "-q", "--allow-empty", "-m", "init"], check=True, env=env, timeout=30)


def _git_head(path: str) -> str:
    return subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=30).stdout.strip()


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_PD_DIR = _REPO_ROOT / "util" / "prompt_discovery"
sys.path.insert(0, str(_PD_DIR))

import concurrency  # noqa: E402
import conventions  # noqa: E402
import dependency_facts  # noqa: E402
import file_probe  # noqa: E402
import repo_context  # noqa: E402
import symbol_probe  # noqa: E402
import test_status  # noqa: E402
from _util import run as _real_run  # noqa: E402

from tests.redacted_env import RedactedEnv

_SHA40 = r"^[0-9a-f]{40}$"
_PROBE_KEYS = {"repo_context", "test_status", "file_probe", "symbol_probe", "dependency_facts", "conventions", "concurrency"}


class RepoContextProbeTest(unittest.TestCase):
    def test_real_repo_resolves_head(self):
        ctx = repo_context.probe(str(_REPO_ROOT))
        self.assertEqual(ctx["status"], "ok")
        self.assertRegex(ctx["head_sha"], _SHA40)
        self.assertTrue(ctx["repo"])

    def test_non_git_dir_is_unavailable(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = repo_context.probe(d)
            self.assertEqual(ctx["status"], "unavailable")
            self.assertIsNone(ctx["head_sha"])


class TestStatusProbeTest(unittest.TestCase):
    """The cold_cache/empty distinction is the headline grounding-hazard guard.

    The D-1 freshness cases extend it: a cache that predates the current HEAD commit (or is
    older than the TTL) is reported ``stale`` with ``failing_count`` blanked, so a measured
    "no failures" cannot masquerade as current when it measured a different tree.
    """

    @staticmethod
    def _write_lastfailed(d, content='{"tests/test_x.py::test_a": true}'):
        cache = Path(d) / ".pytest_cache" / "v" / "cache"
        cache.mkdir(parents=True)
        lf = cache / "lastfailed"
        lf.write_text(content, encoding="utf-8")
        return lf

    def test_cold_cache_when_never_run(self):
        with tempfile.TemporaryDirectory() as d:
            res = test_status.probe(d)
            self.assertEqual(res["status"], "cold_cache")
            self.assertIsNone(res["failing_count"])
            # cold_cache is byte-for-byte preserved -- no freshness provenance is stamped.
            self.assertNotIn("cache_mtime", res)

    def test_empty_cache_means_zero_failures(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".pytest_cache" / "v" / "cache").mkdir(parents=True)
            res = test_status.probe(d)
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["failing_count"], 0)

    def test_failing_names_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d) / ".pytest_cache" / "v" / "cache"
            cache.mkdir(parents=True)
            (cache / "lastfailed").write_text('{"tests/test_x.py::test_a": true}', encoding="utf-8")
            res = test_status.probe(d)
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["failing_count"], 1)
            self.assertIn("tests/test_x.py::test_a", res["failing"])

    def test_fresh_cache_after_commit_is_ok(self):
        # (a) cache mtime >= HEAD commit time and age < TTL -> ok, freshness provenance stamped.
        with tempfile.TemporaryDirectory() as d:
            _git_init_repo(d, commit_epoch=int(time.time()) - 3600)  # HEAD committed an hour ago
            self._write_lastfailed(d)  # written now -> mtime >> commit time, age ~0
            res = test_status.probe(d)
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["failing_count"], 1)
            self.assertIn("cache_mtime", res)
            self.assertIn("age_seconds", res)

    def test_stale_when_cache_predates_head_commit(self):
        # (b) cache mtime < HEAD commit time -> stale (primary signal), isolated from the TTL.
        with tempfile.TemporaryDirectory() as d:
            commit_epoch = int(time.time())
            _git_init_repo(d, commit_epoch=commit_epoch)
            lf = self._write_lastfailed(d)
            os.utime(lf, (commit_epoch - 3600, commit_epoch - 3600))  # cache predates the commit
            res = test_status.probe(d, ttl_seconds=10**9)  # huge TTL -> only the commit signal can fire
            self.assertEqual(res["status"], "stale")
            self.assertIsNone(res["failing_count"])
            self.assertIn("commit", res["reason"])
            self.assertIn("cache_mtime", res)
            self.assertIn("age_seconds", res)

    def test_stale_when_older_than_ttl(self):
        # (c) no git (commit signal is a no-op) + age > TTL -> stale (secondary signal).
        with tempfile.TemporaryDirectory() as d:
            lf = self._write_lastfailed(d)
            os.utime(lf, (time.time() - 10_000, time.time() - 10_000))
            res = test_status.probe(d, ttl_seconds=900)
            self.assertEqual(res["status"], "stale")
            self.assertIsNone(res["failing_count"])
            self.assertIn("TTL", res["reason"])

    def test_unavailable_when_lastfailed_unreadable(self):
        # (e) malformed lastfailed -> unavailable, byte-for-byte preserved (no freshness stamp).
        with tempfile.TemporaryDirectory() as d:
            self._write_lastfailed(d, content="{not valid json")
            res = test_status.probe(d)
            self.assertEqual(res["status"], "unavailable")
            self.assertIsNone(res["failing_count"])
            self.assertNotIn("cache_mtime", res)


class DependencyFactsProbeTest(unittest.TestCase):
    def test_real_pyproject_surface(self):
        dep = dependency_facts.probe(str(_REPO_ROOT))
        self.assertEqual(dep["status"], "ok")
        self.assertIsNotNone(dep["version"])
        self.assertIn("clients", dep["extras"])
        self.assertIn("worker", dep["extras"])


class ConventionsProbeTest(unittest.TestCase):
    def test_real_agents_md_header(self):
        conv = conventions.probe(str(_REPO_ROOT))
        self.assertEqual(conv["line_length"], 512)
        self.assertIn("Project", conv["agents_md_header"])
        self.assertIn("Version", conv["agents_md_header"])


class SymbolProbeTest(unittest.TestCase):
    def test_resolved_and_unresolved(self):
        sp = symbol_probe.probe(str(_REPO_ROOT), ["register_or_reuse", "this_symbol_does_not_exist_zzz"])
        self.assertEqual(sp["symbols"]["register_or_reuse"]["status"], "resolved")
        self.assertIsNotNone(sp["symbols"]["register_or_reuse"]["definition"])
        self.assertEqual(sp["symbols"]["this_symbol_does_not_exist_zzz"]["status"], "unresolved")


class FileProbeTest(unittest.TestCase):
    def test_subject_yields_anchors(self):
        fp = file_probe.probe(str(_REPO_ROOT), "register_or_reuse")
        self.assertEqual(fp["status"], "ok")
        self.assertTrue(fp["anchors"], "expected at least one anchor for a known symbol")
        self.assertIsInstance(fp["anchors"][0]["line"], int)

    def test_no_subject_yields_no_anchors(self):
        fp = file_probe.probe(str(_REPO_ROOT), None)
        self.assertEqual(fp["anchors"], [])


class ConcurrencyProbeTest(unittest.TestCase):
    """Graceful degrade for ``concurrency.probe`` (design S5.6).

    ``gh`` may be missing / unauthenticated / return garbage JSON in headless CI.
    The probe must not raise or poison the bundle — ``open_prs_status`` becomes
    ``unavailable``, and overall status stays ``ok`` when worktrees are still
    readable (work dup-guard still has a signal).
    """

    def test_gh_unavailable_with_worktrees_keeps_overall_ok(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            _git_init_repo(d)

            def fake_run(cmd, cwd=None, timeout=30):
                if cmd and cmd[0] == "gh":
                    return 127, "", "binary not found: gh"
                return _real_run(cmd, cwd=cwd, timeout=timeout)

            with patch.object(concurrency, "run", side_effect=fake_run):
                result = concurrency.probe(d)

            self.assertEqual(result["open_prs_status"], "unavailable")
            self.assertEqual(result["open_prs"], [])
            self.assertTrue(result["worktrees"], "git worktree list must still populate")
            self.assertEqual(result["status"], "ok")

    def test_gh_invalid_json_degrades_prs_slice(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            _git_init_repo(d)

            def fake_run(cmd, cwd=None, timeout=30):
                if cmd and cmd[0] == "gh":
                    return 0, "not-json{", ""
                return _real_run(cmd, cwd=cwd, timeout=timeout)

            with patch.object(concurrency, "run", side_effect=fake_run):
                result = concurrency.probe(d)

            self.assertEqual(result["open_prs_status"], "unavailable")
            self.assertEqual(result["open_prs"], [])
            self.assertEqual(result["status"], "ok")

    def test_gh_ok_parses_open_prs(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            _git_init_repo(d)
            payload = [{"number": 42, "title": "demo", "headRefName": "feat/x"}]

            def fake_run(cmd, cwd=None, timeout=30):
                if cmd and cmd[0] == "gh":
                    return 0, json.dumps(payload), ""
                return _real_run(cmd, cwd=cwd, timeout=timeout)

            with patch.object(concurrency, "run", side_effect=fake_run):
                result = concurrency.probe(d)

            self.assertEqual(result["open_prs_status"], "ok")
            self.assertEqual(result["open_prs"], payload)
            self.assertEqual(result["status"], "ok")

    def test_gh_and_worktrees_both_unavailable(self) -> None:
        def fake_run(cmd, cwd=None, timeout=30):
            return 1, "", "fail"

        with patch.object(concurrency, "run", side_effect=fake_run):
            result = concurrency.probe("/tmp/not-a-real-repo-for-concurrency")

        self.assertEqual(result["open_prs_status"], "unavailable")
        self.assertEqual(result["open_prs"], [])
        self.assertEqual(result["worktrees"], [])
        self.assertEqual(result["status"], "unavailable")


class CliBundleTest(unittest.TestCase):
    def _run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(_PD_DIR / "cli.py"), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )

    def test_bundle_schema_and_provenance(self):
        proc = self._run_cli("--repo-root", str(_REPO_ROOT), "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        bundle = json.loads(proc.stdout)
        self.assertEqual(bundle["schema_version"], 1)
        for key in _PROBE_KEYS | {"provenance"}:
            self.assertIn(key, bundle)
        prov = bundle["provenance"]
        for key in ("captured_at", "head_sha", "dirty", "ttl_seconds", "per_probe_status"):
            self.assertIn(key, prov)
        self.assertRegex(prov["head_sha"], _SHA40)
        self.assertIsInstance(prov["ttl_seconds"], int)
        self.assertEqual(set(prov["per_probe_status"]), _PROBE_KEYS)

    def test_head_sha_matches_git(self):
        proc = self._run_cli("--repo-root", str(_REPO_ROOT))
        bundle = json.loads(proc.stdout)
        git = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(bundle["provenance"]["head_sha"], git.stdout.strip())

    def test_target_repo_grounds_a_sibling_as_repo_root_alias(self):
        # E-3: --target-repo (and --repo-root) ground an explicitly-named sibling repo, distinct
        # from CWD; the bundle's head_sha binds to THAT repo's HEAD, not the caller's.
        with tempfile.TemporaryDirectory() as d:
            _git_init_repo(d)
            head = _git_head(d)
            for flag in ("--target-repo", "--repo-root"):
                proc = self._run_cli(flag, d, "--json")
                self.assertEqual(proc.returncode, 0, f"{flag}: {proc.stderr}")
                bundle = json.loads(proc.stdout)
                self.assertEqual(bundle["provenance"]["head_sha"], head, f"{flag} must ground {d}'s HEAD")
                self.assertEqual(bundle["repo_context"]["repo"], Path(d).name)

    def test_default_repo_root_grounds_cwd_unchanged(self):
        # E-3 regression: with NO flag the bundle grounds CWD -- byte-for-byte the pre-E-3 default.
        proc = subprocess.run(
            [sys.executable, str(_PD_DIR / "cli.py"), "--json"],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(_REPO_ROOT),
            timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        bundle = json.loads(proc.stdout)
        self.assertEqual(bundle["provenance"]["head_sha"], _git_head(str(_REPO_ROOT)))

    def test_hard_stop_on_non_git_root(self):
        with tempfile.TemporaryDirectory() as d:
            proc = self._run_cli("--repo-root", d)
            self.assertEqual(proc.returncode, 2, "discovery failure must be a hard stop (exit 2)")
            envelope = json.loads(proc.stdout)
            self.assertEqual(envelope["status"], "discovery_failed")


if __name__ == "__main__":
    unittest.main()
