#!/usr/bin/env python3
"""Probe: is `--advisory` present in the *invocation args* of the memory-budget
size check, as opposed to merely somewhere in the workflow file's prose?

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc verification (P5 step d, precondition 2)
Author:      Paul Calnon
License:     MIT

Why this exists: `2026-08-26_p5_fleet_state.py` sets `advisory_flag` with
`"--advisory" in wf` over the WHOLE workflow text. After the de-advisory PRs
landed, every repo still mentions `--advisory` in a comment explaining its
removal, and juniper-ml keeps a real `--advisory` on the *Relocation
Completeness* invocation. So the census column reads True fleet-wide and is
uninformative. This probe reconstructs each shell continuation block that
invokes memory_budget_check.py and reports the flag per invocation.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess  # nosec B404 -- fixed-argv `gh api` calls only; nothing is shell-interpolated
import sys

REPOS = [
    ("juniper-canopy", ".github/workflows/ci.yml"),
    ("juniper-cascor", ".github/workflows/ci.yml"),
    ("juniper-cascor-client", ".github/workflows/ci.yml"),
    ("juniper-recurrence", ".github/workflows/memory-budget.yml"),
    ("juniper-data-client", ".github/workflows/ci.yml"),
    ("juniper-data", ".github/workflows/ci.yml"),
    ("juniper-cascor-worker", ".github/workflows/ci.yml"),
    ("juniper-deploy", ".github/workflows/ci.yml"),
    ("juniper-ml", ".github/workflows/ci.yml"),
]


def contents(repo, path):
    """Decoded text of a file on the repo's default branch, or None if genuinely absent (404).

    Any other failure raises: a probe that silently reports "no live invocation found" because
    the API rate-limited would read as a clean de-advisory result, which is the exact failure
    this script exists to rule out.
    """
    p = subprocess.run(  # nosec B603 B607 -- fixed argv, gh on PATH by policy
        ["gh", "api", "repos/pcalnon/%s/contents/%s" % (repo, path), "--jq", ".content"],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        err = (p.stderr or p.stdout).strip()
        if "HTTP 404" in err or '"status":"404"' in err:
            return None
        raise RuntimeError("gh api %s/%s failed: %s" % (repo, path, err[:300]))
    return base64.b64decode(p.stdout.strip()).decode("utf-8", "replace")


def invocations(text):
    """Return each memory_budget_check.py invocation with its full arg list.

    A shell invocation is the starting line plus every following line while the
    previous line ends in a backslash continuation.
    """
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        if "memory_budget_check.py" not in line:
            continue
        stripped = line.strip()
        # Skip comment-only lines and unittest/test references.
        if stripped.startswith("#") or "unittest" in line:
            continue
        block = [line]
        j = i
        while lines[j].rstrip().endswith("\\") and j + 1 < len(lines):
            j += 1
            block.append(lines[j])
        # Strip trailing inline comments from each arg line before flag scan.
        args = "\n".join(re.sub(r"\s+#.*$", "", b) for b in block)
        out.append(
            {
                "line": i + 1,
                "advisory": "--advisory" in args,
                "ratchet": "--ratchet" in args,
                "args": " ".join(a.strip().rstrip("\\").strip() for a in block),
            }
        )
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", metavar="PATH", default=None, help="also write the raw per-invocation JSON here")
    ns = ap.parse_args()
    results = []
    bad = 0
    for repo, wf_path in REPOS:
        wf = contents(repo, wf_path)
        if wf is None:
            print("%-22s WORKFLOW NOT FOUND: %s" % (repo, wf_path))
            bad += 1
            continue
        prose_hits = wf.count("--advisory")
        invs = invocations(wf)
        results.append(
            {
                "repo": repo,
                "workflow": wf_path,
                "prose_occurrences": prose_hits,
                "invocations": invs,
            }
        )
        print("\n=== %s  (%s)" % (repo, wf_path))
        print("    '--advisory' occurrences anywhere in file: %d" % prose_hits)
        if not invs:
            print("    !! no live invocation found")
            bad += 1
        for inv in invs:
            tag = "ADVISORY" if inv["advisory"] else "BLOCKING"
            print("    L%-5d %-8s  %s" % (inv["line"], tag, inv["args"][:150]))
    print("\n" + "=" * 70)
    print("SIZE-CHECK VERDICT (first non-relocation invocation per repo):")
    for r in results:
        size_invs = [i for i in r["invocations"] if "--relocation" not in i["args"]]
        primary = size_invs[0] if size_invs else None
        if primary is None:
            print("  %-22s ?? could not isolate size invocation" % r["repo"])
            bad += 1
            continue
        state = "ADVISORY (NOT de-advisoried)" if primary["advisory"] else "BLOCKING (de-advisoried)"
        if primary["advisory"]:
            bad += 1
        print("  %-22s %s" % (r["repo"], state))
    if ns.out:
        with open(ns.out, "w") as fh:
            json.dump(results, fh, indent=2)
        print("\nraw -> %s" % ns.out)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
