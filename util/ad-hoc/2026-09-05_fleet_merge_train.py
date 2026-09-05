#!/usr/bin/env python3
"""2026-09-05_fleet_merge_train.py -- serial merge driver for a vetted fleet-PR set.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License

WHY A DRIVER

Under `strict_required_status_checks_policy: true` with `allow_update_branch: false`,
every landed merge makes every sibling PR BEHIND, and a BEHIND PR cannot merge until a
manual base refresh re-runs the FULL required-check battery (17 contexts, ~8-20 min on
juniper-ml). A vetted set of N PRs is therefore a STRICTLY SERIAL train, not a batch.

Three hazards this encodes so they are not re-learned per PR:

1. `util/safe_merge.py` EXITS 0 WITHOUT MERGING. It can arm an auto-merge net and return
   while the PR is still open (and a network blip mid-run does exactly that). Exit 0 is
   not evidence; the only evidence is the PR's own `state == MERGED`. This driver
   re-reads state from `gh` after every attempt and never trusts the return code.

2. THE SET GOES STALE UNDERNEATH YOU. Other sessions merge concurrently -- juniper-ml
   #1702 was found already MERGED at 06:49Z, before this driver ever reached it. Each PR
   is therefore re-checked immediately before its attempt, and an already-merged or
   closed PR is skipped rather than treated as an error.

3. DRAFTS MUST BE UNDRAFTED FIRST, and that is the one irreversible-ish step here, so it
   happens only after the state re-check, and only in --execute mode.

Dry-run by default: prints the plan and the live state of every PR, touches nothing.

Usage:
    python util/ad-hoc/2026-09-05_fleet_merge_train.py --repo juniper-ml --owner pcalnon \\
        --pr 1707 --pr 1709 [...] [--execute] [--timeout 2400]
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv gh/python invocations, no shell
import sys
import time
from pathlib import Path

SAFE_MERGE = Path("util/safe_merge.py")


def _run(cmd: list, timeout: int | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603


def pr_state(owner: str, repo: str, pr: int) -> dict:
    """Live state. A merge decision is only ever made from THIS, never from an exit code."""
    cp = _run(["gh", "pr", "view", str(pr), "--repo", f"{owner}/{repo}", "--json", "state,isDraft,mergedAt,title"])
    if cp.returncode != 0:
        return {"error": (cp.stderr or cp.stdout).strip()[:200]}
    try:
        return json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        return {"error": f"non-JSON from gh: {exc}"}


def merge_one(owner: str, repo: str, pr: int, *, execute: bool, timeout: int) -> dict:
    before = pr_state(owner, repo, pr)
    if "error" in before:
        return {"pr": pr, "result": "ERROR", "detail": before["error"]}
    if before.get("state") != "OPEN":
        return {"pr": pr, "result": "SKIP", "detail": f"already {before.get('state')} ({before.get('mergedAt') or '-'})"}

    if not execute:
        return {"pr": pr, "result": "DRY-RUN", "detail": f"OPEN draft={before.get('isDraft')} -- would undraft+merge"}

    if before.get("isDraft"):
        cp = _run(["gh", "pr", "ready", str(pr), "--repo", f"{owner}/{repo}"])
        if cp.returncode != 0:
            return {"pr": pr, "result": "ERROR", "detail": f"undraft failed: {(cp.stderr or cp.stdout).strip()[:160]}"}

    started = time.time()
    try:
        cp = _run([sys.executable, str(SAFE_MERGE), "--pr", str(pr), "--repo", repo, "--owner", owner, "--execute"], timeout=timeout)
        tail = "\n".join((cp.stdout + cp.stderr).strip().splitlines()[-3:])
    except subprocess.TimeoutExpired:
        tail = f"safe_merge exceeded {timeout}s"

    # THE ONLY EVIDENCE. safe_merge's exit code is deliberately not consulted.
    after = pr_state(owner, repo, pr)
    elapsed = int(time.time() - started)
    if after.get("state") == "MERGED":
        return {"pr": pr, "result": "MERGED", "detail": f"{after.get('mergedAt')} in {elapsed}s"}
    return {"pr": pr, "result": "NOT-MERGED", "detail": f"state={after.get('state')} after {elapsed}s | {tail}"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--pr", type=int, action="append", required=True)
    ap.add_argument("--execute", action="store_true", help="actually undraft + merge (default: dry-run)")
    ap.add_argument("--timeout", type=int, default=2400, help="per-PR safe_merge timeout, seconds")
    ap.add_argument("--stop-on-fail", action="store_true", help="halt the train on the first NOT-MERGED/ERROR")
    args = ap.parse_args(argv)

    if args.execute and not SAFE_MERGE.is_file():
        print(f"error: {SAFE_MERGE} not found; run from the juniper-ml repo root", file=sys.stderr)
        return 2

    results = []
    for pr in args.pr:
        r = merge_one(args.owner, args.repo, pr, execute=args.execute, timeout=args.timeout)
        results.append(r)
        print(f"  #{r['pr']:<6} {r['result']:<11} {r['detail']}", flush=True)
        if args.stop_on_fail and r["result"] in ("NOT-MERGED", "ERROR"):
            print("  -- halting: --stop-on-fail", flush=True)
            break

    merged = [r for r in results if r["result"] == "MERGED"]
    print(f"\nMERGED {len(merged)}/{len(args.pr)}; remaining: {[r['pr'] for r in results if r['result'] not in ('MERGED', 'SKIP')]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
