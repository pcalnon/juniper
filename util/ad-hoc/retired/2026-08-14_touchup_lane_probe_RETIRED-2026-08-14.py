"""
Probe every Juniper repo for the agents-md-touch-up lane and its required-context status.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-14
Status: RETIRED 2026-08-14 -- purpose complete (kept for provenance, not for use)
Answer it produced: the touch-up lane exists in 8 repos (NOT 9 -- juniper-recurrence
             has none), all named `Bump AGENTS.md Last Updated`, and that name was a
             required status check on NONE of them -- which is what made the rename
             to `Verify AGENTS.md Last Updated` safe to ship. Renaming a required
             context would have left every PR waiting forever on a context that
             could no longer report.
Note:        it also caught its own bug -- the first version conflated a transient
             `gh` fetch failure with a 404 and reported cascor and canopy as
             lane-less when both have the lane. Any successor MUST distinguish 404
             from error, or it will silently drop repos from a fan-out.
Related: juniper-ml#1099, juniper-cascor#518

Why: converting the lane from "commit a date bump" to "verify the date" renames
its job (``Bump ...`` -> ``Verify ...``). Renaming a status check that a ruleset
lists as REQUIRED would leave every PR waiting forever on a context that can no
longer report, so this must be checked per repo before any rename.

Usage:
    python util/ad-hoc/2026-08-14_touchup_lane_probe.py [--owner pcalnon]
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys

REPOS = [
    "juniper-ml",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-recurrence",
    "juniper-deploy",
]

WORKFLOW = ".github/workflows/agents-md-touch-up.yml"


def gh_json(args: list, retries: int = 3):
    """Return (parsed_json, status) where status is 'ok' | 'missing' | 'error'.

    A transient network failure must NEVER be reported as 'the file is absent':
    that would silently drop a repo from the fan-out. 404 is the only condition
    that means absent.
    """
    last_err = ""
    for _ in range(retries):
        proc = subprocess.run(["gh", *args], capture_output=True, text=True)
        if proc.returncode == 0:
            try:
                return json.loads(proc.stdout), "ok"
            except ValueError:
                return None, "error"
        last_err = (proc.stderr or "").strip()
        if "Not Found" in last_err or "HTTP 404" in last_err:
            return None, "missing"
    return None, "error"


def fetch_workflow(owner: str, repo: str) -> tuple:
    data, status = gh_json(["api", f"repos/{owner}/{repo}/contents/{WORKFLOW}"])
    if status != "ok" or not data or "content" not in data:
        return "", status
    try:
        return base64.b64decode(data["content"]).decode("utf-8", "replace"), "ok"
    except (ValueError, TypeError):
        return "", "error"


def required_contexts(owner: str, repo: str) -> list:
    data, _status = gh_json(["api", f"repos/{owner}/{repo}/rules/branches/main"])
    if not isinstance(data, list):
        return []
    out = []
    for rule in data:
        if rule.get("type") != "required_status_checks":
            continue
        params = rule.get("parameters") or {}
        for chk in params.get("required_status_checks") or []:
            ctx = chk.get("context")
            if ctx:
                out.append(ctx)
    return out


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="pcalnon")
    args = ap.parse_args(argv)

    print(f"{'repo':<24} {'lane?':<6} {'job name':<34} {'required?':<10} {'mutates?'}")
    print("-" * 96)
    exit_code = 0
    for repo in REPOS:
        text, status = fetch_workflow(args.owner, repo)
        if status == "missing":
            print(f"{repo:<24} {'no':<6} {'-':<34} {'-':<10} -")
            continue
        if status != "ok" or not text:
            # Loud, non-zero: an unreadable repo must be re-probed, never
            # quietly treated as 'has no lane'.
            print(f"{repo:<24} {'ERROR':<6} {'(fetch failed - re-probe)':<34} {'?':<10} ?")
            exit_code = 2
            continue

        job_name = "-"
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("name:") and ("Bump" in stripped or "Verify" in stripped):
                job_name = stripped.split("name:", 1)[1].strip().strip("\"'")
                break

        mutates = "yes" if "git commit" in text else "no"
        ctxs = required_contexts(args.owner, repo)
        is_req = "REQUIRED" if job_name in ctxs else "no"
        if is_req == "REQUIRED":
            exit_code = max(exit_code, 1)
        print(f"{repo:<24} {'yes':<6} {job_name:<34} {is_req:<10} {mutates}")
    if exit_code:
        print("\nexit != 0: re-probe the ERROR rows, and do NOT rename any REQUIRED context.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
