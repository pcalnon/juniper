#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-08-25
Status:      ad-hoc -- migration (P5 fleet rollout)
Retire when: every repo in the P5 rollout carries the memory-budget gate, or the
             gate moves into a shared package and stops being copied per-repo.

P5 porting helper: adapt juniper-ml's ``test_memory_budget_check.py`` for a sibling
repo, and splice the ``memory-budget`` job into that repo's ``ci.yml``.

Plan: ``notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`` §P5.

Two adaptations are needed, and BOTH fail in ways that do not point at themselves:

**Repo root depth.** juniper-ml keeps tests at ``tests/`` so the root is
``parents[1]``. canopy and cascor keep them at ``src/tests/`` (``testpaths``), so
the root is ``parents[2]``. Getting this wrong does not raise -- ``REPO_ROOT``
silently resolves to ``src/`` and the suite fails later looking for
``src/conf/memory_budget.json``, which reads like a missing config rather than a
bad path.

**Bandit strictness differs across the fleet.** The byte-identical file passes
juniper-ml's bandit and FAILS juniper-cascor's on B603/B607 at three subprocess
call sites. All three are fixed-argv calls into a ``TemporaryDirectory``, so the
suppression is genuine rather than convenient -- but it has to be written, and the
house idiom is an inline ``# nosec`` naming the codes AND the reason. A bare
``# nosec`` would be the "plausible justification hides a real defect" shape.

Job splicing is a TEXT operation, deliberately: a PyYAML round-trip would strip
every comment, and in these workflows the comments carry the rationale (why the
job is standalone, why a flag is absent) that is the actual institutional memory.

``measure-growth`` exists because P5's ordering rule is "order by RATE, not size" and
a rate is not obtainable from any other tool here. Unlike ``MEMORY.md``, a repo's
``AGENTS.md`` IS tracked, so the burn can be measured rather than assumed -- which is
how cascor (730 chars/day) turned out to be nine times canopy's rate (81/day) despite
having the smaller file.

Usage:
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py adapt-test <test.py> --depth 2
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py insert-job <ci.yml> <job.yml> --before required-checks
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth <repo-path> --days 30 [--ref origin/main]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEPTH_RE = re.compile(r"^REPO_ROOT = Path\(__file__\)\.resolve\(\)\.parents\[(\d+)\]$", re.MULTILINE)

# (marker matched at a call site, nosec comment to append to the `subprocess.run(` line)
#
# SEPARATE THE CODES WITH SPACES, NOT COMMAS. Measured against bandit 1.9.4:
# `# nosec B603,B607` suppressed B607 and left B603 still reported, while
# `# nosec B603 B607` suppressed both. The comma form is the dangerous one precisely
# because it PARTIALLY works -- the count drops, so it reads as though the annotation
# took effect.
#
# juniper-ml's own copy uses the comma form and passes, but NOT because the annotation
# works there: ml's hook passes `--skip=B101,B108,B311,B404,B603,B604,B607` and is scoped
# to `^(scripts|tests)/`, so B603/B607 are disabled repo-wide and every comma-form
# suppression in ml is INERT. Do not read ml's copy as evidence the comma form works.
NOSEC_SITES = [
    (
        '["git", "-C", str(repo), *args],',
        "  # nosec B603 B607 - fixed git argv into a TemporaryDirectory; no untrusted input",
    ),
    (
        '[sys.executable, str(MODULE_PATH), "--repo-root", str(root), "--budget", str(budget), "--base-ref", "HEAD", *extra],',
        "  # nosec B603 - sys.executable + this repo's own checker, fixed argv",
    ),
]


def adapt_test(path: Path, depth: int) -> int:
    s = path.read_text(encoding="utf-8")

    m = DEPTH_RE.search(s)
    if not m:
        print(f"error: no REPO_ROOT parents[...] line in {path}", file=sys.stderr)
        return 2
    if int(m.group(1)) != depth:
        note = (
            f"# This repo keeps tests one level deeper than juniper-ml (testpaths), so the\n"
            f"# repo root is parents[{depth}], not parents[{m.group(1)}]. Getting this wrong does not\n"
            f"# raise -- it resolves to the wrong directory and fails later as a missing config.\n"
        )
        s = DEPTH_RE.sub(note + f"REPO_ROOT = Path(__file__).resolve().parents[{depth}]", s, count=1)
        print(f"  depth: parents[{m.group(1)}] -> parents[{depth}]")
    else:
        print(f"  depth: already parents[{depth}]")

    added = 0
    out = []
    for line in s.splitlines(keepends=True):
        out.append(line)
        for marker, comment in NOSEC_SITES:
            if line.strip() == marker.strip() and "nosec" not in out[-2]:
                # Attach the suppression to the subprocess.run( line above the argv.
                prev = out[-2].rstrip("\n")
                out[-2] = prev + comment + "\n"
                added += 1
                break
    s = "".join(out)
    print(f"  nosec: annotated {added} call site(s)")

    path.write_text(s, encoding="utf-8")
    return 0


