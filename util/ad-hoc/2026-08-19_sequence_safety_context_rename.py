#!/usr/bin/env python3
"""Rename the sequence-safety check from "Sequence Safety (Advisory)" to "Sequence Safety".

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License

Why the suffix is wrong now
---------------------------
The screen was promoted to a REQUIRED status check on all 9 repos on 2026-08-18 (ml#1011).
juniper-ml's job was always plain ``Sequence Safety``; the other eight still say
``Sequence Safety (Advisory)`` -- a required gate labelled advisory, which is actively
misleading to anyone reading a PR's check list.

THE ORDERING TRAP -- read before running anything
-------------------------------------------------
The job name **is** the required-context string, so a rename is a two-sided change. And a PR
that renames the job publishes the **NEW** name on its own CI run, which means the currently
required ``Sequence Safety (Advisory)`` context never reports on it -- the rename PR would be
**permanently blocked, by itself**.

So the only order that works is:

1. ``--phase unrequire``  -- drop the old context from the ruleset (all 8)
2. ``--phase pr``         -- open the workflow rename PRs; merge them
3. ``--phase require``    -- add the new context to the ruleset (all 8)

Between 1 and 3 the screen is **not enforced**. That is deliberate: it is the state the screen
was in until 2026-08-18, and it is far preferable to the alternative, which is blocking every
merge on all eight repos. Keep the window short.

Any PR that was already open and green before the rename will be missing the new context until
its CI re-runs; ``gh api repos/<owner>/<repo>/pulls/<n>/update-branch -X PUT`` re-triggers it.

Commits are created through the GitHub API (``util/open_signed_pr.py``), so they are
GitHub-signed and satisfy ``required_signatures`` -- and no sibling checkout is written to,
which matters because other sessions use those trees.

Usage
-----
    python3 util/ad-hoc/2026-08-19_sequence_safety_context_rename.py --phase status
    python3 util/ad-hoc/2026-08-19_sequence_safety_context_rename.py --phase unrequire
    python3 util/ad-hoc/2026-08-19_sequence_safety_context_rename.py --phase unrequire --execute
    python3 util/ad-hoc/2026-08-19_sequence_safety_context_rename.py --phase pr --execute
    python3 util/ad-hoc/2026-08-19_sequence_safety_context_rename.py --phase require --execute

Exit codes: 0 all requested repos OK / 1 at least one failed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

OWNER = "pcalnon"
OLD = "Sequence Safety (Advisory)"
NEW = "Sequence Safety"
WORKFLOW = ".github/workflows/sequence-safety.yml"
ACTIONS_INTEGRATION_ID = 15368
SIBLING_ROOT = pathlib.Path("/home/pcalnon/Development/python/Juniper")
BRANCH = "chore/sequence-safety-drop-advisory-suffix"

# juniper-ml is absent on purpose: its job is already plain "Sequence Safety".
REPOS = [
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-recurrence",
]


class Failed(RuntimeError):
    pass


def gh(args: list[str], stdin: str | None = None) -> str:
    proc = subprocess.run(  # nosec B603 B607
        ["gh", *args], capture_output=True, text=True, timeout=180, input=stdin, check=False
    )
    if proc.returncode != 0:
        raise Failed(f"gh {' '.join(args[:3])}… failed: {proc.stderr.strip()[:250]}")
    return proc.stdout


def ruleset_id(repo: str) -> int:
    data = json.loads(gh(["api", f"/repos/{OWNER}/{repo}/rulesets"]))
    for rs in data:
        if rs.get("target") == "branch" and rs.get("name") != "juniper-no-direct-push":
            return int(rs["id"])
    raise Failed(f"{repo}: no primary branch ruleset found")


def contexts(repo: str) -> list[str]:
    return json.loads(
        gh([
            "api", f"/repos/{OWNER}/{repo}/rules/branches/main", "--jq",
            '[.[]|select(.type=="required_status_checks")|.parameters.required_status_checks[].context]',
        ])
    )


def set_contexts(repo: str, rid: int, names: list[str]) -> None:
    """Full-replacement PUT; everything but the one context array is carried verbatim."""
    live = json.loads(gh(["api", f"/repos/{OWNER}/{repo}/rulesets/{rid}"]))
    before_rules = sorted(r["type"] for r in live["rules"])
    before_bypass = len(live.get("bypass_actors") or [])
    rules = []
    for rule in live["rules"]:
        if rule["type"] != "required_status_checks":
            rules.append(rule)
            continue
        params = json.loads(json.dumps(rule["parameters"]))
        # PRESERVE each context's existing integration_id. Hardcoding the GitHub Actions id
        # here clobbered juniper-cascor's `Bandit` context (integration 57789) on five repos
        # and made their `main` permanently unmergeable: GitHub then expected "Bandit" FROM
        # ACTIONS, which never reports it. A required context that can never be satisfied is
        # exactly the failure this whole effort exists to prevent, and nothing goes red -- the
        # PRs simply stop merging. Only a genuinely NEW context defaults to Actions.
        existing = {
            c["context"]: c.get("integration_id", ACTIONS_INTEGRATION_ID)
            for c in rule["parameters"]["required_status_checks"]
        }
        params["required_status_checks"] = [
            {"context": c, "integration_id": existing.get(c, ACTIONS_INTEGRATION_ID)}
            for c in names
        ]
        rules.append({**rule, "parameters": params})
    payload = {
        "name": live["name"],
        "target": live["target"],
        "enforcement": live["enforcement"],
        "bypass_actors": [
            {"actor_id": a.get("actor_id"), "actor_type": a["actor_type"], "bypass_mode": a["bypass_mode"]}
            for a in (live.get("bypass_actors") or [])
        ],
        "conditions": live["conditions"],
        "rules": rules,
    }
    got = json.loads(gh(["api", "-X", "PUT", f"/repos/{OWNER}/{repo}/rulesets/{rid}", "--input", "-"],
                        stdin=json.dumps(payload)))
    if sorted(r["type"] for r in got["rules"]) != before_rules:
        raise Failed(f"{repo}: rule set changed during the edit")
    if len(got.get("bypass_actors") or []) != before_bypass:
        raise Failed(f"{repo}: bypass actor count changed during the edit")
    before_ids = {
        c["context"]: c.get("integration_id")
        for r in live["rules"] if r["type"] == "required_status_checks"
        for c in r["parameters"]["required_status_checks"]
    }
    after_ids = {
        c["context"]: c.get("integration_id")
        for r in got["rules"] if r["type"] == "required_status_checks"
        for c in r["parameters"]["required_status_checks"]
    }
    drifted = [c for c, i in after_ids.items() if c in before_ids and before_ids[c] != i]
    if drifted:
        raise Failed(f"{repo}: integration_id changed for {drifted} — a context that never reports")


def phase_status(repo: str) -> str:
    have = [c for c in contexts(repo) if "Sequence Safety" in c]
    src = SIBLING_ROOT / repo / WORKFLOW
    job = "?"
    if src.exists():
        for ln in src.read_text(encoding="utf-8").splitlines():
            if ln.strip().startswith("name: Sequence Safety"):
                job = ln.strip()[6:]
                break
    return f"{repo:<24} job='{job}'  required={have or 'none'}"


def phase_unrequire(repo: str, execute: bool) -> str:
    cur = contexts(repo)
    if OLD not in cur:
        return f"SKIP     {repo}: '{OLD}' not required"
    want = [c for c in cur if c != OLD]
    if not execute:
        return f"DRY      {repo}: would drop '{OLD}' ({len(cur)} -> {len(want)} contexts)"
    set_contexts(repo, ruleset_id(repo), want)
    return f"OK       {repo}: dropped '{OLD}' ({len(cur)} -> {len(contexts(repo))})"


def phase_require(repo: str, execute: bool) -> str:
    cur = contexts(repo)
    if NEW in cur:
        return f"SKIP     {repo}: '{NEW}' already required"
    if OLD in cur:
        raise Failed(f"{repo}: '{OLD}' is still required — run --phase unrequire first")
    want = cur + [NEW]
    if not execute:
        return f"DRY      {repo}: would add '{NEW}' ({len(cur)} -> {len(want)} contexts)"
    set_contexts(repo, ruleset_id(repo), want)
    return f"OK       {repo}: added '{NEW}' ({len(cur)} -> {len(contexts(repo))})"


def phase_pr(repo: str, execute: bool) -> str:
    src = SIBLING_ROOT / repo / WORKFLOW
    if not src.exists():
        raise Failed(f"{repo}: {WORKFLOW} not found at {src}")
    text = src.read_text(encoding="utf-8")
    needle = f"name: {OLD}"
    if needle not in text:
        return f"SKIP     {repo}: already renamed"

    # Each workflow carries the string TWICE: a workflow-level `name:` at column 0, and the
    # INDENTED job-level `name:`. Only the indented one is the required-context string; the
    # workflow-level one is the Actions-UI label. Both are misleading once the check is
    # required, and renaming the label is cosmetic-safe, so both are replaced -- but the shape
    # is asserted first, because silently renaming the wrong one would leave the required
    # context unpublished and block every merge on the repo.
    hits = [ln for ln in text.splitlines() if ln.strip() == needle]
    job_hits = [ln for ln in hits if ln.startswith((" ", "\t"))]
    top_hits = [ln for ln in hits if not ln.startswith((" ", "\t"))]
    if len(job_hits) != 1 or len(top_hits) != 1:
        raise Failed(
            f"{repo}: expected 1 job-level + 1 workflow-level '{needle}', "
            f"got job={len(job_hits)} workflow={len(top_hits)} — inspect before renaming"
        )
    updated = text.replace(needle, f"name: {NEW}")

    # Never write into the sibling checkout -- other sessions use those trees.
    tmp = pathlib.Path(tempfile.gettempdir()) / f"{repo}-sequence-safety.yml"
    tmp.write_text(updated, encoding="utf-8")

    opener = pathlib.Path(__file__).resolve().parents[1] / "open_signed_pr.py"
    body = (
        "Drops the `(Advisory)` suffix now that the screen is a REQUIRED status check "
        "(juniper-ml#1011, 2026-08-18). A required gate labelled advisory is misleading.\n\n"
        "The job name **is** the required-context string, so this lands as part of a three-phase "
        "sequence: the old context was removed from the ruleset first (otherwise this very PR "
        "would be blocked by a context it no longer publishes), and the new context is added "
        "after merge. The screen is unenforced only for the window between those steps.\n\n"
        "Refs pcalnon/juniper-ml#1011\n"
    )
    body_file = pathlib.Path(tempfile.gettempdir()) / f"{repo}-rename-body.md"
    body_file.write_text(body, encoding="utf-8")

    cmd = [
        sys.executable, str(opener),
        "--repo", repo, "--branch", BRANCH,
        "--add", f"{tmp}:{WORKFLOW}",
        "--message", "chore(sequence-safety): drop the (Advisory) suffix from the required check",
        "--title", "chore(sequence-safety): drop the (Advisory) suffix from the required check",
        "--body-file", str(body_file),
    ]
    if not execute:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)  # nosec B603
    out = (proc.stdout or "").strip().splitlines()
    tail = out[-1] if out else (proc.stderr or "").strip()[:200]
    if proc.returncode != 0:
        raise Failed(f"{repo}: open_signed_pr exit {proc.returncode}: {tail}")
    return f"{'OK  ' if execute else 'DRY '}     {repo}: {tail}"


PHASES = {
    "status": None,
    "unrequire": phase_unrequire,
    "pr": phase_pr,
    "require": phase_require,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", required=True, choices=sorted(PHASES))
    ap.add_argument("--repo", help="operate on one repo instead of all 8")
    ap.add_argument("--execute", action="store_true", help="actually write (default: dry-run)")
    args = ap.parse_args()

    targets = [args.repo] if args.repo else REPOS
    if args.repo and args.repo not in REPOS:
        print(f"unknown repo: {args.repo}", file=sys.stderr)
        return 1
    if args.phase != "status" and not args.execute:
        print("*** DRY RUN — nothing will be written (pass --execute) ***\n")

    failed = False
    for repo in targets:
        try:
            print(phase_status(repo) if args.phase == "status"
                  else PHASES[args.phase](repo, args.execute))
        except (Failed, subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as exc:
            failed = True
            print(f"FAIL     {repo}: {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
