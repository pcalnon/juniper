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
4   INTERRUPTED -- a signal arrived mid-wait. Nothing was merged; the child waiter was
    killed. Distinct from 1 and 3 so a killed run is never read as a decision.

A refusal is never silent and never degrades to a merge.
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
# Sized from measurement, not habit: ci.yml PR runs on this fleet have a median of 251 s
# and a max of 333 s (20-run sample, 2026-08-19). 900 s is ~3x the observed worst case, so a
# run that blows through it is stuck, not slow -- and it fails fast enough to be noticed
# rather than being killed opaquely by whatever supervisor is running the script.
DEFAULT_TIMEOUT = 900
# A sync restarts CI, so a BEHIND repair must be followed by another wait. Bounded: under
# sustained concurrent merges a PR can be re-BEHINDed indefinitely, and looping forever
# would be its own failure mode. Refuse instead and let a human decide.
MAX_SYNC_CYCLES = 3
# update-branch is 202 Accepted; the ref moves asynchronously. Poll until it actually does.
REF_SETTLE_POLLS = 20
REF_SETTLE_INTERVAL = 3.0
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
    except Exception:  # nosec B110 - best-effort hardening; never block the merge on it
        pass


def _kill_child() -> None:
    child, globals()["_CHILD"] = _CHILD, None
    if child and child.poll() is None:
        child.kill()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass


def _install_signal_handlers(log) -> None:
    """Turn a supervisor's SIGTERM/SIGINT into an honest, non-zero, self-cleaning exit."""

    def _handler(signum, _frame):
        _kill_child()
        log(
            f"\nINTERRUPTED by signal {signum}: nothing was merged. "
            "The PR keeps whatever base refresh already landed; re-run to resume."
        )
        os._exit(EXIT_INTERRUPTED)

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            signal.signal(sig, _handler)
        except (ValueError, OSError):
            pass


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
        if after.get("mergeStateStatus") == "BEHIND":
            log("  went BEHIND while waiting — re-syncing")
            if update_branch(owner, repo, pr) is None:
                raise Refused("branch refresh did not land within the settle budget")
            continue

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
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"seconds to wait per cycle (default {DEFAULT_TIMEOUT})")
    ap.add_argument("--execute", action="store_true", help="actually merge (default: dry-run)")
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
