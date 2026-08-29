#!/usr/bin/env python3
"""Which AGENTS.md sections are ALREADY duplicated in docs/REFERENCE.md?

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc analysis (plan §P5 step e — the cut)
Author:      Paul Calnon
License:     MIT

Why this exists: several destination REFERENCE.md files already carry a `## `
section with the SAME NAME as one still resident in AGENTS.md (data-client has
"Exception Hierarchy", "Testing Utilities" and "Configuration Reference" in
both). That changes the cut for those sections from a RELOCATION into a plain
DELETION-plus-pointer, and it changes the tooling: the relocate script refuses
when the destination section already exists.

It also changes the size story. Duplicated prose is loaded twice per session,
so removing it is pure win with no destination growth at all.

Compares substantive lines (non-blank, non-heading, length >= --min-chars,
whitespace-normalised) and reports, per same-named section pair, what fraction
of the AGENTS.md lines already appear anywhere in the destination file.

Usage:
    python3 util/ad-hoc/2026-08-28_p5_cut_overlap_probe.py juniper-data-client [...]
"""
from __future__ import annotations

import argparse
import base64
import re
import subprocess  # nosec B404 -- fixed-argv `gh api` calls only; nothing is shell-interpolated
import sys

DEFAULT_REPOS = ["juniper-cascor-client", "juniper-data", "juniper-data-client"]


def contents(repo: str, path: str) -> str | None:
    p = subprocess.run(  # nosec B603 B607 -- fixed argv, gh on PATH by policy
        ["gh", "api", f"repos/pcalnon/{repo}/contents/{path}?ref=main", "--jq", ".content"],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        err = (p.stderr or p.stdout).strip()
        if "HTTP 404" in err or '"status":"404"' in err:
            return None
        raise RuntimeError(f"gh api {repo}/{path}: {err[:300]}")
    return base64.b64decode(p.stdout.strip()).decode("utf-8", "replace")


def norm(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def sections(text: str) -> dict[str, list[str]]:
    """title -> body lines, for each top-level `## ` section (fence-aware)."""
    out: dict[str, list[str]] = {}
    title = None
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            if title is not None:
                out[title].append(line)
            continue
        if not in_fence and line.startswith("## "):
            title = line[3:].strip()
            out[title] = []
            continue
        if title is not None:
            out[title].append(line)
    return out


def substantive(lines: list[str], min_chars: int) -> list[str]:
    keep = []
    for ln in lines:
        n = norm(ln)
        if not n or n.startswith("#") or len(n) < min_chars:
            continue
        keep.append(n)
    return keep


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repos", nargs="*", default=None)
    ap.add_argument("--min-chars", type=int, default=40)
    ns = ap.parse_args(argv)
    for repo in ns.repos or DEFAULT_REPOS:
        agents = contents(repo, "AGENTS.md")
        ref = contents(repo, "docs/REFERENCE.md")
        if agents is None or ref is None:
            print(f"\n### {repo}: missing AGENTS.md or docs/REFERENCE.md")
            continue
        a_secs = sections(agents)
        r_secs = sections(ref)
        ref_pool = set(substantive(ref.splitlines(), ns.min_chars))
        shared = [t for t in a_secs if t in r_secs]
        print(f"\n### {repo}")
        print(f"    AGENTS.md {len(agents):,} chars / {len(a_secs)} sections   "
              f"REFERENCE.md {len(ref):,} chars / {len(r_secs)} sections")
        print(f"    same-named sections in both: {shared if shared else 'NONE'}")
        print(f"    {'dup%':>6} {'lines':>6} {'chars':>8}  section (all AGENTS.md sections vs the WHOLE destination)")
        for title, body in sorted(a_secs.items(), key=lambda kv: -len("\n".join(kv[1]))):
            subs = substantive(body, ns.min_chars)
            if not subs:
                continue
            dup = sum(1 for ln in subs if ln in ref_pool)
            pct = dup / len(subs) * 100
            mark = " <== already in REFERENCE.md" if pct >= 60 else (" <- partial" if pct >= 20 else "")
            print(f"    {pct:>5.0f}% {len(subs):>6} {len('\n'.join(body)):>8}  {title[:52]}{mark}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
