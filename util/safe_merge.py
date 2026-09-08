#!/usr/bin/env python3
"""Merge a PR only after its REQUIRED checks have actually finished green.

Project:     Juniper
Sub-Project: juniper-ml
Application: cross-repo merge gate
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Status:      permanent utility

Why this exists
---------------
Recommendation **R4** of
``notes/JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_BRANCH-PROTECTION-INVESTIGATION-SYNTHESIS.md``.

Two independent audits measured that **12% of freshness-synced PRs merged before the
re-test they had just paid for could finish**. The cost of the sync was paid and its
benefit thrown away. Two concrete cases:

* **ml#932** merged **66 seconds** after its sync, on a head with **zero** CI check-runs.
  ``main`` then went red on Pre-commit x3.
* **ml#924** merged **25 seconds** after its update-branch head was created, again with no
  CI ever run on that head. It introduced the lint violation that reddened ``main``.

Both are *worse than not syncing at all*: the stale-but-tested head was replaced by a
fresh-but-untested one. GitHub did not stop either merge because the owner holds an
``always`` ruleset bypass, which makes every required check advisory for that actor.

This tool is the discipline that bypass removes. It refuses to merge unless the required
contexts for the PR's **current head** have all finished and none failed.

What it is NOT
--------------
**It is not enforcement.** A script can be skipped. Enforcement would mean narrowing the
owner's ``RepositoryRole 5`` bypass, which is a separate decision with its own costs (that
entitlement is genuinely load-bearing -- see the bypass analysis in ml#1012). Use this
because merging untested code is undesirable, not because something forces you to.

Surviving being killed
----------------------
A long wait is a liability: the script can be killed and then nothing finishes the merge. This
is not hypothetical and it is not rare -- see
``notes/JUNIPER_2026-08-19_JUNIPER-ECOSYSTEM_SAFE-MERGE-KILL-FORENSICS.md``. The measured
mechanism (§3.4): a background task runs on a ``[bg]`` worker, spare workers hold a hard
**~3600 s lease**, and a task **cannot outlive its host worker**. A task placed on a fresh
spare gets an hour; the same command placed on a spare that is already 3372 s old gets 229 s.
The incident that motivated this net died exactly that way, matching the lease to 0.426 s.
**The runway is not knowable in advance and "it worked last time" predicts nothing.**

So whenever there is something to wait for, the merge is also handed to GitHub via
``gh pr merge --auto`` -- a **server-side** net that completes even if this process dies.
Auto-merge merges only once the required checks pass on the current head, so it carries the
same checks-green guarantee this tool enforces locally.

The net is **gated on the repo's ``allow_auto_merge``**, and that gate is load-bearing: where
the setting is false, ``--auto`` does not arm at all -- it silently falls back to an
**immediate merge**, which with the owner's ``always`` ruleset bypass can land a PR whose
checks never finished. Arming blind would reintroduce the exact bug this tool prevents.
(Enabled fleet-wide 2026-08-19; the gate stays because a setting can be turned off again.)

It is deliberately NOT armed on an already-green PR: there ``--auto`` merges on the spot,
skipping the head pinning below. ``--no-auto-fallback`` opts out entirely.

**What the net does and does not carry (D4).** Both paths now pass ``--match-head-commit``:
the local one at merge time, the net at ARMING time. But they are not the same guarantee, and
the difference is the part worth knowing.

``expectedHeadOid`` on ``enablePullRequestAutoMerge`` is an **enable-time** check, measured
rather than assumed (probe ml#1225: armed with a pin, pushed a commit to move the head, and
``autoMergeRequest`` was still present with an unchanged ``enabledAt``). So pinning the net
guards against **arming over a stale read** -- if the head moved between reading the PR and
arming, GitHub refuses instead of arming over a SHA this run never verified.

It does **not** keep pinning afterwards. Once armed, the net merges whatever head is current
when the checks pass. That is deliberate rather than merely tolerated: on a ``strict=true``
repo GitHub moves the head itself to satisfy the up-to-date rule, and a continuously-enforced
pin would kill the net exactly when it is needed. So the net still guarantees *"merges only
when required checks are green"* and not *"merges only the SHA this run vouched for"*.
Callers who need the stronger property should pass ``--no-auto-fallback`` and keep the run
alive.

**A refusal takes the net back down.** Any refusal after arming calls ``--disable-auto``
before propagating, so a refusal cannot quietly become a merge once the blocker clears. If
that teardown itself fails, the refusal says so **loudly** and names the PR -- that is the one
state where a stated refusal and a live server-side net coexist, and it must never be
silent.

The TOCTOU problem, and how it is handled
-----------------------------------------
Waiting for checks and then merging is a two-step operation, and the head can move in
between -- a push, or a concurrent session's ``update-branch``. Merging then lands a commit
whose checks were never the ones waited on, which is precisely the ml#924 shape.

So the resolved head SHA is captured **before** the wait and passed to
``gh pr merge --match-head-commit``. GitHub itself rejects the merge if the head moved.
The check is therefore enforced server-side, not by a local re-read that could race.

That guard earned its place on the **first live run** (ml#1170): the merge was rejected with
*"Head branch was modified"*. The cause was a bug here -- ``update-branch`` answers **202
Accepted** and moves the ref *asynchronously*, so reading the PR immediately returned the
OLD head; the tool then waited on that head's already-green checks and tried to merge a SHA
that no longer existed. ``update_branch`` now polls until the ref actually moves. Had the
guard not been there, the tool would have merged an untested head -- the very failure it was
written to prevent.

A rejected merge of that kind is a **refusal** (exit 1), not a hard error: nothing was
merged, which is the correct outcome.

Signing
-------
``BEHIND`` is repaired with ``gh api .../pulls/N/update-branch -X PUT`` -- a server-side
merge, therefore **GitHub-signed**, which ``required_signatures`` accepts fleet-wide. A
local merge + push is unsigned and would be rejected. No local git is used at any point;
this needs no checkout.

Usage
-----
    python util/safe_merge.py --pr 1170                      # dry-run: report only
    python util/safe_merge.py --pr 1170 --execute
    python util/safe_merge.py --pr 524 --repo juniper-cascor --execute
    python util/safe_merge.py --pr 42 --execute --merge-method merge

Exit codes
----------
0   merged (or, under --dry-run, would have merged)
1   REFUSED -- a stated reason (checks failed / still running / BEHIND loop exhausted /
    conflicts / not open / head moved). Nothing was merged.
2   misuse (bad arguments)
3   hard error (``gh`` missing or failing, PR not found)
4   INTERRUPTED -- a signal arrived mid-wait. This run merged nothing and the child waiter
    was killed. Distinct from 1 and 3 so a killed run is never read as a decision. NOTE: if
    an auto-merge net was armed it is **deliberately left up** -- surviving the kill is the
    entire point of the net -- so the PR may still merge server-side once its checks pass.
    The interrupt message says so explicitly.

A refusal is never silent, and a refusal takes the auto-merge net down before returning.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import pathlib
import shutil
import signal
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
import sys
import time

DEFAULT_OWNER = "pcalnon"
DEFAULT_REPO = "juniper-ml"
# CI-wait budget. HISTORICAL RECORD OF THE 2026-08-20 MEASUREMENT -- kept because it is why
# 900 s was abandoned, but every NUMBER in it is superseded. It was produced by
# `util/ad-hoc/2026-08-20_measure_required_check_span.py`, which despite its name filters
# nothing: advisory and bot check-runs on the head SHA enter the span, and the figures below
# overstate the observed max by 11x-110x depending on the repo. The live table is
# `REPO_TIMEOUTS` further down, re-measured 2026-09-08 with the v2 instrument.
#
# The previous 900 s was sized off "ci.yml median 251 s" -- one workflow, one repo. Measured
# across all required contexts the fleet spans differ by ~6x, and 900 s was BELOW the
# observed max on three of the four repos sampled. That conclusion survives the instrument
# correction; the numbers supporting it do not:
#
#   repo                   min  median    p90     max     n
#   juniper-ml             233     248     263     273    18
#   juniper-data           270     462    1100    1196    10
#   juniper-cascor         538     614    1065    1547    12
#   juniper-canopy         785     886    1371    1719    10
#
# 900 s sat essentially AT canopy's median, so roughly half of canopy's merges would have
# refused with "checks did not finish" while the checks were in fact still healthy. A
# spurious refusal is not harmless here: it is indistinguishable from a real blocker.
#
# Two more repos measured the same day, and the inference drawn from them was WRONG:
#
#   juniper-cascor-worker  314    493    1122    1717     8
#   juniper-cascor-client  177    564    6799   15616     8
#
# This comment used to read: "cascor-client's 15,616 s (4h20m) is a check sitting QUEUED, not
# CI doing work", and concluded that sizing must therefore be off the p90 and never the max.
#
# **It was not queue time.** It is the v1 instrument counting bot check-runs that attached to
# the head SHA hours after CI finished. Re-measured 2026-09-08 with the v2 tool over required
# contexts only, cascor-client's max is 1511 s across 30 heads with 0 unmeasurable -- a 19x
# overstatement, the same artifact seen on every other repo (cascor 11x, canopy 20x,
# data-client 27x, cascor-worker 70x, deploy 110x).
#
# The distinction the paragraph was defending is real and still holds: a budget must clear
# the typical worst case and then FIRE on a pathological tail, or a stuck check is
# indistinguishable from a slow one. What changed is that the "pathological tail" was an
# instrument artifact, so clearing the observed max is now both feasible and correct. Sizing
# is therefore off BOTH statistics -- `> observed_max` and `<= 4x p90` -- which is what
# `tests/test_safe_merge.py::test_default_timeout_is_sized_from_measurement` has always
# described in prose and, since 2026-09-08, actually asserts.
#
# The CEILING is a RISK threshold, not a hard bound -- an earlier version of this comment
# claimed it was the latter and that was wrong. What is measured (kill forensics §3.4):
# `[bg]` SPARE workers hold a ~3600 s lease, and 5 background tasks died at 3599.2-3600.0 s.
# What is NOT true is "a budget above 3600 s is unreachable": 8 background tasks in the same
# corpus ran past 3600 s and completed normally, the longest at 59,783 s (16.6 h). Those were
# presumably hosted by long-lived `slash` workers (30k-134k s) rather than spares -- but that
# is an inference, and the host kind is not knowable in advance from inside the task.
#
# So the honest statement: a wait longer than ~3600 s MAY be cut short depending on which
# worker happens to host it, and the caller cannot tell which. Capping below that keeps the
# local wait inside the window that is reliably available; past it, the armed auto-merge net
# is the answer rather than a longer local wait.
TIMEOUT_CEILING = 3300
DEFAULT_TIMEOUT = 2400  # unmeasured repos: the "standard" tier
# RE-MEASURED FLEET-WIDE 2026-09-08, n=30, with
# `util/ad-hoc/2026-09-08_measure_required_check_span_v2.py`. Every number below is the span
# of the repo's REQUIRED contexts only.
#
# The v1 instrument (`util/ad-hoc/2026-08-20_measure_required_check_span.py`) sized this
# table and measured the wrong thing. Its docstring says "over the REQUIRED contexts on ONE
# head SHA"; its code fetches `check-runs?per_page=100` and filters nothing, so advisory and
# bot check-runs enter the span. On cascor#626 a `claude` check-run attached to the head SHA
# 5.7 hours after CI finished, and v1 reported a 21,207 s span for a 605 s CI pass. Measured
# overstatement of the observed max: cascor 11x, canopy 20x, cascor-client 19x,
# data-client 27x, cascor-worker 70x, deploy 110x.
#
# Two consequences that were live in this table until today:
#   * juniper-cascor's 2400 s sat BELOW its own observed max (2561 s) -- a healthy cascor PR
#     at its worst was refused, the same failure that hit ml#1754;
#   * juniper-deploy and juniper-recurrence fell through to DEFAULT_TIMEOUT at 2400 s, which
#     is 9x their p90 -- a stuck run there looked merely slow for 40 minutes.
#
# Sizing rule, both halves now enforced by `KillResilienceTest`: the budget must CLEAR the
# observed max and stay inside 4x p90. Values are picked mid-window, not guessed.
#
# If a repo starts refusing healthy PRs, re-run the v2 tool with `-n 30` and record `n`
# alongside whatever you write here -- the 2026-09-05 juniper-ml re-tier could not be
# reproduced because its sample size was never written down.
REPO_TIMEOUTS = {
    # p90 538, max 773 -> window (773, 2152]. 1500 kept from the 2026-09-05 re-tier; it
    # remains mid-window on the corrected numbers, so this row needed no change. (The
    # 2026-09-05 figures it was chosen from -- p90 455, max 823 -- came from v1, but ml's
    # advisory check-runs happen to sit inside its CI window, so v1 overstated ml by 1.0x.)
    "juniper-ml": 1500,
    # p90 679, max 1047 -> window (1047, 2716].
    "juniper-data": 2400,
    # p90 770, max 2561 -> window (2561, 3080]. RAISED 2400 -> 2800: the old value did not
    # clear the observed max. cascor's spread is the fleet's widest (median 635, max 2561)
    # because `Quality Gate` gates on 23 other required contexts and re-runs extend the tail.
    "juniper-cascor": 2800,
    # p90 888, max 1029 -> window (1029, 3552].
    "juniper-cascor-worker": 2400,
    # p90 1597, max 2067 -> window (2067, 6388]. Kept at the ceiling: canopy's window is
    # wide enough that TIMEOUT_CEILING binds first, and tightening it buys nothing.
    "juniper-canopy": 3300,
    # p90 724, max 1511 -> window (1511, 2896], so 3300 is ABOVE 4x p90 and this row is
    # excluded from `KillResilienceTest`'s pin rather than changed.
    #
    # THE STATED REASON FOR THAT EXCLUSION IS REFUTED, AND THE EXCLUSION IS KEPT ANYWAY.
    # The table previously called cascor-client "ceiling-bound because its tail is queue
    # time" on a v1 max of 15,616 s. It is not queue time: v2 measures a required-context
    # max of 1511 s across 30 heads with 0 unmeasurable, and v1's 19x overstatement here has
    # the same bot-check-run cause as everywhere else. Lowering it is a live merge-path
    # change on a repo this arc was told not to touch, so it is left for an owner ruling.
    "juniper-cascor-client": 3300,
    # p90 893, max 1109 -> window (1109, 3572]. First measurement; was falling through to
    # DEFAULT_TIMEOUT at the same 2400 s, so this row records the number rather than changing it.
    "juniper-data-client": 2400,
    # p90 262, max 375 -> window (375, 1048]. First measurement; was DEFAULT_TIMEOUT 2400.
    "juniper-deploy": 1000,
    # p90 258, max 352 -> window (352, 1032]. First measurement; was DEFAULT_TIMEOUT 2400.
    # juniper-recurrence is absent from the parent CLAUDE.md's repo table, which is why no
    # earlier sweep measured it.
    "juniper-recurrence": 1000,
}


def timeout_for(repo: str) -> int:
    """Per-repo CI budget, falling back to a fleet-safe default for unmeasured repos."""
    return REPO_TIMEOUTS.get(repo, DEFAULT_TIMEOUT)


def clamp_timeout(seconds: int, log=print) -> int:
    """Hold any budget -- including an explicit --timeout -- at TIMEOUT_CEILING.

    TIMEOUT_CEILING used to be a DEAD CONSTANT: defined, asserted against in tests, and
    never consulted at runtime, so `--timeout 7200` sailed straight through. The tests
    passed the whole time because they checked the table's values rather than the code
    path, which is the tidiest way to have a guarantee that does not exist.

    Clamps loudly rather than silently: a caller who asked for two hours should be told
    they are getting 3300 s, not left to infer it from a log timestamp later.
    """
    if seconds > TIMEOUT_CEILING:
        log(
            f"  --timeout {seconds}s exceeds TIMEOUT_CEILING ({TIMEOUT_CEILING}s); "
            f"clamping. A longer local wait may be cut short by the host worker's lease "
            f"anyway -- rely on the armed auto-merge net instead."
        )
        return TIMEOUT_CEILING
    return seconds
# A sync restarts CI, so a BEHIND repair must be followed by another wait. Bounded: under
# sustained concurrent merges a PR can be re-BEHINDed indefinitely, and looping forever
# would be its own failure mode. Refuse instead and let a human decide.
MAX_SYNC_CYCLES = 3
# update-branch is 202 Accepted; the ref moves asynchronously. Poll until it actually does.
REF_SETTLE_POLLS = 20
REF_SETTLE_INTERVAL = 3.0
# GitHub reports mergeStateStatus=UNKNOWN while it recomputes mergeability -- routinely for
# several seconds after an update-branch. That is a "not yet", not a "no", so it gets a
# bounded re-poll instead of a refusal (D2).
MERGEABILITY_POLLS = 10
MERGEABILITY_INTERVAL = 3.0
# Exit code for "interrupted": distinct from refused (1) and hard error (3) so a killed run
# is never mistaken for a decision the tool made.
EXIT_INTERRUPTED = 4
PR_SET_PDEATHSIG = 1  # <linux/prctl.h>

WAITER = pathlib.Path(__file__).with_name("wait_for_checks.py")


class HardError(RuntimeError):
    """gh missing/failing, or the PR cannot be resolved."""


class Refused(RuntimeError):
    """A safety condition was not met. Nothing was merged."""


def _gh(args: list[str], timeout: int = 120) -> str:
    proc = subprocess.run(  # nosec B603 B607
        ["gh", *args], capture_output=True, text=True, timeout=timeout, check=False
    )
    if proc.returncode != 0:
        raise HardError(f"gh {' '.join(args[:3])}… failed: {proc.stderr.strip()[:300]}")
    return proc.stdout


def pr_state(owner: str, repo: str, pr: int) -> dict:
    raw = _gh(
        [
            "pr",
            "view",
            str(pr),
            "--repo",
            f"{owner}/{repo}",
            "--json",
            "state,mergeStateStatus,mergeable,headRefOid,isDraft,title",
        ]
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HardError(f"could not parse PR {pr} state: {exc}") from exc


def update_branch(owner: str, repo: str, pr: int, *, sleeper=time.sleep) -> str | None:
    """Server-side (therefore GitHub-signed) branch refresh; returns the NEW head.

    The endpoint answers **202 Accepted** -- "Updating pull request branch." -- and the ref
    moves asynchronously. Reading the PR immediately therefore returns the OLD head, and a
    caller that trusts it will wait on the previous head's (already green) checks and then
    try to merge a SHA that no longer exists.

    That is not hypothetical: it is exactly what happened on this tool's first live run
    (ml#1170), where ``--match-head-commit`` caught it server-side with "Head branch was
    modified" -- the safety net working, around a bug here.

    So this polls until the head actually changes. Returning ``None`` means the ref did not
    move within the budget; the caller must treat that as "not ready", never as success.
    """
    before = pr_state(owner, repo, pr).get("headRefOid")
    _gh(["api", f"repos/{owner}/{repo}/pulls/{pr}/update-branch", "-X", "PUT"])
    for _ in range(REF_SETTLE_POLLS):
        sleeper(REF_SETTLE_INTERVAL)
        now = pr_state(owner, repo, pr).get("headRefOid")
        if now and now != before:
            return now
    return None


_CHILD: subprocess.Popen | None = None


def _die_with_parent() -> None:
    """Ask the kernel to SIGTERM this child when its parent dies (Linux only).

    Signal handlers cannot run when the parent is SIGKILLed, so a handler alone cannot
    prevent an orphan. ``prctl(PR_SET_PDEATHSIG)`` is enforced by the kernel and therefore
    survives even that. Verified: without it, killing the parent leaves the waiter polling
    GitHub until its own 32-minute timeout. Best-effort -- a platform without prctl simply
    keeps the previous behaviour.
    """
    try:
        ctypes.CDLL("libc.so.6", use_errno=True).prctl(PR_SET_PDEATHSIG, signal.SIGTERM)
    except Exception:  # nosec B110
        # Swallowed on purpose, and the breadth is deliberate. This runs in the child between
        # fork and exec, where raising anything would fail the merge for a reason that has
        # nothing to do with the merge. A platform without prctl (or a different libc soname)
        # simply keeps the previous, orphan-prone behaviour -- degraded, not broken.
        return


def _kill_child() -> None:
    child, globals()["_CHILD"] = _CHILD, None
    if child and child.poll() is None:
        child.kill()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            # Best-effort reap: child was already sent SIGKILL; do not block or
            # fail interruption/cleanup flow if process exit notification lags.
            pass


def _install_signal_handlers(log) -> None:
    """Turn a supervisor's SIGTERM/SIGINT into an honest, non-zero, self-cleaning exit."""

    def _handler(signum, _frame):
        _kill_child()
        # "nothing was merged" was true of the run and false of the outcome: with a net armed
        # the PR can still merge server-side seconds later. Saying so is the difference
        # between an operator re-running safely and an operator merging the same PR twice.
        if _ARMED is not None:
            tail = (
                f"This run merged nothing, but an auto-merge net IS ARMED on "
                f"{_ARMED['owner']}/{_ARMED['repo']}#{_ARMED['pr']} and will merge it once "
                f"the required checks pass — that is intentional, it is what survives this "
                f"kill. To cancel it:\n"
                f"     gh pr merge {_ARMED['pr']} --repo "
                f"{_ARMED['owner']}/{_ARMED['repo']} --disable-auto"
            )
        else:
            tail = (
                "Nothing was merged and no net is armed. The PR keeps whatever base refresh "
                "already landed; re-run to resume."
            )
        log(f"\nINTERRUPTED by signal {signum}: {tail}")
        os._exit(EXIT_INTERRUPTED)

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            signal.signal(sig, _handler)
        except (ValueError, OSError):
            # Best-effort only: some runtimes/threads/platforms reject installing specific
            # handlers (for example, "signal only works in main thread"). Keep running with
            # whatever handlers were accepted rather than failing the merge flow.
            pass


def repo_allows_auto_merge(owner: str, repo: str) -> bool:
    """Is server-side auto-merge available on this repo?

    Load-bearing gate. Where `allow_auto_merge` is FALSE, `gh pr merge --auto` does not arm
    -- it silently falls back to an IMMEDIATE merge, which combined with the owner's `always`
    ruleset bypass can land a PR whose required checks never finished. That is the exact
    failure this tool exists to prevent, so the net must never be armed blind.

    Enabled fleet-wide 2026-08-19 (`util/ad-hoc/2026-08-19_enable_allow_auto_merge.py`); this
    check stays because a repo setting can be turned off again, and because this tool is used
    cross-repo.
    """
    try:
        return json.loads(_gh(["api", f"/repos/{owner}/{repo}", "--jq", ".allow_auto_merge"]).strip())
    except (HardError, json.JSONDecodeError):
        return False


def unresolved_threads(owner: str, repo: str, pr: int) -> list[str]:
    """Unresolved review threads, which block a merge INVISIBLY to `gh pr checks`.

    ml's ruleset sets `required_review_thread_resolution: true`, so one unresolved thread
    blocks the merge with every required context green. A `github-advanced-security` CodeQL
    thread is the usual source. Best-effort: a probe failure returns [] so it can never be the
    thing that fails a merge.
    """
    q = (
        'query { repository(owner:"%s",name:"%s"){ pullRequest(number:%d){ '
        "reviewThreads(first:50){ nodes { isResolved comments(first:1){ nodes { "
        "author { login } body } } } } } } }" % (owner, repo, pr)
    )
    try:
        raw = _gh(["api", "graphql", "-f", f"query={q}"])
        nodes = json.loads(raw)["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    except (HardError, json.JSONDecodeError, KeyError, TypeError):
        return []
    out = []
    for n in nodes:
        if n.get("isResolved"):
            continue
        c = (n.get("comments") or {}).get("nodes") or [{}]
        who = ((c[0].get("author") or {}).get("login")) or "?"
        body = " ".join((c[0].get("body") or "").split())[:80]
        out.append(f"{who}: {body}")
    return out


# States in which arming the net is correct: there is genuinely something to wait for, and
# `--auto` will therefore ARM rather than merge on the spot.
#
#   BLOCKED  -- required checks pending (or a blocker such as an unresolved thread)
#   BEHIND   -- base moved; on a strict repo GitHub will sync AND merge for us
#   UNKNOWN  -- GitHub is recomputing mergeability, which is the NORMAL state for several
#               seconds after an update-branch
#
# UNKNOWN and BEHIND were both missing before (D1). That was the worst possible omission: the
# post-sync full CI re-run is the LONGEST and most kill-exposed wait this tool ever performs,
# and it was the one wait entered with no net. It is also the exact shape of the incident.
ARMABLE_STATES = ("BLOCKED", "BEHIND", "UNKNOWN")

# Module-level so the signal handler can report the net truthfully. A per-cycle local (the
# previous shape) also silently forgot the net across a BEHIND re-sync, so a refusal on cycle
# 2 could not have disarmed a net armed on cycle 1 even if it had tried to.
_ARMED: dict | None = None


def arm_auto_merge(owner: str, repo: str, pr: int, method: str, log, head: str = "") -> bool:
    """Hand the merge to GitHub as a net, so a killed script does not strand the PR.

    Idempotent: arming twice is a no-op, so callers may call this on every cycle.

    Armed only in ARMABLE_STATES -- on an already-green PR ``--auto`` merges on the spot,
    which would skip the head pinning the local path performs, so that case is deliberately
    left to the local path.

    ``head`` pins the arming to a specific SHA (D4). MEASURED before adding, because a wrong
    guess here would be silent and total: probe ml#1225 armed a net with
    ``--match-head-commit``, pushed a new commit to move the head, and re-read the PR --
    ``autoMergeRequest`` was still present with an UNCHANGED ``enabledAt``, so it had not
    been dropped and had not been silently re-armed.

    So ``expectedHeadOid`` on ``enablePullRequestAutoMerge`` is an ENABLE-TIME
    optimistic-concurrency guard, not a continuous constraint. That matters: had it been
    continuous, the net would evaporate the moment GitHub moved the head itself to satisfy
    ``strict``, which is exactly when it is needed -- silently negating D1. A push is a
    stronger head move than GitHub's own sync, and the net survived it.

    What pinning buys: the arming cannot be based on a stale read. If the head moved between
    ``pr_state`` and here, GitHub rejects the mutation instead of arming a net over a SHA
    this run never verified. The net still carries the weaker guarantee AFTER arming (it
    merges whatever head is current once checks pass) -- that part of D4 remains a stated
    trade, not a fixed one, and the docstring says so.

    Passing ``head=""`` skips the pin, which is the pre-D4 behaviour.
    """
    global _ARMED
    if _ARMED is not None:
        return True
    if not repo_allows_auto_merge(owner, repo):
        log("  auto-merge net UNAVAILABLE (allow_auto_merge is false) — local wait only")
        return False
    argv = ["pr", "merge", str(pr), "--repo", f"{owner}/{repo}", "--auto", f"--{method}"]
    if head:
        # Must be the full 40-char OID: an abbreviated SHA is rejected with
        # "Could not coerce value ... to GitObjectID". `headRefOid` is already full-length.
        argv += ["--match-head-commit", head]
    try:
        _gh(argv)
    except HardError as exc:
        log(f"  could not arm auto-merge net ({str(exc)[:80]}) — continuing with local wait")
        return False
    _ARMED = {"owner": owner, "repo": repo, "pr": pr}
    pinned = f" pinned to {head[:8]}" if head else " (UNPINNED)"
    log(
        f"  auto-merge net armed{pinned} — GitHub will complete this merge even if this run "
        "dies (net is checks-green-gated; it does not re-pin the head after arming)"
    )
    return True


def disarm_auto_merge(log) -> bool:
    """Take the server-side net down. Called before every refusal.

    Without this, ``safe_merge`` could state a refusal and then merge the PR anyway minutes
    later when the blocker cleared -- which is the precise opposite of what a refusal means,
    and which was observed live on ml#1185 (2026-08-20T00:23:51Z).

    Returns True if the net is down (or was never up). A False return is a genuinely
    dangerous state and callers MUST surface it rather than swallow it.
    """
    global _ARMED
    if _ARMED is None:
        return True
    owner, repo, pr = _ARMED["owner"], _ARMED["repo"], _ARMED["pr"]
    try:
        _gh(["pr", "merge", str(pr), "--repo", f"{owner}/{repo}", "--disable-auto"])
    except HardError as exc:
        log(
            f"  !! COULD NOT DISARM the auto-merge net on {owner}/{repo}#{pr} "
            f"({str(exc)[:80]}). A LIVE net remains: this PR may merge itself once its "
            f"checks pass, despite the refusal below. Disarm manually:\n"
            f"     gh pr merge {pr} --repo {owner}/{repo} --disable-auto"
        )
        return False
    _ARMED = None
    log("  auto-merge net disarmed")
    return True


def _merged_by_other(pr: int, note: str = "") -> str:
    """Success message for a PR that merged out from under this run's local merge path.

    Worded from ``_ARMED`` rather than assumed. The armed net is the *likely* merger, but it
    is only the merger if this run actually armed one -- with ``--no-auto-fallback``, or on a
    repo where ``allow_auto_merge`` is false, nothing was armed and a concurrent session or a
    human did it. Naming the net regardless would be a claim the machinery could not have
    produced, which is the failure shape this file spends most of its length guarding against.

    Either way it is a SUCCESS: the PR is merged, and GitHub gates its own merges on the same
    required checks this run was waiting for.
    """
    who = (
        "by the armed auto-merge net (required checks green)"
        if _ARMED is not None
        else "concurrently -- this run armed no net, so another actor merged it"
    )
    return f"MERGED #{pr} {who}{note}"


def wait_for_required(owner: str, repo: str, pr: int, timeout: int, verbose: bool) -> dict:
    """Delegate to util/wait_for_checks.py and map its exit code.

    Deliberately a subprocess rather than an import: the waiter owns the definition of
    "finished", and coupling to its internals would let this tool drift from it.
    """
    if not WAITER.exists():
        raise HardError(f"required helper missing: {WAITER}")
    cmd = [
        sys.executable,
        str(WAITER),
        "--pr",
        str(pr),
        "--repo",
        repo,
        "--owner",
        owner,
        "--timeout",
        str(timeout),
        "--json",
    ]
    if verbose:
        cmd.append("--verbose")
    global _CHILD
    proc = subprocess.Popen(  # nosec B603
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=_die_with_parent,  # nosec B606
    )
    _CHILD = proc
    try:
        out, err = proc.communicate(timeout=timeout + 120)
    except subprocess.TimeoutExpired:
        _kill_child()
        raise
    finally:
        _CHILD = None

    payload: dict = {}
    if (out or "").strip():
        try:
            payload = json.loads(out)
        except json.JSONDecodeError:
            payload = {}
    payload["_exit"] = proc.returncode
    if proc.returncode == 3:
        raise HardError(f"wait_for_checks hard error: {(err or '').strip()[:300]}")
    return payload


def _describe(payload: dict) -> str:
    for key in ("failed", "pending", "absent", "missing"):
        names = payload.get(key)
        if names:
            return f"{key}: {', '.join(map(str, names))[:300]}"
    return "see wait_for_checks output"


def safe_merge(
    owner: str,
    repo: str,
    pr: int,
    *,
    execute: bool,
    method: str,
    timeout: int,
    verbose: bool,
    auto_fallback: bool = True,
    log=print,
) -> str:
    """Public entry point. Guarantees a refusal never leaves a live auto-merge net.

    The disarm lives HERE, wrapping every refusal path at once, rather than at each
    ``raise Refused`` site. There are seven of those and the count grows; a rule enforced at
    one choke point cannot be forgotten by the eighth.
    """
    # `_ARMED` is module-global so the signal handler can read it, which makes it survive
    # across calls in one process. That is a hazard, not a feature: a stale entry makes
    # `arm_auto_merge` short-circuit and report a net that was never armed for THIS pr --
    # a silent loss of the guarantee, worse than the D3 bug this whole change fixes. Scope
    # it to the invocation. (Caught by test_safe_merge cross-test leakage, not by review.)
    global _ARMED
    _ARMED = None
    try:
        return _safe_merge_inner(
            owner,
            repo,
            pr,
            execute=execute,
            method=method,
            timeout=timeout,
            verbose=verbose,
            auto_fallback=auto_fallback,
            log=log,
        )
    except Refused as exc:
        if not disarm_auto_merge(log):
            raise Refused(
                f"{exc} [WARNING: the auto-merge net could NOT be disarmed and is still "
                f"live on {owner}/{repo}#{pr} — this refusal may still become a merge]"
            ) from exc
        raise


def _safe_merge_inner(
    owner: str,
    repo: str,
    pr: int,
    *,
    execute: bool,
    method: str,
    timeout: int,
    verbose: bool,
    auto_fallback: bool = True,
    log=print,
) -> str:
    info = pr_state(owner, repo, pr)

    if info.get("state") != "OPEN":
        raise Refused(f"PR #{pr} is {info.get('state')}, not OPEN")
    if info.get("isDraft"):
        raise Refused(f"PR #{pr} is a draft")
    if info.get("mergeStateStatus") == "DIRTY":
        raise Refused(f"PR #{pr} has merge conflicts — resolve them first")

    for cycle in range(1, MAX_SYNC_CYCLES + 1):
        info = pr_state(owner, repo, pr)
        state = info.get("mergeStateStatus")

        if state == "DIRTY":
            raise Refused(f"PR #{pr} became conflicted during the wait")

        if state == "BEHIND":
            log(f"  BEHIND — refreshing base (cycle {cycle}/{MAX_SYNC_CYCLES})")
            if not execute:
                log("  [dry-run] would update-branch, then wait for the restarted checks")
                return "DRY-RUN: would sync and re-wait, then merge if green"
            # D1: arm BEFORE the sync, not after. The sync restarts CI, and the wait that
            # follows it is the longest this tool performs -- so it is the wait that most
            # needs a net, and it was previously the one wait entered without one (this
            # branch `continue`s straight past the arming site below). Arming first also
            # covers the sync itself, which is not instantaneous.
            if auto_fallback:
                # Pin to the PRE-SYNC head. The update-branch immediately below moves it,
                # and that is fine: the pin is an enable-time guard (measured, ml#1225), so
                # the net survives the very sync this branch is about to perform. What it
                # still buys here is that we cannot arm over a head that moved between the
                # `pr_state` read above and this call.
                arm_auto_merge(
                    owner, repo, pr, method, log, head=info.get("headRefOid") or ""
                )
            if update_branch(owner, repo, pr) is None:
                raise Refused(
                    "branch refresh did not land within the settle budget — "
                    "re-run once the base has settled"
                )
            continue

        # Capture the head we are about to vouch for BEFORE waiting. This exact SHA is
        # handed to --match-head-commit so a head that moves during the wait aborts the
        # merge server-side rather than silently landing untested code (the ml#924 shape).
        head = info.get("headRefOid")
        if not head:
            raise HardError(f"PR #{pr} has no resolvable head SHA")

        if not execute:
            # A dry run must be cheap, or nobody will use it. Blocking here for up to the
            # full timeout made the SAFE default the expensive one -- report and return.
            return (
                f"DRY-RUN: would wait for required checks on {head[:8]} "
                f"(mergeStateStatus={state}), then merge via {method}"
            )

        # D1: was `state == "BLOCKED"`. After an update-branch GitHub commonly reports
        # UNKNOWN while it recomputes mergeability, so the post-sync cycle routinely arrived
        # here in a state that armed nothing.
        if auto_fallback and state in ARMABLE_STATES:
            # Pin to the SAME head the local path is about to vouch for, so arming and
            # verifying agree on what is being merged.
            arm_auto_merge(owner, repo, pr, method, log, head=head)

        log(f"  waiting on required checks for {head[:8]} …")
        result = wait_for_required(owner, repo, pr, timeout, verbose)
        code = result.get("_exit")

        if code == 1:
            raise Refused(f"required checks FAILED on {head[:8]} — {_describe(result)}")
        if code == 2:
            raise Refused(
                f"required checks did not finish on {head[:8]} within {timeout}s — "
                f"{_describe(result)}"
            )
        if code != 0:
            raise HardError(f"unexpected wait_for_checks exit {code}")

        after = pr_state(owner, repo, pr)
        if after.get("state") == "MERGED":
            # The armed net got there first. Same guarantee -- GitHub merges only once the
            # required checks pass on the current head -- so this is a success, not a race lost.
            return _merged_by_other(pr)
        if after.get("mergeStateStatus") == "BEHIND":
            log("  went BEHIND while waiting — re-syncing")
            if update_branch(owner, repo, pr) is None:
                raise Refused("branch refresh did not land within the settle budget")
            continue

        # Green checks are NOT the same as mergeable. `mergeStateStatus` can be BLOCKED with
        # every required context passing -- an unresolved review thread does exactly that, and
        # `gh pr checks` does not show it. Merging blind here produced a confusing hard error
        # ("add the --auto flag") instead of naming the real blocker.
        # D2: UNKNOWN is not a verdict, it is GitHub still computing. Refusing on it produced
        # spurious failures, most often right after a sync -- exactly when the checks had in
        # fact just gone green. Re-poll for a bounded spell before treating it as a blocker.
        final = after.get("mergeStateStatus")
        if final == "UNKNOWN":
            log("  mergeStateStatus=UNKNOWN (GitHub recomputing) — re-polling")
            for _ in range(MERGEABILITY_POLLS):
                time.sleep(MERGEABILITY_INTERVAL)
                after = pr_state(owner, repo, pr)
                if after.get("state") == "MERGED":
                    return _merged_by_other(pr)
                final = after.get("mergeStateStatus")
                if final != "UNKNOWN":
                    break
            else:
                raise Refused(
                    f"GitHub did not resolve mergeability for {head[:8]} within "
                    f"{MERGEABILITY_POLLS * MERGEABILITY_INTERVAL:.0f}s "
                    "(mergeStateStatus stuck at UNKNOWN) — re-run to retry"
                )
            log(f"  mergeability resolved: {final}")

        if final == "BEHIND":
            # Can surface here as well as at the top of the cycle -- the base can move during
            # the UNKNOWN re-poll above. Route it back through the sync path rather than
            # refusing, which is what the top-of-loop handler is for.
            log("  resolved to BEHIND while waiting — re-syncing")
            if update_branch(owner, repo, pr) is None:
                raise Refused("branch refresh did not land within the settle budget")
            continue

        if final not in ("CLEAN", "UNSTABLE", "HAS_HOOKS"):
            threads = unresolved_threads(owner, repo, pr)
            detail = (
                f"{len(threads)} unresolved review thread(s): " + "; ".join(threads[:3])
                if threads
                else f"mergeStateStatus={final}"
            )
            # The net is about to be disarmed by the caller, so promising that it "will
            # complete this once the blocker clears" would be a lie -- and was, until D3.
            raise Refused(
                f"required checks are green but GitHub will not merge {head[:8]}: {detail}"
            )

        log(f"  all required checks green — merging {head[:8]} ({method})")
        try:
            _gh(
                [
                    "pr",
                    "merge",
                    str(pr),
                    "--repo",
                    f"{owner}/{repo}",
                    f"--{method}",
                    "--match-head-commit",
                    head,
                ],
                timeout=300,
            )
        except HardError as exc:
            # The TOCTOU guard firing is a REFUSAL, not a hard error: the head moved during
            # the wait, so the checks that passed do not describe what would be merged.
            # Nothing was merged, which is the correct outcome -- report it as such.
            if "head branch was modified" in str(exc).lower():
                raise Refused(
                    f"head moved during the wait (verified {head[:8]}); "
                    "nothing merged — re-run to verify the new head"
                ) from exc
            # The armed net can win the race in the window between the mergeability read
            # above and this call. GitHub then answers "Pull Request is not mergeable" to the
            # local merge -- because it is already MERGED -- and this handler used to report a
            # completed merge as a hard error (ml#1228 landed as 14e7af41 while this path
            # exited 3). The state check before the merge covers the net winning EARLIER;
            # only this window was uncovered, and D1 widened it: arming on
            # BLOCKED/BEHIND/UNKNOWN keeps a net live far more often than arming on BLOCKED
            # alone did. So ask the PR rather than trusting the error text -- on ANY failure,
            # not just "not mergeable", because a merge that landed and then failed to report
            # (a timeout, a 5xx on the response) is the same situation and the same answer.
            try:
                raced = pr_state(owner, repo, pr)
            except (HardError, subprocess.TimeoutExpired):
                raced = {}  # best-effort probe; a failed re-read must not mask the real error
            if raced.get("state") == "MERGED":
                landed = raced.get("headRefOid")
                if landed != head:
                    # Merged, but not at the head this run verified -- so the checks this run
                    # waited on do not describe what shipped. Not a success to claim, and too
                    # surprising to fold into the underlying gh error.
                    raise HardError(
                        f"PR #{pr} is MERGED at {str(landed)[:8]}, but this run verified and "
                        f"tried to merge {head[:8]} — a head this run never vouched for "
                        f"landed; inspect before trusting it (gh reported: {exc})"
                    ) from exc
                return _merged_by_other(
                    pr, f" at {head[:8]}, winning the race against this run's own merge"
                )
            raise
        final = pr_state(owner, repo, pr)
        if final.get("state") != "MERGED":
            raise Refused(
                f"merge command returned but PR #{pr} is {final.get('state')} — inspect manually"
            )
        return f"MERGED #{pr} at {head[:8]} via {method}"

    raise Refused(
        f"PR #{pr} went BEHIND {MAX_SYNC_CYCLES} times without a stable green head; "
        "main is moving faster than CI completes — merge manually or retry when quieter"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pr", type=int, required=True, help="pull request number")
    ap.add_argument("--repo", default=DEFAULT_REPO, help=f"repo name (default {DEFAULT_REPO})")
    ap.add_argument("--owner", default=DEFAULT_OWNER, help=f"repo owner (default {DEFAULT_OWNER})")
    ap.add_argument(
        "--merge-method",
        default="squash",
        choices=("squash", "merge", "rebase"),
        help="default squash; rebase re-creates commits UNSIGNED and required_signatures "
        "will reject them — do not use it on a Juniper repo",
    )
    # default=None so an explicit --timeout still wins, but an omitted one resolves
    # PER REPO once --repo is known. A single default cannot serve a fleet whose CI spans
    # differ by ~6x (see REPO_TIMEOUTS).
    ap.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="seconds to wait per cycle (default: per-repo, see REPO_TIMEOUTS; "
        f"fallback {DEFAULT_TIMEOUT})",
    )
    ap.add_argument("--execute", action="store_true", help="actually merge (default: dry-run)")
    ap.add_argument(
        "--no-auto-fallback",
        action="store_true",
        help="do not arm GitHub auto-merge as a kill-proof net (strict local control)",
    )
    ap.add_argument("--verbose", action="store_true", help="pass --verbose to the waiter")
    args = ap.parse_args(argv)

    if shutil.which("gh") is None:
        print("error: `gh` not found on PATH", file=sys.stderr)
        return 3

    if args.merge_method == "rebase":
        print(
            "error: --merge-method rebase re-creates commits without signatures; "
            "required_signatures rejects them fleet-wide",
            file=sys.stderr,
        )
        return 2

    if args.timeout is None:
        args.timeout = timeout_for(args.repo)
        print(f"CI budget: {args.timeout}s for {args.repo} (measured; override with --timeout)")
    args.timeout = clamp_timeout(args.timeout)
    if not args.execute:
        print("*** DRY RUN — nothing will be merged (pass --execute) ***")
    else:
        _install_signal_handlers(print)

    try:
        print(safe_merge(
            args.owner,
            args.repo,
            args.pr,
            execute=args.execute,
            method=args.merge_method,
            timeout=args.timeout,
            verbose=args.verbose,
            auto_fallback=not args.no_auto_fallback,
        ))
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    except (HardError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
