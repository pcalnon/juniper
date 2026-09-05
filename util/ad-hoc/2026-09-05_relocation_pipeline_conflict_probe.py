#!/usr/bin/env python3
"""Does an AGENTS.md relocation introduce conflicts with the open-PR pipeline?

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc verification tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-05
Status:      ad-hoc -- verification (re-run before every AGENTS.md relocation)
Retire when: a relocation gate runs this in CI, or AGENTS.md stops being a
             multi-writer file.
Related:     util/ad-hoc/2026-08-19_p3_relocate_section.py (the relocator),
             util/relocation_check.py (G3 -- completeness, NOT conflicts).

Why this exists
---------------
A relocation is judged safe by *line distance* from the open PRs' insertion
anchors -- "249 lines away, far outside git's 3-line context". That is a
prediction, not a measurement, and on 2026-09-05 it was wrong in a way that
mattered: the prediction reasoned about the SOURCE file's anchors and never
considered the DESTINATION, where the same relocation appends 89 lines into a
file that dozens of open PRs also append to.

G3 (``util/relocation_check.py``) does not answer this either. It checks that
every removed line reached the destination -- completeness of the MOVE. It says
nothing about whether the move still applies alongside the N other branches
queued against the same two files.

Why it runs a CONTROL, and why that is the whole design
------------------------------------------------------
The first version of this script reported "38 of 44 CONFLICTED" and exited 1.
That number is true and nearly useless: those PRs conflict with plain ``main``
too, because the pipeline is stale. A raw conflict count therefore answers an
adjacent question -- *"are these PRs stale?"* -- while appearing to answer the
one asked, *"does MY change break them?"*.

So the probe merges every PR head twice: once against the relocation, once
against the base alone. Only the **delta** is attributable to the change.
Measured on the 2026-09-05 Worktree-Procedures relocation: 38 conflicted in
both arms, identical membership, 0 introduced -- conflict-neutral.

Usage
-----
    python3 util/ad-hoc/2026-09-05_relocation_pipeline_conflict_probe.py
    python3 util/ad-hoc/2026-09-05_relocation_pipeline_conflict_probe.py \
        --file AGENTS.md --head HEAD --base origin/main --repo pcalnon/juniper-ml
    # raw conflicts only, no control arm (rarely what you want):
    python3 util/ad-hoc/2026-09-05_relocation_pipeline_conflict_probe.py --no-control
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def run(args: list[str], check: bool = True) -> str:
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if check and proc.returncode != 0:
        raise SystemExit(f"command failed: {' '.join(args)}\n{proc.stderr.strip()}")
    return proc.stdout


def open_prs_touching(repo: str, path: str) -> list[int]:
    """PR numbers whose file list includes `path`. Uses gh, not local refs."""
    raw = run([
        "gh", "pr", "list", "--repo", repo, "--limit", "300",
        "--json", "number,files",
    ])
    out = []
    for pr in json.loads(raw):
        if any(f.get("path") == path for f in pr.get("files", [])):
            out.append(pr["number"])
    return sorted(out, reverse=True)


def probe(prs: list[int], head_sha: str) -> tuple[set[int], dict[int, list[str]], set[int]]:
    """Three-way merge every PR head against `head_sha`.

    Returns (clean, {pr: conflicted_paths}, unfetchable).
    """
    clean: set[int] = set()
    conflicted: dict[int, list[str]] = {}
    unfetchable: set[int] = set()

    for n in prs:
        ref = f"refs/tmp/relocprobe/{n}"
        fetch = subprocess.run(
            ["git", "fetch", "-q", "origin", f"pull/{n}/head:{ref}", "--force"],
            capture_output=True, text=True, check=False,
        )
        if fetch.returncode != 0:
            unfetchable.add(n)
            continue

        proc = subprocess.run(
            ["git", "merge-tree", "--write-tree", head_sha, ref],
            capture_output=True, text=True, check=False,
        )
        subprocess.run(["git", "update-ref", "-d", ref], capture_output=True, check=False)

        if proc.returncode == 0:
            clean.add(n)
        else:
            # merge-tree prints stage-2/stage-3 index rows, then an
            # "Auto-merging <path>" / "CONFLICT (<kind>): Merge conflict in <path>"
            # block. Take only the CONFLICT lines and pull the path off the end;
            # an earlier parser here mixed `and`/`or` without parentheses and
            # emitted the raw index rows as if they were paths.
            conflicted[n] = sorted({
                ln.rsplit(" in ", 1)[-1].strip()
                for ln in proc.stdout.splitlines()
                if ln.startswith("CONFLICT") and " in " in ln
            })
    return clean, conflicted, unfetchable


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="pcalnon/juniper-ml")
    ap.add_argument("--file", default="AGENTS.md")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--limit", type=int, default=0, help="probe at most N PRs (0 = all)")
    ap.add_argument("--no-control", action="store_true",
                    help="skip the base-only control arm (raw conflicts, not the delta)")
    args = ap.parse_args()

    base_sha = run(["git", "rev-parse", args.base]).strip()
    head_sha = run(["git", "rev-parse", args.head]).strip()

    prs = open_prs_touching(args.repo, args.file)
    if args.limit:
        prs = prs[: args.limit]

    print("=== relocation pipeline conflict probe ===")
    print(f"file  : {args.file}")
    print(f"base  : {args.base} {base_sha[:8]}   (control arm)")
    print(f"head  : {args.head} {head_sha[:8]}   (the relocation)")
    print(f"probe : {len(prs)} open PRs touching {args.file}\n")

    t_clean, t_conf, t_unf = probe(prs, head_sha)

    if args.no_control:
        print(f"CLEAN {len(t_clean)}  CONFLICTED {len(t_conf)}  UNFETCHABLE {len(t_unf)}")
        for n, files in sorted(t_conf.items(), reverse=True):
            print(f"  #{n}: {', '.join(files) or '(no paths parsed)'}")
        return 1 if t_conf else 0

    c_clean, c_conf, c_unf = probe(prs, base_sha)

    introduced = sorted(set(t_conf) - set(c_conf), reverse=True)
    repaired = sorted(set(c_conf) - set(t_conf), reverse=True)
    preexisting = sorted(set(t_conf) & set(c_conf), reverse=True)

    print(f"control   ({args.base}): clean {len(c_clean)}  conflicted {len(c_conf)}")
    print(f"treatment ({args.head}): clean {len(t_clean)}  conflicted {len(t_conf)}")
    if t_unf or c_unf:
        print(f"unfetchable: {sorted(t_unf | c_unf)}")
    print()
    print(f"PRE-EXISTING conflicts (not attributable): {len(preexisting)}")
    print(f"INTRODUCED by this change                : {len(introduced)}")
    for n in introduced:
        print(f"  #{n}: {', '.join(t_conf[n]) or '(no paths parsed)'}")
    if repaired:
        print(f"REPAIRED by this change                  : {len(repaired)}  "
              f"{' '.join(f'#{n}' for n in repaired)}")

    if introduced:
        print("\nFAIL: this change introduces new conflicts with the open-PR pipeline.")
        return 1
    print(f"\nOK: conflict-neutral. {len(preexisting)} pre-existing conflicts are unchanged by it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
