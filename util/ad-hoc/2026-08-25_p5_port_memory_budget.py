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
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25).

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

The three ``render-*`` commands exist so a port never re-types a figure. Each measures the
target repo itself (``growth_stats`` over its git history, the ceiling as the character
count of its working-tree ``AGENTS.md``) and renders the job block, a standalone workflow
(for a repo with no ``ci.yml``, like juniper-recurrence), or ``conf/memory_budget.json``
from those numbers. Figures transcribed from notes were stale on the first two ports --
the plan said 94,373, a handoff said 93,151, the repo said 95,133 -- and a ceiling that is
wrong by a few hundred chars is either vacuous or fires on the wrong author.

``p90`` is nearest-rank (the ``ceil(n * 0.9)``-th sorted growth). The original floor form,
``int(n * 0.9) - 1``, indexed the SMALLEST growth at n == 2 and undershot for every n < 10;
the 2026-08-25 fleet measurement printed p90 < median for four repos. The slack
recommendation uses ``max`` either way, so port sizing was not affected -- but a number
labelled p90 that sits below the median is exactly the kind of figure that gets
transcribed into a note and believed.

Usage:
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py adapt-test <test.py> --depth 2 \\
        [--sub-project juniper-x] [--header-version 0.4.2|none] [--pytest-marker unit]
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py insert-job <ci.yml> <job.yml> --before required-checks
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth <repo-path> --days 30
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py render-job <repo-path> --pyvar PYTHON_TEST_VERSION \\
        [--match-pins <that repo's ci.yml>] --out job.yml
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py render-workflow <repo-path> --python 3.14 --out memory-budget.yml
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py render-config <repo-path> --out conf/memory_budget.json
"""

from __future__ import annotations

import argparse
import json
import math
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

# The import itself: B404 fires in the client/worker repos' tests-scope bandit hooks (found on
# the cascor-worker port; ml's hook skips B404 so ml's copy never shows it).
IMPORT_NOSEC = (
    "import subprocess",
    "  # nosec B404 - subprocess IS the interface under test: the checker is driven as a CLI with a fixed argv",
)


MARKER_ANCHOR = "from tempfile import TemporaryDirectory\n"
MARKER_BLOCK = (
    "\nimport pytest\n\n"
    "# This repo's unit lane selects tests by marker (`-m`), so an unmarked suite is silently\n"
    "# DESELECTED -- a vacuous port. --strict-markers means the marker must be one pyproject\n"
    "# registers; `{marker}` is.\n"
    "pytestmark = pytest.mark.{marker}\n"
)


def adapt_test(path: Path, depth: int, sub_project: str | None = None, header_version: str | None = None, pytest_marker: str | None = None) -> int:
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

    # Header fields. The `Version:` line cuts both ways across the fleet: cascor FORBIDS it
    # repo-wide (BUG-CC-04, a test in a different file), juniper-data-client REQUIRES it to
    # equal the package version (tests/test_file_header_versions.py). Pre-commit sees neither.
    if sub_project:
        s, n = re.subn(r"^Sub-Project: .*$", f"Sub-Project: {sub_project}", s, count=1, flags=re.MULTILINE)
        print(f"  sub-project: {'-> ' + sub_project if n else 'NO Sub-Project header line'}")
    if header_version:
        if header_version.lower() == "none":
            s, n = re.subn(r"^Version:[ \t]+\S+\n", "", s, count=1, flags=re.MULTILINE)
            print(f"  version: header line {'removed' if n else 'already absent'}")
        else:
            s, n = re.subn(r"^(Version:[ \t]+)\S+$", rf"\g<1>{header_version}", s, count=1, flags=re.MULTILINE)
            print(f"  version: {'-> ' + header_version if n else 'NO Version header line'}")

    # Marker-selected lanes (juniper-data: `-m "unit and not slow"`) silently DESELECT an
    # unmarked unittest module -- the port passes CI by running nothing.
    if pytest_marker:
        if "pytestmark" in s:
            print("  marker: already present")
        elif MARKER_ANCHOR not in s:
            print(f"error: marker anchor {MARKER_ANCHOR.strip()!r} not found in {path}", file=sys.stderr)
            return 2
        else:
            s = s.replace(MARKER_ANCHOR, MARKER_ANCHOR + MARKER_BLOCK.format(marker=pytest_marker), 1)
            print(f"  marker: pytestmark = pytest.mark.{pytest_marker}")

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
    # B404 (import subprocess) is raised by the tests-scope bandit hook in the client and
    # worker repos (their skip lists stop at B101/B104/B108/B110/B311; ml's includes B404).
    # Annotate the import line itself -- the site IS the interface under test.
    if IMPORT_NOSEC[0] + "\n" in s:
        s = s.replace(IMPORT_NOSEC[0] + "\n", IMPORT_NOSEC[0] + IMPORT_NOSEC[1] + "\n", 1)
        added += 1
    print(f"  nosec: annotated {added} site(s)")

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
    # Idempotence guard: a re-run (or a second session) must not splice a duplicate job key --
    # YAML keeps the LAST duplicate silently, so the first copy's rationale would vanish.
    key = re.search(r"^  ([A-Za-z0-9_-]+):$", job_text, re.MULTILINE)
    if key and f"\n  {key.group(1)}:\n" in text:
        print(f"error: job {key.group(1)!r} is already present in {workflow}; refusing a second copy", file=sys.stderr)
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


class GrowthError(RuntimeError):
    """git could not be read in the target repo (distinct from "too few commits")."""


def stats_from_sizes(sizes: list[int], days: int, repo_name: str = "") -> dict:
    """Burn statistics from a chronological list of AGENTS.md sizes (chars).

    ``p90`` is nearest-rank: the smallest growth that at least 90% of the growing commits
    sit at or below (the ``ceil(n * 0.9)``-th of the sorted growths). ``max`` is what slack
    is sized from; p90 is reported because a reader will size from it anyway.
    """
    deltas = [b - a for a, b in zip(sizes, sizes[1:])]
    grew = sorted(d for d in deltas if d > 0)
    shrank = [d for d in deltas if d < 0]
    net = sizes[-1] - sizes[0]
    stats = {
        "repo": repo_name,
        "days": days,
        "commits": len(sizes),
        "start": sizes[0],
        "end": sizes[-1],
        "net": net,
        "rate": net / max(days, 1),
        "grew": len(grew),
        "shrank": len(shrank),
        "median": None,
        "p90": None,
        "max": None,
    }
    if grew:
        stats["median"] = grew[len(grew) // 2]
        stats["p90"] = grew[min(len(grew) - 1, max(0, math.ceil(len(grew) * 0.9) - 1))]
        stats["max"] = grew[-1]
    return stats


def growth_stats(repo: Path, days: int) -> dict | None:
    """AGENTS.md burn over the last ``days`` days, measured from the repo's own git history.

    Returns None (after saying why) when fewer than two commits touched the file in the
    window. Raises GrowthError when git itself fails, so a missing repo is never reported
    as "no growth".
    """
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    p = subprocess.run(
        ["git", "-C", str(repo), "log", f"--since={since}", "--format=%H", "--reverse", "--", "AGENTS.md"],
        capture_output=True,
        text=True,
        check=False,
    )
    if p.returncode != 0:
        raise GrowthError(f"git log failed in {repo}: {p.stderr.strip()}")
    shas = p.stdout.split()
    if len(shas) < 2:
        print(f"only {len(shas)} commit(s) touched AGENTS.md since {since}; widen --days")
        return None

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
        return None
    return stats_from_sizes(sizes, days, repo_name=repo.name)


def print_growth(st: dict) -> None:
    print(f"repo    : {st['repo']}")
    print(f"window  : last {st['days']} days, {st['commits']} commits touching AGENTS.md")
    print(f"size    : {st['start']} -> {st['end']}   net {st['net']:+}")
    print(f"rate    : {st['rate']:.0f} chars/day")
    print(f"commits : {st['grew']} grew, {st['shrank']} shrank")
    if st["max"] is not None:
        print(f"growth  : median {st['median']}  p90 {st['p90']}  max {st['max']}")
        print()
        print(f"=> slack must absorb a single growing commit: >= {st['max']} covers the largest seen.")
        print("   A ceiling with ZERO slack fires on the next growing PR by construction.")


def measure_growth(repo: Path, days: int) -> int:
    """Report a repo's AGENTS.md burn from git, so a ceiling's slack can be sized.

    Every figure a ceiling depends on goes stale fast -- the plan said canopy was
    94,373, a handoff said 93,151, and it was 95,133 when the gate was seeded. So
    this measures rather than reports: run it, do not quote it.
    """
    try:
        st = growth_stats(repo, days)
    except GrowthError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if st is None:
        return 0
    print_growth(st)
    return 0


# --------------------------------------------------------------------------------------
# Rendering. Tokens are @@NAME@@ rather than str.format so the GitHub ${{ }} syntax in the
# templates needs no escaping.
# --------------------------------------------------------------------------------------

DEFAULT_CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1"
DEFAULT_SETUP_PYTHON = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97  # v7.0.0"

JOB_TEMPLATE = """\
  # ═══════════════════════════════════════════════════════════════════════════════════════════════
  # Memory Budget (ADVISORY, standalone): P5 port of juniper-ml's size ratchet.
  # Plan: juniper-ml notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md (§P5);
  # tracking issue juniper-ml#1326. Rendered by juniper-ml's
  # util/ad-hoc/2026-08-25_p5_port_memory_budget.py from figures measured IN THIS REPO on
  # @@DATE@@ -- re-measure, never transcribe.
  #
  # WHY THE RATE AXIS SHIPS FIRST, AND ALONE. juniper-ml's AGENTS.md grew ~20x in six months
  # WHILE UNDER FOUR ACTIVE CI GATES -- every one of them enforced structure or currency and
  # none enforced SIZE; 172 of 200 main-line merges grew it against 14 that shrank it, by 2,628
  # bytes between them. A cut without a ceiling is undone in ~44 days, and a ceiling set AFTER a
  # cut locks in the inflated level. So the ceiling lands first and the cut comes later; this job
  # carries no relocation check yet, because @@REPO@@ has not cut anything to check.
  #
  # STANDALONE, and deliberately ABSENT from any Quality Gate `needs:` (plan correction C9). A
  # `needs:` entry is the wrong promotion mechanism: it makes a skip on a non-PR event fail the
  # gate. Promotion happens in the branch RULESET, the same way Sequence Safety was promoted --
  # and only after the soak below, with `--advisory` removed and the three negative controls
  # re-run against the non-advisory job.
  #
  # ADVISORY during the soak. `--advisory` reports and always exits 0. It is removed only after
  # three negative controls pass in this repo -- clean tree exits 0, +500 chars exits 1, and a
  # waiver trailer exits 0 -- because a blocking gate that cannot fail is worse than none.
  #
  # EXPECT A REPORTED VIOLATION. The ceiling was seeded at the exact size on the day this landed
  # (@@CEILING@@ chars; zero slack, by design). Over the @@DAYS@@ days to @@DATE@@ this repo's
  # AGENTS.md went @@START@@ -> @@END@@ (@@NET@@, ~@@RATE@@ chars/day) across @@COMMITS@@ commits
  # touching it -- @@GREW@@ grew it, @@SHRANK@@ shrank it; median growing commit @@MEDIAN@@,
  # largest @@MAX@@. The first AGENTS.md-growing PR is SUPPOSED to report -- that is the soak
  # measuring the burn, not a misconfiguration.
  memory-budget:
    name: Memory Budget
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request' || github.event_name == 'merge_group'
    permissions:
      contents: read
    steps:
      - name: Checkout Code (full history)
        uses: @@CHECKOUT@@
        with:
          fetch-depth: 0 # need the base tip to apply the no-worsening rule

      - name: Set up Python ${{ env.@@PYVAR@@ }}
        uses: @@SETUP_PYTHON@@
        with:
          python-version: ${{ env.@@PYVAR@@ }}

      - name: Check memory-file size budget
        run: |
          echo "╔════════════════════════════════════════════════════════════╗"
          echo "║@@BANNER@@║"
          echo "╚════════════════════════════════════════════════════════════╝"
          # The base is read from the event rather than hardcoded; merge_group has no
          # github.base_ref, hence the fallback.
          BASE_REF="${{ github.base_ref || 'main' }}"
          git fetch --no-tags origin "$BASE_REF"
          # Allow-Budget-Overrun is a LOAN, not a pass: it suppresses the failure without moving
          # the ceiling, so the debt still blocks the next author. Trailers are injected from an
          # explicit file (the checker never shells out for them) so the classifier stays pure.
          # Two-dot FETCH_HEAD..HEAD = exactly the commits this PR adds on top of base.
          git log --format=%B FETCH_HEAD..HEAD > memory-budget-trailers.txt
          # `--advisory` is the SOAK setting and is removed to promote. Escape hatch once this
          # blocks, when the growth is genuinely warranted: add the commit trailer
          #   Allow-Budget-Overrun: AGENTS.md
          # and carry it into the SQUASH message -- squash composes from the commit messages, so
          # a trailer left only in the PR body is silently discarded.
          python3 util/memory_budget_check.py \\
            --base-ref FETCH_HEAD \\
            --trailers-file memory-budget-trailers.txt \\
            --advisory

"""

WORKFLOW_TEMPLATE = """\
---
#####################################################################################################################################################################################################
# Project:       Juniper
# Application:   @@REPO@@
# File Name:     memory-budget.yml
# Author:        Paul Calnon
#
# Date Created:  @@DATE@@
#
# License:       MIT License
# Copyright:     Copyright (c) 2026 Paul Calnon
#
# Description:
#    Memory-file size budget (ADVISORY, standalone) -- P5 port of juniper-ml's AGENTS.md size
#    ratchet (juniper-ml notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md §P5;
#    tracking issue juniper-ml#1326). This repo has no single ci.yml -- each package lane carries
#    its own required-checks aggregate -- so the job ships as a STANDALONE workflow, the same shape
#    as sequence-safety.yml here: never wired into any required-checks aggregate, never blocking.
#    Promotion to a required context, if ever desired, is an owner-only branch-protection decision
#    taken only after `--advisory` is removed and the three negative controls pass in this repo.
#
# Security Notes:
#    - pull_request-triggered only; workflow permissions are least-privilege (contents: read).
#    - The checker is pure git + stdlib; no network at check time. Actions are SHA-pinned.
#
# References:
#    - util/memory_budget_check.py (ported verbatim from juniper-ml) + conf/memory_budget.json
#    - juniper-canopy / juniper-cascor .github/workflows/ci.yml (the in-ci.yml job shape)
#####################################################################################################################################################################################################

name: Memory Budget

on:
  pull_request:
    branches:
      - main
      - develop

# Per-PR ref, cancel superseded runs: an advisory signal only needs the latest push.
concurrency:
  group: memory-budget-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

env:
  @@PYVAR@@: "@@PYTHON@@"

jobs:
@@JOB@@"""


def _fmt(v) -> str:
    return f"{v:,}" if isinstance(v, int) else "n/a"


def pins_from(workflow: Path | None) -> tuple[str, str]:
    """The checkout / setup-python `uses:` strings already pinned in the target's workflow.

    Dependabot bumps these per repo; a block that carries another repo's pins introduces a
    second copy of the action version for the next bump to miss. Falls back to the fleet
    defaults when the target has no such line.
    """
    checkout, setup = DEFAULT_CHECKOUT, DEFAULT_SETUP_PYTHON
    if workflow is not None and workflow.is_file():
        for line in workflow.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*(?:-\s+)?uses:\s+(actions/(checkout|setup-python)@\S+.*)$", line)
            if not m:
                continue
            if m.group(2) == "checkout" and checkout is DEFAULT_CHECKOUT:
                checkout = m.group(1).rstrip()
            elif m.group(2) == "setup-python" and setup is DEFAULT_SETUP_PYTHON:
                setup = m.group(1).rstrip()
    return checkout, setup


def _fill(template: str, **tokens) -> str:
    out = template
    for key, value in tokens.items():
        out = out.replace(f"@@{key}@@", str(value))
    left = re.findall(r"@@[A-Z_]+@@", out)
    if left:
        raise ValueError(f"unfilled template tokens: {sorted(set(left))}")
    return out


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def render_job(repo_name: str, pyvar: str, stats: dict, ceiling: int, pins: tuple[str, str] | None = None, today: str | None = None) -> str:
    """The `memory-budget` job block, indented for splicing under a workflow's `jobs:`."""
    checkout, setup = pins or (DEFAULT_CHECKOUT, DEFAULT_SETUP_PYTHON)
    banner = f"  {repo_name} - Memory File Size Budget (ADVISORY)".ljust(60)[:60]
    return _fill(
        JOB_TEMPLATE,
        REPO=repo_name,
        PYVAR=pyvar,
        BANNER=banner,
        CEILING=_fmt(ceiling),
        DAYS=stats["days"],
        DATE=today or _today(),
        START=_fmt(stats["start"]),
        END=_fmt(stats["end"]),
        NET=f"{stats['net']:+,}",
        RATE=f"{stats['rate']:.0f}",
        COMMITS=stats["commits"],
        GREW=stats["grew"],
        SHRANK=stats["shrank"],
        MEDIAN=_fmt(stats["median"]),
        MAX=_fmt(stats["max"]),
        CHECKOUT=checkout,
        SETUP_PYTHON=setup,
    )


def render_workflow(repo_name: str, pyvar: str, python_version: str, stats: dict, ceiling: int, pins: tuple[str, str] | None = None, today: str | None = None) -> str:
    """A standalone workflow carrying the job, for a repo with no ci.yml (juniper-recurrence)."""
    today = today or _today()
    job = render_job(repo_name, pyvar, stats, ceiling, pins=pins, today=today)
    return _fill(WORKFLOW_TEMPLATE, REPO=repo_name, DATE=today, PYVAR=pyvar, PYTHON=python_version, JOB=job)


def render_config(repo_name: str, stats: dict, ceiling: int, has_reference: bool, today: str | None = None) -> str:
    """conf/memory_budget.json with the ceiling MEASURED from the target's AGENTS.md (chars)."""
    today = today or _today()
    readme = [
        "Character ceilings for always-loaded memory files. Ported from juniper-ml as P5 of",
        "the shared-session-memory plan (juniper-ml notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md;",
        "tracking issue juniper-ml#1326).",
        "",
        "Enforced by util/memory_budget_check.py via the standalone 'Memory Budget' job.",
        "CHARACTERS, not bytes -- the shipped Claude Code check compares content.length.",
        "",
        "WHY THE RATE AXIS SHIPS FIRST. juniper-ml's AGENTS.md grew ~20x in six months WHILE",
        "UNDER FOUR ACTIVE CI GATES: every one enforced structure or currency, none enforced",
        "size. A cut without a ceiling is undone in ~44 days, and a ceiling set AFTER a cut",
        "locks in the inflated level. So the ceiling lands first, and the cut comes later.",
        "",
        f"MEASURED IN THIS REPO over the {stats['days']} days to {today}: AGENTS.md went",
        f"{_fmt(stats['start'])} -> {_fmt(stats['end'])} chars ({stats['net']:+,}, ~{stats['rate']:.0f}/day) across",
        f"{stats['commits']} commits touching it -- {stats['grew']} grew it, {stats['shrank']} shrank it; median growing",
        f"commit {_fmt(stats['median'])}, p90 {_fmt(stats['p90'])}, largest {_fmt(stats['max'])}. Order the rollout by",
        "RATE, not size: re-measure with juniper-ml's util/ad-hoc/2026-08-25_p5_port_memory_budget.py",
        "measure-growth rather than reusing these figures.",
        "",
        "The ceiling starts at the size on the day the gate landed, so it is satisfiable",
        "immediately and governs only GROWTH. Ratchet it down after each cut with:",
        "  python3 util/memory_budget_check.py --ratchet",
        "",
        "BUT --ratchet TIGHTENS TO THE EXACT CURRENT SIZE, leaving ZERO headroom. It SEEDS; it",
        "does not tighten gracefully. After a real cut, prefer a hand-edit to a value with",
        "DELIBERATE SLACK sized to this repo's own measured burn -- and RE-MEASURE rather than",
        "reusing the figures above.",
        "",
        "RAISING a ceiling FAILS the gate. If a raise is genuinely intended, declare it with an",
        "  Allow-Ceiling-Raise: <path>  commit trailer -- deliberately NOT the same trailer as",
        "Allow-Budget-Overrun, because an overrun borrows against a ceiling that still stands",
        "while a raise moves it and erases the debt for everyone.",
        "",
    ]
    if has_reference:
        readme += [
            "docs/REFERENCE.md is deliberately NOT governed. It is the migration DESTINATION;",
            "capping it would penalise exactly the relocation this plan wants, and it is read on",
            "demand rather than always loaded -- which is the entire point.",
        ]
    else:
        readme += [
            "NOTE FOR THE CUT (P5 step e): this repo has NO docs/REFERENCE.md. The relocation",
            "destination must be created before anything can be moved into it, and G3 (the",
            "relocation-completeness check) cannot be wired until it exists.",
        ]
    slack = _fmt(stats["max"])
    note = (
        f"Seeded {today} at the character count of AGENTS.md IN THIS REPO (rendered by juniper-ml's "
        f"util/ad-hoc/2026-08-25_p5_port_memory_budget.py render-config; `python3 util/memory_budget_check.py --ratchet` "
        f"run afterwards must report nothing to tighten). ZERO slack, deliberately: the ceiling starts at the size on "
        f"the day the gate landed, so it is satisfiable immediately and governs only growth, and the job ships ADVISORY "
        f"so a violation reports rather than blocks. At the measured ~{stats['rate']:.0f} chars/day a violation is "
        f"expected soon -- that is the soak measuring the burn, not a misconfiguration. Before promoting to blocking, "
        f"land a cut and ratchet, or hand-edit slack sized to a RE-MEASURED burn (>= {slack} absorbs the largest single "
        f"commit seen here)."
    )
    doc = {"_README": readme, "files": {"AGENTS.md": {"ceiling_chars": ceiling, "_note": note}}}
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def measured_ceiling(repo: Path) -> int:
    """The ceiling to seed: the character count of the target's working-tree AGENTS.md."""
    return len((repo / "AGENTS.md").read_text(encoding="utf-8"))


def repo_name(repo: Path) -> str:
    """The repo's name from its origin URL, falling back to the directory name.

    A worktree's directory is `juniper-x--branch--stamp--sha`, so the directory name is
    wrong exactly when a port is done the recommended way (in a worktree).
    """
    p = subprocess.run(
        ["git", "-C", str(repo), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )
    url = p.stdout.strip().rstrip("/") if p.returncode == 0 else ""
    if url:
        tail = url.rsplit("/", 1)[-1].rsplit(":", 1)[-1]
        return re.sub(r"\.git$", "", tail)
    return repo.name


def _render(cmd: str, args) -> int:
    repo: Path = args.repo
    if not (repo / "AGENTS.md").is_file():
        print(f"error: {repo} has no AGENTS.md -- nothing to govern", file=sys.stderr)
        return 2
    try:
        st = growth_stats(repo, args.days)
    except GrowthError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if st is None:
        return 2
    name = args.repo_name or repo_name(repo)
    ceiling = measured_ceiling(repo)
    if cmd == "render-config":
        text = render_config(name, st, ceiling, has_reference=(repo / "docs" / "REFERENCE.md").is_file())
    else:
        pins = pins_from(args.match_pins)
        if cmd == "render-job":
            text = render_job(name, args.pyvar, st, ceiling, pins=pins)
        else:
            text = render_workflow(name, args.pyvar, args.python, st, ceiling, pins=pins)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out} for {name}: ceiling {ceiling:,} chars, {st['rate']:.0f} chars/day, largest commit {_fmt(st['max'])}")
    else:
        sys.stdout.write(text)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("adapt-test", help="fix repo-root depth, header fields, marker; add house nosec markers")
    a.add_argument("path", type=Path)
    a.add_argument("--depth", type=int, default=2)
    a.add_argument("--sub-project", default=None, help="rewrite the header's Sub-Project: line")
    a.add_argument("--header-version", default=None, help="rewrite the header's Version: value, or `none` to drop the line")
    a.add_argument("--pytest-marker", default=None, help="add `pytestmark = pytest.mark.<m>` for marker-selected lanes")

    i = sub.add_parser("insert-job", help="splice a job block before a named job")
    i.add_argument("workflow", type=Path)
    i.add_argument("block", type=Path)
    i.add_argument("--before", default="required-checks")

    g = sub.add_parser("measure-growth", help="AGENTS.md burn from git, for sizing a ceiling's slack")
    g.add_argument("repo", type=Path)
    g.add_argument("--days", type=int, default=30)

    for cmd, help_text in (
        ("render-job", "render the memory-budget job block from figures measured in <repo>"),
        ("render-workflow", "render a standalone memory-budget workflow (repos with no ci.yml)"),
        ("render-config", "render conf/memory_budget.json with the ceiling measured in <repo>"),
    ):
        r = sub.add_parser(cmd, help=help_text)
        r.add_argument("repo", type=Path)
        r.add_argument("--days", type=int, default=30)
        r.add_argument("--repo-name", default=None, help="default: the directory name")
        r.add_argument("--out", type=Path, default=None, help="default: stdout")
        if cmd != "render-config":
            r.add_argument("--pyvar", default="PYTHON_TEST_VERSION", help="the target's Python-version env var")
            r.add_argument("--match-pins", type=Path, default=None, help="reuse the action pins found in this workflow")
        if cmd == "render-workflow":
            r.add_argument("--python", default="3.14", help="value for the env var in the standalone workflow")

    args = ap.parse_args()
    if args.cmd == "adapt-test":
        return adapt_test(args.path, args.depth, sub_project=args.sub_project, header_version=args.header_version, pytest_marker=args.pytest_marker)
    if args.cmd == "measure-growth":
        return measure_growth(args.repo, args.days)
    if args.cmd.startswith("render-"):
        return _render(args.cmd, args)
    return insert_job(args.workflow, args.block, args.before)


if __name__ == "__main__":
    sys.exit(main())
