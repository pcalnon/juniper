#!/usr/bin/env python3
"""2026-09-05_fleet_anchor_collision.py -- markdown heading/anchor collisions across fleet PRs.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc analysis (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

Two gates that a per-PR merge simulation cannot see, both load-bearing here:

1. ``.markdownlint.yaml`` sets ``no-duplicate-heading: siblings_only: true``, so two
   PRs that each add ``### Operator pitfalls`` under DIFFERENT parents both lint
   clean and ship two sections whose GitHub anchors collide (``#operator-pitfalls``
   and ``#operator-pitfalls-1``). ``docs/REFERENCE.md`` already carries 6 such
   headings on main, so the ambiguity compounds silently.

2. ``conf/soak_probes.json`` points every probe at ``docs/REFERENCE.md#<anchor>``
   and ``util/soak_ledger.py`` validates that each anchor RESOLVES. A consolidation
   or a duplicate-heading merge that renames or duplicates a target heading breaks
   those pointers, and a "every added line is present" check sees nothing wrong.

So: extract each PR's ADDED markdown headings from its diff, slugify them the way
GitHub does, and report (a) collisions between PRs, (b) collisions with headings
already on main, and (c) any probe anchor whose target heading a PR renames.

Usage:
    python util/ad-hoc/2026-09-05_fleet_anchor_collision.py \
        --repo /path/to/juniper-ml --pr 1701 --pr 1705 [--probes conf/soak_probes.json]
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess  # nosec B404 -- fixed argv gh/git invocations, no shell
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^\+(#{2,6})\s+(.*)")
MAIN_HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)")
DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.*)$")


def slugify(text: str) -> str:
    """Anchor rule, copied VERBATIM from ``util/soak_ledger.py:_slugs`` (the repo's authority).

    Do not "improve" this. An earlier version of this script collapsed whitespace
    runs and stripped underscores; it therefore reported two live probe anchors
    (``#multi-site--multi-interpreter-versions``, ``#non-empty-pidfile-stop-path-validate_pid``)
    as MISSING from ``docs/REFERENCE.md`` when both headings are present at
    ``REFERENCE.md:765`` and ``:409``. Each space becomes its OWN dash (so ``a / b``
    yields ``a--b``) and ``_`` survives.
    """
    s = text.strip().lower()
    return re.sub(r"[^a-z0-9 _-]", "", s).replace(" ", "-")


def pr_added_headings(repo: Path, pr: int) -> dict:
    """{file: [(level, text, slug)]} for markdown headings ADDED by this PR."""
    cp = subprocess.run(  # nosec B603
        ["gh", "pr", "diff", str(pr)], cwd=repo, capture_output=True, text=True, check=False
    )
    if cp.returncode != 0:
        print(f"warn: gh pr diff {pr} failed: {cp.stderr.strip()[:200]}", file=sys.stderr)
        return {}
    out: dict = collections.defaultdict(list)
    current = None
    for line in cp.stdout.splitlines():
        m = DIFF_FILE_RE.match(line)
        if m:
            current = m.group(1)
            continue
        if current and current.endswith(".md"):
            h = HEADING_RE.match(line)
            if h:
                text = h.group(2)
                out[current].append((len(h.group(1)), text, slugify(text)))
    return dict(out)


def main_headings(repo: Path, path: str) -> collections.Counter:
    f = repo / path
    if not f.is_file():
        return collections.Counter()
    c: collections.Counter = collections.Counter()
    for line in f.read_text(errors="replace").splitlines():
        m = MAIN_HEADING_RE.match(line)
        if m:
            c[slugify(m.group(2))] += 1
    return c


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, action="append", required=True)
    ap.add_argument("--probes", default=None, help="conf/soak_probes.json to cross-check anchors")
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()

    per_pr = {pr: pr_added_headings(repo, pr) for pr in args.pr}

    # slug -> {file: [prs]}
    slug_owners: dict = collections.defaultdict(lambda: collections.defaultdict(list))
    for pr, files in per_pr.items():
        for path, heads in files.items():
            for _lvl, _txt, slug in heads:
                slug_owners[slug][path].append(pr)

    print("=== PR-vs-PR anchor collisions ===")
    found = False
    for slug, byfile in sorted(slug_owners.items()):
        for path, prs in byfile.items():
            if len(set(prs)) > 1:
                found = True
                print(f"  COLLIDE  {path}#{slug}  <- PRs {sorted(set(prs))}")
    if not found:
        print("  none")

    print("\n=== collisions with headings already on main ===")
    found = False
    cache: dict = {}
    for slug, byfile in sorted(slug_owners.items()):
        for path, prs in byfile.items():
            if path not in cache:
                cache[path] = main_headings(repo, path)
            n = cache[path].get(slug, 0)
            if n:
                found = True
                print(f"  DUP-ON-MAIN  {path}#{slug}  already x{n} on main; added again by {sorted(set(prs))}")
    if not found:
        print("  none")

    if args.probes:
        p = Path(args.probes)
        if not p.is_absolute():
            p = repo / p
        print(f"\n=== probe anchors declared in {p.name} ===")
        try:
            probes = json.loads(p.read_text())
        except Exception as exc:  # noqa: BLE001
            print(f"  could not read: {exc}")
            return 0
        entries = probes.get("probes", probes) if isinstance(probes, dict) else probes
        targets = []
        for e in entries if isinstance(entries, list) else []:
            for v in (e.values() if isinstance(e, dict) else []):
                if isinstance(v, str) and ".md#" in v:
                    targets.append(v)
        print(f"  {len(targets)} anchor pointer(s) found")
        for t in sorted(set(targets)):
            path, _, anchor = t.partition("#")
            path = path.lstrip("./")
            if path not in cache:
                cache[path] = main_headings(repo, path)
            ok = "RESOLVES" if cache[path].get(anchor) else "MISSING"
            flag = " <-- a PR also adds this slug" if anchor in slug_owners else ""
            print(f"    [{ok}] {t}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
