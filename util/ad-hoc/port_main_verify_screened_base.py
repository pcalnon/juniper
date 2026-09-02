#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Port juniper-ml's SCREENED-not-GREEN catch-up base (ml#1291) into another repo's
``.github/workflows/main-verify.yml``.

Why this exists
---------------
Eight of the nine repos carrying ``main-verify.yml`` resolved their post-merge catch-up
BASE from the last **GREEN** run::

    runs?status=success&branch=main&per_page=1

which conflates "where does the un-screened region begin?" with "where were we last
clean". A screen FINDING then pins the base, so every later merge re-screens the same
window and fails on someone else's damage -- ``main`` goes permanently red rather than
self-clearing. Measured on juniper-canopy 2026-08-31 (canopy#549 -> red on b9ad8255,
base stuck at ab210ec7, escaped only via the hand-authored waiver canopy#553).

What it changes (three edits, all anchored on verbatim strings)
--------------------------------------------------------------
1. ``id: screens`` on the screens step, so its exit codes become step outputs.
2. The screens step stops failing on a finding: it records ``src``/``drc`` and exits 0.
   Two new steps follow -- ``Assert screens reached a verdict`` (coverage signal, fails
   only on an invocation error >=2) and ``Assert screens clean`` (the job's red/green).
   **This split is load-bearing**: if the screens step still failed on a finding, the
   coverage step would be SKIPPED on exactly the runs whose windows most need marking
   screened, silently reinstating the defect.
3. The resolver gains TIER 1 (walk completed runs, take the newest whose screen job
   reached a verdict) ahead of the existing legacy tier, which is KEPT -- no historical
   run carries the tier-1 step name, so without it the first run after the change would
   not sweep, and it is a sound conservative fallback if the jobs API is unavailable.

Safety
------
Idempotent: refuses a file that already contains the tier-1 marker. Every edit asserts
its anchor is present exactly once before substituting, so a drifted file fails loudly
rather than being half-patched. After patching it re-parses the YAML and runs ``bash -n``
over every ``run:`` block; a failure restores the original and exits non-zero.

Usage:  port_main_verify_screened_base.py <repo-root> [--dry-run]
Exit:   0 patched (or already ported, with --dry-run); 1 refused; 2 validation failed.
"""

import argparse
import os
import subprocess  # nosec B404 - bash -n on our own generated workflow text
import sys
import tempfile

import yaml

WORKFLOW_REL = os.path.join(".github", "workflows", "main-verify.yml")
TIER1_MARKER = "VERDICT_STEP="

ANCHOR_SCREENS_STEP = """      - name: Run sequence-safety screens (symbol + docs)
        env:"""
REPLACE_SCREENS_STEP = """      - name: Run sequence-safety screens (symbol + docs)
        id: screens
        env:"""

ANCHOR_TAIL = '''          if [ "${src}" -ge 2 ] || [ "${drc}" -ge 2 ]; then
            echo "::error::sequence-safety screen invocation error (see log)"
            exit 2
          fi
          if [ "${src}" -ge 1 ] || [ "${drc}" -ge 1 ]; then
            echo "::error::post-merge compositional-loss finding(s) at ${HEAD_SHA} -- see the screens above and the sequence-safety-report artifact"
            exit 1
          fi
          echo "::notice::sequence-safety screens clean at ${HEAD_SHA}"
'''

REPLACE_TAIL = '''          # Publish the exit codes for the two assert steps. This step deliberately does NOT fail
          # on a finding -- if it did, the coverage step below would be SKIPPED on exactly the runs
          # whose windows most need to be marked screened.
          echo "src=${src}" >> "$GITHUB_OUTPUT"
          echo "drc=${drc}" >> "$GITHUB_OUTPUT"
          exit 0

      # -- G3.1 COVERAGE SIGNAL ------------------------------------------------------------------
      # !! LOAD-BEARING STEP NAME. The `Resolve catch-up base` step queries this step's conclusion
      # !! through the jobs API to decide whether a run screened its window. Renaming it does not
      # !! fail anything -- it silently drops the resolver to the legacy tier and restores the
      # !! recurring-red defect.
      #
      # Fails ONLY on a screen INVOCATION error (exit >=2), where no verdict exists and the window
      # is genuinely un-screened. A compositional-loss FINDING (exit 1) is a verdict: the window
      # WAS screened, so this step passes and the base is free to advance past it. If the screens
      # step above died outright, this step is `skipped` -- which is not `success`, so no false
      # coverage is ever claimed.
      - name: Assert screens reached a verdict
        env:
          SRC: ${{ steps.screens.outputs.src }}
          DRC: ${{ steps.screens.outputs.drc }}
        run: |
          set -uo pipefail
          # Absent outputs are treated as an invocation error, never as coverage.
          src="${SRC:-99}"
          drc="${DRC:-99}"
          if [ "${src}" -ge 2 ] || [ "${drc}" -ge 2 ]; then
            echo "::error::sequence-safety screen invocation error (symbol=${src} docs=${drc}) -- window NOT screened; the G3.1 catch-up base will NOT advance past this run"
            exit 2
          fi
          echo "::notice::sequence-safety screens reached a verdict (symbol=${src} docs=${drc}) -- this window IS screened"

      # -- VERDICT SIGNAL ------------------------------------------------------------------------
      # The job's red/green. Unchanged in effect: a finding still fails the job, the run, and fires
      # `Notify on Failure`. Only the SHAPE of the failure moved -- from one failing step to a
      # passing coverage step plus this one.
      - name: Assert screens clean
        env:
          SRC: ${{ steps.screens.outputs.src }}
          DRC: ${{ steps.screens.outputs.drc }}
          HEAD_SHA: ${{ github.sha }}
        run: |
          set -uo pipefail
          src="${SRC:-99}"
          drc="${DRC:-99}"
          if [ "${src}" -ge 1 ] || [ "${drc}" -ge 1 ]; then
            echo "::error::post-merge compositional-loss finding(s) at ${HEAD_SHA} -- see the screens above and the sequence-safety-report artifact"
            exit 1
          fi
          echo "::notice::sequence-safety screens clean at ${HEAD_SHA}"
'''

ANCHOR_RESOLVER = '''          last_ok="$(gh api "repos/${REPO}/actions/workflows/main-verify.yml/runs?status=success&branch=main&per_page=1" --jq '.workflow_runs[0].head_sha' 2>/dev/null || true)"
          base=""
          reason=""
          if [ -n "$last_ok" ] && [ "$last_ok" != "null" ] \\'''

REPLACE_RESOLVER = '''          # TIER 1 (screened): the newest completed run whose `Symbol & Docs Screen` job reached a
          # VERDICT -- clean or not -- observed as the conclusion of its `Assert screens reached a
          # verdict` step. That step exits non-zero ONLY on a screen INVOCATION error (exit >=2),
          # where no verdict exists and the window genuinely is un-screened; a FINDING (exit 1) is
          # a verdict and MUST advance the base.
          #
          # The property BASE needs is COVERAGE -- "where does the un-screened region begin?" --
          # never "where were we last clean". Resolving it from run-level `status=success`
          # conflated the two: a finding left the base pinned, so every later merge re-screened the
          # same window and failed on someone else's damage, each red guaranteeing the next.
          # Measured on juniper-canopy 2026-08-31: a PR merged without a sequence-safety waiver,
          # main-verify went red, and `last_ok` stayed pinned -- permanently red rather than
          # self-clearing, escaped only by a hand-authored waiver commit. Ported from juniper-ml
          # (ml#1291); design of record: juniper-ml
          # notes/JUNIPER_2026-08-23_JUNIPER-ML_MAIN-VERIFY-CATCHUP-BASE-SCREENED-NOT-GREEN-DESIGN.md
          #
          # !! The step name below is LOAD-BEARING. Rename it and tier 1 matches nothing, the
          # !! resolver falls silently through to tier 2, and the defect returns with no error.
          SCREEN_JOB="Symbol & Docs Screen"
          VERDICT_STEP="Assert screens reached a verdict"
          SCAN_LIMIT=20
          screened=""
          runs="$(gh api "repos/${REPO}/actions/workflows/main-verify.yml/runs?status=completed&branch=main&per_page=${SCAN_LIMIT}" --jq '.workflow_runs[] | "\\(.id) \\(.head_sha)"' 2>/dev/null || true)"
          while read -r run_id run_sha; do
            [ -n "${run_id:-}" ] && [ -n "${run_sha:-}" ] || continue
            [ "$run_sha" != "null" ] || continue
            # Skip this very push, and anything not usable as a base for THIS head.
            [ "$run_sha" != "$HEAD_SHA" ] || continue
            git rev-parse --verify -q "${run_sha}^{commit}" >/dev/null 2>&1 || continue
            git merge-base --is-ancestor "$run_sha" "$HEAD_SHA" 2>/dev/null || continue
            verdict="$(gh api "repos/${REPO}/actions/runs/${run_id}/jobs" --jq "[.jobs[] | select(.name == \\"${SCREEN_JOB}\\") | .steps[]? | select(.name == \\"${VERDICT_STEP}\\") | .conclusion] | first // \\"\\"" 2>/dev/null || true)"
            if [ "$verdict" = "success" ]; then
              screened="$run_sha"
              break
            fi
          done <<< "$runs"
          # TIER 2 (legacy success): the pre-port single-shot query. Kept for the TRANSITION -- no
          # historical run carries the tier-1 step name, so without this the first run after this
          # change would not sweep -- and as a sound, merely conservative, degradation path if the
          # jobs API is unavailable. A run that SUCCEEDED necessarily reached a verdict, so going
          # forward tier 1 subsumes this and it can never select a NEWER base than tier 1.
          last_ok="$(gh api "repos/${REPO}/actions/workflows/main-verify.yml/runs?status=success&branch=main&per_page=1" --jq '.workflow_runs[0].head_sha' 2>/dev/null || true)"
          base=""
          reason=""
          if [ -n "$screened" ]; then
            n="$(git rev-list --count "${screened}..${HEAD_SHA}" 2>/dev/null || echo '?')"
            base="$screened"
            reason="screened-tip catch-up from ${screened} (${n} commits)"
          elif [ -n "$last_ok" ] && [ "$last_ok" != "null" ] \\'''

EDITS = (
    ("id: screens", ANCHOR_SCREENS_STEP, REPLACE_SCREENS_STEP),
    ("screens tail -> outputs + assert steps", ANCHOR_TAIL, REPLACE_TAIL),
    ("resolver tier 1", ANCHOR_RESOLVER, REPLACE_RESOLVER),
)


def fail(msg, code=1):
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(code)


def validate(text, path):
    """Parse the YAML and shell-check every run block. Returns a list of problems."""
    problems = []
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [f"YAML does not parse: {exc}"]
    jobs = (doc or {}).get("jobs", {})
    if not jobs:
        return ["no jobs found after patch"]
    for jid, job in jobs.items():
        for step in job.get("steps", []) or []:
            if "run" not in step:
                continue
            with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as fh:
                fh.write(step["run"])
                tmp = fh.name
            proc = subprocess.run(["bash", "-n", tmp], capture_output=True, text=True, check=False)  # nosec B603 B607
            os.unlink(tmp)
            if proc.returncode != 0:
                problems.append(f"{jid}/{step.get('name')}: shell syntax: {proc.stderr.strip()}")
    # The invariants the port exists to establish.
    screen_job = next((j for j in jobs.values() if j.get("name") == "Symbol & Docs Screen"), None)
    if screen_job is None:
        problems.append("no job named 'Symbol & Docs Screen' (the resolver filters on it)")
    else:
        names = [s.get("name") for s in screen_job.get("steps", []) or []]
        for required in ("Assert screens reached a verdict", "Assert screens clean"):
            if required not in names:
                problems.append(f"missing step {required!r}")
        if "Assert screens reached a verdict" in names and "Assert screens clean" in names:
            if names.index("Assert screens reached a verdict") > names.index("Assert screens clean"):
                problems.append("coverage assert must precede the clean assert")
        screens = next((s for s in screen_job.get("steps", []) or [] if s.get("id") == "screens"), None)
        if screens is None:
            problems.append("screens step has no 'id: screens'")
        elif "exit 1" in screens.get("run", ""):
            problems.append("screens step still fails on a finding")
    return problems


def main():
    ap = argparse.ArgumentParser(description="port the SCREENED-not-GREEN catch-up base into a repo")
    ap.add_argument("repo_root", help="path to the repo (or worktree) to patch")
    ap.add_argument("--dry-run", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()

    path = os.path.join(os.path.realpath(args.repo_root), WORKFLOW_REL)
    if not os.path.isfile(path):
        fail(f"no {WORKFLOW_REL} at {path}")
    original = open(path, encoding="utf-8").read()

    if TIER1_MARKER in original:
        print(f"ALREADY PORTED: {path}")
        return 0

    patched = original
    for label, anchor, replacement in EDITS:
        count = patched.count(anchor)
        if count != 1:
            fail(f"anchor for {label!r} found {count} times (expected exactly 1) in {path}")
        patched = patched.replace(anchor, replacement, 1)

    problems = validate(patched, path)
    if problems:
        for p in problems:
            print(f"  VALIDATION: {p}", file=sys.stderr)
        fail(f"patched {path} failed validation; nothing written", code=2)

    if args.dry_run:
        print(f"WOULD PATCH: {path} (3 edits, validation clean)")
        return 0

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(patched)
    print(f"PATCHED: {path} (3 edits, YAML + bash -n + invariants clean)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
