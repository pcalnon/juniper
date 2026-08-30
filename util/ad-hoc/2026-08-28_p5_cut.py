#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc tooling (plan §P5 step e — the cut)
Author:      Paul Calnon
License:     MIT License

Drive the P5 cut in one target repo: relocate reference sections out of
``AGENTS.md`` into ``docs/REFERENCE.md`` verbatim, ratchet the ceiling down with
real slack, prove no content was lost, and open a signed PR.

    python3 util/ad-hoc/2026-08-28_p5_cut.py prepare juniper-cascor-client [--reuse]
    python3 util/ad-hoc/2026-08-28_p5_cut.py ship    juniper-cascor-client
    python3 util/ad-hoc/2026-08-28_p5_cut.py status  juniper-cascor-client

Why a script rather than shell
------------------------------
A worktree-isolated session's shell gate refuses ``git -C <sibling>``, loops and
heredocs, so a nine-step per-repo sequence is either impossible or forty hand-typed
commands. Same reason ``2026-08-26_p5_promote_ready.py`` exists; this follows its
shape deliberately (worktree + dup-guard, controls, state file, prepare/ship split)
so the two read alike.

What makes this safe
--------------------
* **Relocation is byte-for-byte**, delegated to ``2026-08-19_p3_relocate_section.py``.
  G3 then passes by construction rather than by the author's judgement — the failure
  this whole effort exists to prevent is a well-meaning author dropping prose while
  keeping the identifiers.
* **The local ``relocation_check.py --expect-removals`` run IS the content-loss
  control** (plan §7.2). G3 runs ``--advisory`` in CI and does not exist post-merge,
  so a green PR proves nothing.
* **The ceiling is lowered with measured slack, never by ``--ratchet``.** Run straight
  after a cut, ``--ratchet`` leaves ZERO headroom and fails the next author on a single
  character (plan step b). Slack = max(largest single growing commit over 30 days,
  2,000 fan-out floor) — the same rule step d used, re-measured, never transcribed.
* Nothing here writes to a ruleset, and nothing merges.

Ordering hazard (plan, do not demote)
-------------------------------------
The cut must land on the target's ``main`` with its PRIMARY checkout pulled BEFORE any
worktree carries the trimmed file. A trimmed worktree over an untrimmed ancestor loads
BOTH copies, so context goes UP. ``ship`` prints the reminder; the pull is an owner step.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess  # nosec B404 -- fixed-argv git/gh/python calls; nothing is shell-interpolated
import sys
from pathlib import Path

JUNIPER = Path("/home/pcalnon/Development/python/Juniper")
WORKTREES = JUNIPER / "worktrees"
ML = JUNIPER / "juniper-ml"
BRANCH = "docs/p5-cut-agents-md"
SAFE_BRANCH = BRANCH.replace("/", "--")

GOVERNED = "AGENTS.md"
DEST = "docs/REFERENCE.md"   # default destination; a PLAN entry may override with "dest"
CONF = "conf/memory_budget.json"
SLACK_FLOOR = 2000
STATE_DIR = Path.home() / ".local" / "state" / "juniper-p5-cut"
SESSION_URL = "https://claude.ai/code/session_01Pg3aLP8H4BCZXSSNB8myCN"

RELOCATE = "util/ad-hoc/2026-08-19_p3_relocate_section.py"
RELOCHECK = "util/relocation_check.py"
BUDGET = "util/memory_budget_check.py"
PORT_HELPER = "util/ad-hoc/2026-08-25_p5_port_memory_budget.py"

CANOPY_PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
DATA_PY = "/opt/miniforge3/envs/JuniperData/bin/python"
# JuniperCascor1, not JuniperCascor: the latter's torch import is broken, and cascor-worker's
# tests/conftest.py imports the package, which needs juniper_config_tools.
CASCOR_PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"

