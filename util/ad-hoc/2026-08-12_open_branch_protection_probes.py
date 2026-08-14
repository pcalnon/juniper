#!/usr/bin/env python3
"""Open the branch-protection validation probe PR in each Juniper publishing repo.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

WHY THIS EXISTS
---------------
The 2026-08-12 fleet ruleset correction needs an end-to-end proof per repo: that a
normal PR can reach ``CLEAN`` and merge WITHOUT admin bypass. juniper-ml proved it
(PR #1071, rule suite 3658849854 ``result=pass``); this opens the equivalent probe
in each remaining repo.

TWO NON-OBVIOUS CONSTRAINTS
---------------------------
1. **The commit must be GitHub-signed.** ``required_signatures`` is active fleet-wide
   and an unsigned commit anywhere on a PR branch blocks the merge (squash-merge does
   NOT rescue it -- juniper-ml#1070). The REST contents API (``PUT .../contents/…``)
   creates an **unsigned** commit; only the GraphQL ``createCommitOnBranch`` mutation
   produces a signed one. This script uses the mutation.
2. **Docs-only is the stricter probe.** Tier 1 admits only always-run contexts, so a
   docs-only PR is the case most likely to expose a path-gated context that was
   wrongly required -- exactly what we want surfaced now rather than later.

Read-only unless ``--execute`` is passed. Default is a dry run.

Usage::

    python util/ad-hoc/2026-08-12_open_branch_protection_probes.py            # dry run
    python util/ad-hoc/2026-08-12_open_branch_protection_probes.py --execute
    python util/ad-hoc/2026-08-12_open_branch_protection_probes.py --execute --repo juniper-data
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

OWNER = "pcalnon"
BRANCH = "chore/branch-protection-validation"
TIMEOUT = 120

# repo -> the REPO token used by the notes naming convention
REPOS = {
    "juniper-cascor": "CASCOR",
    "juniper-canopy": "CANOPY",
    "juniper-data": "DATA",
    "juniper-cascor-worker": "CASCOR-WORKER",
    "juniper-deploy": "DEPLOY",
    "juniper-cascor-client": "CASCOR-CLIENT",
    "juniper-recurrence": "RECURRENCE",
}

COMMIT_MSG = "docs(notes): record the validated branch-protection contract"

BODY = """Probe PR for the 2026-08-12 fleet branch-protection validation.

Records this repo's ruleset contract and the operational lessons from the arc. Doubles \
as the end-to-end check that a normal PR here can reach `CLEAN` and merge **without \
admin bypass**, now that the required-status-check contexts and `code_scanning` tool \
list have been corrected per-repo.

Reference: juniper-ml \
`notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md`.

Docs-only, no code paths touched. The commit is GitHub-signed (created via \
`createCommitOnBranch`) so it satisfies `required_signatures`."""

DOC = """# Branch-Protection Validation — {repo}

**Project**: Juniper
**Sub-Project**: {repo}
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0
**Last Updated**: 2026-08-12

---

Records the outcome of the 2026-08-12 fleet ruleset validation.

`main` is governed by an 8-rule ruleset uniform across all 9 publishing repos:
`code_quality`, `code_scanning`, `creation`, `deletion`, `non_fast_forward`,
`pull_request`, `required_signatures`, `required_status_checks`.

Only `required_status_checks` is per-repo — it names this repo's actual CI job
names. The canonical per-repo lists, the derivation method, and the Tier 2
hardening roadmap live in juniper-ml:

`notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md`

**Operational notes**

- `strict_required_status_checks_policy` is **on** — a PR must be current with
  `main` to merge. Retained deliberately as the anti-storm guarantee.
- `require_last_push_approval` is **off**. With `required_approving_review_count: 0`
  it added no review workflow and made any owner-authored PR unmergeable except by
  admin bypass.
- An unsigned commit anywhere on a PR branch blocks the merge under
  `required_signatures`. Squash-merge does **not** rescue it. Commits made through
  the REST contents API are unsigned; the GraphQL `createCommitOnBranch` mutation
  produces a signed commit.
- If a PR sits at `CLEAN` without merging, **re-arm auto-merge** — a ruleset edit is
  not a PR event, so nothing re-evaluates the queue. Do not admin-merge.
"""

MUTATION = (
    "mutation($input: CreateCommitOnBranchInput!) "
    "{ createCommitOnBranch(input: $input) { commit { oid signature { isValid } } } }"
)


def gh(args: list[str]) -> str:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=TIMEOUT, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:4])}… failed: {proc.stderr.strip()[:300]}")
    return proc.stdout.strip()


def main_sha(repo: str) -> str:
    return gh(["api", f"/repos/{OWNER}/{repo}/git/ref/heads/main", "--jq", ".object.sha"])


def probe(repo: str, code: str, execute: bool) -> dict:
    path = f"notes/JUNIPER_2026-08-12_JUNIPER-{code}_BRANCH-PROTECTION-VALIDATION.md"
    sha = main_sha(repo)
    if not execute:
        return {"repo": repo, "action": "DRY-RUN", "base": sha[:8], "path": path}

    # 1. branch off main (idempotent: a pre-existing ref is reused as-is)
    try:
        gh(["api", "-X", "POST", f"/repos/{OWNER}/{repo}/git/refs",
            "-f", f"ref=refs/heads/{BRANCH}", "-f", f"sha={sha}", "--jq", ".ref"])
    except RuntimeError as exc:
        if "already exists" not in str(exc).lower():
            raise

    # 2. signed commit via GraphQL (REST contents would be UNSIGNED -- see module docstring)
    contents = base64.b64encode(DOC.format(repo=repo).encode()).decode()
    payload = {
        "query": MUTATION,
        "variables": {
            "input": {
                "branch": {"repositoryNameWithOwner": f"{OWNER}/{repo}", "branchName": BRANCH},
                "message": {"headline": COMMIT_MSG},
                "expectedHeadOid": sha,
                "fileChanges": {"additions": [{"path": path, "contents": contents}]},
            }
        },
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(payload, fh)
        tmp = fh.name
    try:
        raw = gh(["api", "graphql", "--input", tmp])
    finally:
        Path(tmp).unlink(missing_ok=True)

    data = json.loads(raw)
    if data.get("errors"):
        raise RuntimeError(f"graphql: {json.dumps(data['errors'])[:300]}")
    commit = data["data"]["createCommitOnBranch"]["commit"]

    # 3. open the PR
    url = gh(["pr", "create", "--repo", f"{OWNER}/{repo}", "--base", "main",
              "--head", BRANCH, "--title", COMMIT_MSG, "--body", BODY])
    return {
        "repo": repo,
        "action": "OPENED",
        "commit": commit["oid"][:8],
        "signed": commit["signature"]["isValid"],
        "pr": url.splitlines()[-1],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", action="store_true", help="actually create branches/commits/PRs")
    ap.add_argument("--repo", help="limit to one repo")
    args = ap.parse_args()

    targets = {args.repo: REPOS[args.repo]} if args.repo else REPOS
    rc = 0
    for repo, code in targets.items():
        try:
            print(json.dumps(probe(repo, code, args.execute)))
        except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as exc:
            print(json.dumps({"repo": repo, "action": "ERROR", "error": str(exc)[:300]}))
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
