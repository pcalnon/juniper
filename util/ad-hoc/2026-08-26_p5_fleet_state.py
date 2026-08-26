#!/usr/bin/env python3
"""
P5 fleet census: per governed repo, what origin's main carries -- port PR state, ceiling,
AGENTS.md size in CHARS, headroom, whether the memory-budget job is still `--advisory`, and
whether `Memory Budget` is a required context in the branch ruleset.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc — investigation (P5 fleet rollout, plan §P5 step d; tracker juniper-ml#1326)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-25_p5-four-ports-and-helper-fold.md
         ("Remaining work" step 1: confirm what the merge run landed);
         util/ad-hoc/2026-08-25_p5_port_verify.bash (the in-worktree controls this census precedes)

Why a script: a worktree-isolated session's shell gate refuses `for` loops and command
substitution, so a nine-repo census is either ~40 hand-typed commands or one script. Every fact
here comes from the GitHub API against origin's `main` (contents / pulls / rules), never from a
local checkout that might be behind. Sizes are counted in CHARS -- `len()` of the UTF-8-decoded
text -- because that is the ceiling's unit; the API's `size` field is BYTES, and a census that
read bytes against a char ceiling concluded two repos were over when both sat exactly at ceiling
(2026-08-25). Nothing here writes anything.

Usage:
    python3 util/ad-hoc/2026-08-26_p5_fleet_state.py [--json] [--repo NAME ...]
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess  # nosec B404 -- fixed-argv `gh api` calls only; nothing is shell-interpolated
import sys
import time

OWNER = "pcalnon"

# (repo, port PR number or None, workflow that carries the memory-budget job)
ROSTER = [
    ("juniper-canopy", 516, ".github/workflows/ci.yml"),
    ("juniper-cascor", 585, ".github/workflows/ci.yml"),
    ("juniper-cascor-client", 139, ".github/workflows/ci.yml"),
    ("juniper-recurrence", 131, ".github/workflows/memory-budget.yml"),
    ("juniper-data-client", 173, ".github/workflows/ci.yml"),
    ("juniper-data", 291, ".github/workflows/ci.yml"),
    ("juniper-cascor-worker", 162, ".github/workflows/ci.yml"),
    ("juniper-deploy", 195, ".github/workflows/ci.yml"),
    ("juniper-ml", None, ".github/workflows/ci.yml"),
]

CONTEXT = "Memory Budget"


def gh_api(path: str) -> dict | list | None:
    """GET one REST path through `gh api`. None means 404 (genuinely absent) and NOTHING else.

    This returned None on ANY non-2xx until 2026-08-26, which made a rate-limit, a 5xx or a
    network blip indistinguishable from "the file is not there". Observed: two consecutive
    censuses in the same minute disagreed about juniper-canopy's docs/REFERENCE.md -- 9,672 chars,
    then NONE -- while the file was present the whole time (9,676 bytes, sha 87ee5fb6). A census
    that under-reports a file as absent is worse than one that crashes: step e keys off exactly
    which repos still need a REFERENCE.md, so a false NONE invents work and a false present hides
    it. Retry the transient classes, then fail loud rather than return a plausible wrong answer.
    """
    last = ""
    for attempt in range(4):
        proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)  # nosec B603 B607 -- fixed argv, gh on PATH by policy
        if proc.returncode == 0:
            try:
                return json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"gh api {path}: 2xx with unparseable JSON: {exc}") from exc
        last = (proc.stderr or proc.stdout).strip()
        if "HTTP 404" in last or '"status":"404"' in last:
            return None  # the only benign absence
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"gh api {path}: failed after 4 attempts, last error: {last[:300]}")


def contents(repo: str, path: str) -> str | None:
    """Decoded text of a file on main, or None if absent. Counted in chars by the caller."""
    obj = gh_api(f"repos/{OWNER}/{repo}/contents/{path}?ref=main")
    if not isinstance(obj, dict) or obj.get("encoding") != "base64":
        return None
    return base64.b64decode(obj["content"]).decode("utf-8")


def required_contexts(repo: str) -> list[str]:
    rules = gh_api(f"repos/{OWNER}/{repo}/rules/branches/main")
    out: list[str] = []
    if not isinstance(rules, list):
        return out
    for rule in rules:
        if rule.get("type") != "required_status_checks":
            continue
        for chk in rule.get("parameters", {}).get("required_status_checks", []):
            out.append(chk.get("context", ""))
    return out


def _size_check_is_advisory(wf: str) -> bool:
    """Is `--advisory` on the memory_budget_check.py INVOCATION, not merely in the file?

    This was `"--advisory" in wf` until 2026-08-26 and read True fleet-wide the moment the
    de-advisory PRs landed -- a false alarm, because every de-advisoried workflow explains the
    removal in a comment ("`--advisory` (the soak setting) is gone"), and juniper-ml keeps a real
    `--advisory` on the SEPARATE relocation_check.py invocation. A whole-file substring cannot
    tell live args from prose, so it reported ADVISORY for nine repos that are all BLOCKING.

    Reconstruct the shell invocation instead: the `memory_budget_check.py` line plus every line
    joined to it by a trailing backslash, with inline `# ...` comments stripped. Returns False
    when no invocation is found -- the caller's `job_present` is what reports that case.
    """
    lines = wf.splitlines()
    for i, line in enumerate(lines):
        if "memory_budget_check.py" not in line:
            continue
        if line.strip().startswith("#") or "unittest" in line:
            continue
        block, j = [line], i
        while lines[j].rstrip().endswith("\\") and j + 1 < len(lines):
            j += 1
            block.append(lines[j])
        args = "\n".join(re.sub(r"\s+#.*$", "", b) for b in block)
        return "--advisory" in args
    return False


def census(repo: str, pr: int | None, workflow: str) -> dict:
    row: dict = {"repo": repo, "port_pr": pr}
    head = gh_api(f"repos/{OWNER}/{repo}/commits/main")
    row["main_sha"] = (head or {}).get("sha", "?")[:8]
    if pr is not None:
        pobj = gh_api(f"repos/{OWNER}/{repo}/pulls/{pr}") or {}
        row["pr_state"] = "MERGED" if pobj.get("merged_at") else pobj.get("state", "?").upper()
        row["pr_merged_at"] = pobj.get("merged_at")
        row["pr_merge_sha"] = (pobj.get("merge_commit_sha") or "?")[:8]
    budget_text = contents(repo, "conf/memory_budget.json")
    row["budget_present"] = budget_text is not None
    row["files"] = []
    if budget_text is not None:
        budget = json.loads(budget_text)
        for path, spec in budget.get("files", {}).items():
            text = contents(repo, path)
            chars = len(text) if text is not None else None
            ceiling = spec.get("ceiling_chars") if isinstance(spec, dict) else None
            row["files"].append(
                {
                    "path": path,
                    "ceiling_chars": ceiling,
                    "chars": chars,
                    "headroom": (ceiling - chars) if (ceiling is not None and chars is not None) else None,
                }
            )
    wf = contents(repo, workflow)
    row["workflow"] = workflow
    row["workflow_present"] = wf is not None
    row["job_present"] = bool(wf) and "memory_budget_check.py" in wf
    row["advisory_flag"] = bool(wf) and _size_check_is_advisory(wf)
    row["banner"] = "ADVISORY" if (wf and "(ADVISORY)" in wf) else ("BLOCKING" if (wf and "(BLOCKING)" in wf) else "?")
    ref = contents(repo, "docs/REFERENCE.md")
    row["reference_md_chars"] = len(ref) if ref is not None else None
    row["reference_mentions_advisory"] = bool(ref) and ("Memory Budget" in ref or "memory-budget" in ref) and "ADVISORY" in ref
    agents = contents(repo, "AGENTS.md")
    row["agents_mentions_gate"] = bool(agents) and ("memory_budget" in agents or "Memory Budget" in agents or "memory-budget" in agents)
    row["agents_mentions_advisory"] = bool(agents) and row["agents_mentions_gate"] and "advisory" in agents.lower()
    req = required_contexts(repo)
    row["required_contexts"] = len(req)
    row["memory_budget_required"] = CONTEXT in req
    return row


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--json", action="store_true", help="emit the census as JSON instead of a table")
    ap.add_argument("--repo", action="append", help="repeatable; default: the full roster")
    ap.add_argument("--dump", metavar="DIR", help="also write each repo's workflow, budget file and docs/REFERENCE.md (as on main) into DIR for offline diffing")
    args = ap.parse_args(argv)
    roster = [r for r in ROSTER if not args.repo or r[0] in args.repo]
    rows = [census(*r) for r in roster]
    if args.dump:
        from pathlib import Path

        out_dir = Path(args.dump)
        out_dir.mkdir(parents=True, exist_ok=True)
        for repo, _pr, workflow in roster:
            for rel in (workflow, "conf/memory_budget.json", "docs/REFERENCE.md"):
                text = contents(repo, rel)
                if text is None:
                    continue
                (out_dir / f"{repo}__{rel.replace('/', '__')}").write_text(text, encoding="utf-8")
        print(f"dumped main-branch copies into {out_dir}\n")
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    hdr = f"{'repo':22} {'main':8} {'port PR':16} {'ceiling':>8} {'chars':>8} {'headroom':>8} {'advisory':8} {'banner':8} {'required':8} {'REF.md':>8} {'AGENTS says':11}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        f = r["files"][0] if r["files"] else {}
        pr = f"#{r['port_pr']} {r.get('pr_state', '')}" if r["port_pr"] else "(origin)"
        ref = str(r["reference_md_chars"]) if r["reference_md_chars"] is not None else "NONE"
        agents_says = "advisory" if r["agents_mentions_advisory"] else ("gate" if r["agents_mentions_gate"] else "-")
        print(
            f"{r['repo']:22} {r['main_sha']:8} {pr:16} {str(f.get('ceiling_chars', '-')):>8} {str(f.get('chars', '-')):>8} "
            f"{str(f.get('headroom', '-')):>8} {str(r['advisory_flag']):8} {r['banner']:8} {str(r['memory_budget_required']):8} {ref:>8} {agents_says:11}"
        )
    missing = [r["repo"] for r in rows if not r["job_present"]]
    if missing:
        print(f"\n!! memory-budget job NOT found on main in: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
