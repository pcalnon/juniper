#!/usr/bin/env python3
"""
P5 step d, preconditions 2-4, one governed repo per invocation: remove `--advisory` from the
ported memory-budget job, raise the ceiling with RE-MEASURED slack under an
`Allow-Ceiling-Raise: AGENTS.md` trailer, and prove both with negative controls run against the
NON-advisory invocation. Makes NO ruleset change -- promotion to a required context is the
owner's separate decision (juniper-ml util/ad-hoc/2026-08-20_require_context_safely.py).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc — migration (P5 fleet rollout, plan §P5 step d; tracking issue juniper-ml#1326)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-08-25_p5_port_verify.bash (the advisory-era controls this supersedes for
         the promotion step); util/ad-hoc/2026-08-25_p5_port_memory_budget.py (measure-growth);
         util/ad-hoc/2026-08-26_p5_fleet_state.py (the census run before this)

Why a script: each step is a plain command, but the sequence is ~20 of them per repo across
eight sibling repos, and a worktree-isolated session's shell gate refuses loops, command
substitution and long git-bearing chains. One invocation per repo also turns the controls into
reproducible provenance rather than a claim in a PR body.

Why the controls are NEGATIVE where they can be: "a blocking gate that cannot fail is worse than
none" (plan §P5 step d). So this proves the raise FAILS without its trailer (rule 4), growth past
the NEW ceiling FAILS, the loan trailer waives it WITHOUT moving the ceiling, and `--ratchet` on a
copy of the budget tightens by exactly the slack -- i.e. the headroom is real and is what the PR
says it is.

Why slack = max(largest single growing commit over 30 days, 2,000): the plan sizes slack from the
re-measured `max`, never from `p90` (unreliable below ~10 growing commits), and the 2,000 floor
covers the fleet-wide fan-out class -- one 2026-08-21 docs sweep added 1,982 chars to six repos'
AGENTS.md at once, the shape a zero-slack ceiling cannot absorb.

Usage:
    python3 util/ad-hoc/2026-08-26_p5_promote_ready.py prepare <repo>   # worktree + edits + controls + diff; NO commit
    python3 util/ad-hoc/2026-08-26_p5_promote_ready.py ship <repo>      # signed commit + push + PR, after review
    python3 util/ad-hoc/2026-08-26_p5_promote_ready.py status <repo>    # what `prepare` recorded

`prepare` STOPS if the branch or a matching worktree already exists in the target (a peer session
may hold the port -- 2026-08-25 two sessions started from one handoff and collided; never
"replace with a clean-room artifact").
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess  # nosec B404 -- fixed-argv git/gh/python calls; nothing is shell-interpolated
import sys
import textwrap
from pathlib import Path

JUNIPER = Path("/home/pcalnon/Development/python/Juniper")
WORKTREES = JUNIPER / "worktrees"
ML_ROOT = Path(__file__).resolve().parents[2]
MEASURE = ML_ROOT / "util" / "ad-hoc" / "2026-08-25_p5_port_memory_budget.py"
BRANCH = "feat/memory-budget-blocking"
SAFE_BRANCH = BRANCH.replace("/", "--")
TODAY = "2026-08-26"
SLACK_FLOOR = 2000
GOVERNED = "AGENTS.md"
CONF = "conf/memory_budget.json"
STATE_DIR = Path.home() / ".local" / "state" / "juniper-p5-promote"
SESSION_URL = "https://claude.ai/code/session_01Nf2joAmuovs5W3L5Sm6pe2"

CANOPY_PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
CASCOR_PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
DATA_PY = "/opt/miniforge3/envs/JuniperData/bin/python"

REPOS: dict[str, dict[str, str]] = {
    "juniper-canopy": {"python": CANOPY_PY, "workflow": ".github/workflows/ci.yml"},
    "juniper-cascor": {"python": CASCOR_PY, "workflow": ".github/workflows/ci.yml"},
    "juniper-cascor-client": {"python": CANOPY_PY, "workflow": ".github/workflows/ci.yml"},
    "juniper-recurrence": {"python": CANOPY_PY, "workflow": ".github/workflows/memory-budget.yml"},
    "juniper-data-client": {"python": CANOPY_PY, "workflow": ".github/workflows/ci.yml"},
    "juniper-data": {"python": DATA_PY, "workflow": ".github/workflows/ci.yml"},
    # the worker's tests/conftest.py imports the package, which needs juniper_config_tools -- JuniperCascor1 has it
    "juniper-cascor-worker": {"python": CASCOR_PY, "workflow": ".github/workflows/ci.yml"},
    "juniper-deploy": {"python": CANOPY_PY, "workflow": ".github/workflows/ci.yml"},
}

RAISE_TRAILER = f"Allow-Ceiling-Raise: {GOVERNED}\n"
LOAN_TRAILER = f"Allow-Budget-Overrun: {GOVERNED}\n"


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


# --------------------------------------------------------------------------------------------
# measurement
# --------------------------------------------------------------------------------------------


def measure_growth(wt: Path) -> dict:
    proc = run([sys.executable, str(MEASURE), "measure-growth", str(wt), "--days", "30"], quiet=True)
    text = proc.stdout
    m = re.search(r"growth\s*:\s*median\s+(\d+)\s+p90\s+(\d+)\s+max\s+(\d+)", text)
    if not m:
        raise Stop(f"measure-growth output has no growth line:\n{text}")
    rate = re.search(r"rate\s*:\s*(-?\d+) chars/day", text)
    size = re.search(r"size\s*:\s*(\d+) -> (\d+)\s+net ([+-]?\d+)", text)
    commits = re.search(r"commits\s*:\s*(\d+) grew, (\d+) shrank", text)
    window = re.search(r"window\s*:\s*last 30 days, (\d+) commits touching", text)
    return {
        "median": int(m.group(1)),
        "p90": int(m.group(2)),
        "max": int(m.group(3)),
        "rate_per_day": int(rate.group(1)) if rate else None,
        "size_from": int(size.group(1)) if size else None,
        "size_to": int(size.group(2)) if size else None,
        "net": int(size.group(3)) if size else None,
        "grew": int(commits.group(1)) if commits else None,
        "shrank": int(commits.group(2)) if commits else None,
        "touching": int(window.group(1)) if window else None,
        "raw": text.strip(),
    }


# --------------------------------------------------------------------------------------------
# edits
# --------------------------------------------------------------------------------------------


def replace_once(text: str, old: str, new: str, what: str) -> str:
    n = text.count(old)
    if n != 1:
        raise Stop(f"{what}: expected exactly 1 occurrence, found {n}: {old[:80]!r}")
    return text.replace(old, new)


def replace_one_of(text: str, candidates: list[tuple[str, str]], what: str) -> str:
    hits = [(old, new) for old, new in candidates if text.count(old) == 1]
    if len(hits) != 1:
        raise Stop(f"{what}: expected exactly one candidate to match once, got {len(hits)}")
    return text.replace(*hits[0])


def edit_workflow(text: str, repo: str, old: int, new: int, slack: int, growth: dict) -> str:
    # 1. job header line
    text = replace_once(
        text,
        "# Memory Budget (ADVISORY, standalone): P5 port of juniper-ml's size ratchet.",
        "# Memory Budget (BLOCKING, standalone): P5 port of juniper-ml's size ratchet.",
        "header line",
    )
    # 2. the promotion sentence, three rendered variants
    text = replace_one_of(
        text,
        [
            (
                "  # and only after the soak below, with `--advisory` removed and the three negative controls\n"
                "  # re-run against the non-advisory job.\n",
                f"  # and only after the soak below -- which ended {TODAY}: `--advisory` is gone and the three\n"
                "  # negative controls were re-run against the non-advisory job (plan §P5 step d).\n",
            ),
            (
                "  # Safety was promoted -- and only after the soak below.\n",
                f"  # Safety was promoted -- and only after the soak below, which ended {TODAY}.\n",
            ),
            (
                "  # soak below.\n",
                f"  # soak below, which ended {TODAY}.\n",
            ),
        ],
        "promotion sentence",
    )
    # 3. the ADVISORY paragraph
    text = replace_once(
        text,
        "  # ADVISORY during the soak. `--advisory` reports and always exits 0. It is removed only after\n"
        "  # three negative controls pass in this repo -- clean tree exits 0, +500 chars exits 1, and a\n"
        "  # waiver trailer exits 0 -- because a blocking gate that cannot fail is worse than none.\n",
        f"  # BLOCKING as of {TODAY} (plan §P5 step d). The job soaked with `--advisory` from the port's merge,\n"
        "  # and the flag was removed only after three negative controls passed IN THIS REPO against the\n"
        "  # non-advisory invocation -- clean tree exits 0, growth past the ceiling exits 1, and a waiver\n"
        "  # trailer exits 0 -- because a blocking gate that cannot fail is worse than none. Whether this\n"
        "  # context is REQUIRED is decided in the branch ruleset, never here.\n",
        "advisory paragraph",
    )
    # 4. the EXPECT paragraph: from its first line up to (not including) the job key
    lines = text.split("\n")
    starts = [i for i, ln in enumerate(lines) if ln.startswith("  # EXPECT A REPORTED VIOLATION")]
    if len(starts) != 1:
        raise Stop(f"EXPECT paragraph: found {len(starts)} starts")
    start = starts[0]
    try:
        end = next(i for i in range(start, len(lines)) if lines[i] == "  memory-budget:")
    except StopIteration as exc:
        raise Stop("EXPECT paragraph: no `  memory-budget:` key after it") from exc
    if end - start > 12:
        raise Stop(f"EXPECT paragraph: {end - start} lines is implausibly long; refusing")
    prose = (
        f"SLACK, MEASURED HERE. The ceiling was seeded at the exact size on the day the port landed ({old:,} chars, "
        f"zero slack) and raised {TODAY} to {new:,} (+{slack:,}) under an Allow-Ceiling-Raise: AGENTS.md trailer. "
        f"The slack is the largest single AGENTS.md-growing commit re-measured over the 30 days to {TODAY} "
        f"({growth['max']:,}; median {growth['median']:,}, {growth['grew']} grew / {growth['shrank']} shrank, "
        f"~{growth['rate_per_day']} chars/day), floored at {SLACK_FLOOR:,} because one fleet-wide docs fan-out (2026-08-21) "
        "added 1,982 chars to six repos' AGENTS.md at once -- the shape a zero-slack ceiling cannot absorb. "
        "Growth past the ceiling now FAILS this check; Allow-Budget-Overrun: AGENTS.md is the loan for a "
        "warranted overrun, and a cut is what brings the ceiling back down (hand-edit with slack, never bare --ratchet)."
    )
    lines[start:end] = ["  # " + ln for ln in textwrap.wrap(prose, width=94)]
    text = "\n".join(lines)
    # 5. banner (same width: "(ADVISORY)" and "(BLOCKING)" are both 10 chars)
    text = replace_once(text, "Memory File Size Budget (ADVISORY)", "Memory File Size Budget (BLOCKING)", "banner")
    # 6. run-step comment
    text = replace_once(
        text,
        "          # `--advisory` is the SOAK setting and is removed to promote. Escape hatch once this\n"
        "          # blocks, when the growth is genuinely warranted: add the commit trailer\n",
        f"          # BLOCKING as of {TODAY}: `--advisory` (the soak setting) is gone, so a violation exits 1 and\n"
        "          # fails this check. Escape hatch, when the growth is genuinely warranted: add the commit trailer\n",
        "run-step comment",
    )
    # 7. the invocation itself
    text = replace_once(
        text,
        "            --trailers-file memory-budget-trailers.txt \\\n            --advisory\n",
        "            --trailers-file memory-budget-trailers.txt\n",
        "--advisory argument",
    )
    # 8. recurrence's standalone workflow carries a file header and a concurrency comment too
    if repo == "juniper-recurrence":
        text = replace_once(
            text,
            "#    Memory Budget (ADVISORY, standalone) -- P5 port",
            "#    Memory Budget (BLOCKING, standalone) -- P5 port",
            "recurrence file header",
        )
        text = replace_once(
            text,
            "#    aggregate, never a required context, and ADVISORY (`--advisory` reports and exits 0) until\n"
            "#    the three negative controls pass against the non-advisory invocation. Promotion, if ever,\n"
            "#    is an owner-only branch-protection decision; this workflow makes NO protection change.\n",
            "#    aggregate and not a required context. It shipped ADVISORY (`--advisory` reports and exits 0)\n"
            f"#    on 2026-08-25 and went BLOCKING on {TODAY} once the three negative controls passed against\n"
            "#    the non-advisory invocation. Promotion to a required context, if ever, is an owner-only\n"
            "#    branch-protection decision; this workflow makes NO protection change.\n",
            "recurrence header paragraph",
        )
        text = replace_once(
            text,
            "# Per-PR ref, cancel superseded runs: an advisory signal only needs the latest push.",
            "# Per-PR ref, cancel superseded runs: only the latest push's verdict matters.",
            "recurrence concurrency comment",
        )
    for stale in ("(ADVISORY", "ADVISORY during the soak", "EXPECT A REPORTED VIOLATION", "is the SOAK setting", "\n            --advisory"):
        if stale in text:
            raise Stop(f"stale advisory text survived the edit: {stale!r}")
    return text


def edit_budget(text: str, old: int, new: int, slack: int, growth: dict) -> str:
    text = replace_once(text, f'"ceiling_chars": {old}', f'"ceiling_chars": {new}', "ceiling_chars")
    note = (
        f"Seeded 2026-08-25 at {old:,} chars, the size of AGENTS.md IN THIS REPO on the day the port landed "
        f"(zero slack; the job shipped ADVISORY for the soak). RAISED {TODAY} to {new:,} (+{slack:,}) under an "
        f"Allow-Ceiling-Raise: AGENTS.md trailer when --advisory was removed (plan P5 step d): the slack is the "
        f"largest single AGENTS.md-growing commit re-measured here over the 30 days to {TODAY} "
        f"(max {growth['max']:,}, median {growth['median']:,}, ~{growth['rate_per_day']} chars/day), floored at "
        f"{SLACK_FLOOR:,} for the fleet-wide fan-out class that added 1,982 chars to six repos' AGENTS.md at once on "
        f"2026-08-21. Growth past the ceiling now FAILS the check; Allow-Budget-Overrun: AGENTS.md is the loan. "
        f"After a cut, lower it by hand to a value with RE-MEASURED slack -- never bare --ratchet, which leaves zero headroom."
    )
    notes = re.findall(r'^(\s*"_note": )".*"(,?)$', text, flags=re.MULTILINE)
    if len(notes) != 1:
        raise Stop(f"_note: expected exactly 1 single-line note, found {len(notes)}")
    text = re.sub(r'^(\s*"_note": )".*"(,?)$', lambda m: m.group(1) + json.dumps(note) + m.group(2), text, count=1, flags=re.MULTILINE)
    return text


# --------------------------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------------------------


def check(py: str, wt: Path, *extra: str, expect: int) -> str:
    proc = run([py, "util/memory_budget_check.py", "--repo-root", ".", "--base-ref", "origin/main", *extra], cwd=wt, expect=None, quiet=True)
    out = proc.stdout + proc.stderr
    if proc.returncode != expect:
        raise Stop(f"control expected exit {expect}, got {proc.returncode}:\n{out[-3000:]}")
    print(f"   -> exit {proc.returncode} (expected {expect})")
    return out


def controls(py: str, wt: Path, scratch: Path, old: int, new: int, slack: int, workflow: str) -> dict:
    results: dict[str, str] = {}
    agents = wt / GOVERNED
    conf = wt / CONF
    orig = agents.read_bytes()
    conf_edited = conf.read_bytes()
    raise_file = scratch / "trailers-raise.txt"
    both_file = scratch / "trailers-raise-and-loan.txt"
    raise_file.write_text(RAISE_TRAILER, encoding="utf-8")
    both_file.write_text(RAISE_TRAILER + LOAN_TRAILER, encoding="utf-8")

    step("control 0: clean tree, raise NOT declared -> exit 1 (rule 4: the raise needs its trailer)")
    out = check(py, wt, expect=1)
    if "RAISED" not in out.upper():
        raise Stop(f"control 0 failed for the wrong reason:\n{out[-1500:]}")
    results["c0_undeclared_raise"] = "exit 1, rule 4 named the raise"

    step("control 1: clean tree, raise declared -> exit 0 (RAISE-WAIVED)")
    out = check(py, wt, "--trailers-file", str(raise_file), expect=0)
    if "raise" not in out.lower():
        raise Stop(f"control 1 passed without reporting the waived raise:\n{out[-1500:]}")
    results["c1_declared_raise"] = "exit 0, raise waived and reported"

    growth = slack + 500
    step(f"control 2: +{growth:,} chars to AGENTS.md (500 past the NEW ceiling), raise declared -> exit 1")
    with agents.open("ab") as fh:
        fh.write(b"0" * growth)
    check(py, wt, "--trailers-file", str(raise_file), expect=1)
    results["c2_growth_past_new_ceiling"] = f"+{growth:,} chars -> exit 1"

    step("control 3: same growth + Allow-Budget-Overrun -> exit 0 WAIVED, ceiling unchanged")
    out = check(py, wt, "--trailers-file", str(both_file), expect=0)
    if "WAIVED" not in out.upper():
        raise Stop(f"control 3 passed without WAIVED:\n{out[-1500:]}")
    if conf.read_bytes() != conf_edited:
        raise Stop("control 3: the loan moved the ceiling")
    results["c3_loan_waives_without_moving_ceiling"] = "exit 0, WAIVED, budget file byte-identical"

    step("restore AGENTS.md byte-for-byte, then control 1 again")
    agents.write_bytes(orig)
    if agents.read_bytes() != orig:
        raise Stop("restore failed")
    check(py, wt, "--trailers-file", str(raise_file), expect=0)
    results["c4_restore"] = "AGENTS.md byte-identical; exit 0"

    step(f"control 5: --ratchet on a COPY of the budget tightens {new:,} -> {old:,} (headroom == slack, exactly)")
    copy = scratch / "budget.copy.json"
    shutil.copyfile(conf, copy)
    run([py, "util/memory_budget_check.py", "--repo-root", ".", "--budget", str(copy), "--ratchet"], cwd=wt, quiet=True)
    tightened = json.loads(copy.read_text(encoding="utf-8"))["files"][GOVERNED]["ceiling_chars"]
    if tightened != old:
        raise Stop(f"control 5: ratchet on the copy gave {tightened}, expected {old}")
    if conf.read_bytes() != conf_edited:
        raise Stop("control 5: --ratchet on the copy touched the real budget file")
    print(f"   -> copy tightened to {tightened:,}; real budget file untouched")
    results["c5_ratchet_copy"] = f"{new:,} -> {tightened:,}"

    step("control 6: workflow parses; memory-budget standalone (in no needs:), NOT advisory, trailer-aware")
    code = (
        "import sys, yaml\n"
        "d = yaml.safe_load(open(sys.argv[1], encoding='utf-8'))\n"
        "jobs = d['jobs']\n"
        "assert 'memory-budget' in jobs, 'no memory-budget job'\n"
        "assert jobs['memory-budget']['name'] == 'Memory Budget'\n"
        "for name, job in jobs.items():\n"
        "    needs = job.get('needs') or []\n"
        "    needs = [needs] if isinstance(needs, str) else needs\n"
        "    assert 'memory-budget' not in needs, f'memory-budget is in {name}.needs -- C9 violation'\n"
        "run = jobs['memory-budget']['steps'][-1]['run']\n"
        "# comments in the run step legitimately mention `--advisory`; only the command lines matter\n"
        "cmd = '\\n'.join(l for l in run.splitlines() if not l.strip().startswith('#'))\n"
        "assert '--advisory' not in cmd, '--advisory survived as an argument'\n"
        "assert '--trailers-file' in cmd and '--base-ref FETCH_HEAD' in cmd\n"
        "print(f'   ok: {len(jobs)} jobs, memory-budget standalone, non-advisory, trailer-aware')\n"
    )
    run([py, "-c", code, workflow], cwd=wt)
    results["c6_workflow"] = "parses; standalone; non-advisory; trailer-aware"
    return results


# --------------------------------------------------------------------------------------------
# messages
# --------------------------------------------------------------------------------------------


def commit_message(repo: str, old: int, new: int, slack: int, growth: dict, results: dict, suite: str) -> str:
    g = growth
    return f"""feat(ci): memory-budget gate BLOCKING -- drop --advisory, ceiling {old:,} -> {new:,} (+{slack:,} slack)

