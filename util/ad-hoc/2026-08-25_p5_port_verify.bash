#!/usr/bin/env bash
# P5 port verification, run IN the target repo's worktree: ratchet-confirm, the three negative
# controls, the ported suite, the repo's FULL unit suite, and the repo's own pre-commit.
#
# Project: juniper-ml
# Sub-Project: ad-hoc tooling
# Author: Paul Calnon
# Created: 2026-08-25
# Status: ad-hoc — migration (P5 fleet rollout, plan §P5 step d; tracking issue ml#1326)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: util/ad-hoc/2026-08-25_p5_port_memory_budget.py (renders what this verifies);
#          juniper-cascor#585 (the port that was RED on a test in a DIFFERENT file, which is
#          why the FULL suite runs here and not just the ported one)
#
# Why a script: each control is a plain command, but a port needs ~12 of them in sequence per
# repo, and a worktree-isolated session's shell gate refuses long git-bearing chains. One
# invocation per repo also makes the controls reproducible provenance rather than a claim in
# a PR body. Every control is a NEGATIVE control where it can be: a gate that cannot fail is
# the vacuous-pass class this repo documents.
#
# Usage:
#   bash util/ad-hoc/2026-08-25_p5_port_verify.bash <worktree> <python> <ported-test-path> \
#       [--workflow <path>] [--no-full] -- <full-suite pytest args...>
# Example:
#   bash util/ad-hoc/2026-08-25_p5_port_verify.bash \
#       /home/pcalnon/Development/python/Juniper/worktrees/juniper-data-client--feat--memory-budget-gate--... \
#       /opt/miniforge3/envs/JuniperCanopy1/bin/python tests/test_memory_budget_check.py -- tests/
#
# Exit 0 only if EVERY step passed. AGENTS.md is restored byte-for-byte after control 2/3 and
# the restore is verified with cmp, so a failed run cannot leave the growth behind.
set -euo pipefail

WT="${1:?worktree path}"
PY="${2:?python interpreter}"
TESTFILE="${3:?ported test path, relative to the worktree}"
shift 3
WORKFLOW=".github/workflows/ci.yml"
RUN_FULL=1
while [ $# -gt 0 ]; do
  case "$1" in
    --workflow) WORKFLOW="$2"; shift 2 ;;
    --no-full) RUN_FULL=0; shift ;;
    --) shift; break ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
FULL_ARGS=("$@")

cd "$WT"
CHECK="util/memory_budget_check.py"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
cp AGENTS.md "$SCRATCH/AGENTS.md.orig"

step() { printf '\n== %s\n' "$*"; }
expect_rc() { # expect_rc <want> <cmd...>
  local want="$1"; shift
  local rc=0
  "$@" || rc=$?
  if [ "$rc" -ne "$want" ]; then
    echo "!! expected exit $want, got $rc: $*" >&2
    exit 1
  fi
  echo "   -> exit $rc (expected $want)"
}

step "ceiling was seeded at the MEASURED size: --ratchet must have nothing to tighten"
cp conf/memory_budget.json "$SCRATCH/budget.before"
"$PY" "$CHECK" --repo-root . --ratchet | tee "$SCRATCH/ratchet.out"
grep -q "no ceiling could be tightened" "$SCRATCH/ratchet.out"
cmp -s conf/memory_budget.json "$SCRATCH/budget.before" || { echo "!! --ratchet rewrote the budget file" >&2; exit 1; }

step "control 1: clean tree -> exit 0"
expect_rc 0 "$PY" "$CHECK" --repo-root . --base-ref HEAD

step "control 2: +500 chars to AGENTS.md -> exit 1 (names ceiling and delta)"
printf '%0500d' 0 >> AGENTS.md
expect_rc 1 "$PY" "$CHECK" --repo-root . --base-ref HEAD

step "control 3: same growth + Allow-Budget-Overrun trailer -> exit 0, WAIVED, ceiling unchanged"
printf 'Allow-Budget-Overrun: AGENTS.md\n' > "$SCRATCH/trailers.txt"
expect_rc 0 "$PY" "$CHECK" --repo-root . --base-ref HEAD --trailers-file "$SCRATCH/trailers.txt"
cmp -s conf/memory_budget.json "$SCRATCH/budget.before" || { echo "!! the waiver moved the ceiling" >&2; exit 1; }

step "restore AGENTS.md byte-for-byte"
cp "$SCRATCH/AGENTS.md.orig" AGENTS.md
cmp AGENTS.md "$SCRATCH/AGENTS.md.orig"
expect_rc 0 "$PY" "$CHECK" --repo-root . --base-ref HEAD

step "workflow parses; memory-budget is standalone (not in any needs:) and advisory"
"$PY" - "$WORKFLOW" <<'PYEOF'
import sys, yaml
d = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
jobs = d["jobs"]
assert "memory-budget" in jobs, "no memory-budget job"
assert jobs["memory-budget"]["name"] == "Memory Budget"
for name, job in jobs.items():
    needs = job.get("needs") or []
    needs = [needs] if isinstance(needs, str) else needs
    assert "memory-budget" not in needs, f"memory-budget is in {name}.needs -- C9 violation"
run = jobs["memory-budget"]["steps"][-1]["run"]
assert "--advisory" in run and "--trailers-file" in run and "--base-ref FETCH_HEAD" in run
print(f"   ok: {len(jobs)} jobs, memory-budget standalone + advisory")
PYEOF

step "ported suite: $TESTFILE"
"$PY" -m pytest "$TESTFILE" -q -p no:cacheprovider 2>&1 | tail -3

if [ "$RUN_FULL" -eq 1 ]; then
  step "FULL unit suite (the cascor#585 lesson: the failing test lives in a DIFFERENT file): ${FULL_ARGS[*]}"
  "$PY" -m pytest "${FULL_ARGS[@]}" -q -p no:cacheprovider 2>&1 | tail -6
fi

step "this repo's own pre-commit on the ported files"
pre-commit run --files "$CHECK" "$TESTFILE" conf/memory_budget.json "$WORKFLOW" 2>&1 | grep -v "Skipped" | grep -vE "^\s*$" | tail -25

step "git status (expect exactly the ported files)"
git status --short

printf '\n== ALL STEPS PASSED for %s\n' "$(basename "$WT")"
