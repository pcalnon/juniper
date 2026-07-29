"""
ci.yml screen for the 2026-07-25..28 Cursor-fleet PR flood.

For each of the 9 ci_yml_touching merges: what the merge actually changed on
main (git diff <M>^1..<M> -- ci.yml), plus a top-level job-key + per-job
step-name inventory at each ^1 vs current main. Flags: dropped jobs, dropped
steps, dropped required-check contexts (the `required-checks` job's `needs`),
DUPLICATE job keys (the 2026-06-06 startup_failure class that yaml.safe_load
silently hides), and duplicate step names.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: agent C1 (flood remediation census)
Created: 2026-07-28
Status: ad-hoc - investigation
Retire when: the Cursor-fleet flood census is closed
Related: 2026-07-26 Cursor Automation fleet incident; 2026-06-06 dup-job-key startup_failure
"""

from __future__ import annotations

import json
import subprocess
import sys

import yaml

HEAD = "3915d1e6a7aa7330e5c16f72efefd40ebdf242a9"
CI = ".github/workflows/ci.yml"


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True)


def blob(ref: str) -> str | None:
    cp = git("cat-file", "-p", f"{ref}:{CI}")
    return cp.stdout if cp.returncode == 0 else None


def raw_dupe_job_keys(text: str) -> list[str]:
    """Detect duplicate top-level job keys textually (safe_load hides them)."""
    lines = text.splitlines()
    in_jobs = False
    seen: dict[str, int] = {}
    for ln in lines:
        if ln.rstrip() == "jobs:" or ln.startswith("jobs:"):
            in_jobs = True
            continue
        if in_jobs:
            # a new top-level key (col 0, non-space) ends the jobs block
            if ln and not ln[0].isspace() and ln.rstrip().endswith(":"):
                break
            if ln[:2] == "  " and ln[2:3] not in (" ", "\t", "#", "") and ln.lstrip().endswith(":") is False:
                pass
            # job key: exactly 2-space indent, "name:"
            if len(ln) > 2 and ln[:2] == "  " and ln[2] not in (" ", "#"):
                stripped = ln.strip()
                if stripped.endswith(":") and " " not in stripped[:-1]:
                    key = stripped[:-1]
                    seen[key] = seen.get(key, 0) + 1
    return sorted(k for k, n in seen.items() if n > 1)


def inventory(text: str):
    data = yaml.safe_load(text)
    jobs = data.get("jobs", {}) if isinstance(data, dict) else {}
    inv = {}
    for jk, jv in jobs.items():
        steps = []
        dstep = []
        if isinstance(jv, dict):
            seen = set()
            for st in jv.get("steps", []) or []:
                if isinstance(st, dict):
                    nm = st.get("name") or (f"uses:{st.get('uses')}" if st.get("uses") else "<unnamed>")
                    if nm in seen:
                        dstep.append(nm)
                    seen.add(nm)
                    steps.append(nm)
        needs = jv.get("needs") if isinstance(jv, dict) else None
        inv[jk] = {"steps": steps, "dupe_steps": dstep, "needs": needs}
    triggers = data.get(True, data.get("on")) if isinstance(data, dict) else None
    return inv, triggers


def main() -> int:
    with open(sys.argv[1]) as f:
        census = json.load(f)
    merges = {m["sha"]: m for m in census["merges"]}
    order = {m["sha"]: i for i, m in enumerate(census["merges"])}
    ci_merges = sorted(census["buckets"]["ci_yml_touching"], key=lambda s: order.get(s, 999))

    head_text = blob(HEAD)
    head_inv, head_trig = inventory(head_text)
    head_jobs = set(head_inv)
    head_dupes = raw_dupe_job_keys(head_text)

    print("=== HEAD ci.yml ===")
    print(f"jobs ({len(head_jobs)}): {sorted(head_jobs)}")
    print(f"DUPLICATE job keys @HEAD: {head_dupes or 'none'}")
    rc = head_inv.get("required-checks") or head_inv.get("required_checks")
    print(f"required-checks.needs @HEAD: {rc['needs'] if rc else '<no required-checks job>'}")
    for j, d in head_inv.items():
        if d["dupe_steps"]:
            print(f"  DUP STEPS in {j}: {d['dupe_steps']}")
    print()

    union_prior_jobs = set()
    findings = []
    for sha in ci_merges:
        m = merges[sha]
        p1 = blob(f"{sha}^1")
        cur = blob(sha)
        print(f"--- PR#{m['pr']} {sha[:9]} ({m['branch'][:44]})")
        if p1 is None:
            print("   ci.yml absent at ^1 (new file)")
        else:
            inv1, _ = inventory(p1)
            jobs1 = set(inv1)
            union_prior_jobs |= jobs1
            d1 = raw_dupe_job_keys(p1)
            if d1:
                print(f"   DUP job keys at ^1: {d1}")
        # what the MERGE changed on main
        diff = git("diff", "--stat", f"{sha}^1", sha, "--", CI).stdout.strip()
        namestat = git("diff", f"{sha}^1", sha, "--", CI).stdout
        added = [l for l in namestat.splitlines() if l.startswith("+") and not l.startswith("+++")]
        removed = [l for l in namestat.splitlines() if l.startswith("-") and not l.startswith("---")]
        curd = raw_dupe_job_keys(cur) if cur else []
        # job-level delta of the merge
        if p1 and cur:
            j1 = set(inventory(p1)[0]); j2 = set(inventory(cur)[0])
            dropped = j1 - j2; addedj = j2 - j1
            if dropped:
                findings.append((m["pr"], sha, "merge dropped job(s)", sorted(dropped)))
                print(f"   *** MERGE DROPPED JOBS: {sorted(dropped)}")
            if addedj:
                print(f"   merge added jobs: {sorted(addedj)}")
        if curd:
            findings.append((m["pr"], sha, "merge introduced DUP job keys", curd))
            print(f"   *** MERGE INTRODUCED DUP JOB KEYS: {curd}")
        print(f"   merge ci.yml diff: {diff or '(no net change to ci.yml in merge)'}  (+{len(added)}/-{len(removed)} lines)")

    print("\n=== union of all ^1 job sets vs HEAD ===")
    dropped_vs_head = union_prior_jobs - head_jobs
    print(f"jobs present at some ^1 but ABSENT at HEAD: {sorted(dropped_vs_head) or 'none'}")
    print(f"\nFINDINGS: {findings or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