P5 step d of the shared-session-memory plan (juniper-ml
notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md §P5; tracking issue
juniper-ml#1326): preconditions 2-4 for promoting `Memory Budget` to a required context,
in {repo}.

  2. `--advisory` REMOVED from the standalone memory-budget job. A violation now exits 1 and
     fails the check. Promoting an advisory job would have created a required check that
     cannot fail -- the vacuous-pass class.
  3. The three negative controls re-run IN THIS REPO against the NON-advisory invocation
     (juniper-ml util/ad-hoc/2026-08-26_p5_promote_ready.py, provenance of the run):
       clean tree, raise NOT declared        -> exit 1 (rule 4 names the undeclared raise)
       clean tree, raise declared            -> exit 0, RAISE-WAIVED and reported
       +{slack + 500:,} chars (500 past the new ceiling) -> exit 1
       same growth + Allow-Budget-Overrun    -> exit 0, WAIVED, budget file byte-identical
       AGENTS.md restored byte-for-byte      -> exit 0
       --ratchet on a COPY of the budget     -> {new:,} -> {old:,}: the headroom is exactly the slack
  4. Real slack: ceiling {old:,} -> {new:,} (+{slack:,}), declared with the trailer below. Sized from
     the largest single AGENTS.md-growing commit RE-MEASURED here over the 30 days to {TODAY}
     (max {g['max']:,}, median {g['median']:,}, ~{g['rate_per_day']} chars/day, {g['grew']} grew / {g['shrank']} shrank of
     {g['touching']} commits touching the file), floored at {SLACK_FLOOR:,} for the fleet-wide fan-out class:
     one 2026-08-21 docs sweep added 1,982 chars to six repos' AGENTS.md at once, the shape a
     zero-slack ceiling cannot absorb.

This PR makes NO ruleset change. The job stays standalone and absent from every `needs:`;
whether `Memory Budget` becomes REQUIRED is the owner's separate decision (plan §P5 step d,
juniper-ml util/ad-hoc/2026-08-20_require_context_safely.py, observed-only by default).

