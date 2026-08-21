#!/usr/bin/env python3
"""Wait for a PR's REQUIRED status checks to finish, then report honestly.

Project: juniper-ml
Sub-Project: cross-repo tooling
Application: CI progress monitoring for headless sessions
Author: Paul Calnon
Created: 2026-08-17
License: MIT License
Status: permanent utility

Why this exists
---------------
Sessions repeatedly hand-roll a "wait for CI" loop and repeatedly get it wrong in
the same two ways. Both failure modes are silent: the loop reports success on a
suite that has not finished, and the session then merges or reports green on
incomplete evidence. This module is the reference implementation so nobody has to
rediscover the traps.

**Trap 1 -- terminal must be defined POSITIVELY.** A GitHub *check run* that is
still going carries ``conclusion: null`` and no ``state``. A loop written as "not
in my list of pending states" therefore reads an in-progress job as finished. The
list of pending states is open-ended (``QUEUED``, ``IN_PROGRESS``, ``WAITING``,
``PENDING``, ``REQUESTED``, plus whatever GitHub adds next); the list of *finished*
conclusions is closed. So this module asks "is it definitely done?" and treats
everything else as still running.

**Trap 2 -- the rollup GROWS, so "everything I can see is done" is not "the suite
is done".** Jobs are added to ``statusCheckRollup`` as they start. Between waves
(for example after the pre-commit matrix finishes but before the test matrix has
been created) every entry present is terminal and the suite looks complete. The
only stable anchor is the repo's own list of **required** contexts, read from the
branch ruleset. A required context that has not appeared yet is *not done* -- it is
absent, which is a distinct and important state.

Trap 2's absent-forever case is real and worth surfacing rather than hiding: a
``[skip ci]`` head commit produces a PR where required contexts never report at
all, the aggregate rollup can read as SUCCESS, and the PR sits permanently
unmergeable. This tool names those contexts instead of waiting mutely.

Read-only by construction: it issues only ``gh pr view`` and ``gh api ... /rules/...``
reads. It never merges, updates a branch, pushes, or comments -- so it is safe for
any session to run at any time. If it reports ``BEHIND``, the signing-safe fix is
``gh api repos/<owner>/<repo>/pulls/<n>/update-branch -X PUT`` (server-side commit,
therefore GitHub-signed; a local merge + push is unsigned and ``required_signatures``
rejects it fleet-wide).

Usage
-----
    python util/wait_for_checks.py --pr 1130
    python util/wait_for_checks.py --pr 524 --repo juniper-cascor
    python util/wait_for_checks.py --pr 266 --repo juniper-data --json
    python util/wait_for_checks.py --pr 42 --timeout 1800 --interval 30

Exit codes
----------
0   every required context finished and none failed
1   at least one required context failed (names printed)
2   timed out -- required contexts still running or absent (names printed)
3   hard error (``gh`` failed, no ruleset, no required-status-checks rule, bad PR)

A hard error is never reported as "nothing yet". That conflation -- a failed probe
looking identical to a legitimately empty result -- is the same class as trap 1 and
is why every ``gh`` call here checks its return code.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
import sys
import time

DEFAULT_OWNER = "pcalnon"
DEFAULT_REPO = "juniper-ml"
DEFAULT_TIMEOUT = 1800
DEFAULT_INTERVAL = 20

# Bounded retry for a flaky GitHub API. Delay-only: a persistent failure still
# raises ProbeError, so this never masks a broken probe.
PROBE_RETRIES = 3
PROBE_RETRY_BACKOFF = 2.0

# Closed set of finished check-run conclusions. Anything outside this set -- an
# empty string, None, QUEUED, IN_PROGRESS, or a value GitHub introduces later --
# counts as still running. See "Trap 1" above; do not invert this into a list of
# pending states.
TERMINAL_CONCLUSIONS = frozenset(
    {
        "SUCCESS",
        "FAILURE",
        "TIMED_OUT",
        "CANCELLED",
        "ACTION_REQUIRED",
        "NEUTRAL",
        "SKIPPED",
        "STALE",
        "ERROR",
    }
)

# Finished states for a legacy commit-status context (as opposed to a check run).
TERMINAL_STATES = frozenset({"SUCCESS", "FAILURE", "ERROR"})

# Conclusions that mean "this required check did not pass".
FAILING = frozenset({"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "ERROR"})

# Terminal PR states: no point waiting on checks for a PR that is already closed.
CLOSED_PR_STATES = frozenset({"MERGED", "CLOSED"})


class ProbeError(RuntimeError):
    """A read against the GitHub API failed, or returned something unusable.

    Raised rather than defaulted, so a broken probe can never masquerade as an
    empty-but-valid result.
    """


def _gh(args: list[str], *, retries: int = PROBE_RETRIES, sleeper=time.sleep) -> str:
    """Run ``gh`` and return stdout, raising :class:`ProbeError` if it keeps failing.

    Retries are **bounded and delay-only**: they never convert a failure into a
    success or an empty result, so the honesty property still holds -- a genuinely
    broken probe (missing PR, no ruleset, bad auth) fails every attempt and still
    raises. What they buy is surviving GitHub API flakiness, which is not
    hypothetical: two of the first three live runs of this tool died on a transient
    ``TLS handshake timeout`` and an ``unexpected EOF`` respectively, throwing away
    a wait that was minutes from finishing.

    Deliberately does not try to classify errors as transient vs permanent. That
    classification is unreliable, and getting it wrong in the "permanent" direction
    would mask a real failure -- the exact bug this module exists to avoid. Retrying
    everything a few times costs a few seconds on a genuine error and is safe.
    """
    if shutil.which("gh") is None:
        raise ProbeError("the `gh` CLI is not on PATH")
    last = ""
    for attempt in range(max(1, retries)):
        try:
            proc = subprocess.run(  # nosec B603 - fixed argv, no shell
                ["gh", *args],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:  # pragma: no cover - defensive
            raise ProbeError(f"could not execute gh: {exc}") from exc
        if proc.returncode == 0:
            return proc.stdout
        last = (proc.stderr or proc.stdout or "").strip()[:500]
        if attempt + 1 < max(1, retries):
            sleeper(PROBE_RETRY_BACKOFF * (attempt + 1))
    raise ProbeError(f"gh {' '.join(args)} failed after {max(1, retries)} attempts: {last}")


def _gh_json(args: list[str]):
    """Run ``gh`` expecting JSON on stdout."""
    out = _gh(args)
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise ProbeError(f"gh {' '.join(args)} did not return JSON: {out.strip()[:200]}") from exc


def pr_facts(owner: str, repo: str, pr: int) -> dict:
    """Return the PR's base branch, state and merge-state.

    ``mergeStateStatus`` is reported but never gated on: ``BEHIND`` is a branch
    freshness question, not a check-completion question, and conflating the two is
    how a caller ends up waiting forever on a suite that is already finished.
    """
    data = _gh_json(
        [
            "pr",
            "view",
            str(pr),
            "--repo",
            f"{owner}/{repo}",
            "--json",
            "baseRefName,state,mergeStateStatus,url",
        ]
    )
    base = data.get("baseRefName")
    if not base:
        raise ProbeError(f"could not resolve base branch for {owner}/{repo}#{pr}")
    return {
        "base": base,
        "state": data.get("state") or "",
        "merge_state": data.get("mergeStateStatus") or "",
        "url": data.get("url") or "",
    }


def required_contexts(owner: str, repo: str, branch: str) -> list[str]:
    """Return the required status-check contexts for ``branch`` from its ruleset.

    This is the anchor that makes the wait correct (see "Trap 2"). An empty or
    missing ``required_status_checks`` rule is a :class:`ProbeError`, not an empty
    list -- silently degrading to "whatever the rollup happens to show" would
    reintroduce the exact bug this module exists to prevent. Callers that genuinely
    want the unanchored behaviour must ask for it explicitly (``--anchor observed``).
    """
    rules = _gh_json(["api", f"repos/{owner}/{repo}/rules/branches/{branch}"])
    if not isinstance(rules, list):
        raise ProbeError(f"unexpected ruleset payload for {owner}/{repo}@{branch}")
    contexts: list[str] = []
    for rule in rules:
        if not isinstance(rule, dict) or rule.get("type") != "required_status_checks":
            continue
        params = rule.get("parameters") or {}
        for entry in params.get("required_status_checks") or []:
            ctx = (entry or {}).get("context")
            if ctx:
                contexts.append(ctx)
    if not contexts:
        raise ProbeError(f"no required_status_checks rule on {owner}/{repo}@{branch} " f"(use --anchor observed to wait on the observed rollup instead)")
    # Deduplicate while preserving declaration order.
    return list(dict.fromkeys(contexts))


def rollup(owner: str, repo: str, pr: int) -> list[dict]:
    """Return the rollup as ``[{name, conclusion, state, started, completed}, ...]``.

    The timestamps are carried because :func:`classify` needs them to pick between several
    runs sharing one context name, and it CANNOT do that from array position -- see the
    note there. They were previously dropped here, which is what made the bug in
    ``classify`` unfixable in place.
    """
    data = _gh_json(
        [
            "pr",
            "view",
            str(pr),
            "--repo",
            f"{owner}/{repo}",
            "--json",
            "statusCheckRollup",
        ]
    )
    rows = data.get("statusCheckRollup")
    if rows is None:
        raise ProbeError("statusCheckRollup missing from gh output")
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "name": row.get("name") or row.get("context") or "",
                "conclusion": (row.get("conclusion") or "").upper(),
                "state": (row.get("state") or "").upper(),
                # `startedAt` for a check run; legacy commit statuses carry `createdAt`.
                "started": row.get("startedAt") or row.get("createdAt") or "",
                "completed": row.get("completedAt") or "",
            }
        )
    return out


def is_terminal(row: dict) -> bool:
    """True only when the row is definitely finished.

    Positive definition on purpose -- an in-progress check run has a null
    conclusion and no state, so any "is it pending?" formulation gets this wrong.
    """
    return row["conclusion"] in TERMINAL_CONCLUSIONS or row["state"] in TERMINAL_STATES


def outcome_of(row: dict) -> str:
    """The row's finished result, or ``""`` when it has not finished."""
    if row["conclusion"] in TERMINAL_CONCLUSIONS:
        return row["conclusion"]
    if row["state"] in TERMINAL_STATES:
        return row["state"]
    return ""


