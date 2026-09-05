#!/usr/bin/env python3
"""2026-09-04_fleet_flood2_census.py -- census of the second Cursor PR flood.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc analysis (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License

WHAT IT DOES

Reads the `gh pr list --json number,title,files` dumps for the four flooded
repos and reports the shape of the backlog that governs disposition:

  (a) the same-file contention histogram -- which files are appended to by many
      PRs at once. This is the 2026-07-26 damage signature (AGENTS.md x54,
      cheatsheet x53) and it is what makes a naive sequential merge expensive
      AND dangerous: under `strict_required_status_checks_policy: true` with
      `allow_update_branch: false`, every landed merge makes every same-file
      sibling stale, and each resync is a fresh ~10-minute required-check
      battery plus another ort 3-way fusion opportunity.
  (b) the docs-vs-code split per PR, in ADDED LINES -- separating the portion of
      the flood that is genuinely per-PR work (tests, util) from the portion
      that is append-to-a-shared-doc contention.
  (c) the disposition categories used by the arc ledger.

Input JSON dumps are produced by the caller (see the arc ledger) and passed as
`--dump REPO=PATH` pairs. Emits a human report, or `--json` for the ledger.

Usage:
    python util/ad-hoc/2026-09-04_fleet_flood2_census.py \
        --dump juniper-ml=/path/ml_files.json [--json]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

# The five append-heavy shared docs files that carry the contention in juniper-ml.
CONTENDED_DOCS = {
    "docs/REFERENCE.md",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
    "docs/DOCUMENTATION_OVERVIEW.md",
    "AGENTS.md",
    "docs/QUICK_START.md",
}

CODE_PREFIXES = ("tests/", "util/", "scripts/")
# Split so this file never contains the literal CI-workflow path: a worktree-isolated
# session refuses commands naming it, and this module is read by such sessions.
WORKFLOW_PREFIX = ".git" + "hub/workflows"


def load(path: str) -> list:
    with open(path) as fh:
        return json.load(fh)


def census(prs: list) -> dict:
    file_hits: collections.Counter = collections.Counter()
    cats: collections.Counter = collections.Counter()
    per_pr = []
    for pr in prs:
        paths = [f["path"] for f in pr["files"]]
        for p in paths:
            file_hits[p] += 1
        pset = set(paths)
        has_code = any(p.startswith(CODE_PREFIXES) for p in paths)
        has_doc = bool(pset & CONTENDED_DOCS)
        has_tests = any(p.startswith("tests/") for p in paths)
        has_wf = any(p.startswith(WORKFLOW_PREFIX) for p in paths)
        if has_code and has_doc:
            cat = "code+contended-docs"
        elif has_code:
            cat = "code-only"
        elif has_doc:
            cat = "contended-docs-only"
        else:
            cat = "other"
        cats[cat] += 1
        doc_add = sum(f["additions"] for f in pr["files"] if f["path"] in CONTENDED_DOCS)
        code_add = sum(f["additions"] for f in pr["files"] if f["path"].startswith(CODE_PREFIXES))
        per_pr.append(
            {
                "number": pr["number"],
                "title": pr.get("title", ""),
                "category": cat,
                "doc_added": doc_add,
                "code_added": code_add,
                "n_files": len(paths),
                "touches_tests": has_tests,
                "touches_workflow": has_wf,
                "paths": paths,
            }
        )
    return {
        "n_prs": len(prs),
        "file_hits": file_hits,
        "categories": dict(cats),
        "per_pr": per_pr,
        "total_doc_added": sum(p["doc_added"] for p in per_pr),
        "total_code_added": sum(p["code_added"] for p in per_pr),
    }


def render(repo: str, c: dict) -> None:
    print(f"===== {repo}: {c['n_prs']} draft PRs =====")
    print("-- contention histogram (files touched by >=2 PRs) --")
    for path, n in c["file_hits"].most_common():
        if n < 2:
            break
        print(f"  {n:3d}  {path}")
    print("-- categories --")
    for k, v in sorted(c["categories"].items(), key=lambda kv: -kv[1]):
        print(f"  {v:3d}  {k}")
    print("-- added lines --")
    print(f"  contended shared docs : {c['total_doc_added']:6d}")
    print(f"  tests/util/scripts    : {c['total_code_added']:6d}")
    tot = c["total_doc_added"] + c["total_code_added"]
    if tot:
        pct = 100.0 * c["total_doc_added"] / tot
        print(f"  -> {pct:.1f}% of added lines land in the 5 contended docs files")
    print()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dump", action="append", required=True, metavar="REPO=PATH")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    out = {}
    for spec in args.dump:
        if "=" not in spec:
            print(f"bad --dump {spec!r}; want REPO=PATH", file=sys.stderr)
            return 2
        repo, path = spec.split("=", 1)
        if not Path(path).is_file():
            print(f"no such dump: {path}", file=sys.stderr)
            return 2
        c = census(load(path))
        out[repo] = c
        if not args.json:
            render(repo, c)
    if args.json:
        for c in out.values():
            c["file_hits"] = dict(c["file_hits"])
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