Verification: ported suite {suite}; this repo's own pre-commit green on the two changed files;
the workflow re-parsed with memory-budget standalone, `--advisory` absent, `--base-ref FETCH_HEAD`
and `--trailers-file` present.

Allow-Ceiling-Raise: AGENTS.md
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: {SESSION_URL}
"""


def pr_body(repo: str, old: int, new: int, slack: int, growth: dict, suite: str) -> str:
    g = growth
    return f"""P5 step d of the shared-session-memory plan (juniper-ml
`notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md` §P5; tracking issue juniper-ml#1326):
**preconditions 2–4 for promoting `Memory Budget` to a required context**, in {repo}. Precondition 1
(the port merged to `main`) was met for all eight governed repos on 2026-08-26.

| # | Precondition | This PR |
|---|---|---|
| 2 | `--advisory` removed | **Removed.** A violation now exits 1 and fails the check. Promoting an advisory job would create a required check that cannot fail — the vacuous-pass class. |
| 3 | Three negative controls re-run against the **non-advisory** invocation | Run IN THIS REPO by juniper-ml `util/ad-hoc/2026-08-26_p5_promote_ready.py` (provenance), transcript below. |
| 4 | Real slack, declared with `Allow-Ceiling-Raise: AGENTS.md` | Ceiling **{old:,} → {new:,} (+{slack:,})**, trailer in this PR's single commit. |

**Slack, measured here and not transcribed** (`measure-growth`, 30 days to {TODAY}): largest single
`AGENTS.md`-growing commit **{g['max']:,}**, median {g['median']:,}, ~{g['rate_per_day']} chars/day, {g['grew']} grew / {g['shrank']} shrank
of {g['touching']} commits touching the file. Slack = max(largest, {SLACK_FLOOR:,}); the {SLACK_FLOOR:,} floor covers the
fleet-wide fan-out class — one 2026-08-21 docs sweep added 1,982 chars to six repos' `AGENTS.md` at once,
the shape a zero-slack ceiling cannot absorb. Size from `max`, never the helper's `p90` (unreliable
below ~10 growing commits).

