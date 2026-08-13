#!/usr/bin/env bash
# Finish the E-A cells whose first pass was corrupted by the GPU leak (or returned the
# 0-unit anomaly), one batch, fully detached.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-10
# Status:     ad-hoc -- one-off
# Retire when: the re-surfaced E-A grid is written up; delete with the campaign script.
# Related:    F-P4-1 re-surface; the GPU-leak trap (see the memory of the same name).
#
# Healthy spiral cells run 245-695 s EACH, so the whole batch exceeds any 10-minute
# harness timeout. Launch this with nohup and poll the log instead of holding a foreground
# process:
#   nohup util/ad-hoc/2026-08-10_ea_finish_cells.bash > /tmp/ea_finish.log 2>&1 &
#
# Reap orphans BEFORE the batch: a leaked forkserver child holds ~116 MiB of GPU and the
# candidates OOM silently once the card fills (runs still report succeeded / no_candidate).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"

# Which suite the cells belong to (E-A by default; E-B / E-C re-runs override it).
SUITE_YAML="${JUNIPER_SUITE_YAML:-${REPO_ROOT}/util/experiments/suites/p4/e-a-cascor-budget-sweep.yaml}"

# Cells may be overridden as positional args, e.g. to re-run only the pool>=16 cells:
#   nohup util/ad-hoc/2026-08-10_ea_finish_cells.bash c002-… c005-… c008-… c011-… &
#
# Those cells needed a widened stall window; that is now the suite's own
# execution.stall_seconds (ml#1069), so the JUNIPER_SUITE_DRIVER stall shim this script
# used to document is deleted and no driver override is required.
if (($# > 0)); then
    CELLS=("$@")
else
    CELLS=(c002-04e1b2e6 c005-3b19604c c007-559459dc c008-f4c5934d c009-15d03f9c c010-bc646387 c011-5e9a552d)
fi

# ONE CELL PER run_suite INVOCATION, reaping before each.
#
# A single batch is not safe: each healthy cell leaks ~285 MiB of GPU through orphaned
# forkserver children, so after 4-5 cells the card fills and the REMAINING cells silently
# degrade to 1 unit / no_candidate while still reporting outcome=succeeded. That is exactly
# what happened to c010 (202 OOM) and c011 (225 OOM) in the previous batch. Reaping between
# cells keeps every cell's GPU clean, at the cost of one suite dir per cell (aggregate by
# hand -- correctness beats a tidy single aggregate.csv here).
overall=0
for cell in "${CELLS[@]}"; do
    printf '\n[%s] reaping before %s\n' "$(date -u +%H:%M:%SZ)" "${cell}"
    "${REPO_ROOT}/util/reap_pytest_orphans.bash" | tail -1
    nvidia-smi --query-gpu=memory.free --format=csv,noheader 2>/dev/null | sed 's/^/  gpu free: /'
    printf '[%s] running %s\n' "$(date -u +%H:%M:%SZ)" "${cell}"
    python3 "${REPO_ROOT}/util/experiments/run_suite.py" \
        --suite "${SUITE_YAML}" \
        --only "${cell}"
    rc=$?
    ((rc != 0)) && overall=1
    printf '[%s] %s finished (exit %d)\n' "$(date -u +%H:%M:%SZ)" "${cell}" "${rc}"
done

printf '\n[%s] batch done (exit %d)\n' "$(date -u +%H:%M:%SZ)" "${overall}"
exit "${overall}"
