#!/usr/bin/env python3
"""Drop topic-branch push globs from each repo's ci.yml so PRs stop running twice.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

WHY THIS EXISTS
---------------
Every repo's ``ci.yml`` push-triggers on topic-branch globs (``feature/**``, ``fix/**``,
and ``chore/**`` in juniper-deploy) AND on ``pull_request``. Once a PR is open both events
fire for the same commit, so every job runs twice. The concurrency group is keyed on
``github.ref``, which differs between a branch push (``refs/heads/…``) and a PR
(``refs/pull/N/merge``), so ``cancel-in-progress`` never collapses the pair.

Already fixed by hand: juniper-recurrence#108, juniper-ml#1076, juniper-canopy#488.
This sweeps the remaining six.

DELIBERATELY OUT OF SCOPE
-------------------------
``lockfile-update.yml`` (cascor / data / cascor-worker) also pairs a push glob with
``pull_request``, but it is a DIFFERENT mechanism, not a duplicate CI suite: its push arm
targets ``dependabot/pip/**`` specifically so the lockfile is regenerated in place on
Dependabot's own branch (hence ``permissions: contents: write``), while the PR arm fires on
any ``pyproject.toml`` change. Removing either arm changes real behaviour. Left alone.

WHY A TEXT TRANSFORM, NOT A YAML ROUND-TRIP
-------------------------------------------
``yaml.safe_load`` + dump would strip every comment in these heavily-annotated workflows.
The edit is therefore done line-wise, scoped strictly to the ``on:`` -> ``push:`` ->
``branches:`` block so a glob under ``pull_request`` (or anywhere else) can never be touched.
The result is re-parsed and asserted before it is pushed.

Read-only unless ``--execute`` is passed.

Usage::

    python util/ad-hoc/2026-08-13_sweep_duplicate_ci_runs.py            # dry run
    python util/ad-hoc/2026-08-13_sweep_duplicate_ci_runs.py --execute
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

OWNER = "pcalnon"
BRANCH = "ci/no-duplicate-runs"
WORKFLOW = ".github/workflows/ci.yml"
TIMEOUT = 120

REPOS = [
    "juniper-cascor",
    "juniper-data",
    "juniper-cascor-worker",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-deploy",
]

COMMIT_MSG = "ci: stop every job running twice per PR"

NOTE = [
    "    # Topic-branch globs (feature/**, fix/**) removed 2026-08-13: once a PR is open,",
    "    # `push` and `pull_request` BOTH fire for the same commit, so every job ran twice.",
    "    # The concurrency group is keyed on github.ref, which differs between a branch push",
    "    # (refs/heads/...) and a PR (refs/pull/N/merge), so cancel-in-progress never collapsed",
    "    # the pair. Same fix as juniper-recurrence#108 / juniper-ml#1076 / juniper-canopy#488.",
    "    # `pull_request` covers every commit once a PR exists; workflow_dispatch remains for a",
    "    # branch with no PR open.",
]

MUTATION = (
    "mutation($input: CreateCommitOnBranchInput!) "
    "{ createCommitOnBranch(input: $input) { commit { oid signature { isValid } } } }"
)


def gh(args: list[str]) -> str:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=TIMEOUT, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:4])}… failed: {proc.stderr.strip()[:300]}")
    return proc.stdout


def strip_topic_globs(text: str) -> tuple[str, list[str]]:
    """Remove ``**`` branch entries from the on: -> push: -> branches: list only.

    Returns (new_text, removed_entries). State machine rather than a regex over the whole
    file so an identical glob under pull_request is provably untouched.
    """
    out: list[str] = []
    removed: list[str] = []
    in_on = in_push = in_branches = False
    noted = False

    for line in text.splitlines():
        stripped = line.strip()

        if re.match(r"^on:\s*$", line) or re.match(r"^(true|'on'|\"on\"):\s*$", line):
            in_on, in_push, in_branches = True, False, False
            out.append(line)
            continue

        if in_on and re.match(r"^\S", line):  # dedent to column 0 ends the on: block
            in_on = in_push = in_branches = False
            out.append(line)
            continue

        if in_on and re.match(r"^  \S", line):  # a key directly under on:
            in_push = bool(re.match(r"^  push:\s*$", line))
            in_branches = False
            out.append(line)
            if in_push and not noted:
                out.extend(NOTE)
                noted = True
            continue

        if in_push and re.match(r"^    \S", line):
            in_branches = bool(re.match(r"^    branches:\s*$", line))
            out.append(line)
            continue

        if in_branches and re.match(r"^      - ", line):
            if "**" in line:
                removed.append(stripped.lstrip("- ").strip())
                continue  # drop it
            out.append(line)
            continue

        out.append(line)

    return "\n".join(out) + "\n", removed


def verify(original: str, patched: str, removed: list[str]) -> None:
    """Assert the patch did exactly what was intended, before anything is pushed."""
    before, after = yaml.safe_load(original), yaml.safe_load(patched)
    on_b, on_a = before[True], after[True]

    push_b = list(on_b["push"]["branches"])
    push_a = list(on_a["push"]["branches"])
    if push_a != [b for b in push_b if "**" not in str(b)]:
        raise AssertionError(f"push.branches wrong: {push_b} -> {push_a}")
    if sorted(removed) != sorted(b for b in push_b if "**" in str(b)):
        raise AssertionError(f"removed set mismatch: {removed}")

    # Nothing outside on.push may change -- especially pull_request and the job graph.
    if on_b.get("pull_request") != on_a.get("pull_request"):
        raise AssertionError("pull_request triggers changed -- refusing")
    if list(before["jobs"].keys()) != list(after["jobs"].keys()):
        raise AssertionError("job graph changed -- refusing")
    if before["jobs"] != after["jobs"]:
        raise AssertionError("job definitions changed -- refusing")


def sweep(repo: str, execute: bool) -> dict:
    sha = gh(["api", f"/repos/{OWNER}/{repo}/git/ref/heads/main", "--jq", ".object.sha"]).strip()
    raw = base64.b64decode(
        gh(["api", f"/repos/{OWNER}/{repo}/contents/{WORKFLOW}?ref={sha}", "--jq", ".content"])
    ).decode()

    patched, removed = strip_topic_globs(raw)
    if not removed:
        return {"repo": repo, "action": "SKIP", "reason": "no topic-branch push globs"}
    verify(raw, patched, removed)

    if not execute:
        return {"repo": repo, "action": "DRY-RUN", "removed": removed, "base": sha[:8]}

    try:
        gh(["api", "-X", "POST", f"/repos/{OWNER}/{repo}/git/refs",
            "-f", f"ref=refs/heads/{BRANCH}", "-f", f"sha={sha}", "--jq", ".ref"])
    except RuntimeError as exc:
        if "already exists" not in str(exc).lower():
            raise

    payload = {
        "query": MUTATION,
        "variables": {
            "input": {
                "branch": {"repositoryNameWithOwner": f"{OWNER}/{repo}", "branchName": BRANCH},
                "message": {"headline": COMMIT_MSG},
                "expectedHeadOid": sha,
                "fileChanges": {
                    "additions": [
                        {"path": WORKFLOW, "contents": base64.b64encode(patched.encode()).decode()}
                    ]
                },
            }
        },
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(payload, fh)
        tmp = fh.name
    try:
        data = json.loads(gh(["api", "graphql", "--input", tmp]))
    finally:
        Path(tmp).unlink(missing_ok=True)
    if data.get("errors"):
        raise RuntimeError(f"graphql: {json.dumps(data['errors'])[:300]}")
    commit = data["data"]["createCommitOnBranch"]["commit"]

    body = (
        "Sweeps this repo into the duplicate-run fix already applied to "
        "juniper-recurrence#108, juniper-ml#1076 and juniper-canopy#488.\n\n"
        "## The problem\n\n"
        f"`ci.yml` push-triggered on {', '.join('`' + r + '`' for r in removed)} **and** on "
        "`pull_request`. Once a PR is open both events fire for the same commit, so **every job "
        "ran twice**. The concurrency group is keyed on `github.ref`, which differs between a "
        "branch push (`refs/heads/…`) and a PR (`refs/pull/N/merge`), so `cancel-in-progress` "
        "never collapsed the pair — a straight 2x CI cost on every PR from a matching branch.\n\n"
        "## The fix\n\n"
        "Drop the topic-branch globs from `on.push`, leaving `[main, develop]`. `pull_request` is "
        "untouched and covers every commit once a PR exists; `workflow_dispatch` remains for a "
        "branch with no PR open. The only behaviour lost is CI on a topic branch with **no PR at "
        "all**.\n\n"
        "## Not a concurrency-group change\n\n"
        "Normalising the group (e.g. `github.head_ref || github.ref_name`) would also collapse the "
        "pair, but by **cancelling** one run — leaving `cancelled` check-runs on the PR alongside "
        "the survivors. That is the confusing signature that cost real diagnosis time on "
        "juniper-data#253, where a cancelled matrix job reported under its un-interpolated "
        "`${{ matrix.* }}` name. Dropping the duplicate trigger yields exactly one run and no "
        "cancelled artifacts.\n\n"
        "## Deliberately untouched\n\n"
        "`lockfile-update.yml` also pairs a push glob with `pull_request`, but it is a different "
        "mechanism, not a duplicate suite: its push arm targets `dependabot/pip/**` so the lockfile "
        "is regenerated in place on Dependabot's own branch (`permissions: contents: write`), while "
        "the PR arm fires on any `pyproject.toml` change. Removing either arm would change real "
        "behaviour.\n\n"
        "## Verification\n\n"
        "Edit applied line-wise (a YAML round-trip would strip every comment in this file) and "
        "scoped strictly to the `on:` -> `push:` -> `branches:` block, then re-parsed and asserted "
        "before push: `push.branches` equals the original minus its globs, `pull_request` is "
        "byte-identical, and the job graph and every job definition are unchanged."
    )
    url = gh(["pr", "create", "--repo", f"{OWNER}/{repo}", "--base", "main",
              "--head", BRANCH, "--title", COMMIT_MSG, "--body", body])
    return {
        "repo": repo,
        "action": "OPENED",
        "removed": removed,
        "signed": commit["signature"]["isValid"],
        "pr": url.strip().splitlines()[-1],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", action="store_true", help="create branches/commits/PRs")
    ap.add_argument("--repo", help="limit to one repo")
    args = ap.parse_args()

    rc = 0
    for repo in ([args.repo] if args.repo else REPOS):
        try:
            print(json.dumps(sweep(repo, args.execute)))
        except (RuntimeError, AssertionError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as exc:
            print(json.dumps({"repo": repo, "action": "ERROR", "error": str(exc)[:300]}))
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
