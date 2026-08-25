#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc
Author:      Paul Calnon
Version:     0.2.0
License:     MIT License
Created:     2026-08-25
Status:      ad-hoc -- migration (P5 fleet rollout)
Retire when: every repo in the P5 rollout carries the memory-budget gate, or the
             gate moves into a shared package and stops being copied per-repo.

P5 porting helper: adapt juniper-ml's ``test_memory_budget_check.py`` for a sibling
repo, seed that repo's ``conf/memory_budget.json`` by ratchet, render the ADVISORY
``memory-budget`` job for it, and splice the job into its ``ci.yml``.

Plan: ``notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`` §P5.

Three adaptations are needed, and ALL fail in ways that do not point at themselves:

**Repo root depth.** juniper-ml keeps tests at ``tests/`` so the root is
``parents[1]``. canopy and cascor keep them at ``src/tests/`` (``testpaths``), so
the root is ``parents[2]``; juniper-data at ``juniper_data/tests/unit/`` so it is
``parents[3]``. Getting this wrong does not raise -- ``REPO_ROOT`` silently resolves
to the wrong directory and the suite fails later looking for a
``conf/memory_budget.json`` that is not there, which reads like a missing config
rather than a bad path.

**Bandit strictness differs across the fleet.** The byte-identical file passes
juniper-ml's bandit and FAILS juniper-cascor's on B603/B607 at three subprocess
call sites (the client repos' tests-scoped bandit is the same shape). All three are
fixed-argv calls into a ``TemporaryDirectory``, so the suppression is genuine rather
than convenient -- but it has to be written, and the house idiom is an inline
``# nosec`` naming the codes AND the reason. A bare ``# nosec`` would be the
"plausible justification hides a real defect" shape.

**Header lines** -- the one cascor#585 found the hard way. The file's ``Version:``
header line is forbidden repo-wide in cascor (BUG-CC-04) and must EQUAL the package
version in data-client (``tests/test_file_header_versions.py`` rglobs ``tests/``).
Both are tests in a DIFFERENT file, fired by the new file's mere presence; neither is
caught by pre-commit, and the ported file's own suite passes. ``adapt-test
--header-version`` sets the line or (``none``) removes it; run the target's FULL
unit suite regardless, because every repo has tests of that shape.

Job splicing is a TEXT operation, deliberately: a PyYAML round-trip would strip
every comment, and in these workflows the comments carry the rationale (why the
job is standalone, why a flag is absent) that is the actual institutional memory.

``measure-growth`` exists because P5's ordering rule is "order by RATE, not size" and
a rate is not obtainable from any other tool here. Unlike ``MEMORY.md``, a repo's
``AGENTS.md`` IS tracked, so the burn can be measured rather than assumed -- which is
how cascor (730 chars/day) turned out to be nine times canopy's rate (81/day) despite
having the smaller file. ``seed-config`` and ``render-job`` build on it so that no
figure is ever transcribed: both measure the target's own history and read back the
ceiling the ratchet actually wrote.

Usage (a full port, in this order; the checker is copied byte-identical -- it is
repo-agnostic -- and ``<tests>`` is wherever the target's runner collects from):
    cp util/memory_budget_check.py <repo>/util/
    cp tests/test_memory_budget_check.py <repo>/<tests>/
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py adapt-test <repo>/<tests>/test_memory_budget_check.py --depth N \\
        --sub-project juniper-<x> [--header-version 0.4.2|none] [--pytest-marker unit]
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py seed-config <repo> --ref origin/main
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py render-job <repo> --out <job.yml> [--python-env-var PYTHON_VERSION]
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py insert-job <repo>/.github/workflows/ci.yml <job.yml> --before required-checks
    # then: the target's own pre-commit on the four files, and its FULL unit suite.
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth <repo> [--days 30] [--ref origin/main]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - shells out to git and the target repo's own checker, fixed argv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEPTH_RE = re.compile(r"^REPO_ROOT = Path\(__file__\)\.resolve\(\)\.parents\[(\d+)\]$", re.MULTILINE)
SUB_PROJECT_RE = re.compile(r"^Sub-Project: .*$", re.MULTILINE)
HEADER_VERSION_RE = re.compile(r"^Version:[ \t]+\S+\n", re.MULTILINE)
CHECKOUT_PIN = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
PLACEHOLDER_CEILING = 10_000_000

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

# The generic half of every ported conf/memory_budget.json's _README. The measured half is
# appended by seed-config from the target's own git history.
README_COMMON = [
    "Character ceilings for always-loaded memory files. Ported from juniper-ml as P5 of",
    "the shared-session-memory plan (juniper-ml notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md).",
    "",
    "Enforced by util/memory_budget_check.py via the standalone 'Memory Budget' job in",
    "ci.yml. CHARACTERS, not bytes -- the shipped Claude Code check compares",
    "content.length.",
    "",
    "WHY THE RATE AXIS SHIPS FIRST. juniper-ml's AGENTS.md grew ~20x in six months WHILE",
    "UNDER FOUR ACTIVE CI GATES: every one enforced structure or currency, none enforced",
    "size. A cut without a ceiling is undone in ~44 days, and a ceiling set AFTER a cut",
    "locks in the inflated level. So the ceiling lands first, and the cut comes later.",
    "",
    "The ceiling starts at the size on the day the gate landed, so it is satisfiable",
    "immediately and governs only GROWTH. Ratchet it down after each cut with:",
    "  python3 util/memory_budget_check.py --ratchet",
    "",
    "BUT --ratchet TIGHTENS TO THE EXACT CURRENT SIZE, leaving ZERO headroom. It SEEDS; it",
    "does not tighten gracefully. After a real cut, prefer a hand-edit to a value with",
    "DELIBERATE SLACK sized to this repo's own measured burn -- and RE-MEASURE rather than",
    "reusing the figures below.",
    "",
    "RAISING a ceiling FAILS the gate. If a raise is genuinely intended, declare it with an",
    "  Allow-Ceiling-Raise: <path>  commit trailer -- deliberately NOT the same trailer as",
    "Allow-Budget-Overrun, because an overrun borrows against a ceiling that still stands",
    "while a raise moves it and erases the debt for everyone.",
    "",
    "docs/REFERENCE.md is deliberately NOT governed. It is the migration DESTINATION;",
    "capping it would penalise exactly the relocation this plan wants, and it is read on",
    "demand rather than always loaded -- which is the entire point.",
]

# The ADVISORY job as it landed on canopy's and cascor's `main` (canopy#516 / cascor#585),
# with the repo-specific facts tokenised. Keep it as text: the comments ARE the port.
BANNER = "  # " + "═" * 95
JOB_TEMPLATE = (
    BANNER
    + """
  # Memory Budget (ADVISORY, standalone): P5 port of juniper-ml's size ratchet.
  # Plan: juniper-ml notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md (§P5).
  #
  # WHY THE RATE AXIS SHIPS FIRST, AND ALONE. juniper-ml's AGENTS.md grew ~20x in six months
  # WHILE UNDER FOUR ACTIVE CI GATES -- every one of them enforced structure or currency and
  # none enforced SIZE; 172 of 200 main-line merges grew it against 14 that shrank it, by 2,628
  # bytes between them. A cut without a ceiling is undone in ~44 days, and a ceiling set AFTER a
  # cut locks in the inflated level. So the ceiling lands first and the cut comes later; this job
  # carries no relocation check yet, because @@SHORT@@ has not cut anything to check.
  #
  # STANDALONE, and deliberately ABSENT from the `required-checks` Quality Gate `needs:` (plan
  # correction C9). A `needs:` entry is the wrong promotion mechanism: it makes a skip on a
  # non-PR event fail the gate. Promotion happens in the branch RULESET, the same way Sequence
  # Safety was promoted -- and only after the soak below.
  #
  # ADVISORY during the soak. `--advisory` reports and always exits 0. It is removed only after
  # three negative controls pass in this repo -- clean tree exits 0, +500 chars exits 1, and a
  # waiver trailer exits 0 -- because a blocking gate that cannot fail is worse than none.
  #
@@EXPECT@@  memory-budget:
    name: Memory Budget
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request' || github.event_name == 'merge_group'
    permissions:
      contents: read
    steps:
      - name: Checkout Code (full history)
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0 # need the base tip to apply the no-worsening rule

      - name: Set up Python ${{ env.@@PYENV@@ }}
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: ${{ env.@@PYENV@@ }}

      - name: Check memory-file size budget
        run: |
          echo "╔════════════════════════════════════════════════════════════╗"
          echo "@@BOX@@"
          echo "╚════════════════════════════════════════════════════════════╝"
          # @@SHORT@@'s PRs target more than one branch, so the base is read from the event rather
          # than hardcoded; merge_group has no github.base_ref, hence the fallback.
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
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)  # nosec B603 B607 - fixed git argv, no untrusted input


def repo_name(repo: Path) -> str:
    """The GitHub repo name (juniper-<x>), from the origin URL -- a worktree's directory
    name is `juniper-<x>--<branch>--<stamp>--<sha>`, so `repo.name` is wrong there."""
    p = _git(repo, "remote", "get-url", "origin")
    url = p.stdout.strip() if p.returncode == 0 else ""
    tail = url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git") if url else ""
    return tail or repo.resolve().name.split("--", 1)[0]


def growth_stats(repo: Path, days: int, ref: str) -> dict | None:
    """AGENTS.md burn over the window, from git. None when there are fewer than two
    commits to difference (widen --days)."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    p = _git(repo, "log", ref, f"--since={since}", "--format=%H", "--reverse", "--", "AGENTS.md")
    if p.returncode != 0:
        raise RuntimeError(f"git log failed in {repo}: {p.stderr.strip()}")
    sizes = []
    for sha in p.stdout.split():
        out = subprocess.run(["git", "-C", str(repo), "show", f"{sha}:AGENTS.md"], capture_output=True, check=False)  # nosec B603 B607 - fixed git argv
        if out.returncode == 0:
            sizes.append(len(out.stdout.decode("utf-8", errors="replace")))
    if len(sizes) < 2:
        return None
    deltas = [b - a for a, b in zip(sizes, sizes[1:])]
    grew = sorted(d for d in deltas if d > 0)
    net = sizes[-1] - sizes[0]
    return {
        "days": days,
        "ref": ref,
        "since": since,
        "commits": len(sizes),
        "first": sizes[0],
        "last": sizes[-1],
        "net": net,
        "rate": net / max(days, 1),
        "grew": len(grew),
        "shrank": sum(1 for d in deltas if d < 0),
        "median": grew[len(grew) // 2] if grew else 0,
        "p90": grew[max(0, int(len(grew) * 0.9) - 1)] if grew else 0,
        "max": grew[-1] if grew else 0,
    }


def adapt_test(path: Path, depth: int, sub_project: str | None, header_version: str | None, marker: str | None) -> int:
    s = path.read_text(encoding="utf-8")

    m = DEPTH_RE.search(s)
    if not m:
        print(f"error: no REPO_ROOT parents[...] line in {path}", file=sys.stderr)
        return 2
    if int(m.group(1)) != depth:
        note = (
            f"# This repo keeps tests deeper than juniper-ml does (testpaths), so the repo root\n"
            f"# is parents[{depth}], not parents[{m.group(1)}]. Getting this wrong does not raise -- it\n"
            f"# resolves to the wrong directory and fails later as a missing config.\n"
        )
        s = DEPTH_RE.sub(note + f"REPO_ROOT = Path(__file__).resolve().parents[{depth}]", s, count=1)
        print(f"  depth: parents[{m.group(1)}] -> parents[{depth}]")
    else:
        print(f"  depth: already parents[{depth}]")

    if sub_project:
        s, n = SUB_PROJECT_RE.subn(f"Sub-Project: {sub_project}", s, count=1)
        print(f"  sub-project: {'set to ' + sub_project if n else 'NO Sub-Project line found'}")

    if header_version is not None:
        if header_version.lower() == "none":
            s, n = HEADER_VERSION_RE.subn("", s, count=1)
            if n:
                s = s.replace(
                    "License:     MIT License\n",
                    "License:     MIT License\n\n"
                    "NOTE: no `Version:` header line, deliberately. This repo's own suite rejects or pins\n"
                    "such lines repo-wide (a test in a DIFFERENT file, fired by this file's presence).\n",
                    1,
                )
            print(f"  header version: {'removed' if n else 'no Version: line to remove'}")
        else:
            s, n = HEADER_VERSION_RE.subn(f"Version:     {header_version}\n", s, count=1)
            print(f"  header version: {'set to ' + header_version if n else 'no Version: line to set'}")

    if marker:
        anchor = "from tempfile import TemporaryDirectory\n"
        if anchor not in s:
            print("error: import anchor for the pytest marker not found", file=sys.stderr)
            return 2
        s = s.replace(
            anchor,
            anchor
            + "\nimport pytest\n\n"
            + "# This repo's CI selects tests by marker; an unmarked module is silently DESELECTED,\n"
            + "# and the gate's own negative controls would never run.\n"
            + f"pytestmark = pytest.mark.{marker}\n",
            1,
        )
        print(f"  pytest marker: {marker}")

    added = 0
    out = []
    for line in s.splitlines(keepends=True):
        out.append(line)
        for mk, comment in NOSEC_SITES:
            if line.strip() == mk.strip() and "nosec" not in out[-2]:
                # Attach the suppression to the subprocess.run( line above the argv.
                prev = out[-2].rstrip("\n")
                out[-2] = prev + comment + "\n"
                added += 1
                break
    s = "".join(out)
    print(f"  nosec: annotated {added} call site(s)")

    # The client repos' tests-scoped bandit does not skip B404 (import subprocess) either;
    # cascor's does, so its port never needed this. Harmless where the code is skipped.
    if "nosec B404" not in s:
        s, n = re.subn(
            r"^import subprocess$",
            "import subprocess  # nosec B404 - the checker under test is driven as a subprocess by design",
            s,
            count=1,
            flags=re.MULTILINE,
        )
        print(f"  nosec B404: {'annotated import subprocess' if n else 'no bare import subprocess line'}")

    path.write_text(s, encoding="utf-8")
    return 0


def measured_paragraph(st: dict | None, today: str) -> list[str]:
    if st is None:
        return [
            "",
            f"BURN NOT MEASURABLE on {today}: fewer than two commits touched AGENTS.md in the window.",
            "Measure before sizing slack:  python3 <juniper-ml>/util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth . --days 90",
        ]
    return [
        "",
        f"THIS REPO'S OWN BURN, measured from git over the {st['days']} days to {today} ({st['ref']}):",
        f"{st['first']:,} -> {st['last']:,}, {st['net']:+,} chars (~{st['rate']:.0f}/day) across {st['commits']} commits",
        f"touching the file -- {st['grew']} grew it, {st['shrank']} shrank it, median growing commit {st['median']:,},",
        f"largest {st['max']:,}. The plan orders the rollout by this RATE, not by size. A fleet-wide",
        "docs sweep lands in every AGENTS.md at once and is exactly the shape a zero-slack ceiling",
        "cannot absorb (the 2026-08-21 base-branch-guard sweep added 1,982 chars to every repo).",
        "Re-measure before sizing slack; do not reuse these figures.",
    ]


def seed_config(repo: Path, days: int, ref: str) -> int:
    """Write conf/memory_budget.json and seed AGENTS.md's ceiling by running the repo's own
    checker with --ratchet -- never by transcribing a number."""
    checker = repo / "util" / "memory_budget_check.py"
    conf = repo / "conf" / "memory_budget.json"
    if not checker.is_file():
        print(f"error: {checker} missing -- copy util/memory_budget_check.py first", file=sys.stderr)
        return 2
    if conf.exists():
        print(f"error: {conf} already exists; seed-config is for a repo with no ceiling yet (use --ratchet directly)", file=sys.stderr)
        return 2
    if not (repo / "AGENTS.md").is_file():
        print(f"error: {repo} has no AGENTS.md -- nothing to govern", file=sys.stderr)
        return 2
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    st = growth_stats(repo, days, ref)
    budget = {
        "_README": README_COMMON + measured_paragraph(st, today),
        "files": {"AGENTS.md": {"ceiling_chars": PLACEHOLDER_CEILING, "_note": "placeholder -- seed-config replaces this by --ratchet"}},
    }
    conf.parent.mkdir(parents=True, exist_ok=True)
    conf.write_text(json.dumps(budget, indent=2) + "\n", encoding="utf-8")

    argv = [sys.executable, str(checker), "--repo-root", str(repo), "--base-ref", ref]
    p = subprocess.run([*argv, "--ratchet"], capture_output=True, text=True, check=False)  # nosec B603 - sys.executable + the target's own checker, fixed argv
    print(p.stdout.strip())
    if p.returncode != 0:
        print(f"error: --ratchet exited {p.returncode}: {p.stderr.strip()}", file=sys.stderr)
        return 2
    budget = json.loads(conf.read_text(encoding="utf-8"))
    ceiling = budget["files"]["AGENTS.md"]["ceiling_chars"]
    if ceiling >= PLACEHOLDER_CEILING:
        print("error: the ratchet did not tighten the placeholder ceiling", file=sys.stderr)
        return 2
    burn = f"At the measured ~{st['rate']:.0f} chars/day (see _README)" if st else "At any growth at all"
    slack = f">={st['max']:,} covers the largest single commit seen" if st else "sized to a measured burn"
    budget["files"]["AGENTS.md"]["_note"] = (
        f"Seeded {today} by `python3 util/memory_budget_check.py --ratchet` run IN THIS REPO, never transcribed. "
        "ZERO slack, deliberately: the ceiling starts at the size on the day the gate landed, so it is satisfiable "
        "immediately and governs only growth, and the job ships ADVISORY so a violation reports rather than blocks. "
        f"{burn} the next AGENTS.md-growing PR is EXPECTED to report -- that is the soak measuring the burn, not a "
        "misconfiguration. Before promoting to blocking: remove --advisory only after the three negative controls pass "
        f"against the non-advisory invocation, and hand-edit slack sized to a re-measured burn ({slack}) declared with "
        "an Allow-Ceiling-Raise: AGENTS.md trailer."
    )
    conf.write_text(json.dumps(budget, indent=2) + "\n", encoding="utf-8")

    p = subprocess.run(argv, capture_output=True, text=True, check=False)  # nosec B603 - as above
    print(p.stdout.strip())
    if p.returncode != 0:
        print(f"error: the checker does not pass on the seeded config (exit {p.returncode}): {p.stderr.strip()}", file=sys.stderr)
        return 2
    print(f"seeded {conf}: AGENTS.md ceiling_chars={ceiling}")
    return 0


def render_job(repo: Path, out: Path, python_env_var: str, days: int, ref: str, name: str | None) -> int:
    conf = repo / "conf" / "memory_budget.json"
    if not conf.is_file():
        print(f"error: {conf} missing -- run seed-config first", file=sys.stderr)
        return 2
    ceiling = json.loads(conf.read_text(encoding="utf-8"))["files"]["AGENTS.md"]["ceiling_chars"]
    name = name or repo_name(repo)
    short = name.removeprefix("juniper-")
    st = growth_stats(repo, days, ref)
    if st:
        expect = (
            "  # EXPECT A REPORTED VIOLATION SOON. The ceiling was seeded at the exact size on the day this\n"
            f"  # landed ({ceiling:,}; zero slack, by design), and {short}'s AGENTS.md grew {st['net']:+,} over the\n"
            f"  # previous {st['days']} days (~{st['rate']:.0f} chars/day) with a median growing commit of {st['median']:,} and a\n"
            f"  # largest of {st['max']:,}. The first AGENTS.md-growing PR is SUPPOSED to report -- that is the soak\n"
            "  # measuring the burn, not a misconfiguration.\n"
        )
    else:
        expect = (
            "  # EXPECT A REPORTED VIOLATION on the first growing PR. The ceiling was seeded at the exact size\n"
            f"  # on the day this landed ({ceiling:,}; zero slack, by design); {short}'s AGENTS.md history was too\n"
            "  # short to measure a burn. That report is the soak measuring the burn, not a misconfiguration.\n"
        )
    box = "║" + f"{name} - Memory File Size Budget (ADVISORY)".center(60) + "║"
    text = JOB_TEMPLATE.replace("@@EXPECT@@", expect).replace("@@SHORT@@", short).replace("@@BOX@@", box).replace("@@PYENV@@", python_env_var)
    if "@@" in text:
        print("error: an unreplaced token survived rendering", file=sys.stderr)
        return 2
    out.write_text(text, encoding="utf-8")
    ci = repo / ".github" / "workflows" / "ci.yml"
    if ci.is_file():
        ci_text = ci.read_text(encoding="utf-8")
        if CHECKOUT_PIN not in ci_text:
            print(f"::warning::{ci} does not pin {CHECKOUT_PIN}; align the rendered job's action pins with this repo's")
        if f"{python_env_var}:" not in ci_text:
            print(f"::warning::{ci} defines no `{python_env_var}:` -- pass --python-env-var with this repo's name for it")
    print(f"rendered {out} for {name} (ceiling {ceiling:,}, env var {python_env_var})")
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
    if "\n  memory-budget:\n" in text:
        print(f"error: {workflow} already has a memory-budget job", file=sys.stderr)
        return 2

    idx = text.index(anchor)
    head = text[: idx + 1]
    lines = head.splitlines(keepends=True)
    cut = len(lines)
    # Walk back over the anchor job's banner comment so the new job lands BEFORE the
    # banner, not wedged between a banner and the job it describes.
    while cut > 0 and lines[cut - 1].lstrip().startswith("#"):
        cut -= 1

    out = "".join(lines[:cut]) + job_text + "".join(lines[cut:]) + text[idx + 1:]
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
    try:
        st = growth_stats(repo, days, ref)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if st is None:
        print(f"fewer than 2 commits touched AGENTS.md since {days} days ago; widen --days")
        return 0
    print(f"repo    : {repo_name(repo)}  ({ref})")
    print(f"window  : last {days} days, {st['commits']} commits touching AGENTS.md")
    print(f"size    : {st['first']} -> {st['last']}   net {st['net']:+}")
    print(f"rate    : {st['rate']:.0f} chars/day")
    print(f"commits : {st['grew']} grew, {st['shrank']} shrank")
    if st["grew"]:
        print(f"growth  : median {st['median']}  p90 {st['p90']}  max {st['max']}")
        print()
        print(f"=> slack must absorb a single growing commit: >= {st['max']} covers the largest seen.")
        print("   A ceiling with ZERO slack fires on the next growing PR by construction.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("adapt-test", help="fix repo-root depth, header lines, marker; add house nosec markers")
    a.add_argument("path", type=Path)
    a.add_argument("--depth", type=int, default=2)
    a.add_argument("--sub-project", default=None, help="value for the Sub-Project: header line, e.g. juniper-cascor-client")
    a.add_argument("--header-version", default=None, help="set the Version: header line to this, or 'none' to remove it (cascor forbids it; data-client pins it)")
    a.add_argument("--pytest-marker", default=None, help="add `pytestmark = pytest.mark.<name>` (repos whose CI selects by -m)")

    s = sub.add_parser("seed-config", help="write conf/memory_budget.json and seed the ceiling by --ratchet in that repo")
    s.add_argument("repo", type=Path)
    s.add_argument("--days", type=int, default=30)
    s.add_argument("--ref", default="HEAD")

    r = sub.add_parser("render-job", help="render the ADVISORY memory-budget job block for a repo")
    r.add_argument("repo", type=Path)
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--python-env-var", default="PYTHON_TEST_VERSION", help="the ci.yml env var holding the Python version (deploy: PYTHON_VERSION)")
    r.add_argument("--repo-name", default=None, help="override the name derived from the origin URL")
    r.add_argument("--days", type=int, default=30)
    r.add_argument("--ref", default="HEAD")

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
        return adapt_test(args.path, args.depth, args.sub_project, args.header_version, args.pytest_marker)
    if args.cmd == "seed-config":
        return seed_config(args.repo, args.days, args.ref)
    if args.cmd == "render-job":
        return render_job(args.repo, args.out, args.python_env_var, args.days, args.ref, args.repo_name)
    if args.cmd == "measure-growth":
        return measure_growth(args.repo, args.days, args.ref)
    return insert_job(args.workflow, args.block, args.before)


if __name__ == "__main__":
    sys.exit(main())