def insert_job(workflow: Path, block: Path, before: str) -> int:
    text = workflow.read_text(encoding="utf-8")
    job_text = block.read_text(encoding="utf-8")

    anchor = f"\n  {before}:\n"
    if anchor not in text:
        print(f"error: job key {before!r} not found at 2-space indent in {workflow}", file=sys.stderr)
        return 2
    if job_text.strip().splitlines()[-1].strip().endswith(":"):
        print("error: job block looks truncated (ends on a bare key)", file=sys.stderr)
        return 2

    idx = text.index(anchor)
    head = text[: idx + 1]
    lines = head.splitlines(keepends=True)
    cut = len(lines)
    # Walk back over the anchor job's banner comment so the new job lands BEFORE the
    # banner, not wedged between a banner and the job it describes.
    while cut > 0 and lines[cut - 1].lstrip().startswith("#"):
        cut -= 1

    out = "".join(lines[:cut]) + job_text + "".join(lines[cut:]) + text[idx + 1 :]
    workflow.write_text(out, encoding="utf-8")
    print(f"inserted {block.name} before job {before!r} in {workflow.name}")
    return 0


def measure_growth(repo: Path, days: int, ref: str = "HEAD") -> int:
    """Report a repo's AGENTS.md burn from git, so a ceiling's slack can be sized.

    Every figure a ceiling depends on goes stale fast -- the plan said canopy was
    94,373, a handoff said 93,151, and it was 95,133 when the gate was seeded. So
    this measures rather than reports: run it, do not quote it.

    ``ref`` defaults to the checkout's HEAD. Pass ``--ref origin/main`` (after a fetch)
    when the checkout may be behind -- on 2026-08-25 one sibling checkout was two
    commits behind its own main, and a measurement is only as current as the ref it
    reads.
    """
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    p = subprocess.run(
        ["git", "-C", str(repo), "log", ref, f"--since={since}", "--format=%H", "--reverse", "--", "AGENTS.md"],
        capture_output=True,
        text=True,
        check=False,
    )
    if p.returncode != 0:
        print(f"error: git log failed in {repo}: {p.stderr.strip()}", file=sys.stderr)
        return 2
    shas = p.stdout.split()
    if len(shas) < 2:
        print(f"only {len(shas)} commit(s) touched AGENTS.md since {since}; widen --days")
        return 0

    sizes = []
    for sha in shas:
        out = subprocess.run(
            ["git", "-C", str(repo), "show", f"{sha}:AGENTS.md"],
            capture_output=True,
            check=False,
        )
        if out.returncode == 0:
            sizes.append(len(out.stdout.decode("utf-8", errors="replace")))
    if len(sizes) < 2:
        print("AGENTS.md not resolvable at enough commits; widen --days")
        return 0

    deltas = [b - a for a, b in zip(sizes, sizes[1:])]
    grew = sorted(d for d in deltas if d > 0)
    shrank = [d for d in deltas if d < 0]
    net = sizes[-1] - sizes[0]

    print(f"repo    : {repo.name}  ({ref})")
    print(f"window  : last {days} days, {len(sizes)} commits touching AGENTS.md")
    print(f"size    : {sizes[0]} -> {sizes[-1]}   net {net:+}")
    print(f"rate    : {net / max(days, 1):.0f} chars/day")
    print(f"commits : {len(grew)} grew, {len(shrank)} shrank")
    if grew:
        median = grew[len(grew) // 2]
        p90 = grew[max(0, int(len(grew) * 0.9) - 1)]
        print(f"growth  : median {median}  p90 {p90}  max {grew[-1]}")
        print()
        print(f"=> slack must absorb a single growing commit: >= {grew[-1]} covers the largest seen.")
        print("   A ceiling with ZERO slack fires on the next growing PR by construction.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("adapt-test", help="fix repo-root depth + add house nosec markers")
    a.add_argument("path", type=Path)
    a.add_argument("--depth", type=int, default=2)

    i = sub.add_parser("insert-job", help="splice a job block before a named job")
    i.add_argument("workflow", type=Path)
    i.add_argument("block", type=Path)
    i.add_argument("--before", default="required-checks")

    g = sub.add_parser("measure-growth", help="AGENTS.md burn from git, for sizing a ceiling's slack")
    g.add_argument("repo", type=Path)
    g.add_argument("--days", type=int, default=30)
    g.add_argument("--ref", default="HEAD", help="ref whose history to measure (default HEAD; use origin/main after a fetch when the checkout may be behind)")

    args = ap.parse_args()
    if args.cmd == "adapt-test":
        return adapt_test(args.path, args.depth)
    if args.cmd == "measure-growth":
        return measure_growth(args.repo, args.days, args.ref)
    return insert_job(args.workflow, args.block, args.before)


if __name__ == "__main__":
    sys.exit(main())