**Negative controls against the non-advisory invocation** (each one a control that can FAIL):

    clean tree, raise NOT declared              -> exit 1  (rule 4 names the undeclared raise)
    clean tree, raise declared                  -> exit 0  (RAISE-WAIVED, reported)
    +{slack + 500:,} chars = 500 past the NEW ceiling  -> exit 1
    same growth + Allow-Budget-Overrun: AGENTS.md -> exit 0  (WAIVED, budget file byte-identical)
    AGENTS.md restored byte-for-byte (cmp)      -> exit 0
    --ratchet on a COPY of the budget           -> tightens {new:,} -> {old:,}: headroom is exactly the slack

**NO ruleset change.** The job stays standalone and absent from every `needs:` (plan correction C9).
Whether `Memory Budget` becomes REQUIRED is the owner's separate decision, via juniper-ml
`util/ad-hoc/2026-08-20_require_context_safely.py --repo {repo} --context 'Memory Budget'` (observed-only
by default). Until then a red `Memory Budget` is visible but does not block.

**Verification:** ported suite {suite}; this repo's own pre-commit green on the two changed files; the
workflow re-parsed with `memory-budget` standalone, `--advisory` absent, `--base-ref FETCH_HEAD` and
`--trailers-file` present. The `Allow-Ceiling-Raise` trailer must survive into the squash message
(single-commit PR; `util/safe_merge.py` squash-of-one carries it) — the job reads trailers from
`FETCH_HEAD..HEAD`, and nothing on `main` re-checks the raise after merge.