def _recency(row: dict) -> tuple:
    """Sort key for 'which run of this name is the current one'.

    ISO-8601 UTC strings compare correctly as plain strings, so no parsing is needed.
    `started` leads because a run that STARTED later is the newer attempt even if it has
    not finished -- and a newer in-flight run must read as *running*, not inherit an older
    run's verdict. A row with no timestamps sorts oldest, so a real timestamped row always
    beats it rather than losing to insertion order.
    """
    return (row.get("started") or "", row.get("completed") or "")


def classify(contexts: list[str], rows: list[dict]) -> dict:
    """Bucket ``contexts`` against ``rows`` into done / running / absent / failed.

    ``absent`` is deliberately distinct from ``running``: a context that has never
    appeared may never appear (the ``[skip ci]`` orphan class), and telling the two
    apart is the difference between "be patient" and "this PR is stuck".
    """
    # Several runs can share one context name -- every trigger type produces its own, and
    # they ALL stay attached to the head SHA. GitHub counts the NEWEST; `gh pr checks`
    # collapses them to a single row pointing at it. So must this module.
    #
    # Pick by TIMESTAMP, never by array position. Two earlier attempts both got this
    # wrong, in opposite directions, and both "worked" on the example that motivated them:
    #
    #   `setdefault` (first wins)  -- reported FAILURE for a context GitHub calls pass,
    #                                 declaring a recoverable PR permanently failed.
    #   `by_name[...] = row` (last) -- assumed array order tracks recency. It does not.
    #
    # Measured on juniper-recurrence#120: rollup index 0 is 23:27:17 and index 1 is
    # 23:24:30 -- not sorted. In that one payload, three of four duplicate-named groups
    # had array-last != newest (`Lint (ruff)`, `Test (Python ...)`, `Build distribution`).
    # Either positional rule is a coin flip on undocumented connection ordering; the
    # first-wins rule would have been *correct* for those three groups and wrong for the
    # guard. Only the timestamp is load-bearing.
    by_name: dict = {}
    for row in rows:
        key = row["name"]
        prev = by_name.get(key)
        if prev is None or _recency(row) >= _recency(prev):
            by_name[key] = row

    done: list[tuple[str, str]] = []
    running: list[str] = []
    absent: list[str] = []
    failed: list[tuple[str, str]] = []

    for ctx in contexts:
        row = by_name.get(ctx)
        if row is None:
            absent.append(ctx)
            continue
        if not is_terminal(row):
            running.append(ctx)
            continue
        result = outcome_of(row)
        done.append((ctx, result))
        if result in FAILING:
            failed.append((ctx, result))

    return {
        "done": done,
        "running": running,
        "absent": absent,
        "failed": failed,
        "settled": not running and not absent,
    }