# Per repo: the sections to move, in file order, each
#   (source heading, destination title, anchor, insert-before heading, pointer sentence)
# Destination titles deliberately avoid colliding with a `## ` section the destination
# ALREADY has -- the relocate script refuses on collision (re-entry safety), and an
# overlap probe on 2026-08-28 showed the same-named pairs share 0-9% of their lines, so
# they are genuinely different content and must not be merged.
PLAN: dict[str, dict] = {
    "juniper-cascor-client": {
        "python": CANOPY_PY,
        "sections": [
            ("## Architecture", "Architecture Reference", "architecture-reference",
             "## Scenario Reference",
             "The full client architecture: layers, transports, retry/backoff, and the reconnect state machine."),
            ("## Directory Layout", "Directory Layout Reference", "directory-layout-reference",
             "## Scenario Reference",
             "The annotated source tree, with the purpose of every package and key module."),
            ("## Constants", "Constants Reference", "constants-reference",
             "## Scenario Reference",
             "Every exported constant, its default, and the failure each one guards against."),
            ("## CI/CD Pipeline", "CI/CD Pipeline Reference", "cicd-pipeline-reference",
             "## Scenario Reference",
             "Per-workflow reference for `.github/workflows/`, including the contract each job must not break."),
        ],
    },
    "juniper-data": {
        "python": DATA_PY,
        "sections": [
            ("## Project Architecture", "Project Architecture Reference", "project-architecture-reference",
             "## Additional Resources",
             "The service's layered architecture, request lifecycle, and generator plug-in model."),
            ("## API Design", "API Design Reference", "api-design-reference",
             "## Additional Resources",
             "Route-by-route design notes: status codes, pagination, content negotiation, and the binary routes."),
            ("## Storage Backends", "Storage Backend Reference", "storage-backend-reference",
             "## Additional Resources",
             "Each storage backend, its configuration, and the durability guarantee it does and does not make."),
            ("## Observability — Prometheus Collectors", "Prometheus Collector Reference", "prometheus-collector-reference",
             "## Additional Resources",
             "Every Prometheus collector this service registers, and the register-or-reuse contract behind it."),
            ("## Docker", "Docker Reference", "docker-reference",
             "## Additional Resources",
             "Image build, compose wiring, and the environment each container expects."),
            ("## CI/CD Pipeline", "CI/CD Pipeline Reference", "cicd-pipeline-reference",
             "## Additional Resources",
             "Per-workflow reference for `.github/workflows/`, including the contract each job must not break."),
        ],
    },
    # juniper-canopy PR1 of TWO sequential single-destination PRs (owner decision 2026-08-29).
    # This one moves the documentation-ABOUT-documentation cluster -- 27,687 chars, 29.1% of the
    # always-resident file -- into docs/DOCUMENTATION_OVERVIEW.md, which is literally the file whose
    # subject that is. PR2 then moves the remaining reference material into a new
    # docs/AGENTS_REFERENCE.md. Two PRs rather than one two-destination PR because each is then a
    # single-destination relocation that `relocation_check.py` verifies with its one `--dest` as-is
    # (prep note §6d): no repeatable --dest, no union pass-condition, no chance of someone hitting a
    # spurious per-destination failure and "fixing" it by relaxing G3.
    #
    # `## Documentation Standards` collides with a section the destination already has (1,630 chars,
    # different content), so its destination title differs. Verified with the fence-aware section
    # tool, not a raw grep: DOCUMENTATION_OVERVIEW.md has 15 REAL sections -- a grep also reports
    # `## Table of Contents` / `## Section 1` / `## Section 2`, which are inside a fenced example.
    "juniper-canopy": {
        "python": CANOPY_PY,
        "dest": "docs/DOCUMENTATION_OVERVIEW.md",
        "sections": [
            ("## Documentation Organization", "Documentation Organization", "documentation-organization",
             "## Contact & Support",
             "How the documentation set is organised: which tree holds what, and why."),
            ("## Documentation Standards", "Documentation Authoring Standards", "documentation-authoring-standards",
             "## Contact & Support",
             "House style for authoring docs: headings, anchors, code samples, and link forms."),
            ("## Documentation Maintenance Workflow", "Documentation Maintenance Workflow", "documentation-maintenance-workflow",
             "## Contact & Support",
             "The end-to-end workflow for keeping documentation current as the code moves."),
            ("## Documentation File Types", "Documentation File Types", "documentation-file-types",
             "## Contact & Support",
             "Every documentation file type, what belongs in it, and where it lives."),
            ("## Update Triggers", "Documentation Update Triggers", "documentation-update-triggers",
             "## Contact & Support",
             "Which code changes oblige a documentation update, and which document each one touches."),
            ("## Archive Procedures", "Archive Procedures", "archive-procedures",
             "## Contact & Support",
             "How superseded documentation is archived under `docs/history/` without breaking links."),
            ("## Documentation Update Workflow", "Documentation Update Workflow", "documentation-update-workflow",
             "## Contact & Support",
             "The per-change checklist for updating documentation alongside a code change."),
        ],
    },
    # worker and deploy, added 2026-08-29 (owner decision to cut them). Section choice follows a
    # rule this arc arrived at the hard way: EXCLUDE any section carrying a score>=2 hazard
    # candidate from 2026-08-28_hazard_triage.py, because a relocation turns a resident fact into a
    # reference someone must know to look up. Excluded here:
    #   worker  `## CI/CD`      -- the no-`branches:`-filter fact (the only check on a stacked PR,
    #                              and it cannot block the merge)
    #   worker  `## Constants`  -- "re-run the cross-repo bit-identity check ... a mismatch SILENTLY
    #                              breaks worker connectivity"
    #   deploy  `## CI/CD Pipeline` -- the same no-filter fact, plus the base-branch-guard warning
    #                              that renaming the job makes `main` unmergeable
    # Score-1 hits inside the sets below were inspected and are false positives: worker L319 matches
    # "WARNING" as a LOG LEVEL in a flag table; deploy L580 is a test-markers table.
    "juniper-cascor-worker": {
        "python": CASCOR_PY,   # its tests/conftest.py imports the package -> needs juniper_config_tools
        "sections": [
            ("## Directory Layout", "Directory Layout Reference", "directory-layout-reference",
             "## Troubleshooting",
             "The annotated source tree, with the purpose of every package and key module."),
            ("## Application Architecture", "Application Architecture Reference", "application-architecture-reference",
             "## Troubleshooting",
             "The worker's process model, lease lifecycle, and how it attaches to a cascor run."),
            ("## Public API", "Public API Reference", "public-api-reference",
             "## Troubleshooting",
             "Every public entry point, its signature, and the exception it raises."),
            ("## Test Details", "Test Details Reference", "test-details-reference",
             "## Troubleshooting",
             "Per-suite detail: what each test file covers and the marker it carries."),
            # dest already has a `## CLI Reference` (different content -- 0% line overlap), so the
            # destination title must differ or the relocate script refuses on collision.
            ("## CLI Reference", "Worker CLI Flag Reference", "worker-cli-flag-reference",
             "## Troubleshooting",
             "Every CLI flag, its default, and the behaviour it selects."),
        ],
    },
    "juniper-deploy": {
        "python": CANOPY_PY,   # deploy has no Python linters of its own; yamllint is its lane
        "sections": [
            # dest already has `## Environment Variables` (different content -- 0% overlap).
            ("## Environment Variables", "Environment Variable Reference", "environment-variable-reference",
             "## Test Configuration",
             "Every environment variable the stack reads, its default, and which service consumes it."),
            ("## Directory Layout", "Directory Layout Reference", "directory-layout-reference",
             "## Test Configuration",
             "The annotated repository tree, with the purpose of every directory and key file."),
            ("## Security Architecture", "Security Architecture Reference", "security-architecture-reference",
             "## Test Configuration",
             "The stack's trust boundaries, bind posture, and the secret-delivery path."),
            ("## Testing", "Testing Reference", "testing-reference",
             "## Test Configuration",
             "Per-suite detail: what each test file covers and the marker it carries."),
            ("## Documentation", "Documentation Reference", "documentation-reference",
             "## Test Configuration",
             "The documentation set, what each document is for, and where it lives."),
        ],
    },
    "juniper-data-client": {
        "python": CANOPY_PY,
        "sections": [
            ("## Public API", "Public API Reference", "public-api-reference",
             "## NPZ Artifact Schema",
             "Every public entry point, its signature, and the exception it raises."),
            ("## Directory Structure", "Directory Structure Reference", "directory-structure-reference",
             "## NPZ Artifact Schema",
             "The annotated source tree, with the purpose of every package and key module."),
            ("## Key Files", "Key Files Reference", "key-files-reference",
             "## NPZ Artifact Schema",
             "Per-file reference for the modules a change is most likely to touch."),
            ("## Architecture & Design Patterns", "Architecture and Design Patterns Reference", "architecture-and-design-patterns-reference",
             "## NPZ Artifact Schema",
             "The client's layering, retry/backoff design, and the patterns a new method must follow."),
            ("## Constants", "Constants Reference", "constants-reference",
             "## NPZ Artifact Schema",
             "Every exported constant, its default, and the failure each one guards against."),
            ("## CI/CD", "CI/CD Reference", "cicd-reference",
             "## NPZ Artifact Schema",
             "Per-workflow reference for `.github/workflows/`, including the contract each job must not break."),
        ],
    },
}


# Repos where the OWNER chose a ceiling raise INSTEAD of a cut (decision 2026-08-28). The value is
# a POLICY ceiling -- the size at which a cut becomes worthwhile in that repo -- not a slack-derived
# one. juniper-recurrence's AGENTS.md is 11.5K across 6 sections and it has no docs/REFERENCE.md;
# splitting a file that small buys little, while its 2,120 headroom is ~15 days at ~137 chars/day.
RAISE_PLAN: dict[str, dict] = {
    "juniper-recurrence": {
        "python": CANOPY_PY,
        "workflow": ".github/workflows/memory-budget.yml",
        "new_ceiling": 20000,
        "why": (
            "the size at which a cut becomes worthwhile in this repo -- below ~20K there is too "
            "little reference material to be worth splitting into a docs/REFERENCE.md this repo "
            "does not yet have"
        ),
    },
}

RAISE_BRANCH = "chore/p5-ceiling-raise"
RAISE_TRAILER = f"Allow-Ceiling-Raise: {GOVERNED}"


