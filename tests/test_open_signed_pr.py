#!/usr/bin/env python3
"""Tests for util/open_signed_pr.py (GitHub-signed cross-repo PR opener).

Promoted from ``util/ad-hoc/`` after the ml#1099 signing fan-out, which it landed
across 8 repos. ``util/`` is outside every pre-commit Python hook's scope
(flake8/black/mypy/bandit scope to ``scripts/`` + ``tests/``), so this suite IS
the gate.

Hermetic: ``gh`` is a PATH stub that records its argv and replays canned stdout.
No network, no real repo, no ``git``.

Contract pinned here:

- The commit is created through ``createCommitOnBranch`` -- that is the whole
  point (GitHub signs API-authored commits; a runner cannot GPG-sign). The
  payload must carry ``expectedHeadOid`` pinned to the resolved base sha so a
  concurrent push fails loudly instead of clobbering.
- ``--add`` content is base64-encoded; ``--delete`` becomes ``fileChanges.deletions``
  and is OMITTED entirely when unused (never sent as an empty list).
- ``--dry-run`` resolves read-only and writes nothing: no ref POST, no mutation,
  no ``pr create``.
- Refusals return 1 and perform no writes: an open PR already on the branch
  (dup-guard -- concurrent sessions are a real hazard in this fleet) and an
  already-existing branch (never force-update someone else's ref).
- Nothing to commit (neither --add nor --delete) is a usage error, exit 2.
- The ``git/refs`` POST carries an explicit ``ref=refs/heads/<branch>`` -- the
  ml#770 R7 lesson; an omitted/empty ref must never be deferred to the live API.

Run: python3 -m unittest -v tests/test_open_signed_pr.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-14
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import stat
import subprocess  # nosec B404 - drives the util's CLI with a PATH-stubbed `gh`
import sys
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

BASE_SHA = "a" * 40
NEW_OID = "b" * 40


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_MODULE_PATH = _REPO_ROOT / "util" / "open_signed_pr.py"


def _load():
    spec = importlib.util.spec_from_file_location("open_signed_pr", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Harness:
    """A tempdir with a stub `gh` on PATH that logs argv and replays canned output."""

    def __init__(self, tmp: Path, *, open_pr_url: str = "", branch_exists: bool = False):
        self.tmp = tmp
        self.log = tmp / "gh.log"
        self.log.write_text("", encoding="utf-8")
        self.bodies = tmp / "bodies"
        self.bodies.mkdir()

        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        # `graphql --input <file>`: copy the request body aside so the test can
        # assert on the exact mutation payload that would hit the API.
        gh.write_text(
            "#!/usr/bin/env bash\n"
            f'LOG="{self.log}"\n'
            f'BODIES="{self.bodies}"\n'
            'printf "%s\\n" "$*" >>"$LOG"\n'
            'if [ "${1:-}" = "pr" ] && [ "${2:-}" = "list" ]; then\n'
            f'  printf "%s" "{open_pr_url}"\n'
            "  exit 0\n"
            "fi\n"
            'if [ "${1:-}" = "pr" ] && [ "${2:-}" = "create" ]; then\n'
            '  echo "https://github.com/pcalnon/repo/pull/1"\n'
            "  exit 0\n"
            "fi\n"
            'if [ "${1:-}" = "api" ] && [ "${2:-}" = "graphql" ]; then\n'
            '  for a in "$@"; do\n'
            '    if [ -f "$a" ]; then cp "$a" "$BODIES/mutation.json"; fi\n'
            "  done\n"
            f'  echo \'{{"data":{{"createCommitOnBranch":{{"commit":{{"oid":"{NEW_OID}","url":"u"}}}}}}}}\'\n'
            "  exit 0\n"
            "fi\n"
            # git/ref/heads/<name> lookups: base resolves, feature branch depends.
            'case "$*" in\n' '  *"git/ref/heads/main"*)\n' f'    echo "{BASE_SHA}"; exit 0 ;;\n' '  *"git/refs"*)\n' '    echo "{}"; exit 0 ;;\n' '  *"git/ref/heads/"*)\n' f'    {"exit 0" if branch_exists else "exit 1"} ;;\n' "esac\n" "exit 0\n",
            encoding="utf-8",
        )
        gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
        self.bin_dir = bin_dir

    def env(self):
        env = RedactedEnv(os.environ)
        env["PATH"] = str(self.bin_dir) + os.pathsep + env.get("PATH", "")
        return env

    def calls(self) -> list:
        return [line for line in self.log.read_text(encoding="utf-8").splitlines() if line.strip()]

    def mutation(self) -> dict:
        path = self.bodies / "mutation.json"
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))


def _run(harness: _Harness, extra: list) -> tuple:
    src = harness.tmp / "payload.yml"
    src.write_text("name: demo\n", encoding="utf-8")
    body = harness.tmp / "body.md"
    body.write_text("PR body\n", encoding="utf-8")

    argv = [
        sys.executable,
        str(_MODULE_PATH),
        "--repo",
        "juniper-cascor",
        "--branch",
        "ci/demo",
        "--message",
        "ci: demo",
        "--title",
        "ci: demo",
        "--body-file",
        str(body),
        *extra,
    ]
    proc = subprocess.run(  # nosec B603 - fixed argv, stubbed PATH
        argv,
        capture_output=True,
        text=True,
        env=harness.env(),
        check=False,
        timeout=60,
    )
    return proc.returncode, proc.stdout + proc.stderr


class OpenSignedPrModuleTest(unittest.TestCase):
    """Unit-level checks that need no subprocess."""

    def test_parse_add_requires_both_halves(self) -> None:
        mod = _load()
        self.assertEqual(mod.parse_add("a.yml:b/c.yml"), ("a.yml", "b/c.yml"))
        for bad in ("no-colon", ":only-repo", "only-local:"):
            with self.assertRaises(argparse.ArgumentTypeError):
                mod.parse_add(bad)

    def test_mutation_name_is_pinned(self) -> None:
        """The signed-commit path is the entire reason this tool exists."""
        mod = _load()
        self.assertIn("createCommitOnBranch", mod.CREATE_COMMIT_MUTATION)


class OpenSignedPrCliTest(unittest.TestCase):
    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            h = _Harness(tmp)
            rc, out = _run(h, ["--add", f"{tmp / 'payload.yml'}:.github/workflows/demo.yml", "--dry-run"])
            self.assertEqual(rc, 0, out)
            self.assertIn("DRY-RUN", out)
            joined = " ".join(h.calls())
            self.assertNotIn("graphql", joined, "dry-run must not create a commit")
            self.assertNotIn("git/refs", joined, "dry-run must not create a branch")
            self.assertNotIn("pr create", joined, "dry-run must not open a PR")

    def test_dup_guard_refuses_when_open_pr_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            h = _Harness(tmp, open_pr_url="https://github.com/pcalnon/juniper-cascor/pull/7")
            rc, out = _run(h, ["--add", f"{tmp / 'payload.yml'}:.github/workflows/demo.yml"])
            self.assertEqual(rc, 1, out)
            self.assertIn("DUP-GUARD", out)
            joined = " ".join(h.calls())
            self.assertNotIn("graphql", joined)
            self.assertNotIn("pr create", joined)

    def test_existing_branch_is_refused_not_force_updated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            h = _Harness(tmp, branch_exists=True)
            rc, out = _run(h, ["--add", f"{tmp / 'payload.yml'}:.github/workflows/demo.yml"])
            self.assertEqual(rc, 1, out)
            self.assertIn("REFUSED", out)
            self.assertNotIn("graphql", " ".join(h.calls()))

    def test_nothing_to_commit_is_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td))
            rc, out = _run(h, [])
            self.assertEqual(rc, 2, out)
            self.assertIn("nothing to commit", out)

    def test_happy_path_creates_branch_signed_commit_and_pr(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            h = _Harness(tmp)
            rc, out = _run(h, ["--add", f"{tmp / 'payload.yml'}:.github/workflows/demo.yml"])
            self.assertEqual(rc, 0, out)
            self.assertIn(NEW_OID[:12], out)

            joined = " ".join(h.calls())
            self.assertIn("git/refs", joined)
            self.assertIn("graphql", joined)
            self.assertIn("pr create", joined)

            # ml#770 R7: the refs POST must name the ref explicitly.
            refs_call = next(c for c in h.calls() if "git/refs" in c)
            self.assertIn("ref=refs/heads/ci/demo", refs_call)

            payload = h.mutation()["variables"]["input"]
            self.assertEqual(payload["expectedHeadOid"], BASE_SHA)
            self.assertEqual(payload["branch"]["branchName"], "ci/demo")
            self.assertEqual(payload["branch"]["repositoryNameWithOwner"], "pcalnon/juniper-cascor")
            adds = payload["fileChanges"]["additions"]
            self.assertEqual([a["path"] for a in adds], [".github/workflows/demo.yml"])
            self.assertNotIn("deletions", payload["fileChanges"], "empty deletions must be omitted, not sent as []")

    def test_delete_is_carried_into_the_same_commit(self) -> None:
        """--add + --delete together express a file move in one signed commit."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            h = _Harness(tmp)
            rc, out = _run(
                h,
                [
                    "--add",
                    f"{tmp / 'payload.yml'}:util/new_home.yml",
                    "--delete",
                    "util/old_home.yml",
                ],
            )
            self.assertEqual(rc, 0, out)
            fc = h.mutation()["variables"]["input"]["fileChanges"]
            self.assertEqual([a["path"] for a in fc["additions"]], ["util/new_home.yml"])
            self.assertEqual([d["path"] for d in fc["deletions"]], ["util/old_home.yml"])

    def test_delete_only_commit_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td))
            rc, out = _run(h, ["--delete", "util/gone.yml"])
            self.assertEqual(rc, 0, out)
            fc = h.mutation()["variables"]["input"]["fileChanges"]
            self.assertEqual(fc["additions"], [])
            self.assertEqual([d["path"] for d in fc["deletions"]], ["util/gone.yml"])

    def test_unreadable_add_source_is_hard_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td))
            rc, out = _run(h, ["--add", "/nonexistent/nope.yml:util/x.yml"])
            self.assertEqual(rc, 2, out)
            self.assertIn("cannot read", out)


if __name__ == "__main__":
    unittest.main()