def wait_for(
    owner: str,
    repo: str,
    pr: int,
    *,
    anchor: str = "required",
    timeout: int = DEFAULT_TIMEOUT,
    interval: int = DEFAULT_INTERVAL,
    fail_fast: bool = False,
    sleeper=time.sleep,
    clock=time.monotonic,
    verbose: bool = False,
) -> dict:
    """Poll until every anchored context is finished, or ``timeout`` elapses.

    Returns a result dict; the caller maps it to an exit code. ``sleeper`` and
    ``clock`` are injected so tests can drive the loop without real time.

    ``fail_fast`` returns as soon as any anchored context has failed. Without it
    the loop keeps going for the full picture, which is the right default when you
    want every failure named -- but see the ``stalled`` flag below: dogfooding this
    tool on its own PR burned 27 polls in a state where nothing was in flight and
    the remaining required contexts were gated behind jobs that had already failed.
    """
    facts = pr_facts(owner, repo, pr)
    if facts["state"] in CLOSED_PR_STATES:
        return {
            "status": "pr_closed",
            "stalled": False,
            "pr_state": facts["state"],
            "merge_state": facts["merge_state"],
            "url": facts["url"],
            "contexts": [],
            "done": [],
            "running": [],
            "absent": [],
            "failed": [],
            "polls": 0,
        }

    contexts: list[str] = []
    if anchor == "required":
        contexts = required_contexts(owner, repo, facts["base"])

    deadline = clock() + timeout
    polls = 0
    result: dict = {}
    status = "timeout"
    anchored: list[str] = []

    while True:
        rows = rollup(owner, repo, pr)
        polls += 1
        anchored = contexts if anchor == "required" else [r["name"] for r in rows]
        result = classify(anchored, rows)
        if verbose:
            print(
                f"poll {polls}: done={len(result['done'])} running={len(result['running'])} " f"absent={len(result['absent'])} failed={len(result['failed'])}",
                file=sys.stderr,
            )
        if result["settled"]:
            status = "failed" if result["failed"] else "green"
            break
        if fail_fast and result["failed"]:
            status = "failed"
            break
        if clock() >= deadline:
            status = "timeout"
            break
        sleeper(interval)

    merge_state = pr_facts(owner, repo, pr)["merge_state"]
    # "Stalled": nothing anchored is in flight, yet required contexts are still
    # absent AND something already failed. In practice those absent contexts are
    # downstream jobs (`needs:` a failed job) that will never report, so further
    # polling cannot change the answer. Surfaced rather than acted on -- a wrong
    # early exit here would be the same class of bug this module exists to prevent.
    stalled = bool(not result["running"] and result["absent"] and result["failed"])
    return {
        "status": status,
        "stalled": stalled,
        "pr_state": facts["state"],
        "merge_state": merge_state,
        "url": facts["url"],
        "contexts": anchored,
        "done": result["done"],
        "running": result["running"],
        "absent": result["absent"],
        "failed": result["failed"],
        "polls": polls,
    }