## Requirements

References the plan's P5 (juniper-ml#1326); no tracked JR requirement changes status.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

{SESSION_URL}
"""


# --------------------------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------------------------


def cmd_prepare(repo: str, reuse: bool = False) -> int:
    cfg = REPOS[repo]
    primary = JUNIPER / repo
    py = cfg["python"]
    workflow = cfg["workflow"]
    if not primary.is_dir():
        raise Stop(f"primary checkout missing: {primary}")

    step(f"{repo}: fetch origin in the primary; dup-guard on branch + worktree")
    run(["git", "-C", str(primary), "fetch", "origin", "--quiet"], quiet=True)
    existing = run(["git", "-C", str(primary), "branch", "--list", BRANCH], quiet=True).stdout.strip()
    taken = sorted(WORKTREES.glob(f"{repo}--{SAFE_BRANCH}--*"))
    sha = run(["git", "-C", str(primary), "rev-parse", "--short=8", "origin/main"], quiet=True).stdout.strip()
    if existing or taken:
        # --reuse: THIS session's own earlier `prepare` stopped part-way (a control failed, or the
        # script was fixed). Reuse is safe only if the worktree is exactly one, carries no commits
        # beyond origin/main, and its base is still origin/main -- then its edits are discarded and
        # everything is regenerated. Anything else is a peer's worktree: STOP.
        if not reuse:
            raise Stop(f"branch/worktree already exists for {repo} ({existing!r}, {taken}) -- a peer may hold it; STOP (or --reuse if it is yours)")
        if len(taken) != 1:
            raise Stop(f"--reuse needs exactly one worktree, found {taken}")
        wt = taken[0]
        ahead = run(["git", "-C", str(wt), "log", "--oneline", "origin/main..HEAD"], quiet=True).stdout.strip()
        if ahead:
            raise Stop(f"--reuse refused: {wt} has commits beyond origin/main:\n{ahead}")
        if run(["git", "-C", str(wt), "rev-parse", "--short=8", "HEAD"], quiet=True).stdout.strip() != sha:
            raise Stop(f"--reuse refused: {wt} is not at origin/main {sha}")
        run(["git", "-C", str(wt), "checkout", "--", "."], quiet=True)
        if run(["git", "-C", str(wt), "status", "--short"], quiet=True).stdout.strip():
            raise Stop(f"--reuse refused: {wt} still dirty after discarding edits")
        print(f"   REUSING {wt} (reset to origin/main {sha})")
    else:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
        wt = WORKTREES / f"{repo}--{SAFE_BRANCH}--{stamp}--{sha}"
        run(["git", "-C", str(primary), "worktree", "add", "-b", BRANCH, str(wt), "origin/main"], quiet=True)
        print(f"   worktree {wt}\n   branch {BRANCH} @ origin/main {sha}")

    step("re-measure the 30-day burn (never transcribe)")
    growth = measure_growth(wt)
    print("   " + growth["raw"].replace("\n", "\n   "))

    budget_text = (wt / CONF).read_text(encoding="utf-8")
    old = json.loads(budget_text)["files"][GOVERNED]["ceiling_chars"]
    chars = len((wt / GOVERNED).read_text(encoding="utf-8"))
    slack = max(growth["max"], SLACK_FLOOR)
    base = max(chars, old)
    new = base + slack
    step(f"ceiling: {GOVERNED} is {chars:,} chars, ceiling {old:,}; slack {slack:,} -> new ceiling {new:,}")
    if chars != old:
        print(f"   !! note: file ({chars:,}) != ceiling ({old:,}); the raise is computed from the larger")

    step(f"edit {workflow} and {CONF}")
    wf_path = wt / workflow
    wf_path.write_text(edit_workflow(wf_path.read_text(encoding="utf-8"), repo, old, new, slack, growth), encoding="utf-8")
    (wt / CONF).write_text(edit_budget(budget_text, old, new, slack, growth), encoding="utf-8")
    if json.loads((wt / CONF).read_text(encoding="utf-8"))["files"][GOVERNED]["ceiling_chars"] != new:
        raise Stop("budget edit did not land")

    scratch = STATE_DIR / f"{repo}.scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    results = controls(py, wt, scratch, old, new, slack, workflow)

    step("ported suite")
    tests = [p for p in wt.rglob("test_memory_budget_check.py") if ".git" not in p.parts]
    if len(tests) != 1:
        raise Stop(f"expected exactly one ported test file, found {tests}")
    test_rel = str(tests[0].relative_to(wt))
    # No `-q` of our own: canopy/cascor already carry `-q` in addopts, and `-qq` drops the summary line.
    proc = run([py, "-m", "pytest", test_rel, "-p", "no:cacheprovider"], cwd=wt, quiet=True)
    summary = re.findall(r"^(.*\b\d+ passed\b.*)$", proc.stdout + proc.stderr, flags=re.MULTILINE)
    if summary:
        suite_line = summary[-1].strip().strip("= ")
    else:
        dots = max((len(ln.strip().split()[0]) for ln in proc.stdout.splitlines() if ln.strip().startswith(".")), default=0)
        suite_line = f"exit 0, {dots} progress dots (summary suppressed by the repo's addopts)"
    print(f"   {test_rel}: {suite_line}")

    step("this repo's own pre-commit on the two changed files")
    proc = run(["pre-commit", "run", "--files", workflow, CONF], cwd=wt, expect=None, quiet=True)
    shown = [ln for ln in proc.stdout.splitlines() if ln.strip() and "Skipped" not in ln]
    print("   " + "\n   ".join(shown[-25:]))
    if proc.returncode != 0:
        raise Stop(f"pre-commit failed (exit {proc.returncode}); see above")

    step("other files that name the job (awareness only; the ported test is expected)")
    run(["git", "-C", str(wt), "grep", "-l", "-e", "memory-budget", "-e", "memory_budget", "--", "*.py", "*.md", "*.toml", "*.cfg"], expect=None)

    step("git status (expect exactly the two files) + diff")
    status = run(["git", "-C", str(wt), "status", "--short"], quiet=True).stdout.strip().splitlines()
    changed = sorted(ln.split()[-1] for ln in status)
    if changed != sorted([workflow, CONF]):
        raise Stop(f"unexpected working-tree changes: {status}")
    run(["git", "-C", str(wt), "--no-pager", "diff"])

    state = {
        "repo": repo,
        "worktree": str(wt),
        "branch": BRANCH,
        "base_sha": sha,
        "workflow": workflow,
        "python": py,
        "test": test_rel,
        "old_ceiling": old,
        "new_ceiling": new,
        "slack": slack,
        "chars": chars,
        "growth": {k: v for k, v in growth.items() if k != "raw"},
        "controls": results,
        "suite": suite_line,
        "prepared_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    (scratch / "COMMIT_MSG.txt").write_text(commit_message(repo, old, new, slack, growth, results, suite_line), encoding="utf-8")
    (scratch / "PR_BODY.md").write_text(pr_body(repo, old, new, slack, growth, suite_line), encoding="utf-8")
    state_path(repo).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"\n== PREPARED {repo}: ceiling {old:,} -> {new:,} (+{slack:,}); state {state_path(repo)}; NOT committed")
    return 0


def cmd_ship(repo: str) -> int:
    state = json.loads(state_path(repo).read_text(encoding="utf-8"))
    wt = Path(state["worktree"])
    scratch = STATE_DIR / f"{repo}.scratch"
    msg = scratch / "COMMIT_MSG.txt"
    body = scratch / "PR_BODY.md"
    if not (wt.is_dir() and body.is_file()):
        raise Stop("nothing prepared; run `prepare` first")
    # Re-render the message from the recorded state so a template fix never needs a re-prepare.
    msg.write_text(commit_message(repo, state["old_ceiling"], state["new_ceiling"], state["slack"], state["growth"], state["controls"], state["suite"]), encoding="utf-8")
    title = msg.read_text(encoding="utf-8").splitlines()[0]

    step(f"{repo}: worktree still exactly the two prepared files")
    ahead = run(["git", "-C", str(wt), "log", "--oneline", "origin/main..HEAD"], quiet=True).stdout.strip().splitlines()
    if ahead:
        # An earlier `ship` committed and then stopped (e.g. on the trailer check) -- replace that
        # commit, but only if it was never pushed and is the single commit on the branch.
        pushed = run(["git", "ls-remote", "--heads", "origin", BRANCH], cwd=wt, quiet=True).stdout.strip()
        if pushed or len(ahead) != 1:
            raise Stop(f"branch already has commits ({ahead}) and pushed={bool(pushed)}; refusing to double-ship")
        run(["git", "-C", str(wt), "reset", "--soft", "origin/main"], quiet=True)
        print(f"   replaced the unpushed commit {ahead[0]}")
    status = run(["git", "-C", str(wt), "status", "--short"], quiet=True).stdout.strip().splitlines()
    changed = sorted(ln.split()[-1] for ln in status)
    if changed != sorted([state["workflow"], CONF]):
        raise Stop(f"working tree drifted since prepare (a peer?): {status}")

    step("signed commit (YubiKey) with the Allow-Ceiling-Raise trailer")
    run(["git", "-C", str(wt), "add", state["workflow"], CONF], quiet=True)
    run(["git", "-C", str(wt), "commit", "-S", "-q", "-F", str(msg)], quiet=True)
    head = run(["git", "-C", str(wt), "rev-parse", "--short=8", "HEAD"], quiet=True).stdout.strip()
    # Two readings of the same commit: git's trailer parser (last paragraph only) and the exact
    # MULTILINE regex the checker applies to `git log --format=%B` in CI.
    trailers = run(["git", "-C", str(wt), "log", "-1", "--format=%(trailers:key=Allow-Ceiling-Raise)"], quiet=True).stdout.strip()
    body_text = run(["git", "-C", str(wt), "log", "-1", "--format=%B"], quiet=True).stdout
    if RAISE_TRAILER.strip() not in trailers or not re.search(r"^Allow-Ceiling-Raise:\s*AGENTS\.md\s*$", body_text, flags=re.MULTILINE):
        raise Stop(f"the commit lost its trailer: git sees {trailers!r}")
    sig = run(["git", "-C", str(wt), "log", "-1", "--format=%G?"], quiet=True).stdout.strip()
    print(f"   {head} signature status %G?={sig}  trailer ok")

    step("push + PR")
    run(["git", "-C", str(wt), "push", "-u", "origin", BRANCH], quiet=True)
    proc = run(
        ["gh", "pr", "create", "--repo", f"pcalnon/{repo}", "--base", "main", "--head", BRANCH, "--title", title, "--body-file", str(body)],
        quiet=True,
    )
    url = proc.stdout.strip().splitlines()[-1]
    number = int(url.rstrip("/").rsplit("/", 1)[-1])
    print(f"   {url}")

    step("attribution + signature as GitHub sees them (a green rollup does not imply a mergeable PR)")
    run(["gh", "api", f"repos/pcalnon/{repo}/pulls/{number}/commits", "--jq", '.[]|"verified=\\(.commit.verification.verified) reason=\\(.commit.verification.reason) login=\\(.author.login//"UNATTRIBUTED")"'])

    state.update({"pr": number, "pr_url": url, "head": head, "shipped_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
    state_path(repo).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"\n== SHIPPED {repo}#{number} head {head}: ceiling {state['old_ceiling']:,} -> {state['new_ceiling']:,}")
    return 0


def cmd_status(repo: str) -> int:
    p = state_path(repo)
    print(p.read_text(encoding="utf-8") if p.is_file() else f"nothing recorded for {repo}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("command", choices=["prepare", "ship", "status"])
    ap.add_argument("repo", choices=sorted(REPOS))
    ap.add_argument("--reuse", action="store_true", help="prepare: reuse THIS session's own uncommitted worktree after a stopped run (never a peer's)")
    args = ap.parse_args(argv)
    try:
        if args.command == "prepare":
            return cmd_prepare(args.repo, reuse=args.reuse)
        return {"ship": cmd_ship, "status": cmd_status}[args.command](args.repo)
    except Stop as exc:
        print(f"\n!! STOP: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