def dest_of(repo: str) -> str:
    """The destination for this repo's cut. Per-plan, defaulting to DEST.

    Each cut stays SINGLE-destination. This is not the multi-dest G3 union (see the prep note
    §6d) -- it exists so juniper-canopy's agreed split can ship as two sequential single-dest
    PRs, each of which `relocation_check.py` can verify with its one `--dest` as-is.
    """
    return PLAN.get(repo, {}).get("dest", DEST)


class Stop(RuntimeError):
    """A precondition failed; nothing after it may run."""


def run(argv: list[str], cwd: Path | None = None, expect: int | None = 0, quiet: bool = False) -> subprocess.CompletedProcess:
    proc = subprocess.run(argv, cwd=str(cwd) if cwd else None, capture_output=True, text=True, check=False)  # nosec B603 -- fixed argv
    if expect is not None and proc.returncode != expect:
        raise Stop(f"exit {proc.returncode} (expected {expect}): {' '.join(argv)}\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
    if not quiet and proc.stdout.strip():
        print(proc.stdout.rstrip())
    return proc


def step(title: str) -> None:
    print(f"\n== {title}")


def state_path(repo: str) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR / f"{repo}.json"


def measure_growth(wt: Path) -> dict:
    """Largest single growing AGENTS.md commit over 30 days, measured at origin/main.

    `--ref` matters: without it the helper reads the checkout's HEAD, so a worktree that
    has not fetched reports yesterday's main as today's rate (the flag was lost in the
    #1378 -> #1379 fold and restored in ml#1398).
    """
    proc = run([sys.executable, str(ML / PORT_HELPER), "measure-growth", str(wt), "--days", "30", "--ref", "origin/main"], quiet=True)
    out = proc.stdout
    m = re.search(r"max\s+(\d+)", out)
    if not m:
        raise Stop(f"could not parse a max growth from measure-growth:\n{out}")
    return {"max": int(m.group(1)), "raw": out.strip()}


def relocate_all(wt: Path, repo: str) -> list[dict]:
    dest = dest_of(repo)
    moved = []
    for heading, title, anchor, before, pointer in PLAN[repo]["sections"]:
        before_chars = len((wt / GOVERNED).read_text(encoding="utf-8"))
        run([
            sys.executable, str(ML / RELOCATE),
            "--repo-root", str(wt), "--source", GOVERNED, "--dest", dest,
            "--heading", heading, "--dest-title", title, "--anchor", anchor,
            "--insert-before", before, "--pointer", pointer,
        ], quiet=True)
        after_chars = len((wt / GOVERNED).read_text(encoding="utf-8"))
        delta = before_chars - after_chars
        if delta <= 0:
            raise Stop(f"{heading!r} did not shrink AGENTS.md (delta {delta}) -- did the pointer replace nothing?")
        print(f"   moved {heading:<48} -{delta:>7,} chars")
        moved.append({"heading": heading, "dest_title": title, "anchor": anchor, "removed": delta})
    return moved


def anchorise(title: str) -> str:
    """GitHub's heading -> anchor slug, for matching an existing TOC entry."""
    slug = title.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    return re.sub(r"\s+", "-", slug).strip("-")


def fix_toc(wt: Path, repo: str) -> int:
    """Add the relocated sections to the destination's Table of Contents.

    The relocate script maintains headings and pointers but knows nothing about a TOC, and every
    destination REFERENCE.md in this fleet carries one. Left alone it silently omits the new
    sections -- a stale index over correct content, which is the [[relocation]] failure mode this
    plan cares about most: a reader who trusts the index concludes the material is not there.

    Each entry is inserted immediately before the TOC line for that section's `--insert-before`
    heading, so TOC order keeps matching document order. Returns the number of entries added.
    """
    path = wt / dest_of(repo)
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    toc_start = next((i for i, ln in enumerate(lines) if ln.strip().lower() == "## table of contents"), None)
    if toc_start is None:
        print("   no Table of Contents in the destination; nothing to update")
        return 0
    toc_end = next((i for i in range(toc_start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    added = 0
    for _heading, title, anchor, before, _pointer in PLAN[repo]["sections"]:
        if f"(#{anchor})" in "".join(lines[toc_start:toc_end]):
            continue
        before_anchor = anchorise(before[3:])
        at = next((i for i in range(toc_start, toc_end) if f"(#{before_anchor})" in lines[i]), None)
        if at is None:
            # A PARTIAL TOC is normal and must not be a hard stop. juniper-canopy's
            # docs/DOCUMENTATION_OVERVIEW.md lists 8 of its 15 sections, stopping well before the
            # `--insert-before` anchor. Appending after the LAST existing entry still preserves
            # document order here, because every unlisted section sits after every listed one --
            # but say so out loud rather than silently choosing a position: a TOC entry in the
            # wrong place is exactly the stale-index failure this whole exercise is about.
            last = max((i for i in range(toc_start, toc_end) if lines[i].lstrip().startswith("- [")), default=None)
            if last is None:
                raise Stop(f"destination TOC has no entries at all; cannot place {title!r}")
            at = last + 1
            print(f"   !! TOC does not list {before!r}; appending after the last entry "
                  f"({lines[last].strip()[:48]}) — verify order")
        lines.insert(at, f"- [{title}](#{anchor})\n")
        toc_end += 1
        added += 1
        print(f"   TOC += {title}")
    path.write_text("".join(lines), encoding="utf-8")
    return added


def edit_budget(text: str, old: int, new: int, chars: int, slack: int, growth: dict, dest: str = DEST) -> str:
    data = json.loads(text)
    if data["files"][GOVERNED]["ceiling_chars"] != old:
        raise Stop(f"budget ceiling is not {old}")
    data["files"][GOVERNED]["ceiling_chars"] = new
    data["_note"] = (
        f"P5 step e (the cut): {GOVERNED} relocated to {dest} verbatim, {chars:,} chars remaining. "
        f"Ceiling lowered {old:,} -> {new:,} = size + {slack:,} slack, where slack is "
        f"max(largest single 30-day growing commit, {SLACK_FLOOR:,} fleet fan-out floor). "
        f"Set by hand, NOT by --ratchet: run straight after a cut --ratchet leaves zero headroom "
        f"and fails the next author on one character. Re-measured {dt.date.today().isoformat()}."
    )
    return json.dumps(data, indent=2) + "\n"


def cmd_prepare(repo: str, reuse: bool = False) -> int:
    if repo not in PLAN:
        raise Stop(f"no cut plan for {repo}; known: {sorted(PLAN)}")
    cfg = PLAN[repo]
    dest = dest_of(repo)
    primary = JUNIPER / repo
    if not primary.is_dir():
        raise Stop(f"primary checkout missing: {primary}")

    step(f"{repo}: fetch origin in the primary; dup-guard on branch + worktree")
    run(["git", "-C", str(primary), "fetch", "origin", "--quiet"], quiet=True)
    existing = run(["git", "-C", str(primary), "branch", "--list", BRANCH], quiet=True).stdout.strip()
    taken = sorted(WORKTREES.glob(f"{repo}--{SAFE_BRANCH}--*"))
    sha = run(["git", "-C", str(primary), "rev-parse", "--short=8", "origin/main"], quiet=True).stdout.strip()
    if existing or taken:
        if not reuse:
            raise Stop(f"branch/worktree already exists for {repo} ({existing!r}, {taken}) -- a peer may hold it; STOP (or --reuse if it is yours)")
        if len(taken) != 1:
            raise Stop(f"--reuse needs exactly one worktree, found {taken}")
        wt = taken[0]
        ahead = run(["git", "-C", str(wt), "log", "--oneline", "origin/main..HEAD"], quiet=True).stdout.strip()
        if ahead:
            raise Stop(f"--reuse refused: {wt} has commits beyond origin/main:\n{ahead}")
        # `checkout -- .` restores the working tree FROM THE INDEX, so it leaves staged edits in
        # place -- and prepare's temp-commit unwind (`reset --soft`) leaves exactly that. Hard-reset
        # instead. Safe only because the branch was just proven to carry no commits beyond
        # origin/main; untracked and ignored files are untouched either way.
        run(["git", "-C", str(wt), "reset", "--hard", "origin/main"], quiet=True)
        if run(["git", "-C", str(wt), "status", "--short"], quiet=True).stdout.strip():
            raise Stop(f"--reuse refused: {wt} still dirty after discarding edits")
        print(f"   REUSING {wt} (reset to origin/main {sha})")
    else:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
        wt = WORKTREES / f"{repo}--{SAFE_BRANCH}--{stamp}--{sha}"
        run(["git", "-C", str(primary), "worktree", "add", "-b", BRANCH, str(wt), "origin/main"], quiet=True)
        print(f"   worktree {wt}\n   branch {BRANCH} @ origin/main {sha}")

    for required in (GOVERNED, dest, CONF):
        if not (wt / required).is_file():
            raise Stop(f"{repo} has no {required} -- this cut plan assumes it exists")

    step("re-measure the 30-day burn (never transcribe)")
    growth = measure_growth(wt)
    print("   " + growth["raw"].replace("\n", "\n   "))

    before_chars = len((wt / GOVERNED).read_text(encoding="utf-8"))
    before_dest = len((wt / dest).read_text(encoding="utf-8"))
    old = json.loads((wt / CONF).read_text(encoding="utf-8"))["files"][GOVERNED]["ceiling_chars"]

    step(f"relocate {len(cfg['sections'])} sections verbatim ({GOVERNED} -> {dest})")
    moved = relocate_all(wt, repo)

    step("update the destination's Table of Contents (the relocate script does not)")
    toc_added = fix_toc(wt, repo)

    step("bump AGENTS.md Last Updated (the AGENTS.md Date Check fails a PR that does not)")
    bump_last_updated(wt)

    chars = len((wt / GOVERNED).read_text(encoding="utf-8"))
    dest_chars = len((wt / dest).read_text(encoding="utf-8"))
    slack = max(growth["max"], SLACK_FLOOR)
    new = chars + slack
    step(f"{GOVERNED} {before_chars:,} -> {chars:,} ({chars - before_chars:+,}); "
         f"{dest} {before_dest:,} -> {dest_chars:,} ({dest_chars - before_dest:+,})")
    print(f"   ceiling {old:,} -> {new:,} = {chars:,} + {slack:,} slack "
          f"(max single commit {growth['max']:,} vs floor {SLACK_FLOOR:,})")
    if new >= old:
        raise Stop(f"a cut must LOWER the ceiling; {new:,} >= {old:,}")

    (wt / CONF).write_text(edit_budget((wt / CONF).read_text(encoding="utf-8"), old, new, chars, slack, growth, dest), encoding="utf-8")

    # The controls below are DIFF-based (origin/main..HEAD), so they need a commit to read.
    # Run them against a temporary UNSIGNED commit, then `reset --soft` so `ship` still makes the
    # single real signed commit. Without this the check sees an empty diff and -- to its credit --
    # refuses with "would have passed vacuously" rather than reporting success (rc=2).
    step("temporary unsigned commit, so the diff-based controls have something to read")
    run(["git", "-C", str(wt), "add", GOVERNED, dest, CONF], quiet=True)
    run(["git", "-C", str(wt), "commit", "--no-gpg-sign", "-q", "-m", "temp: P5 cut, for local verification only"], quiet=True)

    try:
        step("CONTENT-LOSS CONTROL: relocation_check --expect-removals (this local run IS the control)")
        reloc = run([sys.executable, str(ML / RELOCHECK), "--repo-root", str(wt),
                     "--base", "origin/main", "--head", "HEAD",
                     "--source", GOVERNED, "--dest", dest, "--expect-removals"], expect=None)
        if reloc.returncode != 0:
            raise Stop(f"relocation check FAILED (rc={reloc.returncode}) -- content was lost, not moved:\n{reloc.stdout[-3000:]}\n{reloc.stderr[-2000:]}")
        print("   relocation check PASSED — every removed substantive line reappears in the destination")

        step("budget check against the new ceiling (clean tree must exit 0)")
        run([sys.executable, str(ML / BUDGET), "--repo-root", str(wt)], expect=0)

        step("target's own pre-commit on the three changed files")
        pc = run(["pre-commit", "run", "--files", GOVERNED, dest, CONF], cwd=wt, expect=None)
        if pc.returncode != 0:
            raise Stop(f"pre-commit failed:\n{pc.stdout[-4000:]}")
    finally:
        # Always unwind the temp commit -- a Stop above must not leave a commit behind that
        # `ship`'s "exactly the three prepared files" guard would then misread as a peer's work.
        run(["git", "-C", str(wt), "reset", "--soft", "origin/main"], quiet=True)
        print("   temp commit unwound; the three files remain staged for `ship`")

    scratch = STATE_DIR / f"{repo}.scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    state = {
        "repo": repo, "worktree": str(wt), "branch": BRANCH, "base_sha": sha,
        "before_chars": before_chars, "chars": chars, "before_dest": before_dest, "dest_chars": dest_chars,
        "old_ceiling": old, "new_ceiling": new, "slack": slack, "growth": growth, "moved": moved,
        "dest": dest,
        "toc_added": toc_added,
        "prepared_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    state_path(repo).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    (scratch / "COMMIT_MSG.txt").write_text(commit_message(state), encoding="utf-8")
    (scratch / "PR_BODY.md").write_text(pr_body(state), encoding="utf-8")
    print(f"\n== PREPARED {repo}: {GOVERNED} {before_chars:,} -> {chars:,}, ceiling {old:,} -> {new:,}")
    print(f"   review the diff in {wt}, then: ship {repo}")
    return 0


def commit_message(s: dict) -> str:
    dest = s.get("dest", DEST)
    repo, moved = s["repo"], s["moved"]
    saved = s["before_chars"] - s["chars"]
    lines = [
        f"docs(p5): cut {GOVERNED} {s['before_chars']:,} -> {s['chars']:,} chars; relocate {len(moved)} reference sections",
        "",
        f"Plan §P5 step e (the cut) for {repo}. {GOVERNED} is resident in every session's",
        f"context; {dest} is read on demand. Moving reference material between them is the",
        "only lever that lowers the resident cost without losing anything.",
        "",
        "Relocated VERBATIM via util/ad-hoc/2026-08-19_p3_relocate_section.py, so G3 passes by",
        "construction rather than by the author's judgement -- the failure this effort exists to",
        "prevent is a well-meaning author dropping prose while keeping the identifiers:",
        "",
    ]
    for m in moved:
        lines.append(f"  {m['heading']:<48} -{m['removed']:>7,} chars -> {dest} § {m['dest_title']}")
    lines += [
        "",
        f"{GOVERNED} {s['before_chars']:,} -> {s['chars']:,} ({-saved:+,}); {dest} {s['before_dest']:,} -> {s['dest_chars']:,}",
        f"(+{s['dest_chars'] - s['before_dest']:,}). Each source heading stays, with a one-line pointer, so the",
        "docs-deletion screen sees no heading deletion.",
        "",
        f"Ceiling {s['old_ceiling']:,} -> {s['new_ceiling']:,} = {s['chars']:,} + {s['slack']:,} slack, where slack is",
        f"max(largest single 30-day growing commit {s['growth']['max']:,}, {SLACK_FLOOR:,} fleet fan-out floor).",
        "Set BY HAND, not by --ratchet: run straight after a cut --ratchet leaves zero headroom",
        "and fails the next author on a single character.",
        "",
        "Verification: util/relocation_check.py --expect-removals PASSED locally against",
        "origin/main -- that local run IS the content-loss control, because G3 runs --advisory",
        "in CI and does not exist post-merge, so a green PR proves nothing (plan §7.2). Budget",
        "check exits 0 on the clean tree against the new ceiling. The repo's own pre-commit passes.",
        "",
        "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>",
        f"Claude-Session: {SESSION_URL}",
    ]
    return "\n".join(lines) + "\n"


def pr_body(s: dict) -> str:
    dest = s.get("dest", DEST)
    repo, moved = s["repo"], s["moved"]
    rows = "\n".join(
        f"| `{m['heading'][3:]}` | {m['removed']:,} | [§ {m['dest_title']}](../{dest}#{m['anchor']}) |" for m in moved
    )
    return f"""## Summary

Plan §P5 **step e — the cut** for `{repo}`. `{GOVERNED}` is resident in every session's context;
`{dest}` is read on demand. Relocating reference material between them is the only lever that lowers
the resident cost without losing anything.

**`{GOVERNED}` {s['before_chars']:,} → {s['chars']:,} chars ({s['chars'] - s['before_chars']:+,}).**
`{dest}` {s['before_dest']:,} → {s['dest_chars']:,} ({s['dest_chars'] - s['before_dest']:+,}).

## What moved

| Section | chars | now at |
|---|---:|---|
{rows}

Each source heading **stays**, with a one-line pointer under it, so the docs-deletion screen sees no
heading deletion and a reader still finds the topic where they expect it.

## Why this is safe

Relocation is **byte-for-byte**, done by
[`util/ad-hoc/2026-08-19_p3_relocate_section.py`](https://github.com/pcalnon/juniper-ml/blob/main/util/ad-hoc/2026-08-19_p3_relocate_section.py)
rather than by hand, so G3 passes **by construction** instead of by the author's judgement. The
failure this whole effort exists to prevent is a well-meaning author dropping prose while keeping the
identifiers, and hand-editing is exactly how that happens.

`util/relocation_check.py --expect-removals` **PASSED locally** against `origin/main`. That local run
**is** the content-loss control: G3 runs `--advisory` in CI and does not exist post-merge, so a green
PR proves nothing (plan §7.2).

## Ceiling

**{s['old_ceiling']:,} → {s['new_ceiling']:,}** = {s['chars']:,} + **{s['slack']:,} slack**, where slack is
`max(largest single 30-day growing commit {s['growth']['max']:,}, {SLACK_FLOOR:,} fleet fan-out floor)` —
re-measured in this worktree at `origin/main`, never transcribed.

Set **by hand, not by `--ratchet`**: run straight after a cut, `--ratchet` leaves ZERO headroom and
fails the next author on a single character (plan step b). The {SLACK_FLOOR:,} floor exists because one
fleet-wide `AGENTS.md` fan-out added +1,982 chars to six repos at once on 2026-08-21 — a zero-slack
ceiling fires fleet-wide on the first such sweep, by construction.

## Testing

- `util/relocation_check.py --expect-removals` — PASSED (the content-loss control)
- `util/memory_budget_check.py` on the clean tree against the new ceiling — exit 0
- the repo's own `pre-commit run --files` on all three changed files — passed

## Ordering note for the merge

Per the plan's standing hazard: **this must land on `main` with the primary checkout pulled before any
worktree carries the trimmed file.** A trimmed worktree sitting over an untrimmed ancestor loads *both*
copies, so context goes **up** — the one ordering mistake that makes the exercise counter-productive.

## Requirements

No tracked `JR-*` requirement covers the memory-budget ratchet; section left deliberately empty rather
than citing an ID that does not exist.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

{SESSION_URL}
"""


def cmd_ship(repo: str) -> int:
    state = json.loads(state_path(repo).read_text(encoding="utf-8"))
    wt = Path(state["worktree"])
    scratch = STATE_DIR / f"{repo}.scratch"
    msg, body = scratch / "COMMIT_MSG.txt", scratch / "PR_BODY.md"
    if not (wt.is_dir() and body.is_file()):
        raise Stop("nothing prepared; run `prepare` first")
    msg.write_text(commit_message(state), encoding="utf-8")
    body.write_text(pr_body(state), encoding="utf-8")
    title = msg.read_text(encoding="utf-8").splitlines()[0]

    step(f"{repo}: worktree still exactly the three prepared files")
    ahead = run(["git", "-C", str(wt), "log", "--oneline", "origin/main..HEAD"], quiet=True).stdout.strip().splitlines()
    if ahead:
        pushed = run(["git", "ls-remote", "--heads", "origin", BRANCH], cwd=wt, quiet=True).stdout.strip()
        if pushed or len(ahead) != 1:
            raise Stop(f"branch already has commits ({ahead}) and pushed={bool(pushed)}; refusing to double-ship")
        run(["git", "-C", str(wt), "reset", "--soft", "origin/main"], quiet=True)
        print(f"   replaced the unpushed commit {ahead[0]}")
    status = run(["git", "-C", str(wt), "status", "--short"], quiet=True).stdout.strip().splitlines()
    changed = sorted(ln.split()[-1] for ln in status)
    if changed != sorted([GOVERNED, state.get("dest", DEST), CONF]):
        raise Stop(f"working tree drifted since prepare (a peer?): {status}")

    step("signed commit (YubiKey)")
    run(["git", "-C", str(wt), "add", GOVERNED, state.get("dest", DEST), CONF], quiet=True)
    run(["git", "-C", str(wt), "commit", "-S", "-q", "-F", str(msg)], quiet=True)
    head = run(["git", "-C", str(wt), "rev-parse", "--short=8", "HEAD"], quiet=True).stdout.strip()
    sig = run(["git", "-C", str(wt), "log", "-1", "--format=%G?"], quiet=True).stdout.strip()
    if sig not in ("G", "U"):
        raise Stop(f"commit is not signed (%G?={sig})")
    print(f"   {head} signature status %G?={sig}")

    step("push + PR")
    run(["git", "-C", str(wt), "push", "-u", "origin", BRANCH], quiet=True)
    proc = run(["gh", "pr", "create", "--repo", f"pcalnon/{repo}", "--base", "main",
                "--head", BRANCH, "--title", title, "--body-file", str(body)], quiet=True)
    url = proc.stdout.strip().splitlines()[-1]
    number = int(url.rstrip("/").rsplit("/", 1)[-1])
    print(f"   {url}")

    step("attribution + signature as GitHub sees them (a green rollup does not imply a mergeable PR)")
    run(["gh", "api", f"repos/pcalnon/{repo}/pulls/{number}/commits", "--jq",
         '.[]|"verified=\\(.commit.verification.verified) reason=\\(.commit.verification.reason) login=\\(.author.login//"UNATTRIBUTED")"'])

    state.update({"pr": number, "pr_url": url, "head": head,
                  "shipped_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
    state_path(repo).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"\n== SHIPPED {repo}#{number} head {head}: {GOVERNED} {state['before_chars']:,} -> {state['chars']:,}")
    print(f"   REMINDER: after merge, pull {JUNIPER / repo} BEFORE any worktree carries the trimmed file.")
    return 0


def cmd_raise(repo: str) -> int:
    """Raise a ceiling INSTEAD of cutting, under an Allow-Ceiling-Raise trailer.

    One repo, one file (plus a stale-pointer fix in its config prose). Prepares and ships in one
    pass: unlike the cut there is no diff-based control to satisfy, so there is nothing to inspect
    between the two halves -- the negative control IS the check refusing an undeclared raise, which
    this runs explicitly before adding the trailer.
    """
    if repo not in RAISE_PLAN:
        raise Stop(f"no raise plan for {repo}; known: {sorted(RAISE_PLAN)}")
    cfg = RAISE_PLAN[repo]
    primary = JUNIPER / repo
    if not primary.is_dir():
        raise Stop(f"primary checkout missing: {primary}")

    step(f"{repo}: fetch origin in the primary; dup-guard on branch + worktree")
    run(["git", "-C", str(primary), "fetch", "origin", "--quiet"], quiet=True)
    safe = RAISE_BRANCH.replace("/", "--")
    if run(["git", "-C", str(primary), "branch", "--list", RAISE_BRANCH], quiet=True).stdout.strip() or sorted(WORKTREES.glob(f"{repo}--{safe}--*")):
        raise Stop(f"branch/worktree already exists for {repo} -- a peer may hold it; STOP")
    sha = run(["git", "-C", str(primary), "rev-parse", "--short=8", "origin/main"], quiet=True).stdout.strip()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    wt = WORKTREES / f"{repo}--{safe}--{stamp}--{sha}"
    run(["git", "-C", str(primary), "worktree", "add", "-b", RAISE_BRANCH, str(wt), "origin/main"], quiet=True)
    print(f"   worktree {wt}")

    step("re-measure the 30-day burn (never transcribe)")
    growth = measure_growth(wt)
    print("   " + growth["raw"].replace("\n", "\n   "))

    chars = len((wt / GOVERNED).read_text(encoding="utf-8"))
    conf_text = (wt / CONF).read_text(encoding="utf-8")
    data = json.loads(conf_text)
    old = data["files"][GOVERNED]["ceiling_chars"]
    new = cfg["new_ceiling"]
    if new <= old:
        raise Stop(f"a raise must increase the ceiling; {new:,} <= {old:,}")
    step(f"{GOVERNED} {chars:,} chars; ceiling {old:,} -> {new:,} (headroom {new - chars:,})")

    data["files"][GOVERNED]["ceiling_chars"] = new
    data["files"][GOVERNED]["_note"] = (
        f"Seeded 2026-08-25 at 11,578 chars (zero slack, advisory soak); raised 2026-08-26 to {old:,} "
        f"(+2,120 measured slack) when --advisory was removed (plan P5 step d). RAISED AGAIN "
        f"{dt.date.today().isoformat()} to {new:,} under an Allow-Ceiling-Raise: {GOVERNED} trailer. "
        f"This raise is a POLICY ceiling, not a slack-derived one: it is {cfg['why']}. The owner chose "
        f"a raise over a cut for this repo on 2026-08-28 (plan P5 step e scoping). At the re-measured "
        f"burn the headroom is ~{(new - chars) // max(1, _rate(growth)) if _rate(growth) else 0} days; "
        f"revisit with a real cut if {GOVERNED} approaches {new:,}. Growth past the ceiling FAILS the "
        f"check; Allow-Budget-Overrun: {GOVERNED} is the loan. After a cut, lower by hand with "
        f"re-measured slack -- never bare --ratchet, which leaves zero headroom."
    )
    # The config prose points at a file this repo does not have: recurrence has no ci.yml, its job
    # lives in a standalone workflow. A pointer to a nonexistent file is the kind of small wrongness
    # that survives for months because nothing validates prose.
    #
    # The _README is a LIST OF LINES and the sentence wraps, so "ci.yml." lands at the START of the
    # NEXT element ("ci.yml. CHARACTERS, not bytes ..."). A first attempt matched only lines that
    # also mentioned the job, and a whole-element equality test -- it silently changed nothing while
    # the commit message claimed the fix. Rewrite every element, then ASSERT the token is gone.
    wf_name = Path(cfg["workflow"]).name
    data["_README"] = [re.sub(r"\bci\.yml\b", wf_name, ln) for ln in data["_README"]]
    if any("ci.yml" in ln for ln in data["_README"]):
        raise Stop("the _README still references ci.yml after the rewrite")
    if not any(wf_name in ln for ln in data["_README"]):
        raise Stop(f"the _README rewrite produced no reference to {wf_name} -- it matched nothing")
    print(f"   _README: ci.yml -> {wf_name}")
    (wt / CONF).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    step("NEGATIVE CONTROL: the raise must FAIL the check until the trailer declares it")
    undeclared = run([sys.executable, str(ML / BUDGET), "--repo-root", str(wt), "--base-ref", "origin/main"], expect=None)
    if undeclared.returncode == 0:
        raise Stop("an UNDECLARED ceiling raise exited 0 -- the gate is not biting; refusing to ship")
    print(f"   undeclared raise exits {undeclared.returncode} (rule 4 bites)")

    step("target's own pre-commit on the changed file")
    run(["git", "-C", str(wt), "add", CONF], quiet=True)
    pc = run(["pre-commit", "run", "--files", CONF], cwd=wt, expect=None)
    if pc.returncode != 0:
        raise Stop(f"pre-commit failed:\n{pc.stdout[-4000:]}")

    msg = (
        f"chore(p5): raise the {GOVERNED} ceiling {old:,} -> {new:,}; cut deferred for this repo\n"
        "\n"
        f"Plan §P5 step e scoping, owner decision 2026-08-28: {repo} takes a ceiling raise\n"
        "INSTEAD of a cut. Its AGENTS.md is 11,578 chars across 6 sections and it has no\n"
        "docs/REFERENCE.md; splitting a file that small buys little, while its 2,120 headroom\n"
        f"is ~15 days at the re-measured ~{_rate(growth)} chars/day.\n"
        "\n"
        f"{new:,} is a POLICY ceiling, not a slack-derived one: it is {cfg['why']}.\n"
        f"Headroom becomes {new - chars:,} chars. Revisit with a real cut if AGENTS.md approaches it.\n"
        "\n"
        "Also fixes the config prose, which said the gate is enforced by a job \"in ci.yml\" --\n"
        f"this repo has no ci.yml; the job is standalone in {cfg['workflow']}. A pointer to a\n"
        "file that does not exist is the kind of small wrongness nothing validates.\n"
        "\n"
        "Negative control re-run here: the same raise WITHOUT the trailer exits nonzero, so the\n"
        "gate is demonstrably still biting and this trailer is what permits it.\n"
        "\n"
        "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>\n"
        f"Claude-Session: {SESSION_URL}\n"
        f"{RAISE_TRAILER}\n"
    )
    scratch = STATE_DIR / f"{repo}.scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "COMMIT_MSG.txt").write_text(msg, encoding="utf-8")

    step("signed commit with the Allow-Ceiling-Raise trailer")
    run(["git", "-C", str(wt), "commit", "-S", "-q", "-F", str(scratch / "COMMIT_MSG.txt")], quiet=True)
    trailers = run(["git", "-C", str(wt), "log", "-1", "--format=%(trailers:key=Allow-Ceiling-Raise)"], quiet=True).stdout.strip()
    body_text = run(["git", "-C", str(wt), "log", "-1", "--format=%B"], quiet=True).stdout
    if RAISE_TRAILER not in trailers or not re.search(r"^Allow-Ceiling-Raise:\s*AGENTS\.md\s*$", body_text, flags=re.MULTILINE):
        raise Stop(f"the commit lost its trailer: git sees {trailers!r}")
    head = run(["git", "-C", str(wt), "rev-parse", "--short=8", "HEAD"], quiet=True).stdout.strip()
    sig = run(["git", "-C", str(wt), "log", "-1", "--format=%G?"], quiet=True).stdout.strip()
    print(f"   {head} %G?={sig}  trailer ok (both readings)")

    step("push + PR")
    run(["git", "-C", str(wt), "push", "-u", "origin", RAISE_BRANCH], quiet=True)
    body = scratch / "PR_BODY_RAISE.md"
    body.write_text(
        f"""## Summary

Plan §P5 **step e scoping**, owner decision 2026-08-28: `{repo}` takes a **ceiling raise instead of a
cut**. Its `{GOVERNED}` is 11,578 chars across 6 sections and it has **no `docs/REFERENCE.md`** —
splitting a file that small buys little, while its 2,120 headroom is **~15 days** at the re-measured
~{_rate(growth)} chars/day.

**Ceiling {old:,} → {new:,}.** Headroom becomes **{new - chars:,} chars**.

This is a **policy ceiling, not a slack-derived one**: {new:,} is {cfg['why']}. Revisit with a real
cut if `{GOVERNED}` approaches it. The other three repos under ~15 days took the cut instead —
cascor-client#142, data#296, data-client#176.

## Also fixed

`conf/memory_budget.json`'s prose said the gate is enforced by a job *"in `ci.yml`"*. **This repo has
no `ci.yml`** — its `Memory Budget` job is standalone in `{cfg['workflow']}`. A pointer to a file that
does not exist is the kind of small wrongness that survives for months because nothing validates prose.

## Verification

- **Negative control re-run here**: the same raise **without** the trailer exits **{undeclared.returncode}**,
  so the gate is demonstrably still biting and this trailer is what permits it. A ceiling raise that
  passed silently would be the vacuous-pass class.
- Trailer verified two ways — git's own parser (last paragraph only) and the exact `MULTILINE` regex
  the checker applies to `git log --format=%B` in CI.
- The repo's own `pre-commit run --files` passes.

## Requirements

No tracked `JR-*` requirement covers the memory-budget ratchet; section left deliberately empty rather
than citing an ID that does not exist.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

{SESSION_URL}
""", encoding="utf-8")
    proc = run(["gh", "pr", "create", "--repo", f"pcalnon/{repo}", "--base", "main", "--head", RAISE_BRANCH,
                "--title", msg.splitlines()[0], "--body-file", str(body)], quiet=True)
    url = proc.stdout.strip().splitlines()[-1]
    number = int(url.rstrip("/").rsplit("/", 1)[-1])
    print(f"   {url}")
    run(["gh", "api", f"repos/pcalnon/{repo}/pulls/{number}/commits", "--jq",
         '.[]|"verified=\\(.commit.verification.verified) reason=\\(.commit.verification.reason) login=\\(.author.login//"UNATTRIBUTED")"'])
    print(f"\n== RAISED {repo}#{number} head {head}: ceiling {old:,} -> {new:,}")
    return 0


def bump_last_updated(wt: Path) -> str | None:
    """Set AGENTS.md's `**Last Updated**:` header to today (UTC).

    Several repos gate this with an "AGENTS.md Date Check" workflow that fails any PR touching
    AGENTS.md without advancing the header date. A cut is the largest AGENTS.md change these repos
    will ever see, so it must carry the bump. Returns the new date, or None if the file has no such
    header (the check exits 0 with a warning in that case).
    """
    path = wt / GOVERNED
    text = path.read_text(encoding="utf-8")
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    new_text, n = re.subn(r"^(\*\*Last Updated\*\*:)[ \t]*\S.*$", rf"\1 {today}", text, count=1, flags=re.MULTILINE)
    if n == 0:
        print(f"   {GOVERNED} has no '**Last Updated**:' header; nothing to bump")
        return None
    path.write_text(new_text, encoding="utf-8")
    # Assert rather than assume -- an edit that silently matches nothing looks exactly like one
    # that worked (this arc has now hit that twice).
    check = re.search(r"^\*\*Last Updated\*\*:\s*(\S+)\s*$", path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    if not check or check.group(1) != today:
        raise Stop(f"the Last Updated bump did not land (reads {check.group(1) if check else 'nothing'!r})")
    print(f"   {GOVERNED} **Last Updated** -> {today}")
    return today


def cmd_bump_date(repo: str) -> int:
    """Bump AGENTS.md's Last Updated header on an already-shipped cut branch, and push."""
    state = json.loads(state_path(repo).read_text(encoding="utf-8"))
    wt = Path(state["worktree"])
    if not wt.is_dir():
        raise Stop(f"worktree is gone: {wt}")
    step(f"{repo}: bump {GOVERNED} Last Updated")
    today = bump_last_updated(wt)
    if today is None:
        return 0
    if not run(["git", "-C", str(wt), "status", "--short"], quiet=True).stdout.strip():
        print("   already current; nothing to commit")
        return 0
    msg = (
        f"docs(p5): bump {GOVERNED} Last Updated to {today} for the cut\n"
        "\n"
        "The AGENTS.md Date Check fails any PR that touches AGENTS.md without advancing its\n"
        f"`**Last Updated**:` header, and a cut is the largest change that file will ever take.\n"
        "\n"
        "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>\n"
        f"Claude-Session: {SESSION_URL}\n"
    )
    run(["git", "-C", str(wt), "add", GOVERNED], quiet=True)
    run(["git", "-C", str(wt), "commit", "-S", "-q", "-m", msg], quiet=True)
    head = run(["git", "-C", str(wt), "rev-parse", "--short=8", "HEAD"], quiet=True).stdout.strip()
    sig = run(["git", "-C", str(wt), "log", "-1", "--format=%G?"], quiet=True).stdout.strip()
    run(["git", "-C", str(wt), "push", "origin", BRANCH], quiet=True)
    print(f"\n== BUMPED {repo}: {head} %G?={sig}, Last Updated -> {today}")
    return 0


def cmd_waive(repo: str) -> int:
    """Verify every relocated heading landed, then add the Allow-Docs-Rewrite waiver commit.

    Why this is a separate, evidence-bearing step rather than a trailer pasted into the cut commit:
    **G3 does not look at headings.** `relocation_check` matches *substantive prose*, and a heading
    is not substantive, so `unmatched=0` says NOTHING about whether the `###` headings survived the
    move. The docs deletion-magnitude screen is what catches heading loss, and the two gates are
    complementary -- neither alone covers a relocation (juniper-ml learned this on its own cut).

    So: re-derive every heading the diff removed from AGENTS.md, assert each one appears in the
    destination at HEAD, and only then write the waiver. Waiving without that check would be
    declaring "intended" about something nothing verified.
    """
    state = json.loads(state_path(repo).read_text(encoding="utf-8"))
    wt = Path(state["worktree"])
    dest = state.get("dest", DEST)
    if not wt.is_dir():
        raise Stop(f"worktree is gone: {wt}")

    step(f"{repo}: re-derive the headings the diff removed from {GOVERNED}")
    diff = run(["git", "-C", str(wt), "diff", "origin/main...HEAD", "--unified=0", "--", GOVERNED], quiet=True).stdout
    removed = [ln[1:].strip() for ln in diff.splitlines()
               if ln.startswith("-") and not ln.startswith("---") and re.match(r"^-#{2,6}\s", ln)]
    if not removed:
        raise Stop("no headings were removed -- nothing to waive; is this the right branch?")
    print(f"   {len(removed)} headings removed from {GOVERNED}")

    step(f"assert every one of them is present in {dest} at HEAD (G3 does NOT check this)")
    dest_text = run(["git", "-C", str(wt), "show", f"HEAD:{dest}"], quiet=True).stdout
    dest_headings = {ln.strip() for ln in dest_text.splitlines() if re.match(r"^#{2,6}\s", ln)}
    missing = [h for h in removed if h not in dest_headings]
    for h in removed:
        print(f"   {'MISSING ' if h in missing else 'present '} {h[:88]}")
    if missing:
        raise Stop(f"{len(missing)} heading(s) removed from {GOVERNED} do NOT appear in {dest}: {missing}\n"
                   "REFUSING to waive -- that is real heading loss, not a relocation.")
    print(f"   all {len(removed)} headings verified present in {dest}")

    msg = (
        f"docs(p5): waive the docs deletion-magnitude screen for the {GOVERNED} relocation\n"
        "\n"
        "The docs screen FAILs with [heading-deletion] on the cut commit: relocating a section\n"
        f"moves its `###` sub-headings into {dest} and removes them from {GOVERNED}, while the\n"
        "`##` heading stays behind with a pointer. That is the intended shape of a relocation,\n"
        "and the screen is right to make it declare itself.\n"
        "\n"
        "Waiver rationale\n"
        "----------------\n"
        f"Verified before waiving: all {len(removed)} headings removed from {GOVERNED} are present\n"
        f"in {dest} at this HEAD, checked by re-deriving them from the diff and matching against\n"
        "the destination's own headings -- not assumed from the relocation being mechanical.\n"
        "\n"
        "This check is NOT redundant with G3. `relocation_check` matches substantive PROSE and\n"
        "skips headings entirely, so its `unmatched=0` says nothing about heading survival; the\n"
        "docs screen is what covers that. The two gates are complementary and neither alone\n"
        "covers a relocation.\n"
        "\n"
        "Verification on the cut commit:\n"
        f"  G3 (--expect-removals)   removed_substantive={state.get('g3_removed', 'see PR')}  unmatched=0\n"
        f"  headings                 {len(removed)} removed from {GOVERNED}, {len(removed)} present in {dest}\n"
        f"  memory budget            ceiling {state['old_ceiling']:,} -> {state['new_ceiling']:,} (downward)\n"
        "  pre-commit               all hooks pass\n"
        "\n"
        "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>\n"
        f"Claude-Session: {SESSION_URL}\n"
        f"Allow-Docs-Rewrite: {GOVERNED}\n"
    )
    scratch = STATE_DIR / f"{repo}.scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    waiver = scratch / "WAIVER_MSG.txt"
    waiver.write_text(msg, encoding="utf-8")

    step("signed waiver commit (empty: it carries only the trailer and its rationale)")
    run(["git", "-C", str(wt), "commit", "-S", "-q", "--allow-empty", "-F", str(waiver)], quiet=True)
    body_text = run(["git", "-C", str(wt), "log", "-1", "--format=%B"], quiet=True).stdout
    if not re.search(r"^Allow-Docs-Rewrite:\s*AGENTS\.md\s*$", body_text, flags=re.MULTILINE):
        raise Stop("the waiver commit lost its trailer")
    head = run(["git", "-C", str(wt), "rev-parse", "--short=8", "HEAD"], quiet=True).stdout.strip()
    sig = run(["git", "-C", str(wt), "log", "-1", "--format=%G?"], quiet=True).stdout.strip()
    print(f"   {head} %G?={sig}  trailer ok")

    step("push (a normal push fires `synchronize`, so CI re-runs; a force-push would not)")
    run(["git", "-C", str(wt), "push", "origin", BRANCH], quiet=True)
    state["waiver_head"] = head
    state["headings_relocated"] = len(removed)
    state_path(repo).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"\n== WAIVED {repo}: {len(removed)} headings verified, Allow-Docs-Rewrite pushed as {head}")
    return 0


def _rate(growth: dict) -> int:
    m = re.search(r"rate\s+:\s+(-?\d+)", growth["raw"])
    return int(m.group(1)) if m else 0


def cmd_status(repo: str) -> int:
    p = state_path(repo)
    print(p.read_text(encoding="utf-8") if p.is_file() else f"nothing recorded for {repo}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[7])
    ap.add_argument("command", choices=["prepare", "ship", "waive", "bump-date", "status", "raise-ceiling"])
    ap.add_argument("repo")
    ap.add_argument("--reuse", action="store_true", help="reuse THIS session's own stalled worktree")
    ns = ap.parse_args(argv)
    try:
        if ns.command == "prepare":
            return cmd_prepare(ns.repo, reuse=ns.reuse)
        if ns.command == "ship":
            return cmd_ship(ns.repo)
        if ns.command == "waive":
            return cmd_waive(ns.repo)
        if ns.command == "bump-date":
            return cmd_bump_date(ns.repo)
        if ns.command == "raise-ceiling":
            return cmd_raise(ns.repo)
        return cmd_status(ns.repo)
    except Stop as exc:
        print(f"\n!! STOP: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