_EXIT = {"green": 0, "failed": 1, "timeout": 2, "pr_closed": 0}


def render(res: dict, repo_ref: str, pr: int) -> str:
    """Human-readable one-screen summary."""
    lines = []
    if res["status"] == "pr_closed":
        lines.append(f"{repo_ref}#{pr} is {res['pr_state']} — nothing to wait for.")
        return "\n".join(lines)

    n_ok = sum(1 for _, r in res["done"] if r == "SUCCESS")
    head = f"{repo_ref}#{pr}: {res['status'].upper()} — " f"{len(res['done'])}/{len(res['contexts'])} required contexts finished " f"({n_ok} success), mergeState={res['merge_state'] or 'unknown'}"
    lines.append(head)
    if res["failed"]:
        lines.append("  FAILED:")
        lines.extend(f"    {ctx}: {result}" for ctx, result in res["failed"])
    if res["running"]:
        lines.append("  still running:")
        lines.extend(f"    {ctx}" for ctx in res["running"])
    if res["absent"]:
        lines.append("  never reported (may be permanently absent — e.g. a skip-ci head commit):")
        lines.extend(f"    {ctx}" for ctx in res["absent"])
    if res.get("stalled"):
        lines.append("  STALLED: nothing is in flight and a required check already failed, so the")
        lines.append("  never-reported contexts above are almost certainly downstream jobs (`needs:` a")
        lines.append("  failed job) that will never report. Fix the failures and push; waiting will not help.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wait for a PR's required status checks to finish.",
        epilog="Read-only: issues only gh reads. Never merges, updates, or pushes.",
    )
    parser.add_argument("--pr", type=int, required=True, help="pull request number")
    parser.add_argument("--repo", default=DEFAULT_REPO, help=f"repo name (default {DEFAULT_REPO})")
    parser.add_argument("--owner", default=DEFAULT_OWNER, help=f"repo owner (default {DEFAULT_OWNER})")
    parser.add_argument(
        "--anchor",
        choices=("required", "observed"),
        default="required",
        help="'required' (default) waits on the ruleset's required contexts -- the only correct anchor; 'observed' waits on whatever the rollup shows and can finish early when the rollup is still growing",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="return as soon as any required context fails, instead of waiting for the full picture",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"seconds before giving up (default {DEFAULT_TIMEOUT})")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help=f"seconds between polls (default {DEFAULT_INTERVAL})")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit the result dict as JSON")
    parser.add_argument("--verbose", action="store_true", help="log per-poll counts to stderr")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.interval < 1:
        print("error: --interval must be >= 1", file=sys.stderr)
        return 3
    if args.timeout < 0:
        print("error: --timeout must be >= 0", file=sys.stderr)
        return 3
    try:
        res = wait_for(
            args.owner,
            args.repo,
            args.pr,
            anchor=args.anchor,
            timeout=args.timeout,
            interval=args.interval,
            fail_fast=args.fail_fast,
            verbose=args.verbose,
        )
    except ProbeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    if args.as_json:
        print(json.dumps(res, indent=2, sort_keys=True))
    else:
        print(render(res, f"{args.owner}/{args.repo}", args.pr))
    return _EXIT[res["status"]]


if __name__ == "__main__":
    sys.exit(main())
