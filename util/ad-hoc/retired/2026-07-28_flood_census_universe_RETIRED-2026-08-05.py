"""
Pin the Cursor-fleet PR-flood census universe: window merges + per-merge PR-files metric.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Claude (flood-remediation program, orchestrator)
Created: 2026-07-28
Status: ad-hoc — investigation
Retire when: the flood-remediation results doc (notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) is merged and the census is closed
Related: prompts/generated/JUNIPER_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION_PLAN_2026-07-28_0315.md (Task 1.0); heal PRs #838/#842/#843

Computes ONCE, for sharing across census agents C1/C2/C3:
  - window merges = git log --first-parent --merges --since=2026-07-25 --until=2026-07-29 origin/main,
    filtered to subjects starting "Merge pull request #"
  - per-merge touched files = the PR-files metric:
    git diff --name-only $(git merge-base <M>^1 <M>^2) <M>^2
  - bucket membership (tests / util / docs-any-md / doc-union-6 / ci.yml)

Emits JSON to --out (intermediate data artifact; scratchpad/tmp is fine for the DATA).
"""

import argparse
import json
import re
import subprocess

DOC_UNION_6 = [
    "AGENTS.md",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
    "docs/REFERENCE.md",
    "docs/DOCUMENTATION_OVERVIEW.md",
    "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md",
    "notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md",
]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-07-25")
    ap.add_argument("--until", default="2026-07-29")
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    head = git("rev-parse", args.ref).strip()
    log = git(
        "log", "--first-parent", "--merges",
        f"--since={args.since}", f"--until={args.until}",
        "--format=%H\x01%P\x01%s", args.ref,
    )
    merges = []
    for line in log.splitlines():
        sha, parents, subject = line.split("\x01")
        if not subject.startswith("Merge pull request #"):
            continue
        p1, p2 = parents.split()[:2]
        base = git("merge-base", p1, p2).strip()
        files = [f for f in git("diff", "--name-only", base, p2).splitlines() if f]
        m = re.match(r"Merge pull request #(\d+) from \S*?([^/\s]+/.+|\S+)$", subject)
        pr = int(re.search(r"#(\d+)", subject).group(1))
        branch = subject.split(" from ", 1)[1] if " from " in subject else ""
        branch = branch.removeprefix("pcalnon/")
        merges.append({
            "sha": sha, "pr": pr, "branch": branch, "subject": subject,
            "p1": p1, "p2": p2, "base": base, "files": files,
        })

    def bucket(pred):
        return [m["sha"] for m in merges if any(pred(f) for f in m["files"])]

    buckets = {
        "tests_touching": bucket(lambda f: f.startswith("tests/") and f.endswith(".py")),
        "util_touching": bucket(lambda f: f.startswith("util/")),
        "docs_any_md": bucket(lambda f: f.endswith(".md")),
        "doc_union6_touching": bucket(lambda f: f in DOC_UNION_6),
        "ci_yml_touching": bucket(lambda f: f == ".github/workflows/ci.yml"),
    }
    out = {
        "computed_at_head": head,
        "window": {"since": args.since, "until": args.until},
        "pr_files_metric": "git diff --name-only $(git merge-base ^1 ^2) ^2",
        "doc_union_6": DOC_UNION_6,
        "n_merges": len(merges),
        "bucket_counts": {k: len(v) for k, v in buckets.items()},
        "buckets": buckets,
        "merges": merges,
    }
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({"n_merges": len(merges), **{k: len(v) for k, v in buckets.items()}}, indent=1))


if __name__ == "__main__":
    main()
