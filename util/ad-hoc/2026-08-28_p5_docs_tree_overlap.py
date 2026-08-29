#!/usr/bin/env python3
"""Does a repo's AGENTS.md already duplicate its docs/ tree, section by section?

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc analysis (plan §P5 step e — scoping the canopy / cascor cuts)
Author:      Paul Calnon
License:     MIT

Why this matters for the cut. The three cuts shipped on 2026-08-28 relocated into an existing
`docs/REFERENCE.md` that was a genuine CONTENT file. canopy's REFERENCE.md is not: it says outright
that it "serves as a central index ... Each section links to the detailed reference document",
and canopy keeps the real material under `docs/api/`, `docs/testing/`, `docs/ci_cd/` and friends.
cascor has no REFERENCE.md at all but does have `docs/{api,ci_cd,install,overview,source,testing}`.

So for these two the question is not "where do we move this prose" but "is this prose already
somewhere else". Where it is, the cut is a DELETION plus a pointer at the existing document --
cheaper, and it removes a second copy that can drift. Where it is not, it is a real relocation and
needs a destination decision.

Method: per `## ` section of AGENTS.md, take substantive lines (non-blank, non-heading,
>= --min-chars after whitespace normalisation, fenced code EXCLUDED) and ask what fraction already
appears anywhere in the repo's docs/**/*.md. Reports the best-matching single document too, since
"scattered across five files" and "all in one file" call for different actions.

Fence handling is CommonMark-correct on purpose: a naive ```-toggle mis-parsed juniper-canopy's
AGENTS.md, which wraps three-backtick examples in FOUR-backtick fences -- it swallowed 13 real
headings and invented two 15K "sections" out of code samples.

Usage:
    python3 util/ad-hoc/2026-08-28_p5_docs_tree_overlap.py juniper-canopy juniper-cascor
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess  # nosec B404 -- fixed-argv `gh api` calls only; nothing is shell-interpolated
import sys


def gh(args: list[str]) -> str:
    p = subprocess.run(["gh", *args], capture_output=True, text=True)  # nosec B603 B607 -- fixed argv
    if p.returncode != 0:
        err = (p.stderr or p.stdout).strip()
        if "HTTP 404" in err or '"status":"404"' in err:
            return ""
        raise RuntimeError(f"gh {' '.join(args)}: {err[:300]}")
    return p.stdout


def blob(repo: str, path: str) -> str:
    out = gh(["api", f"repos/pcalnon/{repo}/contents/{path}?ref=main", "--jq", ".content"])
    return base64.b64decode(out.strip()).decode("utf-8", "replace") if out.strip() else ""


def md_tree(repo: str, prefix: str = "docs/") -> list[str]:
    """Every .md path under `prefix` on main, via the recursive trees API (one call)."""
    out = gh(["api", f"repos/pcalnon/{repo}/git/trees/main?recursive=1"])
    tree = json.loads(out).get("tree", []) if out else []
    return [n["path"] for n in tree
            if n.get("type") == "blob" and n["path"].startswith(prefix) and n["path"].endswith(".md")]


def fence_mask(lines: list[str]) -> list[bool]:
    """True where a line sits inside a fenced block (CommonMark: close needs >= open ticks, no info)."""
    mask = [False] * len(lines)
    char, count = None, 0
    for i, raw in enumerate(lines):
        s = raw.lstrip()
        indent = len(raw) - len(s)
        m = re.match(r"^(`{3,}|~{3,})(.*)$", s) if indent <= 3 else None
        if m is None:
            mask[i] = char is not None
            continue
        run, info = m.group(1), m.group(2).strip()
        if char is None:
            char, count = run[0], len(run)
        elif run[0] == char and len(run) >= count and not info:
            char, count = None, 0
        else:
            mask[i] = True
    return mask


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def substantive(lines: list[str], min_chars: int) -> list[str]:
    inside = fence_mask(lines)
    out = []
    for i, ln in enumerate(lines):
        if inside[i]:
            continue
        n = norm(ln)
        if not n or n.startswith("#") or n.startswith("|") or len(n) < min_chars:
            continue
        out.append(n)
    return out


def sections(text: str) -> list[tuple[str, list[str]]]:
    lines = text.splitlines()
    inside = fence_mask(lines)
    out, title, buf = [], None, []
    for i, ln in enumerate(lines):
        if not inside[i] and ln.startswith("## "):
            if title is not None:
                out.append((title, buf))
            title, buf = ln[3:].strip(), []
            continue
        if title is not None:
            buf.append(ln)
    if title is not None:
        out.append((title, buf))
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repos", nargs="+")
    ap.add_argument("--min-chars", type=int, default=40)
    ap.add_argument("--prefix", default="docs/")
    ns = ap.parse_args(argv)

    for repo in ns.repos:
        agents = blob(repo, "AGENTS.md")
        if not agents:
            print(f"\n### {repo}: no AGENTS.md")
            continue
        paths = md_tree(repo, ns.prefix)
        per_doc = {}
        pool = set()
        for p in paths:
            s = set(substantive(blob(repo, p).splitlines(), ns.min_chars))
            per_doc[p] = s
            pool |= s
        print(f"\n### {repo}   AGENTS.md {len(agents):,} chars   "
              f"{len(paths)} markdown files under {ns.prefix} ({len(pool):,} distinct substantive lines)")
        print(f"    {'dup%':>5} {'lines':>6} {'chars':>7}  section  ->  best single match")
        secs = sections(agents)
        tot_dup = tot_all = 0
        for title, body in sorted(secs, key=lambda kv: -len("\n".join(kv[1]))):
            subs = substantive(body, ns.min_chars)
            if not subs:
                continue
            dup = sum(1 for ln in subs if ln in pool)
            tot_dup += dup
            tot_all += len(subs)
            best, bestn = "-", 0
            for p, s in per_doc.items():
                n = sum(1 for ln in subs if ln in s)
                if n > bestn:
                    best, bestn = p, n
            pct = dup / len(subs) * 100
            tag = " <== ALREADY DOCUMENTED" if pct >= 60 else (" <- partial" if pct >= 25 else "")
            print(f"    {pct:>4.0f}% {len(subs):>6} {len(chr(10).join(body)):>7}  {title[:44]:<44}"
                  f"  {best.replace(ns.prefix, '') if best != '-' else '-'}"
                  f"{f' ({bestn}/{len(subs)})' if bestn else ''}{tag}")
        if tot_all:
            print(f"\n    OVERALL: {tot_dup}/{tot_all} substantive AGENTS.md lines ({tot_dup / tot_all * 100:.0f}%) "
                  f"already appear under {ns.prefix}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
